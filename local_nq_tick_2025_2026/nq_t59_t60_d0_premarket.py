#!/usr/bin/env python3
"""T59/T60 NEW historical-H-inspired mechanisms, G0/D0 ONLY.

Only completed whole-timestamp Last groups and timestamps <09:45 ET.
Pre-registered NQ_T59_T60_LEGACY_MECHANISM_ADAPTATION_D0_PREREG_2026_10_12.md.
NOT legacy H77/H69, NO trading/future outcome, no reserved data.
"""
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

IDS=('T59_PM_BODY_OPPOSITION','T60_PM_VWAP_OPEN_DISLOCATION')
LABELS=('CASE','CONTROL','OTHER','NOT_EVALUABLE')
CASE,CONTROL,OTHER,MISSING=LABELS

def v(x):
    if not x or any(a[1]<=0 or a[2]<=0 for a in x):
        raise ValueError('INVALID_LAST_GROUP')
    return Fraction(sum(z[1]*z[2] for z in x),sum(z[2] for z in x))

def segment_stats(events,start,end):
    ts=[r[0] for r in events]
    a,b=bisect_left(ts,start),bisect_left(ts,end)
    sub=events[a:b]
    if not sub:return None
    first=sub[0][0];last=sub[-1][0]
    f=[z for z in sub if z[0]==first]
    l=[z for z in sub if z[0]==last]
    if first>=last or len(f)==0 or len(l)==0:
        return None
    for x,y in zip(sub,sub[1:]):
        if x[0]>y[0]:raise ValueError('UNSORTED_TIMESTAMP')
    return {'start':v(f),'end':v(l),'all_vwap':v(sub),
            'range':max(z[1] for z in sub)-min(z[1] for z in sub),
            'groups':len({z[0] for z in sub})}

def classify(events,day):
    dev_day(day)  # sealed guard BEFORE market iteration
    pm=segment_stats(events,et_edge(day,8,30),et_edge(day,9,30))
    rth=segment_stats(events,et_edge(day,9,30),et_edge(day,9,45))
    if pm is None or rth is None:
        return {k:MISSING for k in IDS}
    width=pm['range']
    pb=pm['end']-pm['start']
    rb=rth['end']-rth['start']
    if width<=0 or pb==0 or rb==0:
        return {k:MISSING for k in IDS}
    base=(width>=12 and abs(pb)*5>=width and abs(rb)*10>=width)
    if not base:
        return {k:OTHER for k in IDS}
    pb_sign=1 if pb>0 else -1
    rb_sign=1 if rb>0 else -1
    displacement=rth['start']-pm['all_vwap']
    answer={IDS[0]:CASE if pb_sign!=rb_sign else CONTROL}
    if displacement==0 or abs(displacement)*10<width:
        answer[IDS[1]]=OTHER
    else:
        answer[IDS[1]]=CASE if ((1 if displacement>0 else -1)==pb_sign) else CONTROL
    return answer

def month_stage(root,month):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_BEFORE_IO')
    counts={k:Counter() for k in IDS};qc=Counter();source=0;both=0
    for day in sorted(month_days(root,month)):
        d=dev_day(day);source+=1
        events=list(source_events(file_for(root,d,'Last')))
        status,_,_=frozen_t05(events,day)
        qc[status]+=1
        if status!='READY':continue
        label=classify(events,day)
        if set(label)!=set(IDS):raise AssertionError('MISSING_MEMBER')
        for k,g in label.items():
            if g not in LABELS:raise ValueError('UNKNOWN_CASE_CLASS')
            counts[k][g]+=1
        both+=(label[IDS[0]]==CASE and label[IDS[1]]==CASE)
    eligible=qc['READY']
    if sum(qc.values())!=source or any(sum(counts[k].values())!=eligible for k in IDS):
        raise AssertionError('SOURCE_OR_LABEL_MISMATCH')
    return {'stage':'T59_T60_D0_ONLY','month':month,'source':source,'eligible':eligible,
        'counts':{k:{g:counts[k][g] for g in LABELS} for k in IDS},'both_case':both,
        'future_outcomes_read':False,'trades':None,'PnL':None,'CI90':None,
        'BH_q':None,'PF':None,'DD':None,'portfolio_delta':None,
        'holdouts_opened':False,'new_data':False,'new_5second_signals':False}

