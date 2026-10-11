#!/usr/bin/env python3
"""Monthly risk and frequency summary of PRE-REGISTERED exploratory T04.
Data: NQ Last DEV Oct25-Apr26 only. Costs are unverified assumptions;
neither broker fills nor funded eligibility are established.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import month_days,MONTHS
from nq_t04_execution import simulate_day,PORTFOLIOS,SCENARIOS

def summarize_month(month,day_rows):
    if month not in MONTHS:raise ValueError('Holdout or forbidden month')
    if not day_rows:raise ValueError('Empty study month')
    for x in day_rows:
        if x['date_et'][:7]!=month or x['holdout_2026_may_sep_opened'] is not False:
            raise ValueError('Out of scope day/holdout flag')
        if x['status'] not in ('EXPLORATORY_SIM_ONLY','SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE'):
            raise ValueError('Invalid day QC')
    eligible=[x for x in day_rows if x['status']=='EXPLORATORY_SIM_ONLY']
    stats={}
    for strategy in PORTFOLIOS:
        stats[strategy]={}
        for scenario in SCENARIOS:
            rows=[x['results'][strategy][scenario] for x in eligible]
            total=lambda k:sum(row[k] for row in rows)
            trades=total('trades');wins=total('wins')
            prof=total('total_positive_usd');loss=total('total_negative_usd')
            equity=peak=dd_closed=dd_floating=0.
            for r in rows:
                # Last-only intra-trade mark approximates, does not prove
                # provider/broker floating drawdown or margin rules.
                dd_floating=max(dd_floating,peak-(equity+r['floating_last_mark_min_vs_day_start_usd']))
                equity=round(equity+r['net_usd'],2)
                peak=max(peak,equity)
                dd_closed=max(dd_closed,peak-equity)
            stats[strategy][scenario]={
                'opportunities':total('opportunities'),'trades':trades,
                'active_days':sum(r['trades']>0 for r in rows),
                'wins':wins,'losses':total('losses'),
                'winrate_pct':round(100*wins/trades,2) if trades else None,
                'net_usd':round(equity,2),
                'mean_net_usd_per_trade':round(equity/trades,2) if trades else None,
                'gross_positive_net_usd':round(prof,2),'gross_negative_net_usd':round(loss,2),
                'profit_factor_net':round(prof/loss,3) if loss else None,
                'max_closed_dd_last_usd':round(dd_closed,2),
                'max_intra_last_mark_dd_usd_CONSERVATIVE_APPROX':round(max(dd_floating,dd_closed),2),
                'worst_day_net_usd':min((r['net_usd'] for r in rows),default=None),
                'worst_trade_usd':min((r['worst_trade_usd'] for r in rows
                              if r['worst_trade_usd'] is not None),default=None),
                'invalid_signals_or_ambiguous':total('unknown_entry_or_exit'),
                'aborted_days_ambiguity':sum(r['day_aborted_due_to_ambiguity'] for r in rows),
                'discarded_capacity':total('skipped_max_two_or_daily_stop'),
                'discarded_overlap':total('skipped_overlap'),
                'daily_net_usd':[{'day':x['date_et'],
                   'net_usd':x['results'][strategy][scenario]['net_usd']} for x in eligible]
            }
    return {'month':month,'status':'EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE',
        'source_days':len(day_rows),'eligible_days':len(eligible),
        'excluded_days':len(day_rows)-len(eligible),
        'portfolio_scenarios':stats,'funded_fee_schedule_verified':False,
        'actual_fills_or_payouts':False,'holdout_2026_may_sep_opened':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    args=p.parse_args()
    days=month_days(args.root,args.month)
    results=[simulate_day(args.root,d) for d in days]
    r=summarize_month(args.month,results)
    print('NQ_T04_MONTH='+json.dumps(r,sort_keys=True,separators=(',',':')))
