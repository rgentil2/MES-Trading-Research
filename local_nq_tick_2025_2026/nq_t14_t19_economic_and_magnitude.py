#!/usr/bin/env python3
"""T14-T19 prereg economic + magnitude outcome measurement; no new alpha.

Reuse frozen stage-0 377-print signals and Last DEV, 2025-10..2026-04 only.
Private daily vectors and licensed rows MUST NEVER enter uploaded artifact.
"""
from __future__ import annotations
import argparse,json,math,statistics
from collections import Counter,defaultdict
from bisect import bisect_right
from dataclasses import replace
from pathlib import Path
from itertools import islice
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_b05h01_trade_expansion_month import frozen_t05,BASE,STRESS
from nq_b05h02_reversion_month import share_signals
from nq_t14_t16_signal_feasibility import detect as first_detect,IDS as FIRST
from nq_t17_t19_signal_feasibility import detect as second_detect,IDS as SECOND
from nq_t04_execution import MAX_TRADES_PER_DAY,STOP_NEW_ENTRIES_AFTER_DAILY_USD
from sim_nq_last_execution_skeleton import FillPolicy,Signal,simulate_single_trade
from nq_t08_risk_audit import Envelope,mark_trade_envelope
from nq_b05_t11_month import counter,add_result
from nq_b03_aggregate import stitch
from nq_b05_t11_aggregate import group
from nq_b05h02_reversion_month import risk_trace as frozen_risk_trace
from nq_t04_execution import risk_policy,opening_width
from nq_b05h01_trade_expansion_month import EXTRA_RT
from nq_b05_t11_month import counter as make_counter
from nq_b05_t11_month import add_result as accumulate
from nq_b05h01_trade_expansion_month import et_edge
from nq_b05h02_reversion_month import owner_policy as h02_owner_policy
from nq_t04_execution import SCENARIOS

DIRECTIONAL=(*FIRST,SECOND[1])
MAGNITUDE=(SECOND[0],SECOND[2])
ROUTERS={k:'T05_PLUS_'+k for k in DIRECTIONAL}
MODELS=(BASE,*DIRECTIONAL,*ROUTERS.values())
EXTRA='stress_plus_10_usd_rt_FIXED_PATH_ONLY'
EXPECTED={'2025-10':(15,137.5),'2025-11':(8,760.),
'2025-12':(22,1450.),'2026-01':(19,1572.5),
'2026-02':(13,-827.5),'2026-03':(21,1372.5),
'2026-04':(17,637.5)}
HORIZON_NS=15*60*10_000_000

def trace(day,events,times,oldbars,tagged,tracker):
    """One shared account, frozen policy, no same-time fills, halt on ambiguity."""
    dev_day(day)
    net=0.
    trades=0
    last_exit=-1
    owner=defaultdict(counter)
    xtra=defaultdict(counter)
    issues=Counter()
    for t,side,who in tagged:
        if trades>=MAX_TRADES_PER_DAY or net<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            issues['capacity']+=1;continue
        if t<=last_exit:
            issues['overlap']+=1;continue
        if who==BASE:
            policy=risk_policy(opening_width(oldbars),STRESS)
        elif who in DIRECTIONAL:
            slip,fee=SCENARIOS[STRESS]
            policy=FillPolicy(latency_ms=1,entry_slippage_ticks=slip,
               exit_slippage_ticks=slip,stop_ticks=32,take_profit_ticks=48,
               max_holding_seconds=300,commission_round_trip_usd=fee,contracts=1)
        else:raise ValueError('illegal owner')
        r=simulate_single_trade(islice(events,bisect_right(times,t),None),
               Signal(day,t,side),policy)
        if r['status']!='SYNTHETIC_FILL_MODEL_ONLY':
            if r['status'] in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',
                                'UNRESOLVED_END_OF_LAST_DATA'):
                raise ValueError('HARD_AMBIGUOUS_SYNTHETIC_EXPOSURE_FAIL_CLOSED')
            issues['no_entry']+=1
            continue
        mark_trade_envelope(events,times,r,side,policy,tracker)
        gain=r['estimated_net_usd']
        accumulate(owner[who],gain)
        accumulate(xtra[who],gain-EXTRA_RT)
        trades+=1
        net=round(net+gain,2)
        last_exit=r['exit_timestamp']
    count=make_counter(); extra=make_counter()
    for vals in owner.values():count.update(vals)
    for vals in xtra.values():extra.update(vals)
    if extra['trades']!=count['trades'] or extra['net_cents'] != count['net_cents']-1000*count['trades']:
        raise AssertionError('fixed extra10 path not conserved')
    if round(tracker.equity*100)!=count['net_cents']+round((tracker.equity-net)*100):
        # tracker is continuous for the whole month, not reset daily.
        raise AssertionError('net reconciliation')
    return count,extra,owner,xtra,issues

def combined(t05,new):
    if not new:return t05
    tagged=[(ts,0,side,BASE) for ts,side,who in t05]
    tagged.extend((ts,1,side,k) for ts,side,k in new)
    tagged.sort(key=lambda x:(x[0],x[1]))
    result=[];last=None
    for ts,_,side,who in tagged:
        if last==ts:continue
        result.append((ts,side,who));last=ts
    return result

def future_range(events,times,ts):
    start=bisect_right(times,ts)
    end=bisect_right(times,ts+HORIZON_NS)
    if start>=end:return None
    prices=[item[1] for item in events[start:end]]
    return max(prices)-min(prices)

