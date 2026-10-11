#!/usr/bin/env python3
"""DEV month T13 high-volume shock/retracement NQ + one T05-priority router.

Reuses frozen T04 trace from B05; publishes only aggregate counters and envelopes.
"""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day,build_bars,candidates
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t05_fibonacci_bars import filters_for_signals,selected_families
from nq_t04_execution import SCENARIOS,simulate_portfolio
from nq_t08_risk_audit import Envelope
from nq_t10_t05_bbo_endpoints import SKIPS
from nq_b05_t11_month import trace,counter
from nq_b05c_t13_shock import FAMILIES,candidates_t13

BASE='T05_377'
NEW='T13_FULL'
ROUTER='T05_PLUS_T13_ROUTER'
MODELS=(BASE,*FAMILIES,ROUTER)
STRESS='stress_1p5_fee_2ticks_each_side'

def shared_signals(t05,t13):
    signals=sorted([(i,0,s,BASE) for i,s in t05]+
                   [(i,1,s,NEW) for i,s in t13])
    output=[];last_i=None;ties=0
    for i,_,side,owner in signals:
        if i==last_i:
            ties+=1
            continue
        output.append((i,side,owner))
        last_i=i
    return output,ties

def analyze_month(root,month):
    if month not in MONTHS:
        raise ValueError('SEALED_MONTH_REJECTED_BEFORE_FS')
    days=sorted(month_days(root,month))
    tracks={m:{sc:Envelope() for sc in SCENARIOS} for m in MODELS}
    extras={m:Envelope() for m in MODELS}
    rows={m:{sc:{
        'opportunities':0,'overlap':0,'capacity':0,
        'counter':counter(),'attribution':defaultdict(counter),
        'extra_counter':counter(),'extra_attribution':defaultdict(counter)}
        for sc in SCENARIOS} for m in MODELS}
    status=Counter();tie_count=0;ambiguous_side=0
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        bars=build_bars(events,day)
        old,status_day=candidates(bars,day)
        if status_day in SKIPS:
            status[status_day]+=1
            continue
        if status_day!='READY':raise ValueError('Unrecognized source status')
        status['READY']+=1
        parent=old['T02_combined']
        t05=selected_families(parent,filters_for_signals(events,day,parent))[BASE]
        new,amb=candidates_t13(bars,day)
        if any(len(v)>1 for v in new.values()):
            raise AssertionError('T13 must emit at most 1 candidate per day/model')
        ambiguous_side+=amb
        router,ties=shared_signals(t05,new[NEW]);tie_count+=ties
        choices={BASE:[(i,s,BASE) for i,s in t05],
                 ROUTER:router}
        choices.update({m:[(i,s,m) for i,s in new[m]] for m in FAMILIES})
        for model,signals in choices.items():
            for sc in SCENARIOS:
                x=trace(day,events,bars,signals,sc,tracks[model][sc],
                    extras[model] if sc==STRESS else None)
                # T04 parity on exact same signals, costs, stops and daily capacity.
                parity=simulate_portfolio(day,events,bars,[(i,s) for i,s,_ in signals],sc)
                for key in ('trades','net_usd','wins','losses','total_positive_usd',
                   'total_negative_usd','unknown_entry_or_exit',
                   'day_aborted_due_to_ambiguity','skipped_overlap',
                   'skipped_max_two_or_daily_stop'):
                    if x[key]!=parity[key]:
                        raise AssertionError(f'T04 replay mismatch {day}/{model}/{sc}/{key}')
                if x['unknown_entry_or_exit'] or x['day_aborted_due_to_ambiguity']:
                    raise ValueError('Unresolved Last execution - reject')
                r=rows[model][sc]
                r['opportunities']+=len(signals)
                r['overlap']+=x['skipped_overlap']
                r['capacity']+=x['skipped_max_two_or_daily_stop']
                for owner,counts in x['owner_counters'].items():
                    for key,val in counts.items():
                        r['attribution'][owner][key]+=val
                        r['counter'][key]+=val
                if sc==STRESS:
                    for owner,counts in x['owner_counters_extra'].items():
                        for key,val in counts.items():
                            r['extra_attribution'][owner][key]+=val
                            r['extra_counter'][key]+=val
    if ambiguous_side:raise ValueError('Both sides simultaneously signaled - logic error')
    if status['READY']+sum(status[k] for k in SKIPS)!=len(days):
        raise AssertionError('Monthly day count reconciliation failed')
    outputs={}
    for model in MODELS:
        outputs[model]={}
        for sc in SCENARIOS:
            r=rows[model][sc];v=r['counter'];t=tracks[model][sc]
            if abs(v['net_cents']/100-t.equity)>.01:
                raise AssertionError('Last envelope inconsistent with account balance')
            result={
                'opportunities':r['opportunities'],
                'trades':v['trades'],
                'net_usd':round(v['net_cents']/100,2),
                'positive_usd':round(v['positive_cents']/100,2),
                'negative_usd':round(v['negative_cents']/100,2),
                'wins':v['wins'],'losses':v['losses'],
                'skipped_overlap':r['overlap'],
                'skipped_capacity':r['capacity'],
                'owner_attribution':{
                    k:{'trades':z['trades'],'net_usd':round(z['net_cents']/100,2)}
                    for k,z in r['attribution'].items()},
                'last_envelope_segment':t.segment()}
            if sc==STRESS:
                ex=r['extra_counter'];te=extras[model]
                if ex['trades']!=v['trades'] or (
                    ex['net_cents']!=v['net_cents']-v['trades']*1000):
                    raise AssertionError('Extra fixed $10 RT not conserved')
                if abs(ex['net_cents']/100-te.equity)>.01:
                    raise AssertionError('Extra-cost Last tracker inconsistent')
                result['stress_extra_10usd_fixed_path']={
                    'trades':ex['trades'],
                    'net_usd':round(ex['net_cents']/100,2),
                    'positive_usd':round(ex['positive_cents']/100,2),
                    'negative_usd':round(ex['negative_cents']/100,2),
                    'owner_attribution':{
                        k:{'trades':z['trades'],'net_usd':round(z['net_cents']/100,2)}
                        for k,z in r['extra_attribution'].items()},
                    'last_envelope_segment':te.segment(),
                    'stops_or_daily_risk_recomputed':False}
            outputs[model][sc]=result
    return {
        'month':month,'status':'NQ_B05C_T13_EXPLORATORY_DEV_ONLY',
        'source_days':len(days),'eligible_days':status['READY'],
        'excluded_days':len(days)-status['READY'],
        'same_bar_t05_priority_ties':tie_count,
        'models':outputs,
        'holdouts_opened':False,'broker_fills_verified':False,
        'raw_tick_or_trade_level_exported':False,
        'source_sequenced_quotes_used':False
    }

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--month',required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.month not in MONTHS:raise SystemExit('SEALED_OR_FORBIDDEN_MONTH')
    x=analyze_month(args.root,args.month)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('NQ_B05B_SAFE_MONTH='+json.dumps({
        'month':args.month,'eligible':x['eligible_days'],
        'trades':{m:z[STRESS]['trades'] for m,z in x['models'].items()},
        'status':x['status']},sort_keys=True))
