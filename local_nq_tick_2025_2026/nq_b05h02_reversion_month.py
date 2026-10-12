#!/usr/bin/env python3
"""B05H-02 one-shot prereg VWAP mean-reversion on trade-print bars, NO 5s new signals.

The existing 5s T05 detector is imported ONLY as a frozen comparison.
Strictly no new market-data sources, historical months, or OOS reads.
"""
from __future__ import annotations
import argparse,json
from bisect import bisect_left,bisect_right
from collections import Counter,defaultdict
from dataclasses import replace
from itertools import islice
from pathlib import Path
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t04_execution import SCENARIOS,MAX_TRADES_PER_DAY,STOP_NEW_ENTRIES_AFTER_DAILY_USD,risk_policy,opening_width
from sim_nq_last_execution_skeleton import Signal,FillPolicy,simulate_single_trade
from nq_t08_risk_audit import Envelope,mark_trade_envelope
from nq_b05_t11_month import counter,add_result
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_b05h01_trade_expansion_month import et_edge,frozen_t05,slope_at_least,BASE,STRESS,EXTRA_RT

NEW='H02_PRINT_VWAP_MEAN_REVERSION'
ROUTER='T05_PRIORITY_H02_SHARED_ROUTER'
MODELS=(BASE,NEW,ROUTER)
PRINT_LENGTHS=(377,4181,10946)
M40=2400*10_000_000
M60=3600*10_000_000
STOP_TICKS=32
TP_TICKS=48

def near_flat(a,b,max_ticks):
    """Exact rational |VWAP(b)-VWAP(a)| <= max_ticks in NQ price ticks."""
    if a.total_qty<=0 or b.total_qty<=0 or max_ticks<0:
        raise ValueError('invalid VWAP source')
    diff=abs(b.price_times_qty_ticks*a.total_qty -
             a.price_times_qty_ticks*b.total_qty)
    return diff<=max_ticks*b.total_qty*a.total_qty

def h02_candidates(events,day):
    """At most ONE per day, range regime & countertrend mean-reversion.

    Only count-based 377 /4181 /10946 Last, all bars timestamp atomic.
    No opening-range, T05 signals or five-second bars are read.
    """
    dev_day(day)  # STRICT before any data iterator access
    data=completed_bars_by_print_count(events,day,PRINT_LENGTHS)
    short=data[377]
    medium=data[4181]
    long=data[10946]
    m_end=[x.end_timestamp for x in medium]
    l_end=[x.end_timestamp for x in long]
    window_lo=et_edge(day,10,0)
    window_hi=et_edge(day,11,15)
    counts=Counter()
    for i in range(1,len(short)):
        b,c=short[i-1:i+1]
        t=c.end_timestamp
        if t<window_lo or t>=window_hi:continue
        counts['complete_short_bar_decisions']+=1
        mi=bisect_left(m_end,t)
        li=bisect_left(l_end,t)
        if mi<2 or li<2:continue
        m0,m1=medium[mi-2:mi]
        l0,l1=long[li-2:li]
        if t-m1.end_timestamp>M40 or t-l1.end_timestamp>M60:continue
        counts['ready_context_decisions']+=1
        if not near_flat(m0,m1,24) or not near_flat(l0,l1,36):continue
        counts['neutral_context_decisions']+=1
        if c.high_ticks-c.low_ticks>48:continue
        found=0
        for side in (1,-1):
            if side==1:
                # B extreme below medium, C starts recovering, still discounted
                v=(slope_at_least(m1,b,1,12) and
                   slope_at_least(c,b,1,3) and
                   slope_at_least(m1,c,1,4) and
                   c.low_ticks>=b.low_ticks+2)
            else:
                v=(slope_at_least(b,m1,1,12) and
                   slope_at_least(b,c,1,3) and
                   slope_at_least(c,m1,1,4) and
                   c.high_ticks<=b.high_ticks-2)
            if v:
                if found:raise ValueError('OPPOSING_SAME_BAR_FAIL')
                found=side
        if found:
            counts['h02_opportunities']+=1
            return [(t,found)],dict(counts)
    return [],dict(counts)

