#!/usr/bin/env python3
from __future__ import annotations

import json, sys
from collections import defaultdict, deque
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research.mes_parameter_walkforward_p1 import load_development, build_signal_trades
from research.archive.B12.b12_strategy_architecture import prepare_rth
from research.archive.B13.b13_high_directional_triggers import block_features
from src.research_utils import rth_mask

OUT=ROOT/"results/r072_streaming_engine_emulation"
REF_N=60
WICK=.50
CUTOFF=660

def quantile_linear_last(vals,n,p):
    a=np.sort(np.asarray(vals[-n:],dtype=float))
    idx=(len(a)-1)*p
    lo=int(np.floor(idx)); hi=int(np.ceil(idx))
    if lo==hi:return float(a[lo])
    w=idx-lo
    return float(a[lo]*(1-w)+a[hi]*w)

def build_streaming_h017(raw):
    d=raw[rth_mask(raw.timestamp_et)].copy()
    d["session_date"]=d.timestamp_et.dt.date.astype(str)
    d["group_key"]=d.session_date+"|"+d.contract.astype(str)
    d.sort_values(["group_key","timestamp_et"],inplace=True)

    rv_rows=[]
    for key,g in d.groupby("group_key",sort=False,observed=True):
        g=g.sort_values("timestamp_et").reset_index(drop=True)
        ret=np.full(len(g),np.nan)
        for i in range(1,len(g)):
            if g.timestamp_et.iloc[i]-g.timestamp_et.iloc[i-1]==pd.Timedelta(minutes=1):
                ret[i]=np.log(float(g.close.iloc[i])/float(g.close.iloc[i-1]))
        for i in range(30,len(g)):
            if g.timestamp_et.iloc[i]-g.timestamp_et.iloc[i-30]!=pd.Timedelta(minutes=30):
                continue
            z=ret[i-29:i+1]
            if len(z)!=30 or not np.isfinite(z).all():
                continue
            rv=float(np.sqrt(np.square(z).sum())*10000)
            ts=g.timestamp_et.iloc[i]
            rv_rows.append({
                "group_key":key,
                "session_date":g.session_date.iloc[i],
                "timestamp_et":ts,
                "minute":int(ts.hour*60+ts.minute),
                "rv30":rv,
            })

    rv=pd.DataFrame(rv_rows).sort_values(["minute","timestamp_et"]).reset_index(drop=True)
    histories=defaultdict(list)
    thresholds=[]
    for r in rv.itertuples(index=False):
        hist=histories[int(r.minute)]
        q=np.nan if len(hist)<REF_N else quantile_linear_last(hist,REF_N,.10)
        thresholds.append(q)
        hist.append(float(r.rv30))
    rv["q10"]=thresholds
    rv.sort_values(["group_key","timestamp_et"],inplace=True)

    eligible=rv[
        rv.minute.between(601,690)
        & rv.q10.notna()
        & (rv.rv30<=rv.q10)
    ].copy()
    first=eligible.groupby("group_key",sort=False,observed=True).head(1)
    return dict(zip(first.group_key,first.timestamp_et))

