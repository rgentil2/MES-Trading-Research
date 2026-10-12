#!/usr/bin/env python3
"""Frozen stage-0 distinct questions T17 magnitude, T18 auction direction,
T19 path inefficiency magnitude. Trades, cash, IC90, BH q NOT COMPUTED.
All data preexisting NQ Last DEV; no new 5-second signals or OOS.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_b05h01_trade_expansion_month import et_edge,slope_at_least,frozen_t05

IDS=('T17_SPEED_NO_RANGE','T18_PREOPEN_AUCTION_DRIFT','T19_LOW_PATH_EFFICIENCY')

def t17(b,c):
    rb=b.high_ticks-b.low_ticks
    rc=c.high_ticks-c.low_ticks
    db=b.end_timestamp-b.start_timestamp
    dc=c.end_timestamp-c.start_timestamp
    return db>0 and dc>0 and 2*dc<=db and rb>=4 and 1<=rc<=rb

def t19(last_five):
    if len(last_five)!=5:raise ValueError('Need 5 complete bars')
    points=[Fraction(b.price_times_qty_ticks,b.total_qty) for b in last_five]
    path=sum((abs(y-x) for x,y in zip(points,points[1:])),Fraction(0))
    delta=abs(points[-1]-points[0])
    return path>=16 and 4*delta<=path

def preopen_pairs(events,day):
    """Aggregate quantity-weighted 08:00-08:45 vs 08:45-09:30 ET, no close."""
    dev_day(day)
    split=et_edge(day,8,45)
    end=et_edge(day,9,30)
    a_q=a_px=b_q=b_px=0
    for t,px,qty in events:
        if t<split:
            a_q+=qty;a_px+=px*qty
        elif t<end:
            b_q+=qty;b_px+=px*qty
        else:
            break
    if not a_q or not b_q:return None
    return (SimpleNamespace(total_qty=a_q,price_times_qty_ticks=a_px),
            SimpleNamespace(total_qty=b_q,price_times_qty_ticks=b_px))

def t18(p1,p2,b,c,side):
    return (slope_at_least(p2,p1,side,8) and
            slope_at_least(c,p2,side,8) and
            slope_at_least(c,b,side,2))

def detect(events,day):
    dev_day(day)
    bars=completed_bars_by_print_count(events,day,(377,))[377]
    pre=preopen_pairs(events,day)
    lo=et_edge(day,9,45);hi=et_edge(day,11,0)
    chosen={};num=0
    for i in range(4,len(bars)):
        five=bars[i-4:i+1]
        b,c=five[-2:]
        tm=c.end_timestamp
        if tm<lo or tm>=hi:continue
        if b.end_timestamp>=tm:raise ValueError('timestamp ties split across bars')
        num+=1
        if IDS[0] not in chosen and t17(b,c):chosen[IDS[0]]=(tm,0)
        if IDS[1] not in chosen and pre is not None:
            signs=[s for s in (1,-1) if t18(*pre,b,c,s)]
            if len(signs)>1:raise ValueError('opposed auction sides')
            if signs:chosen[IDS[1]]=(tm,signs[0])
        if IDS[2] not in chosen and t19(five):chosen[IDS[2]]=(tm,0)
        if len(chosen)==3:break
    return chosen,num

def month_stage(root,month):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_DENIED_BEFORE_FS')
    days=month_days(root,month)
    sources=Counter();counts=Counter();pairs=Counter();n=0
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        qc,_,_=frozen_t05(events,day) # coverage only; signals never reused
        sources[qc]+=1
        if qc!='READY':continue
        candidate,inspected=detect(events,day)
        n+=inspected
        keys=sorted(candidate)
        for k in keys:counts[k]+=1
        for i,k in enumerate(keys):
            for v in keys[i+1:]:pairs[k+'__'+v]+=1
    if sum(sources.values())!=len(days):raise AssertionError('coverage')
    return {'status':'T17_T19_MECHANISM_SCREEN_ONLY_NO_RETURNS',
       'month':month,'source_days':len(days),'eligible_days':sources['READY'],
       'excluded_days':len(days)-sources['READY'],
       'hypotheses':{k:{'signal_days':counts[k],
          'economic_trades':None,'net_usd':None,'IC90':None,'q_BH':None,
          'validated':False,
          'directional_trading_signal':k==IDS[1]} for k in IDS},
       'overlap_days':dict(pairs),'inspected_bars':n,
       'oos_read':False,'new_history_acquired':False,
       'five_second_new_signals':False,'PnL_calculated':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('SEALED BEFORE FILES')
    result=month_stage(a.root,a.month)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('T17_T19_SAFE_MONTH='+json.dumps({'month':a.month,
      'source':result['source_days'],'eligible':result['eligible_days'],
      'signal_days':{k:r['signal_days'] for k,r in result['hypotheses'].items()},
      'no_returns':True},sort_keys=True))
