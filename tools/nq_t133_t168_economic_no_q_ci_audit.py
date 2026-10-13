#!/usr/bin/env python3
"""Audit previously published SAFE D1 aggregates ONLY; never load market data.

Remove ONLY BH q and bootstrap confidence interval from decision gates.
Retain pre-registered N/PF/positive net/stress/season/month/DD gates.
This is a POST-HOC sensitivity analysis, not a new strategy selection.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from collections import Counter

IDS=[f'T{i}' for i in range(133,169)]
EXPECTED_STAGE='T133_T168_D1_ECONOMIC_PROXIES_FULL36_DEV_UNVERIFIED'
LOW_N_IDS={'T134','T138','T139','T143','T144'}
MODELLED_NOTE='Ejecucion Last SIMULADA; no fills reales ni OOS independiente.'

def score(r):
    n=r['N_proxy_trades']
    net=r['net_total_usd']
    pf=r['PF_proxy']
    dd=r['maxDD_proxy_usd']
    s15=r['net_stress_1_5x_total_usd']
    s10=r['net_stress_plus_10_rt_usd']
    q4=r['diagnostic_oct_dec_2025_net']
    jan=r['internal_jan_apr_2026_net']
    monthconc=r['month_positive_concentration']
    gates={
      'n_ge_15':n>=15,
      'net_total_gt_0':net>0,
      'net_expectancy_gt_0':r['net_expectancy_per_proxy_trade_usd'] is not None and r['net_expectancy_per_proxy_trade_usd']>0,
      'PF_ge_1_25':pf is not None and pf>=1.25,
      'stress_1_5x_gt_0':s15>0,
      'stress_extra_10_rt_gt_0':s10>0,
      'Q4_2025_gt_0':q4>0,
      'Jan_Apr_2026_gt_0':jan>0,
      'maxDD_le_1500':dd<=1500,
      'month_concentration_lt_40pct':monthconc is not None and monthconc<0.4,
    }
    # This is a diagnostic overlay, not a licensed execution gate.
    d0_ok=r['N_case_D0']>=15 and r['N_control_D0']>=15
    summary={
      'id':None,'block':r['block'],'N_proxy':n,'D0_testable':d0_ok,
      'net_usd_model':round(net,2),'PF_model':None if pf is None else round(pf,4),
      'DD_usd_model':round(dd,2),'stress_1_5x_model':round(s15,2),
      'stress_extra_10_rt_model':round(s10,2),
      'diagnostic_Q4_net':round(q4,2),'internal_2026_net':round(jan,2),
      'month_positive_concentration':None if monthconc is None else round(monthconc,4),
      'gates':gates,'fails':[k for k,v in gates.items() if not v],
      'pass_all_economic_gates_without_q_and_ci':all(gates.values())}
    return summary

def audit(data):
    if (data.get('stage')!=EXPECTED_STAGE
        or data.get('family_size')!=36
        or (data.get('source'),data.get('eligible'))!=(140,135)
        or set(data.get('results',{}))!=set(IDS)
        or data.get('broker_fills_verified') is not False
        or data.get('not_OOS_confirmed') is not True
        or data.get('holdouts_opened') is not False
        or data.get('new_data') is not False
        or data.get('economic_confirmatory_pass_ids')!=[]):
        raise ValueError('UNVERIFIED_OR_WRONG_SAFE_36_MEMBER_SUMMARY')
    rows=[]
    for k in IDS:
        d=data['results'][k]
        row=score(d);row['id']=k
        if (d['broker_fills_verified'] is not False
            or (row['N_proxy']<15)!=(k in LOW_N_IDS)
            or round(row['net_usd_model'],2)!=round(d['net_total_usd'],2)
            or abs(sum(d['monthly_net_usd'].values())-d['net_total_usd'])>1e-6
            or abs(row['diagnostic_Q4_net']+row['internal_2026_net']-row['net_usd_model'])>.011):
            raise AssertionError('INVALID_OR_NON_RECONCILED_MEMBER_'+k)
        rows.append(row)
    passers=[x['id'] for x in rows if x['pass_all_economic_gates_without_q_and_ci']]
    pos=[x for x in rows if x['net_usd_model']>0]
    npos=[x for x in pos if x['N_proxy']>=15]
    pfpos=[x for x in npos if x['PF_model'] is not None and x['PF_model']>=1.25]
    counters={k:sum(row['gates'][k] for row in rows)
      for k in rows[0]['gates']}
    return {
      'source_action':38326216082,'original_cohort':'NQ-C133-168',
      'sensitivity_analysis':'REMOVE_BOTH_BH_Q_AND_CI90_ONLY',
      'original_cost_and_risk_frozen':True,'hypotheses':36,
      'positive_net_model_count':len(pos),
      'positive_net_model_ids':[x['id'] for x in pos],
      'positive_net_and_N_ge15_count':len(npos),
      'positive_net_and_N_ge15_ids':[x['id'] for x in npos],
      'positive_net_N_ge15_PF_ge125_count':len(pfpos),
      'positive_net_N_ge15_PF_ge125_ids':[x['id'] for x in pfpos],
      'economically_pass_all_except_q_and_ci':len(passers),
      'economically_pass_ids':passers,'single_gate_pass_counts':counters,
      'rows':rows,'D2_eligible':False,
      'broker_fills_verified':False,'true_OOS':False}

def md(result):
    r=result;lines=[
     '# T133–T168 — auditoría SIN q-BH NI IC90, con todos los filtros económicos intactos',
     '',
     '**Análisis de sensibilidad POST-HOC** sobre el JSON SAFE de [Action D1 económica 38326216082](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38326216082). **No genera hipótesis nuevas, ni ejecuta trades, ni abre holdouts**, ni constituye nueva confirmación. Se **eliminan exclusivamente q-BH36 e IC90**. Mantiene los 10 gates objetivos N≥15 trades PROXY, neto>0, esperanza>0, PF≥1,25, estrés1,5×>0, estrés +US$10RT>0, resultado positivo separadamente Q4-2025 y Ene–Abr2026, DD≤US$1500, y concentración del mes positivo mayor <40%. No se exige una operación semanal: requisito deseable, no puerta dura congelada.',
     '',
     f"**36 estrategias; neto positivo SIMULADO={r['positive_net_model_count']}**; "
     f"positivo con N≥15={r['positive_net_and_N_ge15_count']}; "
     f"además PF≥1,25={r['positive_net_N_ge15_PF_ge125_count']}; "
     f"**CUMPLEN TODOS LOS 10 ECONÓMICOS SIN q/IC90 = {r['economically_pass_all_except_q_and_ci']}**.",
     '',
     '| Hipótesis | Bloque | N proxy | Neto USD MODELO | PF MODELO | Estrés1,5× | Estrés +$10RT | Q4-2025 | Ene–Abr26 | DD USD | Concentración positiva máxima | Gates fallidos (sin q/IC90) | ¿Pasa económicos? |',
     '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|']
    def money(x):return f'${x:+,.2f}'
    for z in r['rows']:
        c=z['month_positive_concentration']
        lines.append(f"| {z['id']} | {z['block']} | {z['N_proxy']} | "
         f"{money(z['net_usd_model'])} | {z['PF_model'] or 'N/D'} | "
         f"{money(z['stress_1_5x_model'])} | {money(z['stress_extra_10_rt_model'])} | "
         f"{money(z['diagnostic_Q4_net'])} | {money(z['internal_2026_net'])} | "
         f"{money(z['DD_usd_model'])} | "
         f"{'N/D' if c is None else f'{c*100:.1f}%'} | "
         f"{', '.join(z['fails']) or 'Ninguno'} | "
         f"{'SÍ' if z['pass_all_economic_gates_without_q_and_ci'] else 'NO'} |")
    lines+=['',
     '## Interpretación',
     '',
     'Estos criterios comprueban que un beneficio bajo el MODELO DE EJECUCIÓN elegido sería lo suficientemente frecuente, rentable, resistente a costes y diversificado por período. **NO** miden certeza de obtener fills negociables; Last no contiene book/Bid-Ask ni prioridad. **NO** constituyen una prueba de rentabilidad real ni autorización de fondeo.',
     '',
     'Los dos tramos cronológicos provienen de DEV reutilizado y no constituyen OOS independiente. PF, costos y drawdown son del modelo, no bróker real.',
     '',
     '**Esta reevaluación NO cambia el estado del embudo principal: D1 familiar estadística original=0 PASS, D2=0, holdouts sellados.**',
     '']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();result=audit(json.loads(a.input.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    a.report.write_text(md(result)+'\n')
    print('NQ_NO_Q_AND_NO_CI_ECONOMIC_AUDIT_FINAL='+json.dumps(
      {k:v for k,v in result.items() if k not in ('rows','single_gate_pass_counts')},
      sort_keys=True))
    print('NQ_ECONOMIC_GATES_COUNTS='+json.dumps(result['single_gate_pass_counts'],sort_keys=True))
    print('NQ_POSITIVE_ECONOMIC_STRATEGY_DETAILS='+json.dumps(
      [x for x in result['rows'] if x['net_usd_model']>0],sort_keys=True))
