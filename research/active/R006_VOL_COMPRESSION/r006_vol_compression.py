from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import clustered_mean_stats, prepare_rth_features

REFERENCE_SESSIONS = 60
COMPRESSION_QUANTILE = 0.10
START_MINUTE = 10 * 60 + 1
ENTRY_CUTOFF_MINUTE = 11 * 60 + 30


def add_volatility_features(features: pd.DataFrame) -> pd.DataFrame:
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

    lag_ts_30 = group["timestamp_et"].shift(30)
    data["exact_history_30m"] = (
        (data["timestamp_et"] - lag_ts_30) == pd.Timedelta(minutes=30)
    ).fillna(False)

    current_rv = (
        data.groupby("group_key", sort=False, observed=True)["logret_1m"]
        .rolling(30, min_periods=30)
        .apply(lambda x: float(np.sqrt(np.square(x).sum()) * 10000.0), raw=True)
        .reset_index(level=0, drop=True)
    )
    data["rv30_current_bps"] = np.where(
        data["exact_history_30m"],
        current_rv,
        np.nan,
    )

    n_total = len(data)
    future_rv = np.full(n_total, np.nan, dtype=float)
    future_range = np.full(n_total, np.nan, dtype=float)
    indices = data.groupby("group_key", sort=False, observed=True).indices

    for idx in indices.values():
        pos = np.asarray(idx, dtype=int)
        n = len(pos)
        if n <= 30:
            continue

        rets = data.loc[pos, "logret_1m"].to_numpy(dtype=float)
        highs = data.loc[pos, "high"].to_numpy(dtype=float)
        lows = data.loc[pos, "low"].to_numpy(dtype=float)
        closes = data.loc[pos, "close"].to_numpy(dtype=float)

        ret_windows = np.lib.stride_tricks.sliding_window_view(rets[1:], 30)
        high_windows = np.lib.stride_tricks.sliding_window_view(highs[1:], 30)
        low_windows = np.lib.stride_tricks.sliding_window_view(lows[1:], 30)

        target = pos[: n - 30]
        rv_vals = np.sqrt(np.nansum(np.square(ret_windows), axis=1)) * 10000.0
        valid_ret = np.isfinite(ret_windows).all(axis=1)
        rv_vals[~valid_ret] = np.nan
        future_rv[target] = rv_vals

        range_vals = (high_windows.max(axis=1) - low_windows.min(axis=1)) / closes[: n - 30] * 10000.0
        future_range[target] = range_vals

    valid_future = data["exact_30m"].fillna(False).to_numpy(dtype=bool)
    future_rv[~valid_future] = np.nan
    future_range[~valid_future] = np.nan

    data["rv30_future_bps"] = future_rv
    data["future_range_30m_bps"] = future_range
    data["future_abs_return_30m_bps"] = data["fwd_30m"].abs() * 10000.0

    data["minute_of_day"] = data["timestamp_et"].dt.hour * 60 + data["timestamp_et"].dt.minute
    data.sort_values(["minute_of_day", "timestamp_et"], inplace=True)

    by_minute = data.groupby("minute_of_day", sort=False, observed=True)

    data["compression_threshold_bps"] = by_minute["rv30_current_bps"].transform(
        lambda s: s.shift(1).rolling(
            REFERENCE_SESSIONS,
            min_periods=REFERENCE_SESSIONS,
        ).quantile(COMPRESSION_QUANTILE)
    )
    data["baseline_future_rv_bps"] = by_minute["rv30_future_bps"].transform(
        lambda s: s.shift(1).rolling(
            REFERENCE_SESSIONS,
            min_periods=REFERENCE_SESSIONS,
        ).mean()
    )
    data["baseline_abs_return_30m_bps"] = by_minute["future_abs_return_30m_bps"].transform(
        lambda s: s.shift(1).rolling(
            REFERENCE_SESSIONS,
            min_periods=REFERENCE_SESSIONS,
        ).mean()
    )

    data.sort_values("timestamp_et", inplace=True)
    return data