def month_stage(root,month,private_dest):
    if month not in MONTHS:raise ValueError('SEALED MONTH BEFORE FILE READ')
    days=sorted(month_days(root,month))
    tracker={model:Envelope() for model in MODELS}
    details={model:{'count':make_counter(),'extra':make_counter(),
        'by_owner':defaultdict(make_counter),'extra_owner':defaultdict(make_counter),
        'opportunities':0,'capacity':0,'overlap':0,'no_entry':0}
        for model in MODELS}
    coverage=Counter()
    predictions={key:{'n':0,'range_ticks_sum':0,'range_ticks_values':[],'no_endpoint':0}
                 for key in MAGNITUDE}
    daily=[]
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        oldstate,oldbars,t05=frozen_t05(events,day)
        coverage[oldstate]+=1
        if oldstate!='READY':
            daily.append({'day':day,'eligible':False})
            continue
        times=[e[0] for e in events]
        s0,_=first_detect(events,day)
        s1,_=second_detect(events,day)
        for k in MAGNITUDE:
            if k in s1:
                v=future_range(events,times,s1[k][0])
                if v is None:predictions[k]['no_endpoint']+=1
                else:
                    predictions[k]['n']+=1
                    predictions[k]['range_ticks_sum']+=v
                    predictions[k]['range_ticks_values'].append(v)
        routes={BASE:t05}
        for k in DIRECTIONAL:
            new=s0 if k in FIRST else s1
            tag=([(new[k][0],new[k][1],k)] if k in new else [])
            routes[k]=tag
            routes[ROUTERS[k]]=combined(t05,tag)
        day_data={'day':day,'eligible':True,'models':{}}
        for model,route in routes.items():
            z=details[model]
            z['opportunities']+=len(route)
            pre=tracker[model].equity
            ct,ex,own,eown,issues=trace(day,events,times,oldbars,route,tracker[model])
            z['count'].update(ct);z['extra'].update(ex)
            for who,w in own.items():z['by_owner'][who].update(w)
            for who,w in eown.items():z['extra_owner'][who].update(w)
            for k in ('capacity','overlap','no_entry'):z[k]+=issues[k]
            daily_value=round(tracker[model].equity-pre,2)
            if round(daily_value*100)!=ct['net_cents']:
                raise AssertionError('private daily ledger != per-session increments')
            day_data['models'][model]={'trades':ct['trades'],
               'stress_cents':ct['net_cents'],
               'extra_cents':ex['net_cents']}
        daily.append(day_data)
    eligible=coverage['READY']
    if len(days)!=sum(coverage.values()):
        raise ValueError('source coverage')
    if (sum(d['models'][BASE]['trades'] for d in daily if d['eligible']),
        round(sum(d['models'][BASE]['stress_cents'] for d in daily if d['eligible'])/100,2))!=EXPECTED[month]:
        raise AssertionError('FROZEN T05 monthly parity failed')
    if any(v['no_endpoint'] for v in predictions.values()):
        raise ValueError('missing future horizon for predeclared magnitude event')
    safe={'month':month,'status':'T14_T19_ECONOMIC_DEV_ONLY',
       'source_days':len(days),'eligible_days':eligible,
       'excluded_days':len(days)-eligible,'models':{},
       'magnitude':{},'holdouts_opened':False,'new_data_acquired':False,
       'broker_fills_verified':False,'trade_level_exported':False,
       'new_five_second_signals':False}
    for name,v in details.items():
        c=v['count'];x=v['extra']
        if c['net_cents']!=round(tracker[name].equity*100):
            raise AssertionError('monthly risk/net difference')
        basic={'trades':c['trades'],'net_usd':c['net_cents']/100,
            'positive_usd':c['positive_cents']/100,
            'negative_usd':c['negative_cents']/100,
            'wins':c['wins'],'losses':c['losses'],
            'opportunities':v['opportunities'],'no_entry':v['no_entry'],
            'capacity':v['capacity'],'overlap':v['overlap'],
            'owner_attribution':{k:{'trades':w['trades'],'net_usd':w['net_cents']/100}
                          for k,w in v['by_owner'].items()},
            'last_envelope_segment':tracker[name].segment(),
            'extra10':{'trades':x['trades'],'net_usd':x['net_cents']/100,
                'positive_usd':x['positive_cents']/100,'negative_usd':x['negative_cents']/100,
                'owner_attribution':{k:{'trades':w['trades'],'net_usd':w['net_cents']/100}
                          for k,w in v['extra_owner'].items()}}}
        safe['models'][name]=basic
    for k,p in predictions.items():
        safe['magnitude'][k]={'N_signal_and_future_endpoint':p['n'],
              'range_ticks_sum':p['range_ticks_sum'],
              'future_range_ticks_median':statistics.median(p['range_ticks_values']) if p['n'] else None,
              'no_event_comparison_available':False}
    private_dest.parent.mkdir(parents=True,exist_ok=True)
    private_dest.write_text(json.dumps({'safe':safe,'private_daily':daily},separators=(',',':'))+'\n')
    return {'month':month,'source':len(days),'eligible':eligible,
            'trades':{k:v['trades'] for k,v in safe['models'].items()},
            'net':{k:v['net_usd'] for k,v in safe['models'].items()},
            'no_daily_export':True}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--month',required=True)
    p.add_argument('--private-out',required=True,type=Path)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('SEALED MONTH')
    r=month_stage(a.root,a.month,a.private_out)
    print('T14_T19_ECONOMIC_MONTH_SAFE='+json.dumps(r,sort_keys=True))
