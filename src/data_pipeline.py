from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]
CONTRACT_RE = re.compile(r"MES (\\d{2})-(\\d{2})\\.Last\\.txt$")


@dataclass(frozen=True)
class PipelineConfig:
    raw_dir: Path
    processed_dir: Path
    raw_pattern: str
    timestamp_timezone: str
    tick_size: float
    rollover_policy: str


def load_config(path: Path) -> PipelineConfig:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    data = cfg["data"]
    return PipelineConfig(
        raw_dir=Path(data["raw_dir"]),
        processed_dir=Path(data["processed_dir"]),
        raw_pattern=data.get("raw_pattern", "MES ??-??.Last.txt"),
        timestamp_timezone=data.get("timestamp_timezone", "UTC"),
        tick_size=float(data.get("tick_size", 0.25)),
        rollover_policy=data.get("rollover_policy", "ninjatrader_implicit"),
    )


def contract_info(path: Path) -> tuple[int, int, str]:
    match = CONTRACT_RE.fullmatch(path.name)
    if not match:
        raise ValueError(f"Unexpected raw filename: {path.name}")
    month = int(match.group(1))
    year = 2000 + int(match.group(2))
    if month not in {3, 6, 9, 12}:
        raise ValueError(f"Unexpected MES quarterly month in {path.name}")
    return year, month, f"MES {month:02d}-{year % 100:02d}"


def sorted_contract_files(raw_dir: Path, pattern: str) -> list[Path]:
    files = list(raw_dir.glob(pattern))
    return sorted(files, key=lambda p: contract_info(p)[:2])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_contract(path: Path, tick_size: float) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        sep=";",
        header=None,
        names=COLUMNS,
        on_bad_lines="error",
    )
    if df.empty:
        raise ValueError(f"Empty raw file: {path.name}")

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], format="%Y%m%d %H%M%S", errors="raise"
    )

    if not df["timestamp"].is_monotonic_increasing:
        raise ValueError(f"Out-of-order timestamps in {path.name}")
    if df["timestamp"].duplicated().any():
        raise ValueError(f"Duplicate timestamps inside {path.name}")
    if (df["volume"] <= 0).any():
        raise ValueError(f"Non-positive volume in {path.name}")

    price_cols = ["open", "high", "low", "close"]
    prices = df[price_cols].to_numpy(dtype=float)
    if not np.isfinite(prices).all():
        raise ValueError(f"Non-finite OHLC value in {path.name}")

    invalid_ohlc = (
        (df["low"] > df[["open", "close"]].min(axis=1))
        | (df["high"] < df[["open", "close"]].max(axis=1))
        | (df["low"] > df["high"])
    )
    if invalid_ohlc.any():
        raise ValueError(f"Invalid OHLC relationship in {path.name}")

    tick_units = prices / tick_size
    if not np.isclose(tick_units, np.round(tick_units), atol=1e-9).all():
        raise ValueError(f"Price off MES tick size ({tick_size}) in {path.name}")

    return df


