#!/usr/bin/env python3
"""B05H-01 fixed, preregistered transaction-bar expansion+trend (NO 5s signal).

Only existing seven DEV Last releases. Legacy T05 uses its old 5s signal
*only as a fixed benchmark*, never as part of H01 candidate construction.
One shared-account risk for router. Aggregate-only safe monthly output.
"""
from __future__ import annotations
import argparse,json
from bisect import bisect_left,bisect_right
from collections import Counter,defaultdict
from dataclasses import replace
from datetime import datetime,time,timezone
from itertools import islice
from pathlib import Path
from zoneinfo import ZoneInfo
from qc_tick_day import file_for,utc_bounds
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day,build_bars,candidates,STEP_100NS
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t05_fibonacci_bars import filters_for_signals,selected_families
from nq_t04_execution import (
    SCENARIOS,risk_policy,opening_width,MAX_TRADES_PER_DAY,
    STOP_NEW_ENTRIES_AFTER_DAILY_USD)
from sim_nq_last_execution_skeleton import (
    FillPolicy,Signal,simulate_single_trade,ONE_MS)
from nq_t08_risk_audit import Envelope,mark_trade_envelope
from nq_b05_t11_month import counter,add_result
from nq_b05h_atomic_print_bars import completed_bars_by_print_count,prior_completed_context

BASE='T05_377'
NEW='H01_PRINT_EXPANSION_CONTINUATION'
ROUTER='T05_PRIORITY_SHARED_ROUTER'
MODELS=(BASE,NEW,ROUTER)
STRESS='stress_1p5_fee_2ticks_each_side'
EXTRA_RT=10.0
LENGTHS=(233,4181,10946)
TEN_MIN_100NS=600*10_000_000
FORTY_MIN_100NS=2400*10_000_000
SIXTY_MIN_100NS=3600*10_000_000

def et_edge(day,h,m):
    d=dev_day(day)
    dt=datetime.combine(d,time(h,m),tzinfo=ZoneInfo('America/New_York'))
    return int(dt.astimezone(timezone.utc).timestamp())*10_000_000

def slope_at_least(b,a,side,ticks):
    """VWAP(b)-VWAP(a) >= +ticks if side=+1, <= -ticks if -1."""
    if side not in (-1,1) or ticks<0:raise ValueError('bad slope comparison')
    return side*(b.price_times_qty_ticks*a.total_qty -
                 a.price_times_qty_ticks*b.total_qty) >= ticks*b.total_qty*a.total_qty

def h01_candidates(events,day):
    """Events source order may tie timestamps; hypothesis is tie permutation invariant.

    Return (decision_timestamp_UTC100ns, side), max two/day, 10min apart.
    NOT on 5-second or minute bars. Emits no order in a tied timestamp group.
    """
    dev_day(day) # reject sealed before events touched
    series=completed_bars_by_print_count(events,day,LENGTHS)
    shorts=series[233]
    medium=series[4181]
    longs=series[10946]
    medium_ends=[b.end_timestamp for b in medium]
    long_ends=[b.end_timestamp for b in longs]
    start=et_edge(day,9,30)
    end=et_edge(day,11,15)
    signals=[]
    examined=0
    context_ready=0
    structural=0
    for idx in range(2,len(shorts)):
        a,b,c=shorts[idx-2:idx+1]
        t=c.end_timestamp
        if t<start or t>=end:continue
        examined+=1
        med_k=bisect_left(medium_ends,t)
        long_k=bisect_left(long_ends,t)
        if med_k<2 or long_k<2: continue
        med0,med1=medium[med_k-2:med_k]
        lng0,lng1=longs[long_k-2:long_k]
        if (t-med1.end_timestamp>FORTY_MIN_100NS or
            t-lng1.end_timestamp>SIXTY_MIN_100NS):
            continue
        context_ready+=1
        dr=c.end_timestamp-c.start_timestamp
        prev_duration=b.end_timestamp-b.start_timestamp
        if dr<=0 or prev_duration<=0 or 5*dr>4*prev_duration:
            continue
        width_c=c.high_ticks-c.low_ticks
        width_b=b.high_ticks-b.low_ticks
        if width_c<8 or 4*width_c<5*width_b:
            continue
        structural+=1
        side=0
        for sign in (1,-1):
            medium_trend=slope_at_least(med1,med0,sign,1)
            long_trend=slope_at_least(lng1,lng0,sign,1)
            short_trend=slope_at_least(c,b,sign,2)
            breakout=(c.high_ticks>=max(a.high_ticks,b.high_ticks)+4 if sign==1
                      else c.low_ticks<=min(a.low_ticks,b.low_ticks)-4)
            if medium_trend and long_trend and short_trend and breakout:
                if side:
                    raise ValueError('B05H opposing same-time candidate FAIL')
                side=sign
        if not side:continue
        if signals and t-signals[-1][0]<TEN_MIN_100NS:continue
        if any(t<=z[0] for z in signals):
            raise ValueError('Nonincreasing H01 signal timestamps')
        signals.append((t,side))
        if len(signals)==2:break
    return signals,{'inspected_bar_closures':examined,
        'context_ready_closures':context_ready,
        'structural_expansion_closures':structural}

