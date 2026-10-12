#!/usr/bin/env python3
"""T20–T25 stage1, preregistered case/control Last DEV outcomes.
PRIVATE daily labels/fills are ephemeral. Publication ONLY via safe aggregator.
Never access T 2026-05..09, H 2025..26 reserved, or 5-second NEW signals.
"""
from __future__ import annotations
import argparse,json
from bisect import bisect_right
from collections import Counter,defaultdict
from itertools import islice
from pathlib import Path

from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_b05h01_trade_expansion_month import frozen_t05,BASE,STRESS
from nq_t20_t25_fixed_anchor_screen import (
    IDS,CASE,CONTROL,OTHER,MISSING,detect)
from nq_t14_t19_economic_and_magnitude import combined,EXPECTED
from nq_t04_execution import (
    SCENARIOS,MAX_TRADES_PER_DAY,STOP_NEW_ENTRIES_AFTER_DAILY_USD,
    risk_policy,opening_width)
from sim_nq_last_execution_skeleton import FillPolicy,Signal,simulate_single_trade
from nq_t08_risk_audit import Envelope,mark_trade_envelope
from nq_b05_t11_month import counter,add_result

MAG='T23_TEMPO_DECELERATION'
DIRECTIONAL=tuple(k for k in IDS if k!=MAG)
CASE_NAMES={k:k+'_CASE' for k in DIRECTIONAL}
CTRL_NAMES={k:k+'_CONTROL' for k in DIRECTIONAL}
ROUTERS={k:'T05_PLUS_'+k+'_CASE' for k in DIRECTIONAL}
MODELS=(BASE,*CASE_NAMES.values(),*CTRL_NAMES.values(),*ROUTERS.values())
HORIZON_NS=15*60*10_000_000
EXTRA_RT=10.

# Stage0 aggregations were known BEFORE reading any stage1 outcome.
SCREEN_COUNTS={
 'T20_BAR_VALUE_SKEW':(0,100),
 'T21_EXTREME_REJECTION':(38,40),
 'T22_QTY_WITH_PROGRESS':(1,113),
 'T23_TEMPO_DECELERATION':(1,8),
 'T24_SIGN_ALTERNATION':(39,50),
 'T25_CROSS_SCALE_DIVERGENCE':(47,59)}

def first_decision(events,day):
    """Use frozen stage0 labels; private timestamps may NEVER leave runner."""
    dev_day(day)
    # Rebuild once per DAY, exclusively causal 233/377/4181 prints.
    from nq_b05h_atomic_print_bars import completed_bars_by_print_count
    from nq_b05h01_trade_expansion_month import et_edge
    from bisect import bisect_left
    from nq_t20_t25_fixed_anchor_screen import classify
    bars=completed_bars_by_print_count(events,day,(233,377,4181))
    lo,hi=et_edge(day,10,0),et_edge(day,10,15)
    found=next((i for i,b in enumerate(bars[377])
                if lo<=b.end_timestamp<hi),None)
    if found is None or found<4:
        return {k:(MISSING,0) for k in IDS},None
    a,b,c,d,e=bars[377][found-4:found+1]
    if not (a.end_timestamp<b.end_timestamp<c.end_timestamp<
            d.end_timestamp<e.end_timestamp):
        raise ValueError('causal groups time/order mismatch')
    before={}
    for n in (233,4181):
        pool=bars[n]
        ix=bisect_left([q.end_timestamp for q in pool],e.end_timestamp)
        before[n]=pool[max(0,ix-2):ix]
    states=classify(a,b,c,d,e,before[233],before[4181])
    # Assert parity with exactly same stage0 detector, not different triggers.
    stage0,anchored=detect(events,day)
    if not anchored or stage0!=states:
        raise AssertionError('STAGE0 SIGNALS CHANGED')
    return states,e.end_timestamp

