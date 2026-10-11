#!/usr/bin/env python3
"""T10 strictly-prior NQ BBO endpoint audit of frozen T05-377 Last-only trades.

No individual quotes, Last prices, fills, trade times, or per-trade outcomes in output.
DO NOT treat prior BBO quotes as executed fills or rerun historic exit barriers.
All analyses restricted to Oct2025-Apr2026 DEV before any file access.
"""
from __future__ import annotations
import argparse,json
from bisect import bisect_right
from collections import Counter
from heapq import merge
from itertools import groupby,islice
from pathlib import Path
from statistics import median

from qc_tick_day import utc_bounds
from qc_quote_trade import source_paths,source_events as quote_events
from qc_tick_to_minutes import source_events as last_events
from nq_tick_short_horizon import dev_day,build_bars,candidates,STEP_100NS
from nq_t05_fibonacci_bars import filters_for_signals,selected_families
from nq_t04_execution import (SCENARIOS,MAX_TRADES_PER_DAY,
    STOP_NEW_ENTRIES_AFTER_DAILY_USD,opening_width,risk_policy,simulate_portfolio)
from nq_tick_short_horizon_month import MONTHS,month_days
from sim_nq_last_execution_skeleton import Signal,simulate_single_trade

FAMILY='T05_377'
MAX_QUOTE_AGE_MS=250
NQ_TICK_USD=5.0
SKIPS=('SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE')

def quote_snapshots(day, bid_ask_streams, endpoints):
    """Read all quotes and retain only BBO strictly earlier than each request.

    Each request is a timestamp (Last model entry or exit); if same as quote
    timestamp, request MUST see old quote. Grouped multi-update quote timestamp
    is never treated as exchange-ordered with a Last print.
    """
    dev_day(day)
    times=sorted(set(endpoints))
    if not times:return {}
    bid=ask=None
    result={}
    pos=0
    for ts,batch in groupby(merge(*bid_ask_streams,key=lambda e:e[0]),
                            key=lambda e:e[0]):
        while pos<len(times) and times[pos]<=ts:
            result[times[pos]]=(bid,ask)
            pos+=1
        last_b=last_a=None
        for t,kind,price in batch:
            if t!=ts:raise AssertionError('Bad timestamp group')
            if kind=='Bid':last_b=(ts,price)
            elif kind=='Ask':last_a=(ts,price)
            else:raise ValueError('Unexpected quote source')
        if last_b is not None:bid=last_b
        if last_a is not None:ask=last_a
    while pos<len(times):
        result[times[pos]]=(bid,ask)
        pos+=1
    return result

def classify_quote(snapshot, timestamp):
    bid,ask=snapshot
    if bid is None or ask is None:return 'MISSING',None
    if bid[0]>=timestamp or ask[0]>=timestamp:
        raise AssertionError('Noncausal quote used at Last endpoint')
    if bid[1]>=ask[1]:return 'LOCKED_OR_CROSSED',None
    if max(timestamp-bid[0],timestamp-ask[0])>MAX_QUOTE_AGE_MS*10000:
        return 'STALE_GT_250MS',None
    return 'VALID_STRICT_PRIOR_BBO',round((ask[1]-bid[1])*4)

def replay_frozen(day,events,bars,signals,scenario):
    """Reproduce original selection/execution in precise order, no optimization."""
    d=dev_day(day)
    lo,_=utc_bounds(d)
    policy=risk_policy(opening_width(bars),scenario)
    ts=[r[0] for r in events]
    if any(a>b for a,b in zip(ts,ts[1:])):
        raise ValueError('Unsorted Last data')
    pnl=0.;exit_t=-1;trades=[]
    invalid=overlap=capacity=0;aborted=False
    for i,side in signals:
        if side not in (-1,1) or i<0:raise ValueError('Bad signal')
        if len(trades)>=MAX_TRADES_PER_DAY or pnl<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            capacity+=1;continue
        end=lo+(i+1)*STEP_100NS
        if end<=exit_t:overlap+=1;continue
        r=simulate_single_trade(islice(events,bisect_right(ts,end),None),
                                Signal(day,end,side),policy)
        if r['status']!='SYNTHETIC_FILL_MODEL_ONLY':
            invalid+=1
            if r['status'] in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',
                              'UNRESOLVED_END_OF_LAST_DATA'):
                aborted=True;break
            continue
        r['side']=side
        trades.append(r)
        pnl=round(pnl+r['estimated_net_usd'],2)
        exit_t=r['exit_timestamp']
    gains=[r['estimated_net_usd'] for r in trades]
    return trades,{
        'trades':len(trades),'net_usd':round(sum(gains),2),
        'wins':sum(g>0 for g in gains),'losses':sum(g<0 for g in gains),
        'total_positive_usd':round(sum(g for g in gains if g>0),2),
        'total_negative_usd':round(-sum(g for g in gains if g<0),2),
        'unknown_entry_or_exit':invalid,
        'day_aborted_due_to_ambiguity':aborted,
        'skipped_overlap':overlap,'skipped_max_two_or_daily_stop':capacity
    }