def frozen_t05(events,day):
    """EXISTING legacy T05 5s machinery ONLY for historical baseline parity/QC.

    New H01 signals never read bars5, opening width, 5s or timestamps of T05.
    """
    dev_day(day)
    old_bars=build_bars(events,day)
    raw,status=candidates(old_bars,day)
    if status!='READY':
        if status not in ('SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE'):
            raise ValueError('Bad original source status')
        return status,old_bars,[]
    parent=raw['T02_combined']
    signs=selected_families(parent,filters_for_signals(events,day,parent))[BASE]
    lo,_=utc_bounds(dev_day(day))
    tagged=[(lo+(i+1)*STEP_100NS,s,BASE) for i,s in signs]
    return status,old_bars,tagged

def shared_router(t05,new):
    """Sort by exact UTC signal timestamp; T05 priority if same exact instant."""
    raw=[(ts,0,s,BASE) for ts,s,_ in t05]+[
        (ts,1,s,NEW) for ts,s in new]
    raw.sort(key=lambda x:(x[0],x[1]))
    chosen=[];ties=0
    for ts,_,side,owner in raw:
        if chosen and chosen[-1][0]==ts:
            ties+=1
            continue
        chosen.append((ts,side,owner))
    return chosen,ties

def owner_policy(owner,old_bars,scenario):
    if owner==BASE:
        return risk_policy(opening_width(old_bars),scenario)
    if owner!=NEW:raise ValueError('Unknown H01 owner')
    slip,fee=SCENARIOS[scenario]
    return FillPolicy(
        latency_ms=1,entry_slippage_ticks=slip,exit_slippage_ticks=slip,
        stop_ticks=24,take_profit_ticks=48,max_holding_seconds=300,
        commission_round_trip_usd=fee,contracts=1)

def trace(day,events,old_bars,tagged,scenario,track,track_extra=None):
    """One account, mixed owners, exact timestamps, no overlapping active NQ."""
    dev_day(day)
    times=[x[0] for x in events]
    if any(a>b for a,b in zip(times,times[1:])):
        raise ValueError('Last time out of order')
    gains=[]
    owner_stats=defaultdict(counter)
    extra_stats=defaultdict(counter)
    last_exit=-1
    closed_pnl=0.0
    rejects=Counter()
    for ts,side,owner in tagged:
        if len(gains)>=MAX_TRADES_PER_DAY or closed_pnl<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            rejects['capacity']+=1
            continue
        if ts<=last_exit:
            rejects['overlap']+=1
            continue
        pol=owner_policy(owner,old_bars,scenario)
        r=simulate_single_trade(islice(events,bisect_right(times,ts),None),
                                  Signal(day,ts,side),pol)
        if r['status']!='SYNTHETIC_FILL_MODEL_ONLY':
            if r['status'] in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',
                               'UNRESOLVED_END_OF_LAST_DATA'):
                raise ValueError('B05H UNRESOLVED SYNTHETIC EXPOSURE FAIL CLOSED')
            rejects['no_valid_entry']+=1
            continue
        mark_trade_envelope(events,times,r,side,pol,track)
        pnl=r['estimated_net_usd']
        add_result(owner_stats[owner],pnl)
        if track_extra is not None:
            r_extra=dict(r,estimated_net_usd=round(pnl-EXTRA_RT,2))
            pol_extra=replace(pol,commission_round_trip_usd=
                             pol.commission_round_trip_usd+EXTRA_RT)
            mark_trade_envelope(events,times,r_extra,side,pol_extra,track_extra)
            add_result(extra_stats[owner],r_extra['estimated_net_usd'])
        gains.append(pnl)
        last_exit=r['exit_timestamp']
        closed_pnl=round(closed_pnl+pnl,2)
    return owner_stats,extra_stats,rejects

