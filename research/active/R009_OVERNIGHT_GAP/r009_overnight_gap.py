from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import clustered_mean_stats, prepare_rth_features

REFERENCE_SESSIONS = 60
GAP_QUANTILE = 0.70


def build_session_gaps(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy().sort_values("timestamp_et")

    first = (
        data.groupby("group_key", sort=False, observed=True)
        .head(1)
        .copy()
    )
    last = (
        data.groupby("group_key", sort=False, observed=True)
        .tail(1)
        .copy()
    )

    first_min = first["timestamp_et"].dt.hour * 60 + first["timestamp_et"].dt.minute
    last_min = last["timestamp_et"].dt.hour * 60 + last["timestamp_et"].dt.minute

    first = first[first_min == 9 * 60 + 31].copy()
    last = last[last_min == 16 * 60].copy()

    sessions = first[
        [
            "session_date",
            "group_key",
            "timestamp_et",
            "year",
            "contract",
            "open",
            "close",
            "exact_30m",
            "fwd_30m",
            "high",
            "low",
        ]
    ].rename(
        columns={
            "timestamp_et": "signal_timestamp_et",
            "open": "open_0931",
            "close": "close_0931",
            "high": "high_0931",
            "low": "low_0931",
        }
    )

    closes = last[
        ["session_date", "contract", "close", "timestamp_et"]
    ].rename(
        columns={
            "close": "rth_close",
            "timestamp_et": "rth_close_timestamp",
        }
    )

    closes = closes.sort_values("rth_close_timestamp").reset_index(drop=True)
    closes["next_session_date"] = closes["session_date"].shift(-1)

    sessions = sessions.merge(
        closes[
            [
                "next_session_date",
                "contract",
                "rth_close",
                "rth_close_timestamp",
            ]
        ],
        left_on=["session_date", "contract"],
        right_on=["next_session_date", "contract"],
        how="left",
        validate="one_to_one",
    )

    sessions = sessions.drop(columns=["next_session_date"])
    sessions = sessions.sort_values("signal_timestamp_et").reset_index(drop=True)

    sessions["gap_log"] = np.log(
        sessions["open_0931"] / sessions["rth_close"]
    )
    sessions["gap_bps"] = sessions["gap_log"] * 10000.0
    sessions["abs_gap_log"] = sessions["gap_log"].abs()

    sessions["gap_threshold"] = (
        sessions["abs_gap_log"]
        .shift(1)
        .rolling(
            REFERENCE_SESSIONS,
            min_periods=REFERENCE_SESSIONS,
        )
        .quantile(GAP_QUANTILE)
    )

    return sessions


def build_events(sessions: pd.DataFrame) -> pd.DataFrame:
    events = sessions[
        sessions["rth_close"].notna()
        & sessions["gap_threshold"].notna()
        & sessions["exact_30m"].fillna(False)
        & sessions["fwd_30m"].notna()
        & (sessions["abs_gap_log"] >= sessions["gap_threshold"])
        & (sessions["gap_log"] != 0)
    ].copy()

    events["direction"] = np.sign(events["gap_log"]).astype(int)
    events["side"] = np.where(events["direction"] > 0, "GAP_UP", "GAP_DOWN")
    events["directional_30m_bps"] = (
        events["direction"] * events["fwd_30m"] * 10000.0
    )

    # Descriptive: did the first bar already trade through the prior RTH close?
    events["gap_filled_on_first_bar"] = np.where(
        events["direction"] > 0,
        events["low_0931"] <= events["rth_close"],
        events["high_0931"] >= events["rth_close"],
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
            continuation_rate=(
                "directional_30m_bps",
                lambda s: float((s > 0).mean()),
            ),
        )
        .reset_index()
    )

    side = (
        events.groupby("side", observed=True)
        .agg(
            n=("directional_30m_bps", "size"),
            sessions=("session_date", "nunique"),
            mean_directional_bps=("directional_30m_bps", "mean"),
            continuation_rate=(
                "directional_30m_bps",
                lambda s: float((s > 0).mean()),
            ),
            mean_gap_bps=("gap_bps", "mean"),
            first_bar_gap_fill_rate=(
                "gap_filled_on_first_bar",
                "mean",
            ),
        )
        .reset_index()
    )

    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H014",
                "n": int(len(events)),
                "sessions": int(events["session_date"].nunique()),
                "mean_directional_bps": float(y.mean()),
                "median_directional_bps": float(y.median()),
                "std_directional_bps": float(y.std(ddof=1)),
                "continuation_rate": float((y > 0).mean()),
                "mean_abs_gap_bps": float(events["gap_bps"].abs().mean()),
                **robust,
                "years_positive": int(
                    (yearly["mean_directional_bps"] > 0).sum()
                ),
                "years_observed": int(yearly["year"].nunique()),
            }
        ]
    )

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
        "# R009 Strong RTH Overnight Gap — development 2020–2024",
        "",
        f"- Events: {int(r['n'])}",
        f"- Mean directional 30m: {r['mean_directional_bps']:.3f} bps",
        f"- Continuation rate: {r['continuation_rate']:.2%}",
        f"- Mean absolute gap: {r['mean_abs_gap_bps']:.2f} bps",
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
        default="results/R009/development_2020_2024",
    )
    a = p.parse_args()

    raw = pd.read_parquet(a.input)
    features = prepare_rth_features(raw, a.start, a.end, horizons=[30])
    sessions = build_session_gaps(features)
    events = build_events(sessions)
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
