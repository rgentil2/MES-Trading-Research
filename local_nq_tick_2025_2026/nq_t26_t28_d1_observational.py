#!/usr/bin/env python3
"""T26-T28 previously-frozen D1: observational only, no broker fills/PNL.

All outcomes remain private until full 7 DEV months aggregate is verified.
Source prereg research/nq/NQ_T26_T28_D1_OBSERVATIONAL_PREREG_2026_10_12.md
"""
import argparse,json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05,et_edge
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t26_t28_d0_screen import IDS,CASE,CONTROL,OTHER,MISSING,screen_day
from nq_t20_t25_d1_atomic_markout import (
    range_at_900,first_post_horizon_atomic_vwap,bootstrap_delta)
from nq_t29_t58_d1_batch import bh_frozen_family as bh_thirty

CATEGORIES=(CASE,CONTROL,OTHER,MISSING)
EXPECTED={IDS[0]:(18,36),IDS[1]:(6,65),IDS[2]:(3,0)}
N=135

def bh_three(p):
    if len(p)!=3 or any(not 0<=v<=1 for v in p):raise ValueError("family three required")
    o=sorted(range(3),key=lambda k:p[k])
    q=[None]*3;m=1.
    for i in range(3,0,-1):
        j=o[i-1];m=min(m,p[j]*3/i);q[j]=m
    return q

def one_day(events,day):
    dev_day(day)
    labels=screen_day(events,day)
    bars=completed_bars_by_print_count(events,day,(377,))[377]
    low,high=et_edge(day,10,0),et_edge(day,10,15)
    e=next((bar for bar in bars if low<=bar.end_timestamp<high),None)
    if e is None:raise AssertionError('NO_D0_ANCHOR')
    times=[x[0] for x in events]
    future_range=range_at_900(events,times,e.end_timestamp)
    fut=first_post_horizon_atomic_vwap(events,times,e.end_timestamp+3000000000)
    v=Fraction(e.price_times_qty_ticks,e.total_qty)
    result={}
    for k in IDS:
        group,side=labels[k]
        if group not in CATEGORIES:raise ValueError("BAD_D0_CATEGORY")
        if group not in (CASE,CONTROL): outcome=None
        elif k!=IDS[1]:
            if side!=0:raise ValueError('NO_DIRECTION_ON_RANGE')
            outcome=float(future_range)
        else:
            if side not in (-1,1):raise ValueError('NO_SIDE_FOR_T27')
            outcome=float(side*(fut-v))
        result[k]={'group':group,'side':side,'value':outcome}
    return result

def month_stage(root,month,out):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_BEFORE_IO')
    if out.exists():raise ValueError('NO_OVERWRITE_PRIVATE')
    qc=Counter();counts={k:Counter() for k in IDS};vec=[];source=0
    for day in sorted(month_days(root,month)):
        dev_day(day)
        source+=1
        events=list(source_events(file_for(root,day,'Last')))
        ready,_,_=frozen_t05(events,day)
        qc[ready]+=1
        if ready!='READY':continue
        row=one_day(events,day)
        vec.append(row)
        for k in IDS:counts[k][row[k]['group']]+=1
    eligible=qc['READY']
    if len(vec)!=eligible or sum(qc.values())!=source:raise AssertionError('BAD_QC')
    if any(sum(counts[k].values())!=eligible for k in IDS):raise AssertionError('BAD_LABELS')
    r={'stage':'T26_T28_D1_PRIVATE_ONLY','month':month,'source':source,
       'eligible':eligible,'counts':{k:{g:counts[k][g] for g in CATEGORIES} for k in IDS},
       'daily':vec,'PnL':None,'N_trades':0,
       'broker_fills':False,'holdouts_opened':False,'new_data':False,
       'individual_outcomes_public':False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,separators=(',',':'))+'\n')
    return {'month':month,'source':source,'eligible':eligible,'PnL':None}