def analyze_pairs(trades, snaps):
    c=Counter()
    spreads_entry=[];spreads_exit=[];quote_deltas=[]
    for trade in trades:
        c['trades']+=1
        side=trade['side']
        t0=trade['entry_timestamp'];t1=trade['exit_timestamp']
        status_entry,spread_entry=classify_quote(snaps[t0],t0)
        status_exit,spread_exit=classify_quote(snaps[t1],t1)
        c['entry_'+status_entry]+=1
        c['exit_'+status_exit]+=1
        if status_entry=='VALID_STRICT_PRIOR_BBO':
            spreads_entry.append(spread_entry)
            bid,ask=snaps[t0]
            q_entry=ask[1] if side==1 else bid[1]
            c['entry_last_outside_prior_bbo']+=int(
                trade['entry_price_ticks']<round(4*bid[1]) or
                trade['entry_price_ticks']>round(4*ask[1]))
        if status_exit=='VALID_STRICT_PRIOR_BBO':
            spreads_exit.append(spread_exit)
            bid,ask=snaps[t1]
            q_exit=bid[1] if side==1 else ask[1]
            c['exit_last_outside_prior_bbo']+=int(
                trade['exit_price_ticks']<round(4*bid[1]) or
                trade['exit_price_ticks']>round(4*ask[1]))
        if status_entry!='VALID_STRICT_PRIOR_BBO' or status_exit!='VALID_STRICT_PRIOR_BBO':
            continue
        c['valid_quote_pairs']+=1
        b0,a0=snaps[t0];b1,a1=snaps[t1]
        q_entry=(a0 if side==1 else b0)[1]
        q_exit=(b1 if side==1 else a1)[1]
        # Quote units index POINTS; Last model units 0.25-price TICKS.
        last_entry=trade['entry_price_ticks']/4.0
        last_exit=trade['exit_price_ticks']/4.0
        delta=round(side*((q_exit-last_exit)+(last_entry-q_entry))*20.0,2)
        adjusted=round(trade['estimated_net_usd']+delta,2)
        check=round(side*(q_exit-q_entry)*20.0,2)
        # Existing assumed slippage embedded in frozen Last entry/exit prices;
        # no second slippage charge is assessed in this *endpoint-only* comparison.
        # Fee reconstruction should match q-based accounting exactly.
        fee=trade['gross_usd']-trade['estimated_net_usd']
        if abs((check-fee)-adjusted)>0.02:
            raise AssertionError('Quote comparison algebra failed')
        quote_deltas.append(delta)
        c['paired_baseline_model_net_usd_cents']+=int(round(100*trade['estimated_net_usd']))
        c['paired_quote_delta_usd_cents']+=int(round(100*delta))
    return c,spreads_entry,spreads_exit,quote_deltas

def analyze_day(root,day):
    d=dev_day(day)  # Reject any holdout BEFORE filesystem access.
    paths=source_paths(root,day)
    events=list(last_events(paths['Last']))
    bars=build_bars(events,day)
    signal_map,status=candidates(bars,day)
    if status in SKIPS:
        return {'date_et':day,'status':status,'simulated':{},'quote_counts':{},
            'holdouts_opened':False}
    if status!='READY':raise ValueError('Unexpected signal status')
    parent=signal_map['T02_combined']
    selected=selected_families(parent,filters_for_signals(events,day,parent))[FAMILY]
    captures={}
    endpoints=[]
    for sc in SCENARIOS:
        frozen=simulate_portfolio(day,events,bars,selected,sc)
        trades,summary=replay_frozen(day,events,bars,selected,sc)
        for k,v in summary.items():
            if frozen[k]!=v:
                raise AssertionError('Frozen T04 mismatch '+day+'/'+sc+'/'+k)
        captures[sc]=(trades,summary)
        endpoints.extend(t for r in trades for t in
                         (r['entry_timestamp'],r['exit_timestamp']))
    # A date with no frozen simulated fills has no quote endpoint to audit.
    # Source filenames are still checked above. Do not falsely fail source QC
    # just because lazy quote streams correctly were never consumed.
    snapshots={}
    if endpoints:
        lo,hi=utc_bounds(d)
        qc=Counter()
        streams=[quote_events(paths[k],k,lo,hi,qc) for k in ('Bid','Ask')]
        snapshots=quote_snapshots(day,streams,endpoints)
        for kind in ('Bid','Ask'):
            if not qc[kind+'_rows'] or any(v for k,v in qc.items()
                if k.startswith(kind+'_') and ('invalid' in k or
                    'outside_ET_window' in k or 'off_tick_grid' in k)):
                raise ValueError('Quote source QC failed')
    output={}
    for sc,(trades,summary) in captures.items():
        c,s_entry,s_exit,deltas=analyze_pairs(trades,snapshots)
        if c['trades']!=summary['trades']:raise AssertionError('Trade count mismatch')
        output[sc]={'original_trades':summary['trades'],
                    'original_net_usd':summary['net_usd'],
                    'unknown_entries_exits':summary['unknown_entry_or_exit'],
                    'aborted_days':int(summary['day_aborted_due_to_ambiguity']),
                    'quote_counters':dict(c),
                    'entry_spread_ticks':s_entry,
                    'exit_spread_ticks':s_exit,
                    'paired_quote_delta_usd':deltas}
    return {'date_et':day,'status':'T10_DEV_EXECUTION_QUOTE_QC',
        'simulated':output,'holdouts_opened':False}

