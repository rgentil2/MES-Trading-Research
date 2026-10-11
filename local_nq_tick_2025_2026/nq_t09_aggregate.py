#!/usr/bin/env python3
"""Compare T09 independent NQ strategy versus T05 and shared NQ router, DEV only."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_t09_fast_trap import PORTFOLIOS,OWNERS
from nq_t04_execution import SCENARIOS

EXPECTED_T05={'baseline':(115,6220.0),
              'stress_1p5_fee_2ticks_each_side':(115,5102.5)}

def aggregate(months):
    if sorted(months)!=sorted(MONTHS):
        raise ValueError('Missing/extra months or sealed outcomes')
    for m,v in months.items():
        if (v['month']!=m or v['status']!='T09_EXPLORATORY_DEV_ONLY'
            or v['holdouts_opened'] is not False
            or v['broker_fees_verified'] is not False
            or v['all_portfolios_alternative_not_additive'] is not True):
            raise ValueError('Month source, status, or firewall mismatch')
    outputs={}
    for fam in PORTFOLIOS:
        outputs[fam]={}
        for sc in SCENARIOS:
            rows=[months[m]['families'][fam][sc] for m in MONTHS]
            trades=sum(x['trades'] for x in rows)
            net=round(sum(x['net_usd'] for x in rows),2)
            pos=sum(x['gross_positive_usd'] for x in rows)
            neg=sum(x['gross_negative_usd'] for x in rows)
            pf=round(pos/neg,4) if neg else None
            out={'trades':trades,'net_usd':net,
                'pf_net':pf,
                'mean_net_per_trade_usd':round(net/trades,3) if trades else None,
                'min_trades_per_month':min(x['trades'] for x in rows),
                'positive_months':sum(x['net_usd']>0 for x in rows),
                'unknown_or_ambiguous':sum(x['ambiguous_or_unknown'] for x in rows),
                'aborted_days':sum(x['aborted_days'] for x in rows),
                'monthly':[{'month':m,'trades':x['trades'],'net_usd':x['net_usd'],
                           'eligible_days':months[m]['eligible_days']}
                           for m,x in zip(MONTHS,rows)],
                'status':'DEVELOPMENT_NOT_INDEPENDENT',
                'funded_approved':False}
            if fam=='T09_NQ_COMBINED_ROUTER':
                attrib={name:{
                    'trades':sum(x['owner_executed'][name]['trades'] for x in rows),
                    'net_usd':round(sum(x['owner_executed'][name]['net_usd'] for x in rows),2)
                    } for name in OWNERS}
                if (sum(y['trades'] for y in attrib.values())!=trades or
                    abs(sum(y['net_usd'] for y in attrib.values())-net)>0.02):
                    raise AssertionError('Aggregated attribution does not match shared portfolio')
                out['executed_owner_attribution']=attrib
            outputs[fam][sc]=out
    for sc,(n,amount) in EXPECTED_T05.items():
        r=outputs['T05_377'][sc]
        if r['trades']!=n or abs(r['net_usd']-amount)>0.02:
            raise AssertionError('T05 historic benchmark changed or source altered')
    eligible_days=sum(x['eligible_days'] for x in months.values())
    if eligible_days!=135:raise AssertionError('Unexpected eligible days vs previous DEV')
    combined=outputs['T09_NQ_COMBINED_ROUTER']
    parent=outputs['T05_377']
    delta={}
    for sc in SCENARIOS:
        inc=round(combined[sc]['net_usd']-parent[sc]['net_usd'],2)
        delta[sc]={'incremental_net_usd':inc,
                   'incremental_net_per_eligible_session_usd':
                     round(inc/eligible_days,3)}
    stress=combined['stress_1p5_fee_2ticks_each_side']
    baseline=combined['baseline']
    checks={'incremental_net_per_day_base_positive':
               delta['baseline']['incremental_net_per_eligible_session_usd']>0,
            'at_least_5_trades_in_every_month':baseline['min_trades_per_month']>=5,
            'net_stress_positive':stress['net_usd']>0,
            'profit_factor_stress_at_least_1p25':
               stress['pf_net'] is not None and stress['pf_net']>=1.25,
            'nonduplicate_t09_executed':
               baseline['executed_owner_attribution']['T09_FAST_TRAP_60S']['trades']>0,
            'all_attribution_parity_cleared':
               all(outputs[f][s]['aborted_days']==0 and outputs[f][s]['unknown_or_ambiguous']==0
                   for f in PORTFOLIOS for s in SCENARIOS)}
    return {
        'status':'T09_NQ_ONLY_POST_SELECTION_DEVELOPMENT',
        'research_dates':'2025-10-15 through 2026-04-30 DEV only',
        'source_months':list(MONTHS),'eligible_days':eligible_days,
        'source_days':sum(x['source_days'] for x in months.values()),
        'original_T01_rapid_breakouts':sum(x['initial_fast_breakout_opportunities'] for x in months.values()),
        'confirmed_T09_fast_traps':sum(x['confirmed_fast_trap_signals'] for x in months.values()),
        't05_priority_same_bar':sum(x['same_timestamp_T05_priority_skips'] for x in months.values()),
        'models':outputs,'incremental_router_vs_t05':delta,
        'preliminary_non_floating_gates':checks,
        'preliminary_non_floating_pass':all(checks.values()),
        'all_candidates_exploratory':True,
        'full_joint_floating_DD_audit_done':False,
        'minute_vs_tick_independent_reconcile_done':False,
        'actual_BBO_fills_verified':False,
        'funding_rules_verified':False,
        'holdouts_opened':False}

def report(o):
    lines=['# T09 NQ-only: fast-trap strategy vs T05-377 and account router',
        '','**DEVELOPMENT ONLY**: post-selection on previously examined Oct2025-Apr2026.',
        '**Never** add the standalone columns as if they were simultaneous capital.',
        '','| Alternative portfolio | N trades | Net base USD | Net stress USD | PF stress | Min trades/month |',
        '|---|---:|---:|---:|---:|---:|']
    for fam in PORTFOLIOS:
        b=o['models'][fam]['baseline']
        s=o['models'][fam]['stress_1p5_fee_2ticks_each_side']
        lines.append(f"| {fam} | {b['trades']} | {b['net_usd']} | {s['net_usd']} | {s['pf_net']} | {b['min_trades_per_month']} |")
    lines.extend(['','## Incremental NQ portfolio outcome vs T05-377 benchmark','','- Base increment USD: '+
      str(o['incremental_router_vs_t05']['baseline']['incremental_net_usd']),
      '- Stress increment USD: '+str(o['incremental_router_vs_t05']['stress_1p5_fee_2ticks_each_side']['incremental_net_usd']),
      '- Main endpoint incremental base USD / eligible session: '+
         str(o['incremental_router_vs_t05']['baseline']['incremental_net_per_eligible_session_usd']),
      '- T01 initial accelerated breakout opportunities: '+str(o['original_T01_rapid_breakouts']),
      '- T09 confirmed rapid failures: '+str(o['confirmed_T09_fast_traps']),
      '- Same-timestamp decisions with fixed T05 priority: '+str(o['t05_priority_same_bar']),
      '- Joint contributions (baseline): '+str(o['models']['T09_NQ_COMBINED_ROUTER']['baseline']['executed_owner_attribution']),
      '','## Preliminary gates (does not include continuous joint DD or independent OOS)',''])
    for k,v in o['preliminary_non_floating_gates'].items():
        lines.append('- '+k+': '+('PASS' if v else 'FAIL'))
    lines.extend(['','**Full preliminary (nonfloating) gate**: '+('PASS' if o['preliminary_non_floating_pass'] else 'FAIL'),
        '','## Decisions','','- Neither positive development P&L nor PF is evidence of a new independent alpha.',
        '- Do not label T05-377 and 233+377 as independent portfolio strategies.',
        '- No Q3 2026 holdout, no May-Jun 2026 outcome, and no original H01-H78 holdout used.',
        '- Next if promising: T08-like stitched NQ portfolio equity audit, BBO execution and independent minute-source QC.',
        '- If not promising: keep failed T09 as a research observation; preregister next mechanism from its *specific* failure.',
        '- Funded account terms, full joint floating risk, annualized ETF comparison, and real fills remain NOT APPROVED.',
        ])
    return '\n'.join(lines)+'\n'

def load(folder):
    out={}
    for f in folder.rglob('nq_t09_*.json'):
        r=json.loads(f.read_text(encoding='utf8'))
        month=r['month']
        if month in out:raise ValueError('Duplicate month')
        out[month]=r
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    r=aggregate(load(a.inputs))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf8')
    a.report.write_text(report(r),encoding='utf8')
    print('T09_FINAL_SUMMARY='+json.dumps({
        'eligible_days':r['eligible_days'],
        'net_base':{f:r['models'][f]['baseline']['net_usd'] for f in PORTFOLIOS},
        'net_stress':{f:r['models'][f]['stress_1p5_fee_2ticks_each_side']['net_usd'] for f in PORTFOLIOS},
        'incremental_base':r['incremental_router_vs_t05']['baseline']['incremental_net_usd'],
        'checks':r['preliminary_non_floating_gates'],
        'attribution':r['models']['T09_NQ_COMBINED_ROUTER']['baseline']['executed_owner_attribution']
    },sort_keys=True))
