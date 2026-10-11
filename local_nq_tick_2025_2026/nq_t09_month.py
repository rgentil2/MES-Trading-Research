#!/usr/bin/env python3
"""Month-level analysis for T09 pre-registered NQ second-signal portfolio.

Only Oct25-Apr26 DEV Last, no intraday private trades or ticks in output.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_t09_fast_trap import PORTFOLIOS,OWNERS,analyze_day
from nq_t04_execution import SCENARIOS

VALID=('T09_POST_SELECTION_EXPLORATORY',
       'SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE')

def summarize_month(month,days):
    if month not in MONTHS or not days:raise ValueError('SEALED_OR_EMPTY')
    for d in days:
        if (d.get('date_et','')[:7]!=month or d.get('holdout_2026_may_sep_opened') is not False
           or d['status'] not in VALID):
            raise ValueError('Invalid date/holdout/QC in T09 month')
    eligible=[d for d in days if d['status']=='T09_POST_SELECTION_EXPLORATORY']
    if not eligible:raise ValueError('No eligible T09 days')
    families={}
    for fam in PORTFOLIOS:
        families[fam]={}
        for sc in SCENARIOS:
            rows=[d['families'][fam]['scenarios'][sc] for d in eligible]
            trades=sum(r['trades'] for r in rows)
            net=round(sum(r['net_usd'] for r in rows),2)
            positive=round(sum(r['total_positive_usd'] for r in rows),2)
            negative=round(sum(r['total_negative_usd'] for r in rows),2)
            equity=peak=dd_closed=dd_last_approx=0.
            for r in rows:
                dd_last_approx=max(dd_last_approx,peak-(equity+r['floating_last_mark_min_vs_day_start_usd']))
                equity=round(equity+r['net_usd'],2)
                peak=max(peak,equity)
                dd_closed=max(dd_closed,peak-equity)
            if abs(equity-net)>0.02:raise AssertionError('Equity mismatch')
            result={
                'opportunities':sum(d['families'][fam]['opportunities'] for d in eligible),
                'trades':trades,
                'net_usd':net,
                'net_per_trade_usd':round(net/trades,3) if trades else None,
                'profit_factor_net':round(positive/negative,4) if negative else None,
                'win_rate_pct':round(100*sum(r['wins'] for r in rows)/trades,2) if trades else None,
                'gross_positive_usd':positive,
                'gross_negative_usd':negative,
                'closed_daily_curve_dd_usd':round(dd_closed,2),
                'approx_last_based_dd_usd_not_continuous':round(max(dd_closed,dd_last_approx),2),
                'days_with_trades':sum(r['trades']>0 for r in rows),
                'worst_day_usd':min(r['net_usd'] for r in rows),
                'ambiguous_or_unknown':sum(r['unknown_entry_or_exit'] for r in rows),
                'aborted_days':sum(int(r['day_aborted_due_to_ambiguity']) for r in rows),
                'blocked_overlap':sum(r['skipped_overlap'] for r in rows),
                'blocked_capacity':sum(r['skipped_max_two_or_daily_stop'] for r in rows),
            }
            if fam=='T09_NQ_COMBINED_ROUTER':
                result['owner_executed']={name:{
                    'trades':sum(r['owner_contributions'][name]['trades'] for r in rows),
                    'net_usd':round(sum(r['owner_contributions'][name]['net_usd'] for r in rows),2)
                } for name in OWNERS}
                if (sum(x['trades'] for x in result['owner_executed'].values())!=trades
                    or abs(sum(x['net_usd'] for x in result['owner_executed'].values())-net)>0.01):
                    raise AssertionError('Router attribution must reconcile')
            families[fam][sc]=result
    return {'month':month,'status':'T09_EXPLORATORY_DEV_ONLY',
       'source_days':len(days),'eligible_days':len(eligible),
       'initial_fast_breakout_opportunities':sum(d['original_fast_breakout_opportunities'] for d in eligible),
       'confirmed_fast_trap_signals':sum(d['fast_trap_confirmations'] for d in eligible),
       'same_timestamp_T05_priority_skips':sum(d['duplicate_decision_timestamp_t05_priority'] for d in eligible),
       'families':families,'holdouts_opened':False,'broker_fees_verified':False,
       'source_is_private_last':True,'all_portfolios_alternative_not_additive':True}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--out',type=Path,required=False)
    a=p.parse_args()
    if a.month not in MONTHS:raise SystemExit('SEALED_OR_INVALID_MONTH')
    days=[analyze_day(a.root,d) for d in month_days(a.root,a.month)]
    r=summarize_month(a.month,days)
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('T09_MONTH_SUMMARY='+json.dumps({
        'month':r['month'],'eligible_days':r['eligible_days'],
        't01':r['initial_fast_breakout_opportunities'],
        'fast_traps':r['confirmed_fast_trap_signals'],
        'baseline':{f:r['families'][f]['baseline']['net_usd']
                    for f in PORTFOLIOS}},sort_keys=True))
