from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from src.research_utils import clustered_mean_stats, prepare_rth_features

LOW=0.20; HIGH=0.80

def run(raw):
    f=prepare_rth_features(raw,"2020-01-01","2024-12-31",horizons=[30])
    sess=f.groupby("group_key",sort=False,observed=True).agg(
        session_date=("session_date","first"),year=("year","first"),contract=("contract","first"),
        first_ts=("timestamp_et","min"),last_ts=("timestamp_et","max"),
        rth_high=("high","max"),rth_low=("low","min"),rth_close=("close","last")
    ).sort_values("first_ts").reset_index()
    sess["clv"]=(sess["rth_close"]-sess["rth_low"])/(sess["rth_high"]-sess["rth_low"])
    sess["prev_clv"]=sess["clv"].shift(1); sess["prev_contract"]=sess["contract"].shift(1)
    sess.loc[sess["contract"]!=sess["prev_contract"],"prev_clv"]=np.nan

    rows=[]
    for key,g in f.groupby("group_key",sort=False,observed=True):
        g=g.sort_values("timestamp_et")
        if len(g)<30: continue
        first30=g.iloc[:30]
        mins=first30["timestamp_et"].dt.hour*60+first30["timestamp_et"].dt.minute
        if mins.iloc[0]!=571 or mins.iloc[-1]!=600: continue
        meta=sess[sess["group_key"]==key]
        if meta.empty or pd.isna(meta["prev_clv"].iloc[0]): continue
        clv=float(meta["prev_clv"].iloc[0])
        if not (clv>=HIGH or clv<=LOW): continue
        direction=1 if clv>=HIGH else -1
        entry=float(first30["open"].iloc[0]); exitpx=float(first30["close"].iloc[-1])
        ret=(exitpx/entry)-1
        rows.append({
          "timestamp_et":first30["timestamp_et"].iloc[0],"session_date":first30["session_date"].iloc[0],
          "year":int(first30["year"].iloc[0]),"contract":first30["contract"].iloc[0],
          "prev_clv":clv,"side":"LONG" if direction>0 else "SHORT",
          "directional_30m_bps":direction*ret*10000
        })
    e=pd.DataFrame(rows)
    stats=clustered_mean_stats(e["directional_30m_bps"],e["session_date"])
    yearly=e.groupby("year",observed=True)["directional_30m_bps"].mean()
    s=pd.DataFrame([{
      "hypothesis":"H020","experiment":"R015","stage":"DEV_2020_2024",
      "n":len(e),"sessions":e["session_date"].nunique(),
      "mean_effect":e["directional_30m_bps"].mean(),"median_effect":e["directional_30m_bps"].median(),
      **stats,"continuation_rate":float((e["directional_30m_bps"]>0).mean()) if len(e) else np.nan,
      "years_positive":int((yearly>0).sum()),"years_observed":int(yearly.shape[0]),
    }])
    s["passes_individual_gate"]=(s["n"]>=400)&(s["sessions"]>=400)&(s["mean_effect"]>=1)&(s["ci_low"]>0)&(s["years_observed"]==5)&(s["years_positive"]>=4)
    return e,s,yearly.reset_index(name="mean_effect")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir",default="results/B01/R015"); a=p.parse_args()
    raw=pd.read_parquet(a.input); e,s,y=run(raw); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    e.to_parquet(out/"events.parquet",index=False); s.to_csv(out/"summary.csv",index=False); y.to_csv(out/"yearly.csv",index=False); print(s.to_string(index=False))
if __name__=="__main__": main()
