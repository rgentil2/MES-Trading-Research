#!/usr/bin/env python3
"""B05H02 fixed one-family 7-month DEV, exact frozen T05 and shared risk."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_t04_execution import SCENARIOS
from nq_b05_t11_aggregate import group
from nq_b05h02_reversion_month import BASE,NEW,ROUTER,MODELS,STRESS

FROZEN_T05={'baseline':(115,6220.,1725.),
    STRESS:(115,5102.5,1797.5),
    'stress_plus_10_usd_rt_FIXED_PATH_ONLY':(115,3952.5,1887.5)}

def aggregate(months):
    if set(months)!=set(MONTHS):raise ValueError('all seven DEV months required')
    for m in MONTHS:
        x=months[m]
        if (x['month']!=m or x['status']!='B05H02_DEV_EXPLORATORY_ONLY'
            or x['holdouts_opened'] is not False
            or x['new_data_acquired'] is not False
            or x['H02_used_fixed_5s_signals'] is not False
            or x['legacy_T05_baseline_unchanged'] is not True
            or x['broker_fills_verified'] is not False
            or x['trade_level_exported'] is not False
            or x['source_days']!=x['eligible_days']+x['excluded_days']
            or set(x['models'])!=set(MODELS)):
            raise ValueError('untrusted or unsafe monthly source '+m)
    total=sum(months[m]['source_days'] for m in MONTHS)
    eligible=sum(months[m]['eligible_days'] for m in MONTHS)
    if (total,eligible)!=(140,135):raise AssertionError('source mismatch 140/135')
    out={}
    for model in MODELS:
        out[model]={}
        for sc in SCENARIOS:
            out[model][sc]=group(months,model,sc)
            if sc==STRESS:
                out[model]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']=group(
                    months,model,sc,extra=True)
    for sc,(n,net,dd) in FROZEN_T05.items():
        rec=out[BASE][sc]
        if (rec['trades']!=n or abs(rec['net_usd']-net)>.01
            or abs(rec['last_envelope_dd_usd']-dd)>.01):
            raise AssertionError('FROZEN T05 BASELINE PARITY FAILED '+sc)
    r=out[ROUTER][STRESS]
    re=out[ROUTER]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
    b=out[BASE][STRESS]
    be=out[BASE]['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
    h02=r['owner_attribution'].get(NEW,{'trades':0,'net_usd':0.})
    retained=r['owner_attribution'].get(BASE,{'trades':0})['trades']
    if (sum(c['trades'] for c in r['owner_attribution'].values())!=r['trades']
        or abs(sum(c['net_usd'] for c in r['owner_attribution'].values())-r['net_usd'])>.01):
        raise AssertionError('shared-router attribution invalid')
    gates={
      'router_plus10_incremental_net_positive':re['net_usd']>be['net_usd'],
      'router_stress_pf_ge_1p25':r['pf'] is not None and r['pf']>=1.25,
      'router_plus10_pf_ge_1p25':re['pf'] is not None and re['pf']>=1.25,
      'router_Last_DD_below_2000_UNVERIFIED':r['last_envelope_dd_usd']<2000.,
      'H02_executed_and_attributed_stress_positive':
          h02['trades']>0 and h02['net_usd']>0.,
      'T05_retention_ge_104':retained>=104,
      'router_min_5_trades_each_month':all(x['trades']>=5 for x in r['monthly']),
    }
    diag={
       'H02_opportunities':sum(months[m]['signal_diagnostics'].get('h02_opportunities',0) for m in MONTHS),
       'H02_executed_router':h02['trades'],
       'H02_stress_net_router':h02['net_usd'],
       'T05_retained_router':retained,
       'router_minus_T05_stress_usd':round(r['net_usd']-b['net_usd'],2),
       'router_minus_T05_extra10_usd':round(re['net_usd']-be['net_usd'],2),
       'H02_months_w_execution':sum(months[m]['models'][ROUTER][STRESS]['owner_attribution'].get(NEW,{}).get('trades',0)>0 for m in MONTHS),
       'H02_monthly_executed':[{
         'month':m,
         'n':months[m]['models'][ROUTER][STRESS]['owner_attribution'].get(NEW,{}).get('trades',0),
         'net':months[m]['models'][ROUTER][STRESS]['owner_attribution'].get(NEW,{}).get('net_usd',0.)
         } for m in MONTHS],
    }
    return {
       'status':'B05H02_FINISHED_DEV_ONLY_NOT_OOS',
       'decision':'B05H02_PRELIMINARY_DEV_PASS_NOT_LIVE'
             if all(gates.values()) else 'B05H02_REJECT_DO_NOT_PROMOTE',
       'source_months':list(MONTHS),
       'source_days':total,'eligible_days':eligible,
       'models':out,'gates':gates,'diagnostics':diag,
       'hypotheses_evaluated':1,'broker_fills_verified':False,
       'holdouts_opened':False,'new_history_acquired':False,
       'H02_uses_5s_signals':False,'funded_strategy_approved':False,
    }

def report(x):
    lines=['# B05H02 — Reversión por 377 transacciones Last, VWAP 4181/10946',
       '',
       '**Una hipótesis económica registrada antes de resultados. No señales 5 segundos nuevas.**',
       '**Los siete meses fueron usados adaptativamente: NO OOS, NO fills broker, NO cuenta aprobada.**',
       '',
       f"Fuente {x['source_days']} sesiones, {x['eligible_days']} elegibles. Decisión **{x['decision']}**.",
       '',
       '| Modelo | Trades | Neto base USD | Neto estrés USD | PF estrés | DD Last estrés USD | Neto estrés+$10 USD | PF estrés+$10 |',
       '|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in MODELS:
        z=x['models'][m];a=z['baseline'];b=z[STRESS];ex=z['stress_plus_10_usd_rt_FIXED_PATH_ONLY']
        lines.append(f"| {m} | {b['trades']} | {a['net_usd']} | {b['net_usd']} | {b['pf']} | {b['last_envelope_dd_usd']} | {ex['net_usd']} | {ex['pf']} |")
    d=x['diagnostics']
    lines+=['','## Incremento real en la misma cuenta',
       '',
       f"- Oportunidades H02: **{d['H02_opportunities']}**; ejecuciones H02 dentro del router: **{d['H02_executed_router']}**.",
       f"- H02 aporte neto estrés: **USD {d['H02_stress_net_router']}**; T05 conservadas **{d['T05_retained_router']}/115**.",
       f"- Router − T05 bajo estrés: **USD {d['router_minus_T05_stress_usd']}**.",
       f"- Router − T05 estrés+$10 RT sobre ruta fija: **USD {d['router_minus_T05_extra10_usd']}**.",
       '',
       '## Gates prerregistrados']
    for k,v in x['gates'].items():
        lines.append(f"- {k}: **{'PASS' if v else 'FAIL'}**")
    lines+=['','## Todos los meses DEV: escenarios de costes estrés',
      '',
      '| Mes | T05 trades/net | H02 trades/net | Router trades/net | H02 ejecutadas en router/net |',
      '|---|---|---|---|---|']
    a=x['models'][BASE][STRESS]['monthly']
    b=x['models'][NEW][STRESS]['monthly']
    c=x['models'][ROUTER][STRESS]['monthly']
    d=x['diagnostics']['H02_monthly_executed']
    for i,m in enumerate(MONTHS):
        lines.append(f"| {m} | {a[i]['trades']}/{a[i]['net_usd']} | "
             f"{b[i]['trades']}/{b[i]['net_usd']} | "
             f"{c[i]['trades']}/{c[i]['net_usd']} | "
             f"{d[i]['n']}/{d[i]['net']} |")
    lines+=['','## Límites',
      '',
      '- H02 usa SOLO barras por prints de 377 y contextos 4181/10946, sin tiempo fijo de señales.',
      '- T05 usa su detector de cinco segundos **histórico y congelado solo como benchmark**.',
      '- Los mismos 135 días elegibles preservan muestra T05 aunque H02 no dependa de opening range.',
      '- Entry-timestamp stop ambiguity FAIL CLOSED. Si se encuentra, este informe no se genera como rentabilidad válida.',
      '- +USD10 RT sobre mismas rutas es análisis de costes contable; no recalcula stops ni riesgo diario.',
      '- Cuatro meses ambiguos de H01 siguen documentados; este nuevo modelo no los reescribe.',
      '- La fuente Last no certifica precio ejecutable, Bid/Ask secuenciadas, L2 o reglas de fondeo.',
      '- La DD objetivo de $2000 es ilustrativa y NO equivale a límite contractual verificable.',
      '- No convertir variantes futuras elegidas con esta DEV en evidencia independiente. Sin abrir períodos sellados.',
      '']
    return '\n'.join(lines)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    months={}
    for f in a.inputs.rglob('nq_b05h02_*.json'):
        v=json.loads(f.read_text(encoding='utf8'))
        if v['month'] in months:raise ValueError('duplicate month')
        months[v['month']]=v
    r=aggregate(months)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n',encoding='utf8')
    a.report.write_text(report(r)+'\n',encoding='utf8')
    print('B05H02_AGGREGATE_SAFE='+json.dumps({
        'status':r['status'],'decision':r['decision'],
        'source':r['source_days'],'eligible':r['eligible_days'],
        'models':{m:{s:{k:v[s][k] for k in ('trades','net_usd','pf','last_envelope_dd_usd')}
             for s in ('baseline',STRESS,'stress_plus_10_usd_rt_FIXED_PATH_ONLY')}
             for m,v in r['models'].items()},
        'gates':r['gates'],'diagnostics':r['diagnostics'],
        'oos_opened':False,'no_new_history':True},sort_keys=True))
