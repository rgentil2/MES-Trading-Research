#!/usr/bin/env python3
"""T26-T28 frozen D0 ONLY: causal group-atomic Last features, NO outcomes/PnL.

Preregistered at research/nq/NQ_T26_T28_G0_D0_NEW_MECHANISMS_PREREG_2026_10_12.md
Never open any month outside the 2025-Oct -> 2026-Apr DEV whitelist.
"""
from __future__ import annotations
import argparse, json
from bisect import bisect_left, bisect_right
from collections import Counter
from fractions import Fraction
from itertools import groupby
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05,et_edge
from nq_b05h_atomic_print_bars import completed_bars_by_print_count

IDS=('T26_PRICE_PATH_CHOP','T27_PRINT_SIZE_PRICE_PREMIUM',
     'T28_ARRIVAL_BURSTINESS')
CASE,CONTROL,OTHER,MISSING='CASE','CONTROL','OTHER','NOT_EVALUABLE'
LABELS=(CASE,CONTROL,OTHER,MISSING)
EXPECTED_SOURCE,EXPECTED_READY=140,135
PREREG='research/nq/NQ_T26_T28_G0_D0_NEW_MECHANISMS_PREREG_2026_10_12.md'


def grouped_atomic(rows):
    """Every timestamp group is an indivisible, permutation-invariant object."""
    groups=[]
    last=None
    for ts,iterrows in groupby(rows,key=lambda x:x[0]):
        batch=list(iterrows)
        if last is not None and ts <= last:
            raise ValueError('NON_MONOTONE_GROUP_TIMESTAMP')
        if any(len(e)!=3 or e[0]!=ts or type(e[1]) is not int or
               type(e[2]) is not int or e[1]<=0 or e[2]<=0 for e in batch):
            raise ValueError('INVALID_LAST_GROUP')
        quantity=sum(e[2] for e in batch)
        groups.append((ts,Fraction(sum(e[1]*e[2] for e in batch),quantity),
                       len(batch),quantity,sum(e[1] for e in batch),
                       sum(e[1]*e[2] for e in batch)))
        last=ts
    return groups


def metrics(rows,bar):
    if not rows or len(rows)!=bar.prints:
        raise AssertionError('ATOMIC_BAR_ROW_PARITY')
    if rows[0][0]!=bar.start_timestamp or rows[-1][0]!=bar.end_timestamp:
        raise AssertionError('BAR_TIME_PARITY')
    gg=grouped_atomic(rows)
    if len(gg)!=bar.whole_timestamp_groups:
        raise AssertionError('BAR_WHOLE_GROUP_COUNT_MISMATCH')
    n=sum(g[2] for g in gg)
    qty=sum(g[3] for g in gg)
    weighted=sum(g[5] for g in gg)
    if n!=bar.prints or qty!=bar.total_qty or weighted!=bar.price_times_qty_ticks:
        raise AssertionError('BAR_VOLUME_AND_PRICE_PARITY')
    path=sum((abs(a[1]-b[1]) for a,b in zip(gg,gg[1:])),Fraction(0))
    width=bar.high_ticks-bar.low_ticks
    gaps=[gg[i][0]-gg[i-1][0] for i in range(1,len(gg))]
    if any(x<=0 for x in gaps):
        raise AssertionError('NON_POSITIVE_TIMESTAMP_GAP')
    mean_print=Fraction(sum(g[4] for g in gg),n)
    vwap=Fraction(weighted,qty)
    cv2=(Fraction(len(gaps)*sum(x*x for x in gaps),sum(gaps)**2)-1
         if gaps else None)
    return {'width':width,'chop':path/width if width>0 and gaps else None,
            'vwap':vwap,'print_mean':mean_print,'cv2':cv2,
            'n_groups':len(gg)}


def classify(d,e):
    result={}
    if d['chop'] is None or e['chop'] is None or d['width']<8 or e['width']<8 or d['chop']<=0:
        result[IDS[0]]=(MISSING,0)
    else:
        x=e['chop']/d['chop']
        result[IDS[0]]=(CASE if x>=Fraction(3,2) else
                         CONTROL if Fraction(4,5)<=x<=Fraction(6,5) else OTHER,0)
    movement=e['vwap']-d['vwap']
    premium=e['vwap']-e['print_mean']
    if abs(movement)<4:
        result[IDS[1]]=(OTHER,0)
    else:
        side=1 if movement>0 else -1
        if abs(premium)>=2 and premium*movement>0:
            result[IDS[1]]=(CASE,side)
        elif abs(premium)<=Fraction(1,2):
            result[IDS[1]]=(CONTROL,side)
        else:
            result[IDS[1]]=(OTHER,0)
    if e['n_groups']<30 or e['cv2'] is None:
        result[IDS[2]]=(MISSING,0)
    else:
        x=e['cv2']
        if x<0:
            raise ValueError('NEGATIVE_CV2_INVALID')
        result[IDS[2]]=(CASE if x>=4 else CONTROL if x<=1 else OTHER,0)
    if set(result)!=set(IDS) or any(g not in LABELS or side not in (-1,0,1)
                                     for g,side in result.values()):
        raise AssertionError('MISSING_OR_INVALID_D0_CLASS')
    return result


