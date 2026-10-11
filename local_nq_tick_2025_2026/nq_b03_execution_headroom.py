#!/usr/bin/env python3
"""B03: cost-overrun sensitivity on exact frozen NQ T05-377 LAST trade path.

Not an executable fill backtest, not a bound on broker losses. Records only
monthly aggregates. Only 7 original DEV months, no sealed source reads.
"""
from __future__ import annotations
import argparse,json
from dataclasses import replace
from collections import Counter
from pathlib import Path
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day,build_bars,candidates
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t05_fibonacci_bars import filters_for_signals,selected_families
from nq_t04_execution import SCENARIOS,opening_width,risk_policy,simulate_portfolio
from nq_t08_risk_audit import Envelope,mark_trade_envelope,VALID_SKIP
from nq_t10_t05_bbo_endpoints import replay_frozen

SURCHARGE_TICKS_PER_SIDE=(0,1,2,4)
USD_PER_NQ_TICK=5
EXPECTED={
    'baseline':(115,6220.0),
    'stress_1p5_fee_2ticks_each_side':(115,5102.5)
}

def surcharge_usd(extra_ticks_each_side):
    if extra_ticks_each_side not in SURCHARGE_TICKS_PER_SIDE:
        raise ValueError('Surcharge must be a pre-registered scenario')
    return extra_ticks_each_side*2*USD_PER_NQ_TICK

def adjusted_trade(trade,extra):
    # Do not alter entry, exit, original TP, original SL or original timestamps.
    new=dict(trade)
    new['estimated_net_usd']=round(trade['estimated_net_usd']-extra,2)
    return new

def day_audit(day,events,trackers,acc):
    dev_day(day)
    bars=build_bars(events,day)
    signals,status=candidates(bars,day)
    if status in VALID_SKIP:return status
    if status!='READY':raise ValueError('Unexpected signal/source state')
    parent=signals['T02_combined']
    selected=selected_families(parent,filters_for_signals(events,day,parent))['T05_377']
    times=[x[0] for x in events]
    for sc in SCENARIOS:
        trades,ref=replay_frozen(day,events,bars,selected,sc)
        original=simulate_portfolio(day,events,bars,selected,sc)
        for k,v in ref.items():
            if original[k]!=v:
                raise AssertionError(f'Original T04 mismatch {day} {sc} {k}')
        if ref['unknown_entry_or_exit'] or ref['day_aborted_due_to_ambiguity']:
            raise ValueError('Fail-closed on original ambiguous executions')
        acc[sc]['original_count']+=ref['trades']
        acc[sc]['original_net_cents']+=round(100*ref['net_usd'])
        acc[sc]['original_ambiguous']+=ref['unknown_entry_or_exit']
        frozen_policy=risk_policy(opening_width(bars),sc)
        for ticks in SURCHARGE_TICKS_PER_SIDE:
            extra=surcharge_usd(ticks)
            t=trackers[sc][ticks]
            row=acc[sc]['sur'][ticks]
            for tr in trades:
                mod=adjusted_trade(tr,extra)
                surcharge_policy=replace(frozen_policy,
                    commission_round_trip_usd=frozen_policy.commission_round_trip_usd+extra)
                mark_trade_envelope(events,times,mod,tr['side'],surcharge_policy,t)
                gain=mod['estimated_net_usd']
                row['trades']+=1
                row['net_cents']+=round(gain*100)
                row['positive_cents']+=round(max(gain,0)*100)
                row['negative_cents']+=round(max(-gain,0)*100)
    return 'PARITY_OK'

def audit_month(root,month):
    if month not in MONTHS:raise ValueError('SEALED_OR_UNAUTHORIZED_MONTH')
    days=sorted(month_days(root,month)) # chronological even in contract rollover
    trackers={sc:{i:Envelope() for i in SURCHARGE_TICKS_PER_SIDE}
              for sc in SCENARIOS}
    acc={sc:{'original_count':0,'original_net_cents':0,'original_ambiguous':0,
             'sur':{i:Counter() for i in SURCHARGE_TICKS_PER_SIDE}}
         for sc in SCENARIOS}
    status=Counter()
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        status[day_audit(day,events,trackers,acc)]+=1
    out={}
    for sc in SCENARIOS:
        a=acc[sc];d={}
        for ticks in SURCHARGE_TICKS_PER_SIDE:
            r=a['sur'][ticks];t=trackers[sc][ticks]
            net=round(r['net_cents']/100,2)
            if abs(net-t.equity)>0.01:
                raise AssertionError('Cumulative frozen-path equity inconsistent')
            if r['trades']!=a['original_count']:
                raise AssertionError('Trade count drift under penalty')
            exp=round(a['original_net_cents']/100-surcharge_usd(ticks)*r['trades'],2)
            if abs(net-exp)>0.01:
                raise AssertionError('Surcharge accounting inconsistency')
            d[str(ticks)]={
                'extra_ticks_each_side':ticks,
                'additional_usd_per_round_trip':surcharge_usd(ticks),
                'trades':r['trades'],
                'frozen_path_adjusted_net_usd':net,
                'gross_positive_net_usd':round(r['positive_cents']/100,2),
                'gross_negative_net_usd':round(r['negative_cents']/100,2),
                'last_envelope_segment':t.segment(),
                'fills_and_stops_recalculated':False}
        out[sc]={
            'frozen_trades':a['original_count'],
            'frozen_last_net_usd':round(a['original_net_cents']/100,2),
            'original_ambiguities':a['original_ambiguous'],
            'surcharges':d}
    return {'month':month,'status':'B03_FROZEN_PATH_ACCOUNTING_ONLY',
            'source_days':len(days),'eligible_days':status['PARITY_OK'],
            'excluded_days':sum(status[k] for k in VALID_SKIP),
            'chronological_ET_days':True,
            'month_days_dates_unique':len(days)==len(set(days)),
            'scenarios':out,'holdouts_opened':False,
            'no_trade_or_price_level_exported':True,
            'actual_fills_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--month',required=True)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('SEALED_MONTH_BLOCKED')
    r=audit_month(a.root,a.month)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('NQ_B03_SAFE_MONTH='+json.dumps({
        'month':r['month'],'eligible_days':r['eligible_days'],
        'trades':{k:v['frozen_trades'] for k,v in r['scenarios'].items()},
        'status':r['status']},sort_keys=True))
