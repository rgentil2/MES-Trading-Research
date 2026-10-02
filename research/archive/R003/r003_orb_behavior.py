from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from research.archive.R001.r001_vwap_analysis import (
    add_forward_extrema,
    clustered_mean_stats,
    prepare_features,
)
from research.archive.R002.r002_vwap_regimes import benjamini_hochberg


def build_opening_range_events(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy()

    opening = data[data["bar_index"] < 15].copy()
    stats = (
        opening.groupby("group_key", sort=False, observed=True)
        .agg(
            or_high=("high", "max"),
            or_low=("low", "min"),
            or_count=("timestamp_et", "size"),
            or_first_ts=("timestamp_et", "min"),
            or_last_ts=("timestamp_et", "max"),
        )
        .reset_index()
    )

    first_minute = stats["or_first_ts"].dt.hour * 60 + stats["or_first_ts"].dt.minute
    last_minute = stats["or_last_ts"].dt.hour * 60 + stats["or_last_ts"].dt.minute
    stats["or_valid"] = (
        (stats["or_count"] == 15)
        & (first_minute == 9 * 60 + 31)
        & (last_minute == 9 * 60 + 45)
        & ((stats["or_last_ts"] - stats["or_first_ts"]) == pd.Timedelta(minutes=14))
    )

    data = data.merge(
        stats[["group_key", "or_high", "or_low", "or_valid"]],
        on="group_key",
        how="left",
        validate="many_to_one",
    )

    after_or = data["bar_index"] >= 15
    outside = (data["close"] > data["or_high"]) | (data["close"] < data["or_low"])
    candidates = data[data["or_valid"].fillna(False) & after_or & outside].copy()

    if candidates.empty:
        return candidates

    candidates.sort_values(["group_key", "timestamp_et"], inplace=True)
    first = candidates.groupby("group_key", sort=False, observed=True).head(1).copy()

    first["breakout"] = np.where(first["close"] > first["or_high"], "UPPER", "LOWER")
    first["direction"] = np.where(first["breakout"] == "UPPER", 1, -1)

    first = first[first["exact_30m"].fillna(False) & first["fwd_30m"].notna()].copy()

    first["directional_30m_bps"] = first["direction"] * first["fwd_30m"] * 10000.0
    first["or_width_bps"] = (
        (first["or_high"] - first["or_low"]) / first["close"] * 10000.0
    )

    long_side = first["direction"] == 1
    first["mfe_30m_bps"] = np.where(
        long_side,
        (first["future_high_30m"] / first["close"] - 1.0) * 10000.0,
        (1.0 - first["future_low_30m"] / first["close"]) * 10000.0,
    )
    first["mae_30m_bps"] = np.where(
        long_side,
        (first["future_low_30m"] / first["close"] - 1.0) * 10000.0,
        (1.0 - first["future_high_30m"] / first["close"]) * 10000.0,
    )

    keep = [
        "timestamp_et",
        "session_date",
        "year",
        "contract",
        "group_key",
        "breakout",
        "direction",
        "close",
        "or_high",
        "or_low",
        "or_width_bps",
        "fwd_30m",
        "directional_30m_bps",
        "mfe_30m_bps",
        "mae_30m_bps",
    ]
    return first[keep].sort_values("timestamp_et").reset_index(drop=True)


def summarize_primary(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    primary_rows = []
    yearly_rows = []

    for breakout, hypothesis in [("UPPER", "H005"), ("LOWER", "H006")]:
        g = events[events["breakout"] == breakout].copy()
        y = g["directional_30m_bps"]
        robust = clustered_mean_stats(y, g["session_date"])

        yearly = (
            g.groupby("year", observed=True)
            .agg(
                n=("directional_30m_bps", "size"),
                sessions=("session_date", "nunique"),
                mean_directional_bps=("directional_30m_bps", "mean"),
                continuation_rate=("directional_30m_bps", lambda s: float((s > 0).mean())),
            )
            .reset_index()
        )
        yearly["hypothesis"] = hypothesis
        yearly["breakout"] = breakout
        yearly_rows.append(yearly)

        primary_rows.append(
            {
                "hypothesis": hypothesis,
                "breakout": breakout,
                "n": int(len(g)),
                "sessions": int(g["session_date"].nunique()),
                "mean_directional_bps": float(y.mean()) if len(y) else np.nan,
                "median_directional_bps": float(y.median()) if len(y) else np.nan,
                "std_directional_bps": float(y.std(ddof=1)) if len(y) > 1 else np.nan,
                "continuation_rate": float((y > 0).mean()) if len(y) else np.nan,
                "mean_mfe_30m_bps": float(g["mfe_30m_bps"].mean()) if len(g) else np.nan,
                "mean_mae_30m_bps": float(g["mae_30m_bps"].mean()) if len(g) else np.nan,
                "mean_or_width_bps": float(g["or_width_bps"].mean()) if len(g) else np.nan,
                **robust,
            }
        )

    primary = pd.DataFrame(primary_rows)
    yearly = pd.concat(yearly_rows, ignore_index=True) if yearly_rows else pd.DataFrame()

    primary["q_value"] = benjamini_hochberg(primary["p_value"])

    year_signs = (
        yearly.assign(positive=lambda x: x["mean_directional_bps"] > 0)
        .groupby("hypothesis", observed=True)
        .agg(
            years_positive=("positive", "sum"),
            years_observed=("year", "nunique"),
        )
        .reset_index()
    )
    primary = primary.merge(year_signs, on="hypothesis", how="left")

    primary["passes_development_gate"] = (
        (primary["n"] >= 500)
        & (primary["sessions"] >= 500)
        & (primary["q_value"] < 0.05)
        & (primary["ci_low"] > 0)
        & (primary["mean_directional_bps"] >= 1.0)
        & (primary["years_observed"] == 5)
        & (primary["years_positive"] >= 4)
    )

    return primary, yearly


def write_summary(primary: pd.DataFrame, events: pd.DataFrame, output: Path) -> None:
    lines = [
        "# R003 Opening Range Breakout — development 2020–2024",
        "",
        "The event is the first close outside the 09:31–09:45 ET opening range.",
        "Positive directional return means continuation in the breakout direction.",
        "",
        "## Primary hypotheses",
        "",
        "| Hypothesis | Side | N | Sessions | Mean 30m (bps) | p | q | 95% CI | Positive years | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in primary.iterrows():
        lines.append(
            f"| {r['hypothesis']} | {r['breakout']} | {int(r['n'])} | {int(r['sessions'])} | "
            f"{r['mean_directional_bps']:.3f} | {r['p_value']:.4f} | {r['q_value']:.4f} | "
            f"[{r['ci_low']:.3f}, {r['ci_high']:.3f}] | "
            f"{int(r['years_positive'])}/{int(r['years_observed'])} | "
            f"{'PASS' if r['passes_development_gate'] else 'FAIL'} |"
        )
    lines += [
        "",
        f"Eligible first-breakout sessions: {len(events):,}",
        "",
        "2025 and 2026 were not used.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet"
    )
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--output-dir", default="results/R003/development_2020_2024")
    args = parser.parse_args()

    raw = pd.read_parquet(args.input)
    features = prepare_features(raw, args.start, args.end)
    features = add_forward_extrema(features)
    events = build_opening_range_events(features)
    primary, yearly = summarize_primary(events)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    events.to_parquet(out / "events.parquet", index=False, compression="zstd")
    primary.to_csv(out / "primary_hypotheses.csv", index=False)
    yearly.to_csv(out / "yearly_stability.csv", index=False)
    write_summary(primary, events, out / "SUMMARY.md")

    print(primary.to_string(index=False))
    print(f"Eligible sessions: {len(events):,}")


if __name__ == "__main__":
    main()
