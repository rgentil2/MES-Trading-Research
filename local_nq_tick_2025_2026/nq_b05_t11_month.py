#!/usr/bin/env python3
"""B05 NQ T11 DEV replay: independent VWAP control and ONE shared T05 router.

All generated results are MONTHLY COUNTERS and Last envelopes, never per-trade
data. No historical holdout or broker fill claims.
"""
from __future__ import annotations
import argparse,json
from bisect import bisect_right
from collections import Counter,defaultdict
from dataclasses import replace
from itertools import islice
from pathlib import Path
from qc_tick_day import file_for,utc_bounds
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day,build_bars,candidates,STEP_100NS
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t05_fibonacci_bars import filters_for_signals,selected_families
from nq_t04_execution import (SCENARIOS,MAX_TRADES_PER_DAY,
    STOP_NEW_ENTRIES_AFTER_DAILY_USD,opening_width,risk_policy,simulate_portfolio)
from nq_t08_risk_audit import Envelope,mark_trade_envelope
from nq_t10_t05_bbo_endpoints import SKIPS
from sim_nq_last_execution_skeleton import Signal,simulate_single_trade
from nq_b05_t11_vwap import t11_signals,MODELS as T11_MODELS

ROUTER='T05_PLUS_T11_ROUTER'
BASE='T05_377'
MODELS=(BASE,*T11_MODELS,ROUTER)
EXTRA_RT_STRESS_USD=10.0
EXPECTED_T05={'baseline':(115,6220.0),
    'stress_1p5_fee_2ticks_each_side':(115,5102.5)}

def tagged_signals(t05,t11):
    """One decision per 5s bar, fixed T05 tie priority independent of outcomes."""
    candidates=[(i,0,s,BASE) for i,s in t05]
    candidates.extend((i,1,s,'T11_FULL') for i,s in t11)
    candidates.sort(key=lambda x:(x[0],x[1]))
    result=[];ties=0;last_i=None
    for i,_,side,owner in candidates:
        if side not in (-1,1):raise ValueError('Side not valid')
        if i==last_i:
            ties+=1;continue
        result.append((i,side,owner))
        last_i=i
    return result,ties

def counter():
    return Counter(trades=0,wins=0,losses=0,net_cents=0,
                   positive_cents=0,negative_cents=0)

def add_result(c,pnl):
    cents=int(round(100*pnl))
    c['trades']+=1;c['net_cents']+=cents
    c['wins']+=int(cents>0);c['losses']+=int(cents<0)
    c['positive_cents']+=max(0,cents);c['negative_cents']+=max(0,-cents)

def trace(day,events,bars,tagged,sc,tracker,tracker_extra=None):
    """Follow frozen T04 daily equity, with no overlap, 2/day and shared stop."""
    dev_day(day)
    lo,_=utc_bounds(dev_day(day))
    policy=risk_policy(opening_width(bars),sc)
    policy_extra=replace(policy,commission_round_trip_usd=
                         policy.commission_round_trip_usd+EXTRA_RT_STRESS_USD)
    ts=[e[0] for e in events]
    if any(a>b for a,b in zip(ts,ts[1:])):raise ValueError('Nonchronological Last')
    outcomes=[];attribution=defaultdict(counter)
    attr_extra=defaultdict(counter)
    skips=Counter();pnl=0.;last_exit=-1;abort=False
    for i,side,owner in tagged:
        if len(outcomes)>=MAX_TRADES_PER_DAY or pnl<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            skips['capacity']+=1;continue
        sig_t=lo+(i+1)*STEP_100NS
        if sig_t<=last_exit:
            skips['overlap']+=1;continue
        r=simulate_single_trade(islice(events,bisect_right(ts,sig_t),None),
                                Signal(day,sig_t,side),policy)
        if r['status']!='SYNTHETIC_FILL_MODEL_ONLY':
            skips['invalid']+=1
            if r['status'] in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',
                              'UNRESOLVED_END_OF_LAST_DATA'):
                abort=True;break
            continue
        mark_trade_envelope(events,ts,r,side,policy,tracker)
        gain=r['estimated_net_usd']
        if tracker_extra is not None:
            mod=dict(r)
            mod['estimated_net_usd']=round(gain-EXTRA_RT_STRESS_USD,2)
            mark_trade_envelope(events,ts,mod,side,policy_extra,tracker_extra)
            add_result(attr_extra[owner],mod['estimated_net_usd'])
        outcomes.append(gain)
        add_result(attribution[owner],gain)
        pnl=round(pnl+gain,2)
        last_exit=r['exit_timestamp']
    gains=outcomes
    return {
        'trades':len(gains),'net_usd':round(sum(gains),2),
        'wins':sum(v>0 for v in gains),'losses':sum(v<0 for v in gains),
        'total_positive_usd':round(sum(v for v in gains if v>0),2),
        'total_negative_usd':round(-sum(v for v in gains if v<0),2),
        'unknown_entry_or_exit':skips['invalid'],
        'day_aborted_due_to_ambiguity':abort,
        'skipped_overlap':skips['overlap'],
        'skipped_max_two_or_daily_stop':skips['capacity'],
        'owner_counters':{k:dict(v) for k,v in attribution.items()},
        'owner_counters_extra':{k:dict(v) for k,v in attr_extra.items()},
    }

