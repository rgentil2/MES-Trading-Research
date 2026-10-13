#!/usr/bin/env python3
"""Aggregated monetary shadow study; never publishes individual sessions."""
import argparse, json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_b05_t11_aggregate import group
from nq_b05h01_trade_expansion_month import BASE, STRESS, NEW
from nq_t169_t188_monetary_month import IDS, MODEL_IDS, load_frozen

EXTRA='stress_plus_10_usd_rt_FIXED_PATH_ONLY'

def aggregate(months):
    policy=load_frozen()
    if set(months)!=set(MONTHS) or len(months)!=7:
        raise ValueError('EXACT_SEVEN_DEV_MONTHS_REQUIRED')
    for m in MONTHS:
        z=months[m]
        if (z['month']!=m or z['status']!='T169_T188_DEV_MONEY_EXPLORATORY_UNVERIFIED'
            or z['holdouts_opened'] is not False or z['new_history_acquired'] is not False
            or z['new_signal_5second_bars'] is not False
            or z['licensed_data_exported'] is not False
            or z['broker_fills_verified'] is not False
            or set(z['models'])!=set(MODEL_IDS)
            or z['source_days']<z['eligible_days']):
            raise ValueError('UNSAFE_OR_INCOMPLETE_MONTH_'+m)
    sources=sum(months[m]['source_days'] for m in MONTHS)
    ready=sum(months[m]['eligible_days'] for m in MONTHS)
    if (sources,ready)!=(140,135):raise AssertionError('T05_SOURCE_PARITY')
    totals={name:{STRESS:group(months,name,STRESS),
             EXTRA:group(months,name,STRESS,extra=True)}
             for name in MODEL_IDS}
    ref=totals[BASE][STRESS]; extra_ref=totals[BASE][EXTRA]
    if (ref['trades'],ref['net_usd'],ref['last_envelope_dd_usd'])!=(115,5102.5,1797.5):
        raise AssertionError('T05_STRESS_EXACT_PARITY')
    if (extra_ref['trades'],extra_ref['net_usd'],extra_ref['last_envelope_dd_usd'])!=(115,3952.5,1887.5):
        raise AssertionError('T05_EXTRA10_EXACT_PARITY')
    results={}
    for k in IDS:
        s=totals[k+'_ONLY'][STRESS]; sx=totals[k+'_ONLY'][EXTRA]
        r=totals[k+'_PLUS_T05'][STRESS]; rx=totals[k+'_PLUS_T05'][EXTRA]
        owners=r['owner_attribution']
        added=owners.get(NEW,{'trades':0,'net_usd':0})
        retained=owners.get(BASE,{'trades':0,'net_usd':0})
        if (added['trades']+retained['trades']!=r['trades']
            or abs(added['net_usd']+retained['net_usd']-r['net_usd'])>.01):
            raise AssertionError('ATTRIBUTION_'+k)
        if r['trades']!=rx['trades'] or abs(rx['net_usd']-r['net_usd']+10*r['trades'])>.01:
            raise AssertionError('EXTRA10_FIXED_PATH_'+k)
        gates={
         'incremental_net_after_plus10_positive':rx['net_usd']>extra_ref['net_usd'],
         'router_stress_PF_ge_1p25':r['pf'] is not None and r['pf']>=1.25,
         'router_plus10_PF_ge_1p25':rx['pf'] is not None and rx['pf']>=1.25,
         'router_last_dd_le_2000_UNVERIFIED':r['last_envelope_dd_usd']<=2000,
         'at_least_104_T05_trades_retained':retained['trades']>=104,
         'at_least_5_router_trades_each_month':all(q['trades']>=5 for q in r['monthly']),
         'candidate_executed':added['trades']>0}
        results[k]={
          'block':'A' if int(k[1:])<=173 else 'B' if int(k[1:])<=178
                   else 'C' if int(k[1:])<=183 else 'D',
          'question':next(t['question'] for t in policy['members'] if t['id']==k),
          'signal_days':sum(months[m]['signal_counts'].get(k+'_SIGNAL',0) for m in MONTHS),
          'standalone_trades':s['trades'],
          'standalone_net_stress_usd':s['net_usd'],
          'standalone_net_extra10_usd':sx['net_usd'],
          'router_trades':r['trades'],
          'router_net_stress_usd':r['net_usd'],
          'router_net_extra10_usd':rx['net_usd'],
          'router_pf_stress':r['pf'],'router_pf_extra10':rx['pf'],
          'router_last_dd_stress':r['last_envelope_dd_usd'],
          'router_last_dd_extra10':rx['last_envelope_dd_usd'],
          'added_executed':added['trades'],'added_attributed_net':added['net_usd'],
          't05_retained':retained['trades'],
          'delta_stress':round(r['net_usd']-ref['net_usd'],2),
          'delta_extra10':round(rx['net_usd']-extra_ref['net_usd'],2),
          'monthly_router_n':[z['trades'] for z in r['monthly']],
          'monthly_router_pnl':[z['net_usd'] for z in r['monthly']],
          'economic_gates':gates,
          'decision':('ECONOMIC_SCREEN_PASS_DEV_ONLY_NOT_ALPHA_OR_FUNDING'
                      if all(gates.values()) else 'FAIL_MONETARY_NO_PROMOTION')}
    return {'stage':'T169_T188_FOUR_BLOCKS_ECONOMIC_SHADOW_DEV_ONLY',
      'source_days':sources,'ready_days':ready,
      'hypotheses':len(results),'models_simulated':len(MODEL_IDS),
      'baseline':{'trades':115,'net_stress_usd':5102.5,'net_extra10_usd':3952.5,
          'pf_stress':ref['pf'],'pf_extra10':extra_ref['pf'],
          'last_dd_stress':1797.5,'last_dd_extra10':1887.5},
      'passed_exploratory_ids':[k for k,z in results.items()
                      if z['decision'].startswith('ECONOMIC_SCREEN_PASS')],
      'results':results,'p_q_ic90_gates_applied':False,
      'formal_D1_D2_promotions':0,'holdouts_opened':False,
      'new_history_acquired':False,'broker_fills_verified':False,
      'independent_OOS':False,'licensed_data_exported':False}

