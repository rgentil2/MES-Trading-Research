#!/usr/bin/env python3
"""B05K daily P&L inference for FROZEN legacy T05 from seven existing DEV months.

Mode month: temporarily produce PRIVATE per-date returns within same GitHub runner.
Mode aggregate: read PRIVATE results, strict frozen T05 parity, then publish
AGGREGATED inference only. Never upload/reveal private per-date series.
NO alpha variation or new market source. Dates strictly guarded before read.
"""
from __future__ import annotations
import argparse,json,math,random,statistics
from datetime import date
from pathlib import Path
from collections import Counter
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_tick_short_horizon import dev_day
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_b05h01_trade_expansion_month import frozen_t05, BASE, STRESS
from nq_b05h02_reversion_month import risk_trace
from nq_t08_risk_audit import Envelope

B=10000
SEED=20261011
SIZES=(3,5,10)
CORE=5
NET_CENTS=510250
NET_EXTRA_CENTS=395250
MONTH_EXPECTATIONS={
 '2025-10':(15,13750),'2025-11':(8,76000),'2025-12':(22,145000),
 '2026-01':(19,157250),'2026-02':(13,-82750),
 '2026-03':(21,137250),'2026-04':(17,63750)}
ELIGIBLE_DAYS=135
SOURCE_DAYS=140

def cents(x):
    if not isinstance(x,(int,float)) or not math.isfinite(x):
        raise ValueError('invalid money')
    out=round(float(x)*100)
    if abs(out/100-x)>0.00001:raise ValueError('money not a whole cent')
    return int(out)
def money(c):return round(c/100,2)

def frozen_t05_day(day,events):
    """Never modify T05 signals/rules, prices or original risk model."""
    dev_day(day)
    status,old_bars,signals=frozen_t05(events,day)
    if status!='READY':
        if status not in ('SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE'):
            raise ValueError('unknown QC status')
        return {'day':day,'ready':False}
    envelope=Envelope()
    extra_envelope=Envelope()
    owner,extra,skips=risk_trace(day,events,old_bars,signals,STRESS,
                                  envelope,extra_envelope)
    rec=owner.get(BASE,{})
    ext=extra.get(BASE,{})
    n=rec.get('trades',0)
    pnl=rec.get('net_cents',0)
    epnl=ext.get('net_cents',0)
    if (ext.get('trades',0)!=n or epnl != pnl-1000*n
         or cents(envelope.equity)!=pnl or cents(extra_envelope.equity)!=epnl):
        raise AssertionError('Day frozen-path surcharge/equity mismatch')
    return {'day':day,'ready':True,'trades':n,
            'stress_cents':pnl,'stress_extra_cents':epnl}

def month_stage(root:Path,month:str,private_out:Path):
    if month not in MONTHS:
        raise ValueError('B05K SEALED MONTH DENIED BEFORE FILE ACCESS')
    days=sorted(month_days(root,month))
    results=[]
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        results.append(frozen_t05_day(day,events))
    eligible=[d for d in results if d['ready']]
    # Individual months may have zero excluded days; enforce 140/135 on aggregation.
    if (sum(d['trades'] for d in eligible),
        sum(d['stress_cents'] for d in eligible))!=MONTH_EXPECTATIONS[month]:
        raise AssertionError('T05 month parity FAIL: no financial/statistical results')
    if sum(d['stress_extra_cents'] for d in eligible)!=(MONTH_EXPECTATIONS[month][1]-1000*MONTH_EXPECTATIONS[month][0]):
        raise AssertionError('T05 fixed-path extra cost mismatch')
    private_out.parent.mkdir(parents=True,exist_ok=True)
    if private_out.exists():raise ValueError('No replacing existing derived results')
    private_out.write_text(json.dumps({'month':month,'source':len(results),
       'eligible':len(eligible),'days':results,
       'holdout_read':False,'new_history_acquired':False},separators=(',',':'))+'\n')
    return {'month':month,'source':len(results),'eligible':len(eligible),
       'trades':sum(d['trades'] for d in eligible),
       'net_stress_usd':money(sum(d['stress_cents'] for d in eligible)),
       'daily_vectors_publicly_exported':False}