def monthly_audit(root,month):
    if month not in MONTHS:raise ValueError('SEALED_OR_FORBIDDEN_MONTH')
    days=sorted(month_days(root,month))
    trackers={m:{s:Envelope() for s in SCENARIOS} for m in MODELS}
    extra_trackers={m:Envelope() for m in MODELS}
    rows={m:{s:{'aggregate':counter(),'opportunities':0,'overlap':0,
                'capacity':0,'owner_counters':defaultdict(counter),
                'extra_accounting':counter(),'extra_owner_counters':defaultdict(counter)}
             for s in SCENARIOS} for m in MODELS}
    ties=0;statuses=Counter();t11_ops=Counter();t05_ops=0
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        bars=build_bars(events,day)
        source,status=candidates(bars,day)
        if status in SKIPS:
            statuses[status]+=1;continue
        if status!='READY':raise ValueError('Source QC problem')
        statuses['READY']+=1
        parent=source['T02_combined']
        t05=selected_families(parent,filters_for_signals(events,day,parent))[BASE]
        new,conflicts=t11_signals(events,bars,day)
        if any(conflicts.values()):
            raise ValueError('Impossible opposing VWAP signal detected')
        tagged,tied=tagged_signals(t05,new['T11_FULL'])
        ties+=tied;t05_ops+=len(t05)
        for m in T11_MODELS:t11_ops[m]+=len(new[m])
        choices={
            BASE:[(i,s,BASE) for i,s in t05],
            ROUTER:tagged,
        }
        for m in T11_MODELS:choices[m]=[(i,s,m) for i,s in new[m]]
        for m in MODELS:
            candidate=choices[m]
            for sc in SCENARIOS:
                tracker=trackers[m][sc]
                extra=extra_trackers[m] if sc=='stress_1p5_fee_2ticks_each_side' else None
                res=trace(day,events,bars,candidate,sc,tracker,extra)
                cmp=simulate_portfolio(day,events,bars,[(i,s) for i,s,_ in candidate],sc)
                for key in ('trades','net_usd','wins','losses','total_positive_usd',
                     'total_negative_usd','unknown_entry_or_exit',
                     'day_aborted_due_to_ambiguity','skipped_overlap',
                     'skipped_max_two_or_daily_stop'):
                    if res[key]!=cmp[key]:
                        raise AssertionError(f'Frozen T04 parity {day}/{m}/{sc}/{key}')
                if res['unknown_entry_or_exit'] or res['day_aborted_due_to_ambiguity']:
                    raise ValueError('Unknown execution - fail closed')
                dest=rows[m][sc]
                dest['opportunities']+=len(candidate)
                dest['overlap']+=res['skipped_overlap']
                dest['capacity']+=res['skipped_max_two_or_daily_stop']
                agg=dest['aggregate']
                for key,v in res['owner_counters'].items():
                    for field,num in v.items():
                        dest['owner_counters'][key][field]+=num
                        agg[field]+=num
                if extra is not None:
                    for key,v in res['owner_counters_extra'].items():
                        for field,num in v.items():
                            dest['extra_owner_counters'][key][field]+=num
                            dest['extra_accounting'][field]+=num
    if statuses['READY']+sum(statuses[k] for k in SKIPS)!=len(days):
        raise AssertionError('Missing daily data')
    output={}
    for m in MODELS:
        output[m]={}
        for sc in SCENARIOS:
            r=rows[m][sc]
            z=r['aggregate'];tracker=trackers[m][sc]
            net=round(z['net_cents']/100,2)
            if abs(net-tracker.equity)>.01:
                raise AssertionError('Envelope monthly equity mismatch')
            record={
                'opportunities':r['opportunities'],
                'trades':z['trades'],'net_usd':net,
                'wins':z['wins'],'losses':z['losses'],
                'positive_usd':round(z['positive_cents']/100,2),
                'negative_usd':round(z['negative_cents']/100,2),
                'skipped_overlap':r['overlap'],
                'skipped_capacity':r['capacity'],
                'owner_attribution':{k:{
                    'trades':v['trades'],
                    'net_usd':round(v['net_cents']/100,2)}
                    for k,v in r['owner_counters'].items()},
                'last_envelope_segment':tracker.segment(),
            }
            if sc=='stress_1p5_fee_2ticks_each_side':
                e=r['extra_accounting'];tr=extra_trackers[m]
                if e['trades']!=z['trades'] or (e['net_cents']!=
                    z['net_cents']-round(100*EXTRA_RT_STRESS_USD)*z['trades']):
                    raise AssertionError('Stress extra surcharge not conserved')
                if abs(e['net_cents']/100-tr.equity)>.01:
                    raise AssertionError('Extra surcharge tracker out of sync')
                record['stress_extra_10usd_fixed_path']={
                    'trades':e['trades'],
                    'net_usd':round(e['net_cents']/100,2),
                    'positive_usd':round(e['positive_cents']/100,2),
                    'negative_usd':round(e['negative_cents']/100,2),
                    'last_envelope_segment':tr.segment(),
                    'owner_attribution':{k:{
                        'trades':v['trades'],
                        'net_usd':round(v['net_cents']/100,2)}
                        for k,v in r['extra_owner_counters'].items()},
                    'stops_or_daily_risk_recomputed':False}
            output[m][sc]=record
    return {
        'month':month,'status':'B05_T11_DEV_EXPLORATORY_LAST_ONLY',
        'source_days':len(days),'eligible_days':statuses['READY'],
        'excluded_days':len(days)-statuses['READY'],
        't05_signal_opportunities':t05_ops,
        't11_signal_opportunities':dict(t11_ops),
        'same_bar_t05_priority_ties':ties,
        'models':output,
        'holdouts_opened':False,'broker_fills_verified':False,
        'trade_level_exported':False,'source_sequenced_quotes_used':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--month',required=True)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('SEALED_MONTH_DENIED')
    r=monthly_audit(a.root,a.month)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('NQ_B05_SAFE_MONTH='+json.dumps({
        'month':a.month,'eligible_days':r['eligible_days'],
        'trades':{m:r['models'][m]['stress_1p5_fee_2ticks_each_side']['trades'] for m in MODELS},
        'status':r['status']},sort_keys=True))
