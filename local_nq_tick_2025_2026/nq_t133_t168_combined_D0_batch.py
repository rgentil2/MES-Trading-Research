#!/usr/bin/env python3
"""Expand frozen T133-T152 (20) with prereg T153-T168 (16) into ONE 36-family D0.
NO FUTURE market outcome. Old 20 CASE/CONTROL/OTHER/MISSING must EXACTLY
match previously frozen source counts before evaluating cohort gate.
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
from nq_t133_t152_executable_d0_batch import (
  load_registry as old_registry, classify_day as old_classify,
  IDS as OLD_IDS,BLOCKS as OLD_BLOCKS,diversity as old_diversity)
from nq_t153_t168_executable_d0_features import (
  classify_day as new_classify,FEATURES,LABELS,CASE,CONTROL,OTHER,MISSING)

SOURCE,READY=140,135
NEW_IDS=tuple('T'+str(i) for i in range(153,169))
IDS=OLD_IDS+NEW_IDS
NEW_BLOCKS=('E_VWAP_COUNTERMOVE','F_AUCTION_ALIGNMENT',
            'G_AUCTION_LOCATION','H_TAPE_STRUCTURE')
BLOCKS=OLD_BLOCKS+NEW_BLOCKS
ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/'research/nq/NQ_T153_T168_FOUR_STRATEGY_BLOCKS_D0_PREREG_2026_10_12.json'
OLD=ROOT/'research/nq/NQ_T133_T152_D0_COUNTS_FROZEN_2026_10_12.json'

def load_new(path=REG):
    x=json.loads(path.read_text())
    m=x['members']
    if (x.get('prereg_id')!='NQ-T153-T168-FOUR-INDEPENDENT-STRATEGY-BLOCKS-D0-V1'
        or x.get('expanded_cohort_id')!='NQ-C133-168'
        or x.get('original_seed_D0_action')!=38324292967
        or x.get('original_seed_D0_count_diverse')!=15
        or x.get('additional_count')!=16
        or x.get('whole_family_for_eventual_D1')!=36
        or tuple(x.get('original_seed_ids',[]))!=OLD_IDS
        or tuple(x['dev_months'])!=tuple(MONTHS)
        or tuple(x['diagnostic_months'])!=tuple(MONTHS[:3])
        or tuple(x['chronological_sensitivity_months'])!=tuple(MONTHS[3:])
        or tuple(x['blocks'])!=NEW_BLOCKS
        or tuple(z['id'] for z in m)!=NEW_IDS
        or tuple(z['feature'] for z in m)!=FEATURES
        or [sum(z['block']==b for z in m) for b in NEW_BLOCKS]!=[4]*4
        or (x['expected_source_sessions'],x['expected_ready_sessions'])!=(SOURCE,READY)
        or x['D0_case_min']!=15 or x['D0_ctrl_min']!=15
        or x['minimum_combined_diverse_for_D1']!=20
        or x['diverse_mask_jaccard_below']!=.85
        or (x['min_stop_ticks'],x['max_stop_ticks'],x['max_nominal_risk_usd'])!=(8,400,250)
        or any(x[k] is not False for k in ('outcome_reads_in_D0',
          'chronological_sensitivity_is_OOS','open_sealed_holdouts',
          'new_market_data','new_5s_signals','broker_fills_claim'))
        or x['D1_status']!='NOT_AUTHORIZED_UNTIL_WHOLE_COHORT_D0_PASS_AND_ECONOMIC_PREREG'
        or not x['original_and_expansion_D0_masks_must_match_frozen_seed']
        or any(z['future_outcomes_in_D0'] is not False or z['max_trades_per_day']!=1
               for z in m)):
        raise ValueError('D0_16_PROSPECTIVE_REGISTRY_TAMPERED')
    return x

def frozen_seed(path=OLD):
    r=json.loads(path.read_text())
    if (r['source_action_run']!=38324292967
        or r['cohort_id']!='NQ-C133-152'
        or r['family_size']!=20
        or r['all_ids']!=list(OLD_IDS)
        or r['source']!=SOURCE or r['eligible']!=READY
        or r['D0_testable_count']!=15 or r['D0_diverse_count']!=15
        or r['D1_executed'] is not False):
        raise ValueError('FROZEN_SEED_INVALID')
    return r

def month_stage(root,month,old,new):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_BEFORE_MARKET_IO')
    cnt={k:Counter() for k in IDS};pair=Counter();src=ready=0;qc=Counter()
    for day in sorted(month_days(root,month)):
        d=dev_day(day);src+=1
        e=list(source_events(file_for(root,d,'Last')))
        status,_,_=frozen_t05(e,day)
        qc[status]+=1
        if status!='READY':continue
        a=old_classify(e,day,old)
        b=new_classify(e,day,new)
        labels={**a,**b}
        if set(labels)!=set(IDS):raise AssertionError('36_MEMBER_ORIGINAL_FAMILY_NOT_COMPLETE')
        for id_,label in labels.items():
            if label not in LABELS:raise AssertionError('INVALID_LABEL')
            cnt[id_][label]+=1
        cs=[k for k in IDS if labels[k]==CASE]
        for aa,bb in combinations(cs,2):pair[aa+'__'+bb]+=1
        ready+=1
    if qc['READY']!=ready or sum(qc.values())!=src or (
        any(sum(cnt[k].values())!=ready for k in IDS)):
        raise AssertionError('SOURCE_SESSION_PARITY')
    return {'stage':'NQ_C133_168_PRIVATE_FREE_D0','month':month,
      'source':src,'eligible':ready,
      'counts':{k:{g:cnt[k][g] for g in LABELS} for k in IDS},
      'case_overlap':dict(pair),
      'future_outcomes_read':False,'broker_fills_verified':False,
      'holdouts_opened':False,'new_data':False,'new_five_second_signals':False,
      'PnL':None,'PF':None,'DD':None,'N_trades':None,
      'CI90':None,'p':None,'q':None,'Holm':None}

def diversity(testable,questions,pair,new,old):
    # One interleaved round-robin across ALL 8 mechanism families.
    mem=old['members']+new['members']
    g={b:[z['id'] for z in mem if z['block']==b and z['id'] in testable] for b in BLOCKS}
    order=[]
    while any(g.values()):
        for b in BLOCKS:
            if g[b]:order.append(g[b].pop(0))
    selected=[];dupes={}
    for k in order:
        for j in selected:
            aa,bb=sorted((k,j),key=lambda a:int(a[1:]))
            overlap=pair.get(aa+'__'+bb,0)
            union=questions[k]['N_case']+questions[j]['N_case']-overlap
            jac=overlap/union if union else 1.
            if jac>=.85:
                dupes[k]={'of':j,'jaccard_case':round(jac,6)}
                break
        else:selected.append(k)
    return selected,dupes

def aggregate(months,old,new,seed):
    if set(months)!=set(MONTHS):raise ValueError('REQUIRES_7_DEV_MONTHS')
    cnt={k:Counter() for k in IDS};pair=Counter();src=ready=0;coverage=[]
    for m in MONTHS:
        z=months[m]
        if (z['stage']!='NQ_C133_168_PRIVATE_FREE_D0' or z['month']!=m
            or set(z['counts'])!=set(IDS)
            or any(z[k] is not False for k in ('future_outcomes_read',
             'broker_fills_verified','holdouts_opened','new_data',
             'new_five_second_signals'))
            or any(z[k] is not None for k in ('PnL','PF','DD','N_trades',
              'CI90','p','q','Holm'))):
            raise ValueError('UNSAFE_D0_INTERMEDIATE')
        src+=z['source'];ready+=z['eligible']
        for k in IDS:
            if set(z['counts'][k])!=set(LABELS) or sum(z['counts'][k].values())!=z['eligible']:
                raise AssertionError('36_MEMBER_SESSIONS_NOT_EQUAL')
            cnt[k].update(z['counts'][k])
        pair.update(z['case_overlap'])
        coverage.append({'month':m,'phase':'DIAGNOSTIC' if m in MONTHS[:3]
           else 'INTERNAL_TEMPORAL_SENSITIVITY_NOT_OOS',
          'source':z['source'],'eligible':z['eligible'],
          'case_control':{k:[z['counts'][k][CASE],z['counts'][k][CONTROL]] for k in IDS}})
    if (src,ready)!=(SOURCE,READY):raise AssertionError('NOT_140_135')
    for k in OLD_IDS:
        if any(cnt[k][g]!=seed['case_control_other_missing'][k][g] for g in LABELS):
            raise AssertionError('OLD_20_FROZEN_MASKS_HAVE_CHANGED: '+k)
    q={}
    for z in old['members']+new['members']:
        k=z['id'];v=cnt[k]
        status=('UNIDENTIFIABLE' if not v[CASE] or not v[CONTROL] else
          'LOW_POWER' if min(v[CASE],v[CONTROL])<15 else 'TESTABLE')
        q[k]={'block':z['block'],'question':z['question'],
          'N_case':v[CASE],'N_control':v[CONTROL],
          'N_other':v[OTHER],'N_not_evaluable':v[MISSING],
          'D0':status,'D1':'NOT_STARTED',
          'N_trades':None,'net_PnL':None,'PF':None,'DD':None,'IC90':None,'p':None,'q':None}
    ok=[k for k in IDS if q[k]['D0']=='TESTABLE']
    selected,duplicates=diversity(ok,q,pair,new,old)
    return {'stage':'NQ_C133_168_36_MEMBER_D0_COMPLETE',
      'cohort_id':'NQ-C133-168','family_size':36,'all_ids':list(IDS),
      'additional_prereg_id':new['prereg_id'],
      'seed_action':seed['source_action_run'],
      'seed_20_masks_identical':True,
      'source':src,'eligible':ready,
      'questions':q,'months':coverage,
      'D0_testable_ids':ok,'D0_testable_count':len(ok),
      'D0_diverse_ids':selected,'D0_diverse_count':len(selected),
      'D0_near_duplicates':duplicates,
      'D1_20_gate':len(selected)>=20,
      'D1_executed':False,'D1_economic_prereg_required':True,
      'future_outcomes_read':False,'broker_fills_verified':False,
      'holdouts_opened':False,'new_data':False,'new_five_second_signals':False,
      'N_trades':None,'PnL':None,'PF':None,'DD':None,'p':None,'q_BH':None,'IC90':None}

def report(r):
    s=['# NQ T133–T168 (20+16): cohorte conjunta de 36 estrategias D0',
      '',f"Fuentes {r['source']} y READY {r['eligible']}; 7 Last DEV.",
      '**20 MASKS originales T133–T152 cotejadas y 100% idénticas al congelado.**',
      f"**D0: 36 → {r['D0_testable_count']} TESTABLE → "
      f"{r['D0_diverse_count']} distintas**, "
      f"GATE20 = {'SATISFECHO (SOLO D0)' if r['D1_20_gate'] else 'NO SATISFECHO'}",
      '**D1 NO EJECUTADA**. Economía, p/q BH, DD/PF, fills y PnL N/D.',
      '', '| ID | Bloque | CASE | CONTROL | OTHER | N/D | D0 | Diversa |',
      '|---|---|---:|---:|---:|---:|---|---|']
    sel=set(r['D0_diverse_ids'])
    for k,v in r['questions'].items():
        s.append(f"| {k} | {v['block']} | {v['N_case']} | "
          f"{v['N_control']} | {v['N_other']} | "
          f"{v['N_not_evaluable']} | {v['D0']} | "
          f"{'SÍ' if k in sel else 'NO'} |")
    s+=['',
      'Jaccard calcula intersecciones de CASE a través de los OCHO bloques '
      'y considera los 36 originales, no solo las nuevas 16.',
      'Los meses 2025-10..12 son diagnóstico, 2026-01..04 sensibilidad temporal '
      'interna y nunca nuevo OOS. Sin información económica ni fills.',
      '**D1 requiere prerregistro de la familia COMPLETA k36, costes de '
      'ejecución NQ/MNQ, secuencia adversa, ventanas internas y BH.**',
      'Si D0 falla, nuevos IDs sin retocar ni original ni expansión.','']
    return '\n'.join(s)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path);p.add_argument('--month')
    p.add_argument('--inputs',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path);a=p.parse_args()
    old=old_registry();new=load_new();seed=frozen_seed()
    if a.month:
        if a.month not in MONTHS:raise SystemExit('SEALED_MONTH_BEFORE_IO')
        z=month_stage(a.root,a.month,old,new)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,sort_keys=True)+'\n')
        print('NQ_T133_168_SAFE_D0_MONTH='+json.dumps({
          'month':a.month,'source':z['source'],'eligible':z['eligible'],'futures':False}))
    else:
        if not a.inputs or not a.report:raise ValueError('requires inputs/report')
        z=aggregate({m:json.loads((a.inputs/f't133_t168_d0_{m}.json').read_text())
            for m in MONTHS},old,new,seed)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
        a.report.write_text(report(z))
        print('NQ_T133_168_D0_FINAL='+json.dumps({
           'source':z['source'],'eligible':z['eligible'],
           'registered':36,'testable':z['D0_testable_count'],
           'diverse':z['D0_diverse_count'],'D1_gate':z['D1_20_gate'],
           'shortlist':z['D0_diverse_ids'],'outcomes':False},sort_keys=True))