def build_continuous(
    files: list[Path], timestamp_timezone: str, tick_size: float
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not files:
        raise ValueError("No raw MES contract files found")

    parts: list[pd.DataFrame] = []
    manifest_rows: list[dict] = []
    transition_rows: list[dict] = []

    previous_raw_end: pd.Timestamp | None = None
    previous_contract: str | None = None

    for index, path in enumerate(files):
        _, _, contract = contract_info(path)
        df = read_contract(path, tick_size=tick_size)
        raw_start = df["timestamp"].min()
        raw_end = df["timestamp"].max()
        raw_rows = len(df)

        if previous_raw_end is None:
            kept = df.copy()
        else:
            # Frozen project methodology:
            # keep the old contract through its final NinjaTrader-exported timestamp;
            # the next contract becomes active only after that timestamp.
            kept = df.loc[df["timestamp"] > previous_raw_end].copy()

        if kept.empty:
            raise ValueError(
                f"{path.name} contributes no rows after previous contract cutoff "
                f"{previous_raw_end}"
            )

        kept["contract"] = contract
        kept["is_rollover"] = False
        kept["rollover_from"] = pd.NA
        if index > 0:
            first_idx = kept.index[0]
            kept.loc[first_idx, "is_rollover"] = True
            kept.loc[first_idx, "rollover_from"] = previous_contract
            transition_rows.append(
                {
                    "old_contract": previous_contract,
                    "new_contract": contract,
                    "old_last_timestamp_utc": previous_raw_end,
                    "new_first_timestamp_used_utc": kept["timestamp"].min(),
                    "gap_minutes": (
                        kept["timestamp"].min() - previous_raw_end
                    ).total_seconds()
                    / 60.0,
                    "overlap_rows_removed_from_new": raw_rows - len(kept),
                }
            )

        manifest_rows.append(
            {
                "file": path.name,
                "contract": contract,
                "raw_rows": raw_rows,
                "raw_start_utc": raw_start,
                "raw_end_utc": raw_end,
                "rows_used": len(kept),
                "overlap_rows_removed": raw_rows - len(kept),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
        parts.append(kept)
        previous_raw_end = raw_end
        previous_contract = contract

    continuous = pd.concat(parts, ignore_index=True)
    continuous["timestamp_utc"] = continuous.pop("timestamp").dt.tz_localize(
        timestamp_timezone
    )
    continuous["timestamp_et"] = continuous["timestamp_utc"].dt.tz_convert(
        "America/New_York"
    )

    continuous = continuous[
        [
            "timestamp_utc",
            "timestamp_et",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "contract",
            "rollover_from",
            "is_rollover",
        ]
    ]

    if continuous["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate timestamps in continuous dataset")
    if not continuous["timestamp_utc"].is_monotonic_increasing:
        raise ValueError("Continuous dataset is not timestamp-sorted")

    return continuous, pd.DataFrame(manifest_rows), pd.DataFrame(transition_rows)


def write_outputs(
    continuous: pd.DataFrame,
    manifest: pd.DataFrame,
    transitions: pd.DataFrame,
    processed_dir: Path,
    results_dir: Path,
) -> dict:
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = processed_dir / "MES_CONTINUOUS_1M_2020_2026.parquet"
    manifest_path = results_dir / "raw_manifest.csv"
    transitions_path = results_dir / "rollover_transitions.csv"
    qc_path = results_dir / "qc_summary.json"

    continuous.to_parquet(parquet_path, index=False, compression="zstd")
    manifest.to_csv(manifest_path, index=False)
    transitions.to_csv(transitions_path, index=False)

    qc = {
        "contracts": int(len(manifest)),
        "raw_rows": int(manifest["raw_rows"].sum()),
        "continuous_rows": int(len(continuous)),
        "overlap_rows_removed": int(manifest["overlap_rows_removed"].sum()),
        "rollovers": int(continuous["is_rollover"].sum()),
        "duplicate_timestamps": int(continuous["timestamp_utc"].duplicated().sum()),
        "timestamp_sorted": bool(continuous["timestamp_utc"].is_monotonic_increasing),
        "start_utc": str(continuous["timestamp_utc"].min()),
        "end_utc": str(continuous["timestamp_utc"].max()),
        "min_rollover_gap_minutes": float(transitions["gap_minutes"].min()),
        "max_rollover_gap_minutes": float(transitions["gap_minutes"].max()),
        "methodology": (
            "NinjaTrader implicit rollover: use each old contract through its last "
            "exported timestamp, then use the next contract. No back-adjustment or "
            "synthetic bars are introduced."
        ),
    }
    qc_path.write_text(json.dumps(qc, indent=2), encoding="utf-8")
    return qc


def main() -> None:
    parser = argparse.ArgumentParser(description="Build continuous MES 1-minute dataset")
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    if cfg.rollover_policy != "ninjatrader_implicit":
        raise ValueError(
            f"Unsupported rollover_policy={cfg.rollover_policy!r}; expected "
            "'ninjatrader_implicit'"
        )

    files = sorted_contract_files(cfg.raw_dir, cfg.raw_pattern)
    continuous, manifest, transitions = build_continuous(
        files,
        timestamp_timezone=cfg.timestamp_timezone,
        tick_size=cfg.tick_size,
    )
    qc = write_outputs(
        continuous,
        manifest,
        transitions,
        processed_dir=cfg.processed_dir,
        results_dir=Path("results/data_quality"),
    )

    print(json.dumps(qc, indent=2))
    print("IMPORTANT: downstream returns must not cross rows where is_rollover=True.")


if __name__ == "__main__":
    main()