def run_month(root,month):
    if month not in MONTHS:
        raise ValueError('SEALED_OR_FORBIDDEN_MONTH_BEFORE_FS')
    days=sorted(month_days(root,month))
    tracks={m:{s:Envelope() for s in SCENARIOS} for m in MODELS}
    extras={m:Envelope() for m in MODELS}
    tally={m:{sc:{'counter':counter(),'extra_counter':counter(),
                 'attr':defaultdict(counter),
                 'extra_attr':defaultdict(counter),'opportunities':0,
                 'capacity':0,'overlap':0,'no_valid_entry':0}
              for sc in SCENARIOS} for m in MODELS}
    coverage=Counter();signal_stats=Counter()
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        original_state,old_bars,t05=frozen_t05(events,day)
        coverage[original_state]+=1
        if original_state!='READY':continue
        h01,stats=h01_candidates(events,day)
        signal_stats.update(stats)
        signal_stats['h01_opportunities']+=len(h01)
        router,ties=shared_router(t05,h01)
        signal_stats['exact_ties_t05_preferred']+=ties
        sets={
            BASE:t05,
            NEW:[(ts,s,NEW) for ts,s in h01],
            ROUTER:router}
        for model,tagged in sets.items():
            for sc in SCENARIOS:
                agg=tally[model][sc]
                agg['opportunities']+=len(tagged)
                x,xtra,rejects=trace(day,events,old_bars,tagged,sc,
                    tracks[model][sc],extras[model] if sc==STRESS else None)
                for owner,z in x.items():
                    agg['counter'].update(z)
                    agg['attr'][owner].update(z)
                if sc==STRESS:
                    for owner,z in xtra.items():
                        agg['extra_counter'].update(z)
                        agg['extra_attr'][owner].update(z)
                for k in ('capacity','overlap','no_valid_entry'):
                    agg[k]+=rejects[k]
    source=len(days)
    eligible=coverage['READY']
    if eligible+coverage['SKIP_MISSING_OPENING_RANGE']+coverage['SKIP_TINY_OPENING_RANGE']!=source:
        raise AssertionError('B05H source eligibility reconciliation')
    models={}
    for model in MODELS:
        models[model]={}
        for sc in SCENARIOS:
            z=tally[model][sc];c=z['counter'];tracker=tracks[model][sc]
            net=round(c['net_cents']/100,2)
            if abs(net-tracker.equity)>.01:raise AssertionError('B05H envelope parity')
            rec={'opportunities':z['opportunities'],
                 'trades':c['trades'],'net_usd':net,'wins':c['wins'],'losses':c['losses'],
                 'positive_usd':round(c['positive_cents']/100,2),
                 'negative_usd':round(c['negative_cents']/100,2),
                 'skipped_overlap':z['overlap'],
                 'skipped_capacity':z['capacity'],
                 'no_valid_entry':z['no_valid_entry'],
                 'owner_attribution':{owner:{'trades':vals['trades'],
                     'net_usd':round(vals['net_cents']/100,2)}
                     for owner,vals in z['attr'].items()},
                 'last_envelope_segment':tracker.segment()}
            if sc==STRESS:
                ex=z['extra_counter'];te=extras[model]
                if ex['trades']!=c['trades'] or ex['net_cents']!=c['net_cents']-1000*c['trades']:
                    raise AssertionError('B05H $10 fixed path conservation')
                if abs(ex['net_cents']/100-te.equity)>.01:
                    raise AssertionError('B05H $10 envelope mismatch')
                rec['stress_extra_10usd_fixed_path']={
                    'trades':ex['trades'],'net_usd':round(ex['net_cents']/100,2),
                    'positive_usd':round(ex['positive_cents']/100,2),
                    'negative_usd':round(ex['negative_cents']/100,2),
                    'owner_attribution':{owner:{'trades':vals['trades'],
                      'net_usd':round(vals['net_cents']/100,2)}
                      for owner,vals in z['extra_attr'].items()},
                    'last_envelope_segment':te.segment(),
                    'stops_or_daily_risk_recomputed':False}
            models[model][sc]=rec
    return {'month':month,'status':'B05H01_HYPOTHESIS_EXPLORATORY_DEV_ONLY',
        'source_days':source,'eligible_days':eligible,
        'excluded_days':source-eligible,
        'model_id':NEW,'signal_counts':dict(signal_stats),
        'models':models,
        'holdouts_opened':False,'broker_fills_verified':False,
        'new_market_history_acquired':False,'market_data_exported':False,
        'five_second_bars_used_for_new_H01_signals':False,
        'legacy_T05_signal_only_as_frozen_comparator':True}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.month not in MONTHS:raise SystemExit('B05H01 SEALED MONTH DENIED')
    results=run_month(args.root,args.month)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(results,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('B05H01_SAFE_MONTH='+json.dumps({
        'month':args.month,'source_days':results['source_days'],
        'eligible_days':results['eligible_days'],
        'h01_opportunities':results['signal_counts'].get('h01_opportunities',0),
        'models':{m:{'trades':results['models'][m][STRESS]['trades']}
                  for m in MODELS},
        'no_new_history':True,'holdouts_opened':False},sort_keys=True))
