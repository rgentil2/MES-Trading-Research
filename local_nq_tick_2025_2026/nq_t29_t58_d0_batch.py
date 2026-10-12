#!/usr/bin/env python3
"""NQ T29-T58: 30 preregistered hypotheses in 5 G0/D0 blocks, NO outcome.

Reports all 30; D1 remains LOCKED until >=20 distinct, diverse TESTABLE
case/control mechanisms; never acquire data or unseal 2026 holdouts.
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
from nq_t29_t58_d0_features import screen_day,CASE,CONTROL,OTHER,MISSING,LABELS

REGISTRY=Path(__file__).resolve().parents[1] / 'research/nq/NQ_T29_T58_30_HYPOTHESES_G0_D0_FROZEN_2026_10_12.json'
SOURCE,READY=140,135
BLOCKS=('B1_BAR_GEOMETRY','B2_MULTI_BAR_CONTEXT','B3_SIZE_VOLUME_STRUCTURE',
        'B4_ARRIVAL_GROUP_SHAPE','B5_PRICE_TOPOLOGY')

def load_registry(path=REGISTRY):
    data=json.loads(path.read_text())
    ids=[z['id'] for z in data['hypotheses']]
    if (data['prereg_id']!='NQ-T29-T58-D0-V1' or
        data['parent_policy_id']!='NQ-DISCOVERY-STAGED-GATES-V1' or
        data['family_size']!=30 or len(ids)!=30 or
        set(ids)!={f'T{i}' for i in range(29,59)} or
        data['block_names']!=list(BLOCKS) or
        [sum(z['block']==b for z in data['hypotheses']) for b in BLOCKS] != [6]*5 or
        data['dev_months']!=list(MONTHS) or
        data['expected_source_days']!=SOURCE or
        data['expected_eligible_days']!=READY or
        data['expected_anchor_days']!=READY or
        data['d1_authorized_now'] is not False or
        data['outcomes_read'] is not False or
        any(data[k] is not False for k in (
          'new_history_acquisition','new_five_second_signals','holdouts_opened')) or
        any(z['comparison']!='E_vs_D_ratio' or z['case_ratio_min']!='11/10' or
            z['control_ratio_max']!='10/11' or z['outcome_read_in_D0'] is not False
            for z in data['hypotheses'])):
        raise ValueError('FROZEN_BATCH_REGISTRY_INVALID_FAIL_CLOSED')
    return data

def month_stage(root,month,registry):
    if month not in MONTHS:
        raise ValueError('SEALED_MONTH_BEFORE_IO')
    days=sorted(month_days(root,month))
    counts={z['id']:Counter() for z in registry['hypotheses']}
    overlaps=Counter()
    qc=Counter()
    anchor=0
    ids=list(counts)
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        state,_,_=frozen_t05(events,day)
        qc[state]+=1
        if state!='READY':
            continue
        classifications=screen_day(events,day,registry)
        if set(classifications)!=set(ids):
            raise AssertionError('ALL_30_D0_LABELS_REQUIRED')
        anchor+=1
        for k,g in classifications.items():
            if g not in LABELS:raise ValueError('ILLEGAL_D0_LABEL')
            counts[k][g]+=1
        cases=[k for k in ids if classifications[k]==CASE]
        for a,b in combinations(cases,2):
            overlaps[a+'__'+b]+=1
    source=len(days)
    eligible=qc['READY']
    if anchor!=eligible or sum(qc.values())!=source or (
        any(sum(counts[k].values())!=eligible for k in ids)):
        raise AssertionError('MONTH_QC_COUNTER_RECONCILIATION')
    return {'stage':'T29_T58_G0_D0_NO_OUTCOMES',
            'month':month,'source':source,'eligible':eligible,'anchors':anchor,
            'counts':{k:{g:counts[k][g] for g in LABELS} for k in ids},
            'case_pair_overlap':dict(overlaps),
            'N_trades':None,'PnL':None,'IC90':None,'p':None,'BH_q':None,
            'Holm':None,'PF':None,'DD':None,'router_delta':None,
            'future_outcomes_computed':False,'holdouts_opened':False,
            'new_history_acquired':False,'new_five_second_signals':False,
            'licensed_rows_exported':False}

def diverse_shortlist(candidates,full,overlap,registry):
    """Deterministic block round-robin; near-identical CASE masks do not count."""
    rows=registry['hypotheses']
    pool={b:[z['id'] for z in rows if z['block']==b and z['id'] in candidates]
          for b in BLOCKS}
    ordered=[]
    while any(pool.values()):
        for b in BLOCKS:
            if pool[b]:ordered.append(pool[b].pop(0))
    selected=[];rejected={}
    for k in ordered:
        similar=None
        for prior in selected:
            a,b=sorted((prior,k),key=lambda s:int(s[1:]))
            inter=overlap.get(a+'__'+b,0)
            union=full[prior]['N_case']+full[k]['N_case']-inter
            j=inter/union if union else 1.
            if j>=.85:
                similar=(prior,round(j,6))
                break
        if similar:
            rejected[k]={'near_duplicate_of':similar[0],'case_jaccard':similar[1]}
        else:selected.append(k)
    return selected,rejected

def aggregate(months,registry):
    if set(months)!=set(MONTHS):
        raise ValueError('EXACT_SEVEN_MONTHS_REQUIRED')
    ids=[z['id'] for z in registry['hypotheses']]
    totals={k:Counter() for k in ids}
    overlap=Counter()
    src=ready=anch=0
    safe_month=[]
    for m in MONTHS:
        z=months[m]
        if z['stage']!='T29_T58_G0_D0_NO_OUTCOMES' or z['month']!=m or (
            any(z[k] is not False for k in ('future_outcomes_computed',
                 'holdouts_opened','new_history_acquired','new_five_second_signals',
                 'licensed_rows_exported')) or
            any(z[k] is not None for k in ('N_trades','PnL','IC90','p','BH_q',
                 'Holm','PF','DD','router_delta')) or
            set(z['counts'])!=set(ids)):
            raise ValueError('D0_MONTH_IS_UNSAFE_OR_INCOMPLETE')
        src+=z['source'];ready+=z['eligible'];anch+=z['anchors']
        for k in ids:
            if set(z['counts'][k])!=set(LABELS) or sum(z['counts'][k].values())!=z['eligible']:
                raise AssertionError('MONTH_LABEL_COVERAGE_FAIL_CLOSED')
            totals[k].update(z['counts'][k])
        overlap.update(z['case_pair_overlap'])
        safe_month.append({'month':m,'source':z['source'],'eligible':z['eligible'],
          'anchors':z['anchors'],
          'counts_case_control':{k:[z['counts'][k][CASE],z['counts'][k][CONTROL]]
                                 for k in ids}})
    if (src,ready,anch)!=(SOURCE,READY,READY):
        raise AssertionError('EXPECTED_140_135_135_COVERAGE_FAIL')
    questions={}
    for row in registry['hypotheses']:
        k=row['id'];cnt=totals[k]
        if sum(cnt.values())!=READY:
            raise AssertionError('FAMILY_FULL_D0_COVERAGE')
        status=('UNIDENTIFIABLE' if not cnt[CASE] or not cnt[CONTROL] else
                'LOW_POWER' if min(cnt[CASE],cnt[CONTROL])<15 else 'TESTABLE')
        questions[k]={
          'block':row['block'],'question':row['question'],
          'feature':row['feature'],'N_case':cnt[CASE],
          'N_control':cnt[CONTROL],'N_other':cnt[OTHER],
          'N_not_evaluable':cnt[MISSING],'N_sessions':READY,
          'N_effective':None,'N_trades':None,'CI90':None,'p':None,
          'BH_q':None,'Holm':None,'PF':None,'DD':None,
          'router_delta':None,'D0':status,'D1':'NOT_RUN'}
    overlap_table={}
    alerts=[]
    for a,b in combinations(ids,2):
        inter=overlap[a+'__'+b]
        union=questions[a]['N_case']+questions[b]['N_case']-inter
        j=inter/union if union else 1.
        overlap_table[a+'__'+b]={'both_cases':inter,
              'case_jaccard':round(j,6)}
        if j>=.85:
            alerts.append({'a':a,'b':b,'jaccard':round(j,6),
                           'exact_case_masks':inter==questions[a]['N_case']==
                                              questions[b]['N_case']})
    eligible=[k for k in ids if questions[k]['D0']=='TESTABLE']
    shortlist,duplicates=diverse_shortlist(eligible,questions,overlap,registry)
    next_locked=len(shortlist)<registry['min_diversified_TESTABLE_before_D1']
    return {'stage':'T29_T58_FIVE_BLOCKS_G0_D0_FINAL_NO_OUTCOMES',
        'policy_id':registry['parent_policy_id'],
        'prereg_id':registry['prereg_id'],'source_sessions':src,
        'eligible_sessions':ready,'anchor_sessions':anch,
        'family_size':len(ids),'blocks':list(BLOCKS),
        'questions':questions,'month_counts':safe_month,
        'case_pair_overlap':overlap_table,'near_duplicate_case_mask_alerts':alerts,
        'D0_testable_count':len(eligible),
        'D0_testable_ids':eligible,'D0_distinct_diverse_count':len(shortlist),
        'D0_diverse_shortlist_ids':shortlist,
        'excluded_for_near_duplicate_case_masks':duplicates,
        'D1_20_candidate_gate_satisfied':not next_locked,
        'D1_still_requires_separate_prereg':True,
        'D1_executed':False,'market_outcomes_computed':False,
        'N_trades':None,'PnL':None,'CI90':None,'p':None,
        'BH_q':None,'Holm':None,'PF':None,'DD':None,'router_delta':None,
        'holdouts_opened':False,'new_history_acquired':False,
        'individual_rows_exported':False}

def report(z):
    s=['# T29–T58 — 30 preguntas de cinco bloques, G0/D0 SIN OUTCOMES','',
       f"Fuente={z['source_sessions']} READY={z['eligible_sessions']} "
       f"anclas={z['anchor_sessions']}; 7 meses exactos DEV; 0 nuevas fuentes.",
       f"TESTABLE={z['D0_testable_count']}, diversificadas (Jaccard<0,85)="
       f"{z['D0_distinct_diverse_count']}; objetivo >=20: "
       f"{'ALCANZADO' if z['D1_20_candidate_gate_satisfied'] else 'NO ALCANZADO'}.",
       'N trades, neto, PF/DD/IC90/p/q/Holm/DeltaRouter = N/D sin futuros.','',
       '| ID | Bloque | Pregunta causal | N case/control | OTHER/MISSING | D0 | Diversa? |',
       '|---|---|---|---:|---:|---|---|']
    selected=set(z['D0_diverse_shortlist_ids'])
    for id_,x in z['questions'].items():
        s.append(f"| {id_} | {x['block']} | {x['question']} | "
                 f"{x['N_case']}/{x['N_control']} | "
                 f"{x['N_other']}/{x['N_not_evaluable']} | "
                 f"**{x['D0']}** | {'Sí' if id_ in selected else 'No'} |")
    s+=['',f"Alertas pares Jaccard>=0,85: {len(z['near_duplicate_case_mask_alerts'])}.",
        f"Mascaras redundantes descartadas de shortlist: "
        f"{len(z['excluded_for_near_duplicate_case_masks'])}.",
        'D1 permanece sin ejecutar. Si <20 diversas, preregistrar nuevas preguntas',
        'y repetir D0 SIN cambiar umbrales o excluir las 30 preguntas observadas.',
        'IC90/q en D0 nunca se calculan ni se imputan ceros.']
    return '\n'.join(s)+'\n'

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path)
    ap.add_argument('--month')
    ap.add_argument('--inputs',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--report',type=Path)
    a=ap.parse_args()
    registry=load_registry()
    if a.month is not None:
        if a.month not in MONTHS:
            raise SystemExit('SEALED_MONTH_BEFORE_IO')
        z=month_stage(a.root,a.month,registry)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n')
        print('T29_T58_D0_SAFE_MONTH='+json.dumps({
          'month':a.month,'source':z['source'],'eligible':z['eligible'],
          'anchors':z['anchors'],'future_outcomes':False},sort_keys=True))
    else:
        if a.inputs is None or a.report is None:
            raise ValueError('requires inputs and report')
        months={m:json.loads((a.inputs/f't29_t58_d0_{m}.json').read_text())
                for m in MONTHS}
        summary=aggregate(months,registry)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
        a.report.write_text(report(summary))
        print('T29_T58_D0_SAFE_FINAL='+json.dumps({
          'source':summary['source_sessions'],
          'eligible':summary['eligible_sessions'],
          'family':summary['family_size'],
          'testable':summary['D0_testable_count'],
          'diverse':summary['D0_distinct_diverse_count'],
          'gate_20_satisfied':summary['D1_20_candidate_gate_satisfied'],
          'shortlist':summary['D0_diverse_shortlist_ids'],
          'outcomes':False},sort_keys=True))
