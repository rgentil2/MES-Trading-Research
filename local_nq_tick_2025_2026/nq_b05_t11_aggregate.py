#!/usr/bin/env python3
"""B05 seven-month T11 VWAP ablations and T05-priority router audit.

All dates already seen for T05: never treat this result as OOS. Never turn
postselected ablations into fresh hypotheses. Publish aggregate data only.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_t04_execution import SCENARIOS
from nq_b05_t11_month import MODELS,BASE,ROUTER,EXPECTED_T05
from nq_b03_aggregate import stitch

PF_TARGET=1.25
UNVERIFIED_DD_USD=2000.0

def group(rows,model,scenario,extra=False):
    fields=[]
    original_agg={'trades':0,'net_usd':0.,'positive_usd':0.,'negative_usd':0.}
    allowners={}
    for m in MONTHS:
        row=rows[m]['models'][model][scenario]
        x=row['stress_extra_10usd_fixed_path'] if extra else row
        for key in original_agg:
            if key in x:
                original_agg[key]+=x[key]
        fields.append({
            'frozen_path_adjusted_net_usd':x['net_usd'],
            'gross_positive_net_usd':x['positive_usd'],
            'gross_negative_net_usd':x['negative_usd'],
            'trades':x['trades'],
            'last_envelope_segment':x['last_envelope_segment']})
        for owner,o in x['owner_attribution'].items():
            z=allowners.setdefault(owner,{'trades':0,'net_usd':0.})
            z['trades']+=o['trades']
            z['net_usd']=round(z['net_usd']+o['net_usd'],2)
    r=stitch(fields)
    if (r['trades']!=original_agg['trades'] or
        abs(r['adjusted_net_usd_FROZEN_PATH_ONLY']-original_agg['net_usd'])>.01):
        raise AssertionError('B05 monthly risk stitch trade/net mismatch')
    return {
        'trades':r['trades'],
        'net_usd':r['adjusted_net_usd_FROZEN_PATH_ONLY'],
        'pf':r['pf_FROZEN_PATH_ONLY'],
        'last_envelope_dd_usd':r['last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH'],
        'closed_dd_usd':r['closed_trade_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH'],
        'owner_attribution':allowners,
        'monthly':[
            {'month':m,
             'trades':(rows[m]['models'][model][scenario]['stress_extra_10usd_fixed_path']
                       if extra else rows[m]['models'][model][scenario])['trades'],
             'net_usd':(rows[m]['models'][model][scenario]['stress_extra_10usd_fixed_path']
                       if extra else rows[m]['models'][model][scenario])['net_usd']}
            for m in MONTHS],
        'broker_fill_or_live_dd':False,
        'extra_cost_is_frozen_path_only':bool(extra)}

def aggregate(months):
    if sorted(months)!=sorted(MONTHS):
        raise ValueError('Require all and ONLY 7 DEV months')
    if any(months[m]['month']!=m or
           months[m]['status']!='B05_T11_DEV_EXPLORATORY_LAST_ONLY' or
           months[m]['holdouts_opened'] is not False or
           months[m]['broker_fills_verified'] is not False or
           months[m]['trade_level_exported'] is not False or
           months[m]['source_sequenced_quotes_used'] is not False or
           months[m]['source_days']!=months[m]['eligible_days']+months[m]['excluded_days']
           for m in MONTHS):
        raise ValueError('Incomplete months/security violation')
    count=sum(months[m]['source_days'] for m in MONTHS)
    eligible=sum(months[m]['eligible_days'] for m in MONTHS)
    if (count,eligible)!=(140,135):
        raise AssertionError(f'Wrong DEV coverage {count}/{eligible}')
    out={}
    for name in MODELS:
        out[name]={}
        for sc in SCENARIOS:
            out[name][sc]=group(months,name,sc)
            if sc=='stress_1p5_fee_2ticks_each_side':
                out[name]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']=group(months,name,sc,extra=True)
    for sc,(trades,pnl) in EXPECTED_T05.items():
        z=out[BASE][sc]
        if z['trades']!=trades or abs(z['net_usd']-pnl)>.01:
            raise AssertionError(f'Frozen T05 changed {sc}')
    # Preserve cross-study B03 risk: exactly same 7-month chronological Last path.
    expected_dd={'baseline':1725.,'stress_1p5_fee_2ticks_each_side':1797.5,
                 'stress_plus_10_usd_rt_FIXED_PATH_ONLY':1887.5}
    for sc,dd in expected_dd.items():
        if abs(out[BASE][sc]['last_envelope_dd_usd']-dd)>.01:
            raise AssertionError(f'B03 baseline DD parity failed {sc}')
    if (out[BASE]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']['trades']!=115 or
        out[BASE]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']['net_usd']!=3952.5):
        raise AssertionError('B03 extra-cost parity failed')
    original=out[BASE]['stress_1p5_fee_2ticks_each_side']
    combined=out[ROUTER]['stress_1p5_fee_2ticks_each_side']
    original_extra=out[BASE]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
    combined_extra=out[ROUTER]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
    delta=round(combined['net_usd']-original['net_usd'],2)
    extra_delta=round(combined_extra['net_usd']-original_extra['net_usd'],2)
    owners=combined['owner_attribution']
    if sum(x['trades'] for x in owners.values())!=combined['trades'] or abs(
        sum(x['net_usd'] for x in owners.values())-combined['net_usd'])>.01:
        raise AssertionError('Combined shared-router attribution mismatch')
    add_n=owners.get('T11_FULL',{}).get('trades',0)
    t05_in_router=owners.get(BASE,{}).get('trades',0)
    losses=[x for x in combined['monthly'] if x['net_usd']<0]
    min_per_month=min(x['trades'] for x in combined['monthly'])
    gates={
        'incremental_stress_plus10_net_usd_positive':extra_delta>0,
        'stress_original_pf_ge_1p25':(combined['pf'] is not None
                                     and combined['pf']>=PF_TARGET),
        'stress_plus10_pf_ge_1p25_preferred':(combined_extra['pf'] is not None
                                             and combined_extra['pf']>=PF_TARGET),
        'last_envelope_dd_below_2000_UNVERIFIED_reference':
            combined['last_envelope_dd_usd']<UNVERIFIED_DD_USD,
        'combined_at_least_5_trades_each_dev_month':min_per_month>=5,
        'meaningful_T11_incremental_execution_n_greater_than_zero':add_n>0,
        'T11_added_5_or_more_executed_each_month':
            False, # computed below through contributor aggregation
    }
    add_month=[]
    for m in MONTHS:
        x=months[m]['models'][ROUTER]['stress_1p5_fee_2ticks_each_side']
        n=x['owner_attribution'].get('T11_FULL',{}).get('trades',0)
        add_month.append({'month':m,'t11_contributed_trades':n})
    gates['T11_added_5_or_more_executed_each_month']=all(
        m['t11_contributed_trades']>=5 for m in add_month)
    # The original 5 trades/mo criterion is more realistic for the final combined router.
    # A new component may prove useful with fewer than five; both are shown, not hidden.
    full_gate=all(gates[k] for k in (
        'incremental_stress_plus10_net_usd_positive',
        'stress_original_pf_ge_1p25',
        'last_envelope_dd_below_2000_UNVERIFIED_reference',
        'combined_at_least_5_trades_each_dev_month',
        'meaningful_T11_incremental_execution_n_greater_than_zero',
        'T11_added_5_or_more_executed_each_month'))
    decision='PRELIMINARY_INCREMENTAL_SCREENS_PASS_NOT_OOS' if full_gate else 'DO_NOT_PROMOTE_T11_B05_INCREMENTAL_GATE_FAIL'
    return {
        'status':'NQ_B05_COMPLETE_POSTSELECTION_EXPLORATORY_ONLY',
        'source_months':list(MONTHS),
        'source_days':count,'eligible_days':eligible,'holdouts_opened':False,
        'hypothesis_tested':'T11_VWAP_ACCEPTANCE_PULLBACK_PRINT_REACCEL',
        'ablation_is_independent_alpha':False,
        'new_holdout_or_broker_fills_tested':False,
        'models':out,
        'router_primary_comparison':{
            'stress_original_delta_usd_ROUTER_MINUS_FROZEN_T05':delta,
            'stress_plus10_fixed_path_delta_usd_ROUTER_MINUS_FROZEN_T05':extra_delta,
            't11_executed_in_shared_router':add_n,
            't05_executed_in_shared_router':t05_in_router,
            'same_bar_priority_t05_ties':sum(months[m]['same_bar_t05_priority_ties'] for m in MONTHS),
            'monthly_incremental_t11':add_month,
            'number_of_negative_combined_months':len(losses),
            'gates':gates,
            'decision':decision}}

def report(x):
    lines=['# NQ-B05 — T11 VWAP causal vs T05, ablations and shared NQ router',
    '','**POSTSELECTION DEV ONLY**: no OOS, no broker fills or validated funding terms.',
    'Thresholds and controls frozen in B05 prereg, no optimization after results.',
    '','## Full 7-month alternative-model comparison','',
    '| Model (ALTERNATIVES, not additive) | Base trades | Base net USD | Stress trades | Stress net USD | Stress PF | Stress Last-envelope DD USD | Stress+$10/RT net USD (same trade path) |',
    '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,row in x['models'].items():
        b=row['baseline'];s=row['stress_1p5_fee_2ticks_each_side']
        extra=row['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
        lines.append(f"| {name} | {b['trades']} | {b['net_usd']} | "
                     f"{s['trades']} | {s['net_usd']} | {s['pf']} | "
                     f"{s['last_envelope_dd_usd']} | {extra['net_usd']} |")
    p=x['router_primary_comparison']
    lines+=['','## Primary shared-account incremental criterion','',
        f"- Router minus frozen T05 stress = **{p['stress_original_delta_usd_ROUTER_MINUS_FROZEN_T05']} USD**.",
        f"- Router minus frozen T05 stress+$10/RT = **{p['stress_plus10_fixed_path_delta_usd_ROUTER_MINUS_FROZEN_T05']} USD** (contabilidad sobre rutas fijas).",
        f"- Router T05 trades = {p['t05_executed_in_shared_router']}, T11 trades = {p['t11_executed_in_shared_router']}; priority T05 on simultaneous 5s bar.",
        f"- **DECISION:** \`{p['decision']}\`.",
        '','## Gates (predeclared)', '']
    for gate,ok in p['gates'].items():
        lines.append(f"- {gate}: **{'PASS' if ok else 'FAIL'}**")
    lines+=['','## Every development month in STRESS', '',
            '| Month | T05 trades/net | T11 FULL trades/net | Router trades/net | T11 executions inside router |',
            '|---|---:|---:|---:|---:|']
    ref=x['models'][BASE]['stress_1p5_fee_2ticks_each_side']['monthly']
    t11=x['models']['T11_FULL']['stress_1p5_fee_2ticks_each_side']['monthly']
    rtr=x['models'][ROUTER]['stress_1p5_fee_2ticks_each_side']['monthly']
    for t,a,b,c in zip(MONTHS,ref,t11,rtr):
        n=next(z['t11_contributed_trades'] for z in p['monthly_incremental_t11'] if z['month']==t)
        lines.append(f"| {t} | {a['trades']} / {a['net_usd']} | "
                     f"{b['trades']} / {b['net_usd']} | {c['trades']} / {c['net_usd']} | {n} |")
    lines+=['','## Limitations and next step','',
        '- 7 DEV months were used to research T05 first: do NOT assert statistical independence or formal multiple-testing success for T11.',
        '- Separate ablations are nested variants with shared VWAP cause and may NOT be counted as independent strategies or profitable portfolios.',
        '- We reused original T04 stop, TP, 2/day, daily-stop, 1 NQ and frozen simulated Last fill engine; no intraday slippage/queue proof.',
        '- The additional +$10/RT is ACCOUNTING ONLY and does not recalc any actual stop, fill, daily stop or router admission.',
        '- Without an incremental net benefit under a single shared router and adequate DD/PF, reject promotion even when standalone appears profitable.',
        '- Next phase B06 can only evaluate an eligible T11 component if these predeclared gates pass; otherwise preserve the negative finding and design a DIFFERENT causal hypothesis under fresh preregistration.',
        '- No May-Sep 2026 outcomes accessed; 2025/26 historical H program remains sealed.',
        '']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    data={}
    for f in a.inputs.rglob('nq_b05_*.json'):
        r=json.loads(f.read_text(encoding='utf8'))
        if r['month'] in data:raise ValueError('Duplicate month')
        data[r['month']]=r
    result=aggregate(data)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    a.report.write_text(report(result),encoding='utf8')
    p=result['router_primary_comparison']
    print('NQ_B05_SAFE_SUMMARY='+json.dumps({
        'status':result['status'],'source_days':result['source_days'],
        'eligible_days':result['eligible_days'],'decision':p['decision'],
        'delta_stress':p['stress_original_delta_usd_ROUTER_MINUS_FROZEN_T05'],
        'delta_stress_extra':p['stress_plus10_fixed_path_delta_usd_ROUTER_MINUS_FROZEN_T05'],
        'models':{n:{sc:{'trades':z['trades'],'net':z['net_usd'],
                        'pf':z['pf'],'dd':z['last_envelope_dd_usd']}
             for sc,z in models.items()}
            for n,models in result['models'].items()}
        },sort_keys=True))
