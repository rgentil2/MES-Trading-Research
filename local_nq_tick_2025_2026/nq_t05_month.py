#!/usr/bin/env python3
"""Month-level comparison T05 233/377 Last-print causal filters vs T02 parent.
Only NQ Tick Last DEV 2025-10..2026-04. Never live, no real fees, no holdouts.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t05_fibonacci_bars import FAMILIES,analyze_day
from nq_t04_execution import SCENARIOS

def summarize_month(month,days):
    if month not in MONTHS or not days:raise ValueError('SEALED_OR_EMPTY')
    for d in days:
        if d.get('date_et','')[:7]!=month or d.get('holdout_2026_may_sep_opened') is not False:
            raise ValueError('Month mismatch or sealed source flag')
        if d['status'] not in ('EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE',
                              'SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE'):
            raise ValueError('Unexpected source QC status')
    eligible=[d for d in days if d['status']=='EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE']
    if not eligible:raise ValueError('No eligible days')
    outputs={}
    for fam in FAMILIES:
        outputs[fam]={}
        for scenario in SCENARIOS:
            r=[d['families'][fam]['cost_scenarios'][scenario] for d in eligible]
            raw_signal_counts=[d['families'][fam]['opportunities_after_filter'] for d in eligible]
            count=lambda k:sum(x[k] for x in r)
            equity=0.;peak=0.;dd_closed=0.;dd_float=0.
            for item in r:
                dd_float=max(dd_float,peak-(equity+item['floating_last_mark_min_vs_day_start_usd']))
                equity=round(equity+item['net_usd'],2)
                peak=max(peak,equity)
                dd_closed=max(dd_closed,peak-equity)
            gains=count('total_positive_usd')
            losses=count('total_negative_usd')
            trades=count('trades')
            outputs[fam][scenario]={
                'opportunities':sum(raw_signal_counts),
                'parent_opportunities':sum(d['families'][fam]['parent_opportunities'] for d in eligible),
                'executed_trades':trades,
                'active_days':sum(x['trades']>0 for x in r),
                'total_net_usd':round(equity,2),
                'mean_net_per_trade_usd':round(equity/trades,2) if trades else None,
                'net_profit_factor':round(gains/losses,3) if losses else None,
                'win_rate_pct':round(100*count('wins')/trades,2) if trades else None,
                'closed_equity_dd_usd':round(dd_closed,2),
                'approx_intra_last_mark_dd_usd':round(max(dd_closed,dd_float),2),
                'aborted_ambiguity':sum(int(x['day_aborted_due_to_ambiguity']) for x in r),
                'unknown_entries_exits':count('unknown_entry_or_exit'),
                'skipped_max_trades':count('skipped_max_two_or_daily_stop'),
                'worst_trade_usd':min((x['worst_trade_usd'] for x in r
                      if x['worst_trade_usd'] is not None),default=None),
                'daily_net_usd':[{'day':d['date_et'],'pnl':r[i]['net_usd']} for i,d in enumerate(eligible)]
            }
    return {'month':month,'status':'EXPLORATORY_SIMULATED_LAST_PRINTS_ONLY',
        'source_days':len(days),'eligible_days':len(eligible),
        'excluded_days':len(days)-len(eligible),'families':outputs,
        'ticker':'NQ','research_approach':'short-term tick count bars, not microsecond latency',
        'fees_from_funding_company_verified':False,
        'live_fills_or_real_roi':False,
        'holdout_2026_may_sep_opened':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--month',required=True)
    p.add_argument('--root',type=Path,required=True)
    a=p.parse_args()
    daily=[analyze_day(a.root,d) for d in month_days(a.root,a.month)]
    print('NQ_T05_MONTH='+json.dumps(summarize_month(a.month,daily),sort_keys=True,separators=(',',':')))
