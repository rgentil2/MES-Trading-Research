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
ANCHOR_BLOCKS = tuple(range(0, 8))   # 09:45 ... 11:30
MAX_FUTURE_BLOCK = 4                 # +60m


def classify_state(v, q20, q80):
    if pd.isna(v) or pd.isna(q20) or pd.isna(q80):
        return np.nan
    if v <= q20:
        return "LOW"
    if v >= q80:
        return "HIGH"
    return "NORMAL"


def build_blocks(raw: pd.DataFrame) -> pd.DataFrame:
    rth = prepare_rth_features(
        raw,
        "2020-01-01",
        "2025-12-31",
        horizons=[15],
    )
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

        # Need blocks through 12:30 ET for +60m outcomes from 11:30 anchors.
        max_end_min = 12 * 60 + 30
        eligible = g[mins <= max_end_min].copy().reset_index(drop=True)
        if len(eligible) < 180:
            continue

        for block_id in range(12):  # end times 09:45 ... 12:30
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
            high = float(b["high"].max())
            low = float(b["low"].min())
            if close <= 0 or high <= low:
                continue

            rows.append({
                "group_key": key,
                "session_date": b["session_date"].iloc[0],
                "year": year,
                "contract": b["contract"].iloc[0],
                "block_id": block_id,
                "block_end_ts": b["timestamp_et"].iloc[-1],
                "block_end_minute": int(bmins.iloc[-1]),
                "range15_bps": (high - low) / close * 10000.0,
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


def build_events(blocks: pd.DataFrame) -> pd.DataFrame:
    cur = blocks[blocks["block_id"].isin(ANCHOR_BLOCKS)].copy()
    cur = cur[cur["state"].notna()].copy()

    for k in range(1, MAX_FUTURE_BLOCK + 1):
        fut = blocks[
            [
                "group_key",
                "block_id",
                "range15_bps",
                "baseline_mean",
                "state",
            ]
        ].copy()
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


def effect_for_state(events: pd.DataFrame, state: str, k: int) -> pd.Series:
    ratio = events[f"ratio_plus{k}"]
    return (ratio - 1.0) * 100.0 if state == "HIGH" else (1.0 - ratio) * 100.0


def summarize_effect(hypothesis, events, state, k, min_n, min_sessions, min_mean):
    e = events[
        (events["state"] == state)
        & events[f"ratio_plus{k}"].notna()
        & (events[f"baseline_plus{k}"] > 0)
    ].copy()
    e["effect"] = effect_for_state(e, state, k)
    stats = clustered_mean_stats(e["effect"], e["session_date"])
    yearly = e.groupby("year", observed=True)["effect"].mean().reset_index(name="mean_effect")
    row = {
        "hypothesis": hypothesis,
        "state": state,
        "horizon_blocks": k,
        "n": int(len(e)),
        "sessions": int(e["session_date"].nunique()),
        "mean_effect": float(e["effect"].mean()) if len(e) else np.nan,
        "median_effect": float(e["effect"].median()) if len(e) else np.nan,
        "positive_rate": float((e["effect"] > 0).mean()) if len(e) else np.nan,
        **stats,
        "years_positive": int((yearly["mean_effect"] > 0).sum()),
        "years_observed": int(yearly["year"].nunique()),
        "min_n_gate": min_n,
        "min_sessions_gate": min_sessions,
        "min_mean_gate": min_mean,
    }
    return e, row, yearly


def decay_table(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state in ["HIGH", "LOW"]:
        base = events[events["state"] == state].copy()
        for k in range(1, 5):
            e = base[base[f"ratio_plus{k}"].notna() & (base[f"baseline_plus{k}"] > 0)].copy()
            e["effect"] = effect_for_state(e, state, k)
            rows.append({
                "state": state,
                "minutes_ahead": k * 15,
                "n": int(len(e)),
                "sessions": int(e["session_date"].nunique()),
                "mean_effect_pct": float(e["effect"].mean()) if len(e) else np.nan,
                "median_effect_pct": float(e["effect"].median()) if len(e) else np.nan,
                "same_state_rate": float((e[f"state_plus{k}"] == state).mean()) if len(e) else np.nan,
            })
    return pd.DataFrame(rows)


def transition_results(events: pd.DataFrame):
    e = events[events["state_plus1"].notna()].copy()
    matrix = pd.crosstab(e["state"], e["state_plus1"], normalize="index").reindex(
        index=["LOW", "NORMAL", "HIGH"],
        columns=["LOW", "NORMAL", "HIGH"],
        fill_value=0.0,
    )

    hi = e[e["state"] == "HIGH"]
    lo = e[e["state"] == "LOW"]
    hi_success = int((hi["state_plus1"] == "HIGH").sum())
    lo_success = int((lo["state_plus1"] == "LOW").sum())
    hi_n = int(len(hi))
    lo_n = int(len(lo))
    hi_rate = hi_success / hi_n if hi_n else np.nan
    lo_rate = lo_success / lo_n if lo_n else np.nan
    hi_p = float(binomtest(hi_success, hi_n, 0.20, alternative="greater").pvalue) if hi_n else np.nan
    lo_p = float(binomtest(lo_success, lo_n, 0.20, alternative="greater").pvalue) if lo_n else np.nan
    primary_p = max(hi_p, lo_p) if np.isfinite(hi_p) and np.isfinite(lo_p) else np.nan

    summary = {
        "hypothesis": "H063",
        "n": hi_n + lo_n,
        "sessions": int(e[e["state"].isin(["HIGH", "LOW"])]["session_date"].nunique()),
        "high_n": hi_n,
        "low_n": lo_n,
        "high_self_rate": hi_rate,
        "low_self_rate": lo_rate,
        "high_p_value": hi_p,
        "low_p_value": lo_p,
        "p_value": primary_p,
        "passes_individual_gate": bool(
            hi_n >= 500
            and lo_n >= 500
            and hi_rate >= 0.30
            and lo_rate >= 0.30
            and hi_p < 0.05
            and lo_p < 0.05
        ),
    }
    return matrix, summary


def anchor_breakdown(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state in ["HIGH", "LOW"]:
        for block_id, g in events[events["state"] == state].groupby("block_id", observed=True):
            if not g["ratio_plus1"].notna().any():
                continue
            x = g[g["ratio_plus1"].notna() & (g["baseline_plus1"] > 0)].copy()
            x["effect"] = effect_for_state(x, state, 1)
            rows.append({
                "state": state,
                "block_id": int(block_id),
                "block_end_minute": int(g["block_end_minute"].iloc[0]),
                "n": int(len(x)),
                "mean_next15_effect_pct": float(x["effect"].mean()) if len(x) else np.nan,
                "same_state_next_rate": float((x["state_plus1"] == state).mean()) if len(x) else np.nan,
            })
    return pd.DataFrame(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir", default="results/B09")
    a = p.parse_args()

    raw = pd.read_parquet(a.input)
    blocks = build_blocks(raw)
    events = build_events(blocks)

    e59, r59, y59 = summarize_effect("H059", events, "HIGH", 1, 500, 300, 10.0)
    e60, r60, y60 = summarize_effect("H060", events, "LOW", 1, 500, 300, 10.0)
    e61, r61, y61 = summarize_effect("H061", events, "HIGH", 4, 300, 250, 5.0)
    e62, r62, y62 = summarize_effect("H062", events, "LOW", 4, 300, 250, 5.0)

    decay = decay_table(events)
    for row, state in [(r61, "HIGH"), (r62, "LOW")]:
        mids = decay[(decay["state"] == state) & (decay["minutes_ahead"].isin([15,30,45]))]
        row["intermediate_all_positive"] = bool((mids["mean_effect_pct"] > 0).all() and len(mids) == 3)

    matrix, r63 = transition_results(events)

    summary = pd.DataFrame([r59, r60, r61, r62, r63])
    summary["q_value_bh"] = benjamini_hochberg(summary["p_value"])

    for h in ["H059", "H060"]:
        i = summary["hypothesis"] == h
        summary.loc[i, "passes_individual_gate"] = (
            (summary.loc[i, "n"] >= summary.loc[i, "min_n_gate"])
            & (summary.loc[i, "sessions"] >= summary.loc[i, "min_sessions_gate"])
            & (summary.loc[i, "mean_effect"] >= summary.loc[i, "min_mean_gate"])
            & (summary.loc[i, "ci_low"] > 0)
            & (summary.loc[i, "years_observed"] == 6)
            & (summary.loc[i, "years_positive"] >= 4)
        )

    for h in ["H061", "H062"]:
        i = summary["hypothesis"] == h
        summary.loc[i, "passes_individual_gate"] = (
            (summary.loc[i, "n"] >= summary.loc[i, "min_n_gate"])
            & (summary.loc[i, "sessions"] >= summary.loc[i, "min_sessions_gate"])
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
    e59.to_parquet(out / "H059_events.parquet", index=False)
    e60.to_parquet(out / "H060_events.parquet", index=False)
    e61.to_parquet(out / "H061_events.parquet", index=False)
    e62.to_parquet(out / "H062_events.parquet", index=False)
    pd.concat([
        y59.assign(hypothesis="H059"),
        y60.assign(hypothesis="H060"),
        y61.assign(hypothesis="H061"),
        y62.assign(hypothesis="H062"),
    ], ignore_index=True).to_csv(out / "yearly.csv", index=False)
    decay.to_csv(out / "decay_curve.csv", index=False)
    matrix.to_csv(out / "transition_matrix.csv")
    anchor_breakdown(events).to_csv(out / "anchor_breakdown.csv", index=False)
    summary.to_csv(out / "B09_SUMMARY.csv", index=False)

    print(summary.to_string(index=False))
    print("\nDecay curve")
    print(decay.to_string(index=False))
    print("\nTransition matrix")
    print(matrix.to_string())


if __name__ == "__main__":
    main()
