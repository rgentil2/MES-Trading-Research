from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import clustered_mean_stats, prepare_rth_features

ENTRY_CUTOFF_MINUTE = 11 * 60 + 30


def add_previous_levels(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy().sort_values("timestamp_et")

    sessions = (
        data.groupby("group_key", sort=False, observed=True)
        .agg(
            session_date=("session_date", "first"),
            contract=("contract", "first"),
            session_first_ts=("timestamp_et", "min"),
            prev_candidate_high=("high", "max"),
            prev_candidate_low=("low", "min"),
        )
        .sort_values("session_first_ts")
        .reset_index()
    )

    sessions["prev_session_date"] = sessions["session_date"].shift(1)
    sessions["prev_contract"] = sessions["contract"].shift(1)
    sessions["pdh"] = sessions["prev_candidate_high"].shift(1)
    sessions["pdl"] = sessions["prev_candidate_low"].shift(1)

    same_contract = sessions["contract"] == sessions["prev_contract"]
    sessions.loc[~same_contract, ["pdh", "pdl", "prev_session_date"]] = np.nan

    data = data.merge(
        sessions[["group_key", "pdh", "pdl", "prev_session_date"]],
        on="group_key",
        how="left",
        validate="many_to_one",
    )
    return data


def build_events(features: pd.DataFrame) -> pd.DataFrame:
    data = add_previous_levels(features)
    minute = data["timestamp_et"].dt.hour * 60 + data["timestamp_et"].dt.minute

    eligible = (
        (minute >= 9 * 60 + 31)
        & (minute <= ENTRY_CUTOFF_MINUTE)
        & data["pdh"].notna()
        & data["pdl"].notna()
    )

    outside = (data["close"] > data["pdh"]) | (data["close"] < data["pdl"])
    candidates = data[eligible & outside].copy()
    candidates.sort_values(["group_key", "timestamp_et"], inplace=True)

    events = (
        candidates.groupby("group_key", sort=False, observed=True)
        .head(1)
        .copy()
    )

    events["breakout"] = np.where(
        events["close"] > events["pdh"],
        "BREAK_HIGH",
        "BREAK_LOW",
    )
    events["direction"] = np.where(
        events["breakout"] == "BREAK_HIGH",
        1,
        -1,
    )

    events = events[
        events["exact_30m"].fillna(False)
        & events["fwd_30m"].notna()
    ].copy()

    events["directional_30m_bps"] = (
        events["direction"] * events["fwd_30m"] * 10000.0
    )
    events["distance_beyond_level_bps"] = np.where(
        events["direction"] > 0,
        (events["close"] / events["pdh"] - 1.0) * 10000.0,
        (events["pdl"] / events["close"] - 1.0) * 10000.0,
    )
    events["event_time_et"] = events["timestamp_et"].dt.strftime("%H:%M")

    keep = [
        "timestamp_et",
        "session_date",
        "year",
        "contract",
        "group_key",
        "prev_session_date",
        "breakout",
        "event_time_et",
        "close",
        "pdh",
        "pdl",
        "distance_beyond_level_bps",
        "directional_30m_bps",
    ]
    return events[keep].sort_values("timestamp_et").reset_index(drop=True)


def summarize(events: pd.DataFrame):
    y = events["directional_30m_bps"]
    robust = clustered_mean_stats(y, events["session_date"])

    yearly = (
        events.groupby("year", observed=True)
        .agg(
            n=("directional_30m_bps", "size"),
            sessions=("session_date", "nunique"),
            mean_directional_bps=("directional_30m_bps", "mean"),
            continuation_rate=(
                "directional_30m_bps",
                lambda s: float((s > 0).mean()),
            ),
        )
        .reset_index()
    )

    side = (
        events.groupby("breakout", observed=True)
        .agg(
            n=("directional_30m_bps", "size"),
            sessions=("session_date", "nunique"),
            mean_directional_bps=("directional_30m_bps", "mean"),
            continuation_rate=(
                "directional_30m_bps",
                lambda s: float((s > 0).mean()),
            ),
            mean_distance_beyond_level_bps=(
                "distance_beyond_level_bps",
                "mean",
            ),
        )
        .reset_index()
    )

    summary = pd.DataFrame([{
        "hypothesis": "H015",
        "n": int(len(events)),
        "sessions": int(events["session_date"].nunique()),
        "mean_directional_bps": float(y.mean()),
        "median_directional_bps": float(y.median()),
        "std_directional_bps": float(y.std(ddof=1)),
        "continuation_rate": float((y > 0).mean()),
        "mean_distance_beyond_level_bps": float(
            events["distance_beyond_level_bps"].mean()
        ),
        **robust,
        "years_positive": int(
            (yearly["mean_directional_bps"] > 0).sum()
        ),
        "years_observed": int(yearly["year"].nunique()),
    }])

    summary["passes_development_gate"] = (
        (summary["n"] >= 500)
        & (summary["sessions"] >= 500)
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
        "# R010 Previous RTH High/Low Breakout — development 2020–2024",
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
    p.add_argument(
        "--input",
        default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet",
    )
    p.add_argument("--start", default="2020-01-01")
    p.add_argument("--end", default="2024-12-31")
    p.add_argument(
        "--output-dir",
        default="results/R010/development_2020_2024",
    )
    a = p.parse_args()

    raw = pd.read_parquet(a.input)
    features = prepare_rth_features(raw, a.start, a.end, horizons=[30])
    events = build_events(features)
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
