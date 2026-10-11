#!/usr/bin/env python3
"""T08: post-selection NQ funded-risk diagnostic, DEV Last-only, no broker fills.

Frozen T02/T05 signals/T04 simulator, independent per-portfolio comparison.
Full-session mark-to-market *Last envelope* is an adverse bounding exercise,
NOT a broker trailing DD calculation or an actual exchange fill reconstruction.
No individual prices, signals or trades are printed or written to public logs.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
from dataclasses import dataclass
from itertools import groupby, islice
import json
from pathlib import Path

from qc_tick_day import file_for, utc_bounds
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day, build_bars, candidates, STEP_100NS
from nq_tick_short_horizon_month import MONTHS, month_days
from nq_t04_execution import (SCENARIOS, NQ_TICK_USD, risk_policy,
    opening_width, simulate_portfolio, MAX_TRADES_PER_DAY,
    STOP_NEW_ENTRIES_AFTER_DAILY_USD)
from nq_t05_fibonacci_bars import filters_for_signals, selected_families
from sim_nq_last_execution_skeleton import Signal, simulate_single_trade

FAMILIES=('T02_PARENT','T05_377','T05_233_AND_377')
VALID_SKIP=('SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE')

@dataclass
class Envelope:
    equity: float=0.0
    high: float=0.0
    low: float=0.0
    peak: float=0.0
    max_dd: float=0.0
    closed_peak: float=0.0
    closed_low: float=0.0
    closed_high: float=0.0
    closed_dd: float=0.0

    def mark(self, lo:float, hi:float):
        if lo>hi: raise ValueError('Bad Last envelope')
        # Timestamp-local order is unknown: high-before-low is an adverse
        # *bound*, and must NEVER be described as true chronological tick order.
        self.high=max(self.high,hi)
        self.low=min(self.low,lo)
        self.peak=max(self.peak,hi)
        self.max_dd=max(self.max_dd,self.peak-lo)

    def close(self, net:float):
        self.equity=round(self.equity+net,2)
        self.mark(self.equity,self.equity)
        self.closed_peak=max(self.closed_peak,self.equity)
        self.closed_low=min(self.closed_low,self.equity)
        self.closed_high=max(self.closed_high,self.equity)
        self.closed_dd=max(self.closed_dd,self.closed_peak-self.equity)

    def segment(self):
        return {k:round(getattr(self,k),2) for k in
            ('equity','high','low','max_dd','closed_high','closed_low','closed_dd')}

def mark_trade_envelope(events, times, r, side, policy, tracker):
    t0=r['entry_timestamp'];t1=r['exit_timestamp']
    if t1<=t0:raise AssertionError('Invalid chronology')
    entry=r['entry_price_ticks']
    fee=policy.commission_round_trip_usd
    cost_at_exit=policy.exit_slippage_ticks*NQ_TICK_USD
    # Position immediately after the hypothetical entry already bears
    # estimated round-trip transaction costs if flattened at that instant.
    tracker.mark(tracker.equity-fee-cost_at_exit,
                 tracker.equity-fee-cost_at_exit)
    left=bisect_right(times,t0)
    right=bisect_right(times,t1)
    seen_exit=False
    for ts, rows in groupby(events[left:right],key=lambda e:e[0]):
        prices=[item[1] for item in rows]
        if not prices:continue
        marks=[tracker.equity+side*(p-entry)*NQ_TICK_USD-fee-cost_at_exit
               for p in prices]
        tracker.mark(min(marks),max(marks))
        if ts==t1:seen_exit=True
    if not seen_exit:raise AssertionError('Missing exit event in Last source')
    tracker.close(r['estimated_net_usd'])

def trace_portfolio(day,events,bars,signals,scenario,tracker):
    # No data access is permitted before this guard.
    d=dev_day(day)
    lo,_=utc_bounds(d)
    opening=opening_width(bars)
    if opening is None:raise ValueError('Missing opening context')
    policy=risk_policy(opening,scenario)
    times=[x[0] for x in events]
    if any(a>b for a,b in zip(times,times[1:])):
        raise ValueError('Nonchronological Last source')
    pnl=0.;last_exit=-1;gains=[]
    invalid=0;aborted=False
    for i,side in signals:
        if side not in (-1,1) or i<0:raise ValueError('Invalid signal')
        if len(gains)>=MAX_TRADES_PER_DAY or pnl<=STOP_NEW_ENTRIES_AFTER_DAILY_USD:
            continue
        signal_t=lo+(i+1)*STEP_100NS
        if signal_t<=last_exit:continue
        start=bisect_right(times,signal_t)
        r=simulate_single_trade(islice(events,start,None),
             Signal(day,signal_t,side),policy)
        if r['status']!='SYNTHETIC_FILL_MODEL_ONLY':
            invalid+=1
            if r['status'] in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',
                              'UNRESOLVED_END_OF_LAST_DATA'):
                aborted=True;break
            continue
        mark_trade_envelope(events,times,r,side,policy,tracker)
        gains.append(r['estimated_net_usd'])
        pnl=round(pnl+r['estimated_net_usd'],2)
        last_exit=r['exit_timestamp']
    return {
        'trades':len(gains),'wins':sum(x>0 for x in gains),
        'losses':sum(x<0 for x in gains),
        'net_usd':round(pnl,2),
        'total_positive_usd':round(sum(x for x in gains if x>0),2),
        'total_negative_usd':round(-sum(x for x in gains if x<0),2),
        'unknown_entry_or_exit':invalid,
        'day_aborted_due_to_ambiguity':aborted
    }

def audit_day(day,events,tracks):
    dev_day(day)
    bars=build_bars(events,day)
    signal_map,status=candidates(bars,day)
    if status in VALID_SKIP:
        return {'date':day,'status':status,'rows':{}}
    if status!='READY':raise ValueError('Unexpected signal status')
    parent=signal_map['T02_combined']
    selection=selected_families(parent,filters_for_signals(events,day,parent))
    rows={}
    for fam in FAMILIES:
        rows[fam]={}
        for sc in SCENARIOS:
            reference=simulate_portfolio(day,events,bars,selection[fam],sc)
            actual=trace_portfolio(day,events,bars,selection[fam],sc,tracks[fam][sc])
            for key,value in actual.items():
                if reference[key]!=value:
                    raise AssertionError(f'T04 parity failed {day}/{fam}/{sc}/{key}')
            rows[fam][sc]=actual
    return {'date':day,'status':'PARITY_OK_LAST_ENVELOPE_ONLY','rows':rows}

def summarize_month(month,day_rows,tracks):
    if month not in MONTHS or not day_rows:raise ValueError('SEALED_OR_EMPTY')
    valid=[x for x in day_rows if x['status']=='PARITY_OK_LAST_ENVELOPE_ONLY']
    if not valid:raise ValueError('No eligible sessions')
    for day in day_rows:
        if (day['date'][:7]!=month or day['status'] not in
                ('PARITY_OK_LAST_ENVELOPE_ONLY',*VALID_SKIP)):
            raise ValueError('Bad month/date/QC')
    families={}
    for fam in FAMILIES:
        families[fam]={}
        for sc in SCENARIOS:
            rows=[x['rows'][fam][sc] for x in valid]
            trades=sum(r['trades'] for r in rows)
            gain=sum(r['total_positive_usd'] for r in rows)
            loss=sum(r['total_negative_usd'] for r in rows)
            total=round(sum(r['net_usd'] for r in rows),2)
            tr=tracks[fam][sc]
            if abs(tr.equity-total)>0.01:raise AssertionError('Equity not reconciled')
            families[fam][sc]={
                'trades':trades,
                'net_usd':total,
                'profit_factor_net':round(gain/loss,5) if loss else None,
                'gross_positive_net_usd':round(gain,2),
                'gross_negative_net_usd':round(loss,2),
                'positive_days':sum(r['net_usd']>0 for r in rows),
                'worst_day_net_usd':min(r['net_usd'] for r in rows),
                'ambiguous_or_unknown':sum(r['unknown_entry_or_exit'] for r in rows),
                'aborted_days':sum(bool(r['day_aborted_due_to_ambiguity']) for r in rows),
                'last_envelope_segment':tr.segment()
            }
    return {'month':month,'status':'T08_DEV_RISK_DIAGNOSTIC_NOT_BROKER_OR_OOS',
        'source_days':len(day_rows),'eligible_days':len(valid),
        'excluded_days':len(day_rows)-len(valid),
        'funded_rules_verified':False,'costs_verified':False,
        'holdouts_opened':False,'families':families}

def run_month(root,month):
    if month not in MONTHS:raise ValueError('Holdout forbidden')
    tracks={f:{s:Envelope() for s in SCENARIOS} for f in FAMILIES}
    results=[]
    for day in month_days(root,month):
        d=dev_day(day)
        events=list(source_events(file_for(root,d,'Last')))
        results.append(audit_day(day,events,tracks))
    return summarize_month(month,results,tracks)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--month',required=True)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    opts=parser.parse_args()
    if opts.month not in MONTHS:raise SystemExit('SEALED_OR_UNKNOWN_MONTH')
    result=run_month(opts.root,opts.month)
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf8')
    print('T08_MONTH_AGGREGATE='+json.dumps(result,sort_keys=True,separators=(',',':')))
