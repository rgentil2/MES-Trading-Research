from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import clustered_mean_stats, prepare_rth_features

REFERENCE_SESSIONS = 60
START_MINUTE = 9 * 60 + 46
ENTRY_CUTOFF_MINUTE = 11 * 60 + 30
EFFICIENCY_MIN = 0.70
MAGNITUDE_QUANTILE = 0.90


def add_momentum_features(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy().reset_index(drop=True)
    group = data.groupby("group_key", sort=False, observed=True)

    prev_close = group["close"].shift(1)
    prev_ts = group["timestamp_et"].shift(1)
    exact_1m = (data["timestamp_et"] - prev_ts) == pd.Timedelta(minutes=1)
    data["logret_1m"] = np.where(
        exact_1m,
        np.log(data["close"] / prev_close),
        np.nan,
    )

    lag_close_15 = group["close"].shift(15)
    lag_ts_15 = group["timestamp_et"].shift(15)
    exact_15_history = (
        (data["timestamp_et"] - lag_ts_15) == pd.Timedelta(minutes=15)
    ).fillna(False)

    data["r15_log"] = np.where(
        exact_15_history,
        np.log(data["close"] / lag_close_15),
        np.nan,
    )

    abs_path = (
        data.groupby("group_key", sort=False, observed=True)["logret_1m"]
        .rolling(15, min_periods=15)
        .apply(lambda x: float(np.abs(x).sum()), raw=True)
        .reset_index(level=0, drop=True)
    )
    data["path_abs_15"] = np.where(exact_15_history, abs_path, np.nan)
    data["er15"] = np.where(
        data["path_abs_15"] > 0,
        np.abs(data["r15_log"]) / data["path_abs_15"],
        np.nan,
    )

    data["minute_of_day"] = (
        data["timestamp_et"].dt.hour * 60 + data["timestamp_et"].dt.minute
    )
    data.sort_values(["minute_of_day", "timestamp_et"], inplace=True)

    data["abs_r15_threshold"] = data.groupby(
        "minute_of_day",
        sort=False,
        observed=True,
    )["r15_log"].transform(
        lambda s: s.abs().shift(1).rolling(
            REFERENCE_SESSIONS,
            min_periods=REFERENCE_SESSIONS,
        ).quantile(MAGNITUDE_QUANTILE)
    )

    data.sort_values("timestamp_et", inplace=True)
    return data


def build_events(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy()
    minute = data["minute_of_day"]

    eligible = (
        (minute >= START_MINUTE)
        & (minute <= ENTRY_CUTOFF_MINUTE)
        & data["r15_log"].notna()
        & data["er15"].notna()
        & data["abs_r15_threshold"].notna()
        & data["exact_15m"].fillna(False)
        & data["fwd_15m"].notna()
    )

    signal = (
        data["r15_log"].abs() >= data["abs_r15_threshold"]
    ) & (data["er15"] >= EFFICIENCY_MIN)

    candidates = data[eligible & signal].copy()
    candidates.sort_values(["group_key", "timestamp_et"], inplace=True)
    events = (
        candidates.groupby("group_key", sort=False, observed=True)
        .head(1)
        .copy()
    )

    events["direction"] = np.sign(events["r15_log"]).astype(int)
    events["side"] = np.where(events["direction"] > 0, "UP", "DOWN")
    events["directional_15m_bps"] = (
        events["direction"] * events["fwd_15m"] * 10000.0
    )
    events["trailing_15m_bps"] = events["r15_log"] * 10000.0
    events["event_time_et"] = events["timestamp_et"].dt.strftime("%H:%M")

    keep = [
        "timestamp_et",
        "session_date",
        "year",
        "contract",
        "group_key",
        "event_time_et",
        "side",
        "trailing_15m_bps",
        "abs_r15_threshold",
        "er15",
        "directional_15m_bps",
    ]
    return events[keep].sort_values("timestamp_et").reset_index(drop=True)


def summarize(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    y = events["directional_15m_bps"]
    robust = clustered_mean_stats(y, events["session_date"])

    yearly = (
        events.groupby("year", observed=True)
        .agg(
            n=("directional_15m_bps", "size"),
            sessions=("session_date", "nunique"),
            mean_directional_bps=("directional_15m_bps", "mean"),
            continuation_rate=(
                "directional_15m_bps",
                lambda s: float((s > 0).mean()),
            ),
        )
        .reset_index()
    )

    side = (
        events.groupby("side", observed=True)
        .agg(
            n=("directional_15m_bps", "size"),
            sessions=("session_date", "nunique"),
            mean_directional_bps=("directional_15m_bps", "mean"),
            continuation_rate=(
                "directional_15m_bps",
                lambda s: float((s > 0).mean()),
            ),
            mean_er15=("er15", "mean"),
            mean_trailing_15m_bps=("trailing_15m_bps", "mean"),
        )
        .reset_index()
    )

    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H012",
                "n": int(len(events)),
                "sessions": int(events["session_date"].nunique()),
                "mean_directional_bps": float(y.mean()),
                "median_directional_bps": float(y.median()),
                "std_directional_bps": float(y.std(ddof=1)),
                "continuation_rate": float((y > 0).mean()),
                "mean_er15": float(events["er15"].mean()),
                "mean_abs_trailing_15m_bps": float(events["trailing_15m_bps"].abs().mean()),
                **robust,
                "years_positive": int((yearly["mean_directional_bps"] > 0).sum()),
                "years_observed": int(yearly["year"].nunique()),
            }
        ]
    )

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


def write_summary(summary: pd.DataFrame, output: Path) -> None:
    r = summary.iloc[0]
    lines = [
        "# R007 Efficient Momentum — development 2020–2024",
        "",
        f"- Events: {int(r['n'])}",
        f"- Mean directional 15m: {r['mean_directional_bps']:.3f} bps",
        f"- Continuation rate: {r['continuation_rate']:.2%}",
        f"- p-value: {r['p_value']:.6f}",
        f"- 95% CI: [{r['ci_low']:.3f}, {r['ci_high']:.3f}] bps",
        f"- Positive years: {int(r['years_positive'])}/{int(r['years_observed'])}",
        f"- Gate: {'PASS' if r['passes_development_gate'] else 'FAIL'}",
        "",
        "2025 and 2026 were not used.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet",
    )
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument(
        "--output-dir",
        default="results/R007/development_2020_2024",
    )
    args = parser.parse_args()

    raw = pd.read_parquet(args.input)
    features = prepare_rth_features(raw, args.start, args.end, horizons=[15])
    features = add_momentum_features(features)
    events = build_events(features)
    summary, yearly, side = summarize(events)

    out = Path(args.output_dir)
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
