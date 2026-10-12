#!/usr/bin/env python3
"""B05G complete 7-month DEV perturbation audit; all four variants always shown."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_t04_execution import SCENARIOS
from nq_b05_t11_aggregate import group
from nq_b05g_same_timestamp_month import VARIANTS,STRESS

EXPECTED={'baseline':(115,6220.0,1725.0),
          STRESS:(115,5102.5,1797.5),
          'stress_plus_10_usd_rt_FIXED_PATH_ONLY':(115,3952.5,1887.5)}
B05F_ADJACENT_EQUAL_TS=15979304

def aggregate(months):
    if set(months)!=set(MONTHS) or len(months)!=len(MONTHS):
        raise ValueError('B05G seven and only seven registered DEV months required')
    for month in MONTHS:
        x=months[month]
        if (x['month']!=month or
           x['status']!='B05G_T05_EQUAL_TIMESTAMP_ORDER_STRESS_DEV_ONLY' or
           x['holdouts_opened'] is not False or
           x['broker_fills_verified'] is not False or
           x['trade_level_exported'] is not False or
           x['source_exchange_sequence_verified'] is not False or
           x['new_market_history_acquired'] is not False or
           set(x['models'])!=set(VARIANTS) or
           x['source_days']!=x['eligible_days']+x['excluded_days']):
            raise ValueError('B05G invalid/unsafe source month '+month)
    source=sum(months[x]['source_days'] for x in MONTHS)
    eligible=sum(months[x]['eligible_days'] for x in MONTHS)
    if (source,eligible)!=(140,135):
        raise ValueError('B05G 140/135 frozen DEV source parity failed')
    tie=Counter();signal=Counter()
    for month in MONTHS:
        tie.update(months[month]['timestamp_ties'])
        signal.update(months[month]['signal_change_counts'])
    if tie['adjacent_same_ts_prints']!=B05F_ADJACENT_EQUAL_TS:
        raise AssertionError('B05G source same timestamp count differs from B05F')
    models={}
    for v in VARIANTS:
        models[v]={}
        for sc in SCENARIOS:
            models[v][sc]=group(months,v,sc)
            if sc==STRESS:
                models[v]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']=group(
                    months,v,sc,extra=True)
        if (models[v][STRESS]['trades']!=
            models[v]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']['trades']):
            raise AssertionError('B05G frozen-path charge altered trade counts')
        z=models[v]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
        original=models[v][STRESS]
        if abs(z['net_usd']-(original['net_usd']-10*original['trades']))>.01:
            raise AssertionError('B05G fixed +10 dollar charge parity')
    for sc,(n,net,dd) in EXPECTED.items():
        z=models[VARIANTS[0]][sc]
        if (z['trades']!=n or abs(z['net_usd']-net)>.01 or
            abs(z['last_envelope_dd_usd']-dd)>.01):
            raise AssertionError('B05G original T05 exact historical parity '+sc)
    baseline=models[VARIANTS[0]][STRESS]
    bounds={x:{'n_trades':models[x][STRESS]['trades'],
        'stress_net_usd':models[x][STRESS]['net_usd'],
        'stress_pf':models[x][STRESS]['pf'],
        'stress_last_envelope_dd_usd':models[x][STRESS]['last_envelope_dd_usd'],
        'stress_plus10_fixed_path_net_usd':
            models[x]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']['net_usd'],
        'stress_plus10_fixed_path_pf':
            models[x]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']['pf'],
        'stress_plus10_fixed_path_dd':
            models[x]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']['last_envelope_dd_usd'],
        'stress_delta_vs_original_usd':
            round(models[x][STRESS]['net_usd']-baseline['net_usd'],2),
        'days_with_signal_changes_vs_original':
            signal['signal_days_'+x] if x!=VARIANTS[0] else 0,
        'added_signals_vs_original':
            signal['added_signals_'+x] if x!=VARIANTS[0] else 0,
        'removed_signals_vs_original':
            signal['removed_signals_'+x] if x!=VARIANTS[0] else 0,
        } for x in VARIANTS}
    worst=min(VARIANTS,key=lambda x:bounds[x]['stress_net_usd'])
    most_dd=max(VARIANTS,key=lambda x:bounds[x]['stress_last_envelope_dd_usd'])
    return {
      'status':'B05G_COMPLETED_TIMESTAMP_ORDER_SENSITIVITY_ONLY_NOT_OOS',
      'source_months':list(MONTHS),
      'source_days':source,'eligible_days':eligible,
      'holdouts_opened':False,'new_history_acquired':False,
      'new_alpha_hypotheses_tested':0,
      'timestamp_tie_counters':dict(tie),
      'signal_change_counts':dict(signal),
      'models':models,'comparison':bounds,
      'minimum_stress_net_usd_across_variants':bounds[worst]['stress_net_usd'],
      'worst_stress_net_variant':worst,
      'maximum_last_envelope_dd_usd_across_variants':
           bounds[most_dd]['stress_last_envelope_dd_usd'],
      'maximum_last_envelope_dd_variant':most_dd,
      'all_variants_stress_net_positive':
         all(bounds[v]['stress_net_usd']>0 for v in VARIANTS),
      'all_variants_stress_plus10_pf_ge_1p25':
         all((bounds[v]['stress_plus10_fixed_path_pf'] or 0)>=1.25 for v in VARIANTS),
      'actual_exchange_sequence_verified':False,
      'actual_broker_fills_verified':False,'funded_rules_verified':False,
      'fixed_path_extra_surcharge_not_recomputed_stops':True,
      'real_trades_or_ticks_exported':False,
    }

def report(x):
    lines=['# NQ-B05G — robustez a orden intratimestamp de ticks Last, sin datos nuevos',
      '',
      '**Solo NQ Last Oct2025–Abr2026 DEV; cuatro ordenamientos determinísticos congelados.',
      'NO equivalen a secuencia verdadera CME, NO constituyen nuevas estrategias,',
      'NO certifican fills ni fondeo y NO abren holdouts.**',
      '',
      'Fuente auditada: 140 días, 135 elegibles. La variante ORIGINAL reproduce',
      'exactamente T05: 115 trades +$6220 base, +$5102,50 estrés,',
      'DD Last estrés $1797,50, +$10 RT ruta fija +$3952,50.',
      '',
      '## Comparación de las CUATRO alternativas (misma estrategia T05)',
      '',
      '| Orden de filas Last con tiempo idéntico | Trades estrés | Neto estrés USD | PF estrés | DD Last estrés USD | Neto estrés+$10 RT fijo USD | PF estrés+$10 fijo | Días señales cambiadas |',
      '|---|---:|---:|---:|---:|---:|---:|---:|']
    for v in VARIANTS:
        d=x['comparison'][v]
        lines.append(f"| {v} | {d['n_trades']} | {d['stress_net_usd']} | "
            f"{d['stress_pf']} | {d['stress_last_envelope_dd_usd']} | "
            f"{d['stress_plus10_fixed_path_net_usd']} | "
            f"{d['stress_plus10_fixed_path_pf']} | "
            f"{d['days_with_signal_changes_vs_original']} |")
    c=x['timestamp_tie_counters']
    lines+=['','## Evidencia de fuente y sensibilidad','',
      f"- Iguales timestamps en filas Last adyacentes: **{c['adjacent_same_ts_prints']}**, coincide exactamente con B05F.",
      f"- Grupos de timestamps con múltiples prints: **{c.get('multi_print_groups',0)}**, grupos con más de un precio **{c.get('multi_price_groups',0)}**.",
      f"- **Mínimo neto estrés entre perturbaciones: {x['minimum_stress_net_usd_across_variants']} USD ({x['worst_stress_net_variant']}).**",
      f"- **Peor DD Last estrés: {x['maximum_last_envelope_dd_usd_across_variants']} USD ({x['maximum_last_envelope_dd_variant']}).**",
      f"- Todos los ordenamientos positivos neto estrés: **{x['all_variants_stress_net_positive']}**; todos con PF estrés+$10 ≥1,25: **{x['all_variants_stress_plus10_pf_ge_1p25']}**.",
      '- Una permutación no representa una réplica aleatoria independiente ni un fill posible garantizado. Los resultados cuantifican sensibilidad del modelo Last a una incertidumbre de orden.',
      '- La comparación de señal se hace solo sobre los 135 días elegibles, sin publicar sesiones/trades individuales.',
      '- No escoger el orden rentable, ni borrar simultáneos, ni usar P&L para limpiar datos.',
      '',
      '## Desglose de los siete meses bajo estrés',
      '',
      '| Mes | Original operaciones/neto USD | Reverse operaciones/neto | Ascendente operaciones/neto | Descendente operaciones/neto |',
      '|---|---|---|---|---|']
    for i,month in enumerate(MONTHS):
        cells=[]
        for v in VARIANTS:
            z=x['models'][v][STRESS]['monthly'][i]
            cells.append(f"{z['trades']} / {z['net_usd']}")
        lines.append('| '+month+' | '+' | '.join(cells)+' |')
    lines+=['','## Decisión',
      '',
      'T05 permanece exploratoria aun si las perturbaciones mejoran o empeoran su P&L, debido a reutilización del mismo DEV, incertidumbre de secuencia/fills y estrés coste+$10.',
      'El paso siguiente debe utilizar exclusivamente fuente existente, nueva pregunta medible Last, evaluación incremental en UNA cuenta y controles de selección adaptativa.',
      'B06, B07–B10, fondeo y OOS sellado permanecen bloqueados.',
      '']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    months={}
    for f in a.inputs.rglob('nq_b05g_*.json'):
        z=json.loads(f.read_text('utf8'))
        if z['month'] in months:raise ValueError('Duplicate month')
        months[z['month']]=z
    x=aggregate(months)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf8')
    a.report.write_text(report(x)+'\n',encoding='utf8')
    print('B05G_FINAL_SAFE='+json.dumps({
       'status':x['status'],'source_days':x['source_days'],
       'eligible_days':x['eligible_days'],
       'worst_variant':x['worst_stress_net_variant'],
       'worst_stress_net':x['minimum_stress_net_usd_across_variants'],
       'max_last_dd':x['maximum_last_envelope_dd_usd_across_variants'],
       'all_positive':x['all_variants_stress_net_positive'],
       'all_plus10_pf':x['all_variants_stress_plus10_pf_ge_1p25'],
       'variants':{v:{'trades':d['n_trades'],
                     'net':d['stress_net_usd'],
                     'pf':d['stress_pf'],
                     'dd':d['stress_last_envelope_dd_usd']}
                   for v,d in x['comparison'].items()},
       'no_OOS':True},sort_keys=True))
