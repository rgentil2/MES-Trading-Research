#!/usr/bin/env python3
"""T05: causal 233/377-print (transaction-count) bars as filters for NQ T02.
All operations 2025-10-15..2026-04-30 DEV only. These are not price ticks;
1 exported Last row = 1 'tick-bar' event even if qty>1 contracts.
Bars reset at 08:00 ET, thus NOT necessarily the NinjaTrader chart session anchor.
"""
from __future__ import annotations
import argparse,json
from collections import deque
from pathlib import Path
from qc_tick_day import utc_bounds,file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day,build_bars,candidates,STEP_100NS
from nq_t04_execution import simulate_portfolio,SCENARIOS

FAMILIES=('T02_PARENT','T05_233','T05_377','T05_233_AND_377')
BAR_LENGTHS=(233,377)

def filters_for_signals(events,day,signals):
    """Return booleans for completed 233/377 Last trade-count bars STRICTLY before signal end.

    A signal's completed 5s decision point = start 08:00 UTC-adjusted ET
    plus (i+1)*5 seconds. Never look at an in-progress event bar or same-time ticks.
    """
    d=dev_day(day)  # before iterating events
    lo,hi=utc_bounds(d)
    if signals!=sorted(signals):
        raise ValueError('Signals must be time ordered')
    recent={n:deque(maxlen=2) for n in BAR_LENGTHS}
    state={n:[0,None] for n in BAR_LENGTHS}
    pos=0;last_ts=None
    answers=[]
    for i,side in signals:
        if side not in (-1,1) or i<0:raise ValueError('Unknown signal')
        cutoff=lo+(i+1)*STEP_100NS
        if not lo<cutoff<=hi:raise ValueError('Signal outside source window')
        while pos<len(events) and events[pos][0]<cutoff:
            ts,price,qty=events[pos]
            if not lo<=ts<hi or (last_ts is not None and ts<last_ts):
                raise ValueError('Noncausal/unsorted Last')
            if type(price)!=int or price<=0 or type(qty)!=int or qty<=0:
                raise ValueError('Invalid Last row')
            last_ts=ts
            for n in BAR_LENGTHS:
                state[n][0]+=1
                state[n][1]=price
                if state[n][0]==n:
                    recent[n].append(price)
                    state[n]=[0,None]
            pos+=1
        has233=len(recent[233])==2
        has377=len(recent[377])==2
        rule233=has233 and side*(recent[233][-1]-recent[233][-2])>0
        rule377=has377 and side*(recent[377][-1]-recent[377][-2])<0
        answers.append((bool(rule233),bool(rule377)))
    return answers

def selected_families(signals,flags):
    if len(signals)!=len(flags):
        raise ValueError('Not one flag per signal')
    result={k:[] for k in FAMILIES}
    for signal,(ok233,ok377) in zip(signals,flags):
        result['T02_PARENT'].append(signal)
        if ok233:result['T05_233'].append(signal)
        if ok377:result['T05_377'].append(signal)
        if ok233 and ok377:result['T05_233_AND_377'].append(signal)
    return result

def analyze_events(events,day):
    dev_day(day)
    bars=build_bars(events,day)
    signals,status=candidates(bars,day)
    if status!='READY':
        return {'date_et':day,'status':status,'families':{},
                'holdout_2026_may_sep_opened':False}
    parent=signals['T02_combined']
    flags=filters_for_signals(events,day,parent)
    families=selected_families(parent,flags)
    outcomes={}
    for name in FAMILIES:
        outcomes[name]={
            'parent_opportunities':len(parent),
            'opportunities_after_filter':len(families[name]),
            'cost_scenarios':{
                sc:simulate_portfolio(day,events,bars,families[name],sc)
                for sc in SCENARIOS
            }
        }
    return {'date_et':day,'status':'EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE',
       'tick_bar_reset_et':'08:00',
       'strict_last_bar_closure':'event_ts < signal_5sec_bar_end',
       'families':outcomes,
       'source_is_individual_last_prints':True,
       'fees_are_assumptions_not_verified':True,
       'holdout_2026_may_sep_opened':False}

def analyze_day(root,day):
    d=dev_day(day)
    path=file_for(root,d,'Last')
    return analyze_events(list(source_events(path)),day)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--day',required=True)
    a=p.parse_args()
    result=analyze_day(a.root,a.day)
    print('NQ_T05_DAY='+json.dumps(result,sort_keys=True,separators=(',',':')))
    if result['status'] not in ('EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE','SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE'):
        raise SystemExit(2)
