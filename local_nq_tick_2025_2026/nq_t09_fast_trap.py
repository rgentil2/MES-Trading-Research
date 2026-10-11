#!/usr/bin/env python3
"""NQ T09: distinct fast-breakout -> rapid-range-reentry strategy and shared T05 router.

PREREGISTERED: see NQ_T09_FAST_TRAP_SECOND_STRATEGY_PREREG_2026_10_11.md
Development ONLY; Last prints are not guaranteed exchange/broker fills.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
from itertools import islice
import json
from pathlib import Path

from qc_tick_day import file_for, utc_bounds
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import (
    dev_day,build_bars,candidates,OR_START,OR_END,LAST_SIGNAL,STEP_100NS)
from nq_t05_fibonacci_bars import filters_for_signals,selected_families
from nq_t04_execution import (simulate_portfolio,SCENARIOS,opening_width,risk_policy,
    MAX_TRADES_PER_DAY,STOP_NEW_ENTRIES_AFTER_DAILY_USD)
from sim_nq_last_execution_skeleton import Signal, simulate_single_trade

PORTFOLIOS=('T01_CONT','T09_RAW_FADE','T09_FAST_TRAP_60S','T05_377',
            'T09_NQ_COMBINED_ROUTER')
OWNERS=('T05_377','T09_FAST_TRAP_60S')

def opening_levels(bars):
    o=bars[OR_START:OR_END]
    if len(o)!=OR_END-OR_START or any(b is None for b in o):
        raise ValueError('No complete opening range')
    return max(x[1] for x in o),min(x[2] for x in o)

def fast_trap_signals(bars,accelerated):
    """Return first completed 5s reentry strictly AFTER each T01 breakout.

    Missing 5s bars terminate the detection path, rather than getting
    interpolated after data gaps. 60s and 2-tick reentry are pre-registered.
    """
    hi,lo=opening_levels(bars)
    signals=[]
    last_confirm=-1
    for i,break_side in accelerated:
        if not (OR_END<=i<LAST_SIGNAL) or break_side not in (-1,1):
            raise ValueError('Bad original T01 signal')
        for j in range(i+1,min(i+13,LAST_SIGNAL)):
            if bars[j] is None:break
            c=bars[j][3]  # completed 5s Last bar, never intrabar
            reentered=(c<=hi-2 if break_side==1 else c>=lo+2)
            if reentered:
                if j<=last_confirm:raise ValueError('Duplicate/out-of-order confirmation')
                signals.append((j,-break_side))
                last_confirm=j
                break
    return signals

def combine_signals(t05,t09):
    """One signal/decision bar: fixed T05 priority, no outcome selection.

    Execution-level overlap, daily capacity, and daily-stop handled by
    original T04 simulator. The combined router never doubles position size.
    """
    tags=[(i,0,side,'T05_377') for i,side in t05]
    tags.extend((i,1,side,'T09_FAST_TRAP_60S') for i,side in t09)
    tags.sort(key=lambda x:(x[0],x[1]))
    result=[];skipped_equal_timestamp=0;last=None
    for i,priority,side,owner in tags:
        if side not in (-1,1):raise ValueError('Bad side')
        if last==i:
            skipped_equal_timestamp+=1
            continue
        result.append((i,side,owner))
        last=i
    return result,skipped_equal_timestamp

def replay_router_attribution(day,events,bars,tagged,scenario):
    """Parity-check router against SAME T04 fills/costs and record owner totals.

    Attribution is ONLY of simulated net fills; never logs private timestamps
    or per-trade prices into GitHub Actions.
    """
    d=dev_day(day)
    lo,_=utc_bounds(d)
    opening=opening_width(bars)
    if opening is None:raise ValueError('Opening missing')
    policy=risk_policy(opening,scenario)
    times=[e[0] for e in events]
    if any(a>b for a,b in zip(times,times[1:])):
        raise ValueError('Last data not chronological')
    pnl=0.;gains=[];last_exit=-1;overlap=capacity=invalid=0;aborted=False
    contributions={o:{'trades':0,'net_usd':0.0} for o in OWNERS}
    for i,side,owner in tagged:
        if owner not in OWNERS:raise ValueError('Unexpected owner')
        if len(gains)>=MAX_TRADES_PER_DAY or pnl<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            capacity+=1
            continue
        signal_t=lo+(i+1)*STEP_100NS
        if signal_t<=last_exit:
            overlap+=1
            continue
        r=simulate_single_trade(islice(events,bisect_right(times,signal_t),None),
                                Signal(day,signal_t,side),policy)
        if r['status']!='SYNTHETIC_FILL_MODEL_ONLY':
            invalid+=1
            if r['status'] in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',
                              'UNRESOLVED_END_OF_LAST_DATA'):
                aborted=True
                break
            continue
        value=r['estimated_net_usd']
        gains.append(value)
        pnl=round(pnl+value,2)
        contributions[owner]['trades']+=1
        contributions[owner]['net_usd']=round(contributions[owner]['net_usd']+value,2)
        last_exit=r['exit_timestamp']
    return {
        'trades':len(gains),'net_usd':round(sum(gains),2),
        'wins':sum(x>0 for x in gains),'losses':sum(x<0 for x in gains),
        'total_positive_usd':round(sum(x for x in gains if x>0),2),
        'total_negative_usd':round(-sum(x for x in gains if x<0),2),
        'unknown_entry_or_exit':invalid,
        'day_aborted_due_to_ambiguity':aborted,
        'skipped_overlap':overlap,
        'skipped_max_two_or_daily_stop':capacity,
        'contributions':contributions
    }

def analyze_events(events,day):
    dev_day(day) # holdout guard BEFORE looking at events
    bars=build_bars(events,day)
    sig,status=candidates(bars,day)
    if status!='READY':
        return {'date_et':day,'status':status,'families':{},
            'holdout_2026_may_sep_opened':False}
    initial=sig['T01_combined']
    raw=[(i,-s) for i,s in initial]
    confirmed=fast_trap_signals(bars,initial)
    parent=sig['T02_combined']
    flags=filters_for_signals(events,day,parent)
    t05=selected_families(parent,flags)['T05_377']
    tagged,duplicates=combine_signals(t05,confirmed)
    choices={
        'T01_CONT':initial,
        'T09_RAW_FADE':raw,
        'T09_FAST_TRAP_60S':confirmed,
        'T05_377':t05,
        'T09_NQ_COMBINED_ROUTER':[(i,s) for i,s,_ in tagged]
    }
    outputs={}
    for fam in PORTFOLIOS:
        outputs[fam]={'opportunities':len(choices[fam]),'scenarios':{}}
        for sc in SCENARIOS:
            x=simulate_portfolio(day,events,bars,choices[fam],sc)
            if fam=='T09_NQ_COMBINED_ROUTER':
                attribution=replay_router_attribution(day,events,bars,tagged,sc)
                for key in ('trades','net_usd','wins','losses','total_positive_usd',
                            'total_negative_usd','unknown_entry_or_exit',
                            'day_aborted_due_to_ambiguity','skipped_overlap',
                            'skipped_max_two_or_daily_stop'):
                    if x[key]!=attribution[key]:
                        raise AssertionError('Frozen T04 parity failed: '+day+':'+fam+':'+sc+':'+key)
                x['owner_contributions']=attribution['contributions']
            outputs[fam]['scenarios'][sc]=x
    return {'date_et':day,'status':'T09_POST_SELECTION_EXPLORATORY',
        'original_fast_breakout_opportunities':len(initial),
        'fast_trap_confirmations':len(confirmed),
        't05_377_opportunities':len(t05),
        'duplicate_decision_timestamp_t05_priority':duplicates,
        'families':outputs,'private_data_exported':False,
        'live_fills_or_funded_rules_verified':False,
        'holdout_2026_may_sep_opened':False}

def analyze_day(root,day):
    d=dev_day(day)
    return analyze_events(list(source_events(file_for(root,d,'Last'))),day)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--day',required=True)
    a=parser.parse_args()
    r=analyze_day(a.root,a.day)
    # Day-level timestamps/prices suppressed: only aggregate output by month.
    print('T09_DAY_STATUS='+r['status'])
