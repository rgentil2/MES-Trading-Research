from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from src.research_utils import benjamini_hochberg, clustered_mean_stats, prepare_rth_features

REF = 60
LOW_Q = 0.20
HIGH_Q = 0.80
ANCHOR_BLOCKS = tuple(range(0, 8))
MAX_FUTURE_BLOCK = 16  # +240m


def classify_state(v, q20, q80):
    if pd.isna(v) or pd.isna(q20) or pd.isna(q80):
        return np.nan
    if v <= q20:
        return "LOW"
    if v >= q80:
        return "HIGH"
    return "NORMAL"


def build_blocks(raw):
    rth = prepare_rth_features(raw, "2020-01-01", "2025-12-31", horizons=[15])
    rows = []

    for key, g in rth.groupby("group_key", sort=False, observed=True):
        g = g.sort_values("timestamp_et").reset_index(drop=True)
        if len(g) != 390:
            continue

        mins = g["timestamp_et"].dt.hour * 60 + g["timestamp_et"].dt.minute
        if int(mins.iloc[0]) != 571 or int(mins.iloc[-1]) != 960:
            continue

        year = int(g["year"].iloc[0])
        if year < 2020 or year > 2025:
            continue

        # Through 15:30 ET = 24 complete 15m blocks from 09:31.
        eligible = g.iloc[:360].copy().reset_index(drop=True)
        if len(eligible) != 360:
            continue

        for block_id in range(24):
            start = block_id * 15
            end = start + 15
            b = eligible.iloc[start:end]
            if len(b) != 15:
                continue

            bmins = b["timestamp_et"].dt.hour * 60 + b["timestamp_et"].dt.minute
            expected_start = 571 + start
            expected_end = 570 + end
            if int(bmins.iloc[0]) != expected_start or int(bmins.iloc[-1]) != expected_end:
                continue

            close = float(b["close"].iloc[-1])
            hi = float(b["high"].max())
            lo = float(b["low"].min())
            if close <= 0 or hi <= lo:
                continue

            rows.append({
                "group_key": key,
                "session_date": b["session_date"].iloc[0],
                "year": year,
                "contract": b["contract"].iloc[0],
                "block_id": block_id,
                "block_end_ts": b["timestamp_et"].iloc[-1],
                "block_end_minute": int(bmins.iloc[-1]),
                "range15_bps": (hi - lo) / close * 10000.0,
            })

    d = pd.DataFrame(rows).sort_values(["block_id", "block_end_ts"]).reset_index(drop=True)

    d["q20"] = d.groupby("block_id", sort=False, observed=True)["range15_bps"].transform(
        lambda s: s.shift(1).rolling(REF, min_periods=REF).quantile(LOW_Q)
    )
    d["q80"] = d.groupby("block_id", sort=False, observed=True)["range15_bps"].transform(
        lambda s: s.shift(1).rolling(REF, min_periods=REF).quantile(HIGH_Q)
    )
    d["baseline_mean"] = d.groupby("block_id", sort=False, observed=True)["range15_bps"].transform(
        lambda s: s.shift(1).rolling(REF, min_periods=REF).mean()
    )
    d["state"] = [
        classify_state(v, q20, q80)
        for v, q20, q80 in zip(d["range15_bps"], d["q20"], d["q80"])
    ]

    return d.sort_values(["group_key", "block_id"]).reset_index(drop=True)


def build_events(blocks):
    cur = blocks[blocks["block_id"].isin(ANCHOR_BLOCKS)].copy()
    cur = cur[cur["state"].notna()].copy()

    base = blocks[["group_key", "block_id", "range15_bps", "baseline_mean", "state"]].copy()

    for k in range(1, MAX_FUTURE_BLOCK + 1):
        fut = base.copy()
        fut["block_id"] = fut["block_id"] - k
        fut = fut.rename(columns={
            "range15_bps": f"range_plus{k}",
            "baseline_mean": f"baseline_plus{k}",
            "state": f"state_plus{k}",
        })
        cur = cur.merge(
            fut,
            on=["group_key", "block_id"],
            how="left",
            validate="one_to_one",
        )
        cur[f"ratio_plus{k}"] = cur[f"range_plus{k}"] / cur[f"baseline_plus{k}"]

    return cur


