#!/usr/bin/env python3
"""T97-T132 WHOLE-COHORT D1 signed VWAP markout at +300s, preregistered.

ONLY runs after frozen completed D0 140/135/36/20 diverse; never fills/trades.
All 135 daily vectors and licensed Last stored PRIVATE in one action runner.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05
from nq_t61_t96_d0_features import first_bars,CASE,CONTROL,OTHER,MISSING
from nq_t97_t132_d0_batch import load_registry,IDS,SOURCE,READY
from nq_t97_t132_d0_features import classify_day
from nq_t20_t25_d1_atomic_markout import first_post_horizon_atomic_vwap,bootstrap_delta

CLASSES=(CASE,CONTROL,OTHER,MISSING)
PREREG=Path(__file__).resolve().parents[1]/'research/nq/NQ_T97_T132_D1_WHOLE_COHORT_PREREG_2026_10_12.md'
D0=Path(__file__).resolve().parents[1]/'research/nq/NQ_T97_T132_D0_FROZEN_COUNTS_2026_10_12.json'
FAMILY=36

def d0_gate(path=D0):
    if not PREREG.is_file():raise ValueError('PREREG_D1_NOT_PRESENT')
    d=json.loads(path.read_text())
    if (d.get('cohort_id')!='NQ-C97-132'
        or d.get('prereg_id')!='NQ-T97-T132-SIX-BLOCKS-D0-V1'
        or (d.get('source'),d.get('eligible'))!=(SOURCE,READY)
        or d.get('family_size')!=FAMILY
        or d.get('all_ids')!=list(IDS)
        or d.get('D0_diverse_count',0)<20
        or d.get('D0_testable_count',0)<20
        or d.get('D1_20_diverse_gate_satisfied') is not True
        or d.get('D1_executed') is not False
        or d.get('outcomes_read') is not False
        or d.get('holdouts_opened') is not False
        or set(d.get('case_control_other_missing',{}))!=set(IDS)
        or any(set(d['case_control_other_missing'][k])!=set(CLASSES) or
           sum(d['case_control_other_missing'][k].values())!=READY for k in IDS)):
        raise ValueError('D0_WHOLE_COHORT_20_DIVERSE_GATE_FAILED')
    return d

def bh36(p):
    if len(p)!=FAMILY or any(not 0<=x<=1 for x in p):
        raise ValueError('FULL_36_MEMBER_BH_REQUIRED')
    order=sorted(range(FAMILY),key=lambda z:p[z])
    q=[None]*FAMILY;running=1.
    for rank in range(FAMILY,0,-1):
        ix=order[rank-1]
        running=min(running,p[ix]*FAMILY/rank)
        q[ix]=running
    return q

def one_day(events,day,reg):
    dev_day(day)
    labels=classify_day(events,day,reg)
    bars,anchor=first_bars(events,day)
    d,e=bars[-2],bars[-1]
    vD=F(sum(px*q for _,px,q in d),sum(q for _,px,q in d))
    vE=F(sum(px*q for _,px,q in e),sum(q for _,px,q in e))
    side=(vE>vD)-(vE<vD)
    times=[x[0] for x in events]
    future=first_post_horizon_atomic_vwap(
         events,times,anchor+300*10_000_000)
    result={}
    for id_ in IDS:
        group=labels[id_]
        if group not in CLASSES:raise AssertionError('ILLEGAL_D0_CATEGORY')
        val=(float(side*(future-vE)) if
             group in (CASE,CONTROL) and side in (-1,1) else None)
        result[id_]={'group':group,'value':val,'side':side if val is not None else 0}
    return result

def month_stage(root,month,out,reg):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_BEFORE_IO')
    if out.exists():raise ValueError('NO_OVERWRITE_PRIVATE_VECTORS')
    qc=Counter();count={k:Counter() for k in IDS};daily=[];source=0
    for day in sorted(month_days(root,month)):
        d=dev_day(day);source+=1
        events=list(source_events(file_for(root,d,'Last')))
        status,_,_=frozen_t05(events,day)
        qc[status]+=1
        if status!='READY':continue
        observations=one_day(events,day,reg)
        daily.append(observations)
        for k,v in observations.items():count[k][v['group']]+=1
    if len(daily)!=qc['READY'] or sum(qc.values())!=source:
        raise AssertionError('D1_MONTH_READY_COVERAGE_FAIL')
    if any(sum(count[k].values())!=len(daily) for k in IDS):
        raise AssertionError('ALL_36_CATEGORY_COUNTER_FAIL')
    r={'stage':'T97_T132_D1_PRIVATE_NO_FILLS','month':month,
       'source':source,'eligible':qc['READY'],'daily':daily,
       'counts':{k:{g:count[k][g] for g in CLASSES} for k in IDS},
       'N_trades':0,'PnL':None,'PF':None,'DD':None,
       'broker_fills_verified':False,'private_day_vectors_public':False,
       'holdouts_opened':False,'new_data':False,'five_second_signals':False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,separators=(',',':'))+'\n')
    return {'month':month,'source':source,'eligible':qc['READY'],
      'N_trades':0,'PnL':None,'private':True}

def aggregate(months,reg,d0):
    if set(months)!=set(MONTHS):raise ValueError('REQUIRE_FULL_SEVEN_MONTHS')
    totals={k:Counter() for k in IDS};daily=[];source=eligible=0;months_safe=[]
    for m in MONTHS:
        x=months[m]
        if (x['stage']!='T97_T132_D1_PRIVATE_NO_FILLS' or x['month']!=m
           or x['N_trades']!=0 or x['PnL'] is not None or x['PF'] is not None
           or x['DD'] is not None or set(x['counts'])!=set(IDS)
           or x['eligible']!=len(x['daily'])
           or any(x[k] is not False for k in ('broker_fills_verified',
               'private_day_vectors_public','holdouts_opened','new_data',
               'five_second_signals'))):
            raise ValueError('UNSAFE_D1_MONTH')
        source+=x['source'];eligible+=x['eligible']
        daily.extend(x['daily'])
        for k in IDS:
            if set(x['counts'][k])!=set(CLASSES) or sum(x['counts'][k].values())!=x['eligible']:
                raise AssertionError('D1_CASE_DROPPED')
            totals[k].update(x['counts'][k])
        months_safe.append({'month':m,'source':x['source'],'eligible':x['eligible'],
           'N_case_control':{k:[x['counts'][k][CASE],x['counts'][k][CONTROL]] for k in IDS}})
    if (source,eligible,len(daily))!=(SOURCE,READY,READY):
        raise AssertionError('D1_EXPECTED_140_135_MISMATCH')
    for k in IDS:
        if any(totals[k][g]!=d0['case_control_other_missing'][k][g] for g in CLASSES):
            raise AssertionError('D0_MASK_CHANGED_AFTER_OUTCOME')
    results={};pvals=[]
    for row in reg['members']:
        k=row['id']
        sample={g:[z[k]['value'] for z in daily if z[k]['group']==g and z[k]['value'] is not None]
                for g in (CASE,CONTROL)}
        means={g:sum(sample[g])/len(sample[g]) if sample[g] else None for g in (CASE,CONTROL)}
        effect=means[CASE]-means[CONTROL] if all(means[g] is not None for g in (CASE,CONTROL)) else None
        boot={str(L):bootstrap_delta(daily,k,L) for L in (3,5,10)}
        p=boot['5']['p_exploratory']
        pvals.append(p if p is not None else 1.)
        results[k]={'block':row['block'],'question':row['question'],
           'N_case':totals[k][CASE],'N_control':totals[k][CONTROL],
           'N_case_observed':len(sample[CASE]),
           'N_control_observed':len(sample[CONTROL]),
           'delta_ticks':effect,'mean_case':means[CASE],
           'mean_control':means[CONTROL],
           'bootstrap_L3_L5_L10':boot,'p_exploratory':p,
           'q_BH36':None,'Holm':None,'N_trades':0,
           'PnL':None,'PF':None,'DD':None,'DeltaRouter':None}
    q=bh36(pvals)
    for ix,k in enumerate(IDS):
        x=results[k];ci=x['bootstrap_L3_L5_L10']['5']['ci90']
        x['q_BH36']=None if x['p_exploratory'] is None else q[ix]
        if ci is None:x['D1']='NOT_ESTIMABLE'
        elif x['delta_ticks']<=0:x['D1']='NOT_SUPPORTED'
        elif ci[0]<=0 or q[ix]>.10:x['D1']='INCONCLUSIVE'
        else:x['D1']='PASS_EXPLORATORY_MARKOUT_ONLY'
    return {'stage':'T97_T132_D1_COMPLETE_OBSERVATIONAL_ONLY',
      'prereg_id':reg['prereg_id'],'D0_run_id':d0.get('source_action_run'),
      'source':source,'eligible':eligible,'family_size':FAMILY,
      'questions':results,'monthly_coverage':months_safe,
      'D1_survivor_ids':[k for k,v in results.items() if v['D1']=='PASS_EXPLORATORY_MARKOUT_ONLY'],
      'economic_eligible_ids':[], 'N_trades':0,'PnL':None,
      'PF':None,'DD':None,'DeltaRouter':None,'Holm':None,
      'holdouts_opened':False,'broker_fills_verified':False,
      'new_data':False,'private_daily_vectors_public':False,
      'DEV_reused_not_confirmatory':True}

def report(x):
    f=lambda a:'N/D' if a is None else f'{a:+.3f}'
    ls=['# NQ T97–T132 — D1 del bloque COMPLETO k36, SOLO OBSERVACIONAL',
      '',f"Fuentes existentes: {x['source']} / {x['eligible']} READY, 7 meses DEV.",
      'Y=side impulso E377 × [VWAP primer timestamp completo >E.end+300s −VWAP E].',
      'L5 bootstrap moving-block B=10000 e IC90; sensibilidad L3 y L10.',
      'BH36 incluye los 36 miembros originales aun NO ESTIMABLES (sentinela p=1).',
      'DEV reutilizada: resultados EXPLORATORIOS, no Holm/OOS.',
      '', '| ID | Mecanismo | CASE / CTRL | Delta ticks | IC90 L5 | p / q_BH36 | D1 |',
      '|---|---|---:|---:|---|---|---|']
    for k,v in x['questions'].items():
        ci=v['bootstrap_L3_L5_L10']['5']['ci90']
        ls.append(f"| {k} | {v['block']} | {v['N_case']}/{v['N_control']} | "
          f"{f(v['delta_ticks'])} | "
          f"{'['+f(ci[0])+', '+f(ci[1])+']' if ci else 'N/D'} | "
          f"{f(v['p_exploratory'])}/{f(v['q_BH36'])} | {v['D1']} |")
    ls+=['',f"**D1 PASS exploratoria = {len(x['D1_survivor_ids'])}**. "
         'No son trades ni estrategias monetizadas.',
       '**D2 BLOQUEADO:** N_trades=0, fills Last no verificados, '
       'USD neto/PF/DD/ROI/Holm/DeltaRouter=N/D. No OOS, no nueva data.','']
    return '\n'.join(ls)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path);p.add_argument('--month')
    p.add_argument('--inputs',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path);a=p.parse_args()
    expected=d0_gate()
    reg=load_registry()
    if a.month:
        if a.month not in MONTHS:raise SystemExit('SEALED_MONTH_BEFORE_IO')
        print('NQ_T97_T132_PRIVATE_D1_MONTH='+json.dumps(
          month_stage(a.root,a.month,a.out,reg),sort_keys=True))
    else:
        if not a.inputs or not a.report:raise ValueError('inputs/report required')
        ms={m:json.loads((a.inputs/f't97_t132_d1_{m}.json').read_text()) for m in MONTHS}
        out=aggregate(ms,reg,expected)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        a.report.write_text(report(out))
        print('NQ_T97_T132_D1_SAFE_FINAL='+json.dumps({
          'source':out['source'],'eligible':out['eligible'],'family':out['family_size'],
          'status':dict(Counter(v['D1'] for v in out['questions'].values())),
          'shortlist':out['D1_survivor_ids'],'economic_pass':[],
          'N_trades':0,'holdouts_opened':False},sort_keys=True))
