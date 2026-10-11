#!/usr/bin/env python3
"""NQ-B05C T13: all 7 DEV months, independent compression-release and shared-router gates."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_t04_execution import SCENARIOS
from nq_b05_t11_aggregate import group # generic frozen-path risk stitch, unchanged
from nq_b05c_t13_month import BASE,NEW,ROUTER,MODELS,STRESS

REFERENCE_DD=2000.0 # NOT broker terms
PF_MIN=1.25

def aggregate(months):
    if sorted(months)!=sorted(MONTHS):
        raise ValueError('Exactly seven preregistered DEV months required')
    if any(months[m]['month']!=m or
           months[m]['status']!='NQ_B05C_T13_EXPLORATORY_DEV_ONLY' or
           months[m]['holdouts_opened'] is not False or
           months[m]['broker_fills_verified'] is not False or
           months[m]['raw_tick_or_trade_level_exported'] is not False or
           months[m]['source_sequenced_quotes_used'] is not False or
           months[m]['source_days']!=months[m]['eligible_days']+months[m]['excluded_days']
           for m in MONTHS):
        raise ValueError('Incomplete source months or data boundary violation')
    src=sum(months[m]['source_days'] for m in MONTHS)
    elig=sum(months[m]['eligible_days'] for m in MONTHS)
    if (src,elig)!=(140,135):
        raise AssertionError('Frozen DEV sample changed')
    out={}
    for model in MODELS:
        out[model]={}
        for sc in SCENARIOS:
            out[model][sc]=group(months,model,sc)
            if sc==STRESS:
                out[model]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']=group(
                    months,model,sc,extra=True)
    expected={
        'baseline':(115,6220.0,1725.0),
        STRESS:(115,5102.5,1797.5),
        'stress_plus_10_usd_rt_FIXED_PATH_ONLY':(115,3952.5,1887.5)}
    for sc,(num,net,dd) in expected.items():
        x=out[BASE][sc]
        if x['trades']!=num or abs(x['net_usd']-net)>.01 or abs(
            x['last_envelope_dd_usd']-dd)>.01:
            raise AssertionError('Frozen T05 historical parity FAIL '+sc)
    combined=out[ROUTER][STRESS]
    comb_extra=out[ROUTER]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
    t05=out[BASE][STRESS]
    t05extra=out[BASE]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
    contribution=combined['owner_attribution']
    num_added=contribution.get(NEW,{}).get('trades',0)
    p_added=contribution.get(NEW,{}).get('net_usd',0.)
    if sum(z['trades'] for z in contribution.values())!=combined['trades']:
        raise AssertionError('Route trade attribution wrong')
    if abs(sum(z['net_usd'] for z in contribution.values())-combined['net_usd'])>.01:
        raise AssertionError('Route owner PnL attribution wrong')
    monthly_new=[
        {'month':m,'t13_trades_in_router':months[m]['models'][ROUTER][STRESS]['owner_attribution'].get(NEW,{}).get('trades',0)}
        for m in MONTHS]
    required={
      'incremental_router_stress_extra10_net_positive':
        comb_extra['net_usd']>t05extra['net_usd'],
      'router_stress_pf_ge_1p25':
        (combined['pf'] is not None and combined['pf']>=PF_MIN),
      'router_stress_extra10_pf_ge_1p25':
        (comb_extra['pf'] is not None and comb_extra['pf']>=PF_MIN),
      'router_stress_last_envelope_dd_below_UNVERIFIED_2000':
        combined['last_envelope_dd_usd']<REFERENCE_DD,
      'T13_attributed_stress_net_positive_and_trades':
        num_added>0 and p_added>0,
      'T05_retains_at_least_104_of_115_original_trades':
        contribution.get(BASE,{}).get('trades',0)>=104,
      'router_at_least_five_trades_each_month':
        all(z['trades']>=5 for z in combined['monthly'])}
    optional={'T13_at_least_one_contributed_trade_in_five_of_seven_months':
        sum(z['t13_trades_in_router']>=1 for z in monthly_new)>=5}
    decision=('PRELIMINARY_DEV_GATES_PASS_NOT_OOS_NOT_FUNDED'
         if all(required.values())
         else 'B05C_T13_FAIL_DO_NOT_PROMOTE')
    return {
      'status':'B05C_T13_COMPLETE_ADAPTIVE_DEV_NOT_OOS',
      'source_months':list(MONTHS),'source_days':src,
      'eligible_days':elig,'holdouts_opened':False,
      'hypothesis_family':'T13_COMPRESSION_RELEASE',
      'prior_adaptive_search_T05_T09_T11':True,
      'actual_fills_verified':False,
      'model_outputs':out,
      'router_gate':{
        'delta_stress_usd':round(combined['net_usd']-t05['net_usd'],2),
        'delta_stress_extra10_usd':round(comb_extra['net_usd']-t05extra['net_usd'],2),
        'router_t05_trades':contribution.get(BASE,{}).get('trades',0),
        'router_t13_trades':num_added,
        'router_t13_attributed_net_stress_usd':p_added,
        'ties':sum(months[m]['same_bar_t05_priority_ties'] for m in MONTHS),
        'required_gates':required,
        'optional_frequency_diagnostic':optional,
        'monthly_t13_in_router':monthly_new,
        'decision':decision}}

def markdown(result):
    lines=['# NQ-B05C — T13 shock volumen negociado y reversión causal del desplazamiento',
        '',
        '**Siete meses DEV ya explorados: NO OOS, NO fills reales, NO límite de fondeo verificado.**',
        'Las alternativas no se suman; el router es una sola cuenta 1 NQ, 2 trades/día.',
        '',
        '| Modelo | Trades | P&L base USD | P&L estrés USD | PF estrés | DD Last estrés USD | P&L estrés+$10 USD (misma ruta) |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for model in result['model_outputs']:
        o=result['model_outputs'][model]
        b=o['baseline'];s=o[STRESS];z=o['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
        lines.append(f"| {model} | {s['trades']} | {b['net_usd']} | {s['net_usd']} | {s['pf']} | {s['last_envelope_dd_usd']} | {z['net_usd']} |")
    p=result['router_gate']
    lines+=['','## Router T05 prioridad, una cuenta, comparación incremental','',
        f"- Router menos T05 neto estrés: **{p['delta_stress_usd']} USD**.",
        f"- Router menos T05 neto estrés+$10/RT contable: **{p['delta_stress_extra10_usd']} USD**.",
        f"- En router: **{p['router_t05_trades']} trades T05**, **{p['router_t13_trades']} trades T13**, T13 aporte neto estrés **{p['router_t13_attributed_net_stress_usd']} USD**.",
        f"- Prioridad en empate T05: {p['ties']} coincidencias en misma barra.",
        f"- **DECISIÓN preregistrada: {p['decision']}**.",
        '','## Gates obligatorios']
    for key,ok in p['required_gates'].items():
        lines.append(f"- {key}: **{'PASS' if ok else 'FAIL'}**")
    for key,ok in p['optional_frequency_diagnostic'].items():
        lines.append(f"- {key}: **{'PASS' if ok else 'FAIL / insufficient'}**")
    lines+=['','## Todos los meses bajo estrés (sin filtrar)','',
        '| Mes | T05 trades/neto | T13 trades/neto | Router trades/neto | T13 trades en router |',
        '|---|---:|---:|---:|---:|']
    base=result['model_outputs'][BASE][STRESS]['monthly']
    t13=result['model_outputs'][NEW][STRESS]['monthly']
    router=result['model_outputs'][ROUTER][STRESS]['monthly']
    for i,m in enumerate(MONTHS):
        x=next(x for x in p['monthly_t13_in_router'] if x['month']==m)
        lines.append(f"| {m} | {base[i]['trades']}/{base[i]['net_usd']} | "
                     f"{t13[i]['trades']}/{t13[i]['net_usd']} | "
                     f"{router[i]['trades']}/{router[i]['net_usd']} | "
                     f"{x['t13_trades_in_router']} |")
    lines+=['','## Interpretación y límites','',
      '- T13 pregunta por pérdida de desplazamiento tras shock de qty negociada; no usa OR como disparador, VWAP ni agresor Bid/Ask. Solo primera señal por día.',
      '- El ancho OR aún determina el mismo stop histórico T04 (16–48 price ticks) para comparabilidad.',
      '- El recargo $10/RT es contabilidad sobre ruta congelada: no recalcula stop, fill, daily stop o capacidad.',
      '- Se informa toda ablation aunque alguna sea rentable; ninguna es una nueva estrategia independiente.',
      '- La métrica DD es envolvente adversa Last, no broker trailing DD. La referencia $2000 no se verificó con firma.',
      '- El conjunto se compara contra T05 SOLO, mismo simulador/capital; no suma P&L de estrategias aisladas.',
      '- Siete meses 2025-10..2026-04 son retrospectivos ya usados en búsqueda adaptativa; no inferir causalidad independiente.',
      '- Mayo–junio 2026 resultados y julio–septiembre pseudo-forward continúan cerrados.',
      '']
    return '\n'.join(lines)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args()
    results={}
    for f in args.inputs.rglob('nq_b05b_*.json'):
        x=json.loads(f.read_text(encoding='utf8'))
        if x['month'] in results:raise ValueError('Duplicate month')
        results[x['month']]=x
    x=aggregate(results)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n',encoding='utf8')
    args.report.write_text(markdown(x),encoding='utf8')
    p=x['router_gate']
    print('NQ_B05C_SAFE_RESULTS='+json.dumps({
      'source_days':x['source_days'],'eligible_days':x['eligible_days'],
      'decision':p['decision'],'delta_stress':p['delta_stress_usd'],
      'delta_stress_extra10':p['delta_stress_extra10_usd'],
      'owners':{'t05':p['router_t05_trades'],'t13':p['router_t13_trades'],
                't13_net':p['router_t13_attributed_net_stress_usd']},
      'gates':p['required_gates'],
      'models':{name:{sc:{k:r[k] for k in ('trades','net_usd','pf','last_envelope_dd_usd')}
            for sc,r in data.items()} for name,data in x['model_outputs'].items()},
    },sort_keys=True))
