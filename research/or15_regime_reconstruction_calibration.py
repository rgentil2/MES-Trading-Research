#!/usr/bin/env python3
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np, pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.mes_parameter_walkforward_p1 import load_development
from research.archive.B12.b12_strategy_architecture import prepare_rth

def wilder(s,n=14):
    x=s.to_numpy(float); out=np.full(len(x),np.nan)
    if len(x)<n:return pd.Series(out,index=s.index)
    out[n-1]=np.mean(x[:n])
    for i in range(n,len(x)):
        out[i]=(out[i-1]*(n-1)+x[i])/n
    return pd.Series(out,index=s.index)

def daily(groups):
    rows=[]
    for k,g in groups.items():
        g=g.sort_values("timestamp_et")
        rows.append(dict(group_key=k,session_date=str(g.session_date.iloc[0]),year=int(g.year.iloc[0]),
                         first_ts=g.timestamp_et.iloc[0],open=float(g.open.iloc[0]),
                         high=float(g.high.max()),low=float(g.low.min()),close=float(g.close.iloc[-1])))
    d=pd.DataFrame(rows).sort_values("first_ts").reset_index(drop=True)
    pc=d.close.shift(1)
    d["tr"]=pd.concat([(d.high-d.low),(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
    d["atr_sma"]=d.tr.rolling(14,min_periods=14).mean()
    d["atr_wilder"]=wilder(d.tr,14)
    diff=d.close.diff().abs()
    d["er10"]=(d.close-d.close.shift(10)).abs()/diff.rolling(10,min_periods=10).sum()
    return d

def first_or15_event(g):
    g=g.sort_values("timestamp_et").reset_index(drop=True)
    if len(g)<16:return "NONE"
    op=g.iloc[:15]
    if len(op)!=15:return "NONE"
    orh=float(op.high.max()); orl=float(op.low.min())
    for i in range(15,len(g)):
        m=int(g.iloc[i].minute)
        if m>690: break
        cc=float(g.iloc[i].close)
        if cc>orh:return "UPPER"
        if cc<orl:return "LOWER"
    return "NONE"

def main():
    raw=load_development()
    _,groups=prepare_rth(raw)
    d=daily(groups)
    ev={k:first_or15_event(g) for k,g in groups.items()}
    rows=[]
    for atrcol in ["atr_sma","atr_wilder"]:
      for warm in [60,100,126,180,252]:
        x=d.copy()
        vr=x[atrcol]/x.close
        p67=vr.shift(1).rolling(252,min_periods=warm).quantile(.67)
        erp33=x.er10.shift(1).rolling(252,min_periods=warm).quantile(.33)
        # today's regime must use yesterday's completed values and thresholds known then.
        prev_vr=vr.shift(1)
        prev_er=x.er10.shift(1)
        # At today's pre-open we know yesterday's value and the rolling
        # thresholds computed from history through yesterday.
        x["r1"]=(prev_vr>p67)&(prev_er>erp33)
        z=x[(x.year>=2020)&(x.year<=2024)&x.r1]
        r1_sessions=len(z)
        r1_upper=sum(ev.get(k)=="UPPER" for k in z.group_key)
        r1_lower=sum(ev.get(k)=="LOWER" for k in z.group_key)
        rows.append(dict(atr=atrcol,warmup=warm,r1_sessions=r1_sessions,r1_upper_events=r1_upper,r1_lower_events=r1_lower))
    out=pd.DataFrame(rows)
    print(out.to_string(index=False))
    print("reference sessions=170 events=106")
if __name__=="__main__": main()
