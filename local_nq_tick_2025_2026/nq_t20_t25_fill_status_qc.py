#!/usr/bin/env python3
"""Only technical execution STATUS of six frozen stage0 hypotheses, no PnL.
Standalone first-anchor simulation, NOT a verified broker fill or shared router.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from itertools import islice
from bisect import bisect_right
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05
from nq_t20_t25_economic_month import (
    IDS,MAG,DIRECTIONAL,SCREEN_COUNTS,first_decision,policy)
from nq_t20_t25_fixed_anchor_screen import CASE,CONTROL,OTHER,MISSING
from sim_nq_last_execution_skeleton import Signal,simulate_single_trade

STATES=('SYNTHETIC_FILL_MODEL_ONLY','ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',
    'UNRESOLVED_END_OF_LAST_DATA','NO_ENTRY_BEFORE_SESSION_CUTOFF','NO_ENTRY_EVENT',
    'CONTROL_WITHOUT_DIRECTION','NO_TRADE_MODEL_MAGNITUDE')
GROUPS=(CASE,CONTROL)


def month_stage(root,month):
    if month not in MONTHS:
        raise ValueError('SEALED_MONTH_DENIED_BEFORE_IO')
    qc=Counter()
    seen={k:Counter() for k in IDS}
    results={k:{g:Counter() for g in GROUPS} for k in IDS}
    source=0
    for day in sorted(month_days(root,month)):
        dev_day(day)
        source+=1
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        eligible,oldbars,_=frozen_t05(events,day)
        qc[eligible]+=1
        if eligible!='READY':
            continue
        labels,tm=first_decision(events,day)
        if tm is None:
            raise AssertionError('missing prereg 10:00 anchor')
        times=[e[0] for e in events]
        for k,(kind,side) in labels.items():
            seen[k][kind]+=1
            if kind not in GROUPS:
                continue
            if k==MAG:
                state='NO_TRADE_MODEL_MAGNITUDE'
            elif side==0:
                if kind!=CONTROL:
                    raise AssertionError('case with missing direction')
                state='CONTROL_WITHOUT_DIRECTION'
            else:
                pol=policy(k,oldbars)
                row=simulate_single_trade(islice(events,bisect_right(times,tm),None),
                      Signal(day,tm,side),pol)
                state=row['status']
                if state not in STATES:
                    raise ValueError('UNREGISTERED_LAST_SIM_STATUS')
                # Explicitly discard all price, PnL, fill and trade details.
                del row
            results[k][kind][state]+=1
    n=qc['READY']
    if sum(qc.values())!=source:
        raise AssertionError('QC coverage missing')
    for k in IDS:
        if sum(seen[k].values())!=n:
            raise AssertionError('QC missing/extra category')
        for g in GROUPS:
            if sum(results[k][g].values())!=seen[k][g]:
                raise AssertionError('status sum != observed label count')
    return {'status':'T20_T25_FILL_STATUS_DIAGNOSTIC_ONLY',
       'month':month,'source':source,'eligible':n,
       'by_question':{k:{
           'labels':{g:seen[k][g] for g in (CASE,CONTROL,OTHER,MISSING)},
           'status_by_group':{g:{state:results[k][g][state] for state in STATES}
                              for g in GROUPS}} for k in IDS},
       'PnL_computed_for_reporting':False,'fill_prices_exported':False,
       'trade_rows_exported':False,'holdouts_opened':False,
       'new_history_acquired':False,'new_5second_signals':False,
       'shared_router_reconstructed':False}

def aggregate(months):
    if set(months)!=set(MONTHS):
        raise ValueError('require EXACT seven existing DEV months')
    sums={k:{g:Counter() for g in GROUPS} for k in IDS}
    labels={k:Counter() for k in IDS}
    total=eligible=0
    report=[]
    for m in MONTHS:
        a=months[m]
        if (a['status']!='T20_T25_FILL_STATUS_DIAGNOSTIC_ONLY' or
            a['month']!=m or set(a['by_question'])!=set(IDS) or
            any(a[z] is not False for z in ('PnL_computed_for_reporting',
                'fill_prices_exported','trade_rows_exported','holdouts_opened',
                'new_history_acquired','new_5second_signals','shared_router_reconstructed'))):
            raise ValueError('unsafe or incomplete month')
        total+=a['source'];eligible+=a['eligible']
        row={'month':m,'source':a['source'],'eligible':a['eligible']}
        for k in IDS:
            x=a['by_question'][k]
            if set(x['labels'])!={CASE,CONTROL,OTHER,MISSING} or set(x['status_by_group'])!=set(GROUPS):
                raise ValueError('missing classification/controls')
            labels[k].update(x['labels'])
            row[k]={'case':x['labels'][CASE],'control':x['labels'][CONTROL]}
            for g in GROUPS:
                if set(x['status_by_group'][g])!=set(STATES):
                    raise ValueError('unlisted simulator state')
                z=x['status_by_group'][g]
                if any(type(n) is not int or n<0 for n in z.values()) or sum(z.values())!=x['labels'][g]:
                    raise ValueError('unreconciled simulator statuses')
                sums[k][g].update(z)
        report.append(row)
    if (total,eligible)!=(140,135):
        raise AssertionError('baseline source/eligibility changed')
    for k in IDS:
        if (labels[k][CASE],labels[k][CONTROL])!=SCREEN_COUNTS[k]:
            raise AssertionError('stage0 fixed case/control altered')
        if labels[k][MISSING]:
            raise AssertionError('all 135 stage0 anchor sessions required')
    return {'status':'T20_T25_FULL_DEV_EXECUTION_STATUS_DIAGNOSTIC_NO_ALPHA',
        'source_days':total,'eligible_days':eligible,
        'by_question':{k:{
           'N_case':labels[k][CASE],'N_control':labels[k][CONTROL],
           'statuses':{g:{state:sums[k][g][state] for state in STATES}
                       for g in GROUPS}}
                       for k in IDS},
        'months':report,'pnl_or_return_effect':None,
        'CI90':None,'BH_q':None,'PF':None,'DD':None,
        'broker_fill_validated':False,'holdouts_opened':False,
        'new_history_acquired':False,'shared_router_reconstructed':False,
        'individual_rows_exported':False}

def report(x):
    l=['# NQ T20–T25 — QC técnico estados del simulador Last (SIN P&L)',
       '',
       'Simulaciones standalone solo en primera ancla fija. NO son fills de broker,',
       'no validan la cartera compartida ni resuelven el bloqueo económico original.',
       '',
       '| Hipótesis | N caso/control | Caso: modelo Last / ambiguas / no entrada | Control: modelo Last / ambiguas / no entrada | Estado |',
       '|---|---:|---:|---:|---|']
    for k in IDS:
        v=x['by_question'][k]
        def summ(g):
            s=v['statuses'][g]
            return f"{s['SYNTHETIC_FILL_MODEL_ONLY']} / {s['ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS']+s['UNRESOLVED_END_OF_LAST_DATA']} / {s['NO_ENTRY_EVENT']+s['NO_ENTRY_BEFORE_SESSION_CUTOFF']}"
        l.append(f"| {k} | {v['N_case']}/{v['N_control']} | {summ(CASE)} | {summ(CONTROL)} | "
                 +('NO DIRECCIONAL; no simulada' if k==MAG else 'STATUS ONLY, NO ALPHA')+' |')
    l+=['','Categorías completas adicionales side0 por control y N/D disponibles en summary.json.',
        'En cada grupo el total estados debe ser igual a N caso o N control.',
        'No se han reportado retornos, netos, fill price, equity, fechas ni timestamps.',
        'Aun sin ambigüedades standalone, el router T05 requiere resolver su bloqueo',
        'por documentación independiente; NO asumir rentabilidad ni eliminar señales.',
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
        out=month_stage(args.root,args.month)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
        print('NQ_T20_T25_QC_MONTH='+json.dumps({'month':args.month,
              'source':out['source'],'eligible':out['eligible'],
              'no_economics':True},sort_keys=True))
    else:
        months={m:json.loads((args.inputs/f't20_t25_qc_{m}.json').read_text())
                for m in MONTHS}
        a=aggregate(months)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(a,sort_keys=True,indent=2)+'\n')
        args.report.write_text(report(a)+'\n')
        print('NQ_T20_T25_QC_FINAL='+json.dumps({
             'source':a['source_days'],'eligible':a['eligible_days'],
             'by_question':{k:{
                'case_ambiguous':sum(a['by_question'][k]['statuses'][CASE][s]
                        for s in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS','UNRESOLVED_END_OF_LAST_DATA')),
                'control_ambiguous':sum(a['by_question'][k]['statuses'][CONTROL][s]
                        for s in ('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS','UNRESOLVED_END_OF_LAST_DATA'))}
                         for k in IDS},
             'no_pnl':True},sort_keys=True))
