#!/usr/bin/env python3
"""T133–T152 D0 whole-cohort runner. No future/markout/trading from Last.

Only 7 existing DEV months and prereg 20 members. D0 count includes CASE,
CONTROL, OTHER, NOT_EVALUABLE and overlap of causal opportunity masks.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from itertools import combinations
from pathlib import Path
from datetime import date

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05
from nq_t133_t152_executable_d0_features import (
    classify_day,LABELS,CASE,CONTROL,OTHER,MISSING,NAMES)

REGISTRY=Path(__file__).resolve().parents[1]/'research/nq/NQ_T133_T152_EXECUTABLE_D0_PREREG_2026_10_12.json'
IDS=tuple(f'T{x}' for x in range(133,153))
BLOCKS=('A_BREAKOUT_RETEST','B_PULLBACK_CONTINUATION',
        'C_FALSE_BREAK_REVERSAL','D_REGIME_RISK_ROUTER')
SOURCE,READY=140,135

def load_registry(path=REGISTRY):
    x=json.loads(path.read_text());rows=x['members']
    if (x.get('prereg_id')!='NQ-T133-T152-EXECUTABLE-STRATEGIES-D0-V1'
        or x.get('policy_id')!='NQ-COHORT-FUNNEL-V1'
        or x.get('cohort_id')!='NQ-C133-152'
        or x.get('family_original_size')!=20 or len(rows)!=20
        or tuple(y['id'] for y in rows)!=IDS
        or tuple(y['feature'] for y in rows)!=NAMES
        or tuple(x.get('blocks',[]))!=BLOCKS
        or [sum(z['block']==block for z in rows) for block in BLOCKS]!=[5]*4
        or x.get('source_dev_months')!=list(MONTHS)
        or (x.get('source_sessions_expected'),x.get('eligible_sessions_expected'))!=(SOURCE,READY)
        or x.get('D0_case_min')!=15 or x.get('D0_control_min')!=15
        or x.get('D1_min_diverse_testable')!=20
        or x.get('jaccard_cutoff')!=.85
        or x.get('minimum_stop_ticks')!=8
        or x.get('maximum_stop_ticks_for_MNQ')!=400
        or x.get('max_risk_usd_per_hypothetical_trade')!=250
        or x.get('stop_padding_ticks')!=1
        or x.get('D1_status')!='LOCKED_UNTIL_D0_PASS_AND_NEW_PRE_REGISTERED_ECONOMIC_D1'
        or x.get('chronological_check_is_independent_OOS') is not False
        or x.get('development_months')!=list(MONTHS[:3])
        or x.get('chronological_sensitivity_months')!=list(MONTHS[3:])
        or any(x[z] is not False for z in ('D0_may_read_future',
              'broker_fills_verified','new_market_data','holdouts_opened','no_retuning') if z!='no_retuning')
        or x.get('no_retuning') is not True
        or x.get('no_5_second_signals') is not True
        or x.get('atomic_timestamp_groups') is not True
        or x.get('no_competing_orders_same_account') is not True
        or any(z['CASE']!='PREREGISTERED_TRIGGER_AND_DEFINED_CAUSAL_STOP_RISK_OK'
           or z['CONTROL']!='REFERENCE_DEFINED_BUT_NO_TRIGGER'
           or z['outcomes_observed_in_D0'] is not False
           or z['entry']!='MARKET_HYPOTHETICAL_NEXT_ATOMIC_LAST_GROUP_AFTER_ANCHOR_UNVERIFIED'
           or z['max_trades_per_day']!=1
           for z in rows)):
        raise ValueError('20_COMPLETE_STRATEGIES_FROZEN_REGISTRY_VIOLATION')
    return x

def month_stage(root,month,registry):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_BEFORE_IO')
    counts={k:Counter() for k in IDS};weeks={k:set() for k in IDS}
    pairs=Counter();qc=Counter();source=0;ready=0
    for day in sorted(month_days(root,month)):
        d=dev_day(day);source+=1
        events=list(source_events(file_for(root,d,'Last')))
        status,_,_=frozen_t05(events,day)
        qc[status]+=1
        if status!='READY':continue
        labels=classify_day(events,day,registry)
        if set(labels)!=set(IDS):raise AssertionError('ALL20_D0_REQUIRED')
        for k,label in labels.items():
            if label not in LABELS:raise ValueError('INVALID_CATEGORY')
            counts[k][label]+=1
            if label==CASE:
                iso=date.fromisoformat(day).isocalendar()
                weeks[k].add((iso.year,iso.week))
        cases=[k for k in IDS if labels[k]==CASE]
        for a,b in combinations(cases,2):pairs[a+'__'+b]+=1
        ready+=1
    if sum(qc.values())!=source or qc['READY']!=ready or (
            any(sum(counts[k].values())!=ready for k in IDS)):
        raise AssertionError('SOURCE_COUNT_OR_FAMILY_MISMATCH')
    return {'stage':'T133_T152_D0_NO_FUTURE',
      'month':month,'source':source,'eligible':ready,
      'counts':{k:{v:counts[k][v] for v in LABELS} for k in IDS},
      'case_week_count_in_month':{k:len(weeks[k]) for k in IDS},
      'case_pair_overlap':dict(pairs),
      'future_read':False,'broker_fills_verified':False,
      'licensed_rows_exported':False,'holdouts_opened':False,
      'new_data_acquired':False,'new_5s_signals':False,
      'N_trades':None,'PNL':None,'PF':None,'DD':None,
      'IC90':None,'p':None,'q':None,'Holm':None,
      'cost_realized':None,'ROI':None}

def diversity(testable,questions,pairs,registry):
    groups={b:[x['id'] for x in registry['members']
               if x['block']==b and x['id'] in testable] for b in BLOCKS}
    ordered=[]
    while any(groups.values()):
        for b in BLOCKS:
            if groups[b]:ordered.append(groups[b].pop(0))
    selected=[];dupes={}
    for k in ordered:
        found=None
        for p in selected:
            a,b=sorted((k,p),key=lambda x:int(x[1:]))
            intersection=pairs.get(a+'__'+b,0)
            union=questions[k]['N_case']+questions[p]['N_case']-intersection
            j=intersection/union if union else 1.
            if j>=registry['jaccard_cutoff']:
                found={'of':p,'jaccard_case':round(j,6)}
                break
        if found:dupes[k]=found
        else:selected.append(k)
    return selected,dupes

def aggregate(months,registry):
    if set(months)!=set(MONTHS):raise ValueError('REQUIRE_ALL_7_DEV_MONTHS')
    counts={k:Counter() for k in IDS};pair=Counter();source=ready=0;summ=[]
    for m in MONTHS:
        x=months[m]
        if (x.get('stage')!='T133_T152_D0_NO_FUTURE'
            or x.get('month')!=m
            or set(x.get('counts',{}))!=set(IDS)
            or any(x[k] is not False for k in ('future_read',
              'broker_fills_verified','licensed_rows_exported',
              'holdouts_opened','new_data_acquired','new_5s_signals'))
            or any(x[k] is not None for k in ('N_trades','PNL','PF','DD',
              'IC90','p','q','Holm','cost_realized','ROI'))):
            raise ValueError('UNSAFE_OR_INCOMPLETE_MONTH_DATA')
        source+=x['source'];ready+=x['eligible']
        for k in IDS:
            y=x['counts'][k]
            if set(y)!=set(LABELS) or sum(y.values())!=x['eligible']:
                raise AssertionError('INCOMPLETE_D0_LABELS')
            counts[k].update(y)
        pair.update(x['case_pair_overlap'])
        summ.append({'month':m,'segment':'DIAGNOSTIC' if m in MONTHS[:3]
             else 'CHRONOLOGICAL_SENSITIVITY_NOT_OOS',
             'source':x['source'],'eligible':x['eligible'],
             'case_control':{k:[x['counts'][k][CASE],x['counts'][k][CONTROL]]
                  for k in IDS},
             'case_week_count_within_month':x['case_week_count_in_month']})
    if (source,ready)!=(SOURCE,READY):raise AssertionError('BASELINE_140_135_CHANGED')
    qs={}
    for member in registry['members']:
        k=member['id'];x=counts[k]
        if sum(x.values())!=READY:raise AssertionError('ID_NOT_135_DAYS')
        status=('UNIDENTIFIABLE' if not x[CASE] or not x[CONTROL] else
                'LOW_POWER' if min(x[CASE],x[CONTROL])<15 else 'TESTABLE')
        qs[k]={'question':member['question'],'block':member['block'],
         'entry':member['entry'],'stop_rule':member['stop_rule'],
         'target_R':member['take_profit_R'],
         'time_stop_minutes':member['max_minutes'],
         'N_case':x[CASE],'N_control':x[CONTROL],
         'N_other':x[OTHER],'N_not_evaluable':x[MISSING],
         'N_sessions':READY,'N_weeks_distinct_exact':None,
         'N_trades_actual':None,'N_trades_simulated':None,
         'D0':status,'D1':'NOT_STARTED','D2':'NOT_STARTED',
         'CI90':None,'p':None,'q':None,'Holm':None,
         'PNL':None,'PF':None,'DD':None,'DeltaRouter':None}
    eligible=[k for k in IDS if qs[k]['D0']=='TESTABLE']
    shortlist,duplicates=diversity(eligible,qs,pair,registry)
    return {'stage':'T133_T152_D0_COMPLETE_NO_FUTURES',
      'cohort_id':registry['cohort_id'],'prereg_id':registry['prereg_id'],
      'family_original_size':len(IDS),'all_original_ids':list(IDS),
      'source_sessions':source,'eligible_sessions':ready,
      'questions':qs,'months':summ,'case_pair_overlap':dict(pair),
      'D0_testable_ids':eligible,'D0_testable_count':len(eligible),
      'D0_diverse_shortlist_ids':shortlist,
      'D0_diverse_count':len(shortlist),'D0_near_duplicates':duplicates,
      'D1_20_diverse_gate_satisfied':len(shortlist)>=20,
      'D1_executed':False,'D1_unregistered_economics':True,
      'future_outcomes_read':False,'actual_trades_computed':False,
      'broker_fills_verified':False,'holdouts_opened':False,
      'new_data_acquired':False,'new_5s_signals':False,
      'PNL':None,'PF':None,'DD':None,'q_BH':None,'Holm':None}

def report(z):
    lines=['# NQ T133–T152 — 20 estrategias COMPLETAS, G0/D0 SIN resultados futuros',
      '',f"Fuente: {z['source_sessions']} sesiones; DEV READY: {z['eligible_sessions']}. "
      '7 archivos Last existentes, sin nuevos datos, 5 segundos ni holdouts.',
      f"**D0 TESTABLE: {z['D0_testable_count']} /20; D0 diversas: "
      f"{z['D0_diverse_count']} /20**. Gate D1= "
      f"{'ALCANZADO (PERO REQUIERE PRERREGISTRO D1 SEPARADO)' if z['D1_20_diverse_gate_satisfied'] else 'BLOQUEADO; NO CORRER D1'}",
      'CASE=trigger causal activado Y distancia riesgo ≤ límite; '
      'CONTROL=estado conocido sin trigger, OTHER=ambiguo/filtro riesgo, '
      'NO EVAL=referencia/print bar ausente.','',
      '| ID | Bloque | Pregunta | R objetivo | Time stop | N_CASE | N_CTRL | OTHER | NO_EVAL | D0 | Diversa |',
      '|---|---|---|---:|---:|---:|---:|---:|---|---|']
    s=set(z['D0_diverse_shortlist_ids'])
    for k,v in z['questions'].items():
        lines.append(f"| {k} | {v['block']} | {v['question']} | {v['target_R']} | "
           f"{v['time_stop_minutes']}m | {v['N_case']} | {v['N_control']} | "
           f"{v['N_other']} | {v['N_not_evaluable']} | {v['D0']} | "
           f"{'SÍ' if k in s else 'NO'} |")
    lines.extend(['',f"Máscaras duplicadas Jaccard≥0,85: {len(z['D0_near_duplicates'])}.",
      '**Oct–dic 2025 diseño/diagnóstico, ene–abr 2026 examen cronológico '
      'interno DEV REUTILIZADA (NO OOS):** tabla separada de N por mes '
      'disponible en el JSON del artifact SAFE; no se analizaron retornos.',
      '**Nada medido en D0:** PNL, PF, DD, trades efectivos, broker fills, '
      'IC90, p, BH, Holm y ROI = N/D (NO cero). Stop/TP y riesgo solamente '
      'son reglas predefinidas; referencia VWAP Last NO es fill negociable.',
      '**Si menos de 20 distintas TESTABLE, D1 prohibida**. No ajustar '
      'umbral o rescatar una señal particular.', ''])
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path)
    p.add_argument('--month')
    p.add_argument('--inputs',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path)
    a=p.parse_args();r=load_registry()
    if a.month:
        if a.month not in MONTHS:raise SystemExit('SEALED_MONTH_BEFORE_IO')
        data=month_stage(a.root,a.month,r)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
        print('NQ_T133_T152_D0_SAFE_MONTH='+json.dumps({
           'month':a.month,'source':data['source'],'eligible':data['eligible'],
           'future_outcomes':False},sort_keys=True))
    else:
        if not a.inputs or not a.report:raise ValueError('missing month inputs/report')
        data=aggregate({m:json.loads((a.inputs/f't133_t152_d0_{m}.json').read_text())
           for m in MONTHS},r)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
        a.report.write_text(report(data)+'\n')
        print('NQ_T133_T152_D0_SAFE_FINAL='+json.dumps({
          'source':data['source_sessions'],'eligible':data['eligible_sessions'],
          'family':20,'testable':data['D0_testable_count'],
          'diverse':data['D0_diverse_count'],
          'D1_gate':data['D1_20_diverse_gate_satisfied'],
          'shortlist':data['D0_diverse_shortlist_ids'],
          'outcomes':False,'PNL':None},sort_keys=True))
