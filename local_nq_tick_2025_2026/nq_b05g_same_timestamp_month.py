#!/usr/bin/env python3
"""B05G preregistered Last SAME-timestamp ordering stress. Existing DEV only.

Each variant preserves the exact (timestamp, price, qty) multiset; no new
market data, no learning from profits, no changes to frozen T05/T04 rules.
Publishes ONLY monthly counters and risk envelopes, never trades or prices.
"""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from itertools import groupby
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day,build_bars,candidates
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t05_fibonacci_bars import filters_for_signals,selected_families
from nq_t04_execution import SCENARIOS,simulate_portfolio
from nq_t08_risk_audit import Envelope
from nq_b05_t11_month import BASE,trace,counter
from nq_t10_t05_bbo_endpoints import SKIPS

VARIANTS=('ORIGINAL_SOURCE_ORDER','REVERSE_WITHIN_EQUAL_TS',
          'PRICE_ASC_WITHIN_EQUAL_TS','PRICE_DESC_WITHIN_EQUAL_TS')
STRESS='stress_1p5_fee_2ticks_each_side'
EXPECTED_SOURCE=140
EXPECTED_ELIGIBLE=135
PARITY_KEYS=('trades','net_usd','wins','losses','total_positive_usd',
             'total_negative_usd','unknown_entry_or_exit',
             'day_aborted_due_to_ambiguity','skipped_overlap',
             'skipped_max_two_or_daily_stop')

def tie_variants(events):
    """Produce EXACT frozen variants, with no changes outside equal-time groups.

    Sorting price ASC or DESC is stable for equal-price rows.
    This generator DOES NOT publish, infer or assign CME transaction order.
    """
    variants={k:[] for k in VARIANTS}
    stats=Counter()
    for timestamp,stream in groupby(events,key=lambda r:r[0]):
        original=list(stream)
        if len(original)>1:
            stats['multi_print_groups']+=1
            stats['prints_in_multi_print_groups']+=len(original)
            stats['adjacent_same_ts_prints']+=len(original)-1
            if len({row[1] for row in original})>1:
                stats['multi_price_groups']+=1
        variants['ORIGINAL_SOURCE_ORDER'].extend(original)
        options={
            'REVERSE_WITHIN_EQUAL_TS':list(reversed(original)),
            'PRICE_ASC_WITHIN_EQUAL_TS':sorted(original,key=lambda r:r[1]),
            'PRICE_DESC_WITHIN_EQUAL_TS':sorted(original,key=lambda r:-r[1]),
        }
        for variant,ordered in options.items():
            if ordered!=original:
                stats['changed_groups_'+variant]+=1
                stats['changed_prints_'+variant]+=len(original)
                # Fail closed on implementation mistakes while allowing zero qty.
                if Counter(ordered)!=Counter(original):
                    raise AssertionError('B05G changed group multiset')
            variants[variant].extend(ordered)
    for variant,items in variants.items():
        if len(items)!=len(events):
            raise AssertionError('B05G changed Last number of prints')
        if any(a[0]>b[0] for a,b in zip(items,items[1:])):
            raise AssertionError('B05G moved prints across timestamp groups')
    if variants['ORIGINAL_SOURCE_ORDER']!=events:
        raise AssertionError('Original variant MUST be exact source order')
    return variants,stats

