#!/usr/bin/env python3
"""T189-T208 monetary discovery: 20 frozen hypotheses, only existing NQ Last DEV.

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
POLICY=ROOT/'research/nq/NQ_T189_T208_MONEY_FIRST_20_PREREG_2026_10_13.json'
WINDOWS={'A':((9,30),(9,45)), 'B':((9,50),(10,10)),
         'C':((10,25),(10,45)), 'D':((11,0),(11,20))}
CODES={
 'T189':'A_FAST_BREAK','T190':'A_SLOW_REVERSAL',
 'T191':'A_VOLUME_SURGE','T192':'A_VOLUME_DROP_TURN','T193':'A_CLUSTER_FADE',
 'T194':'B_ACCEPT_UP','T195':'B_ACCEPT_DOWN',
 'T196':'B_SWEEP_HIGH','T197':'B_SWEEP_LOW','T198':'B_BALANCE_RELEASE',
 'T199':'C_ABSORPTION_PROXY','T200':'C_THIN_DRIFT',
 'T201':'C_EXPANSION_CONFIRM','T202':'C_HIGH_VOLUME_NARROW',
 'T203':'C_EFFICIENT_VOLUME','T204':'D_ASCENDING_EXPANSION',
 'T205':'D_DESCENDING_EXPANSION','T206':'D_ALTERNATION',
 'T207':'D_DECELERATION','T208':'D_BURST_WITHOUT_PROGRESS'}
IDS=tuple(CODES)
MODEL_IDS=[BASE]+[name for i in IDS for name in (i+'_ONLY',i+'_PLUS_T05')]

def load_frozen():
    x=json.loads(POLICY.read_text(encoding='utf8'))
    members=x['members']
    if (x['id']!='NQ-T189-T208-MONEY-ONLY-ATOMIC233-V1'
        or [m['id'] for m in members]!=list(IDS)
        or any(m['code']!=CODES[m['id']] for m in members)
        or tuple(x['source_months'])!=MONTHS
        or (x['expected_source_days'],x['expected_ready_days'])!=(140,135)
        or x['reference_T05']!=BASE
        or x['selection']!='FIRST_COMPLETE_ATOMIC_233_PRINT_BAR_CLOSING_INSIDE_BLOCK_TIME_WINDOW; prior bars C and D strictly earlier; if no trigger do not scan later bars'
        or x['new_signals_use_five_seconds'] is not False
        or x['new_strategy_execution']['stop_ticks']!=24
        or x['new_strategy_execution']['take_profit_ticks']!=48
        or x['new_strategy_execution']['max_holding_seconds']!=300
        or x['economic_comparison']['extra_fee_usd_per_rt']!=10
        or x['formal_D1_D2_unchanged'] is not True
        or any(tuple(m['window_et'])!=tuple(next(t['window_et']
              for t in x['blocks'] if t['block']==m['block']))
              for m in members)):
        raise ValueError('T189_T208_PREREG_MISMATCH')
    if any(tuple(next(b['window_et'] for b in x['blocks']
             if b['block']==letter))!=tuple(f'{h:02d}:{m:02d}' for h,m in WINDOWS[letter])
           for letter in WINDOWS):
        raise ValueError('WINDOWS_DIFFER_FROM_FROZEN_POLICY')
    return x

def v(b):
    return b.price_times_qty_ticks/b.total_qty

def sgn(x):
    return (x>0)-(x<0)

def width(b):
    return b.high_ticks-b.low_ticks

def dur(b):
    return b.end_timestamp-b.start_timestamp

def choose(code,x,p,q):
    """Exact ex-ante conditional of one fixed 233-print bar and its 2 priors."""
    dx=v(x)-v(p)
    dp=v(p)-v(q)
    ax=abs(dx)
    ap=abs(dp)
    wx,wp,wq=width(x),width(p),width(q)
    tx,tp,tq=dur(x),dur(p),dur(q)
    Qx,Qp=x.total_qty,p.total_qty
    if code=='A_FAST_BREAK':
        return sgn(dx) if tp>0 and tx>0 and 3*tx<=2*tp and wx>=16 and ax>=4 else 0
    if code=='A_SLOW_REVERSAL':
        return -sgn(dp) if tp>0 and tx>=2*tp and ap>=4 else 0
    if code=='A_VOLUME_SURGE':
        return sgn(dx) if Qx>=2*Qp and ax>=4 else 0
    if code=='A_VOLUME_DROP_TURN':
        return sgn(dx) if 2*Qx<=Qp and ap>=4 and ax>=2 and sgn(dx)==-sgn(dp) else 0
    if code=='A_CLUSTER_FADE':
        return -sgn(dx) if 20*x.whole_timestamp_groups<=13*x.prints and wx>=20 and ax>=4 else 0

    upper=max(p.high_ticks,q.high_ticks)
    lower=min(p.low_ticks,q.low_ticks)
    if code=='B_ACCEPT_UP':
        return 1 if v(x)>=upper+2 else 0
    if code=='B_ACCEPT_DOWN':
        return -1 if v(x)<=lower-2 else 0
    if code=='B_SWEEP_HIGH':
        return -1 if x.high_ticks>=upper+4 and v(x)<upper else 0
    if code=='B_SWEEP_LOW':
        return 1 if x.low_ticks<=lower-4 and v(x)>lower else 0
    if code=='B_BALANCE_RELEASE':
        return sgn(dx) if wp<=12 and wq<=12 and wx>=20 and ax>=4 else 0

    if code=='C_ABSORPTION_PROXY':
        return -sgn(dp) if 2*Qx>=3*Qp and ax<=2 and ap>=4 else 0
    if code=='C_THIN_DRIFT':
        return sgn(dx) if 10*Qx<=7*Qp and ax>=6 else 0
    if code=='C_EXPANSION_CONFIRM':
        return sgn(dx) if wx>=2*wp and 5*Qx>=6*Qp and ax>=4 else 0
    if code=='C_HIGH_VOLUME_NARROW':
        return -sgn(dp) if 2*wx<=wp and Qx>=Qp and ap>=4 else 0
    if code=='C_EFFICIENT_VOLUME':
        return sgn(dx) if Qx>=2*Qp and wx<=wp and ax>=3 else 0

    if code=='D_ASCENDING_EXPANSION':
        return 1 if dx>=2 and dp>=2 and wx>wp>wq else 0
    if code=='D_DESCENDING_EXPANSION':
        return -1 if dx<=-2 and dp<=-2 and wx>wp>wq else 0
    if code=='D_ALTERNATION':
        return sgn(dx) if ax>=5 and ap>=2 and sgn(dx)==-sgn(dp) and wx<wp else 0
    if code=='D_DECELERATION':
        return -sgn(dp) if tq>0 and tp>0 and 2*tx>=3*tp and 2*tp>=3*tq and wx<=12 and ap>=4 else 0
    if code=='D_BURST_WITHOUT_PROGRESS':
        return -sgn(dp) if tp>0 and 2*tx<=tp and 2*Qx>=3*Qp and ax<=2 and ap>=4 else 0
    raise ValueError('UNKNOWN_FROZEN_MEMBER_'+code)

def new_signals(events,day):
    """One pre-registered 233 close/window; no adaptive next-bar rescue."""
    dev_day(day)
    bars=completed_bars_by_print_count(events,day,(233,))[233]
    anchor_idx={}
    for block,(lo,hi) in WINDOWS.items():
        start=et_edge(day,*lo); end=et_edge(day,*hi)
        anchor_idx[block]=next((i for i,x in enumerate(bars)
                     if start<=x.end_timestamp<end),None)
    output={};stats=Counter()
    for k,code in CODES.items():
        n=int(k[1:])
        block='A' if n<=193 else 'B' if n<=198 else 'C' if n<=203 else 'D'
        idx=anchor_idx[block]
        if idx is None or idx<2:
            output[k]=None
            stats[block+'_NO_COMPLETE_CONTEXT']+=1
            continue
        x,p,q=bars[idx],bars[idx-1],bars[idx-2]
        if not(q.end_timestamp<p.end_timestamp<x.end_timestamp):
            raise AssertionError('ATOM_CLOSED_CONTEXT_ORDER')
        side=choose(code,x,p,q)
        if side not in (-1,0,1):raise AssertionError('INVALID_SIDE')
        output[k]=(x.end_timestamp,side) if side else None
        if side:stats[k+'_SIGNAL']+=1
    if set(output)!=set(IDS):raise AssertionError('MISSING_FROZEN_MEMBER')
    return output,stats

def run_month(root,month):
    if month not in MONTHS:raise ValueError('T189_T208_FORBIDDEN_MONTH')
    load_frozen()
    days=sorted(month_days(root,month))
    envelopes={name:Envelope() for name in MODEL_IDS}
    extras={name:Envelope() for name in MODEL_IDS}
    stats={name:{'c':counter(),'extra':counter(),
          'owners':defaultdict(counter),'extra_owners':defaultdict(counter),
          'opps':0,'overlap':0,'capacity':0,'reject':0} for name in MODEL_IDS}
    qc=Counter();signal_counts=Counter();censored=set()
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
            if key in censored:continue
            z=stats[key];z['opps']+=len(signals)
            try:
                attrs,more,skips=trace(day,events,old_bars,signals,STRESS,
                     envelopes[key],extras[key])
            except ValueError as exc:
                if str(exc)!='B05H UNRESOLVED SYNTHETIC EXPOSURE FAIL CLOSED':
                    raise
                if key==BASE:
                    raise ValueError('T05_FROZEN_BASELINE_UNRESOLVED_FAIL_WHOLE_MONTH') from exc
                censored.add(key)
                continue
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
        if name in censored:
            # Model is not counted as zero or profitable; discard its entire
            # partial 1-month vector. Requiring all 7 months makes N/D global.
            models[name]={STRESS:{'status':'NOT_ESTIMABLE_UNRESOLVED_EXECUTION',
                  'trades':None,'net_usd':None,
                  'stress_extra_10usd_fixed_path':None}}
            continue
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
    return {'month':month,'status':'T189_T208_DEV_MONEY_EXPLORATORY_UNVERIFIED',
       'source_days':source,'eligible_days':ready,
       'models':models,'signal_counts':dict(signal_counts),
       'n_censored_models':len(censored),
       'censored_model_keys':sorted(censored),
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
    print('T189_T208_MONTH_SAFE='+json.dumps({
       'month':a.month,'source':result['source_days'],
       'ready':result['eligible_days'],
       'signals':result['signal_counts'],
       'n_censored_models':result['n_censored_models'],
       'holdouts_opened':False,'licensed_data_exported':False},sort_keys=True))
