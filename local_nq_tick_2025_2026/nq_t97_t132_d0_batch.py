#!/usr/bin/env python3
"""T97–T132 cohort G0/D0: six new mechanistic blocks with atomic 233/377/4181.

NO market future outcomes or fills. Aggregate N, mask Jaccard, 20-diverse gate.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from itertools import combinations
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05
from nq_t97_t132_d0_features import classify_day,FEATURES,CASE,CONTROL,OTHER,MISSING,LABELS

REGISTRY=Path(__file__).resolve().parents[1]/'research/nq/NQ_T97_T132_SIX_BLOCKS_D0_PREREG_2026_10_12.json'
IDS=tuple(f'T{i}' for i in range(97,133))
BLOCKS=tuple(f'B{i}_{x}' for i,x in (
   (12,'MICRO_233'),(13,'MACRO_4181'),(14,'CROSS_BARRIER'),
   (15,'RETEST_LOCATION'),(16,'PACE_CONTRACTION'),(17,'CONSENSUS_INTERACTION')))
SOURCE,READY=140,135

def load_registry(path=REGISTRY):
    reg=json.loads(path.read_text())
    mem=reg['members']
    if (reg.get('prereg_id')!='NQ-T97-T132-SIX-BLOCKS-D0-V1'
        or reg.get('policy_id')!='NQ-COHORT-FUNNEL-V1'
        or reg.get('cohort_id')!='NQ-C97-132'
        or reg.get('stage_authorized')!='G0_D0_ONLY'
        or reg.get('family_size')!=36 or len(mem)!=36
        or tuple(z['id'] for z in mem)!=IDS
        or tuple(z['feature'] for z in mem)!=FEATURES
        or tuple(reg.get('blocks',[]))!=BLOCKS
        or [sum(z['block']==k for z in mem) for k in BLOCKS]!=[6]*6
        or reg.get('source_dev_months')!=list(MONTHS)
        or (reg.get('expected_source'),reg.get('expected_ready'),
            reg.get('expected_anchors'))!=(SOURCE,READY,READY)
        or reg.get('required_D0_n_case')!=15 or reg.get('required_D0_n_control')!=15
        or reg.get('near_duplicate_case_jaccard_cutoff')!=.85
        or reg.get('new_D1_cohort_min_diverse')!=20
        or any(reg[z] is not False for z in (
           'future_outcomes_in_D0','bar_5_seconds_new_signals',
           'D1_started','OOS_opened','new_market_data'))
        or reg.get('no_broker_fills_claim') is not True
        or any(z['case']!='vote>0' or z['control']!='vote<0'
           or z['outcome_read_in_D0'] is not False
           or z['mode'] not in ('VOTO','REGIMEN','CONSENSO')
           for z in mem)):
        raise ValueError('D0_NEW_COHORT_PREREG_MISMATCH')
    return reg

def month_stage(root,month,reg):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_BEFORE_IO')
    src=ready=0;qc=Counter();count={k:Counter() for k in IDS};ov=Counter()
    for day in sorted(month_days(root,month)):
        d=dev_day(day)
        src+=1
        events=list(source_events(file_for(root,d,'Last')))
        status,_,_=frozen_t05(events,day)
        qc[status]+=1
        if status!='READY':continue
        labels=classify_day(events,day,reg)
        if set(labels)!=set(IDS):raise AssertionError('D0_MUST_COVER_ALL_36')
        for k,v in labels.items():
            if v not in LABELS:raise ValueError('INVALID_CASE_LABEL')
            count[k][v]+=1
        cases=[k for k in IDS if labels[k]==CASE]
        for a,b in combinations(cases,2):ov[a+'__'+b]+=1
        ready+=1
    if (sum(qc.values())!=src or ready!=qc['READY']
        or any(sum(count[k].values())!=ready for k in IDS)):
        raise AssertionError('MISSING_SOURCE_OR_LABELS')
    return {'stage':'T97_T132_PRIVATE_FREE_D0','month':month,
      'source':src,'eligible':ready,
      'counts':{k:{g:count[k][g] for g in LABELS} for k in IDS},
      'case_pair_overlap':dict(ov),
      'future_outcomes_read':False,'individual_days_exported':False,
      'holdouts_opened':False,'new_data':False,'five_second_signals':False,
      'N_trades':None,'PnL':None,'PF':None,'DD':None,'CI90':None,'p':None,'q':None}

def shortlist(ids,questions,pairs,reg):
    groups={b:[z['id'] for z in reg['members']
            if z['block']==b and z['id'] in ids] for b in BLOCKS}
    ordered=[]
    while any(groups.values()):
        for k in BLOCKS:
            if groups[k]:ordered.append(groups[k].pop(0))
    selected=[];dupes={}
    for i in ordered:
        for j in selected:
            a,b=sorted((i,j),key=lambda x:int(x[1:]))
            same=pairs.get(a+'__'+b,0)
            union=questions[i]['N_case']+questions[j]['N_case']-same
            jac=same/union if union else 1.0
            if jac>=.85:
                dupes[i]={'of':j,'case_jaccard':round(jac,6)}
                break
        else:selected.append(i)
    return selected,dupes

def aggregate(ms,reg):
    if set(ms)!=set(MONTHS):raise ValueError('SEVEN_MONTHS_REQUIRED')
    tot={k:Counter() for k in IDS};over=Counter();src=ready=0
    months=[]
    for m in MONTHS:
        x=ms[m]
        if (x['stage']!='T97_T132_PRIVATE_FREE_D0'
            or x['month']!=m or set(x['counts'])!=set(IDS)
            or any(x[k] is not False for k in ('future_outcomes_read',
              'individual_days_exported','holdouts_opened','new_data',
              'five_second_signals'))
            or any(x[k] is not None for k in ('N_trades','PnL','PF','DD','CI90','p','q'))):
            raise ValueError('UNSAFE_D0_MONTH')
        src+=x['source'];ready+=x['eligible']
        for k in IDS:
            if set(x['counts'][k])!=set(LABELS) or sum(x['counts'][k].values())!=x['eligible']:
                raise AssertionError('BAD_MONTH_COUNTERS')
            tot[k].update(x['counts'][k])
        over.update(x['case_pair_overlap'])
        months.append({'month':m,'source':x['source'],'eligible':x['eligible'],
          'N_case_control':{k:[x['counts'][k][CASE],x['counts'][k][CONTROL]] for k in IDS}})
    if (src,ready)!=(SOURCE,READY):raise AssertionError('SOURCE_140_READY_135_REQUIRED')
    questions={}
    for z in reg['members']:
        k=z['id'];v=tot[k]
        if sum(v.values())!=READY:raise AssertionError('135_ROWS_ALL_MEMBERS_REQUIRED')
        state='UNIDENTIFIABLE' if not v[CASE] or not v[CONTROL] else (
              'LOW_POWER' if min(v[CASE],v[CONTROL])<15 else 'TESTABLE')
        questions[k]={'block':z['block'],'feature':z['feature'],
          'question':z['question'],'N_case':v[CASE],'N_control':v[CONTROL],
          'N_other':v[OTHER],'N_not_evaluable':v[MISSING],
          'D0':state,'D1':'NOT_RUN',
          'N_trades':None,'PnL':None,'PF':None,'DD':None,
          'CI90':None,'p':None,'q':None,'Holm':None}
    eligible=[k for k in IDS if questions[k]['D0']=='TESTABLE']
    chosen,duplicate=shortlist(eligible,questions,over,reg)
    return {'stage':'NQ_T97_T132_SIX_BLOCKS_D0_AGGREGATE',
      'cohort_id':reg['cohort_id'],'prereg_id':reg['prereg_id'],
      'source_sessions':src,'eligible_sessions':ready,
      'family_size':36,'questions':questions,'month_counts':months,
      'D0_testable_ids':eligible,'D0_testable_count':len(eligible),
      'D0_diverse_shortlist_ids':chosen,'D0_diverse_count':len(chosen),
      'D0_near_duplicate_ids':duplicate,
      'D1_20_diverse_gate_satisfied':len(chosen)>=20,
      'D1_requires_separate_prereg':True,'D1_executed':False,
      'market_outcomes_read':False,'holdouts_opened':False,
      'new_data':False,'five_second_signals':False,
      'N_trades':None,'PnL':None,'PF':None,'DD':None,
      'CI90':None,'p':None,'q':None,'Holm':None}

def report(x):
    s=['# T97–T132 — cohorte NUEVA de seis bloques, G0/D0 SOLO VIABILIDAD',
       '',f"Fuente={x['source_sessions']}, READY={x['eligible_sessions']}; "
          'siete archivos DEV existentes 2025-10…2026-04.',
       f"**36 preguntas inscritas**, TESTABLE={x['D0_testable_count']}; "
       f"diversas={x['D0_diverse_count']}; **gate20="
       f"{'PASS' if x['D1_20_diverse_gate_satisfied'] else 'NOT_YET'}**.",
       'N trades/retorno/IC90/p/q/Holm/PF/DD=NO MEDIDOS en D0.','',
       '| ID | Mecanismo | Pregunta | CASE | CTRL | OTHER | NO EVAL | D0 | Diversa? |',
       '|---|---|---|---:|---:|---:|---:|---|---|']
    for k,z in x['questions'].items():
        s.append(f"| {k} | {z['block']} | {z['question']} | "
          f"{z['N_case']} | {z['N_control']} | {z['N_other']} | "
          f"{z['N_not_evaluable']} | {z['D0']} | "
          f"{'SÍ' if k in x['D0_diverse_shortlist_ids'] else 'NO'} |")
    s+=['',f"En shortlist se excluyeron {len(x['D0_near_duplicate_ids'])} "
            'near duplicates por máscara CASE Jaccard≥0,85.',
            '**No hay todavía D1 ni D2.** Si se supera 20: '
            'prerregistro separado de familia completa k36, no 20 escogidas.',
            'Si <20: nuevas hipótesis con ID nuevos, sin retunar las presentes.',
            'No nuevos datos, 5s, OOS ni fills.','']
    return '\n'.join(s)

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--root',type=Path)
    a.add_argument('--month')
    a.add_argument('--inputs',type=Path)
    a.add_argument('--out',type=Path,required=True)
    a.add_argument('--report',type=Path)
    t=a.parse_args();reg=load_registry()
    if t.month:
        if t.month not in MONTHS:raise SystemExit('SEALED_MONTH_BEFORE_IO')
        out=month_stage(t.root,t.month,reg)
        t.out.parent.mkdir(parents=True,exist_ok=True)
        t.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print('NQ_T97_T132_D0_MONTH='+json.dumps({'month':t.month,
          'source':out['source'],'eligible':out['eligible'],'outcomes':False}))
    else:
        if not t.inputs or not t.report:raise ValueError('missing inputs and report')
        ms={m:json.loads((t.inputs/f't97_t132_d0_{m}.json').read_text()) for m in MONTHS}
        out=aggregate(ms,reg)
        t.out.parent.mkdir(parents=True,exist_ok=True)
        t.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        t.report.write_text(report(out))
        print('NQ_T97_T132_D0_FINAL='+json.dumps({
          'source':out['source_sessions'],'eligible':out['eligible_sessions'],
          'testable':out['D0_testable_count'],'diverse':out['D0_diverse_count'],
          'gate_20':out['D1_20_diverse_gate_satisfied'],
          'shortlist':out['D0_diverse_shortlist_ids'],'outcomes':False},sort_keys=True))
