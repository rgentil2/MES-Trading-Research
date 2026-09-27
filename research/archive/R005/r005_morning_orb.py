from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import add_forward_extrema, benjamini_hochberg, clustered_mean_stats, prepare_rth_features

ENTRY_CUTOFF_MINUTE = 11 * 60 + 30


def build_events(features):
    data = features.copy()
    opening = data[data["bar_index"] < 15].copy()
    stats = opening.groupby("group_key", sort=False, observed=True).agg(
        or_high=("high", "max"), or_low=("low", "min"), or_count=("timestamp_et", "size"),
        or_first_ts=("timestamp_et", "min"), or_last_ts=("timestamp_et", "max")
    ).reset_index()
    first_minute = stats["or_first_ts"].dt.hour * 60 + stats["or_first_ts"].dt.minute
    last_minute = stats["or_last_ts"].dt.hour * 60 + stats["or_last_ts"].dt.minute
    stats["or_valid"] = (
        (stats["or_count"] == 15)
        & (first_minute == 9 * 60 + 31)
        & (last_minute == 9 * 60 + 45)
        & ((stats["or_last_ts"] - stats["or_first_ts"]) == pd.Timedelta(minutes=14))
    )
    data = data.merge(stats[["group_key","or_high","or_low","or_valid"]], on="group_key", how="left", validate="many_to_one")
    outside = (data["close"] > data["or_high"]) | (data["close"] < data["or_low"])
    candidates = data[data["or_valid"].fillna(False) & (data["bar_index"] >= 15) & outside].copy()
    if candidates.empty:
        return candidates
    candidates.sort_values(["group_key","timestamp_et"], inplace=True)
    first = candidates.groupby("group_key", sort=False, observed=True).head(1).copy()
    minute = first["timestamp_et"].dt.hour * 60 + first["timestamp_et"].dt.minute
    first = first[minute <= ENTRY_CUTOFF_MINUTE].copy()
    first["breakout"] = np.where(first["close"] > first["or_high"], "UPPER", "LOWER")
    first["direction"] = np.where(first["breakout"] == "UPPER", 1, -1)
    first = first[first["exact_30m"].fillna(False) & first["fwd_30m"].notna()].copy()
    first["directional_30m_bps"] = first["direction"] * first["fwd_30m"] * 10000.0
    first["or_width_bps"] = (first["or_high"] - first["or_low"]) / first["close"] * 10000.0
    long_side = first["direction"] == 1
    first["mfe_30m_bps"] = np.where(long_side, (first["future_high_30m"]/first["close"]-1)*10000, (1-first["future_low_30m"]/first["close"])*10000)
    first["mae_30m_bps"] = np.where(long_side, (first["future_low_30m"]/first["close"]-1)*10000, (1-first["future_high_30m"]/first["close"])*10000)
    first["breakout_time_et"] = first["timestamp_et"].dt.strftime("%H:%M")
    keep=["timestamp_et","session_date","year","contract","group_key","breakout","direction","breakout_time_et","close","or_high","or_low","or_width_bps","fwd_30m","directional_30m_bps","mfe_30m_bps","mae_30m_bps"]
    return first[keep].sort_values("timestamp_et").reset_index(drop=True)


def summarize(events):
    primary_rows=[]; yearly_rows=[]
    for breakout,hypothesis in [("UPPER","H009"),("LOWER","H010")]:
        g=events[events["breakout"]==breakout].copy()
        y=g["directional_30m_bps"]
        robust=clustered_mean_stats(y,g["session_date"])
        yearly=g.groupby("year", observed=True).agg(
            n=("directional_30m_bps","size"),
            sessions=("session_date","nunique"),
            mean_directional_bps=("directional_30m_bps","mean"),
            continuation_rate=("directional_30m_bps",lambda s: float((s>0).mean()))
        ).reset_index()
        yearly["hypothesis"]=hypothesis; yearly["breakout"]=breakout
        yearly_rows.append(yearly)
        primary_rows.append({
            "hypothesis":hypothesis,"breakout":breakout,"n":int(len(g)),"sessions":int(g["session_date"].nunique()),
            "mean_directional_bps":float(y.mean()) if len(y) else np.nan,
            "median_directional_bps":float(y.median()) if len(y) else np.nan,
            "continuation_rate":float((y>0).mean()) if len(y) else np.nan,
            "mean_mfe_30m_bps":float(g["mfe_30m_bps"].mean()) if len(g) else np.nan,
            "mean_mae_30m_bps":float(g["mae_30m_bps"].mean()) if len(g) else np.nan,
            "mean_or_width_bps":float(g["or_width_bps"].mean()) if len(g) else np.nan,
            **robust
        })
    primary=pd.DataFrame(primary_rows)
    yearly=pd.concat(yearly_rows,ignore_index=True)
    primary["q_value"]=benjamini_hochberg(primary["p_value"])
    signs=yearly.assign(positive=lambda x:x["mean_directional_bps"]>0).groupby("hypothesis",observed=True).agg(
        years_positive=("positive","sum"),years_observed=("year","nunique")
    ).reset_index()
    primary=primary.merge(signs,on="hypothesis",how="left")
    primary["passes_development_gate"]=(
        (primary["n"]>=500)&(primary["sessions"]>=500)&(primary["q_value"]<0.05)&
        (primary["ci_low"]>0)&(primary["mean_directional_bps"]>=1.0)&
        (primary["years_observed"]==5)&(primary["years_positive"]>=4)
    )
    return primary,yearly


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--start",default="2020-01-01"); p.add_argument("--end",default="2024-12-31")
    p.add_argument("--output-dir",default="results/R005/development_2020_2024")
    a=p.parse_args()
    raw=pd.read_parquet(a.input)
    feat=prepare_rth_features(raw,a.start,a.end,horizons=[30])
    feat=add_forward_extrema(feat,horizons=[30])
    events=build_events(feat); primary,yearly=summarize(events)
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    events.to_parquet(out/"events.parquet",index=False,compression="zstd")
    primary.to_csv(out/"primary_hypotheses.csv",index=False)
    yearly.to_csv(out/"yearly_stability.csv",index=False)
    print(primary.to_string(index=False))
    print(f"Eligible sessions: {len(events):,}")


if __name__=="__main__":
    main()
