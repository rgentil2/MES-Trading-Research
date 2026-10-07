#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development
from research.archive.B12.b12_strategy_architecture import prepare_rth
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_dynamic_outputs

OUT=ROOT/"results/r072_engine_reference"
WICK=0.50
CUTOFF=660

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    dyn=build_dynamic_outputs(raw).copy()
    dyn=dyn[dyn["block_id"].between(0,6)].copy()

    rows=[]
    for r in dyn.itertuples(index=False):
        g=groups.get(r.group_key)
        if g is None:
            continue
        start=int(r.block_id)*15
        end=start+15
        b=g.iloc[start:end]
        if len(b)!=15:
            continue

        op=float(b.open.iloc[0])
        cl=float(b.close.iloc[-1])
        hi=float(b.high.max())
        lo=float(b.low.min())
        rng=hi-lo
        if rng<=0:
            continue

        upper=(hi-max(op,cl))/rng
        lower=(min(op,cl)-lo)/rng
        end_ts=b.timestamp_et.iloc[-1]
        minute=int(end_ts.hour*60+end_ts.minute)

        direction=0
        if str(r.engine_state)=="HIGH" and minute<=CUTOFF:
            if upper>=WICK and cl<op:
                direction=1
            elif lower>=WICK and cl>op:
                direction=-1

        rows.append({
            "group_key":r.group_key,
            "session_date":str(r.session_date),
            "year":int(r.year),
            "contract":str(r.contract),
            "block_id":int(r.block_id),
            "block_end_et":end_ts,
            "block_end_minute":minute,
            "range15_bps":float(r.range15_bps),
            "q20":float(r.q20) if pd.notna(r.q20) else np.nan,
            "q80":float(r.q80) if pd.notna(r.q80) else np.nan,
            "raw_state":r.state,
            "engine_state":r.engine_state,
            "engine_stage":r.engine_stage,
            "h017_time":r.h017_time,
            "block_open":op,
            "block_high":hi,
            "block_low":lo,
            "block_close":cl,
            "upper_wick_ratio":upper,
            "lower_wick_ratio":lower,
            "r072_candidate_direction":direction,
        })

    x=pd.DataFrame(rows).sort_values(["session_date","block_id"]).reset_index(drop=True)
    x["r072_first_signal"]=False
    for key,g in x[x.r072_candidate_direction!=0].groupby("group_key",sort=False):
        idx=g.sort_values("block_end_et").index[0]
        x.loc[idx,"r072_first_signal"]=True

    OUT.mkdir(parents=True,exist_ok=True)
    x.to_csv(OUT/"R072_ENGINE_BLOCK_REFERENCE.csv",index=False)
    x[x.r072_first_signal].to_csv(OUT/"R072_ENGINE_FIRST_SIGNALS_PRE_NEWS.csv",index=False)

    print("blocks:",len(x))
    print("HIGH blocks:",int((x.engine_state=="HIGH").sum()))
    print("pre-news first R072 signals:",int(x.r072_first_signal.sum()))
    print(x[x.r072_first_signal][[
        "session_date","block_id","block_end_et","engine_state",
        "upper_wick_ratio","lower_wick_ratio","r072_candidate_direction"
    ]].head(20).to_string(index=False))

if __name__=="__main__":
    main()
