#!/usr/bin/env python3
"""B04 exploratory temporal diagnostics for FROZEN T05-377 Last trades.

Monthly JSON is only aggregated by month and ISO week. Never exports trade
timestamps, signals, entry/exit prices or individual trade outcomes. This is
NOT execution validation, not OOS, not a new trading hypothesis.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day, build_bars, candidates
from nq_tick_short_horizon_month import MONTHS, month_days
from nq_t05_fibonacci_bars import filters_for_signals, selected_families
from nq_t04_execution import SCENARIOS, simulate_portfolio
from nq_t10_t05_bbo_endpoints import replay_frozen, SKIPS

MODELS=("baseline", "stress_1p5_fee_2ticks_each_side",
        "stress_original_plus_10usd_rt")
FROZEN_ORIGINAL_EXPECTED={
    "baseline":(115,6220.0),
    "stress_1p5_fee_2ticks_each_side":(115,5102.5)}
EXTRA_RT_USD=10.0

def week_id(day):
    d=date.fromisoformat(day)
    y,w,_=d.isocalendar()
    return f"{y}-W{w:02d}"

def empty():
    return dict(trades=0,win=0,loss=0,flat=0,
                net_cents=0,pos_cents=0,neg_cents=0)

def add_trade(acc,gain):
    c=int(round(100*gain))
    acc['trades']+=1
    acc['net_cents']+=c
    acc['pos_cents']+=max(c,0)
    acc['neg_cents']+=max(-c,0)
    if c>0:acc['win']+=1
    elif c<0:acc['loss']+=1
    else:acc['flat']+=1

def assemble_month(root,month):
    if month not in MONTHS:
        raise ValueError('FORBIDDEN_MONTH_BEFORE_FILE_ACCESS')
    dates=sorted(month_days(root,month))
    if len(set(dates))!=len(dates):
        raise ValueError('Duplicate ET day')
    weekly={s:defaultdict(empty) for s in MODELS}
    monthly={s:empty() for s in MODELS}
    status_count=Counter()
    original_check={s:empty() for s in SCENARIOS}
    for day in dates:
        dev_day(day)
        w=week_id(day)
        for sc in MODELS:
            weekly[sc][w]  # Include 0-trade source weeks
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        bars=build_bars(events,day)
        signal_map,status=candidates(bars,day)
        if status in SKIPS:
            status_count[status]+=1
            continue
        if status!='READY':
            raise ValueError('Unexpected source status')
        status_count['READY']+=1
        parent=signal_map['T02_combined']
        chosen=selected_families(parent,filters_for_signals(events,day,parent))['T05_377']
        for sc in SCENARIOS:
            trades,summary=replay_frozen(day,events,bars,chosen,sc)
            control=simulate_portfolio(day,events,bars,chosen,sc)
            if control!=summary:
                raise AssertionError(f'T04 signal/fill parity failed {day}/{sc}')
            if summary['unknown_entry_or_exit'] or summary['day_aborted_due_to_ambiguity']:
                raise ValueError('Unresolved frozen execution ambiguity')
            model=sc
            for trade in trades:
                gain=trade['estimated_net_usd']
                add_trade(monthly[model],gain)
                add_trade(weekly[model][w],gain)
                if sc=='stress_1p5_fee_2ticks_each_side':
                    extra_gain=round(gain-EXTRA_RT_USD,2)
                    add_trade(monthly['stress_original_plus_10usd_rt'],extra_gain)
                    add_trade(weekly['stress_original_plus_10usd_rt'][w],extra_gain)
    if status_count['READY']+sum(status_count[s] for s in SKIPS)!=len(dates):
        raise AssertionError('Incomplete DEV month coverage')
    for sc in MODELS:
        coll=monthly[sc]
        if any(sum(week[k] for week in weekly[sc].values())!=coll[k]
               for k in coll):
            raise AssertionError('Unreconciled ISO-week splits')
    base=monthly['stress_1p5_fee_2ticks_each_side']
    adj=monthly['stress_original_plus_10usd_rt']
    if (adj['trades']!=base['trades'] or
        adj['net_cents']!=base['net_cents']-round(EXTRA_RT_USD*100)*base['trades']):
        raise AssertionError('Frozen-path surcharge is not linear')
    return {
        'month':month,'status':'B04_DEV_WEEK_MONTH_AGGREGATE_ONLY',
        'source_days':len(dates),
        'eligible_days':status_count['READY'],
        'excluded_days':len(dates)-status_count['READY'],
        'chronological_et_dates':True,
        'holdouts_opened':False,'trade_level_data_exported':False,
        'pnl_is_real_broker_fills':False,
        'scenarios':{sc:{
            'month_counter':monthly[sc],
            'iso_week_counters':dict(sorted(weekly[sc].items()))}
            for sc in MODELS}}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--month',required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.month not in MONTHS:
        raise SystemExit('SEALED_MONTH_BLOCKED')
    result=assemble_month(args.root,args.month)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('B04_SAFE_MONTH='+json.dumps({
        'month':args.month,'source_days':result['source_days'],
        'eligible_days':result['eligible_days'],
        'trades':{sc:d['month_counter']['trades'] for sc,d in result['scenarios'].items()},
        'status':result['status']},sort_keys=True))
