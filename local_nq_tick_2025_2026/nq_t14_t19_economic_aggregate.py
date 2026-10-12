#!/usr/bin/env python3
"""Pre-registered 6-mechanism evaluation: four economic, two magnitude-only.

Reconciles private 135 DEV daily sessions, outputs AGGREGATE data only.
No daily PnL, trade timestamps, ticks or licensed source go to artifacts.
"""
from __future__ import annotations
import argparse,json,math,statistics
from pathlib import Path
from collections import Counter
from nq_tick_short_horizon_month import MONTHS
from nq_t14_t16_signal_feasibility import IDS as FIRST
from nq_t17_t19_signal_feasibility import IDS as SECOND
from nq_t14_t19_economic_and_magnitude import (
  BASE,DIRECTIONAL,MAGNITUDE,ROUTERS,MODELS,STRESS,EXTRA,EXPECTED)
from nq_b03_aggregate import stitch
from nq_b05k_t05_daily_block_bootstrap import moving_block_stats,SEED

SCENARIOS=('stress','stress_plus10_fixed_path')
SAMPLE_MONTHS=7
DAYS=135
REPS=10000

def cents(v):
    if not isinstance(v,(int,float)) or not math.isfinite(v):
        raise ValueError('invalid money')
    c=round(v*100)
    if abs(v-c/100)>.0001:raise ValueError('money not cents')
    return c

def bh(p):
    n=len(p)
    if n!=4:raise ValueError('The FOUR predeclared economic hypotheses required')
    a=sorted(p,key=p.get)
    q={}
    v=1.
    for i in range(n-1,-1,-1):
        v=min(v,p[a[i]]*n/(i+1))
        q[a[i]]=round(v,6)
    return q

