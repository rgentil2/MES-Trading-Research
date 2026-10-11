#!/usr/bin/env python3
"""Frozen T06: 233+377 Fibonacci vs 250+400 near-scale control.
Only Oct 2025-Apr 2026 outcomes; May-Jun hold for internal validation,
Jul-Sep sealed. No optimization or actual broker fills.
"""
from __future__ import annotations
import argparse,json
from collections import deque
from pathlib import Path
from qc_tick_day import utc_bounds,file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day,build_bars,candidates,STEP_100NS
from nq_t04_execution import simulate_portfolio,SCENARIOS

SIZES=(233,250,377,400)
FAMILIES=('T02_PARENT','T05_233_AND_377','T06_250','T06_400','T06_250_AND_400')

def context_flags(events,day,signals):
    d=dev_day(day)
    lo,hi=utc_bounds(d)
    if signals!=sorted(signals):raise ValueError('signals must be ordered')
    recent={n:deque(maxlen=2) for n in SIZES}
    count={n:0 for n in SIZES}
    pos=0;last_ts=None;result=[]
    for i,side in signals:
        if side not in (-1,1) or i<0:raise ValueError('invalid signal')
        cutoff=lo+(i+1)*STEP_100NS
        if not lo<cutoff<=hi:raise ValueError('cutoff outside DEV session')
        while pos<len(events) and events[pos][0]<cutoff:
            ts,price,qty=events[pos]
            if not lo<=ts<hi or (last_ts is not None and ts<last_ts):
                raise ValueError('unsorted/out-of-window Last')
            if type(price)!=int or price<=0 or type(qty)!=int or qty<=0:
                raise ValueError('bad Last tick')
            last_ts=ts
            for n in SIZES:
                count[n]+=1
                if count[n]==n:
                    recent[n].append(price)
                    count[n]=0
            pos+=1
        result.append({n:len(recent[n])==2 and (
            side*(recent[n][-1]-recent[n][-2])>0 if n in (233,250)
            else side*(recent[n][-1]-recent[n][-2])<0) for n in SIZES})
    return result

def select_families(signals,flags):
    if len(signals)!=len(flags):raise ValueError('signal flag mismatch')
    a={name:[] for name in FAMILIES}
    for sig,check in zip(signals,flags):
        a['T02_PARENT'].append(sig)
        if check[233] and check[377]:a['T05_233_AND_377'].append(sig)
        if check[250]:a['T06_250'].append(sig)
        if check[400]:a['T06_400'].append(sig)
        if check[250] and check[400]:a['T06_250_AND_400'].append(sig)
    return a

def analyze_events(events,day):
    dev_day(day)
    bars=build_bars(events,day)
    signals,status=candidates(bars,day)
    if status!='READY':
        return {'date_et':day,'status':status,'families':{},
                'holdout_2026_may_sep_opened':False}
    parent=signals['T02_combined']
    chosen=select_families(parent,context_flags(events,day,parent))
    return {'date_et':day,'status':'EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE',
      'risk_policy':'T04_UNMODIFIED',
      'bar_anchor':'08:00 ET',
      'families':{name:{
        'parent_opportunities':len(parent),
        'opportunities_after_filter':len(chosen[name]),
        'cost_scenarios':{sc:simulate_portfolio(day,events,bars,chosen[name],sc)
                          for sc in SCENARIOS}}
                          for name in FAMILIES},
      'costs_are_assumptions_not_verified':True,
      'holdout_2026_may_sep_opened':False}

def analyze_day(root,day):
    d=dev_day(day)
    return analyze_events(list(source_events(file_for(root,d,'Last'))),day)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--day',required=True)
    a=p.parse_args()
    print('NQ_T06_DAY='+json.dumps(analyze_day(a.root,a.day),separators=(',',':'),sort_keys=True))
