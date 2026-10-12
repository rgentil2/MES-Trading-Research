#!/usr/bin/env python3
"""T14-T16 predeclared DISTINCT trade-print signal feasibility, NOT P&L.

Three frozen question mechanisms, a first opportunity per eligible DEV session,
377-print bars with timestamp groups indivisible. No new 5-second signal,
broker fills, p-values, q values, market history or holdout access.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_b05h01_trade_expansion_month import et_edge,slope_at_least,frozen_t05

IDS=('T14_PERSISTENT_DRIFT','T15_ROUND_NUMBER_ACCEPTANCE','T16_EFFORT_NO_PROGRESS')
MIN_PRINTS=377
GRID_TICKS=100  # 25 NQ INDEX POINTS
MINUTES_NS=10_000_000 * 60

def within_ticks(a,b,limit):
    """Compare VWAP rationals exactly without rounded prices."""
    if min(a.total_qty,b.total_qty)<=0:raise ValueError('zero qty')
    return abs(a.price_times_qty_ticks*b.total_qty -
               b.price_times_qty_ticks*a.total_qty) <= limit*a.total_qty*b.total_qty

def t14(a,b,c,sign):
    ra=b.high_ticks-b.low_ticks
    rc=c.high_ticks-c.low_ticks
    return (rc<=24 and rc<=ra and
      slope_at_least(b,a,sign,2) and slope_at_least(c,b,sign,2))

def t15(b,c,sign):
    """25 NQ-point acceptance, not 5-second opening-range break."""
    if sign==1:
        level=(b.price_times_qty_ticks//(GRID_TICKS*b.total_qty)+1)*GRID_TICKS
        return (b.price_times_qty_ticks <= (level-4)*b.total_qty
            and c.price_times_qty_ticks >= (level+4)*c.total_qty
            and c.low_ticks>=level)
    level=(b.price_times_qty_ticks//(GRID_TICKS*b.total_qty))*GRID_TICKS
    return (b.price_times_qty_ticks >= (level+4)*b.total_qty
        and c.price_times_qty_ticks <= (level-4)*c.total_qty
        and c.high_ticks<=level)

def t16(a,b,c,sign):
    """Big qty per print but stagnant price: predict OPPOSITE prior drift."""
    rb=b.high_ticks-b.low_ticks
    rc=c.high_ticks-c.low_ticks
    return (rb>0 and rc>=1 and 2*rc<=rb
            and c.total_qty*b.prints >= 2*b.total_qty*c.prints
            and within_ticks(c,b,2)
            and slope_at_least(b,a,-sign,4))

def detect(events,day):
    """Return PRIVATE first timestamp/side per hypothesis; public only counts."""
    dev_day(day)  # seal BEFORE touching the iterator
    bars=completed_bars_by_print_count(events,day,(MIN_PRINTS,))[MIN_PRINTS]
    lo=et_edge(day,9,45);hi=et_edge(day,11,0)
    picked={}
    observations=0
    for i in range(2,len(bars)):
        a,b,c=bars[i-2:i+1]
        ts=c.end_timestamp
        if ts<lo or ts>=hi:continue
        if not(a.end_timestamp<b.end_timestamp<c.end_timestamp):
            raise ValueError('No complete non-overlapping timestamp groups')
        observations+=1
        for name, fn in zip(IDS, (lambda s:t14(a,b,c,s),
                                  lambda s:t15(b,c,s),
                                  lambda s:t16(a,b,c,s))):
            if name in picked:continue
            sides=[s for s in (1,-1) if fn(s)]
            if len(sides)>1:raise ValueError('AMBIGUOUS_DIRECTION_BOTH_SIDES')
            if sides:picked[name]=(ts,sides[0])
        if len(picked)==len(IDS):break
    return picked,observations

def month_stage(root,month):
    if month not in MONTHS:raise ValueError('SEALED_OR_INVALID_MONTH_BEFORE_FS')
    days=month_days(root,month)
    status=Counter()
    selected=Counter()
    active=Counter()
    overlaps=Counter()
    inspected=0
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        qc,_,_=frozen_t05(events,day) # comparability QC ONLY. Not used as signal.
        status[qc]+=1
        if qc!='READY':continue
        opportunities,n=detect(events,day)
        inspected+=n
        keys=tuple(sorted(opportunities))
        for k in keys:
            selected[k]+=1
            active[k]+=1 # max 1 per eligible day, not actual trade
        for i,a in enumerate(keys):
            for b in keys[i+1:]:
                overlaps[a+'__'+b]+=1
    source=len(days);eligible=status['READY']
    if sum(status.values())!=source or source<=0:raise ValueError('QC coverage incomplete')
    return {'status':'T14_T16_FROZEN_SIGNAL_SCREEN_ONLY_NO_RETURNS',
      'month':month,'source_days':source,'eligible_days':eligible,
      'excluded_days':source-eligible,'skip_reasons':{k:v for k,v in status.items() if k!='READY'},
      'hypotheses':{k:{'candidate_signal_days':selected[k],
                        'candidate_signals':selected[k],
                        'executed_trades':None,'net_pnl':None,'IC90':None,
                        'p':None,'q_BH':None,'holm':None,
                        'economically_validated':False} for k in IDS},
      'pairwise_candidate_days':dict(overlaps),
      'eligible_bar_decisions':inspected,
      'new_data_acquired':False,'holdouts_opened':False,
      'new_5second_signals':False,'returns_or_fills_computed':False,
      'tick_or_trade_rows_exported':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('SEALED BEFORE FS')
    x=month_stage(a.root,a.month)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
    print('T14_T16_SCREEN_SAFE='+json.dumps({
      'month':x['month'],'source':x['source_days'],
      'eligible':x['eligible_days'],
      'count':{k:z['candidate_signals'] for k,z in x['hypotheses'].items()},
      'pnl_calculated':False,'no_holdouts':True},sort_keys=True))
