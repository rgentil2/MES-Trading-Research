#!/usr/bin/env python3
"""Monthly T07 233/4181/10946 versus matched 240/4200/11000 and original T02/T05.

Preregistered BEFORE outcomes in NQ_T06_233_377_VS_250_400_CONTROL_PREREG.
All five mutually exclusive PORTFOLIO ALTERNATIVES (not additive PnL).
Only 2025-10..2026-04 (development already observed in T05).
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t07_three_scale import FAMILIES,analyze_day
from nq_t04_execution import SCENARIOS

def summarize_month(month,days):
    if month not in MONTHS or not days:raise ValueError('Out-of-scope or empty month')
    for day in days:
        if day.get('date_et','')[:7]!=month or day.get('holdout_2026_may_sep_opened') is not False:
            raise ValueError('Unexpected/holdout day')
        if day['status'] not in ('EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE',
            'SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE'):
            raise ValueError('Invalid data status')
    approved=[x for x in days if x['status']=='EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE']
    if not approved:raise ValueError('No eligible sessions')
    parent_count=sum(x['families']['T02_PARENT']['parent_opportunities'] for x in approved)
    outputs={}
    for family in FAMILIES:
        outputs[family]={}
        for scenario in SCENARIOS:
            daily=[x['families'][family]['cost_scenarios'][scenario] for x in approved]
            count=lambda k:sum(x[k] for x in daily)
            trades=count('trades')
            net=round(count('net_usd'),2)
            pos=count('total_positive_usd')
            neg=count('total_negative_usd')
            equity=peak=0.
            max_dd_closed=0.
            approx_float=0.
            for x in daily:
                approx_float=max(approx_float,peak-(equity+x['floating_last_mark_min_vs_day_start_usd']))
                equity=round(equity+x['net_usd'],2)
                peak=max(peak,equity)
                max_dd_closed=max(max_dd_closed,peak-equity)
            outputs[family][scenario]={
                'parent_opportunities':parent_count,
                'eligible_opportunities':sum(x['families'][family]['opportunities_after_filter'] for x in approved),
                'trades':trades,
                'net_usd':net,
                'net_per_parent_opportunity_usd':round(net/parent_count,2) if parent_count else None,
                'mean_net_per_trade_usd':round(net/trades,2) if trades else None,
                'profit_factor_net':round(pos/neg,3) if neg else None,
                'win_rate_pct':round(100*count('wins')/trades,2) if trades else None,
                'closed_day_equity_drawdown_usd':round(max_dd_closed,2),
                'approx_last_intramonth_drawdown_usd':round(max(max_dd_closed,approx_float),2),
                'days_with_trades':sum(x['trades']>0 for x in daily),
                'worst_day_usd':round(min(x['net_usd'] for x in daily),2),
                'unknown_entry_or_exit_count':count('unknown_entry_or_exit'),
                'ambiguity_abort_days':sum(int(x['day_aborted_due_to_ambiguity']) for x in daily),
            }
    return {
        'month':month,'source_days':len(days),'eligible_days':len(approved),
        'status':'EXPLORATORY_POST_T05_SELECTION_NOT_OOS',
        'returns_only_development_before_2026_may':True,
        'costs_are_assumptions':True,
        'source':'PRIVATE_DEV_LAST_PRINTS',
        'portfolios_are_alternatives_not_additive':True,
        'holdout_2026_may_sep_opened':False,
        'families':outputs
    }

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('Month forbidden')
    daily=[analyze_day(a.root,day) for day in month_days(a.root,a.month)]
    print('NQ_T07_MONTH='+json.dumps(summarize_month(a.month,daily),separators=(',',':'),sort_keys=True))
