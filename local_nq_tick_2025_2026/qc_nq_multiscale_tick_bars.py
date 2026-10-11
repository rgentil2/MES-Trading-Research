#!/usr/bin/env python3
"""NQ tick-bar scale study. Last print counts, NOT price moves/contract volume.
DEV dates 2025-10..2026-06 only. Reset at 08:00 ET. No prices or PnL output.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from statistics import median
from qc_tick_day import check_day,file_for,utc_bounds
from qc_tick_to_minutes import source_events

FIB=(233,4181,10946)
ROUND=(240,4200,11000)
SCALES=FIB+ROUND
MINUTE=60*10_000_000
SNAPSHOTS=(90,150,210)  # 09:30,10:30,11:30 ET
WINDOW=(90,210)  # first two hours after US open

def quantile(xs,p):
    if not xs:return None
    a=sorted(xs);i=(len(a)-1)*p;k=int(i)
    return round(a[k]+(a[min(k+1,len(a)-1)]-a[k])*(i-k),3)

class Builder:
    def __init__(self,size):
        self.size=size
        self.count=0
        self.start=None
        self.last=None
        self.complete_last=None
        self.same=0
        self.qty=0
        self.o=self.h=self.l=self.c=None
    def add(self,t,price,volume):
        if self.count==0:
            self.start=t
            self.last=None  # exclude duplicates carried over from previous bar
            self.o=self.h=self.l=price
            self.qty=self.same=0
        if self.last==t:self.same+=1
        self.h=max(self.h,price);self.l=min(self.l,price)
        self.c=price
        self.qty+=volume
        self.count+=1
        self.last=t
        if self.count==self.size:
            duration=(t-self.start)/10_000_000
            self.complete_last=t
            assert self.qty>=self.size
            self.count=0
            return duration,self.same
        return None

def analyze_events(events,day):
    d=check_day(day)  # refuse sealed *before* touching iterators
    lo,hi=utc_bounds(d)
    builders={n:Builder(n) for n in SCALES}
    durations={n:[] for n in SCALES}
    active_durations={n:[] for n in SCALES}
    completed={n:0 for n in SCALES}
    active_count={n:0 for n in SCALES}
    repeated_bars={n:0 for n in SCALES}
    last_at_snapshot={n:[None]*3 for n in SCALES}
    snapshot_index=0
    total=0
    duplicate_stamps=0
    previous=None
    for t,price,volume in events:
        if not lo<=t<hi:raise ValueError("Last tick outside 08-12 ET")
        if previous is not None and t<previous:raise ValueError("Unordered Last")
        if type(price)!=int or price<=0 or type(volume)!=int or volume<=0:
            raise ValueError("Invalid Last event")
        while snapshot_index<3 and t>=lo+SNAPSHOTS[snapshot_index]*MINUTE:
            for n in SCALES:
                last_at_snapshot[n][snapshot_index]=builders[n].complete_last
            snapshot_index+=1
        if previous==t:duplicate_stamps+=1
        for n,b in builders.items():
            bar=b.add(t,price,volume)
            if bar is None:continue
            elapsed,repeated=bar
            completed[n]+=1
            durations[n].append(elapsed)
            if repeated:repeated_bars[n]+=1
            if lo+WINDOW[0]*MINUTE<=t<lo+WINDOW[1]*MINUTE:
                active_count[n]+=1
                active_durations[n].append(elapsed)
        previous=t;total+=1
    if not total:raise ValueError("Empty Last source")
    for ix in range(snapshot_index,3):
        for n in SCALES:
            last_at_snapshot[n][ix]=builders[n].complete_last
    scale={}
    for n,b in builders.items():
        if completed[n]*n+b.count!=total:raise ValueError("Bar event conservation failed")
        ages=[None if t is None else round((lo+m*MINUTE-t)/10_000_000,3)
              for t,m in zip(last_at_snapshot[n],SNAPSHOTS)]
        scale[str(n)]={
            "complete_bars_0800_1200":completed[n],
            "complete_bars_0930_1130":active_count[n],
            "final_incomplete_events":b.count,
            "duration_seconds_0930_1130":{
                "p10":quantile(active_durations[n],.1),
                "median":quantile(active_durations[n],.5),
                "p90":quantile(active_durations[n],.9)},
            "duration_seconds_0800_1200":{
                "p10":quantile(durations[n],.1),
                "median":quantile(durations[n],.5),
                "p90":quantile(durations[n],.9)},
            "closed_context_exists_at_0930_1030_1130":[x is not None for x in ages],
            "age_of_last_closed_context_at_0930_1030_1130_s":ages,
            "bars_with_repeated_timestamp_rows":repeated_bars[n]
        }
    return {
        "day_et":day,"last_print_rows":total,
        "repeated_timestamp_rows":duplicate_stamps,
        "status":"MULTISCALE_ACTIVITY_QC_ONLY",
        "bar_unit":"one Last print record, not volume contracts or price ticks",
        "bar_reset":"08:00 ET each development day",
        "snapshot_causality":"only bars closed at strictly earlier timestamps",
        "full_daily_context_available":False,
        "tested_strategy_returns":False,
        "holdout_2026_jul_sep_opened":False,
        "raw_prices_emitted":False,
        "scales":scale
    }

def summarize_month(month,days):
    from qc_bbo_month_batch import DAYS_BY_MONTH
    if month not in DAYS_BY_MONTH:
        raise ValueError("Month outside approved DEV/QC period")
    expected={month+"-"+x for x in DAYS_BY_MONTH[month]}
    if len(days)!=4 or {r["day_et"] for r in days}!=expected:
        raise ValueError("Unexpected/missing monthly day")
    scales={}
    for n in SCALES:
        key=str(n)
        vals=[r["scales"][key]["duration_seconds_0930_1130"]["median"] for r in days]
        if any(x is None for x in vals):raise ValueError("No completed bar in operating window")
        counts=[r["scales"][key]["complete_bars_0930_1130"] for r in days]
        scales[key]={
            "median_of_four_daily_median_duration_seconds":round(median(vals),3),
            "minimum_daily_median_seconds":min(vals),
            "maximum_daily_median_seconds":max(vals),
            "median_completed_bars_0930_1130":median(counts),
            "all_days_context_ready_at_0930":all(
                r["scales"][key]["closed_context_exists_at_0930_1030_1130"][0] for r in days)}
    return {
        "month":month,"status":"ACTIVITY_TIME_SCALE_QC_NO_PNL",
        "study_period":"2025-10..2026-06",
        "daily":days,"monthly_scales":scales,
        "holdout_2026_jul_sep_opened":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--month",required=True)
    a=p.parse_args()
    from qc_bbo_month_batch import DAYS_BY_MONTH
    if a.month not in DAYS_BY_MONTH:raise SystemExit("Forbidden month")
    days=[]
    for day in DAYS_BY_MONTH[a.month]:
        dt=a.month+"-"+day
        check_day(dt)
        file=file_for(a.root,check_day(dt),"Last")
        days.append(analyze_events(source_events(file),dt))
    print("NQ_MULTISCALE_QC_JSON="+json.dumps(summarize_month(a.month,days),separators=(",",":"),sort_keys=True))

if __name__=="__main__":main()
