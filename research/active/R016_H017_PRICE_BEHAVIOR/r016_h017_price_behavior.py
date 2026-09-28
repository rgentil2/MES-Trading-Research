from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import benjamini_hochberg, clustered_mean_stats, prepare_rth_features

REF = 60
RV_Q = 0.10
R5_Q = 0.70
START_MINUTE = 10 * 60 + 1
ENTRY_CUTOFF = 11 * 60 + 30


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy().reset_index(drop=True)
    g = d.groupby("group_key", sort=False, observed=True)

    prev_close = g["close"].shift(1)
    prev_ts = g["timestamp_et"].shift(1)
    exact1 = (d["timestamp_et"] - prev_ts) == pd.Timedelta(minutes=1)
    d["r1"] = np.where(exact1, np.log(d["close"] / prev_close), np.nan)

    lag_ts30 = g["timestamp_et"].shift(30)
    exact_hist30 = ((d["timestamp_et"] - lag_ts30) == pd.Timedelta(minutes=30)).fillna(False)
    d["rv30"] = (
        d.groupby("group_key", sort=False, observed=True)["r1"]
        .rolling(30, min_periods=30)
        .apply(lambda x: float(np.sqrt(np.square(x).sum()) * 10000.0), raw=True)
        .reset_index(level=0, drop=True)
    )
    d["rv30"] = np.where(exact_hist30, d["rv30"], np.nan)

    lag_close5 = g["close"].shift(5)
    lag_ts5 = g["timestamp_et"].shift(5)
    exact_hist5 = ((d["timestamp_et"] - lag_ts5) == pd.Timedelta(minutes=5)).fillna(False)
    d["r5"] = np.where(exact_hist5, np.log(d["close"] / lag_close5), np.nan)

    # Fixed 15-bar range ending at each row.
    lag_ts14 = g["timestamp_et"].shift(14)
    exact_range15 = ((d["timestamp_et"] - lag_ts14) == pd.Timedelta(minutes=14)).fillna(False)
    d["range15_high"] = (
        d.groupby("group_key", sort=False, observed=True)["high"]
        .rolling(15, min_periods=15)
        .max()
        .reset_index(level=0, drop=True)
    )
    d["range15_low"] = (
        d.groupby("group_key", sort=False, observed=True)["low"]
        .rolling(15, min_periods=15)
        .min()
        .reset_index(level=0, drop=True)
    )
    d["range15_high"] = np.where(exact_range15, d["range15_high"], np.nan)
    d["range15_low"] = np.where(exact_range15, d["range15_low"], np.nan)

    d["abs_fwd30_bps"] = d["fwd_30m"].abs() * 10000.0
    d["minute"] = d["timestamp_et"].dt.hour * 60 + d["timestamp_et"].dt.minute

    d.sort_values(["minute", "timestamp_et"], inplace=True)
    by = d.groupby("minute", sort=False, observed=True)

    d["rv_threshold"] = by["rv30"].transform(
        lambda s: s.shift(1).rolling(REF, min_periods=REF).quantile(RV_Q)
    )
    d["baseline_abs_fwd30_bps"] = by["abs_fwd30_bps"].transform(
        lambda s: s.shift(1).rolling(REF, min_periods=REF).mean()
    )
    d["r5_abs_threshold"] = by["r5"].transform(
        lambda s: s.abs().shift(1).rolling(REF, min_periods=REF).quantile(R5_Q)
    )

    d.sort_values("timestamp_et", inplace=True)
    return d


def h017_events(features: pd.DataFrame) -> pd.DataFrame:
    d = features.copy()
    minute = d["minute"]
    eligible = (
        (minute >= START_MINUTE)
        & (minute <= ENTRY_CUTOFF)
        & d["rv30"].notna()
        & d["rv_threshold"].notna()
        & (d["rv30"] <= d["rv_threshold"])
    )
    c = d[eligible].copy()
    c.sort_values(["group_key", "timestamp_et"], inplace=True)
    return c.groupby("group_key", sort=False, observed=True).head(1).copy()


def stats_row(hypothesis, metric, events, stage, min_n, min_mean, min_positive_years=None):
    y = events[metric]
    stats = clustered_mean_stats(y, events["session_date"])
    yearly = events.groupby("year", observed=True)[metric].mean() if len(events) else pd.Series(dtype=float)
    row = {
        "hypothesis": hypothesis,
        "stage": stage,
        "n": int(len(events)),
        "sessions": int(events["session_date"].nunique()) if len(events) else 0,
        "mean_effect": float(y.mean()) if len(events) else np.nan,
        "median_effect": float(y.median()) if len(events) else np.nan,
        **stats,
        "positive_rate": float((y > 0).mean()) if len(events) else np.nan,
        "years_positive": int((yearly > 0).sum()) if len(yearly) else 0,
        "years_observed": int(len(yearly)),
    }
    passes = (
        row["n"] >= min_n
        and row["sessions"] >= min_n
        and np.isfinite(row["mean_effect"])
        and row["mean_effect"] >= min_mean
        and np.isfinite(row["ci_low"])
        and row["ci_low"] > 0
    )
    if min_positive_years is not None:
        passes = passes and row["years_observed"] == 6 and row["years_positive"] >= min_positive_years
    row["passes_individual_gate"] = bool(passes)
    return row, yearly.reset_index(name="mean_effect")


