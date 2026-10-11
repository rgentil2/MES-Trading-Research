#!/usr/bin/env python3
"""NQ prior-BBO displacement QC: Oct 2025-Jun 2026, aggregate-only, no backtest.

At T trades see Bid/Ask strictly before T. Same-time BBO is a NONCAUSAL
sensitivity thought experiment, not an available execution price.
"""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from datetime import datetime, time, timezone
from itertools import groupby
from heapq import merge
from pathlib import Path
from zoneinfo import ZoneInfo
from qc_tick_day import check_day, utc_bounds
from qc_quote_trade import source_paths, source_events

AGES=(50,100,250,500,1000)
WINDOWS=(("pre_0800_0930","08:00","09:30"),
 ("open_0930_1000","09:30","10:00"),("mid_1000_1030","10:00","10:30"),
 ("late_1030_1130","10:30","11:30"),("post_1130_1200","11:30","12:00"))

def window_edges(day):
    ny=ZoneInfo("America/New_York")
    def edge(s):
        h,m=map(int,s.split(":"))
        dt=datetime.combine(day,time(h,m),tzinfo=ny).astimezone(timezone.utc)
        return int(dt.timestamp())*10000000
    return [(label,edge(a),edge(b)) for label,a,b in WINDOWS]

def classify(price,bid,ask):
    if bid is None or ask is None or bid>=ask:return "invalid_book"
    if price<bid:return "below_bid"
    if price>ask:return "above_ask"
    if price==bid:return "at_bid"
    if price==ask:return "at_ask"
    return "inside"

def aggregate_events(streams,day):
    d=check_day(day)  # deny sealed dates before accessing iterators
    edges=window_edges(d)
    counts=defaultdict(Counter)
    bid=ask=None
    for ts,batch in groupby(merge(*streams,key=lambda v:v[0]),key=lambda v:v[0]):
        trades,bu,au=[],[],[]
        for _,kind,px in batch:
            if kind=="Last": trades.append(px)
            elif kind=="Bid":bu.append(px)
            elif kind=="Ask":au.append(px)
            else:raise ValueError("unknown source type")
        if not trades:
            if bu:bid=(ts,bu[-1])
            if au:ask=(ts,au[-1])
            continue
        matches=[label for label,lo,hi in edges if lo<=ts<hi]
        if len(matches)!=1:raise ValueError("tick outside development ET windows")
        c=counts[matches[0]]
        same=bool(bu or au)
        nextbid=(ts,bu[-1]) if bu else bid
        nextask=(ts,au[-1]) if au else ask
        for px in trades:
            c["trades"]+=1
            if same:c["same_time_trades"]+=1
            if bid is None or ask is None:c["missing_prior"]+=1;continue
            if not (bid[0]<ts and ask[0]<ts):raise ValueError("noncausal prior BBO")
            if bid[1]>=ask[1]:c["crossed_or_locked"]+=1;continue
            c["valid_prior"]+=1
            prior=classify(px,bid[1],ask[1])
            outside=prior in ("below_bid","above_ask")
            c["outside"]+=int(outside)
            if outside:c[prior]+=1
            age=max(ts-bid[0],ts-ask[0])/10000.0
            for ms in AGES:
                if age<=ms:
                    c[f"age{ms}_n"]+=1
                    if outside:c[f"age{ms}_outside"]+=1
            if age<=250:
                spread=round((ask[1]-bid[1])*4)
                spreadband="1" if spread==1 else "2-3" if spread<=3 else "4+"
                c[f"spread{spreadband}_n"]+=1
                if outside:
                    c[f"spread{spreadband}_outside"]+=1
                    dist=round((bid[1]-px if px<bid[1] else px-ask[1])*4)
                    distband="1" if dist<=1 else "2" if dist==2 else "3+"
                    c["distance"+distband]+=1
            if same:
                c["same_time_eligible"]+=1
                if outside:c["prior_outside_same_time"]+=1
                if nextbid is not None and nextask is not None and nextbid[1]<nextask[1]:
                    alternative=classify(px,nextbid[1],nextask[1])
                    altout=alternative in ("below_bid","above_ask")
                    c["alternative_positive_book"]+=1
                    if altout:c["alternative_outside"]+=1
                    if outside and not altout:c["prior_outside_alt_inside"]+=1
                    if not outside and altout:c["prior_inside_alt_outside"]+=1
                else:c["alternative_invalid_book"]+=1
        if bu:bid=(ts,bu[-1])
        if au:ask=(ts,au[-1])
    return summarize(day,counts)

def summarize(day,counts):
    def pct(a,b):return round(100*a/b,2) if b else None
    segments={}
    for label,_,_ in WINDOWS:
        c=counts[label]
        out={"trades":c["trades"],"valid_prior":c["valid_prior"],
             "outside":c["outside"],"outside_pct":pct(c["outside"],c["valid_prior"]),
             "same_time_pct":pct(c["same_time_trades"],c["trades"]),
             "age_thresholds_ms":{},"spread_ticks_when_age_le_250ms":{},
             "outside_distance_ticks_age_le_250ms":{x:c["distance"+x] for x in ("1","2","3+")},
             "same_timestamp_alternative_NONCAUSAL":{
               "eligible":c["same_time_eligible"],
               "prior_outside":c["prior_outside_same_time"],
               "alternative_positive_book":c["alternative_positive_book"],
               "alternative_outside":c["alternative_outside"],
               "prior_outside_alt_inside":c["prior_outside_alt_inside"],
               "prior_inside_alt_outside":c["prior_inside_alt_outside"]}}
        for age in AGES:
            n=c[f"age{age}_n"];o=c[f"age{age}_outside"]
            out["age_thresholds_ms"][str(age)]={"n":n,"outside":o,"outside_pct":pct(o,n)}
        for band in ("1","2-3","4+"):
            n=c[f"spread{band}_n"];o=c[f"spread{band}_outside"]
            out["spread_ticks_when_age_le_250ms"][band]={"n":n,"outside":o,"outside_pct":pct(o,n)}
        segments[label]=out
    return {"date_et":day,"status":"DIAGNOSTIC_ONLY",
      "strict_rule":"prior_quote_time < trade_time",
      "holdout_2026_jul_sep_opened":False,"no_individual_prices_emitted":True,
      "no_execution_or_return_claims":True,
      "same_time_warning":"Alternative BBO is NONCAUSAL sensitivity, not a fillable quote",
      "segments":segments}

def analyze_day(root,day):
    d=check_day(day)
    files=source_paths(root,day)
    lo,hi=utc_bounds(d)
    qc=Counter()
    streams=[source_events(files[k],k,lo,hi,qc) for k in ("Last","Bid","Ask")]
    report=aggregate_events(streams,day)
    report["source_qc_counts"]=dict(qc)
    if any(k.endswith(("_invalid","_outside_ET_window","_off_tick_grid")) and v for k,v in qc.items()):
        report["status"]="SOURCE_REJECT"
    if qc.get("Last_invalid_size",0):report["status"]="SOURCE_REJECT"
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--day",required=True)
    args=p.parse_args()
    result=analyze_day(args.root,args.day)
    print(json.dumps(result,indent=2,sort_keys=True))
    if result["status"]!="DIAGNOSTIC_ONLY":raise SystemExit(2)