def aggregate(months):
    if set(months)!=set(MONTHS):raise ValueError('exact months required')
    source=0;eligible=0;diary=[]
    for m in MONTHS:
        z=months[m]
        s=z['safe']
        if (s['status']!='T14_T19_ECONOMIC_DEV_ONLY'
          or s['month']!=m
          or s['holdouts_opened'] is not False
          or s['new_data_acquired'] is not False
          or s['broker_fills_verified'] is not False
          or s['trade_level_exported'] is not False
          or s['new_five_second_signals'] is not False
          or set(s['models'])!=set(MODELS)
          or set(s['magnitude'])!=set(MAGNITUDE)
          or s['source_days']!=s['eligible_days']+s['excluded_days']
          or len(z['private_daily'])!=s['source_days']):
            raise ValueError('untrusted or incomplete month')
        source+=s['source_days'];eligible+=s['eligible_days']
        for d in z['private_daily']:
            if d['day'][:7]!=m:raise ValueError('mismatched private date month')
            if d['eligible']:
                if set(d['models'])!=set(MODELS):raise ValueError('daily model missing')
                for key in MODELS:
                    x=d['models'][key]
                    if (x['trades'] not in (0,1,2) or
                        x['extra_cents']!=x['stress_cents']-1000*x['trades']):
                        raise AssertionError('corrupt private daily path')
                diary.append(d)
            elif set(d)!=set(['day','eligible']):
                raise ValueError('excluded day outcome leakage')
        if (s['models'][BASE]['trades'],
            s['models'][BASE]['net_usd'])!=EXPECTED[m]:
            raise ValueError('T05 monthly count/net benchmark changed')
    if (source,eligible,len(diary))!=(140,135,135):
        raise ValueError('frozen coverage 140/135')
    if [z['day'] for z in diary]!=sorted(z['day'] for z in diary):
        raise ValueError('daily chronology')
    table={};daily_cache={};summary_months={}
    for model in MODELS:
        a=[months[m]['safe']['models'][model] for m in MONTHS]
        n=sum(z['trades'] for z in a)
        pos=sum(cents(z['positive_usd']) for z in a)
        neg=sum(cents(z['negative_usd']) for z in a)
        net=sum(cents(z['net_usd']) for z in a)
        if net!=pos-neg:raise AssertionError('NET gross inconsistent')
        if sum(d['models'][model]['trades'] for d in diary)!=n:
            raise AssertionError('daily n mismatch')
        if sum(d['models'][model]['stress_cents'] for d in diary)!=net:
            raise AssertionError('daily net mismatch')
        rows=[{'frozen_path_adjusted_net_usd':z['net_usd'],
               'gross_positive_net_usd':z['positive_usd'],
               'gross_negative_net_usd':z['negative_usd'],
               'trades':z['trades'],
               'last_envelope_segment':z['last_envelope_segment']}
              for z in a]
        dd=stitch(rows)['last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH']
        epos=sum(cents(z['extra10']['positive_usd']) for z in a)
        eneg=sum(cents(z['extra10']['negative_usd']) for z in a)
        enet=sum(cents(z['extra10']['net_usd']) for z in a)
        if enet!=net-1000*n or enet!=epos-eneg:raise AssertionError('extra cost parity')
        daily_cache[model]={
          'stress':[d['models'][model]['stress_cents']/100 for d in diary],
          'extra':[d['models'][model]['extra_cents']/100 for d in diary]}
        owners=Counter()
        attribution={}
        for z in a:
            for owner,entry in z['owner_attribution'].items():
                e=attribution.setdefault(owner,{'trades':0,'net_usd':0.})
                e['trades']+=entry['trades'];e['net_usd']+=entry['net_usd']
        if sum(z['trades'] for z in attribution.values())!=n or abs(
            sum(z['net_usd'] for z in attribution.values())-net/100)>.02:
            raise ValueError('router attribution fails')
        months_n=[z['trades'] for z in a]
        months_net=[z['net_usd'] for z in a]
        table[model]={
            'N_trades':n,'N_days_active':sum(d['models'][model]['trades']>0 for d in diary),
            'stress_net_usd':net/100,
            'stress_pf':round(pos/neg,5) if neg else None,
            'stress_last_dd_usd':dd,
            'extra10_fixed_path_net_usd':enet/100,
            'extra10_pf':round(epos/eneg,5) if eneg else None,
            'stress_monthly_n':months_n,'stress_monthly_net':months_net,
            'months_with_5_trades':sum(v>=5 for v in months_n),
            'months_profitable':sum(v>0 for v in months_net),
            'owner_attribution':attribution,
            'LOMO_range_net_usd':[round((net-max(cents(v) for v in months_net))/100,2),
                round((net-min(cents(v) for v in months_net))/100,2)],
            'bootstrap':{}}
    if (table[BASE]['N_trades'],table[BASE]['stress_net_usd'],
      table[BASE]['extra10_fixed_path_net_usd'],
      table[BASE]['stress_last_dd_usd'])!=(115,5102.5,3952.5,1797.5):
        raise AssertionError('T05 FROZEN global parity fail')
    if table[FIRST[2]]['N_trades']!=0:raise AssertionError('T16 prereg 0 signals changed')
    for model in (BASE,*DIRECTIONAL):
        for label in SCENARIOS:
            arr=daily_cache[model]['stress' if label=='stress' else 'extra']
            table[model]['bootstrap'][label]={
               str(L):moving_block_stats(arr,L,seed=20261012+L+len(model),reps=REPS)
               for L in (3,5,10)}
    comparison={}
    for new,router in ROUTERS.items():
        comp={'new_id':new,'router':router}
        for key,label in [('stress','stress'),('extra','extra10_fixed_path')]:
            a=daily_cache[router][key];b=daily_cache[BASE][key]
            delta=[round(x-y,2) for x,y in zip(a,b)]
            aggregate_delta=round(sum(delta),2)
            if abs(aggregate_delta-(table[router][
                  'stress_net_usd' if key=='stress' else 'extra10_fixed_path_net_usd'
                  ]-table[BASE]['stress_net_usd' if key=='stress' else 'extra10_fixed_path_net_usd']))>.011:
                raise AssertionError('paired delta mismatch')
            comp[label]={
                'net_usd':aggregate_delta,
                'N_months_positive':sum(
                   months[m]['safe']['models'][router]['net_usd']>
                   months[m]['safe']['models'][BASE]['net_usd'] for m in MONTHS),
                'bootstrap':{
                  str(L):moving_block_stats(delta,L,seed=20261012+L+len(router),reps=REPS)
                  for L in (3,5,10)}}
        comparison[new]=comp
    p={k:table[k]['bootstrap']['extra10_fixed_path']['5']['p_one_sided_centered_null_approx']
       if table[k]['N_trades'] else 1. for k in DIRECTIONAL}
    q=bh(p)
    for k in DIRECTIONAL:
        m=table[k]
        ce=comparison[k]['extra10_fixed_path']
        lower=m['bootstrap']['extra10_fixed_path']['5']['ci90_mean_daily_usd'][0]
        if not m['N_trades']:
            economic_status='NO_SIGNALS'
        else:
            gates={
             'N_min_5_per_month':all(x>=5 for x in m['stress_monthly_n']),
             'net_extra10_positive':m['extra10_fixed_path_net_usd']>0,
             'pf_stress_ge_1p25':m['stress_pf'] is not None and m['stress_pf']>=1.25,
             'pf_extra10_ge_1p25':m['extra10_pf'] is not None and m['extra10_pf']>=1.25,
             'DD_last_stress_lt_2000_UNVERIFIED':m['stress_last_dd_usd']<2000,
             'router_extra10_delta_positive':ce['net_usd']>0,
             'CI90_extra10_lower_positive_L5':lower>0}
            economic_status='RESEARCH_ONLY_GATES_PASS' if all(gates.values()) else 'REJECT_IN_SAMPLE_ECONOMIC_GATE'
            m['gates']=gates
        m['descriptive_bh_q_from_prior_adaptive_dev']=q[k]
        m['decision']=economic_status
    magnitude={}
    for k in MAGNITUDE:
        vals=[months[m]['safe']['magnitude'][k] for m in MONTHS]
        n=sum(v['N_signal_and_future_endpoint'] for v in vals)
        total=sum(v['range_ticks_sum'] for v in vals)
        if n!=135:raise ValueError('Missing signal endpoint or non-universal pattern')
        magnitude[k]={
          'N_days_with_signal_and_future15min_range':n,
          'average_future_15min_high_low_range_price_ticks':round(total/n,4),
          'N_without_signal':0,'difference_vs_no_signal':None,
          'difference_CI90':None,'predictive_p':None,'q_BH':None,
          'economic_PF':None,'economic_profit':None,
          'status':'UNIDENTIFIABLE_NO_NON_EVENT_GROUP_ALL_135_DAYS_SIGNAL'}
    return {'status':'T14_T19_EXPLORATORY_DEV_ECONOMIC_AND_MAGNITUDE_COMPLETE',
      'source_days':source,'eligible_days':eligible,'hypotheses':table,
      'router_incremental':comparison,'magnitude':magnitude,
      'N_economic_hypotheses_in_family':4,'N_magnitude_questions':2,
      'q_BH_is_postselected_descriptive_only':True,
      'q_Holm_confirmatory':None,'N_effective_independent':None,
      'broker_fills_verified':False,'holdouts_opened':False,
      'new_data_acquired':False,'daily_series_exported':False,
      'no_new_5second_signals':True}

