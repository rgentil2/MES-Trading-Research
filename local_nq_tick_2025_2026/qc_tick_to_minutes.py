#!/usr/bin/env python3
"""NQ Last ticks -> 1m and 5m source-QC, development slice only.

Independently aggregates every Last tick into two sets of bars. Does NOT
publish OHLCV or claim comparison with an external minute history. Does NOT
read July-Sep 2026 or any old 2025-26 minute research holdouts.
"""
from __future__ import annotations
import argparse, json, re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from qc_tick_day import check_day, file_for, parse_row, utc_bounds

CONTRACT_RE=re.compile(r"^NQ_(\d{2}-\d{2})_(\d{4})_(\d{8})_Tick_Last_ET0800_1200\.txt$")
TICKS_PER_POINT=4
MINUTE_100NS=60*10000000

@dataclass
class Bar:
    first:int
    last:int
    high:int
    low:int
    qty:int
    events:int
    first_ts:int
    last_ts:int

    @classmethod
    def start(cls,p:int,q:int,t:int):
        return cls(p,p,p,p,q,1,t,t)

    def add(self,p:int,q:int,t:int):
        self.last=p;self.high=max(self.high,p);self.low=min(self.low,p)
        self.qty+=q;self.events+=1;self.last_ts=t

def consolidate_bars(bars,slot=5):
    """Group 1m bars in order without revisiting ticks."""
    out={}
    for idx,bar in sorted(bars.items()):
        target=idx//slot
        if target not in out:
            out[target]=Bar(bar.first,bar.last,bar.high,bar.low,bar.qty,
                            bar.events,bar.first_ts,bar.last_ts)
        else:
            x=out[target]
            x.last=bar.last;x.high=max(x.high,bar.high);x.low=min(x.low,bar.low)
            x.qty+=bar.qty;x.events+=bar.events;x.last_ts=bar.last_ts
    return out

def audit_last_events(events, day):
    """Events are (UTC time 100ns, price in 0.25 ticks, positive integer size)."""
    d=check_day(day)   # fail closed before accessing events
    lo,hi=utc_bounds(d)
    minute, five={},{}
    c=Counter()
    prev_ts=None;prior_px=None
    first_ts=last_ts=None
    largest_gap=0
    for ts,px,qty in events:
        if not lo<=ts<hi:raise ValueError("Last event outside ET 08-12")
        if qty<=0 or not isinstance(qty,int):raise ValueError("bad integer Last size")
        if not isinstance(px,int) or px<=0:raise ValueError("bad price tick")
        if prev_ts is not None:
            if ts<prev_ts:raise ValueError("out-of-order Last event")
            if ts==prev_ts:
                c["same_timestamp"]+=1
                if px!=prior_px:c["same_timestamp_price_changes"]+=1
            if ts>prev_ts:
                gap=ts-prev_ts
                largest_gap=max(largest_gap,gap)
                if gap>=MINUTE_100NS:c["intertrade_gaps_ge_60s"]+=1
        else:first_ts=ts
        idx=(ts-lo)//MINUTE_100NS
        idx5=idx//5
        for bars,k in ((minute,idx),(five,idx5)):
            if k not in bars:bars[k]=Bar.start(px,qty,ts)
            else:bars[k].add(px,qty,ts)
        prev_ts=last_ts=ts;prior_px=px
        c["events"]+=1
        c["trade_quantity"]+=qty
    if not c["events"]:raise ValueError("zero Last trades")
    if len(minute)>240 or len(five)>48:raise ValueError("minute range invalid")
    back=consolidate_bars(minute)
    if back != five:
        raise ValueError("OHLCV 1m->5m consistency failure")
    if sum(b.qty for b in minute.values())!=c["trade_quantity"]:
        raise ValueError("1m volume conservation failed")
    if sum(b.events for b in minute.values())!=c["events"]:
        raise ValueError("1m event conservation failed")
    # Safe aggregate-only; no individual bars, times or prices emitted.
    return {
        "date_et":day,"status":"INTERNAL_TICK_BAR_QC_PASS",
        "minutes_expected":240,"minutes_with_last":len(minute),
        "minutes_without_last":240-len(minute),
        "five_minutes_with_last":len(five),
        "ticks_last":c["events"],"total_last_contracts":c["trade_quantity"],
        "duplicate_timestamp_event_count":c["same_timestamp"],
        "same_timestamp_price_change_event_count":c["same_timestamp_price_changes"],
        "intertrade_gaps_ge_60s":c["intertrade_gaps_ge_60s"],
        "longest_intertrade_gap_s":round(largest_gap/10000000,3),
        "minutes_0930_1130_with_last":sum(1 for i in range(90,210) if i in minute),
        "cross_resolution_consistency":True,
        "independent_minute_source_comparison":"NOT_PERFORMED_NO_AUTHORIZED_INDEPENDENT_NQ_MINUTE_SOURCE",
        "backtest_or_profit_calculated":False,
        "holdout_2026_jul_sep_opened":False,
        "market_prices_or_bars_published":False,
        "note":"Same-timestamp Last records have input order only; exchange sequencing is not demonstrated"
    }

def source_events(path:Path):
    with path.open("r",encoding="utf-8-sig") as f:
        for raw in f:
            ts,px,qty=parse_row(raw)
            if abs(px*TICKS_PER_POINT-round(px*TICKS_PER_POINT))>1e-7:
                raise ValueError("NQ off 0.25 tick grid")
            if not float(qty).is_integer():raise ValueError("fractional Last volume")
            yield ts,int(round(px*TICKS_PER_POINT)),int(qty)

def audit_day(root:Path,day:str):
    d=check_day(day)
    path=file_for(root,d,"Last")
    m=CONTRACT_RE.fullmatch(path.name)
    if not m or m.group(3)!=d.strftime("%Y%m%d") or m.group(2)!=str(d.year):
        raise ValueError("Unexpected source contract/date")
    result=audit_last_events(source_events(path),day)
    result["quarterly_contract_id"]=m.group(1)
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--day",required=True)
    a=ap.parse_args()
    print(json.dumps(audit_day(a.root,a.day),sort_keys=True))