def owner_policy(owner,old_bars,scenario):
    if owner==BASE:
        return risk_policy(opening_width(old_bars),scenario)
    if owner!=NEW:raise ValueError('Unknown owner')
    slip,fee=SCENARIOS[scenario]
    return FillPolicy(latency_ms=1,entry_slippage_ticks=slip,
       exit_slippage_ticks=slip,stop_ticks=STOP_TICKS,
       take_profit_ticks=TP_TICKS,max_holding_seconds=300,
       commission_round_trip_usd=fee,contracts=1)

def share_signals(t05,h02):
    """Absolute UTC timestamp order, T05 wins an exact tie, 1 account."""
    entries=[(ts,0,side,BASE) for ts,side,owner in t05]
    entries.extend((ts,1,side,NEW) for ts,side in h02)
    entries.sort(key=lambda x:(x[0],x[1]))
    out=[];ties=0
    for ts,_,side,who in entries:
        if out and out[-1][0]==ts:
            ties+=1;continue
        out.append((ts,side,who))
    return out,ties

def risk_trace(day,events,old_bars,signals,scenario,tracker,extra_tracker=None):
    """H02 fixed risk, T05 original dynamic stop; hard fail on unknown fills."""
    dev_day(day)
    ts=[x[0] for x in events]
    if any(a>b for a,b in zip(ts,ts[1:])):
        raise ValueError('Nonchronological Last')
    ntr=0;pnl=0.;last_exit=-1
    owner=defaultdict(counter);extra=defaultdict(counter);skip=Counter()
    for t,side,which in signals:
        if ntr>=MAX_TRADES_PER_DAY or pnl<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            skip['capacity']+=1;continue
        if t<=last_exit:
            skip['overlap']+=1;continue
        policy=owner_policy(which,old_bars,scenario)
        result=simulate_single_trade(islice(events,bisect_right(ts,t),None),
                    Signal(day,t,side),policy)
        if result['status']!='SYNTHETIC_FILL_MODEL_ONLY':
            if result['status'] in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',
                                    'UNRESOLVED_END_OF_LAST_DATA'):
                raise ValueError('B05H02_HARD_FILL_AMBIGUOUS_ABORT_NO_TRADING_PNL')
            skip['no_entry']+=1
            continue
        mark_trade_envelope(events,ts,result,side,policy,tracker)
        net=result['estimated_net_usd']
        add_result(owner[which],net)
        if extra_tracker is not None:
            rec=dict(result,estimated_net_usd=round(net-EXTRA_RT,2))
            pol=replace(policy,commission_round_trip_usd=
                        policy.commission_round_trip_usd+EXTRA_RT)
            mark_trade_envelope(events,ts,rec,side,pol,extra_tracker)
            add_result(extra[which],rec['estimated_net_usd'])
        ntr+=1;pnl=round(pnl+net,2);last_exit=result['exit_timestamp']
    return owner,extra,skip