def render(r):
    lines=['# T169–T188 — Evaluación monetaria en cuatro bloques, comparación emparejada con T05',
      '', '**Modelo Last DEV no ejecutable ni validación OOS.** Cada fila es un router independiente, NO una cartera de 20 estrategias.',
      '', 'Fuente: 140 sesiones/135 READY, 7 meses oct2025–abr2026.',
      'T05 intacto: 115 trades, +US$5102,50 bajo estrés y +US$3952,50 con US$10 RT extra.',
      '', '| ID | Bloque | Señales | N solo | Neto solo estrés | N router | Alt ejecutadas | T05 conservadas | Delta estrés | Delta estrés+$10 | PF router+$10 | DD Last estrés | Pantalla |',
      '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for k,z in r['results'].items():
        lines.append(f"| {k} | {z['block']} | {z['signal_days']} | {z['standalone_trades']} | {z['standalone_net_stress_usd']} | {z['router_trades']} | {z['added_executed']} | {z['t05_retained']} | {z['delta_stress']} | {z['delta_extra10']} | {z['router_pf_extra10']} | {z['router_last_dd_stress']} | {'PASS-DEV' if z['decision'].startswith('ECONOMIC_SCREEN_PASS') else 'FAIL'} |")
    lines+=['', '**Pantallas económicas exploratorias que pasan (SIN aprobación real):** '+str(r['passed_exploratory_ids']),
     '', '## Interpretación y límites', '',
     '- Se preservó T05 y se usó un router compartido que arbitra por timestamp, capacidad y PnL diario sin mirar el futuro.',
     '- +US$10 RT es sensibilidad contable sobre camino fijo, no recalcula admisiones.',
     '- Los costos/slippage y envolvente Last no acreditan fills ni trailing real de firma. Límite DD $2.000 solo ilustrativo.',
     '- Q4/2025 y ene–abr/2026 han sido reexaminados adaptativamente: resultados in sample, no ROI futuro demostrado.',
     '- Se aplazan p/q/IC90 en la pantalla MONETARIA exploratoria, no se aprueba alfa ni se cambia D1/D2 formal.',
     '- No se puede agregar PnL standalone de filas con exposiciones coincidentes.',
     '- Sin nuevas barras 5s para señales, sin datos comprados y mayo–septiembre/H totalmente sellados.',
     '- Cualquier corrección técnica no puede cambiar stops, direcciones, horarios ni selección tras observar retornos.']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    x={}
    for f in a.inputs.rglob('nq_t169_t188_*.json'):
        y=json.loads(f.read_text())
        if y['month'] in x:raise ValueError('DUPLICATE_MONTH')
        x[y['month']]=y
    z=aggregate(x)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
    a.report.write_text(render(z))
    print('T169_T188_SAFE='+json.dumps({'ready':z['ready_days'],
      'pass_ids':z['passed_exploratory_ids'],
      'deltas':{k:{'n':v['standalone_trades'],'delta_extra10':v['delta_extra10'],
         'pf_extra10':v['router_pf_extra10'],'dd':v['router_last_dd_stress'],
         'decision':v['decision']} for k,v in z['results'].items()},
      'holdouts_opened':False},sort_keys=True))
