#!/usr/bin/env python3
"""EXPLORATORY T04: NQ T02 failed break + slowing Last activity vs C02 ablation.
Frozen 1 NQ, <=2 trades/day, 5-min exit, stop/TP, no overlap, adverse fills.
Development Oct25-Apr26 only. Commission cost scenarios are ASSUMPTIONS,
not verified funded-broker fees. Never infer live fills from Last prints.
"""
from __future__ import annotations
import argparse,json
from bisect import bisect_right
from itertools import islice
from pathlib import Path
from qc_tick_day import file_for,utc_bounds
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day,build_bars,candidates,STEP_100NS
from sim_nq_last_execution_skeleton import FillPolicy,Signal,simulate_single_trade

PORTFOLIOS=('T02_combined','C02_reversal_no_rate')
SCENARIOS={'baseline':(1,5.0),'stress_1p5_fee_2ticks_each_side':(2,7.5)}
NQ_TICK_USD=5.0
MAX_TRADES_PER_DAY=2
STOP_NEW_ENTRIES_AFTER_DAILY_USD=-600.0

def stop_ticks(opening_range_ticks):
    """One fixed prereg stop: 25% opening range, bounded 16..48 ticks."""
    if type(opening_range_ticks)!=int or opening_range_ticks<4:
        raise ValueError('Bad opening range')
    return min(48,max(16,(opening_range_ticks+3)//4))

def risk_policy(opening_range_ticks,scenario):
    if scenario not in SCENARIOS:raise ValueError('Unknown cost scenario')
    slip,fee=SCENARIOS[scenario]
    s=stop_ticks(opening_range_ticks)
    return FillPolicy(latency_ms=1,entry_slippage_ticks=slip,
       exit_slippage_ticks=slip,stop_ticks=s,take_profit_ticks=2*s,
       max_holding_seconds=300,commission_round_trip_usd=fee,contracts=1)

def opening_width(bars):
    op=bars[1080:1140]
    if len(op)!=60 or any(b is None for b in op):return None
    return max(b[1] for b in op)-min(b[2] for b in op)

def simulate_portfolio(day,events,bars,signals,scenario):
    d=dev_day(day)   # NO sealed data even iterator access
    lo,_=utc_bounds(d)
    opening=opening_width(bars)
    if opening is None:raise ValueError('Missing opening range')
    policy=risk_policy(opening,scenario)
    times=[e[0] for e in events]
    if any(x>y for x,y in zip(times,times[1:])):
        raise ValueError('Out-of-order source ticks')
    pnl=0.0;closed_min=0.0;floating_min=0.0
    gains=[];overlap=capacity=invalid=0;aborted=False
    last_exit=-1
    for i,side in signals:
        if side not in (-1,1) or i<0:raise ValueError('Invalid source signal')
        if len(gains)>=MAX_TRADES_PER_DAY or pnl<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            capacity+=1;continue
        signal_t=lo+(i+1)*STEP_100NS  # end of completed 5s bar
        if signal_t<=last_exit:
            overlap+=1;continue
        start=bisect_right(times,signal_t)
        signal=Signal(day,signal_t,side)
        r=simulate_single_trade(islice(events,start,None),signal,policy)
        if r['status']!='SYNTHETIC_FILL_MODEL_ONLY':
            invalid+=1
            if r['status'] in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS','UNRESOLVED_END_OF_LAST_DATA'):
                aborted=True;break # unknown live exposure -> fail closed
            continue
        t0,t1=r['entry_timestamp'],r['exit_timestamp']
        if t1<=t0:raise ValueError('Noncausal synthetic fill')
        net=r['estimated_net_usd']
        ref=r['entry_price_ticks']
        ia=bisect_right(times,t0-1)
        ib=bisect_right(times,t1)
        # Conservative last-trade intra-position floating mark, NOT exchange BBO.
        worst=min((side*(px-ref)*NQ_TICK_USD-policy.commission_round_trip_usd-
                  policy.exit_slippage_ticks*NQ_TICK_USD
                  for _,px,_ in events[ia:ib]),default=0.0)
        floating_min=min(floating_min,pnl+worst)
        pnl=round(pnl+net,2)
        closed_min=min(closed_min,pnl)
        gains.append(net)
        last_exit=t1
    pos=sum(g for g in gains if g>0)
    loss=-sum(g for g in gains if g<0)
    return {'opportunities':len(signals),'trades':len(gains),
        'skipped_overlap':overlap,'skipped_max_two_or_daily_stop':capacity,
        'unknown_entry_or_exit':invalid,'day_aborted_due_to_ambiguity':aborted,
        'net_usd':round(sum(gains),2),
        'wins':sum(g>0 for g in gains),'losses':sum(g<0 for g in gains),
        'total_positive_usd':round(pos,2),'total_negative_usd':round(loss,2),
        'worst_trade_usd':min(gains) if gains else None,
        'closed_min_vs_day_start_usd':round(closed_min,2),
        'floating_last_mark_min_vs_day_start_usd':round(floating_min,2)}

def simulate_day(root:Path,day):
    d=dev_day(day)
    path=file_for(root,d,'Last')
    events=list(source_events(path))
    bars=build_bars(events,day)
    signals,status=candidates(bars,day)
    if status!='READY':
        return {'date_et':day,'status':status,'results':{},
                'holdout_2026_may_sep_opened':False}
    s=stop_ticks(opening_width(bars))
    results={fam:{sc:simulate_portfolio(day,events,bars,signals[fam],sc)
         for sc in SCENARIOS} for fam in PORTFOLIOS}
    return {'date_et':day,'status':'EXPLORATORY_SIM_ONLY',
      'preregistered_stop_ticks':s,'results':results,
      'simulation_uses_last_not_live_fills':True,
      'broker_fees_verified':False,
      'holdout_2026_may_sep_opened':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--day',required=True)
    a=p.parse_args()
    print('NQ_T04_DAY='+json.dumps(simulate_day(a.root,a.day),sort_keys=True,separators=(',',':')))