def run_month(root,month):
    if month not in MONTHS:
        raise ValueError('B05H02_SEALED_MONTH_DENIED_BEFORE_FS')
    days=sorted(month_days(root,month))
    trackers={m:{s:Envelope() for s in SCENARIOS} for m in MODELS}
    extra_tracks={m:Envelope() for m in MODELS}
    tally={m:{sc:{'counter':counter(),'extra_counter':counter(),
                  'by_owner':defaultdict(counter),
                  'extra_owner':defaultdict(counter),'opportunities':0,
                  'overlap':0,'capacity':0,'no_entry':0}
              for sc in SCENARIOS} for m in MODELS}
    skip_days=Counter();indicators=Counter()
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        state,old_bars,t05=frozen_t05(events,day)
        skip_days[state]+=1
        if state!='READY':continue
        h02,diag=h02_candidates(events,day)
        indicators.update(diag)
        combined,ties=share_signals(t05,h02)
        indicators['exact_t05_h02_ties']+=ties
        routes={BASE:t05,NEW:[(t,s,NEW) for t,s in h02],ROUTER:combined}
        for m,choices in routes.items():
            for sc in SCENARIOS:
                z=tally[m][sc]
                z['opportunities']+=len(choices)
                out,extra,sk=risk_trace(day,events,old_bars,choices,sc,
                    trackers[m][sc],extra_tracks[m] if sc==STRESS else None)
                for key,rec in out.items():
                    z['by_owner'][key].update(rec)
                    z['counter'].update(rec)
                if sc==STRESS:
                    for key,rec in extra.items():
                        z['extra_owner'][key].update(rec)
                        z['extra_counter'].update(rec)
                for k in ('overlap','capacity','no_entry'):
                    z[k]+=sk[k]
    n=len(days);elig=skip_days['READY']
    if elig+skip_days['SKIP_MISSING_OPENING_RANGE']+skip_days['SKIP_TINY_OPENING_RANGE']!=n:
        raise AssertionError('Source days not reconciled')
    outputs={}
    for m in MODELS:
        outputs[m]={}
        for sc in SCENARIOS:
            z=tally[m][sc];c=z['counter'];tracking=trackers[m][sc]
            net=round(c['net_cents']/100,2)
            if abs(tracking.equity-net)>.01:raise AssertionError('risk tracker mismatch')
            info={'opportunities':z['opportunities'],
                'trades':c['trades'],'net_usd':net,
                'wins':c['wins'],'losses':c['losses'],
                'positive_usd':round(c['positive_cents']/100,2),
                'negative_usd':round(c['negative_cents']/100,2),
                'skipped_overlap':z['overlap'],'skipped_capacity':z['capacity'],
                'no_entry':z['no_entry'],
                'owner_attribution':{k:{'trades':v['trades'],
                    'net_usd':round(v['net_cents']/100,2)}
                    for k,v in z['by_owner'].items()},
                'last_envelope_segment':tracking.segment()}
            if sc==STRESS:
                e=z['extra_counter'];te=extra_tracks[m]
                if e['trades']!=c['trades'] or e['net_cents']!=c['net_cents']-1000*c['trades']:
                    raise AssertionError('extra10 money conservation broken')
                if abs(te.equity-e['net_cents']/100)>.01:
                    raise AssertionError('extra10 risk tracker broken')
                info['stress_extra_10usd_fixed_path']={
                    'trades':e['trades'],'net_usd':round(e['net_cents']/100,2),
                    'positive_usd':round(e['positive_cents']/100,2),
                    'negative_usd':round(e['negative_cents']/100,2),
                    'owner_attribution':{k:{'trades':v['trades'],
                       'net_usd':round(v['net_cents']/100,2)}
                       for k,v in z['extra_owner'].items()},
                    'last_envelope_segment':te.segment(),
                    'stops_or_daily_risk_recomputed':False}
            outputs[m][sc]=info
    return {'status':'B05H02_DEV_EXPLORATORY_ONLY','month':month,
            'source_days':n,'eligible_days':elig,'excluded_days':n-elig,
            'signal_diagnostics':dict(indicators),'models':outputs,
            'holdouts_opened':False,'new_data_acquired':False,
            'H02_used_fixed_5s_signals':False,
            'legacy_T05_baseline_unchanged':True,
            'broker_fills_verified':False,'trade_level_exported':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('SEALED MONTH REJECTED')
    out=run_month(a.root,a.month)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('B05H02_SAFE_MONTH='+json.dumps({
        'month':a.month,'source':out['source_days'],'eligible':out['eligible_days'],
        'h02_opportunities':out['signal_diagnostics'].get('h02_opportunities',0),
        'trades':{name:out['models'][name][STRESS]['trades'] for name in MODELS},
        'holdouts_closed':True},sort_keys=True))