def build_events(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy()
    minute = data["minute_of_day"]

    eligible = (
        (minute >= START_MINUTE)
        & (minute <= ENTRY_CUTOFF_MINUTE)
        & data["rv30_current_bps"].notna()
        & data["compression_threshold_bps"].notna()
        & data["baseline_future_rv_bps"].notna()
        & data["baseline_abs_return_30m_bps"].notna()
        & data["rv30_future_bps"].notna()
        & data["fwd_30m"].notna()
    )

    compressed = data["rv30_current_bps"] <= data["compression_threshold_bps"]
    candidates = data[eligible & compressed].copy()
    candidates.sort_values(["group_key", "timestamp_et"], inplace=True)

    events = (
        candidates.groupby("group_key", sort=False, observed=True)
        .head(1)
        .copy()
    )

    events["rv_uplift_pct"] = (
        events["rv30_future_bps"] / events["baseline_future_rv_bps"] - 1.0
    ) * 100.0
    events["abs_return_uplift_pct"] = (
        events["future_abs_return_30m_bps"]
        / events["baseline_abs_return_30m_bps"]
        - 1.0
    ) * 100.0
    events["event_time_et"] = events["timestamp_et"].dt.strftime("%H:%M")

    keep = [
        "timestamp_et",
        "session_date",
        "year",
        "contract",
        "group_key",
        "event_time_et",
        "rv30_current_bps",
        "compression_threshold_bps",
        "rv30_future_bps",
        "baseline_future_rv_bps",
        "rv_uplift_pct",
        "future_abs_return_30m_bps",
        "baseline_abs_return_30m_bps",
        "abs_return_uplift_pct",
        "future_range_30m_bps",
    ]
    return events[keep].sort_values("timestamp_et").reset_index(drop=True)


def summarize(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    y = events["rv_uplift_pct"]
    robust = clustered_mean_stats(y, events["session_date"])

    yearly = (
        events.groupby("year", observed=True)
        .agg(
            n=("rv_uplift_pct", "size"),
            sessions=("session_date", "nunique"),
            mean_rv_uplift_pct=("rv_uplift_pct", "mean"),
            median_rv_uplift_pct=("rv_uplift_pct", "median"),
            mean_abs_return_uplift_pct=("abs_return_uplift_pct", "mean"),
            mean_future_range_30m_bps=("future_range_30m_bps", "mean"),
        )
        .reset_index()
    )

    years_positive = int((yearly["mean_rv_uplift_pct"] > 0).sum())
    years_observed = int(yearly["year"].nunique())

    summary = pd.DataFrame(
        [
            {
                "hypothesis": "H011",
                "n": int(len(events)),
                "sessions": int(events["session_date"].nunique()),
                "mean_rv_uplift_pct": float(y.mean()),
                "median_rv_uplift_pct": float(y.median()),
                "std_rv_uplift_pct": float(y.std(ddof=1)),
                "mean_abs_return_uplift_pct": float(events["abs_return_uplift_pct"].mean()),
                "mean_future_range_30m_bps": float(events["future_range_30m_bps"].mean()),
                "mean_current_rv30_bps": float(events["rv30_current_bps"].mean()),
                "mean_future_rv30_bps": float(events["rv30_future_bps"].mean()),
                "mean_baseline_future_rv30_bps": float(events["baseline_future_rv_bps"].mean()),
                **robust,
                "years_positive": years_positive,
                "years_observed": years_observed,
            }
        ]
    )

    summary["passes_development_gate"] = (
        (summary["n"] >= 500)
        & (summary["sessions"] >= 500)
        & (summary["p_value"] < 0.05)
        & (summary["ci_low"] > 0)
        & (summary["mean_rv_uplift_pct"] >= 10.0)
        & (summary["years_observed"] == 5)
        & (summary["years_positive"] >= 4)
    )
    return summary, yearly


def write_summary(summary: pd.DataFrame, output: Path) -> None:
    r = summary.iloc[0]
    lines = [
        "# R006 Compression → Expansion — development 2020–2024",
        "",
        "Signals are restricted to 10:01–11:30 ET. Exits/outcomes may occur after 11:30.",
        "",
        f"- Events: {int(r['n'])}",
        f"- Sessions: {int(r['sessions'])}",
        f"- Mean future RV uplift: {r['mean_rv_uplift_pct']:.2f}%",
        f"- Median future RV uplift: {r['median_rv_uplift_pct']:.2f}%",
        f"- p-value: {r['p_value']:.6f}",
        f"- 95% CI: [{r['ci_low']:.2f}%, {r['ci_high']:.2f}%]",
        f"- Positive years: {int(r['years_positive'])}/{int(r['years_observed'])}",
        f"- Development gate: {'PASS' if r['passes_development_gate'] else 'FAIL'}",
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
        default="results/R006/development_2020_2024",
    )
    args = parser.parse_args()

    raw = pd.read_parquet(args.input)
    features = prepare_rth_features(raw, args.start, args.end, horizons=[30])
    features = add_volatility_features(features)
    events = build_events(features)
    summary, yearly = summarize(events)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    events.to_parquet(out / "events.parquet", index=False, compression="zstd")
    summary.to_csv(out / "primary_hypothesis.csv", index=False)
    yearly.to_csv(out / "yearly_stability.csv", index=False)
    write_summary(summary, out / "SUMMARY.md")

    print(summary.to_string(index=False))
    print(yearly.to_string(index=False))


if __name__ == "__main__":
    main()