def aggregate(ms):
    if set(ms)!=set(MONTHS):raise ValueError('ALL_SEVEN_MONTHS_REQUIRED')
    src=ready=joint=0
    totals={k:Counter() for k in IDS};months=[]
    for m in MONTHS:
        x=ms[m]
        if (x['month']!=m or x['stage']!='T59_T60_D0_ONLY'
            or any(x[k] is not False for k in ('future_outcomes_read','holdouts_opened',
                        'new_data','new_5second_signals'))
            or any(x[k] is not None for k in ('trades','PnL','CI90','BH_q','PF','DD','portfolio_delta'))
            or set(x['counts'])!=set(IDS)):
            raise ValueError('UNSAFE_D0_MONTH')
        src+=x['source'];ready+=x['eligible'];joint+=x['both_case']
        for k in IDS:
            if sum(x['counts'][k].values())!=x['eligible']:raise AssertionError('MISSING_LABELS')
            totals[k].update(x['counts'][k])
        months.append({'month':m,'source':x['source'],'eligible':x['eligible'],
          'N_case_control':{k:[x['counts'][k][CASE],x['counts'][k][CONTROL]] for k in IDS}})
    if (src,ready)!=(140,135):raise AssertionError('EXPECTED_140_135')
    q={}
    for k in IDS:
        a,b=totals[k][CASE],totals[k][CONTROL]
        if sum(totals[k].values())!=135:raise AssertionError('BAD_D0_COVERAGE')
        status='UNIDENTIFIABLE' if not a or not b else (
             'LOW_POWER' if min(a,b)<15 else 'TESTABLE')
        q[k]={'N_case':a,'N_control':b,'N_other':totals[k][OTHER],
           'N_not_evaluable':totals[k][MISSING],'D0':status,
           'N_trades':None,'CI90':None,'p':None,'q':None,'PF':None,
           'DD':None,'PnL':None,'DeltaRouter':None,'D1':'LOCKED_BELOW_BATCH_20'}
    return {'stage':'T59_T60_D0_COMPLETE_NO_OUTCOME',
        'source':src,'eligible':ready,'family_size':2,'questions':q,
        'case_overlap':joint,'months':months,'D1_unlocked':False,
        'broker_fills':False,'holdouts_opened':False,'new_data':False,
        'PnL':None,'N_trades':None,'CI90':None,'p':None,'q':None}

def report(z):
    s=['# T59/T60 — Nuevas hipótesis premkt, D0 SOLO CASOS/CONTROLES','','No son H77/H69 originales. No futuro ni retorno.','','| ID | N CASE | N CONTROL | OTHER | NO_EVAL | Gate D0 |','|---|---:|---:|---:|---:|---|']
    for k,x in z['questions'].items():
        s.append(f"| {k} | {x['N_case']} | {x['N_control']} | {x['N_other']} | {x['N_not_evaluable']} | {x['D0']} |")
    s+=['',f"Solapamiento CASE-CASE = {z['case_overlap']} sesiones.",
        'H77/H69 originales G0 NOT_PORTABLE: faltan ATR14 RTH y cierre prev16:00.',
        'N trades/IC90/q/Holm/PF/DD/neto/DeltaRouter N/D. D1 locked, nueva cohorte ≥20 requerida.',
        'Sin historia nueva ni OOS.']
    return '\n'.join(s)+'\n'

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--root',type=Path);a.add_argument('--month')
    a.add_argument('--inputs',type=Path);a.add_argument('--out',type=Path,required=True)
    a.add_argument('--report',type=Path);q=a.parse_args()
    if q.month:
        if q.month not in MONTHS:raise SystemExit('SEALED_MONTH')
        z=month_stage(q.root,q.month)
        q.out.parent.mkdir(parents=True,exist_ok=True)
        q.out.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n')
        print('T59_T60_D0_MONTH='+json.dumps({'month':q.month,'source':z['source'],'eligible':z['eligible'],'future':False}))
    else:
        if not q.inputs or not q.report:raise ValueError('inputs/report required')
        z=aggregate({m:json.loads((q.inputs/f'd0_{m}.json').read_text()) for m in MONTHS})
        q.out.parent.mkdir(parents=True,exist_ok=True)
        q.out.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n')
        q.report.write_text(report(z))
        print('T59_T60_D0_FINAL='+json.dumps({'source':z['source'],'eligible':z['eligible'],
           'cases_controls':{k:[v['N_case'],v['N_control']] for k,v in z['questions'].items()},
           'gate':{k:v['D0'] for k,v in z['questions'].items()},
           'outcomes_read':False,'D1_unlocked':False},sort_keys=True))
