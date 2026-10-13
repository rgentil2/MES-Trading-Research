#!/usr/bin/env python3
"""T169-T188 monetary discovery: 20 frozen hypotheses, only existing NQ Last DEV.

Research-only proxies. New signals use *atomic* print count bars, NEVER five-second
bars. T05 legacy 5s is called only as immutable comparison in shared routers.
Private trade/day outcomes may NEVER be exported by this process.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_b05h01_trade_expansion_month import (
    BASE, NEW, STRESS, frozen_t05, shared_router, trace, et_edge)
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS, month_days
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_t08_risk_audit import Envelope
from nq_b05_t11_month import counter

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'research/nq/NQ_T169_T188_MONETARY_BLOCKS_PREREG_2026_10_13.json'
WINDOWS={'A':((9,10),(9,25)), 'B':((9,30),(9,40)),
         'C':((10,20),(10,40)), 'D':((11,10),(11,35))}
CODES={
 'T169':'A_PRE_TREND','T170':'A_PRE_EXHAUST',
 'T171':'A_PRE_COMPRESSION','T172':'A_PRE_BREAK','T173':'A_PRE_SWEEP',
 'T174':'B_OPEN_MACRO_MOMENTUM','T175':'B_OPEN_MACRO_FADE',
 'T176':'B_OPEN_EXPANSION','T177':'B_OPEN_VALUE_CROSS',
 'T178':'B_OPEN_REJECTION','T179':'C_MID_MICRO_ALIGN',
 'T180':'C_MID_MICRO_DIVERGE','T181':'C_MID_MACRO_BREAK',
 'T182':'C_MID_MACRO_SWEEP','T183':'C_MID_VOLUME_EXPANSION',
 'T184':'D_LATE_DRIFT','T185':'D_LATE_MICRO_EXHAUST',
 'T186':'D_LATE_MACRO_FADE','T187':'D_LATE_TIGHT_BREAK',
 'T188':'D_LATE_LARGE_REVERT'}
IDS=tuple(CODES)
MODEL_IDS=[BASE]+[name for i in IDS for name in (i+'_ONLY',i+'_PLUS_T05')]

def load_frozen():
    x=json.loads(POLICY.read_text(encoding='utf8'))
    ms=x['members']
    if (x['prereg_id']!='NQ-T169-T188-MONETARY-BLOCKS-V1'
        or [m['id'] for m in ms]!=list(IDS)
        or any(m['code']!=CODES[m['id']] for m in ms)
        or tuple(x['source_months'])!=MONTHS
        or (x['expected_source'],x['expected_ready'])!=(140,135)
        or x['frozen_benchmark']!=BASE
        or x['signals_use']!='FIRST_COMPLETED_ATOMIC_377_PRINT_BAR_IN_FIXED_ET_WINDOW_WITH_233_377_4181_PRIOR_CONTEXT'
        or x['stop_ticks']!=24 or x['target_ticks']!=48
        or x['max_holding_seconds']!=300
        or x['per_candidate_max_daily_signals']!=1
        or x['extra_cost_rt_usd']!=10
        or x['holdouts_opened'] is not False
        or x['new_5s_signals'] is not False
        or any(tuple(m['window'])!=tuple(next(b['window_et'] for b in x['block_members']
                  if b['block']==m['block'])) for m in ms)
       ):raise ValueError('T169_T188_PREREG_MISMATCH')
    return x

def v(b):
    return b.price_times_qty_ticks/b.total_qty

def sgn(x):
    return (x>0)-(x<0)

def width(b):
    return b.high_ticks-b.low_ticks

def choose(code,x,p,q,micro,macro):
    """Causal side fixed from *complete* bars at anchor, no price lookahead."""
    dx=v(x)-v(p)
    dp=v(p)-v(q)
    sm=0 if len(micro)<2 else v(micro[-1])-v(micro[-2])
    gap=0 if macro is None else v(x)-v(macro)
    positive=signed=0

    if code=='A_PRE_TREND':
        return sgn(dx) if abs(dx)>=2 and abs(dp)>=2 and sgn(dx)==sgn(dp) else 0
    if code=='A_PRE_EXHAUST':
        return -sgn(dx) if abs(dx)>=8 else 0
    if code=='A_PRE_COMPRESSION':
        return sgn(dx) if width(p)<=16 and width(x)>=32 and abs(dx)>=2 else 0
    if code=='A_PRE_BREAK':
        if x.high_ticks>=p.high_ticks+4 and v(x)>p.high_ticks:return 1
        if x.low_ticks<=p.low_ticks-4 and v(x)<p.low_ticks:return -1
        return 0
    if code in ('A_PRE_SWEEP','B_OPEN_REJECTION'):
        if x.high_ticks>=p.high_ticks+8 and v(x)<p.high_ticks:return -1
        if x.low_ticks<=p.low_ticks-8 and v(x)>p.low_ticks:return 1
        return 0
    if code=='B_OPEN_MACRO_MOMENTUM':
        return sgn(gap) if macro is not None and abs(gap)>=12 else 0
    if code=='B_OPEN_MACRO_FADE':
        return -sgn(gap) if macro is not None and abs(gap)>=48 else 0
    if code=='B_OPEN_EXPANSION':
        return sgn(dx) if width(x)*2>=3*max(1,width(p)) and abs(dx)>=8 else 0
    if code=='B_OPEN_VALUE_CROSS':
        return sgn(dx) if abs(dx)>=2 and abs(dp)>=2 and sgn(dx)==sgn(dp) else 0
    if code=='C_MID_MICRO_ALIGN':
        return sgn(dx) if abs(dx)>=2 and abs(sm)>=2 and sgn(dx)==sgn(sm) else 0
    if code=='C_MID_MICRO_DIVERGE':
        return sgn(sm) if abs(dx)>=2 and abs(sm)>=2 and sgn(dx)==-sgn(sm) else 0
    if code=='C_MID_MACRO_BREAK':
        if macro is None:return 0
        if v(x)>=macro.high_ticks+4:return 1
        if v(x)<=macro.low_ticks-4:return -1
        return 0
    if code=='C_MID_MACRO_SWEEP':
        if macro is None:return 0
        if x.high_ticks>=macro.high_ticks+4 and v(x)<macro.high_ticks:return -1
        if x.low_ticks<=macro.low_ticks-4 and v(x)>macro.low_ticks:return 1
        return 0
    if code=='C_MID_VOLUME_EXPANSION':
        return sgn(dx) if 4*x.total_qty>=7*p.total_qty and abs(dx)>=2 else 0
    if code=='D_LATE_DRIFT':
        return sgn(dx) if (abs(dx)>=2 and abs(dp)>=2 and abs(sm)>=2
              and sgn(dx)==sgn(dp)==sgn(sm)) else 0
    if code=='D_LATE_MICRO_EXHAUST':
        return sgn(sm) if abs(dx)>=8 and abs(sm)>=2 and sgn(dx)==-sgn(sm) else 0
    if code=='D_LATE_MACRO_FADE':
        return -sgn(gap) if macro is not None and abs(gap)>=48 else 0
    if code=='D_LATE_TIGHT_BREAK':
        return sgn(dx) if width(x)<=12 and abs(dx)>=2 else 0
    if code=='D_LATE_LARGE_REVERT':
        return -sgn(dx) if width(x)>=40 and abs(dx)>=8 else 0
    raise ValueError('Unknown registered strategy code '+code)

def new_signals(events,day):
    dev_day(day)
    data=completed_bars_by_print_count(events,day,(233,377,4181))
    bars=data[377]; micros=data[233]; macros=data[4181]
    anchor_idx={}
    for block,(lo,hi) in WINDOWS.items():
        start=et_edge(day,*lo);stop=et_edge(day,*hi)
        anchor_idx[block]=next((i for i,b in enumerate(bars)
                 if start<=b.end_timestamp<stop),None)
    out={}; reasons=Counter()
    for k,code in CODES.items():
        block=k[1:2] # not valid; use numeric ranges below, no signal fallback
        n=int(k[1:])
        block='A' if n<=173 else 'B' if n<=178 else 'C' if n<=183 else 'D'
        idx=anchor_idx[block]
        if idx is None or idx<2:
            out[k]=None;reasons[block+'_NO_ANCHOR_OR_PRIOR']+=1;continue
        x,p,q=bars[idx],bars[idx-1],bars[idx-2]
        completed_micro=[b for b in micros if b.end_timestamp<x.end_timestamp]
        completed_macro=[b for b in macros if b.end_timestamp<x.end_timestamp]
        if len(completed_micro)<2:
            out[k]=None;reasons[block+'_NO_MICRO_CONTEXT']+=1;continue
        mk=completed_macro[-1] if completed_macro else None
        side=choose(code,x,p,q,completed_micro[-2:],mk)
        if side not in (-1,0,1):raise AssertionError('BAD_SIDE')
        out[k]=(x.end_timestamp,side) if side else None
        if side:reasons[k+'_SIGNAL']+=1
    if set(out)!=set(IDS):raise AssertionError('MISSING_NEW_ID')
    return out,reasons

def run_month(root,month):
    if month not in MONTHS:raise ValueError('T169_T188_FORBIDDEN_MONTH')
    load_frozen()
    days=sorted(month_days(root,month))
    envelopes={name:Envelope() for name in MODEL_IDS}
    extras={name:Envelope() for name in MODEL_IDS}
    stats={name:{'c':counter(),'extra':counter(),
          'owners':defaultdict(counter),'extra_owners':defaultdict(counter),
          'opps':0,'overlap':0,'capacity':0,'reject':0} for name in MODEL_IDS}
    qc=Counter();signal_counts=Counter()
    for day in days:
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        status,old_bars,t05=frozen_t05(events,day)
        qc[status]+=1
        if status!='READY':continue
        # Recompute atomic print-bars only once/day. Do not use legacy 5s signals.
        new,counts=new_signals(events,day)
        signal_counts.update(counts)
        sets={BASE:t05}
        for k in IDS:
            z=new[k]
            chosen=[(z[0],z[1],NEW)] if z else []
            sets[k+'_ONLY']=chosen
            route,_=shared_router(t05,[(z[0],z[1])] if z else [])
            sets[k+'_PLUS_T05']=route
        for key,signals in sets.items():
            z=stats[key];z['opps']+=len(signals)
            attrs,more,skips=trace(day,events,old_bars,signals,STRESS,
                 envelopes[key],extras[key])
            for owner,c in attrs.items():
                z['c'].update(c);z['owners'][owner].update(c)
            for owner,c in more.items():
                z['extra'].update(c);z['extra_owners'][owner].update(c)
            z['overlap']+=skips['overlap'];z['capacity']+=skips['capacity']
            z['reject']+=skips['no_valid_entry']
    source=len(days);ready=qc['READY']
    if source!=ready+qc['SKIP_MISSING_OPENING_RANGE']+qc['SKIP_TINY_OPENING_RANGE']:
        raise AssertionError('DEV_QC_NO_PARTIAL_SOURCE')
    if not ready:raise AssertionError('NO_READY_DEV_SESSIONS')
    models={}
    for name,z in stats.items():
        c=z['c'];extra=z['extra']
        if (extra['trades']!=c['trades'] or
             extra['net_cents']!=c['net_cents']-1000*c['trades']):
            raise AssertionError('EXTRA10_CENTS_FAIL '+name)
        if abs(c['net_cents']/100-envelopes[name].equity)>.01:
            raise AssertionError('ENVELOPE_BASE_FAIL '+name)
        if abs(extra['net_cents']/100-extras[name].equity)>.01:
            raise AssertionError('ENVELOPE_EXTRA_FAIL '+name)
        def owners(a):
            return {key:{'trades':v['trades'],
                'net_usd':round(v['net_cents']/100,2)} for key,v in a.items()}
        models[name]={STRESS:{
            'opportunities':z['opps'],'trades':c['trades'],
            'net_usd':round(c['net_cents']/100,2),
            'positive_usd':round(c['positive_cents']/100,2),
            'negative_usd':round(c['negative_cents']/100,2),
            'owner_attribution':owners(z['owners']),
            'last_envelope_segment':envelopes[name].segment(),
            'rejected_overlap':z['overlap'],
            'rejected_capacity':z['capacity'],
            'rejected_fill':z['reject'],
            'stress_extra_10usd_fixed_path':{
                'trades':extra['trades'],
                'net_usd':round(extra['net_cents']/100,2),
                'positive_usd':round(extra['positive_cents']/100,2),
                'negative_usd':round(extra['negative_cents']/100,2),
                'owner_attribution':owners(z['extra_owners']),
                'last_envelope_segment':extras[name].segment()}}}
    return {'month':month,'status':'T169_T188_DEV_MONEY_EXPLORATORY_UNVERIFIED',
       'source_days':source,'eligible_days':ready,
       'models':models,'signal_counts':dict(signal_counts),
       'holdouts_opened':False,'new_history_acquired':False,
       'new_signal_5second_bars':False,'licensed_data_exported':False,
       'broker_fills_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('SEALED_MONTH_REJECTED')
    result=run_month(a.root,a.month)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('T169_T188_MONTH_SAFE='+json.dumps({
       'month':a.month,'source':result['source_days'],
       'ready':result['eligible_days'],
       'signals':result['signal_counts'],
       'holdouts_opened':False,'licensed_data_exported':False},sort_keys=True))