def future_range(events,times,t):
    if t is None or times[-1]<t+HORIZON_NS:
        raise ValueError('T23 INCOMPLETE FUTURE 15MIN ENDPOINT FAIL CLOSED')
    a=bisect_right(times,t)
    b=bisect_right(times,t+HORIZON_NS)
    if b<=a:
        raise ValueError('T23 no Last events in forward window')
    prices=[e[1] for e in events[a:b]]
    return max(prices)-min(prices)

def policy(who,old_bars):
    if who==BASE:
        return risk_policy(opening_width(old_bars),STRESS)
    if who not in DIRECTIONAL:
        raise ValueError('Unknown NQ T20–25 owner')
    slip,fee=SCENARIOS[STRESS]
    return FillPolicy(latency_ms=1,entry_slippage_ticks=slip,
        exit_slippage_ticks=slip,stop_ticks=32,take_profit_ticks=48,
        max_holding_seconds=300,commission_round_trip_usd=fee,contracts=1)

def route(day,events,times,old_bars,tagged,tracker):
    """Frozen conservative Last fill; single account, no ambiguous fills."""
    dev_day(day)
    result=counter()
    xtra=counter()
    owners=defaultdict(counter)
    skipped=Counter()
    closed_pnl=0.
    last_exit=-1
    for tm,side,who in tagged:
        if side not in (-1,1):
            raise AssertionError('cannot trade side0')
        if result['trades']>=MAX_TRADES_PER_DAY or closed_pnl<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            skipped['capacity']+=1
            continue
        if tm<=last_exit:
            skipped['overlap']+=1
            continue
        p=policy(who,old_bars)
        fill=simulate_single_trade(islice(events,bisect_right(times,tm),None),
                Signal(day,tm,side),p)
        if fill['status']!='SYNTHETIC_FILL_MODEL_ONLY':
            if fill['status'] in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',
                                  'UNRESOLVED_END_OF_LAST_DATA'):
                raise ValueError('T20_T25_AMBIGUOUS_EXECUTION_FAIL_CLOSED')
            skipped['no_entry']+=1
            continue
        mark_trade_envelope(events,times,fill,side,p,tracker)
        pnl=fill['estimated_net_usd']
        add_result(result,pnl)
        add_result(xtra,pnl-EXTRA_RT)
        add_result(owners[who],pnl)
        closed_pnl=round(closed_pnl+pnl,2)
        last_exit=fill['exit_timestamp']
    if xtra['trades']!=result['trades'] or xtra['net_cents']!=(
            result['net_cents']-1000*result['trades']):
        raise AssertionError('extra10 RT same-path parity')
    return result,xtra,owners,skipped

