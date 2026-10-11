#!/usr/bin/env python3
"""T07 predeclared NQ 233/4181/10946 vs 240/4200/11000 context.
Strictly Oct25-Apr26 DEV Last; no May-Jun outcomes or Jul-Sep sealed.
No claims of real fills or statistical validation.
"""
from __future__ import annotations
import argparse,json
from collections import deque
from pathlib import Path
from qc_tick_day import utc_bounds,file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day,build_bars,candidates,STEP_100NS
from nq_t04_execution import simulate_portfolio,SCENARIOS

SIZES=(233,377,4181,10946,240,4200,11000)
FAMILIES=('T02_PARENT','T05_233_AND_377','T07_233_4181',
          'T07_233_4181_10946','T07_CONTROL_240_4200_11000')

def flags_before_signals(events,day,signals):
    d=dev_day(day)  # preflight before touching market events
    lower,upper=utc_bounds(d)
    if signals!=sorted(signals):raise ValueError('Signals must be chronologically ordered')
    recent={k:deque(maxlen=2) for k in SIZES}
    counts={k:0 for k in SIZES}
    pos=0;previous=None;all_flags=[]
    for index,side in signals:
        if side not in (1,-1) or index<0:raise ValueError('Invalid signal')
        cutoff=lower+(index+1)*STEP_100NS
        if not lower<cutoff<=upper:raise ValueError('Decision cutoff outside allowed source')
        while pos<len(events) and events[pos][0]<cutoff:
            ts,price,qty=events[pos]
            if not lower<=ts<upper or (previous is not None and ts<previous):
                raise ValueError('Bad Last chronology')
            if type(price)!=int or price<=0 or type(qty)!=int or qty<=0:
                raise ValueError('Invalid Last source row')
            previous=ts
            for k in SIZES:
                counts[k]+=1
                if counts[k]==k:
                    recent[k].append(price)
                    counts[k]=0
            pos+=1
        def trend(k,dir):
            return len(recent[k])==2 and dir*side*(recent[k][-1]-recent[k][-2])>0
        # short continuation, medium countertrend pullback, long trend continuation
        all_flags.append((trend(233,1),trend(377,-1),trend(4181,-1),
          trend(10946,1),trend(240,1),trend(4200,-1),trend(11000,1)))
    return all_flags

def split_signals(signals,flags):
    if len(signals)!=len(flags):raise ValueError('Mismatched flags')
    result={name:[] for name in FAMILIES}
    for signal,flag in zip(signals,flags):
        f233,f377,f4181,f10946,f240,f4200,f11000=flag
        result['T02_PARENT'].append(signal)
        if f233 and f377:result['T05_233_AND_377'].append(signal)
        if f233 and f4181:result['T07_233_4181'].append(signal)
        if f233 and f4181 and f10946:
            result['T07_233_4181_10946'].append(signal)
        if f240 and f4200 and f11000:
            result['T07_CONTROL_240_4200_11000'].append(signal)
    return result

def analyze_events(events,day):
    dev_day(day)
    bars=build_bars(events,day)
    signals,status=candidates(bars,day)
    if status!='READY':
        return {'date_et':day,'status':status,'families':{},
                'holdout_2026_may_sep_opened':False}
    original=signals['T02_combined']
    selected=split_signals(original,flags_before_signals(events,day,original))
    portfolios={}
    for name in FAMILIES:
        portfolios[name]={
            'parent_opportunities':len(original),
            'opportunities_after_filter':len(selected[name]),
            'cost_scenarios':{
                sc:simulate_portfolio(day,events,bars,selected[name],sc)
                for sc in SCENARIOS
            }
        }
    return {
        'date_et':day,'status':'EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE',
        'bar_anchor':'08:00 ET',
        'bar_closure':'strictly before the 5s signal',
        'risk_policy':'T04_UNMODIFIED',
        'families':portfolios,
        'fees_are_assumptions_not_verified':True,
        'holdout_2026_may_sep_opened':False}

def analyze_day(root,day):
    d=dev_day(day)
    return analyze_events(list(source_events(file_for(root,d,'Last'))),day)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--day',required=True)
    a=p.parse_args()
    print('NQ_T07_DAY='+json.dumps(analyze_day(a.root,a.day),sort_keys=True,separators=(',',':')))
