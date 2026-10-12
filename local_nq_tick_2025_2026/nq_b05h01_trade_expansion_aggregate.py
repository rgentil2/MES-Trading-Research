#!/usr/bin/env python3
"""B05H-01 single-preregistered hypothesis on existing Last DEV, same account."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_t04_execution import SCENARIOS
from nq_b05_t11_aggregate import group
from nq_b05h01_trade_expansion_month import BASE,NEW,ROUTER,MODELS,STRESS

PARITY={'baseline':(115,6220.0,1725.0),
        STRESS:(115,5102.5,1797.5),
        'stress_plus_10_usd_rt_FIXED_PATH_ONLY':(115,3952.5,1887.5)}

def aggregate(months):
    if set(months)!=set(MONTHS) or len(months)!=7:
        raise ValueError('B05H01 needs EXACTLY 7 frozen DEV months')
    for m in MONTHS:
        x=months[m]
        if (x['month']!=m or
            x['status']!='B05H01_HYPOTHESIS_EXPLORATORY_DEV_ONLY' or
            x['model_id']!=NEW or
            x['holdouts_opened'] is not False or
            x['broker_fills_verified'] is not False or
            x['new_market_history_acquired'] is not False or
            x['market_data_exported'] is not False or
            x['five_second_bars_used_for_new_H01_signals'] is not False or
            x['legacy_T05_signal_only_as_frozen_comparator'] is not True or
            x['source_days']!=x['eligible_days']+x['excluded_days'] or
            set(x['models'])!=set(MODELS)):
            raise ValueError('Malformed B05H01 or holdout violation')
    source=sum(months[m]['source_days'] for m in MONTHS)
    eligible=sum(months[m]['eligible_days'] for m in MONTHS)
    if (source,eligible)!=(140,135):
        raise ValueError('Frozen T05 140/135 DEV sample changed')
    outputs={}
    for model in MODELS:
        outputs[model]={}
        for sc in SCENARIOS:
            outputs[model][sc]=group(months,model,sc)
            if sc==STRESS:
                outputs[model]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']=group(
                    months,model,sc,extra=True)
    for sc,(count,net,dd) in PARITY.items():
        x=outputs[BASE][sc]
        if (x['trades']!=count or abs(x['net_usd']-net)>.01
                or abs(x['last_envelope_dd_usd']-dd)>.01):
            raise AssertionError('PREREG FROZEN T05 EXACT PARITY FAILED '+sc)
    rtr=outputs[ROUTER][STRESS]
    rtr_extra=outputs[ROUTER]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
    original=outputs[BASE][STRESS]
    original_extra=outputs[BASE]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
    contributions=rtr['owner_attribution']
    extra_contributions=rtr_extra['owner_attribution']
    executed_h01=contributions.get(NEW,{}).get('trades',0)
    executed_h01_net=contributions.get(NEW,{}).get('net_usd',0.)
    retained_t05=contributions.get(BASE,{}).get('trades',0)
    if (sum(q['trades'] for q in contributions.values())!=rtr['trades'] or
         abs(sum(q['net_usd'] for q in contributions.values())-rtr['net_usd'])>.01):
        raise AssertionError('B05H shared-owner attribution mismatch')
    if (sum(q['trades'] for q in extra_contributions.values())!=rtr_extra['trades'] or
        abs(sum(q['net_usd'] for q in extra_contributions.values())-rtr_extra['net_usd'])>.01):
        raise AssertionError('B05H surcharge owner reconciliation')
    needed={
     'shared_router_extra10_delta_positive':rtr_extra['net_usd']>original_extra['net_usd'],
     'router_stress_pf_at_least_1p25':rtr['pf'] is not None and rtr['pf']>=1.25,
     'router_extra10_pf_at_least_1p25':rtr_extra['pf'] is not None and rtr_extra['pf']>=1.25,
     'router_stress_last_dd_below_UNVERIFIED_2000':rtr['last_envelope_dd_usd']<2000.,
     'H01_executed_and_attributed_stress_net_positive':executed_h01>0 and executed_h01_net>0,
     'retained_T05_at_least_104_of_115':retained_t05>=104,
     'combined_at_least_five_each_month':all(z['trades']>=5 for z in rtr['monthly']),
    }
    additional={
     'H01_signal_opportunities':sum(months[m]['signal_counts'].get('h01_opportunities',0) for m in MONTHS),
     'H01_months_with_at_least_one_executed_trade':sum(
         months[m]['models'][ROUTER][STRESS]['owner_attribution'].get(NEW,{}).get('trades',0)>0
         for m in MONTHS),
     'H01_exec_trades':executed_h01,
     'H01_attributed_stress_net_usd':executed_h01_net,
     'T05_retained_in_router':retained_t05,
     'delta_router_minus_T05_stress_usd':round(rtr['net_usd']-original['net_usd'],2),
     'delta_router_minus_T05_extra10_usd':round(rtr_extra['net_usd']-original_extra['net_usd'],2),
    }
    status='B05H01_COMPLETE_DEV_EXPLORATORY_NOT_OOS'
    decision=('B05H01_PRELIMINARY_DEV_GATES_PASS_NOT_FUNDING'
        if all(needed.values()) else 'B05H01_FAIL_DO_NOT_PROMOTE')
    return {'status':status,'decision':decision,
      'source_months':list(MONTHS),'source_days':source,'eligible_days':eligible,
      'research_unit':'H01_233_PRINT_EXPANSION_4181_10946_TREND',
      'hypotheses_tested':1,'model_outputs':outputs,
      'incremental_gate':{'required':needed,'diagnostics':additional},
      'holdouts_opened':False,'new_history_acquired':False,
      'new_signals_use_5second_bars':False,
      'old_T05_comparator_legacy_only':True,
      'true_aggressor_or_level2_used':False,'broker_fills_verified':False,
      'funded_account_approved':False}

def report(x):
    lines=['# NQ B05H-01 — Expansión y aceleración 233 prints con 4181/10946 contexto',
      '', '**Una hipótesis nueva, cero barras de 5 segundos como señal nueva.**',
      'T05 usa su regla histórica inalterada solo como benchmark. Siete meses DEV',
      'reutilizados adaptativamente: **NO OOS, NO fills reales, NO fondeo aprobado.**',
      '',
      f"Fuente: {x['source_days']} sesiones, {x['eligible_days']} elegibles; fuente YA existente.",
      '',
      '| Modelo (alternativas en la misma cuenta) | Trades | Neto base USD | Neto estrés USD | PF estrés | DD Last estrés USD | Neto estrés+$10 USD | PF estrés+$10 |',
      '|---|---:|---:|---:|---:|---:|---:|---:|']
    for model in MODELS:
        z=x['model_outputs'][model]
        base=z['baseline'];stress=z[STRESS]
        extra=z['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
        lines.append(f"| {model} | {stress['trades']} | {base['net_usd']} | "
           f"{stress['net_usd']} | {stress['pf']} | {stress['last_envelope_dd_usd']} | "
           f"{extra['net_usd']} | {extra['pf']} |")
    p=x['incremental_gate']
    lines+=['','## Gates prerregistrados de contribución incremental — no seleccionar positivos','',
      f"**Decisión: {x['decision']}**",
      '',
      f"- H01 señales de oportunidad: {p['diagnostics']['H01_signal_opportunities']}.",
      f"- Trades H01 ejecutados dentro de router: {p['diagnostics']['H01_exec_trades']}; H01 atribuido estrés: {p['diagnostics']['H01_attributed_stress_net_usd']} USD.",
      f"- Trades T05 conservados: {p['diagnostics']['T05_retained_in_router']}/115.",
      f"- Router menos T05 bajo estrés: {p['diagnostics']['delta_router_minus_T05_stress_usd']} USD.",
      f"- Router menos T05 bajo estrés+$10/RT contable: {p['diagnostics']['delta_router_minus_T05_extra10_usd']} USD.",
      '']
    for k,v in p['required'].items():
        lines.append(f"- {k}: **{'PASS' if v else 'FAIL'}**")
    lines+=['','## Siete meses DEV bajo el mismo riesgo de cuenta','',
       '| Mes | T05 operaciones/neto USD | H01 operaciones/neto | Router operaciones/neto | H01 router operaciones |',
       '|---|---:|---:|---:|---:|']
    a=x['model_outputs'][BASE][STRESS]['monthly']
    b=x['model_outputs'][NEW][STRESS]['monthly']
    c=x['model_outputs'][ROUTER][STRESS]['monthly']
    for i,m in enumerate(MONTHS):
        n=x['model_outputs'][ROUTER][STRESS]['owner_attribution']
        # Month-level contributed H01 held separately within underlying month JSON.
        lines.append(f"| {m} | {a[i]['trades']}/{a[i]['net_usd']} | "
          f"{b[i]['trades']}/{b[i]['net_usd']} | "
          f"{c[i]['trades']}/{c[i]['net_usd']} | Ver resumen owner en artifacts mes |")
    lines+=['','## Interpretación y límites','',
       '- H01 trigger 233 PRINTS, contexto 4181/10946 PRINTS, sin velas de 5 segundos/minuto en su decisión, VWAP de grupo invariante a mismo timestamp; no usar close arbitrario.',
       '- T05 es baseline histórico congelado con reglas antiguas: NO describir su disparador como nueva idea.',
       '- Los 5 días excluidos por antiguo QC opening range afectan al COMPARADOR y a H01 para mantener igual denominador, pero H01 no usa opening range como disparador.',
       '- El presupuesto de 1 nueva familia no rejuvenece DEV ya optimizado previamente: falsación exploratoria.',
       '- El suplemento de $10 RT es contable sobre rutas fijas, NO recalcula stops y admisión diaria.',
       '- Last no acredita que órdenes habrían ejecutado a esos precios, mismo timestamp ni drawdown broker; la referencia $2000 es ILUSTRATIVA no verificada.',
       '- Si algún gate falla, NO promocionar ni rescatar parámetros o sustituir 233 por 377 postresultados.',
       '- Holdouts T mayo–junio, julio–septiembre y H cerrados; no nueva data.',
       '']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    months={}
    for f in a.inputs.rglob('nq_b05h01_*.json'):
        r=json.loads(f.read_text(encoding='utf8'))
        if r['month'] in months:raise ValueError('Duplicate month')
        months[r['month']]=r
    z=aggregate(months)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n',encoding='utf8')
    a.report.write_text(report(z),encoding='utf8')
    print('B05H01_AGGREGATE_SAFE='+json.dumps({
      'status':z['status'],'decision':z['decision'],
      'source':z['source_days'],'eligible':z['eligible_days'],
      'gates':z['incremental_gate']['required'],
      'diagnostics':z['incremental_gate']['diagnostics'],
      'models':{k:{s:{field:v[s][field] for field in
           ('trades','net_usd','pf','last_envelope_dd_usd')}
           for s in ('baseline',STRESS,'stress_plus_10_usd_rt_FIXED_PATH_ONLY')}
           for k,v in z['model_outputs'].items()},
      'no_sealed':True},sort_keys=True))
