from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import clustered_mean_stats, prepare_rth_features

REFERENCE_SESSIONS = 60
DRIVE_QUANTILE = 0.70
SIGNAL_MINUTE = 10 * 60


def build_opening_drives(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy()

    opening = data[data["bar_index"] < 30].copy()
    rows = []

    for group_key, g in opening.groupby("group_key", sort=False, observed=True):
        g = g.sort_values("timestamp_et")
        if len(g) != 30:
            continue

        first_ts = g["timestamp_et"].iloc[0]
        last_ts = g["timestamp_et"].iloc[-1]
        first_minute = first_ts.hour * 60 + first_ts.minute
        last_minute = last_ts.hour * 60 + last_ts.minute

        if first_minute != 9 * 60 + 31 or last_minute != SIGNAL_MINUTE:
            continue
        if (last_ts - first_ts) != pd.Timedelta(minutes=29):
            continue

        open_px = float(g["open"].iloc[0])
        close_px = float(g["close"].iloc[-1])
        drive_log = float(np.log(close_px / open_px))
        range_bps = float((g["high"].max() - g["low"].min()) / open_px * 10000.0)

        signal = g.iloc[-1]
        rows.append(
            {
                "timestamp_et": signal["timestamp_et"],
                "session_date": signal["session_date"],
                "year": int(signal["year"]),
                "contract": signal["contract"],
                "group_key": group_key,
                "open_0931": open_px,
                "close_1000": close_px,
                "opening_drive_log": drive_log,
                "opening_drive_bps": drive_log * 10000.0,
                "opening_range_30m_bps": range_bps,
                "exact_30m": bool(signal["exact_30m"]),
                "fwd_30m": signal["fwd_30m"],
            }
        )

    drives = pd.DataFrame(rows).sort_values("timestamp_et").reset_index(drop=True)
    drives["abs_drive_log"] = drives["opening_drive_log"].abs()
    drives["drive_threshold"] = (
        drives["abs_drive_log"]
        .shift(1)
        .rolling(REFERENCE_SESSIONS, min_periods=REFERENCE_SESSIONS)
        .quantile(DRIVE_QUANTILE)
    )
    return drives


def build_events(drives: pd.DataFrame) -> pd.DataFrame:
    events = drives[
        drives["drive_threshold"].notna()
        & drives["exact_30m"]
        & drives["fwd_30m"].notna()
        & (drives["abs_drive_log"] >= drives["drive_threshold"])
    ].copy()

    events["direction"] = np.sign(events["opening_drive_log"]).astype(int)
    events = events[events["direction"] != 0].copy()
    events["side"] = np.where(events["direction"] > 0, "UP", "DOWN")
    events["directional_30m_bps"] = (
        events["direction"] * events["fwd_30m"] * 10000.0
    )
    return events.reset_index(drop=True)


def summarize(events: pd.DataFrame):
    y = events["directional_30m_bps"]
    robust = clustered_mean_stats(y, events["session_date"])

    yearly = (
        events.groupby("year", observed=True)
        .agg(
            n=("directional_30m_bps", "size"),
            sessions=("session_date", "nunique"),
            mean_directional_bps=("directional_30m_bps", "mean"),
            continuation_rate=("directional_30m_bps", lambda s: float((s > 0).mean())),
        )
        .reset_index()
    )

    side = (
        events.groupby("side", observed=True)
        .agg(
            n=("directional_30m_bps", "size"),
            sessions=("session_date", "nunique"),
            mean_directional_bps=("directional_30m_bps", "mean"),
            continuation_rate=("directional_30m_bps", lambda s: float((s > 0).mean())),
            mean_opening_drive_bps=("opening_drive_bps", "mean"),
        )
        .reset_index()
    )

    summary = pd.DataFrame([{
        "hypothesis": "H013",
        "n": int(len(events)),
        "sessions": int(events["session_date"].nunique()),
        "mean_directional_bps": float(y.mean()),
        "median_directional_bps": float(y.median()),
        "std_directional_bps": float(y.std(ddof=1)),
        "continuation_rate": float((y > 0).mean()),
        "mean_abs_opening_drive_bps": float(events["opening_drive_bps"].abs().mean()),
        "mean_opening_range_30m_bps": float(events["opening_range_30m_bps"].mean()),
        **robust,
        "years_positive": int((yearly["mean_directional_bps"] > 0).sum()),
        "years_observed": int(yearly["year"].nunique()),
    }])

    summary["passes_development_gate"] = (
        (summary["n"] >= 300)
        & (summary["sessions"] >= 300)
        & (summary["p_value"] < 0.05)
        & (summary["ci_low"] > 0)
        & (summary["mean_directional_bps"] >= 1.0)
        & (summary["years_observed"] == 5)
        & (summary["years_positive"] >= 4)
    )
    return summary, yearly, side


def write_summary(summary: pd.DataFrame, output: Path):
    r = summary.iloc[0]
    lines = [
        "# R008 Strong Opening Drive — development 2020–2024",
        "",
        f"- Events: {int(r['n'])}",
        f"- Mean directional 30m: {r['mean_directional_bps']:.3f} bps",
        f"- Continuation rate: {r['continuation_rate']:.2%}",
        f"- p-value: {r['p_value']:.6f}",
        f"- 95% CI: [{r['ci_low']:.3f}, {r['ci_high']:.3f}] bps",
        f"- Positive years: {int(r['years_positive'])}/{int(r['years_observed'])}",
        f"- Gate: {'PASS' if r['passes_development_gate'] else 'FAIL'}",
        "",
        "2025 and 2026 were not used.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--start", default="2020-01-01")
    p.add_argument("--end", default="2024-12-31")
    p.add_argument("--output-dir", default="results/R008/development_2020_2024")
    a = p.parse_args()

    raw = pd.read_parquet(a.input)
    features = prepare_rth_features(raw, a.start, a.end, horizons=[30])
    drives = build_opening_drives(features)
    events = build_events(drives)
    summary, yearly, side = summarize(events)

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    events.to_parquet(out / "events.parquet", index=False, compression="zstd")
    summary.to_csv(out / "primary_hypothesis.csv", index=False)
    yearly.to_csv(out / "yearly_stability.csv", index=False)
    side.to_csv(out / "side_breakdown.csv", index=False)
    write_summary(summary, out / "SUMMARY.md")

    print(summary.to_string(index=False))
    print(yearly.to_string(index=False))
    print(side.to_string(index=False))


if __name__ == "__main__":
    main()