def quantile(sorted_x,q):
    if not sorted_x or not 0<=q<=1:raise ValueError('bad quantile')
    z=(len(sorted_x)-1)*q
    lo=int(z);hi=math.ceil(z)
    return sorted_x[lo]+(sorted_x[hi]-sorted_x[lo])*(z-lo)

def moving_block_stats(values,length,seed=SEED,reps=B):
    """Non-circular overlapping moving block bootstrap, n-length resamples.

    Primary L=5, sensitivity L=3 and L=10. No iid resampling.
    Null approximation: centered block-bootstrap distribution, one-sided.
    """
    v=[float(x) for x in values]
    n=len(v)
    if n<20 or length<2 or length>n or reps<100:
        raise ValueError('inadequate daily vector or block config')
    if any(not math.isfinite(x) for x in v):raise ValueError('nonfinite daily')
    obs=sum(v)/n
    rng=random.Random(seed)
    samples=[]
    limit=n-length
    for _ in range(reps):
        remaining=n
        total=0.
        while remaining>0:
            begin=rng.randrange(limit+1)
            take=min(length,remaining)
            total+=sum(v[begin:begin+take])
            remaining-=take
        samples.append(total/n)
    samples.sort()
    low,high=quantile(samples,.05),quantile(samples,.95)
    sdev=statistics.stdev(samples)
    # P_H0 centered basic bootstrap; do not call an exact valid selective p.
    p=(1+sum((m-obs)>=obs for m in samples))/(reps+1)
    mde=(1.2815515655446004+.8416212335729143)*sdev
    return {'length_sessions':length,'resamples':reps,'seed':seed,
       'mean_daily_usd':round(obs,4),
       'ci90_mean_daily_usd':[round(low,4),round(high,4)],
       'bootstrap_se_daily_usd':round(sdev,4),
       'ci90_width_usd':round(high-low,4),
       'p_one_sided_centered_null_approx':round(p,6),
       'p_is_confirmatory':False,
       'mde_approx_usd_per_session_80pct_power_one_sided_alpha_10pct':round(mde,4),
       'mde_is_not_a_power_guarantee':True}