def streaming_signals(raw,groups):
    h017=build_streaming_h017(raw)

    # chronological complete-session order
    ordered=sorted(groups.items(),key=lambda kv: kv[1].timestamp_et.iloc[0])
    hist={i:[] for i in range(7)}
    rows=[]

    for key,g0 in ordered:
        g=g0.sort_values("timestamp_et").reset_index(drop=True)
        htime=h017.get(key,pd.NaT)
        session_candidates=[]
        today_ranges={}

        for bid in range(7):
            start=bid*15; end=start+15
            b=g.iloc[start:end]
            if len(b)!=15:continue
            op=float(b.open.iloc[0]); cl=float(b.close.iloc[-1])
            hi=float(b.high.max()); lo=float(b.low.min()); rng=hi-lo
            if cl<=0 or rng<=0:continue

            rbps=(hi-lo)/cl*10000
            today_ranges[bid]=rbps

            if len(hist[bid])<REF_N:
                continue
            q20=quantile_linear_last(hist[bid],REF_N,.20)
            q80=quantile_linear_last(hist[bid],REF_N,.80)
            if rbps<=q20:
                state="LOW"
            elif rbps>=q80:
                state="HIGH"
            else:
                state="NORMAL"

            end_ts=b.timestamp_et.iloc[-1]
            engine=state
            if pd.notna(htime) and end_ts>=htime and end_ts<=htime+pd.Timedelta(minutes=30):
                engine="LOW"

            upper=(hi-max(op,cl))/rng
            lower=(min(op,cl)-lo)/rng
            direction=0
            minute=int(end_ts.hour*60+end_ts.minute)
            if engine=="HIGH" and minute<=CUTOFF:
                if upper>=WICK and cl<op:
                    direction=1
                elif lower>=WICK and cl>op:
                    direction=-1

            if direction:
                signal_pos=end-1
                if signal_pos+1>=len(g):continue
                nxt=g.iloc[signal_pos+1]
                if nxt.timestamp_et-end_ts!=pd.Timedelta(minutes=1):continue
                session_candidates.append({
                    "group_key":key,
                    "session_date":str(g.session_date.iloc[0]),
                    "block_id":bid,
                    "signal_ts":end_ts,
                    "direction":direction,
                    "entry_price":float(nxt.open),
                    "q20":q20,"q80":q80,"range15_bps":rbps,
                    "h017_time":htime,
                })

        # Update state histories only AFTER today's classifications are complete.
        for bid,v in today_ranges.items():
            hist[bid].append(v)

        if session_candidates:
            rows.append(min(session_candidates,key=lambda z:z["signal_ts"]))

    return pd.DataFrame(rows).sort_values("signal_ts").reset_index(drop=True)

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)

    stream=streaming_signals(raw,groups)
    vector=build_signal_trades(block_features(raw,groups),groups,WICK,CUTOFF).copy()

    ref=pd.DataFrame({
        "group_key":vector.group_key,
        "session_date":vector.session_date.astype(str),
        "block_id":vector.block_id.astype(int),
        "signal_ts":pd.to_datetime(vector.entry_clock_et),
        "direction":vector.direction.astype(int),
        "entry_price":vector.entry_price.astype(float),
    })

    m=ref.merge(
        stream,
        on="group_key",
        how="outer",
        suffixes=("_vec","_stream"),
        indicator=True,
    )
    both=m[m._merge=="both"].copy()
    both["block_match"]=both.block_id_vec.eq(both.block_id_stream)
    both["time_match"]=pd.to_datetime(both.signal_ts_vec).eq(pd.to_datetime(both.signal_ts_stream))
    both["direction_match"]=both.direction_vec.eq(both.direction_stream)
    both["entry_match"]=(both.entry_price_vec-both.entry_price_stream).abs()<=1e-9

    report={
        "vector_signals":int(len(ref)),
        "streaming_signals":int(len(stream)),
        "common_sessions":int(len(both)),
        "vector_only":int((m._merge=="left_only").sum()),
        "streaming_only":int((m._merge=="right_only").sum()),
        "block_match_rate":float(both.block_match.mean()) if len(both) else 0,
        "time_match_rate":float(both.time_match.mean()) if len(both) else 0,
        "direction_match_rate":float(both.direction_match.mean()) if len(both) else 0,
        "entry_price_match_rate":float(both.entry_match.mean()) if len(both) else 0,
    }
    report["exact_engine_signal_parity"]=bool(
        report["vector_signals"]==report["streaming_signals"]
        and report["vector_only"]==0
        and report["streaming_only"]==0
        and all(report[k]==1.0 for k in [
            "block_match_rate","time_match_rate","direction_match_rate","entry_price_match_rate"
        ])
    )

    OUT.mkdir(parents=True,exist_ok=True)
    stream.to_csv(OUT/"R072_STREAMING_SIGNALS.csv",index=False)
    m.to_csv(OUT/"R072_STREAMING_VS_VECTOR.csv",index=False)
    (OUT/"R072_STREAMING_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

    bad=both[~(both.block_match&both.time_match&both.direction_match&both.entry_match)]
    if len(bad):
        print("\nFIRST COMMON MISMATCHES")
        print(bad.head(20).to_string(index=False))
    extra=m[m._merge!="both"]
    if len(extra):
        print("\nONLY-ONE-SIDE")
        print(extra.head(30).to_string(index=False))

if __name__=="__main__":
    main()