def run_month(root,month):
    if month not in MONTHS:
        raise ValueError('SEALED_OR_NOT_EXISTING_DEV_MONTH_DENIED_BEFORE_FS')
    days=sorted(month_days(root,month))
    trackers={v:{sc:Envelope() for sc in SCENARIOS} for v in VARIANTS}
    extras={v:Envelope() for v in VARIANTS}
    rows={v:{sc:dict(opportunities=0,account=counter(),
                    extra_account=counter(),skipped_capacity=0,skipped_overlap=0)
             for sc in SCENARIOS} for v in VARIANTS}
    status=Counter();tie_stats=Counter()
    changed=Counter()
    for day in days:
        dev_day(day)
        original=list(source_events(file_for(root,dev_day(day),'Last')))
        permutations,stats=tie_variants(original)
        tie_stats.update(stats)
        baseline_sig=None; baseline_status=None
        for name in VARIANTS:
            events=permutations[name]
            bars=build_bars(events,day)
            selected,state=candidates(bars,day)
            if name==VARIANTS[0]:
                baseline_status=state
                status[state]+=1
            if state!=baseline_status:
                # Reordering may change close but should not affect OR availability
                # or OR high/low, which are permutation-invariant per 5s bin.
                raise AssertionError('B05G same-time ordering changed OR readiness')
            if state in SKIPS: continue
            if state!='READY':raise ValueError('Unknown source readiness status')
            parent=selected['T02_combined']
            signals=selected_families(parent,
                          filters_for_signals(events,day,parent))[BASE]
            if baseline_sig is None:baseline_sig=signals
            elif baseline_sig!=signals:
                changed['signal_days_'+name]+=1
                changed['added_signals_'+name]+=len(set(signals)-set(baseline_sig))
                changed['removed_signals_'+name]+=len(set(baseline_sig)-set(signals))
            tagged=[(i,s,BASE) for i,s in signals]
            for sc in SCENARIOS:
                record=rows[name][sc]
                record['opportunities']+=len(signals)
                result=trace(day,events,bars,tagged,sc,trackers[name][sc],
                          extras[name] if sc==STRESS else None)
                frozen=simulate_portfolio(day,events,bars,signals,sc)
                for k in PARITY_KEYS:
                    if frozen[k]!=result[k]:
                        raise AssertionError('T04 parity broken variant/'+name+'/'+sc+'/'+k)
                if result['unknown_entry_or_exit'] or result['day_aborted_due_to_ambiguity']:
                    # Never silently omit ambiguous trades or reward a variant
                    # for making fills unresolvable.
                    raise ValueError('B05G_VARIANT_UNKNOWN_FILL_FAIL_CLOSED '+name)
                record['skipped_capacity']+=result['skipped_max_two_or_daily_stop']
                record['skipped_overlap']+=result['skipped_overlap']
                for _,counts in result['owner_counters'].items():
                    record['account'].update(counts)
                if sc==STRESS:
                    for _,counts in result['owner_counters_extra'].items():
                        record['extra_account'].update(counts)
    if status['READY']+sum(status[x] for x in SKIPS)!=len(days):
        raise AssertionError('B05G did not audit every day')
    models={}
    for v in VARIANTS:
        models[v]={}
        for sc in SCENARIOS:
            z=rows[v][sc]; c=z['account'];track=trackers[v][sc]
            net=round(c['net_cents']/100,2)
            if abs(net-track.equity)>.01:raise AssertionError('B05G Last equity mismatch')
            record={
              'opportunities':z['opportunities'],
              'trades':c['trades'],'net_usd':net,
              'wins':c['wins'],'losses':c['losses'],
              'positive_usd':round(c['positive_cents']/100,2),
              'negative_usd':round(c['negative_cents']/100,2),
              'skipped_overlap':z['skipped_overlap'],
              'skipped_capacity':z['skipped_capacity'],
              'last_envelope_segment':track.segment(),
              'owner_attribution':{BASE:{'trades':c['trades'],'net_usd':net}}}
            if sc==STRESS:
                e=z['extra_account'];tr=extras[v]
                if e['trades']!=c['trades'] or e['net_cents']!=c['net_cents']-c['trades']*1000:
                    raise AssertionError('B05G extra 10 dollar accounting inconsistent')
                if abs(e['net_cents']/100-tr.equity)>.01:
                    raise AssertionError('B05G +10 USD envelope mismatch')
                record['stress_extra_10usd_fixed_path']={
                  'trades':e['trades'],'net_usd':round(e['net_cents']/100,2),
                  'positive_usd':round(e['positive_cents']/100,2),
                  'negative_usd':round(e['negative_cents']/100,2),
                  'last_envelope_segment':tr.segment(),
                  'owner_attribution':{BASE:{'trades':e['trades'],
                                            'net_usd':round(e['net_cents']/100,2)}},
                  'stops_or_daily_risk_recomputed':False}
            models[v][sc]=record
    return {
       'month':month,
       'status':'B05G_T05_EQUAL_TIMESTAMP_ORDER_STRESS_DEV_ONLY',
       'source_days':len(days),
       'eligible_days':status['READY'],
       'excluded_days':len(days)-status['READY'],
       'skipped_days_by_reason':{s:status[s] for s in SKIPS},
       'timestamp_ties':dict(tie_stats),
       'signal_change_counts':dict(changed),
       'models':models,'holdouts_opened':False,'broker_fills_verified':False,
       'trade_level_exported':False,'source_exchange_sequence_verified':False,
       'new_market_history_acquired':False
    }

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('B05G_SEALED_MONTH_BLOCKED')
    result=run_month(a.root,a.month)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('B05G_SAFE_MONTH='+json.dumps({'month':a.month,
         'source_days':result['source_days'],'eligible_days':result['eligible_days'],
         'variants':{v:result['models'][v][STRESS]['trades'] for v in VARIANTS},
         'new_history_acquired':False,'holdouts_opened':False},sort_keys=True))
