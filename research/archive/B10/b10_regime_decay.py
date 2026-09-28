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
ANCHOR_BLOCKS = tuple(range(0, 8))  # 09:45 ... 11:30 ET
MAX_FUTURE_BLOCK = 8                # +120m
PRACTICAL_THRESHOLD_PCT = 10.0


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

        # 09:31 through 13:30 = 240 bars = 16 non-overlapping 15m blocks.
        eligible = g.iloc[:240].copy().reset_index(drop=True)
        if len(eligible) != 240:
            continue

        for block_id in range(16):
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

    base_cols = [
        "group_key",
        "block_id",
        "range15_bps",
        "baseline_mean",
        "state",
    ]

    for k in range(1, MAX_FUTURE_BLOCK + 1):
        fut = blocks[base_cols].copy()
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


def state_effect(events: pd.DataFrame, state: str, k: int) -> pd.Series:
    ratio = events[f"ratio_plus{k}"]
    if state == "HIGH":
        return (ratio - 1.0) * 100.0
    return (1.0 - ratio) * 100.0


def summarize_effect(hypothesis, events, state, k, min_n, min_sessions, min_mean):
    e = events[
        (events["state"] == state)
        & events[f"ratio_plus{k}"].notna()
        & (events[f"baseline_plus{k}"] > 0)
    ].copy()
    e["effect"] = state_effect(e, state, k)

    stats = clustered_mean_stats(e["effect"], e["session_date"])
    yearly = (
        e.groupby("year", observed=True)["effect"]
        .mean()
        .reset_index(name="mean_effect")
    )

    row = {
        "hypothesis": hypothesis,
        "state": state,
        "horizon_blocks": k,
        "horizon_minutes": k * 15,
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


def full_decay_table(events: pd.DataFrame) -> pd.DataFrame:
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
                "minutes_ahead": k * 15,
                "n": int(len(e)),
                "sessions": int(e["session_date"].nunique()),
                "mean_effect_pct": float(e["effect"].mean()) if len(e) else np.nan,
                "median_effect_pct": float(e["effect"].median()) if len(e) else np.nan,
                "same_state_rate": float((e[f"state_plus{k}"] == state).mean()) if len(e) else np.nan,
                "opposite_state_rate": float((e[f"state_plus{k}"] == opposite).mean()) if len(e) else np.nan,
            })
    return pd.DataFrame(rows)