def quantile(values,frac):
    if not values:return None
    a=sorted(values)
    i=(len(a)-1)*frac
    low=int(i);high=min(low+1,len(a)-1)
    return round(a[low]*(1-(i-low))+a[high]*(i-low),3)

def aggregate_month(month,days):
    if month not in MONTHS or not days:raise ValueError('SEALED_OR_EMPTY')
    if any(x['date_et'][:7]!=month or x['holdouts_opened'] is not False or
           x['status'] not in ('T10_DEV_EXECUTION_QUOTE_QC',*SKIPS) for x in days):
        raise ValueError('Invalid month/holdout/QC')
    out={}
    for sc in SCENARIOS:
        rows=[x['simulated'][sc] for x in days if x['status']=='T10_DEV_EXECUTION_QUOTE_QC']
        total=Counter()
        entry=[];exit=[];delta=[]
        for x in rows:
            total.update(x['quote_counters'])
            entry.extend(x['entry_spread_ticks'])
            exit.extend(x['exit_spread_ticks'])
            delta.extend(x['paired_quote_delta_usd'])
        out[sc]={
            'trades':sum(x['original_trades'] for x in rows),
            'simulated_last_net_usd':round(sum(x['original_net_usd'] for x in rows),2),
            'unknown_or_ambiguous':sum(x['unknown_entries_exits'] for x in rows),
            'aborted_days':sum(x['aborted_days'] for x in rows),
            'counts':dict(total),
            'entry_spread_median_ticks':quantile(entry,.5),
            'entry_spread_p90_ticks':quantile(entry,.9),
            'exit_spread_median_ticks':quantile(exit,.5),
            'exit_spread_p90_ticks':quantile(exit,.9),
            'quote_delta_paired_median_usd':quantile(delta,.5),
            'quote_delta_paired_p10_usd':quantile(delta,.1),
            'quote_delta_paired_p90_usd':quantile(delta,.9),
        }
    return {'month':month,'status':'T10_PRIOR_BBO_QC_ONLY_NOT_REAL_FILLS',
        'source_days':len(days),
        'eligible_days':sum(x['status']=='T10_DEV_EXECUTION_QUOTE_QC' for x in days),
        'excluded_days':sum(x['status'] in SKIPS for x in days),
        'scenarios':out,'holdouts_opened':False,
        'prior_250ms_is_NOT_executable_quote_certification':True,
        'trade_level_data_exported':False}

def run_month(root,month):
    if month not in MONTHS:raise ValueError('Sealed or invalid month')
    return aggregate_month(month,[analyze_day(root,d) for d in month_days(root,month)])

def summarize_private_day_files(root,month,day_dir):
    # Last month source list is used to prove all DEV source dates were processed.
    if month not in MONTHS:raise ValueError('Forbidden month')
    expected=sorted(month_days(root,month))  # rollover filenames can sort by contract, not by date
    files=list(day_dir.glob('nq_t10_day_*.json'))
    if len(files)!=len(expected):raise ValueError('Incomplete day set')
    days=[json.loads(f.read_text(encoding='utf8')) for f in files]
    if sorted(x['date_et'] for x in days)!=expected:
        raise ValueError('Missing/duplicate/out-of-month day')
    return aggregate_month(month,sorted(days,key=lambda d:d['date_et']))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--day',required=False)
    p.add_argument('--internal-day-inputs',type=Path,required=False)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('HOLDOUT_BLOCKED')
    if a.day:
        if a.day[:7]!=a.month:raise SystemExit('DAY_NOT_IN_MONTH')
        dev_day(a.day)
        result=analyze_day(a.root,a.day)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,sort_keys=True)+'\n',encoding='utf8')
        print('T10_DAY_COMPLETED_QC_ONLY')
    else:
        result=(summarize_private_day_files(a.root,a.month,a.internal_day_inputs)
                if a.internal_day_inputs else run_month(a.root,a.month))
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf8')
        print('T10_MONTH_SAFE_SUMMARY='+json.dumps({
            'month':result['month'],'eligible_days':result['eligible_days'],
            'trades':{k:v['trades'] for k,v in result['scenarios'].items()},
            'valid_pairs':{k:v['counts'].get('valid_quote_pairs',0)
                           for k,v in result['scenarios'].items()},
            'status':result['status']},sort_keys=True))
