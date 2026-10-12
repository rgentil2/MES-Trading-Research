#!/usr/bin/env python3
"""NQ 38-member cohort T59/T60 + T61...T96: SIX NEW G0/D0 mechanism blocks.

D0 is source-only CASE/CONTROL and case-mask overlap. Absolutely no markouts,
N trades, PF, DD, PNL, or market outcome post E; no new historical sources/OOS.
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
from nq_t59_t60_d0_premarket import classify as classify_old,IDS as OLD_IDS
from nq_t61_t96_d0_features import classify_day,CASE,CONTROL,OTHER,MISSING,LABELS

REGISTRY=Path(__file__).resolve().parents[1]/'research/nq/NQ_T61_T96_SIX_BLOCK_D0_FROZEN_2026_10_12.json'
SOURCE,READY=140,135
NEW_IDS=tuple(f'T{i}' for i in range(61,97))
IDS=('T59','T60')+NEW_IDS
OLD_BLOCK='B5_INHERITED_PREMARKET_D0'
EXPECTED_BLOCKS=(
    'B6_PREMARKET_AUCTION','B7_OPENING_TRANSITION',
    'B8_PRIOR_377_CONTEXT','B9_PRINT_SIZE_ALLOCATION',
    'B10_TIME_GROUP_MECHANICS','B11_PRICE_LEVEL_TOPOLOGY')
BLOCKS=(OLD_BLOCK,)+EXPECTED_BLOCKS
NEGATIVE=None

def load_registry(path=REGISTRY):
    data=json.loads(path.read_text())
    rows=data['hypotheses']
    if (data.get('prereg_id')!='NQ-T61-T96-G0-D0-FROZEN-V1'
       or data.get('policy_id')!='NQ-COHORT-FUNNEL-V1'
       or data.get('cohort')!='NQ-C59-NEXT'
       or data.get('family_size')!=36 or len(rows)!=36
       or tuple(x['id'] for x in rows)!=NEW_IDS
       or tuple(data.get('blocks',[]))!=EXPECTED_BLOCKS
       or [sum(z['block']==b for z in rows) for b in EXPECTED_BLOCKS]!=[6]*6
       or len(set(x['feature'] for x in rows))!=36
       or data.get('existing_candidate_member_id')!='T59'
       or data.get('existing_low_power_member_id')!='T60'
       or data.get('future_possible_family_size')!=38
       or data.get('expected_source')!=SOURCE or data.get('expected_ready')!=READY
       or data.get('expected_anchor')!=READY
       or data.get('allowed_months')!=list(MONTHS)
       or data.get('d1_new_batch_min_diverse')!=20
       or data.get('d0_min_case_control')!=15
       or data.get('d0_jaccard_duplicate_cutoff')!=.85
       or any(data[k] is not False for k in ('d1_authorized_now','lookahead',
           'price_signals_from_new_5s','holdouts_opened','new_data_acquired',
           'broker_fills_assumed','outcomes_read'))
       or data.get('all_timestamp_groups_atomic') is not True
       or data.get('no_D1_until_separate_prereg') is not True
       or any(x['CASE']!='feature_vote==side'
               or x['CONTROL']!='feature_vote==-side'
               or x['outcome_observed_in_D0'] is not False for x in rows)):
        raise ValueError('FROZEN_NEW_SIX_BLOCK_D0_REGISTRY_INVALID')
    return data

def month_stage(root,month,registry):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_BEFORE_IO')
    days=sorted(month_days(root,month))
    counts={k:Counter() for k in IDS}
    overlaps=Counter();qc=Counter();anchors=0
    for day in days:
        date=dev_day(day)
        events=list(source_events(file_for(root,date,'Last')))
        status,_,_=frozen_t05(events,day)
        qc[status]+=1
        if status!='READY':continue
        new=classify_day(events,day,registry)
        old=classify_old(events,day)
        labels={'T59':old['T59_PM_BODY_OPPOSITION'],
                'T60':old['T60_PM_VWAP_OPEN_DISLOCATION'],**new}
        if set(labels)!=set(IDS):raise AssertionError('COHORT_FULL_38_UNIVERSE')
        for k,v in labels.items():
            if v not in LABELS:raise ValueError('BAD_D0_LABEL')
            counts[k][v]+=1
        anchors+=1
        cases=[k for k in IDS if labels[k]==CASE]
        for a,b in combinations(cases,2):
            overlaps[a+'__'+b]+=1
    if (sum(qc.values())!=len(days) or anchors!=qc['READY']
        or any(sum(counts[k].values())!=qc['READY'] for k in IDS)):
        raise AssertionError('MONTH_SOURCE_COVERAGE_FAILED')
    return {'stage':'NQ_C59_T96_D0_ONLY','month':month,'source':len(days),
       'eligible':qc['READY'],'anchors':anchors,
       'counts':{k:{x:counts[k][x] for x in LABELS} for k in IDS},
       'case_pair_overlap':dict(overlaps),
       'N_trades':None,'PnL':None,'IC90':None,'p':None,'BH_q':None,
       'Holm':None,'PF':None,'DD':None,'router_delta':None,
       'future_outcomes_computed':False,'holdouts_opened':False,
       'new_history_acquired':False,'new_five_second_signals':False,
       'licensed_rows_exported':False}

def shortlist(eligible,questions,overlap,registry):
    """Round-robin by mechanism block, with frozen numerical IDs within block."""
    groups={b:[] for b in BLOCKS}
    groups[OLD_BLOCK]=[k for k in ('T59','T60') if k in eligible]
    for x in registry['hypotheses']:
        if x['id'] in eligible:groups[x['block']].append(x['id'])
    ordered=[]
    while any(groups.values()):
        for b in BLOCKS:
            if groups[b]:ordered.append(groups[b].pop(0))
    selected=[];dupes={}
    for k in ordered:
        near=None
        for prior in selected:
            a,b=sorted((k,prior),key=lambda x:int(x[1:]))
            inter=overlap.get(a+'__'+b,0)
            union=questions[k]['N_case']+questions[prior]['N_case']-inter
            jacc=inter/union if union else 1.
            if jacc>=.85:
                near={'of':prior,'case_jaccard':round(jacc,6)}
                break
        if near:dupes[k]=near
        else:selected.append(k)
    return selected,dupes

def aggregate(months,registry):
    if set(months)!=set(MONTHS):raise ValueError('MUST_COVER_SEVEN_DEV_MONTHS')
    totals={k:Counter() for k in IDS}
    ov=Counter();src=ready=anchors=0;smonths=[]
    for month in MONTHS:
        x=months[month]
        if (x['stage']!='NQ_C59_T96_D0_ONLY' or x['month']!=month
            or set(x['counts'])!=set(IDS)
            or any(x[k] is not False for k in ('future_outcomes_computed',
                  'holdouts_opened','new_history_acquired','new_five_second_signals',
                  'licensed_rows_exported'))
            or any(x[k] is not None for k in ('N_trades','PnL','IC90','p','BH_q',
                  'Holm','PF','DD','router_delta'))):
            raise ValueError('UNSAFE_INCOMPLETE_MONTH')
        src+=x['source'];ready+=x['eligible'];anchors+=x['anchors']
        for k in IDS:
            if set(x['counts'][k])!=set(LABELS) or sum(x['counts'][k].values())!=x['eligible']:
                raise AssertionError('MISSING_CASE_CONTROL_ON_MONTH')
            totals[k].update(x['counts'][k])
        ov.update(x['case_pair_overlap'])
        smonths.append({'month':month,'source':x['source'],'eligible':x['eligible'],
            'anchors':x['anchors'],'case_control':{
                k:[x['counts'][k][CASE],x['counts'][k][CONTROL]] for k in IDS}})
    if (src,ready,anchors)!=(SOURCE,READY,READY):
        raise AssertionError('BASELINE_140_135_135_CHANGED')
    qs={}
    for k in IDS:
        t=totals[k]
        if sum(t.values())!=READY:raise AssertionError('NOT_ALL_135_CATEGORIZED')
        d0='UNIDENTIFIABLE' if not t[CASE] or not t[CONTROL] else (
           'LOW_POWER' if min(t[CASE],t[CONTROL])<15 else 'TESTABLE')
        block=OLD_BLOCK if k in ('T59','T60') else next(x['block'] for x in registry['hypotheses'] if x['id']==k)
        qs[k]={'block':block,'N_case':t[CASE],'N_control':t[CONTROL],
            'N_other':t[OTHER],'N_not_evaluable':t[MISSING],
            'D0':d0,'D1':'NOT_RUN_NO_OUTCOMES','N_trades':None,'CI90':None,
            'p':None,'q':None,'Holm':None,'PnL':None,'PF':None,'DD':None,
            'router_delta':None}
    if (qs['T59']['N_case'],qs['T59']['N_control'])!=(45,42) or (
        qs['T60']['N_case'],qs['T60']['N_control'])!=(71,6)):
        raise AssertionError('PRIOR_T59_T60_D0_PARITY_BROKEN')
    overlaps={}
    for a,b in combinations(IDS,2):
        both=ov.get(a+'__'+b,0)
        union=qs[a]['N_case']+qs[b]['N_case']-both
        overlaps[a+'__'+b]={'both_case':both,
            'case_jaccard':round(both/union,6) if union else 1.}
    eligible=[k for k in IDS if qs[k]['D0']=='TESTABLE']
    selected,near=shortlist(eligible,qs,ov,registry)
    return {'stage':'NQ_C59_T96_SIX_BLOCKS_D0_DONE_NO_OUTCOMES',
       'policy_id':registry['policy_id'],'cohort_id':registry['cohort'],
       'prereg_id':registry['prereg_id'],'source_sessions':src,
       'eligible_sessions':ready,'anchor_sessions':anchors,'family_size':len(IDS),
       'all_original_ids':list(IDS),'blocks':list(BLOCKS),
       'questions':qs,'months':smonths,'pairwise_case_overlap':overlaps,
       'D0_testable_ids':eligible,'D0_testable_count':len(eligible),
       'D0_diverse_shortlist_ids':selected,'D0_diverse_count':len(selected),
       'near_duplicate_ids':near,'gate_20_satisfied':len(selected)>=20,
       'D1_authorized_now':False,'D1_requires_NEW_frozen_prereg':True,
       'D1_executed':False,'future_outcomes_computed':False,
       'N_trades':None,'PnL':None,'IC90':None,'p':None,'BH_q':None,
       'Holm':None,'PF':None,'DD':None,'router_delta':None,
       'holdouts_opened':False,'new_history_acquired':False,
       'new_five_second_signals':False,'individual_rows_exported':False}

def report(z):
    a=['# C59–C96 — Siete bloques, 38 preguntas completas, D0 únicamente',
       '',f"Fuente {z['source_sessions']}, READY {z['eligible_sessions']}, "
           f"anclas completas {z['anchor_sessions']}. No se midieron futuros.",
       f"**D0 TESTABLE {z['D0_testable_count']}, shortlist diversa "
           f"{z['D0_diverse_count']}**, gate de >=20: "
           f"{'SATISFECHO' if z['gate_20_satisfied'] else 'NO CUMPLE'}.",
       'Las 38 (incluidas T59/T60) pertenecen a una misma futura familia de D1 solo si se PRERREGISTRA por separado.','',
       '| ID | Bloque | CASE | CONTROL | OTHER | NO EVAL | D0 | Diversa? |',
       '|---|---|---:|---:|---:|---:|---|---|']
    chosen=set(z['D0_diverse_shortlist_ids'])
    for k,v in z['questions'].items():
        a.append(f"| {k} | {v['block']} | {v['N_case']} | {v['N_control']} | "
          f"{v['N_other']} | {v['N_not_evaluable']} | {v['D0']} | "
          f"{'SÍ' if k in chosen else 'NO'} |")
    a+=['',f"Duplicados Jaccard≥0,85 excluidos de shortlist: {len(z['near_duplicate_ids'])}.",
        '**No se analizó NINGÚN resultado económico/predictivo**: '
        'N trades, P&L, PF, DD, IC90, p, q, Holm, ROl y router delta = N/D.',
        '**D1 NO EJECUTADO**; si >=20, solo permite nuevo prerregistro familiar '
        'y posterior evaluación como lote, sin invertir votos por conteos.',
        'No se abrió OOS, ni descargó nueva historia, ni construyeron señales 5s.'
        ]
    return '\n'.join(a)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path)
    p.add_argument('--month')
    p.add_argument('--inputs',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    reg=load_registry()
    if a.month:
        if a.month not in MONTHS:raise SystemExit('SEALED_MONTH_BEFORE_IO')
        z=month_stage(a.root,a.month,reg)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n')
        print('NQ_C59_T96_D0_SAFE_MONTH='+json.dumps({
          'month':a.month,'source':z['source'],'eligible':z['eligible'],
          'anchors':z['anchors'],'outcomes':False},sort_keys=True))
    else:
        if a.inputs is None or a.report is None:raise ValueError('missing 7 inputs + report')
        ms={m:json.loads((a.inputs/f't61_t96_d0_{m}.json').read_text())
            for m in MONTHS}
        z=aggregate(ms,reg)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
        a.report.write_text(report(z))
        print('NQ_C59_T96_D0_SAFE_FINAL='+json.dumps({
          'source':z['source_sessions'],'eligible':z['eligible_sessions'],
          'family':z['family_size'],'testable':z['D0_testable_count'],
          'diverse':z['D0_diverse_count'],'gate_20_satisfied':z['gate_20_satisfied'],
          'shortlist':z['D0_diverse_shortlist_ids'],'outcomes':False},sort_keys=True))
