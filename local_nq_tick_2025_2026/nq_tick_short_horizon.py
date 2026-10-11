#!/usr/bin/env python3
"""NQ 5-second Last-only joint signals: Oct25-Apr26 DEVELOPMENT ONLY.
T01 opening-range continuation + trade-rate; T02 rejected breakout + declining
trade-rate; T03 predeclared volatility router; C01/C02 no-rate ablations.
OUTCOMES ARE GROSS TICK DIRECTIONS, NEVER FILLS/P&L/ANNUAL RETURNS.
"""
from __future__ import annotations
import argparse,json
from datetime import date
from pathlib import Path
from statistics import mean,median

STEP_100NS=5*10000000
N_BARS=2880
OR_START,OR_END=1080,1140  # 09:30..09:35 ET, 5-second bars
LAST_SIGNAL=2280  # 11:10 ET, gives 20-min window before 11:30
HORIZONS=(1,3,5,10,20)
FAMILIES=('T01_combined','T02_combined','T03_router',
          'C01_breakout_no_rate','C02_reversal_no_rate')

def dev_day(day):
    d=date.fromisoformat(day)
    if d<date(2025,10,15) or d>date(2026,4,30) or d.weekday()>=5:
        raise ValueError('SEALED_OR_OUT_OF_SCOPE: allowed development dates 2025-10-15..2026-04-30')
    return d

def build_bars(events,day):
    from qc_tick_day import utc_bounds
    d=dev_day(day)  # reject holdout BEFORE looking at any events
    start,stop=utc_bounds(d)
    bars=[None]*N_BARS
    prev=None;count=0
    for ts,px,qty in events:
        if not start<=ts<stop or (prev is not None and ts<prev):
            raise ValueError('out-of-order or out-of-session Last')
        if type(px)!=int or px<=0 or type(qty)!=int or qty<=0:
            raise ValueError('bad tick price/volume')
        i=(ts-start)//STEP_100NS
        b=bars[i]
        if b is None:bars[i]=[px,px,px,px,1,qty]
        else:
            b[1]=max(b[1],px);b[2]=min(b[2],px)
            b[3]=px;b[4]+=1;b[5]+=qty
        prev=ts;count+=1
    if not count:raise ValueError('Last day empty')
    return bars

def complete(bars,a,b):
    part=bars[a:b]
    return part if len(part)==b-a and all(x is not None for x in part) else None

def candidates(bars,day):
    dev_day(day)
    opening=complete(bars,OR_START,OR_END)
    if opening is None:return {},'SKIP_MISSING_OPENING_RANGE'
    high=max(b[1] for b in opening);low=min(b[2] for b in opening)
    width=high-low
    if width<4:return {},'SKIP_TINY_OPENING_RANGE'
    result={k:[] for k in FAMILIES}
    last={k:-10000 for k in FAMILIES}
    for i in range(OR_END+60,LAST_SIGNAL):
        window=complete(bars,i-60,i+1)
        if window is None:continue
        now=bars[i][3];previous=bars[i-1][3]
        new=sum(b[4] for b in bars[i-5:i+1])
        old=sum(b[4] for b in bars[i-11:i-5])
        faster=(old>=20 and 100*new>=135*old)
        slower=(old>=20 and 100*new<=85*old)
        recent_range=max(b[1] for b in window)-min(b[2] for b in window)
        high_state=(2*recent_range>=width)
        direction=now-bars[i-12][3]
        excursion=bars[i-18:i] # all complete, within window
        cont=1 if previous<=high and now>=high+4 and direction>=8 else (
             -1 if previous>=low and now<=low-4 and direction<=-8 else 0)
        rev=-1 if previous>=high-1 and now<=high-2 and max(b[1] for b in excursion)>=high+4 else (
             1 if previous<=low+1 and now>=low+2 and min(b[2] for b in excursion)<=low-4 else 0)
        T01=cont if faster else 0
        T02=rev if slower else 0
        options={
          'T01_combined':T01,'T02_combined':T02,
          'T03_router':T01 if high_state else T02,
          'C01_breakout_no_rate':cont,'C02_reversal_no_rate':rev}
        for name,side in options.items():
            if side and i-last[name]>=60: # one every 5 minutes per family
                result[name].append((i,side));last[name]=i
    return result,'READY'

def analyze_bars(bars,day):
    selected,status=candidates(bars,day)
    if status!='READY':
        return {'date_et':day,'status':status,'families':{},'holdout_2026_may_sep_opened':False}
    output={}
    for name in FAMILIES:
        events=selected[name];future={h:[] for h in HORIZONS}
        for i,side in events:
            if bars[i+1] is None:continue
            later_entry=bars[i+1][0]  # first PRINT in NEXT 5-second interval
            for h in HORIZONS:
                target=i+12*h
                if target>=N_BARS or bars[target] is None:continue
                future[h].append(side*(bars[target][3]-later_entry))
        output[name]={
          'opportunities':len(events),
          'forward_ticks':{str(h):{
            'n':len(future[h]),
            'mean':round(mean(future[h]),3) if future[h] else None,
            'median':median(future[h]) if future[h] else None,
            'positive_pct':round(100*sum(x>0 for x in future[h])/len(future[h]),2)
                  if future[h] else None} for h in HORIZONS}
        }
    return {'date_et':day,'status':'DIAGNOSTIC_ONLY','families':output,
      'causal_signal':'completed 5s Last bar, later print for horizon study',
      'no_individual_prices_or_timestamps_emitted':True,
      'execution_or_pnl_simulated':False,'costs_applied':False,
      'holdout_2026_may_sep_opened':False}

def analyze_day(root,day):
    from qc_tick_day import file_for
    from qc_tick_to_minutes import source_events
    d=dev_day(day)
    path=file_for(root,d,'Last')
    return analyze_bars(build_bars(source_events(path),day),day)

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--root',type=Path,required=True)
    a.add_argument('--day',required=True)
    x=a.parse_args()
    result=analyze_day(x.root,x.day)
    print('NQ_SHORT_HORIZON_DIAGNOSTIC='+json.dumps(result,sort_keys=True,separators=(',',':')))
    if result['status']!='DIAGNOSTIC_ONLY':raise SystemExit(2)
