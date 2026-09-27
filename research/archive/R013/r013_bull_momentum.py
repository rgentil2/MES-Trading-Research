from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from src.research_utils import clustered_mean_stats, prepare_rth_features

REF=60; Q=0.90; ER_MIN=0.70; START=586; CUTOFF=690

def add_features(d):
    d=d.copy().reset_index(drop=True); g=d.groupby("group_key",sort=False,observed=True)
    pc=g["close"].shift(1); pts=g["timestamp_et"].shift(1)
    exact1=(d["timestamp_et"]-pts)==pd.Timedelta(minutes=1)
    d["r1"]=np.where(exact1,np.log(d["close"]/pc),np.nan)
    lc=g["close"].shift(15); lt=g["timestamp_et"].shift(15)
    exact15=((d["timestamp_et"]-lt)==pd.Timedelta(minutes=15)).fillna(False)
    d["r15"]=np.where(exact15,np.log(d["close"]/lc),np.nan)
    path=d.groupby("group_key",sort=False,observed=True)["r1"].rolling(15,min_periods=15).apply(
        lambda x:float(np.abs(x).sum()),raw=True).reset_index(level=0,drop=True)
    d["er15"]=np.where((exact15)&(path>0),np.abs(d["r15"])/path,np.nan)
    d["minute"]=d["timestamp_et"].dt.hour*60+d["timestamp_et"].dt.minute
    d.sort_values(["minute","timestamp_et"],inplace=True)
    d["thr"]=d.groupby("minute",sort=False,observed=True)["r15"].transform(
        lambda s:s.abs().shift(1).rolling(REF,min_periods=REF).quantile(Q))
    d.sort_values("timestamp_et",inplace=True); return d

def run(raw):
    f=prepare_rth_features(raw,"2024-09-01","2025-12-31",horizons=[15]); f=add_features(f); m=f["minute"]
    c=f[(m>=START)&(m<=CUTOFF)&(f["r15"]>0)&(f["r15"].abs()>=f["thr"])&
        (f["er15"]>=ER_MIN)&f["fwd_15m"].notna()&f["exact_15m"].fillna(False)].copy()
    c.sort_values(["group_key","timestamp_et"],inplace=True)
    e=c.groupby("group_key",sort=False,observed=True).head(1).copy()
    yr=pd.to_datetime(e["timestamp_et"],utc=True).dt.tz_convert("America/New_York").dt.year
    e=e[yr==2025].copy(); e["directional_15m_bps"]=e["fwd_15m"]*10000
    stats=clustered_mean_stats(e["directional_15m_bps"],e["session_date"])
    cont=float((e["directional_15m_bps"]>0).mean()) if len(e) else np.nan
    s=pd.DataFrame([{
      "hypothesis":"H018","experiment":"R013","stage":"OOS_2025",
      "n":len(e),"sessions":e["session_date"].nunique(),
      "mean_effect":e["directional_15m_bps"].mean(),"median_effect":e["directional_15m_bps"].median(),
      **stats,"continuation_rate":cont,"years_positive":np.nan,"years_observed":1,
    }])
    s["passes_individual_gate"]=(s["n"]>=30)&(s["sessions"]>=30)&(s["mean_effect"]>=1)&(s["ci_low"]>0)&(s["continuation_rate"]>0.5)
    return e,s

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir",default="results/B01/R013"); a=p.parse_args()
    raw=pd.read_parquet(a.input); e,s=run(raw); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    e.to_parquet(out/"events.parquet",index=False); s.to_csv(out/"summary.csv",index=False); print(s.to_string(index=False))
if __name__=="__main__": main()