def screen_day(events,day):
    """Only two complete 377-print bars ending at or before 10:15 ET."""
    dev_day(day)
    bars=completed_bars_by_print_count(events,day,(377,))[377]
    start,end=et_edge(day,10,0),et_edge(day,10,15)
    anchor=next((i for i,b in enumerate(bars)
                 if start <= b.end_timestamp < end),None)
    if anchor is None or anchor<1:
        raise AssertionError('MISSING_FROZEN_ANCHOR')
    d,e=bars[anchor-1:anchor+1]
    if d.end_timestamp >= e.start_timestamp or d.end_timestamp >= e.end_timestamp:
        raise AssertionError('NONCAUSAL_ADJACENT_BARS')
    times=[r[0] for r in events]
    def segment(bar):
        i=bisect_left(times,bar.start_timestamp)
        j=bisect_right(times,bar.end_timestamp)
        return events[i:j]
    labels=classify(metrics(segment(d),d),metrics(segment(e),e))
    return labels


def month_stage(root,month):
    if month not in MONTHS:
        raise ValueError('SEALED_MONTH_DENIED_BEFORE_IO')
    files=sorted(month_days(root,month))
    source=len(files)
    qc=Counter()
    seen={k:Counter() for k in IDS}
    directions={k:Counter() for k in IDS}
    overlap=Counter()
    anchors=0
    for day in files:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        status,_,_=frozen_t05(events,day)
        qc[status]+=1
        if status!='READY':
            continue
        labels=screen_day(events,day)
        anchors+=1
        cases=[]
        for k,(group,side) in labels.items():
            seen[k][group]+=1
            if group in (CASE,CONTROL):
                directions[k][str(side)]+=1
            if group==CASE:
                cases.append(k)
        for i,k in enumerate(cases):
            for g in cases[i+1:]:
                overlap[k+'__'+g]+=1
    ready=qc['READY']
    if sum(qc.values())!=source or ready!=anchors:
        raise AssertionError('DEV_ANCHOR_OR_COVERAGE_FAIL')
    if any(sum(seen[k].values())!=ready for k in IDS):
        raise AssertionError('D0_MISSING_CLASSIFICATION')
    return {'stage':'G0_D0_ONLY_NO_OUTCOMES','month':month,
            'source':source,'eligible':ready,'anchors':anchors,
            'labels':{k:{g:seen[k][g] for g in LABELS} for k in IDS},
            'sides_by_case_control':{k:dict(directions[k]) for k in IDS},
            'case_overlap':dict(overlap),
            'N_trades':None,'PnL':None,'CI90':None,'BH_q':None,'PF':None,
            'DD':None,'router_delta':None,'future_outcomes_read':False,
            'holdouts_opened':False,'new_market_data_acquired':False,
            'new_five_second_signals':False,'individual_rows_exported':False}


