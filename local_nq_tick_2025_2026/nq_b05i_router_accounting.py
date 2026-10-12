#!/usr/bin/env python3
"""B05I SAFE-ARTIFACT-ONLY: attribution of H02 vs displaced T05; no ticks."""
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS

B='T05_377'
H='H02_PRINT_VWAP_MEAN_REVERSION'
R='T05_PRIORITY_H02_SHARED_ROUTER'
STRESS='stress_1p5_fee_2ticks_each_side'

def cents(x):
    n=round(float(x)*100)
    if abs(n/100-float(x))>.0001:raise ValueError('not exact cents')
    return n
def usd(c):return c/100

def decompose_month(a,h,r,o):
    if a['month']!=h['month'] or a['month']!=r['month'] or a['month']!=o['month']:
        raise ValueError('month mismatch')
    retained_n=r['trades']-o['n']
    displaced_n=a['trades']-retained_n
    if min(retained_n,displaced_n,o['n'],h['trades']-o['n'])<0:
        raise ValueError('negative trade counts')
    howner=cents(o['net'])
    t05retained=cents(r['net_usd'])-howner
    displaced=cents(a['net_usd'])-t05retained
    incr=howner-displaced
    if incr!=cents(r['net_usd'])-cents(a['net_usd']):
        raise AssertionError('monthly attribution identity')
    return {'month':a['month'],
      't05_original_trades':a['trades'],'t05_original_usd':a['net_usd'],
      't05_retained_trades':retained_n,'t05_retained_usd':usd(t05retained),
      't05_displaced_trades':displaced_n,'t05_displaced_usd':usd(displaced),
      'h02_standalone_trades':h['trades'],'h02_standalone_usd':h['net_usd'],
      'h02_router_trades':o['n'],'h02_router_usd':usd(howner),
      'h02_unexecuted_trades':h['trades']-o['n'],
      'router_trades':r['trades'],'router_usd':r['net_usd'],
      'router_increment_usd':usd(incr)}

def audit(x):
    if (x.get('status')!='B05H02_FINISHED_DEV_ONLY_NOT_OOS' or
        x.get('decision')!='B05H02_REJECT_DO_NOT_PROMOTE' or
        (x.get('source_days'),x.get('eligible_days'))!=(140,135) or
        x.get('source_months')!=list(MONTHS) or
        x.get('holdouts_opened') is not False or
        x.get('new_history_acquired') is not False or
        x.get('H02_uses_5s_signals') is not False or
        x.get('broker_fills_verified') is not False or
        x.get('funded_strategy_approved') is not False):
        raise ValueError('source not safe/frozen')
    m=x['models'];d=x['diagnostics']
    if set(m)!={B,H,R}:raise ValueError('model IDs differ')
    a=m[B][STRESS];h=m[H][STRESS];r=m[R][STRESS]
    if (a['trades'],cents(a['net_usd']),h['trades'],cents(h['net_usd']),
        r['trades'],cents(r['net_usd']),
        d['H02_executed_router'],cents(d['H02_stress_net_router']))!=(
        115,510250,75,-142750,166,219500,60,-253000):
        raise ValueError('frozen H02 output no longer matches source')
    rows=[]
    for i,month in enumerate(MONTHS):
        rows.append(decompose_month(a['monthly'][i],h['monthly'][i],r['monthly'][i],
                                   d['H02_monthly_executed'][i]))
        if rows[-1]['month']!=month:raise ValueError('source chronology changed')
    n=lambda key:sum(z[key] for z in rows)
    totals={
      'T05_original_usd':n('t05_original_usd'),
      'T05_retained_usd':n('t05_retained_usd'),
      'T05_displaced_usd':n('t05_displaced_usd'),
      'H02_router_usd':n('h02_router_usd'),
      'router_usd':n('router_usd'),
      'increment_usd':n('router_increment_usd'),
      'H02_router_trades':n('h02_router_trades'),
      'H02_unexecuted_trades':n('h02_unexecuted_trades'),
      'T05_retained_trades':n('t05_retained_trades'),
      'T05_displaced_trades':n('t05_displaced_trades'),
      'H02_router_negative_months':sum(z['h02_router_usd']<0 for z in rows)}
    target={'T05_original_usd':5102.5,'T05_retained_usd':4725.,
      'T05_displaced_usd':377.5,'H02_router_usd':-2530.,
      'router_usd':2195.,'increment_usd':-2907.5,'H02_router_trades':60,
      'H02_unexecuted_trades':15,'T05_retained_trades':106,
      'T05_displaced_trades':9,'H02_router_negative_months':6}
    for k,v in target.items():
        if abs(totals[k]-v)>.001:raise AssertionError('frozen source mismatch '+k)
    return {'status':'B05I_SAFE_ROUTER_ACCOUNTING_COMPLETE',
       'decision':'H02_REJECT_INCREMENTAL_RETURN_NEGATIVE',
       'source_kind':'PREEXISTING_B05H02_AGGREGATE_JSON_ONLY',
       'totals':totals,'monthly':rows,'new_hypotheses_tested':0,
       'history_acquired':False,'raw_ticks_accessed':False,
       'holdouts_opened':False,'broker_fills_verified':False,
       'posthoc_filter_adopted':False}

def report(r):
    t=r['totals']
    lines=['# B05I — Descomposición de contribución al router (artifact seguro únicamente)',
       '', '**Cero nuevas hipótesis, cero lectura de ticks y cero OOS.**',
       '', 'Ecuación: Δrouter = P&L H02 ejecutado − P&L T05 desplazado.',
       '',
       'T05 original: USD '+str(t['T05_original_usd'])+
       '; T05 retenida: USD '+str(t['T05_retained_usd'])+
       '; T05 desplazada (9): USD '+str(t['T05_displaced_usd'])+
       '; H02 en router (60): USD '+str(t['H02_router_usd'])+
       '; incremento del router: USD '+str(t['increment_usd'])+'.',
       '', '| Mes | H02 ejecutada en router USD | T05 desplazadas # / neto USD | Router − T05 USD | H02 sola USD |',
       '|---|---:|---:|---:|---:|']
    for x in r['monthly']:
        lines.append(f"| {x['month']} | {x['h02_router_usd']} | "
            f"{x['t05_displaced_trades']}/{x['t05_displaced_usd']} | "
            f"{x['router_increment_usd']} | {x['h02_standalone_usd']} |")
    lines+=['', '**Dictamen: H02 rechazada, 6 de 7 meses con contribución negativa en router.**',
       'La diferencia entre H02 standalone y H02 ejecutada en router es selección por',
       'cronología y capacidad de capital, NO una regla ex-ante para escoger el mejor mes.',
       'No filtrar meses, horas ni señales que salieron negativas en este mismo histórico.',
       'No construir otra familia sin un mecanismo genuinamente diferente, control de',
       'hipótesis adaptativas y riesgo en una sola cuenta. T05 tampoco está validada.',
       'No usar 5 segundos para señales nuevas, ni obtener más historia ni abrir OOS.',
       '']
    return '\n'.join(lines)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    x=audit(json.loads(a.source.read_text('utf8')))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n',encoding='utf8')
    a.report.write_text(report(x)+'\n',encoding='utf8')
    print('B05I_SAFE_AUDIT='+json.dumps({'status':x['status'],'totals':x['totals'],
       'decision':x['decision'],'raw_ticks_accessed':False},sort_keys=True))