def month_stage(root,month,private_out):
    if month not in MONTHS:
        raise ValueError('SEALED MONTH DENIED BEFORE ANY SOURCE READ')
    days=sorted(month_days(root,month))
    tracking={k:Envelope() for k in MODELS}
    agg={k:{'stress':counter(),'extra':counter(),'owners':defaultdict(counter),
            'capacity':0,'overlap':0,'no_entry':0}
         for k in MODELS}
    categories={k:Counter() for k in IDS}
    magnitude={CASE:{'n':0,'sum_ticks':0},CONTROL:{'n':0,'sum_ticks':0}}
    daily=[]
    qc=Counter()
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        status,oldbars,t05=frozen_t05(events,day)
        qc[status]+=1
        if status!='READY':
            daily.append({'day':day,'eligible':False})
            continue
        times=[e[0] for e in events]
        states,t=first_decision(events,day)
        if t is None:
            raise AssertionError('NO ANCHOR for eligible DEV session')
        for k,(state,side) in states.items():
            categories[k][state]+=1
        if states[MAG][0] in (CASE,CONTROL):
            rr=future_range(events,times,t)
            d=magnitude[states[MAG][0]]
            d['n']+=1
            d['sum_ticks']+=rr
        tags={BASE:t05}
        for k in DIRECTIONAL:
            st,side=states[k]
            one=[(t,side,k)] if st==CASE and side else []
            zero=[(t,side,k)] if st==CONTROL and side else []
            tags[CASE_NAMES[k]]=one
            tags[CTRL_NAMES[k]]=zero
            tags[ROUTERS[k]]=combined(t05,one)
        detail={'day':day,'eligible':True,
                'labels':{k:states[k][0] for k in IDS},
                'models':{},'future_range_T23_ticks':(
                   rr if states[MAG][0] in (CASE,CONTROL) else None)}
        for model,tagged in tags.items():
            pre=tracking[model].equity
            c,extra,owners,skips=route(day,events,times,oldbars,tagged,tracking[model])
            z=agg[model]
            z['stress'].update(c)
            z['extra'].update(extra)
            for own,ct in owners.items():
                z['owners'][own].update(ct)
            for name in ('capacity','overlap','no_entry'):
                z[name]+=skips[name]
            if round((tracking[model].equity-pre)*100)!=c['net_cents']:
                raise AssertionError('private daily amount/equity mismatch')
            detail['models'][model]={'trades':c['trades'],
                'stress_cents':c['net_cents'],'extra_cents':extra['net_cents']}
        daily.append(detail)
    source=len(days)
    eligible=qc['READY']
    if source!=sum(qc.values()):
        raise ValueError('QC/source count inconsistent')
    if (sum(d['models'][BASE]['trades'] for d in daily if d['eligible']),
        round(sum(d['models'][BASE]['stress_cents'] for d in daily
                  if d['eligible'])/100,2))!=EXPECTED[month]:
        raise AssertionError('T05 monthly benchmark changed')
    result={'status':'T20_T25_STAGE1_DEV_PRIVATE_OUTCOMES',
       'month':month,'source':source,'eligible':eligible,
       'not_eligible':source-eligible,'category_counts':{
           k:{x:categories[k][x] for x in (CASE,CONTROL,OTHER,MISSING)}
           for k in IDS},'models':{},'magnitude':magnitude,
       'holdouts_opened':False,'new_history_acquired':False,
       'five_second_new_signals':False,'broker_fill_verified':False,
       'daily_or_trade_rows_public':False}
    for model in MODELS:
        z=agg[model]
        c,e=z['stress'],z['extra']
        if round(tracking[model].equity*100)!=c['net_cents']:
            raise AssertionError('monthly envelope/ledger mismatch')
        result['models'][model]={
            'trades':c['trades'],'net_usd':c['net_cents']/100,
            'positive_usd':c['positive_cents']/100,
            'negative_usd':c['negative_cents']/100,
            'wins':c['wins'],'losses':c['losses'],
            'net_extra10_usd':e['net_cents']/100,
            'extra_positive_usd':e['positive_cents']/100,
            'extra_negative_usd':e['negative_cents']/100,
            'last_envelope_segment':tracking[model].segment(),
            'owners':{k:{'trades':v['trades'],'net_usd':v['net_cents']/100}
                      for k,v in z['owners'].items()},
            'capacity':z['capacity'],'overlap':z['overlap'],
            'no_entry':z['no_entry']}
    private_out.parent.mkdir(parents=True,exist_ok=True)
    if private_out.exists():
        raise ValueError('do not overwrite private daily artifacts')
    private_out.write_text(json.dumps({'safe':result,'private_daily':daily},
                                      separators=(',',':'))+'\n')
    return {'month':month,'source':source,'eligible':eligible,
            'cases':{k:categories[k][CASE] for k in IDS},
            'trades_case':{k:result['models'][CASE_NAMES[k]]['trades']
                           for k in DIRECTIONAL},
            'T05_parity':True,'market_rows_private':True}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--month',required=True)
    p.add_argument('--private-out',required=True,type=Path)
    args=p.parse_args()
    if args.month not in MONTHS:
        raise SystemExit('SEALED BEFORE FILES')
    print('T20_T25_MONTH_SAFE='+json.dumps(
        month_stage(args.root,args.month,args.private_out),sort_keys=True))
