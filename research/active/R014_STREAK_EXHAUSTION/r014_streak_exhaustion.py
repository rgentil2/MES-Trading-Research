from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from src.research_utils import clustered_mean_stats, prepare_rth_features

REF=60; Q=0.80; START=576; CUTOFF=690

def add_features(d):
    d=d.copy().reset_index(drop=True); g=d.groupby("group_key",sort=False,observed=True)
    pc=g["close"].shift(1); pts=g["timestamp_et"].shift(1)
    exact1=(d["timestamp_et"]-pts)==pd.Timedelta(minutes=1)
    d["r1"]=np.where(exact1,np.log(d["close"]/pc),np.nan)
    lc=g["close"].shift(5); lt=g["timestamp_et"].shift(5)
    exact5=((d["timestamp_et"]-lt)==pd.Timedelta(minutes=5)).fillna(False)
    d["r5"]=np.where(exact5,np.log(d["close"]/lc),np.nan)
    signs=np.sign(d["r1"])
    def same_sign(x):
        x=np.asarray(x)
        return float((np.all(x>0) or np.all(x<0)))
    d["same5"]=d.groupby("group_key",sort=False,observed=True)["r1"].rolling(5,min_periods=5).apply(same_sign,raw=True).reset_index(level=0,drop=True)
    d["same5"]=np.where(exact5,d["same5"],0)
    d["minute"]=d["timestamp_et"].dt.hour*60+d["timestamp_et"].dt.minute
    d.sort_values(["minute","timestamp_et"],inplace=True)
    d["thr"]=d.groupby("minute",sort=False,observed=True)["r5"].transform(
        lambda s:s.abs().shift(1).rolling(REF,min_periods=REF).quantile(Q))
    d.sort_values("timestamp_et",inplace=True); return d

def run(raw):
    f=prepare_rth_features(raw,"2020-01-01","2024-12-31",horizons=[15]); f=add_features(f); m=f["minute"]
    c=f[(m>=START)&(m<=CUTOFF)&(f["same5"]==1)&f["thr"].notna()&
        (f["r5"].abs()>=f["thr"])&f["exact_15m"].fillna(False)&f["fwd_15m"].notna()].copy()
    c.sort_values(["group_key","timestamp_et"],inplace=True)
    e=c.groupby("group_key",sort=False,observed=True).head(1).copy()
    e["reversion_15m_bps"]=-np.sign(e["r5"])*e["fwd_15m"]*10000
    stats=clustered_mean_stats(e["reversion_15m_bps"],e["session_date"])
    yearly=e.groupby("year",observed=True)["reversion_15m_bps"].mean()
    s=pd.DataFrame([{
      "hypothesis":"H019","experiment":"R014","stage":"DEV_2020_2024",
      "n":len(e),"sessions":e["session_date"].nunique(),
      "mean_effect":e["reversion_15m_bps"].mean(),"median_effect":e["reversion_15m_bps"].median(),
      **stats,"continuation_rate":float((e["reversion_15m_bps"]>0).mean()) if len(e) else np.nan,
      "years_positive":int((yearly>0).sum()),"years_observed":int(yearly.shape[0]),
    }])
    s["passes_individual_gate"]=(s["n"]>=300)&(s["sessions"]>=300)&(s["mean_effect"]>=1)&(s["ci_low"]>0)&(s["years_observed"]==5)&(s["years_positive"]>=4)
    return e,s,yearly.reset_index(name="mean_effect")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir",default="results/B01/R014"); a=p.parse_args()
    raw=pd.read_parquet(a.input); e,s,y=run(raw); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    e.to_parquet(out/"events.parquet",index=False); s.to_csv(out/"summary.csv",index=False); y.to_csv(out/"yearly.csv",index=False); print(s.to_string(index=False))
if __name__=="__main__": main()
