#!/usr/bin/env python3
"""Thirty-member D1 observational predictive block, pre-registered, NO trading.

All new outcomes restricted to seven existing protected NQ Last DEV releases.
Family BH k=30 includes D0-screen failures; no brokerage fills or P&L.
"""
from __future__ import annotations
import argparse,json
from bisect import bisect_left
from collections import Counter
from fractions import Fraction
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05,et_edge
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t29_t58_d0_batch import load_registry
from nq_t29_t58_d0_features import screen_day,CASE,CONTROL,OTHER,MISSING
from nq_t20_t25_d1_atomic_markout import (
    range_at_900,first_post_horizon_atomic_vwap,bootstrap_delta)

SOURCE=140
ELIGIBLE=135
CLASSES=(CASE,CONTROL,OTHER,MISSING)
EXPECTED_PAIRS=[
(80,31),(44,72),(65,65),(85,40),(72,59),(46,67),
(45,60),(66,64),(68,62),(61,68),(62,30),(31,36),
(15,17),(45,42),(60,40),(79,51),(79,39),(48,39),
(28,100),(89,14),(101,23),(14,93),(13,84),(67,46),
(80,32),(50,44),(69,55),(60,64),(53,27),(58,58)]
EXPECTED={f'T{i}':p for i,p in zip(range(29,59),EXPECTED_PAIRS)}

def one_day(events,day,reg):
    dev_day(day)
    labels=screen_day(events,day,reg)
    bars=completed_bars_by_print_count(events,day,(377,))[377]
    lo,hi=et_edge(day,10,0),et_edge(day,10,15)
    ix=next((i for i,b in enumerate(bars) if lo<=b.end_timestamp<hi),None)
    if ix is None or ix<4:
        raise AssertionError('STAGE0_ANCHOR_PARITY_FAIL')
    e,d=bars[ix],bars[ix-1]
    ts=[x[0] for x in events]
    # Two independent physical endpoints, NEVER a broker execution.
    physical_range=range_at_900(events,ts,e.end_timestamp)
    future_vwap=first_post_horizon_atomic_vwap(
        events,ts,e.end_timestamp+300*10_000_000)
    vw_e=Fraction(e.price_times_qty_ticks,e.total_qty)
    vw_d=Fraction(d.price_times_qty_ticks,d.total_qty)
    side=(vw_e>vw_d)-(vw_e<vw_d)
    values={}
    for row in reg['hypotheses']:
        id_=row['id'];label=labels[id_]
        if label not in CLASSES:raise AssertionError('INVALID_D0_LABEL')
        if label not in (CASE,CONTROL):
            value=None;local_side=0
        elif row['block']=='B2_MULTI_BAR_CONTEXT':
            local_side=side
            value=float(side*(future_vwap-vw_e)) if side else None
        else:
            local_side=0;value=float(physical_range)
        values[id_]={'group':label,'side':local_side,'value':value}
    if set(values)!=set(EXPECTED):
        raise AssertionError('MISSING_MEMBERS')
    return values

def month_stage(root,month,out,reg):
    if month not in MONTHS:
        raise ValueError('SEALED_MONTH_DENIED_BEFORE_IO')
    if out.exists():
        raise ValueError('PRIVATE_OUTCOMES_CANNOT_OVERWRITE')
    qc=Counter();counts={z['id']:Counter() for z in reg['hypotheses']}
    daily=[];src=0
    for day in sorted(month_days(root,month)):
        dev_day(day)
        src+=1
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        status,_,_=frozen_t05(events,day)
        qc[status]+=1
        if status!='READY':continue
        vals=one_day(events,day,reg)
        daily.append(vals)
        for id_,x in vals.items():
            counts[id_][x['group']]+=1
    ready=qc['READY']
    if sum(qc.values())!=src or ready!=len(daily):
        raise AssertionError('ELIGIBILITY_COVERAGE_FAIL_CLOSED')
    if any(sum(counts[k].values())!=ready for k in counts):
        raise AssertionError('CLASS_COVERAGE_FAIL_CLOSED')
    obj={'stage':'T29_T58_PRIVATE_D1_PREDICTION_NO_PNL',
        'month':month,'source':src,'eligible':ready,
        'counts':{k:{g:counts[k][g] for g in CLASSES} for k in counts},
        'daily':daily,'broker_fills_modelled':False,
        'trades_simulated':0,'Pnl':None,'private_data_public':False,
        'holdouts_opened':False,'new_market_data_acquired':False,
        'new_five_second_signals':False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(obj,separators=(',',':'))+'\n')
    return {'month':month,'source':src,'eligible':ready,
        'trades':0,'Pnl':None,'future_private':True}

