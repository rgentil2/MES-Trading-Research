from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import benjamini_hochberg, clustered_mean_stats, prepare_rth_features

REF=60
STREAK_Q=0.60
OVEREXT_Q=0.80
HIGH_RANGE_Q=0.80
LOW_RANGE_Q=0.20


def build_sessions(raw):
    rth=prepare_rth_features(raw,"2020-01-01","2025-12-31",horizons=[30])
    rows=[]
    for key,g in rth.groupby("group_key",sort=False,observed=True):
        g=g.sort_values("timestamp_et").reset_index(drop=True)
        if len(g)!=390:
            continue
        mins=g["timestamp_et"].dt.hour*60+g["timestamp_et"].dt.minute
        if int(mins.iloc[0])!=571 or int(mins.iloc[-1])!=960:
            continue
        year=int(g["year"].iloc[0])
        if year<2020 or year>2025:
            continue

        op=float(g["open"].iloc[0]); cl=float(g["close"].iloc[-1])
        hi=float(g["high"].max()); lo=float(g["low"].min())
        first30=g.iloc[:30]
        close1000=float(first30["close"].iloc[-1])
        if op<=0 or cl<=0 or hi<=lo or close1000<=0:
            continue

        rows.append({
            "group_key":key,
            "session_date":g["session_date"].iloc[0],
            "year":year,
            "contract":g["contract"].iloc[0],
            "first_ts":g["timestamp_et"].iloc[0],
            "rth_open":op,
            "rth_close":cl,
            "rth_high":hi,
            "rth_low":lo,
            "day_return":float(np.log(cl/op)),
            "range_bps":float((hi-lo)/cl*10000.0),
            "opening_return_bps":float(np.log(close1000/op)*10000.0),
            "opening_range_bps":float((first30["high"].max()-first30["low"].min())/op*10000.0),
        })

    s=pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)

    # require same-contract rolling windows
    for lag in range(1,6):
        s[f"contract_lag{lag}"]=s["contract"].shift(lag)
        s[f"return_lag{lag}"]=s["day_return"].shift(lag)
        s[f"open_lag{lag}"]=s["rth_open"].shift(lag)
        s[f"close_lag{lag}"]=s["rth_close"].shift(lag)
        s[f"high_lag{lag}"]=s["rth_high"].shift(lag)
        s[f"low_lag{lag}"]=s["rth_low"].shift(lag)
        s[f"range_lag{lag}"]=s["range_bps"].shift(lag)

    same3=np.ones(len(s),dtype=bool)
    for lag in range(1,4):
        same3 &= (s["contract"]==s[f"contract_lag{lag}"]).to_numpy()
    same5=np.ones(len(s),dtype=bool)
    for lag in range(1,6):
        same5 &= (s["contract"]==s[f"contract_lag{lag}"]).to_numpy()

    s["same3"]=same3
    s["same5"]=same5

    # Three-day streak
    r1=s["return_lag1"]; r2=s["return_lag2"]; r3=s["return_lag3"]
    same_sign=((r1>0)&(r2>0)&(r3>0))|((r1<0)&(r2<0)&(r3<0))
    s["streak3_sign"]=np.where(same_sign,np.sign(r1),0)
    s["streak3_mag"]=np.where(
        s["same3"]&same_sign,
        (r1+r2+r3).abs(),
        np.nan
    )

    streak_idx=s.index[s["streak3_mag"].notna()]
    streak_vals=s.loc[streak_idx,"streak3_mag"]
    s["streak3_q60"]=np.nan
    s.loc[streak_idx,"streak3_q60"]=(
        streak_vals.shift(1).rolling(REF,min_periods=REF).quantile(STREAK_Q)
    )

    # Five-day breakout levels, total return, avg range.
    highs=s[[f"high_lag{i}" for i in range(1,6)]]
    lows=s[[f"low_lag{i}" for i in range(1,6)]]
    ranges=s[[f"range_lag{i}" for i in range(1,6)]]

    s["prior5_high"]=np.where(s["same5"],highs.max(axis=1),np.nan)
    s["prior5_low"]=np.where(s["same5"],lows.min(axis=1),np.nan)
    s["avg_range5"]=np.where(s["same5"],ranges.mean(axis=1),np.nan)

    # total return from open 5 sessions ago to close previous session
    s["return5d"]=np.where(
        s["same5"],
        np.log(s["close_lag1"]/s["open_lag5"]),
        np.nan
    )

    # rolling thresholds on eligible prior observations
    for col,q,out in [
        ("return5d",OVEREXT_Q,"return5d_q80"),
        ("avg_range5",HIGH_RANGE_Q,"avg_range5_q80"),
        ("avg_range5",LOW_RANGE_Q,"avg_range5_q20"),
    ]:
        idx=s.index[s[col].notna()]
        vals=s.loc[idx,col].abs() if col=="return5d" else s.loc[idx,col]
        s[out]=np.nan
        s.loc[idx,out]=vals.shift(1).rolling(REF,min_periods=REF).quantile(q)

    s["opening_range_baseline"]=s["opening_range_bps"].shift(1).rolling(REF,min_periods=REF).mean()
    return s


