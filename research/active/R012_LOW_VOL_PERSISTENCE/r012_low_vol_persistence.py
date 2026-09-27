from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from src.research_utils import clustered_mean_stats, prepare_rth_features

REF=60
Q=0.10
START=601
CUTOFF=690

def add_features(data):
    d=data.copy().reset_index(drop=True)
    g=d.groupby("group_key",sort=False,observed=True)
    pc=g["close"].shift(1); pts=g["timestamp_et"].shift(1)
    exact=(d["timestamp_et"]-pts)==pd.Timedelta(minutes=1)
    d["r1"]=np.where(exact,np.log(d["close"]/pc),np.nan)
    lag=g["timestamp_et"].shift(30)
    hist=((d["timestamp_et"]-lag)==pd.Timedelta(minutes=30)).fillna(False)
    d["rv30"]=d.groupby("group_key",sort=False,observed=True)["r1"].rolling(30,min_periods=30).apply(
        lambda x: float(np.sqrt(np.square(x).sum())*10000),raw=True
    ).reset_index(level=0,drop=True)
    d["rv30"]=np.where(hist,d["rv30"],np.nan)

    future=np.full(len(d),np.nan)
    for idx in d.groupby("group_key",sort=False,observed=True).indices.values():
        pos=np.asarray(idx,dtype=int); n=len(pos)
        if n<=30: continue
        rr=d.loc[pos,"r1"].to_numpy(float)
        w=np.lib.stride_tricks.sliding_window_view(rr[1:],30)
        vals=np.sqrt(np.nansum(np.square(w),axis=1))*10000
        vals[~np.isfinite(w).all(axis=1)]=np.nan
        future[pos[:n-30]]=vals
    future[~d["exact_30m"].fillna(False).to_numpy(bool)]=np.nan
    d["future_rv30"]=future
    d["minute"]=d["timestamp_et"].dt.hour*60+d["timestamp_et"].dt.minute
    d.sort_values(["minute","timestamp_et"],inplace=True)
    by=d.groupby("minute",sort=False,observed=True)
    d["threshold"]=by["rv30"].transform(lambda s:s.shift(1).rolling(REF,min_periods=REF).quantile(Q))
    d["baseline_future"]=by["future_rv30"].transform(lambda s:s.shift(1).rolling(REF,min_periods=REF).mean())
    d.sort_values("timestamp_et",inplace=True)
    return d

def run(raw):
    f=prepare_rth_features(raw,"2024-09-01","2025-12-31",horizons=[30])
    f=add_features(f)
    m=f["minute"]
    cand=f[(m>=START)&(m<=CUTOFF)&f["rv30"].notna()&f["threshold"].notna()&
           f["baseline_future"].notna()&f["future_rv30"].notna()&
           (f["rv30"]<=f["threshold"])].copy()
    cand.sort_values(["group_key","timestamp_et"],inplace=True)
    e=cand.groupby("group_key",sort=False,observed=True).head(1).copy()
    y=pd.to_datetime(e["timestamp_et"],utc=True).dt.tz_convert("America/New_York").dt.year
    e=e[y==2025].copy()
    e["persistence_discount_pct"]=(1-e["future_rv30"]/e["baseline_future"])*100
    stats=clustered_mean_stats(e["persistence_discount_pct"],e["session_date"])
    s=pd.DataFrame([{
        "hypothesis":"H017","experiment":"R012","stage":"OOS_2025",
        "n":len(e),"sessions":e["session_date"].nunique(),
        "mean_effect":e["persistence_discount_pct"].mean(),
        "median_effect":e["persistence_discount_pct"].median(),
        **stats,
        "continuation_rate":np.nan,
        "years_positive":np.nan,"years_observed":1,
    }])
    s["passes_individual_gate"]=(s["n"]>=60)&(s["sessions"]>=60)&(s["mean_effect"]>=20)&(s["ci_low"]>0)
    return e,s

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir",default="results/B01/R012")
    a=p.parse_args(); raw=pd.read_parquet(a.input); e,s=run(raw)
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    e.to_parquet(out/"events.parquet",index=False); s.to_csv(out/"summary.csv",index=False)
    print(s.to_string(index=False))
if __name__=="__main__": main()