def aggregate(ms):
    if set(ms)!=set(MONTHS):raise ValueError('SEVEN_MONTHS_REQUIRED')
    totals={k:Counter() for k in IDS};daily=[];src=eligible=0
    by_month=[]
    for m in MONTHS:
        x=ms[m]
        if (x['stage']!='T26_T28_D1_PRIVATE_ONLY' or x['month']!=m or
          x['PnL'] is not None or x['N_trades']!=0 or
          any(x[k] is not False for k in ('broker_fills','holdouts_opened','new_data','individual_outcomes_public')) or
          set(x['counts'])!=set(IDS) or len(x['daily'])!=x['eligible']):
            raise ValueError('UNSAFE_OR_INCOMPLETE_MONTH')
        daily.extend(x['daily']);src+=x['source'];eligible+=x['eligible']
        for k in IDS:
            if sum(x['counts'][k].values())!=x['eligible']:raise AssertionError('LABEL_NOT_ALL')
            totals[k].update(x['counts'][k])
        by_month.append({'month':m,'source':x['source'],'eligible':x['eligible'],
             'case_control':{k:[x['counts'][k][CASE],x['counts'][k][CONTROL]] for k in IDS}})
    if (src,eligible,len(daily))!=(140,N,N):raise AssertionError('SOURCE_140_READY_135_FAIL')
    results={};ps=[]
    for k in IDS:
        n=(totals[k][CASE],totals[k][CONTROL])
        if n!=EXPECTED[k] or sum(totals[k].values())!=N:
            raise AssertionError('D0_COUNTS_CHANGED')
        by_g={g:[d[k]['value'] for d in daily if d[k]['group']==g and d[k]['value'] is not None] for g in (CASE,CONTROL)}
        means={g:sum(v)/len(v) if v else None for g,v in by_g.items()}
        delta=means[CASE]-means[CONTROL] if all(means[g] is not None for g in (CASE,CONTROL)) else None
        ci={str(L):bootstrap_delta(daily,k,L) for L in (3,5,10)}
        p=ci['5']['p_exploratory'];ps.append(p if p is not None else 1.)
        results[k]={'N_case':n[0],'N_control':n[1],
          'N_case_observed':len(by_g[CASE]),'N_control_observed':len(by_g[CONTROL]),
          'case_mean_ticks':means[CASE],'control_mean_ticks':means[CONTROL],
          'delta_ticks':delta,'bootstrap_L3_L5_L10':ci,'p_L5_exploratory':p,
          'p1_sentinel_for_BH':p is None,'unit':'NQ_TICK_SIGNED_VWAP_300S' if k==IDS[1]
                            else 'NQ_TICK_RANGE_15MIN'}
    q=bh_three(ps)
    for i,k in enumerate(IDS):
        x=results[k];ci=x['bootstrap_L3_L5_L10']['5']['ci90']
        x['q_BH3_descriptive']=None if x['p1_sentinel_for_BH'] else q[i]
        x['D1']='NOT_ESTIMABLE' if ci is None else (
              'NOT_SUPPORTED_DESCRIPTIVE' if x['delta_ticks']<=0 else
              'INCONCLUSIVE' if ci[0]<=0 else
              'PROMISING_PREDICTIVE_IN_SAMPLE_NOT_TRADABLE')
    return {'stage':'T26_T28_D1_OBSERVATIONAL_COMPLETE',
      'source':src,'eligible':eligible,'family_size':3,'months':by_month,
      'questions':results,'PnL':None,'N_trades':0,'PF':None,'DD':None,
      'portfolio_delta':None,'N_effective':None,'Holm':None,
      'holdouts_opened':False,'broker_fills':False,'new_data':False}

def md(z):
    lines=['# T26-T28 D1 — COMPLETE: observational only, not trading','','Seven DEV months only; 140 source /135 eligible; no fills/PNL.','','| ID | N case/control | mean CASE | mean CTRL | Delta price ticks | IC90 L5 | p L5 | q BH3 | D1 |','|---|---:|---:|---:|---:|---|---:|---:|---|']
    f=lambda x:'N/D' if x is None else f'{x:+.3f}'
    for k,v in z['questions'].items():
        ci=v['bootstrap_L3_L5_L10']['5']['ci90']
        lines.append(f"| {k} | {v['N_case']}/{v['N_control']} | {f(v['case_mean_ticks'])} | {f(v['control_mean_ticks'])} | {f(v['delta_ticks'])} | {('['+f(ci[0])+','+f(ci[1])+']') if ci else 'N/D'} | {f(v['p_L5_exploratory'])} | {f(v['q_BH3_descriptive'])} | {v['D1']} |")
    lines+=['','Q exploratory on reused DEV, no Holm and no strategy profitability.']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path);p.add_argument('--month')
    p.add_argument('--inputs',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    if a.month:
        if a.month not in MONTHS:raise SystemExit('SEALED_MONTH_BEFORE_IO')
        print(json.dumps(month_stage(a.root,a.month,a.out),sort_keys=True))
    else:
        if a.inputs is None or a.report is None:raise ValueError('inputs+report required')
        z=aggregate({m:json.loads((a.inputs/f'd1_{m}.json').read_text()) for m in MONTHS})
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
        a.report.write_text(md(z))
        print('T26_D1_FINAL='+json.dumps({'n':z['eligible'],'questions':{
          k:{'delta':v['delta_ticks'],'ci90':v['bootstrap_L3_L5_L10']['5']['ci90'],
             'p':v['p_L5_exploratory'],'q':v['q_BH3_descriptive'],'status':v['D1']}
           for k,v in z['questions'].items()}},sort_keys=True))