def continuous_survival(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    survival_rows = []
    duration_rows = []

    for state in ["HIGH", "LOW"]:
        base = events[events["state"] == state].copy()
        if base.empty:
            continue

        continuous_blocks = np.zeros(len(base), dtype=int)
        alive = np.ones(len(base), dtype=bool)

        for k in range(1, MAX_FUTURE_BLOCK + 1):
            same = (base[f"state_plus{k}"].to_numpy(object) == state)
            alive = alive & same
            continuous_blocks[alive] = k
            survival_rows.append({
                "state": state,
                "minutes": k * 15,
                "n_origin": int(len(base)),
                "continuous_survival_rate": float(alive.mean()),
            })

        for i, (_, row) in enumerate(base.iterrows()):
            duration_rows.append({
                "state": state,
                "group_key": row["group_key"],
                "session_date": row["session_date"],
                "year": int(row["year"]),
                "block_id": int(row["block_id"]),
                "continuous_same_state_minutes": int(continuous_blocks[i] * 15),
                "censored_at_120": bool(continuous_blocks[i] == MAX_FUTURE_BLOCK),
            })

    return pd.DataFrame(survival_rows), pd.DataFrame(duration_rows)


def decay_landmarks(decay: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state in ["HIGH", "LOW"]:
        d = decay[decay["state"] == state].sort_values("minutes_ahead")
        first = float(d.iloc[0]["mean_effect_pct"])
        half_threshold = first * 0.5

        half_candidates = d[d["mean_effect_pct"] < half_threshold]
        practical_candidates = d[d["mean_effect_pct"] < PRACTICAL_THRESHOLD_PCT]

        rows.append({
            "state": state,
            "effect_at_15_pct": first,
            "half_effect_threshold_pct": half_threshold,
            "first_below_half_minutes": (
                int(half_candidates.iloc[0]["minutes_ahead"])
                if len(half_candidates) else np.nan
            ),
            "first_below_10pct_minutes": (
                int(practical_candidates.iloc[0]["minutes_ahead"])
                if len(practical_candidates) else np.nan
            ),
        })
    return pd.DataFrame(rows)


def h068_summary(events: pd.DataFrame):
    k = 8
    e = events[events[f"state_plus{k}"].notna()].copy()

    hi = e[e["state"] == "HIGH"]
    lo = e[e["state"] == "LOW"]

    hi_success = int((hi[f"state_plus{k}"] == "HIGH").sum())
    lo_success = int((lo[f"state_plus{k}"] == "LOW").sum())
    hi_n = int(len(hi))
    lo_n = int(len(lo))

    hi_rate = hi_success / hi_n if hi_n else np.nan
    lo_rate = lo_success / lo_n if lo_n else np.nan

    hi_p = (
        float(binomtest(hi_success, hi_n, 0.20, alternative="greater").pvalue)
        if hi_n else np.nan
    )
    lo_p = (
        float(binomtest(lo_success, lo_n, 0.20, alternative="greater").pvalue)
        if lo_n else np.nan
    )
    primary_p = max(hi_p, lo_p) if np.isfinite(hi_p) and np.isfinite(lo_p) else np.nan

    return {
        "hypothesis": "H068",
        "n": hi_n + lo_n,
        "sessions": int(e[e["state"].isin(["HIGH", "LOW"])]["session_date"].nunique()),
        "high_n": hi_n,
        "low_n": lo_n,
        "high_same_state_120": hi_rate,
        "low_same_state_120": lo_rate,
        "high_p_value": hi_p,
        "low_p_value": lo_p,
        "p_value": primary_p,
        "passes_individual_gate": bool(
            hi_n >= 1000
            and lo_n >= 1000
            and hi_rate >= 0.30
            and lo_rate >= 0.30
            and hi_p < 0.05
            and lo_p < 0.05
        ),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet",
    )
    p.add_argument("--output-dir", default="results/B10")
    a = p.parse_args()

    raw = pd.read_parquet(a.input)
    blocks = build_blocks(raw)
    events = build_events(blocks)

    e64, r64, y64 = summarize_effect("H064", events, "HIGH", 6, 1000, 500, 20.0)
    e65, r65, y65 = summarize_effect("H065", events, "LOW", 6, 1000, 500, 15.0)
    e66, r66, y66 = summarize_effect("H066", events, "HIGH", 8, 1000, 500, 15.0)
    e67, r67, y67 = summarize_effect("H067", events, "LOW", 8, 1000, 500, 10.0)

    decay = full_decay_table(events)

    for row, state, max_intermediate in [
        (r64, "HIGH", 5),
        (r65, "LOW", 5),
        (r66, "HIGH", 7),
        (r67, "LOW", 7),
    ]:
        mids = decay[
            (decay["state"] == state)
            & (decay["minutes_ahead"].isin([15 * k for k in range(1, max_intermediate + 1)]))
        ]
        row["intermediate_all_positive"] = bool(
            len(mids) == max_intermediate
            and (mids["mean_effect_pct"] > 0).all()
        )

    r68 = h068_summary(events)

    summary = pd.DataFrame([r64, r65, r66, r67, r68])
    summary["q_value_bh"] = benjamini_hochberg(summary["p_value"])

    for h in ["H064", "H065", "H066", "H067"]:
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

    survival, durations = continuous_survival(events)
    landmarks = decay_landmarks(decay)

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    blocks.to_parquet(out / "blocks.parquet", index=False)
    events.to_parquet(out / "events.parquet", index=False)
    e64.to_parquet(out / "H064_events.parquet", index=False)
    e65.to_parquet(out / "H065_events.parquet", index=False)
    e66.to_parquet(out / "H066_events.parquet", index=False)
    e67.to_parquet(out / "H067_events.parquet", index=False)

    pd.concat([
        y64.assign(hypothesis="H064"),
        y65.assign(hypothesis="H065"),
        y66.assign(hypothesis="H066"),
        y67.assign(hypothesis="H067"),
    ], ignore_index=True).to_csv(out / "yearly.csv", index=False)

    decay.to_csv(out / "decay_curve_15_to_120.csv", index=False)
    survival.to_csv(out / "continuous_survival.csv", index=False)
    durations.to_csv(out / "continuous_durations.csv", index=False)
    landmarks.to_csv(out / "decay_landmarks.csv", index=False)
    summary.to_csv(out / "B10_SUMMARY.csv", index=False)

    print(summary.to_string(index=False))
    print("\nDecay curve")
    print(decay.to_string(index=False))
    print("\nContinuous survival")
    print(survival.to_string(index=False))
    print("\nDecay landmarks")
    print(landmarks.to_string(index=False))
    if len(durations):
        print("\nMedian continuous same-state minutes")
        print(
            durations.groupby("state", observed=True)["continuous_same_state_minutes"]
            .median()
            .to_string()
        )


if __name__ == "__main__":
    main()