def state_effect(frame, state, k):
    ratio = frame[f"ratio_plus{k}"]
    if state == "HIGH":
        return (ratio - 1.0) * 100.0
    return (1.0 - ratio) * 100.0


def summarize_effect(h, events, state, k, min_mean):
    e = events[
        (events["state"] == state)
        & events[f"ratio_plus{k}"].notna()
        & (events[f"baseline_plus{k}"] > 0)
    ].copy()
    e["effect"] = state_effect(e, state, k)

    stats = clustered_mean_stats(e["effect"], e["session_date"])
    yearly = e.groupby("year", observed=True)["effect"].mean().reset_index(name="mean_effect")

    return e, {
        "hypothesis": h,
        "state": state,
        "horizon_minutes": k * 15,
        "n": int(len(e)),
        "sessions": int(e["session_date"].nunique()),
        "mean_effect": float(e["effect"].mean()) if len(e) else np.nan,
        "median_effect": float(e["effect"].median()) if len(e) else np.nan,
        "positive_rate": float((e["effect"] > 0).mean()) if len(e) else np.nan,
        **stats,
        "years_positive": int((yearly["mean_effect"] > 0).sum()),
        "years_observed": int(yearly["year"].nunique()),
        "min_mean_gate": min_mean,
    }, yearly


def decay_table(events):
    rows = []
    for state in ["HIGH", "LOW"]:
        base = events[events["state"] == state].copy()
        for k in range(1, MAX_FUTURE_BLOCK + 1):
            e = base[
                base[f"ratio_plus{k}"].notna()
                & (base[f"baseline_plus{k}"] > 0)
            ].copy()
            e["effect"] = state_effect(e, state, k)
            opposite = "LOW" if state == "HIGH" else "HIGH"
            rows.append({
                "state": state,
                "minutes_ahead": 15 * k,
                "n": int(len(e)),
                "sessions": int(e["session_date"].nunique()),
                "mean_effect_pct": float(e["effect"].mean()) if len(e) else np.nan,
                "median_effect_pct": float(e["effect"].median()) if len(e) else np.nan,
                "same_state_rate": float((e[f"state_plus{k}"] == state).mean()) if len(e) else np.nan,
                "opposite_state_rate": float((e[f"state_plus{k}"] == opposite).mean()) if len(e) else np.nan,
            })
    return pd.DataFrame(rows)


def h073(events):
    k = 16
    e = events[events[f"state_plus{k}"].notna()].copy()
    hi = e[e["state"] == "HIGH"]
    lo = e[e["state"] == "LOW"]

    hi_n = int(len(hi))
    lo_n = int(len(lo))
    hi_success = int((hi[f"state_plus{k}"] == "HIGH").sum())
    lo_success = int((lo[f"state_plus{k}"] == "LOW").sum())

    hi_rate = hi_success / hi_n if hi_n else np.nan
    lo_rate = lo_success / lo_n if lo_n else np.nan

    hi_p = float(binomtest(hi_success, hi_n, 0.20, alternative="greater").pvalue) if hi_n else np.nan
    lo_p = float(binomtest(lo_success, lo_n, 0.20, alternative="greater").pvalue) if lo_n else np.nan

    return {
        "hypothesis": "H073",
        "n": hi_n + lo_n,
        "sessions": int(e[e["state"].isin(["HIGH", "LOW"])]["session_date"].nunique()),
        "high_n": hi_n,
        "low_n": lo_n,
        "high_same_state_240": hi_rate,
        "low_same_state_240": lo_rate,
        "high_p_value": hi_p,
        "low_p_value": lo_p,
        "p_value": max(hi_p, lo_p) if np.isfinite(hi_p) and np.isfinite(lo_p) else np.nan,
        "passes_individual_gate": bool(
            hi_n >= 1000
            and lo_n >= 1000
            and hi_rate >= 0.25
            and lo_rate >= 0.25
            and hi_p < 0.05
            and lo_p < 0.05
        ),
    }