def bh_frozen_family(ps):
    if len(ps)!=30 or any(not 0<=p<=1 for p in ps):
        raise ValueError('FULL_30_FAMILY_REQUIRED')
    ords=sorted(range(30),key=lambda i:ps[i])
    result=[None]*30
    running=1.
    for rank in range(30,0,-1):
        i=ords[rank-1]
        running=min(running,ps[i]*30/rank)
        result[i]=running
    return result

def aggregate(months,reg):
    if set(months)!=set(MONTHS):
        raise ValueError('SEVEN_COMPLETE_MONTHS_REQUIRED')
    totals={z['id']:Counter() for z in reg['hypotheses']}
    daily=[];source=eligible=0
    periods=[]
    for m in MONTHS:
        x=months[m]
        if (x['month']!=m or x['stage']!='T29_T58_PRIVATE_D1_PREDICTION_NO_PNL'
            or x['trades_simulated']!=0 or x['Pnl'] is not None
            or any(x[k] is not False for k in ('broker_fills_modelled',
                'private_data_public','holdouts_opened','new_market_data_acquired',
                'new_five_second_signals')) or
            set(x['counts'])!=set(EXPECTED)):
            raise ValueError('INVALID_OR_UNSAFE_D1_MONTH')
        source+=x['source'];eligible+=x['eligible']
        if len(x['daily'])!=x['eligible']:
            raise AssertionError('MISSING_DAILY_ROWS')
        daily.extend(x['daily'])
        for id_ in totals:
            if set(x['counts'][id_])!=set(CLASSES) or sum(x['counts'][id_].values())!=x['eligible']:
                raise AssertionError('MISSING_D0_CLASS_LABEL')
            totals[id_].update(x['counts'][id_])
        periods.append({'month':m,'source':x['source'],'eligible':x['eligible'],
           'case_control_counts':{k:[x['counts'][k][CASE],x['counts'][k][CONTROL]]
                                  for k in totals}})
    if (source,eligible,len(daily))!=(SOURCE,ELIGIBLE,ELIGIBLE):
        raise AssertionError('EXPECTED_140_135_DEVELOPMENT_FAIL')
    questions={}
    ps=[]
    for row in reg['hypotheses']:
        k=row['id'];n=(totals[k][CASE],totals[k][CONTROL])
        if n!=EXPECTED[k] or sum(totals[k].values())!=ELIGIBLE:
            raise AssertionError('D0_PREREG_LABEL_CHANGED')
        observed={g:[v[k]['value'] for v in daily
                     if v[k]['group']==g and v[k]['value'] is not None]
                  for g in (CASE,CONTROL)}
        means={g:sum(observed[g])/len(observed[g]) if observed[g] else None
               for g in (CASE,CONTROL)}
        delta=(means[CASE]-means[CONTROL] if
               means[CASE] is not None and means[CONTROL] is not None else None)
        boots={str(L):bootstrap_delta(daily,k,L) for L in (3,5,10)}
        p=boots['5']['p_exploratory']
        ps.append(p if p is not None else 1.)
        questions[k]={'block':row['block'],'feature':row['feature'],
           'question':row['question'],'N_case':n[0],'N_control':n[1],
           'N_case_observed':len(observed[CASE]),
           'N_control_observed':len(observed[CONTROL]),
           'N_case_no_side':n[0]-len(observed[CASE]),
           'N_control_no_side':n[1]-len(observed[CONTROL]),
           'mean_case':means[CASE],'mean_control':means[CONTROL],
           'delta_predicted_ticks':delta,
           'outcome_units':'NQ_PRICE_TICKS_SIGNED_VWAP_300S' if
              row['block']=='B2_MULTI_BAR_CONTEXT' else 'NQ_PRICE_TICKS_FUTURE_RANGE_15MIN',
           'bootstrap_L3_L5_L10':boots,'p_L5_exploratory':p,
           'BH_p_adjustment_sentinel':ps[-1],
           'p_missing_sentinel_only':p is None}
    qs=bh_frozen_family(ps)
    for idx,k in enumerate(questions):
        v=questions[k];lo=v['bootstrap_L3_L5_L10']['5']['ci90']
        v['q_BH_descriptive']=None if v['p_missing_sentinel_only'] else qs[idx]
        if lo is None:v['D1']='NOT_ESTIMABLE'
        elif v['delta_predicted_ticks']<=0:v['D1']='NOT_SUPPORTED_DESCRIPTIVE'
        elif lo[0]<=0:v['D1']='INCONCLUSIVE'
        else:v['D1']='PROMISING_PREDICTIVE_IN_SAMPLE_NOT_TRADABLE'
    return {'stage':'T29_T58_D1_COMPLETE_OBSERVATIONAL_NOT_FINANCIAL',
        'policy_id':'NQ-DISCOVERY-STAGED-GATES-V1',
        'source_sessions':source,'eligible_sessions':eligible,
        'family_size':30,'shortlist_D0_ids':[
          'T29','T35','T41','T47','T30','T36','T42','T49','T54',
          'T31','T37','T43','T52','T55','T38','T44','T56',
          'T33','T39','T45','T57','T34','T40','T46','T58'],
        'questions':questions,'monthly_coverage_counts':periods,
        'exploratory_selection_valid_confirmatory_p':False,
        'Holm_confirmatory':None,'robust_3_of_5_years':None,'N_effective':None,
        'N_trades':0,'net_PnL':None,'PF':None,'DD':None,
        'portfolio_delta':None,'broker_fills_verified':False,
        'holdouts_opened':False,'new_market_data_acquired':False,
        'individual_outcomes_public':False}