def build_h021(regimes: pd.DataFrame):
    e = regimes[
        (regimes["year"] == 2025)
        & regimes["baseline_abs_fwd30_bps"].notna()
        & regimes["abs_fwd30_bps"].notna()
        & (regimes["baseline_abs_fwd30_bps"] > 0)
    ].copy()
    e["abs_return_discount_pct"] = (
        1.0 - e["abs_fwd30_bps"] / e["baseline_abs_fwd30_bps"]
    ) * 100.0
    row, yearly = stats_row(
        "H021",
        "abs_return_discount_pct",
        e,
        "CONFIRMATORY_2025",
        min_n=60,
        min_mean=20.0,
    )
    return e, row, yearly


def build_h022(regimes: pd.DataFrame):
    e = regimes[
        regimes["r5"].notna()
        & regimes["r5_abs_threshold"].notna()
        & (regimes["r5"] != 0)
        & (regimes["r5"].abs() >= regimes["r5_abs_threshold"])
        & regimes["exact_15m"].fillna(False)
        & regimes["fwd_15m"].notna()
    ].copy()
    e["reversion_15m_bps"] = -np.sign(e["r5"]) * e["fwd_15m"] * 10000.0
    row, yearly = stats_row(
        "H022",
        "reversion_15m_bps",
        e,
        "DEV_2020_2025",
        min_n=100,
        min_mean=1.0,
        min_positive_years=4,
    )
    return e, row, yearly


def build_h023(features: pd.DataFrame, regimes: pd.DataFrame):
    rows = []
    grouped = {k: g.sort_values("timestamp_et") for k, g in features.groupby("group_key", sort=False, observed=True)}

    for _, event in regimes.iterrows():
        if pd.isna(event["range15_high"]) or pd.isna(event["range15_low"]):
            continue
        g = grouped.get(event["group_key"])
        if g is None:
            continue
        after = g[
            (g["timestamp_et"] > event["timestamp_et"])
            & ((g["timestamp_et"].dt.hour * 60 + g["timestamp_et"].dt.minute) <= ENTRY_CUTOFF)
        ].copy()
        if after.empty:
            continue
        outside = after[
            (after["close"] > event["range15_high"])
            | (after["close"] < event["range15_low"])
        ].copy()
        if outside.empty:
            continue
        b = outside.iloc[0]
        if not bool(b["exact_15m"]) or pd.isna(b["fwd_15m"]):
            continue
        direction = 1 if b["close"] > event["range15_high"] else -1
        rows.append({
            "timestamp_et": b["timestamp_et"],
            "session_date": b["session_date"],
            "year": int(b["year"]),
            "contract": b["contract"],
            "group_key": b["group_key"],
            "regime_timestamp_et": event["timestamp_et"],
            "breakout": "UP" if direction > 0 else "DOWN",
            "range15_high": float(event["range15_high"]),
            "range15_low": float(event["range15_low"]),
            "breakout_close": float(b["close"]),
            "fade_15m_bps": -direction * float(b["fwd_15m"]) * 10000.0,
        })

    e = pd.DataFrame(rows)
    if e.empty:
        e = pd.DataFrame(columns=[
            "timestamp_et","session_date","year","contract","group_key",
            "regime_timestamp_et","breakout","range15_high","range15_low",
            "breakout_close","fade_15m_bps"
        ])
    row, yearly = stats_row(
        "H023",
        "fade_15m_bps",
        e,
        "DEV_2020_2025",
        min_n=150,
        min_mean=1.0,
        min_positive_years=4,
    )
    return e, row, yearly


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir", default="results/R016")
    a = p.parse_args()

    raw = pd.read_parquet(a.input)
    features = prepare_rth_features(raw, "2020-01-01", "2025-12-31", horizons=[15, 30])
    features = add_features(features)
    regimes = h017_events(features)

    h21, r21, y21 = build_h021(regimes)
    h22, r22, y22 = build_h022(regimes)
    h23, r23, y23 = build_h023(features, regimes)

    summary = pd.DataFrame([r21, r22, r23])
    summary["q_value_bh"] = benjamini_hochberg(summary["p_value"])
    summary["passes_block_gate"] = (
        summary["passes_individual_gate"].astype(bool)
        & (summary["q_value_bh"] < 0.05)
    )

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    regimes.to_parquet(out / "h017_regime_events_2020_2025.parquet", index=False)

    for name, e, y in [
        ("H021", h21, y21),
        ("H022", h22, y22),
        ("H023", h23, y23),
    ]:
        e.to_parquet(out / f"{name}_events.parquet", index=False)
        y.to_csv(out / f"{name}_yearly.csv", index=False)

    summary.to_csv(out / "R016_SUMMARY.csv", index=False)

    lines = [
        "# R016 Results",
        "",
        "| Hypothesis | Stage | N | Mean effect | p | q(BH) | Individual | Block |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| {r['hypothesis']} | {r['stage']} | {int(r['n'])} | "
            f"{r['mean_effect']:.3f} | {r['p_value']:.6g} | {r['q_value_bh']:.6g} | "
            f"{bool(r['passes_individual_gate'])} | {bool(r['passes_block_gate'])} |"
        )
    lines += ["", "2026 was not used."]
    (out / "R016_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