def summarize(h,e,metric,min_n,min_mean):
    y=e[metric]
    st=clustered_mean_stats(y,e["session_date"])
    yearly=e.groupby("year",observed=True)[metric].mean().reset_index(name="mean_effect")
    side=e.groupby("signal_side",observed=True).agg(
        n=(metric,"size"),
        mean_effect=(metric,"mean"),
        positive_rate=(metric,lambda z:float((z>0).mean())),
    ).reset_index() if "signal_side" in e.columns else pd.DataFrame()

    row={
        "hypothesis":h,
        "n":int(len(e)),
        "sessions":int(e["session_date"].nunique()),
        "mean_effect":float(y.mean()) if len(y) else np.nan,
        "median_effect":float(y.median()) if len(y) else np.nan,
        "positive_rate":float((y>0).mean()) if len(y) else np.nan,
        **st,
        "years_positive":int((yearly["mean_effect"]>0).sum()),
        "years_observed":int(yearly["year"].nunique()),
        "min_n_gate":min_n,
        "min_mean_gate":min_mean,
    }
    return row,yearly,side


def h054(s):
    e=s[
        s["streak3_mag"].notna()&
        s["streak3_q60"].notna()&
        (s["streak3_mag"]>=s["streak3_q60"])
    ].copy()
    e["signal_side"]=np.where(e["streak3_sign"]>0,"BULL_STREAK","BEAR_STREAK")
    e["effect"]=-e["streak3_sign"]*e["opening_return_bps"]
    return e,*summarize("H054",e,"effect",150,1.0)


def h055(s):
    bull=s["same5"]&(s["rth_open"]>s["prior5_high"])
    bear=s["same5"]&(s["rth_open"]<s["prior5_low"])
    e=s[bull|bear].copy()
    e["direction"]=np.where(bull.loc[e.index],1,-1)
    e["signal_side"]=np.where(e["direction"]>0,"BREAK_HIGH","BREAK_LOW")
    e["effect"]=e["direction"]*e["opening_return_bps"]
    return e,*summarize("H055",e,"effect",150,1.0)


def h056(s):
    e=s[
        s["return5d"].notna()&
        s["return5d_q80"].notna()&
        (s["return5d"].abs()>=s["return5d_q80"])&
        (s["return5d"]!=0)
    ].copy()
    e["signal_side"]=np.where(e["return5d"]>0,"UP_EXTREME","DOWN_EXTREME")
    e["effect"]=-np.sign(e["return5d"])*e["opening_return_bps"]
    return e,*summarize("H056",e,"effect",200,1.0)


def h057(s):
    e=s[
        s["avg_range5"].notna()&
        s["avg_range5_q80"].notna()&
        s["opening_range_baseline"].notna()&
        (s["opening_range_baseline"]>0)&
        (s["avg_range5"]>=s["avg_range5_q80"])
    ].copy()
    e["signal_side"]="HIGH_RANGE5"
    e["effect"]=(e["opening_range_bps"]/e["opening_range_baseline"]-1)*100
    return e,*summarize("H057",e,"effect",200,10.0)


def h058(s):
    e=s[
        s["avg_range5"].notna()&
        s["avg_range5_q20"].notna()&
        s["opening_range_baseline"].notna()&
        (s["opening_range_baseline"]>0)&
        (s["avg_range5"]<=s["avg_range5_q20"])
    ].copy()
    e["signal_side"]="LOW_RANGE5"
    e["effect"]=(1-e["opening_range_bps"]/e["opening_range_baseline"])*100
    return e,*summarize("H058",e,"effect",200,10.0)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir",default="results/B08")
    a=p.parse_args()

    s=build_sessions(pd.read_parquet(a.input))
    results=[]; events=[]; yearly_parts=[]; side_parts=[]
    for h,fn in [("H054",h054),("H055",h055),("H056",h056),("H057",h057),("H058",h058)]:
        e,row,y,side=fn(s)
        results.append(row); events.append((h,e))
        y["hypothesis"]=h; yearly_parts.append(y)
        if len(side):
            side["hypothesis"]=h; side_parts.append(side)

    summary=pd.DataFrame(results)
    summary["q_value_bh"]=benjamini_hochberg(summary["p_value"])
    summary["passes_individual_gate"]=(
        (summary["n"]>=summary["min_n_gate"])&
        (summary["sessions"]>=summary["min_n_gate"])&
        (summary["mean_effect"]>=summary["min_mean_gate"])&
        (summary["ci_low"]>0)&
        (summary["years_observed"]==6)&
        (summary["years_positive"]>=4)
    )
    summary["passes_block_gate"]=summary["passes_individual_gate"]&(summary["q_value_bh"]<0.05)

    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    s.to_parquet(out/"session_features.parquet",index=False)
    for h,e in events:
        e.to_parquet(out/f"{h}_events.parquet",index=False)
    pd.concat(yearly_parts,ignore_index=True).to_csv(out/"yearly.csv",index=False)
    if side_parts:
        pd.concat(side_parts,ignore_index=True).to_csv(out/"side_breakdown.csv",index=False)
    summary.to_csv(out/"B08_SUMMARY.csv",index=False)

    print(summary.to_string(index=False))
    if side_parts:
        print("\nSide breakdown")
        print(pd.concat(side_parts,ignore_index=True).to_string(index=False))


if __name__=="__main__":
    main()