def calculate(rows):
    """All seven months, complete dates used PRIVATE then discarded from report."""
    if set(rows)!=set(MONTHS):raise ValueError('All 7 months needed')
    timeline=[]
    all_source=0
    for m in MONTHS:
        obj=rows[m]
        if (obj.get('month')!=m or obj.get('holdout_read') is not False or
            obj.get('new_history_acquired') is not False or
            obj['source']!=len(obj['days']) or
            obj['eligible'] != sum(d['ready'] for d in obj['days'])):
            raise ValueError('unsafe or inconsistent month')
        if len(set(d['day'] for d in obj['days']))!=len(obj['days']):
            raise ValueError('duplicate days')
        if [d['day'] for d in obj['days']]!=sorted(d['day'] for d in obj['days']):
            raise ValueError('unsorted month')
        for d in obj['days']:
            dev_day(d['day'])
            if d['day'][:7]!=m:raise ValueError('mixed month')
            if d['ready']:
                if (d['stress_extra_cents'] != d['stress_cents']-1000*d['trades'] or
                    d['trades'] not in (0,1,2)):
                    raise ValueError('corrupted daily pnl/trade gate')
                timeline.append(d)
            elif set(d)!=set(('day','ready')):
                raise ValueError('ineligible day falsely assigned outcome')
        a=MONTH_EXPECTATIONS[m]
        eligible=[d for d in obj['days'] if d['ready']]
        if (sum(d['trades'] for d in eligible),
            sum(d['stress_cents'] for d in eligible))!=a:
            raise ValueError('monthly locked T05 totals invalid')
        all_source+=obj['source']
    if all_source!=SOURCE_DAYS or len(timeline)!=ELIGIBLE_DAYS:
        raise ValueError('frozen T05 coverage 140/135 FAIL')
    if [d['day'] for d in timeline]!=sorted(d['day'] for d in timeline):
        raise ValueError('crossmonth chronological order invalid')
    ntr=sum(d['trades'] for d in timeline)
    v=[money(d['stress_cents']) for d in timeline]
    extra=[money(d['stress_extra_cents']) for d in timeline]
    if (ntr,sum(d['stress_cents'] for d in timeline),
        sum(d['stress_extra_cents'] for d in timeline))!=(115,NET_CENTS,NET_EXTRA_CENTS):
        raise AssertionError('frozen T05 exact global count/PnL parity fail')
    def summary(values,label):
        stats={str(L):moving_block_stats(values,L,seed=SEED+L,reps=B)
               for L in SIZES}
        if any(z['ci90_width_usd']<0 for z in stats.values()):
            raise AssertionError('bad CI width')
        return {'scenario':label,'total_usd':round(sum(values),2),
           'mean_daily_usd':round(statistics.mean(values),4),
           'median_daily_usd':round(statistics.median(values),4),
           'n_positive_days':sum(x>0 for x in values),
           'n_negative_days':sum(x<0 for x in values),
           'n_zero_net_days':sum(x==0 for x in values),
           'n_sessions':len(values),'blocks':stats,
           'ci90_per_trade_computed':False,'q_BH':None,'holm':None,
           'status':'DEPENDENCE_AWARE_IN_SAMPLE_EXPLORATORY_ONLY'}
    active=sum(d['trades']>0 for d in timeline)
    month_net={m:sum(d['stress_cents'] for d in timeline if d['day'][:7]==m) for m in MONTHS}
    lom=[NET_CENTS-month_net[m] for m in MONTHS]
    aggregate={
      'status':'B05K_DAILY_BLOCK_DIAGNOSTIC_COMPLETE_IN_SAMPLE_ONLY',
      'source_kind':'SAME_SEVEN_EXISTING_NQ_LAST_RELEASES_FROZEN_T05',
      'n_source_days':all_source,'n_eligible_sessions':len(timeline),
      'n_active_sessions':active,'n_trades':ntr,
      'n_months':7,'n_effective_independent_events':None,
      'n_calendar_weeks_observed':len(set(date.fromisoformat(d['day']).isocalendar()[:2] for d in timeline)),
      'scenarios':{'stress':summary(v,'stress_original_T05'),'stress_extra10_fixed_path':summary(extra,'stress_plus10_fixed_path')},
      'monthly_positive_count':sum(x>0 for x in month_net.values()),
      'leave_one_month_out_total_range_usd':[money(min(lom)),money(max(lom))],
      'gate1_statistical_confirmed':False,
      'multitesting_family_q_calculated':False,
      'model_parameters_changed':False,
      'out_of_sample_read':False,'new_history_acquired':False,
      'daily_outcomes_publicly_exported':False,
      'broker_fills_verified':False,
      'funded_strategy_approved':False}
    return aggregate

