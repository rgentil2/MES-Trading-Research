from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from research.archive.R001.r001_vwap_analysis import clustered_mean_stats, prepare_features
from research.archive.R002.r002_vwap_regimes import benjamini_hochberg

SHOCK_THRESHOLD = 2.0


def add_shock_features(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy()
    group = data.groupby("group_key", sort=False, observed=True)

    prev_close = group["close"].shift(1)
    prev_ts = group["timestamp_et"].shift(1)
    exact_1m = (data["timestamp_et"] - prev_ts) == pd.Timedelta(minutes=1)
    data["logret_1m"] = np.where(
        exact_1m,
        np.log(data["close"] / prev_close),
        np.nan,
    )

    lag_close_5 = group["close"].shift(5)
    lag_ts_5 = group["timestamp_et"].shift(5)
    exact_5m = (data["timestamp_et"] - lag_ts_5) == pd.Timedelta(minutes=5)
    data["r5_log"] = np.where(
        exact_5m,
        np.log(data["close"] / lag_close_5),
        np.nan,
    )

    lag_ts_60 = group["timestamp_et"].shift(60)
    exact_60m = (data["timestamp_et"] - lag_ts_60) == pd.Timedelta(minutes=60)
    data["exact_history_60m"] = exact_60m.fillna(False)

    rolling_std = (
        data.groupby("group_key", sort=False, observed=True)["logret_1m"]
        .rolling(window=60, min_periods=60)
        .std(ddof=0)
        .reset_index(level=0, drop=True)
    )
    data["sigma1_60"] = np.where(data["exact_history_60m"], rolling_std, np.nan)
    denom = data["sigma1_60"] * np.sqrt(5.0)
    data["shock_z"] = np.where(
        exact_5m & data["exact_history_60m"] & (denom > 0),
        data["r5_log"] / denom,
        np.nan,
    )

    data["prev_shock_z"] = data.groupby(
        "group_key", sort=False, observed=True
    )["shock_z"].shift(1)
    return data


def build_events(features: pd.DataFrame) -> pd.DataFrame:
    positive = (features["shock_z"] >= SHOCK_THRESHOLD) & (
        features["prev_shock_z"] < SHOCK_THRESHOLD
    )
    negative = (features["shock_z"] <= -SHOCK_THRESHOLD) & (
        features["prev_shock_z"] > -SHOCK_THRESHOLD
    )

    frames = []
    for event, shock_direction, mask in [
        ("POSITIVE_SHOCK", 1, positive),
        ("NEGATIVE_SHOCK", -1, negative),
    ]:
        ev = features.loc[
            mask,
            [
                "timestamp_et",
                "session_date",
                "year",
                "contract",
                "group_key",
                "close",
                "shock_z",
                "sigma1_60",
                "r5_log",
                "exact_15m",
                "fwd_15m",
            ],
        ].copy()
        ev["event"] = event
        ev["shock_direction"] = shock_direction
        frames.append(ev)

    events = pd.concat(frames, ignore_index=True)
    events = events[events["exact_15m"] & events["fwd_15m"].notna()].copy()
    events["reversion_15m_bps"] = (
        -events["shock_direction"] * events["fwd_15m"] * 10000.0
    )
    return events.sort_values("timestamp_et").reset_index(drop=True)


def summarize(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    primary_rows = []
    yearly_rows = []

    for event, hypothesis in [
        ("POSITIVE_SHOCK", "H007"),
        ("NEGATIVE_SHOCK", "H008"),
    ]:
        g = events[events["event"] == event].copy()
        y = g["reversion_15m_bps"]
        robust = clustered_mean_stats(y, g["session_date"])

        yearly = (
            g.groupby("year", observed=True)
            .agg(
                n=("reversion_15m_bps", "size"),
                sessions=("session_date", "nunique"),
                mean_reversion_bps=("reversion_15m_bps", "mean"),
                reversion_rate=("reversion_15m_bps", lambda s: float((s > 0).mean())),
            )
            .reset_index()
        )
        yearly["hypothesis"] = hypothesis
        yearly["event"] = event
        yearly_rows.append(yearly)

        primary_rows.append(
            {
                "hypothesis": hypothesis,
                "event": event,
                "n": int(len(g)),
                "sessions": int(g["session_date"].nunique()),
                "mean_reversion_bps": float(y.mean()) if len(y) else np.nan,
                "median_reversion_bps": float(y.median()) if len(y) else np.nan,
                "std_reversion_bps": float(y.std(ddof=1)) if len(y) > 1 else np.nan,
                "reversion_rate": float((y > 0).mean()) if len(y) else np.nan,
                "mean_abs_shock_z": float(g["shock_z"].abs().mean()) if len(g) else np.nan,
                **robust,
            }
        )

    primary = pd.DataFrame(primary_rows)
    yearly = pd.concat(yearly_rows, ignore_index=True)
    primary["q_value"] = benjamini_hochberg(primary["p_value"])

    years = (
        yearly.assign(positive=lambda x: x["mean_reversion_bps"] > 0)
        .groupby("hypothesis", observed=True)
        .agg(
            years_positive=("positive", "sum"),
            years_observed=("year", "nunique"),
        )
        .reset_index()
    )
    primary = primary.merge(years, on="hypothesis", how="left")

    primary["passes_development_gate"] = (
        (primary["n"] >= 1000)
        & (primary["sessions"] >= 500)
        & (primary["q_value"] < 0.05)
        & (primary["ci_low"] > 0)
        & (primary["mean_reversion_bps"] >= 1.0)
        & (primary["years_observed"] == 5)
        & (primary["years_positive"] >= 4)
    )
    return primary, yearly


def write_summary(primary: pd.DataFrame, events: pd.DataFrame, output: Path) -> None:
    lines = [
        "# R004 Standardized 5m Shock Reversion — development 2020–2024",
        "",
        "Positive score means reversal against the preceding standardized 5-minute shock.",
        "",
        "| Hypothesis | Event | N | Sessions | Mean reversion (bps) | p | q | 95% CI | Positive years | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in primary.iterrows():
        lines.append(
            f"| {r['hypothesis']} | {r['event']} | {int(r['n'])} | {int(r['sessions'])} | "
            f"{r['mean_reversion_bps']:.3f} | {r['p_value']:.4f} | {r['q_value']:.4f} | "
            f"[{r['ci_low']:.3f}, {r['ci_high']:.3f}] | "
            f"{int(r['years_positive'])}/{int(r['years_observed'])} | "
            f"{'PASS' if r['passes_development_gate'] else 'FAIL'} |"
        )
    lines += [
        "",
        f"Eligible events: {len(events):,}",
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
    parser.add_argument("--output-dir", default="results/R004/development_2020_2024")
    args = parser.parse_args()

    raw = pd.read_parquet(args.input)
    features = prepare_features(raw, args.start, args.end)
    features = add_shock_features(features)
    events = build_events(features)
    primary, yearly = summarize(events)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    events.to_parquet(out / "events.parquet", index=False, compression="zstd")
    primary.to_csv(out / "primary_hypotheses.csv", index=False)
    yearly.to_csv(out / "yearly_stability.csv", index=False)
    write_summary(primary, events, out / "SUMMARY.md")

    print(primary.to_string(index=False))
    print(f"Eligible events: {len(events):,}")


if __name__ == "__main__":
    main()
