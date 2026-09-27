from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from research.active.R009_OVERNIGHT_GAP.r009_overnight_gap import (
    build_events,
    build_session_gaps,
    summarize,
)
from src.research_utils import prepare_rth_features


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet",
    )
    p.add_argument("--warmup-start", default="2024-09-01")
    p.add_argument("--validation-start", default="2025-01-01")
    p.add_argument("--validation-end", default="2025-12-31")
    p.add_argument(
        "--output-dir",
        default="results/R009/validation_2025",
    )
    a = p.parse_args()

    raw = pd.read_parquet(a.input)
    features = prepare_rth_features(
        raw,
        a.warmup_start,
        a.validation_end,
        horizons=[30],
    )
    sessions = build_session_gaps(features)
    events_all = build_events(sessions)

    start = pd.Timestamp(a.validation_start).date()
    end = pd.Timestamp(a.validation_end).date()
    event_date = pd.to_datetime(
        events_all["signal_timestamp_et"],
        utc=True,
    ).dt.tz_convert("America/New_York").dt.date
    events = events_all[(event_date >= start) & (event_date <= end)].copy()

    summary, yearly, side = summarize(events)
    summary = summary.drop(columns=["passes_development_gate"])

    summary["passes_validation_gate"] = (
        (summary["n"] >= 50)
        & (summary["sessions"] >= 50)
        & (summary["mean_directional_bps"] >= 1.0)
        & (summary["p_value"] < 0.05)
        & (summary["ci_low"] > 0)
        & (summary["continuation_rate"] > 0.50)
    )

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    events.to_parquet(out / "events.parquet", index=False, compression="zstd")
    summary.to_csv(out / "validation_summary.csv", index=False)
    yearly.to_csv(out / "yearly_stability.csv", index=False)
    side.to_csv(out / "side_breakdown.csv", index=False)

    r = summary.iloc[0]
    lines = [
        "# R009 — OOS Validation 2025",
        "",
        f"- N: {int(r['n'])}",
        f"- Mean directional 30m: {r['mean_directional_bps']:.3f} bps",
        f"- Continuation rate: {r['continuation_rate']:.2%}",
        f"- p-value: {r['p_value']:.6f}",
        f"- 95% CI: [{r['ci_low']:.3f}, {r['ci_high']:.3f}] bps",
        f"- Validation gate: {'PASS' if r['passes_validation_gate'] else 'FAIL'}",
    ]
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(summary.to_string(index=False))
    print(side.to_string(index=False))


if __name__ == "__main__":
    main()