def write_report(z):
    lines=['# B05K T05 — 135 sesiones, IC90 y p exploratorio por bootstrap de bloques móviles',
      '',
      '**RECONSTRUCCIÓN DE T05 ORIGINAL, SIN NUEVA HIPÓTESIS. NO OOS / NO FONDEO.**',
      'Un solo escenario de riesgo y trayectoria histórica congelados. Los datos P&L por',
      'fecha únicamente existieron en el runner; NO se publican series diarias/ticks ni',
      'se permite reinterpretar el p-value como prueba selectiva independiente.',
      '',
      f"Sesiones fuente={z['n_source_days']}; elegibles={z['n_eligible_sessions']}; días con trade={z['n_active_sessions']}; N trades={z['n_trades']}; semanas observadas={z['n_calendar_weeks_observed']}; N independiente efectivo=N/D.",
      '',
      '| Escenario | Neto 7m USD | Media USD/sesión | L (sesiones) | IC90 USD/sesión | p unilateral exploratorio H0≤0 | SE USD/sesión | MDE aprox USD/sesión |',
      '|---|---:|---:|---:|---|---:|---:|---:|']
    for key in ['stress','stress_extra10_fixed_path']:
        sc=z['scenarios'][key]
        for L in ('3','5','10'):
            b=sc['blocks'][L]
            lines.append(f"| {key} | {sc['total_usd']:.2f} | {sc['mean_daily_usd']:.3f} | {L} | "
               f"[{b['ci90_mean_daily_usd'][0]:.3f}, {b['ci90_mean_daily_usd'][1]:.3f}] | "
               f"{b['p_one_sided_centered_null_approx']:.4f} | {b['bootstrap_se_daily_usd']:.3f} | "
               f"{b['mde_approx_usd_per_session_80pct_power_one_sided_alpha_10pct']:.3f} |")
    lines+=['','### Contexto y límites',
      '',
      f"- Positivos {z['scenarios']['stress']['n_positive_days']}, negativos {z['scenarios']['stress']['n_negative_days']}, neto cero {z['scenarios']['stress']['n_zero_net_days']} sobre 135 sesiones. Meses positivos {z['monthly_positive_count']}/7.",
      f"- LOMO excluyendo un mes completo, neto estrés [USD {z['leave_one_month_out_total_range_usd'][0]}, USD {z['leave_one_month_out_total_range_usd'][1]}] sobre seis meses; NO se descarta ningún mes realmente.",
      '- El p bootstrap usa distribución centrada en la media observada, válida solo como aproximación exploratoria bajo H0 y estacionariedad de bloques, no p postselección válido de la familia histórica.',
      '- Bootstrap NO CIRCULAR, 10,000 muestras, L=5 principal, L=3 y L=10 sensibilidad sin elegir la más favorable.',
      '- MDE normal aproximado para alpha unilateral .10, 80% potencia, escala por sesión; no una garantía de poder real en esta muestra.',
      '- N=135 sesiones no representa N_independiente=135; Ntrades=115 tampoco.',
      '- Resultados originales T05: +$5102,50 estrés y +$3952,50 estrés+$10, PF estrés+$10 1,23717<1,25. DD bajo reordenamiento de eventos intratimestamp hasta $2462,50 y riesgo de fills sin confirmar.',
      '- NO calculamos q BH, Holm ni confirmación por cinco años. No abrir los holdouts ni operar/fondeo.',
      '- Análisis repetido sobre DEV previamente seleccionado: aunque IC90 excluya 0 bajo algún bloque, SOLO IN_SAMPLE_DEPENDENCE_DIAGNOSTIC.',
      '']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--mode',required=True,choices=['month','aggregate'])
    p.add_argument('--root',type=Path)
    p.add_argument('--month')
    p.add_argument('--private-out',type=Path)
    p.add_argument('--private-inputs',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    if a.mode=='month':
        if a.month not in MONTHS:raise SystemExit('SEALED MONTH NOT ACCEPTED')
        if not a.root or not a.private_out:raise SystemExit('missing month args')
        print('B05K_MONTH_SAFE='+json.dumps(month_stage(a.root,a.month,a.private_out),sort_keys=True))
    else:
        if not a.private_inputs or not a.out or not a.report:raise SystemExit('missing aggregate args')
        allmonths={}
        for m in MONTHS:
            allmonths[m]=json.loads((a.private_inputs/f't05_daily_{m}.json').read_text('utf8'))
        result=calculate(allmonths)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
        a.report.write_text(write_report(result),encoding='utf8')
        print('B05K_SAFE_FINAL='+json.dumps({'source':result['n_source_days'],
          'eligible':result['n_eligible_sessions'],'active':result['n_active_sessions'],
          'ntrades':result['n_trades'],'weeks':result['n_calendar_weeks_observed'],
          'stats':{k:v['blocks']['5'] for k,v in result['scenarios'].items()},
          'no_oos':True,'no_new_history':True,'daily_exported':False},sort_keys=True))
