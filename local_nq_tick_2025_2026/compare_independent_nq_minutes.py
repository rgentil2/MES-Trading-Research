#!/usr/bin/env python3
"""Compare NQ Last ticks against INDEPENDENT sanitized single-day NQ Minute Last.

Input minute file must contain exactly one authorized ET session (08:00-12:00)
and MUST NOT be the original multi-year NQ/MNQ ZIP or a full 2026 contract.
Only Oct-2025..Jun-2026 days permitted. No bar prices are emitted.
The clock convention is explicit; NinjaTrader BarsRequest is normally bar-END
timestamped, but confirm against exported examples rather than maximizing match.
"""
from __future__ import annotations
import argparse, json, math, re
from collections import Counter
from pathlib import Path
from qc_tick_day import check_day, utc_bounds, utc_minute_100ns
from qc_tick_to_minutes import source_events, MINUTE_100NS, Bar

MIN_RE=re.compile(r"^NQ_(\d{2}-\d{2})_(\d{4})_(\d{8})_Minute_Last_ET0800_1200\.txt$")
TICK_RE=re.compile(r"^NQ_(\d{2}-\d{2})_(\d{4})_(\d{8})_Tick_Last_ET0800_1200\.txt$")
STAMP_RE=re.compile(r"^(\d{8}) (\d{2})(\d{2})(\d{2})$")

def _tick_float(text):
    px=float(text)
    if not math.isfinite(px) or px<=0 or abs(px*4-round(px*4))>1e-7:
        raise ValueError("not an NQ tick-grid price")
    return round(px*4)

def _size_int(text):
    n=float(text)
    if not math.isfinite(n) or n<0 or n!=int(n):
        raise ValueError("invalid minute volume")
    return int(n)

def source_paths(root:Path,day:str):
    d=check_day(day)  # first, before any pathlib glob/open
    stamp=d.strftime("%Y%m%d")
    tick=list((root/"Tick_Last").glob("NQ_*_"+stamp+"_Tick_Last_ET0800_1200.txt"))
    minute=list((root/"Minute_Last").glob("NQ_*_"+stamp+"_Minute_Last_ET0800_1200.txt"))
    if len(tick)!=1 or len(minute)!=1:
        raise FileNotFoundError("exactly one tick and one sanitized minute day file required")
    a=TICK_RE.fullmatch(tick[0].name)
    b=MIN_RE.fullmatch(minute[0].name)
    if not a or not b or a.groups()!=b.groups():
        raise ValueError("contract, year or session mismatch")
    return tick[0],minute[0]

def iter_minute_file(path:Path):
    with path.open("r",encoding="utf-8-sig") as f:
        for line in f:
            v=line.rstrip("\r\n").split(";")
            if len(v)!=6:raise ValueError("NinjaTrader minute row must have six columns")
            m=STAMP_RE.fullmatch(v[0])
            if not m or int(m[2])>23 or int(m[3])>59 or int(m[4])>59:
                raise ValueError("bad minute timestamp")
            timestamp=utc_minute_100ns(m[1]+m[2]+m[3])+int(m[4])*10_000_000
            op,hi,lo,cl=map(_tick_float,v[1:5])
            qty=_size_int(v[5])
            if not lo<=op<=hi or not lo<=cl<=hi:raise ValueError("invalid OHLC")
            yield timestamp,(op,hi,lo,cl,qty)

def compare_events(tick_events,minute_events,day:str,minute_label:str="end"):
    d=check_day(day) # BEFORE accessing iterators
    if minute_label not in ("end","start"):raise ValueError("choose explicit minute convention")
    start,stop=utc_bounds(d)
    bars={}
    prev=None
    for ts,price,qty in tick_events:
        if ts<start or ts>=stop or (prev is not None and ts<prev):
            raise ValueError("out-of-window/out-of-order Last tick")
        prev=ts
        if not isinstance(price,int) or price<=0 or not isinstance(qty,int) or qty<=0:
            raise ValueError("invalid Last event")
        minute=(ts-start)//MINUTE_100NS
        if minute not in bars:bars[minute]=Bar.start(price,qty,ts)
        else:bars[minute].add(price,qty,ts)
    if not bars:raise ValueError("no source Last tick events")
    observed={}
    prev=None
    for ts,ohlcv in minute_events:
        if prev is not None and ts<=prev:
            raise ValueError("minute timestamps duplicated or unordered")
        prev=ts
        # End labels 08:01..12:00; start labels 08:00..11:59.
        relative=ts-start-(MINUTE_100NS if minute_label=="end" else 0)
        if relative<0 or relative>=stop-start or relative%MINUTE_100NS:
            raise ValueError("minute timestamp outside allowed single-day session")
        minute=relative//MINUTE_100NS
        if minute in observed:raise ValueError("duplicate minute")
        observed[minute]=ohlcv
    if not observed:raise ValueError("no independent minute bars")
    both=set(bars).intersection(observed)
    diffs=Counter()
    max_deltas=Counter()
    for k in both:
        b=bars[k]
        expected=(b.first,b.high,b.low,b.last,b.qty)
        found=observed[k]
        for col,a,z in zip(("open","high","low","close","volume"),expected,found):
            if a!=z:
                diffs[col]+=1
                max_deltas[col]=max(max_deltas[col],abs(a-z))
    ok=len(both)==len(bars)==len(observed)==240 and not diffs
    return {
       "date_et":day,"minute_timestamp_convention":minute_label,
       "status":"INDEPENDENT_MINUTE_MATCH" if ok else "SOURCE_MISMATCH_OR_INCOMPLETE",
       "tick_minutes":len(bars),"independent_minute_rows":len(observed),
       "minutes_compared":len(both),"missing_independent_minutes":len(set(bars)-set(observed)),
       "missing_tick_minutes":len(set(observed)-set(bars)),
       "difference_minutes_by_field":{x:diffs[x] for x in ("open","high","low","close","volume")},
       "maximum_abs_difference_ticks_or_contracts":{x:max_deltas[x] for x in ("open","high","low","close","volume")},
       "verified_fully_240_minutes":ok,
       "outcome_pnl_simulated":False,"raw_prices_emitted":False,
       "holdout_2026_jul_sep_opened":False,
       "note":"Required minutes are from a separate provider export, not resampled from the compared ticks. Volume may reflect vendor conventions."
    }

def compare_day(root:Path,day:str,minute_label:str):
    tick,minute=source_paths(root,day)
    return compare_events(source_events(tick),iter_minute_file(minute),day,minute_label)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--day",required=True)
    p.add_argument("--minute-label",choices=("end","start"),required=True)
    a=p.parse_args()
    result=compare_day(a.root,a.day,a.minute_label)
    print(json.dumps(result,indent=2,sort_keys=True))
    if result["status"]!="INDEPENDENT_MINUTE_MATCH":
        raise SystemExit(2)

if __name__=="__main__":main()