def landmarks(decay):
    rows = []
    for state in ["HIGH", "LOW"]:
        d = decay[decay["state"] == state].sort_values("minutes_ahead")
        first = float(d.iloc[0]["mean_effect_pct"])
        half = first * 0.5

        below_half = d[d["mean_effect_pct"] < half]
        below_10 = d[d["mean_effect_pct"] < 10.0]

        rows.append({
            "state": state,
            "effect_15_pct": first,
            "effect_120_pct": float(d[d["minutes_ahead"] == 120]["mean_effect_pct"].iloc[0]),
            "effect_180_pct": float(d[d["minutes_ahead"] == 180]["mean_effect_pct"].iloc[0]),
            "effect_240_pct": float(d[d["minutes_ahead"] == 240]["mean_effect_pct"].iloc[0]),
            "first_below_half_minutes": int(below_half.iloc[0]["minutes_ahead"]) if len(below_half) else np.nan,
            "first_below_10pct_minutes": int(below_10.iloc[0]["minutes_ahead"]) if len(below_10) else np.nan,
        })
    return pd.DataFrame(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir", default="results/B11")
    a = p.parse_args()

    blocks = build_blocks(pd.read_parquet(a.input))
    events = build_events(blocks)

    e69, r69, y69 = summarize_effect("H069", events, "HIGH", 12, 10.0)
    e70, r70, y70 = summarize_effect("H070", events, "LOW", 12, 5.0)
    e71, r71, y71 = summarize_effect("H071", events, "HIGH", 16, 5.0)
    e72, r72, y72 = summarize_effect("H072", events, "LOW", 16, 5.0)
    r73 = h073(events)

    decay = decay_table(events)

    for row, state, target_k in [
        (r69, "HIGH", 12),
        (r70, "LOW", 12),
        (r71, "HIGH", 16),
        (r72, "LOW", 16),
    ]:
        mids = decay[
            (decay["state"] == state)
            & (decay["minutes_ahead"].isin([15 * k for k in range(1, target_k)]))
        ]
        row["intermediate_all_positive"] = bool(
            len(mids) == target_k - 1
            and (mids["mean_effect_pct"] > 0).all()
        )

    summary = pd.DataFrame([r69, r70, r71, r72, r73])
    summary["q_value_bh"] = benjamini_hochberg(summary["p_value"])

    for h in ["H069", "H070", "H071", "H072"]:
        i = summary["hypothesis"] == h
        summary.loc[i, "passes_individual_gate"] = (
            (summary.loc[i, "n"] >= 1000)
            & (summary.loc[i, "sessions"] >= 500)
            & (summary.loc[i, "mean_effect"] >= summary.loc[i, "min_mean_gate"])
            & (summary.loc[i, "ci_low"] > 0)
            & (summary.loc[i, "years_observed"] == 6)
            & (summary.loc[i, "years_positive"] >= 4)
            & summary.loc[i, "intermediate_all_positive"].astype(bool)
        )

    summary["passes_block_gate"] = (
        summary["passes_individual_gate"].fillna(False).astype(bool)
        & (summary["q_value_bh"] < 0.05)
    )

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    blocks.to_parquet(out / "blocks.parquet", index=False)
    events.to_parquet(out / "events.parquet", index=False)
    e69.to_parquet(out / "H069_events.parquet", index=False)
    e70.to_parquet(out / "H070_events.parquet", index=False)
    e71.to_parquet(out / "H071_events.parquet", index=False)
    e72.to_parquet(out / "H072_events.parquet", index=False)

    pd.concat([
        y69.assign(hypothesis="H069"),
        y70.assign(hypothesis="H070"),
        y71.assign(hypothesis="H071"),
        y72.assign(hypothesis="H072"),
    ], ignore_index=True).to_csv(out / "yearly.csv", index=False)

    decay.to_csv(out / "decay_curve_15_to_240.csv", index=False)
    landmarks(decay).to_csv(out / "decay_landmarks.csv", index=False)
    summary.to_csv(out / "B11_SUMMARY.csv", index=False)

    print(summary.to_string(index=False))
    print("\nSelected decay horizons")
    print(
        decay[decay["minutes_ahead"].isin([15, 60, 120, 180, 240])]
        .to_string(index=False)
    )
    print("\nLandmarks")
    print(landmarks(decay).to_string(index=False))


if __name__ == "__main__":
    main()