def aggregate(months):
    if set(months)!=set(MONTHS):
        raise ValueError('ALL_SEVEN_DEV_MONTHS_REQUIRED')
    src=eligible=anchors=0
    totals={k:Counter() for k in IDS}
    overlap=Counter()
    details=[]
    for m in MONTHS:
        v=months[m]
        if (v['month']!=m or v['stage']!='G0_D0_ONLY_NO_OUTCOMES'
            or any(v[k] is not False for k in ('future_outcomes_read',
                'holdouts_opened','new_market_data_acquired',
                'new_five_second_signals','individual_rows_exported'))
            or any(v[k] is not None for k in ('N_trades','PnL','CI90','BH_q',
                                              'PF','DD','router_delta'))
            or set(v['labels'])!=set(IDS)):
            raise ValueError('UNSAFE_OR_INCOMPLETE_D0_MONTH')
        src+=v['source'];eligible+=v['eligible'];anchors+=v['anchors']
        for k in IDS:
            if set(v['labels'][k])!=set(LABELS) or sum(v['labels'][k].values())!=v['eligible']:
                raise AssertionError('INVALID_D0_CLASS_COUNTS')
            totals[k].update(v['labels'][k])
        overlap.update(v['case_overlap'])
        details.append({'month':m,'source':v['source'],'eligible':v['eligible'],
                        'anchors':v['anchors'],
                        'cases_controls':{k:[v['labels'][k][CASE],v['labels'][k][CONTROL]]
                                          for k in IDS}})
    if (src,eligible,anchors)!=(EXPECTED_SOURCE,EXPECTED_READY,EXPECTED_READY):
        raise AssertionError('UNEXPECTED_SOURCE_ELIGIBLE_ANCHOR_140_135')
    family={}
    for k in IDS:
        x=totals[k]
        if sum(x.values())!=EXPECTED_READY:
            raise AssertionError('UNBALANCED_D0_LABELS')
        state=('UNIDENTIFIABLE' if not x[CASE] or not x[CONTROL] else
               'LOW_POWER' if min(x[CASE],x[CONTROL])<15 else 'TESTABLE')
        family[k]={'N_case':x[CASE],'N_control':x[CONTROL],
                   'N_other':x[OTHER],'N_not_evaluable':x[MISSING],
                   'N_trades':None,'N_effective':None,'CI90':None,
                   'BH_q':None,'Holm':None,'PF':None,'DD':None,
                   'delta_router':None,'D0':state,
                   'D1':'NOT_RUN_NO_OUTCOMES'}
    return {'stage':'G0_D0_COMPLETE_ONLY_NO_OUTCOMES',
            'policy_id':'NQ-DISCOVERY-STAGED-GATES-V1',
            'source_sessions':src,'eligible_sessions':eligible,
            'anchor_sessions':anchors,'months':details,'questions':family,
            'case_overlap':dict(overlap),'no_outcomes_computed':True,
            'N_trades':None,'N_effective':None,'PnL':None,'CI90':None,
            'p':None,'BH_q':None,'Holm':None,'PF':None,'DD':None,
            'router_delta':None,'holdouts_opened':False,
            'new_data_acquired':False,'individual_rows_exported':False}


def report(summary):
    l=['# NQ T26–T28 — G0/D0 de tres mecanismos nuevos (SOLO VIABILIDAD)','',
       'Política NQ-DISCOVERY-STAGED-GATES-V1. Siete DEV meses 140/135/135.',
       'Fuente Last almacenada + SHA256, barras 377 atomic group. SIN outcomes/PnL.','',
       '| ID | Pregunta | N caso/control | Otros | No evaluable | D0 | IC90/q/PF/DD/Δrouter |',
       '|---|---|---:|---:|---:|---|---|']
    questions={'T26_PRICE_PATH_CHOP':'Recorrido zigzag vs trayectoria estable',
               'T27_PRINT_SIZE_PRICE_PREMIUM':'Prima VWAP−media de prints',
               'T28_ARRIVAL_BURSTINESS':'Irregularidad entre timestamps'}
    for k in IDS:
        a=summary['questions'][k]
        l.append(f"| {k} | {questions[k]} | {a['N_case']}/{a['N_control']} | "
                 f"{a['N_other']} | {a['N_not_evaluable']} | **{a['D0']}** | N/D: no outcomes |")
    l+=['','Caso/control = días categorizados, no trades ni N independiente.',
        'No medir retornos, no abrir OOS ni validar señales para fondeo.',
        'D1 requiere NUEVO prerregistro de outcome y costos/familia ANTES de leer futuro.',
        '']
    return '\n'.join(l)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path)
    p.add_argument('--month')
    p.add_argument('--inputs',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path)
    args=p.parse_args()
    if args.month:
        if args.month not in MONTHS:
            raise SystemExit('SEALED_BEFORE_IO')
        if args.root is None:
            raise ValueError('root required for month')
        z=month_stage(args.root,args.month)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n')
        print('NQ_T26_T28_D0_MONTH='+json.dumps({'month':args.month,
              'source':z['source'],'eligible':z['eligible'],'anchor':z['anchors'],
              'outcomes':False},sort_keys=True))
    else:
        if args.inputs is None or args.report is None:
            raise ValueError('inputs and report required to aggregate')
        months={m:json.loads((args.inputs/f'd0_{m}.json').read_text()) for m in MONTHS}
        z=aggregate(months)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n')
        args.report.write_text(report(z)+'\n')
        print('NQ_T26_T28_D0_FINAL='+json.dumps({'source':z['source_sessions'],
              'eligible':z['eligible_sessions'],'anchors':z['anchor_sessions'],
              'questions':{k:{'case':v['N_case'],'control':v['N_control'],
                              'D0':v['D0']} for k,v in z['questions'].items()},
              'outcomes':False},sort_keys=True))