def report(z):
    out=['# NQ T29–T58 D1 — 30 hipótesis (25 diversas) SOLO PREDICCIÓN',
       '', '7 meses DEV/140 fuente/135 elegibles; NO trading, NO PnL.',
       'B1,B3,B4,B5: RANGO 15min. B2: VWAP markout signed +300s.',
       'IC90 bootstrap no circular L5 10.000, sensibilidad L3/L10.',
       'Todos q-BH en DEV adaptativo DESCRIPTIVOS, ninguno es Holm.',
       '', '| ID | Bloque | N case/ctrl | Media case | Media ctrl | Delta ticks | IC90 L5 | p/q BH descriptivas | D1 |',
       '|---|---|---:|---:|---:|---:|---|---|---|']
    def f(x):return 'N/D' if x is None else f'{x:+.3f}'
    for k,x in z['questions'].items():
        ci=x['bootstrap_L3_L5_L10']['5']['ci90']
        cis=('['+f(ci[0])+', '+f(ci[1])+']') if ci else 'N/D'
        out.append(f"| {k} | {x['block']} | {x['N_case']}/{x['N_control']} | "
                   f"{f(x['mean_case'])} | {f(x['mean_control'])} | "
                   f"{f(x['delta_predicted_ticks'])} | {cis} | "
                   f"{f(x['p_L5_exploratory'])}/{f(x['q_BH_descriptive'])} | {x['D1']} |")
    out+=['', 'N trades=0; PF/DD/CAGR/retorno fondeo/DeltaRouter=NO MEDIDOS.',
        'No reinterpretar una asociación de rango como dirección u oportunidad ejecutable.',
        '30 miembros en la BH familiar, incluidos 5 descartados en D0.', '']
    return '\n'.join(out)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path)
    p.add_argument('--month')
    p.add_argument('--inputs',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path)
    a=p.parse_args();reg=load_registry()
    if a.month is not None:
        if a.month not in MONTHS:
            raise SystemExit('SEALED_BEFORE_IO')
        x=month_stage(a.root,a.month,a.out,reg)
        print('T29_T58_D1_PRIVATE_MONTH='+json.dumps(x,sort_keys=True))
    else:
        if a.inputs is None or a.report is None:
            raise ValueError('missing inputs/report')
        months={m:json.loads((a.inputs/f't29_t58_d1_{m}.json').read_text())
                for m in MONTHS}
        z=aggregate(months,reg)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n')
        a.report.write_text(report(z)+'\n')
        print('T29_T58_D1_SAFE_AGGREGATE='+json.dumps({
          'source':z['source_sessions'],'eligible':z['eligible_sessions'],
          'family_size':z['family_size'],'trades':0,'PnL':None,
          'counts':dict(Counter(x['D1'] for x in z['questions'].values())),
          'positive_CI90_ids':[k for k,x in z['questions'].items() if
             x['D1']=='PROMISING_PREDICTIVE_IN_SAMPLE_NOT_TRADABLE'],
          'holdouts_opened':False},sort_keys=True))