def report(x):
    lines=['# T14–T19 — Seis preguntas medidas con NQ DEV sin datos nuevos',
      '', '**SIMULACIÓN Last no es ejecución broker ni resultado validado.**',
      '135 sesiones elegibles, siete meses, una cuenta 1NQ con max 2 operaciones/día.',
      'Cuatro direccionales con SL32ticks, TP48, 300s y costes estrés $7.50',
      'más 2 ticks/lado, sensibilidad extra $10RT. T17/T19 solo MAGNITUD.',
      '',
      '| Hipótesis | N trades | Neto estrés USD | PF estrés | DD Last USD | Neto +$10 RT USD | PF extra | IC90 extra USD/sesión L5 | q BH descriptiva | Δ router+$10 USD | Estado |',
      '|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|']
    for k in DIRECTIONAL:
        z=x['hypotheses'][k]
        ci=z.get('bootstrap',{}).get('extra10_fixed_path',{}).get('5',{}).get('ci90_mean_daily_usd')
        lines.append(f"| {k} | {z['N_trades']} | {z['stress_net_usd']} | {z['stress_pf']} | {z['stress_last_dd_usd']} | "
          f"{z['extra10_fixed_path_net_usd']} | {z['extra10_pf']} | {ci or 'N/D'} | "
          f"{z['descriptive_bh_q_from_prior_adaptive_dev']} | "
          f"{x['router_incremental'][k]['extra10_fixed_path']['net_usd']} | {z['decision']} |")
    lines+=['','## Preguntas de magnitud, NO operaciones',
      '| ID | N sesiones evento | Rango máximo−mínimo futuro 15m promedio (ticks NQ) | Días sin evento | IC90 diferencia vs no-evento | ¿Predicción identificable? |',
      '|---|---:|---:|---:|---|---|']
    for k,z in x['magnitude'].items():
        lines.append(f"| {k} | {z['N_days_with_signal_and_future15min_range']} | "
          f"{z['average_future_15min_high_low_range_price_ticks']} | 0 | **N/D** | **NO, señal en todos 135 días** |")
    lines+=['','## Interpretación crítica',
      '',
      '- **T16 cero señales**, no alterar umbrales para generar P&L ficticio.',
      '- **T17/T19 135/135 eventos**: no hay días control sin evento; media futura es DESCRIPTIVA, no existe efecto predictivo causal vs no-evento, q N/D.',
      '- q BH T14/T15/T16/T18 es DESCRIPTIVA del bootstrap postselección en DEV; NO confirmación.',
      '- Todas las rutas T05 y combinadas son UNA cuenta bajo solapamiento y stop diario; nunca sumar standalone.',
      '- IC90 diario incluye días sin trade y bootstrap por bloques L5 principal, L3/L10 sensibilidad.',
      '- El $10 adicional es contabilidad sobre ruta fija y no mueve entrada/salida ni stop diario.',
      '- Fills Last simulados, DD de envolvente Last, ni trailing real de fondeo ni HOLM/OOS verificados.',
      '- No se reoptimizaron parámetros, ni se abrieron periodos sellados o descargaron datos nuevos.',
      '']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--private',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    months={}
    for m in MONTHS:
        months[m]=json.loads((a.private/f't14_t19_{m}.json').read_text())
    result=aggregate(months)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    a.report.write_text(report(result)+'\n')
    print('T14_T19_ECONOMIC_AGGREGATE_SAFE='+json.dumps({
      'source':result['source_days'],'eligible':result['eligible_days'],
      'hypotheses':{k:{'N':result['hypotheses'][k]['N_trades'],
        'net_stress':result['hypotheses'][k]['stress_net_usd'],
        'extra_net':result['hypotheses'][k]['extra10_fixed_path_net_usd'],
        'decision':result['hypotheses'][k]['decision']} for k in DIRECTIONAL},
      'magnitude_n':{k:v['N_days_with_signal_and_future15min_range']
         for k,v in result['magnitude'].items()},'oos':False},sort_keys=True))
