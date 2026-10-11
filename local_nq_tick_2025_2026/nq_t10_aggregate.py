#!/usr/bin/env python3
"""T10: frozen T05 Last/BBO quote availability, seven DEV months no trade-level data."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_t04_execution import SCENARIOS
from nq_t10_t05_bbo_endpoints import quantile

EXPECTED={'baseline':(115,6220.),'stress_1p5_fee_2ticks_each_side':(115,5102.5)}
CATS=('MISSING','LOCKED_OR_CROSSED','STALE_GT_250MS','VALID_STRICT_PRIOR_BBO')

def aggregate(months):
    if sorted(months)!=sorted(MONTHS):
        raise ValueError('Require seven and ONLY seven DEV months')
    for month,row in months.items():
        if (row['month']!=month or row['status']!='T10_PRIOR_BBO_QC_ONLY_NOT_REAL_FILLS'
            or row['holdouts_opened'] is not False or
            row['trade_level_data_exported'] is not False):
            raise ValueError('Month QC status or holdout firewall invalid')
    scenarios={}
    for sc in SCENARIOS:
        total=Counter()
        trade_count=0;pnl=0.;bad=0;aborts=0
        per_month=[]
        for month in MONTHS:
            x=months[month]['scenarios'][sc]
            trade_count+=x['trades'];pnl=round(pnl+x['simulated_last_net_usd'],2)
            bad+=x['unknown_or_ambiguous'];aborts+=x['aborted_days']
            total.update(x['counts'])
            per_month.append({'month':month,
                'trades':x['trades'],
                'quote_pairs_valid':x['counts'].get('valid_quote_pairs',0),
                'matched_pairs_pct':round(100*x['counts'].get('valid_quote_pairs',0)/x['trades'],2)
                   if x['trades'] else None,
                'entry_spread_median_ticks':x['entry_spread_median_ticks'],
                'exit_spread_median_ticks':x['exit_spread_median_ticks'],
                'paired_quote_delta_median_usd':x['quote_delta_paired_median_usd']})
        if (trade_count,pnl)!=EXPECTED[sc]:
            raise AssertionError(f'Old T05 Last outcomes not reproduced {sc}: {trade_count}, {pnl}')
        pairs=total['valid_quote_pairs']
        if total['trades']!=trade_count or pairs>trade_count:
            raise AssertionError('Wrong endpoint coverage denominators')
        if any(sum(total[f'{prefix}_{x}'] for x in CATS)!=trade_count
               for prefix in ('entry','exit')):
            raise AssertionError('Endpoint classifications do not cover all trades')
        scen={
           'frozen_T05_last_simulated_trades':trade_count,
           'frozen_T05_last_simulated_net_usd_NOT_EXECUTABLE':pnl,
           'entry_quotes_valid_n':total['entry_VALID_STRICT_PRIOR_BBO'],
           'exit_quotes_valid_n':total['exit_VALID_STRICT_PRIOR_BBO'],
           'both_endpoints_valid_n':pairs,
           'both_endpoints_valid_pct':round(100*pairs/trade_count,2),
           'entry_quote_categories':{v:total['entry_'+v] for v in CATS},
           'exit_quote_categories':{v:total['exit_'+v] for v in CATS},
           'paired_side_correct_quote_delta_sum_usd_ACCOUNTING_ONLY':
             round(total['paired_quote_delta_usd_cents']/100,2),
           'paired_original_model_net_usd_ACCOUNTING_ONLY':
             round(total['paired_baseline_model_net_usd_cents']/100,2),
           'quote_matched_baseline_total_minus_delta_unmatched_NOT_VALID':True,
           'entry_last_fill_outside_prior_bbo_n':
                total['entry_last_outside_prior_bbo'],
           'exit_last_fill_outside_prior_bbo_n':
                total['exit_last_outside_prior_bbo'],
           'ambiguous_or_unknown_last_trade_states':bad,
           'aborted_last_days':aborts,
           'per_month':per_month,
           'status':'COMPLETE_QUOTE_ENDPOINT_QC_ONLY' if pairs==trade_count and not bad and not aborts
             else 'INCOMPLETE_OR_AMBIGUOUS_QUOTE_COVERAGE',
           'actual_exchange_sequence_or_broker_fill_verified':False
        }
        scenarios[sc]=scen
    return {'status':'NQ_T10_T05_EXECUTION_QC_NOT_TRADING_APPROVED',
        'source_months':list(MONTHS),
        'source_days':sum(x['source_days'] for x in months.values()),
        'eligible_days':sum(x['eligible_days'] for x in months.values()),
        'source_source_NQ_Last_Bid_Ask_private_checked':True,
        'prior_quote_rule':'BID_ASK_T_STRICTLY_LESS_THAN_LAST_MODEL_ENDPOINT_T',
        'quote_max_age_ms':250,
        'holdouts_opened':False,
        'new_hypothesis_executed':False,
        'independent_minute_parity_done':False,
        'broker_fills_or_ETF_comparison_done':False,
        'scenarios':scenarios}

def text_report(x):
    lines=['# NQ T10 — quote availability at T05-377 simulated endpoints',
        '','**EXPLORATORY SOURCE QUALITY ONLY**. No executable backtest, no firm',
        'account approval, no access to May-Jun 2026 outcomes or sealed Jul-Sep.',
        '','| Scenario | Frozen trades | Prior BBO valid at both endpoints |',
        'Valid pair % | Entry valid | Exit valid | Classification |',
    ]
    lines[-2]=lines[-2]+' '+lines.pop()
    lines+=['|---|---:|---:|---:|---:|---:|---|']
    for sc in SCENARIOS:
        y=x['scenarios'][sc]
        lines.append(f"| {sc} | {y['frozen_T05_last_simulated_trades']} | "
          f"{y['both_endpoints_valid_n']} | {y['both_endpoints_valid_pct']}% | "
          f"{y['entry_quotes_valid_n']} | {y['exit_quotes_valid_n']} | {y['status']} |")
    lines+=['','## Availability / source caveats','',
        '- T05 Last-only net P&L is **unchanged**; the quote comparisons are not fills.',
        '- Strictly earlier Bid/Ask, both sides positive and max age 250ms.',
        '- No guarantees of queue, latency, cancellation, marketable price or stop fills.',
        '- Quote delta sensitivity is paired ACCOUNTING ONLY on existing trade timestamps;',
        '  it never re-evaluates TP/SL, daily stop, fills, drawdown, or signals.',
        '- Do not extrapolate matched-only quote sensitivity to unmatched trades.',
        '','## Monthly matched quote coverage','',
        '| Month | T05 trades base | Both endpoints valid | % valid |',
        '|---|---:|---:|---:|']
    for r in x['scenarios']['baseline']['per_month']:
        lines.append(f"| {r['month']} | {r['trades']} | {r['quote_pairs_valid']} | {r['matched_pairs_pct']}% |")
    lines+=['','## Preliminary conclusion','',
      'The audit only establishes as-of BBO availability and price mismatches.',
      'A real quote-aware stop/TP and order simulation with sequenced data plus',
      'independent Minute Last vs Tick Last reconciliation is still required.',
      'The NQ-only multi-strategy objective remains unchanged. T09 is not promoted.',
      '']
    return '\n'.join(lines)

def load(path):
    rows={}
    for f in path.rglob('nq_t10_*.json'):
        x=json.loads(f.read_text(encoding='utf8'))
        if x['month'] in rows:raise ValueError('Duplicate month')
        rows[x['month']]=x
    return rows

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--inputs',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--report',required=True,type=Path)
    args=ap.parse_args()
    r=aggregate(load(args.inputs))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n',encoding='utf8')
    args.report.write_text(text_report(r),encoding='utf8')
    print('T10_RESULT='+json.dumps({sc:{
        'trades':v['frozen_T05_last_simulated_trades'],
        'matched':v['both_endpoints_valid_n'],
        'coverage_pct':v['both_endpoints_valid_pct'],
        'entry_valid':v['entry_quotes_valid_n'],
        'exit_valid':v['exit_quotes_valid_n'],
        'quote_delta_usd_ACCOUNTING_ONLY':v['paired_side_correct_quote_delta_sum_usd_ACCOUNTING_ONLY'],
        'status':v['status']} for sc,v in r['scenarios'].items()},sort_keys=True))
