#!/usr/bin/env python3
"""T20–T25: SIX frozen questions, ONE fixed 10:00 ET 377-print anchor/day.
Stage 0 ONLY: case/control counts; NO forward returns, fills, PnL or holdouts.
"""
from __future__ import annotations
import argparse
import json
from bisect import bisect_left
from collections import Counter
from fractions import Fraction
from pathlib import Path

from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_b05h01_trade_expansion_month import et_edge,frozen_t05
from qc_tick_day import file_for
from qc_tick_to_minutes import source_events

IDS=('T20_BAR_VALUE_SKEW','T21_EXTREME_REJECTION',
     'T22_QTY_WITH_PROGRESS','T23_TEMPO_DECELERATION',
     'T24_SIGN_ALTERNATION','T25_CROSS_SCALE_DIVERGENCE')
CASE='CASE'
CONTROL='CONTROL'
OTHER='OTHER'
MISSING='NOT_EVALUABLE'
LABELS=(CASE,CONTROL,OTHER,MISSING)


def v(b):
    if b.total_qty<=0:
        raise ValueError('zero volume')
    return Fraction(b.price_times_qty_ticks,b.total_qty)


def slope(a,b):
    """VWAP(b) - VWAP(a), ticks."""
    return v(b)-v(a)


def sign(a):
    return (a>0)-(a<0)


def label(state,side=0):
    if state not in LABELS or side not in (-1,0,1):
        raise ValueError('invalid state or direction')
    return state,side


def classify(a,b,c,d,e,small=(),medium=()):
    """All tests share the same fixed E; no outcome or trade path is read."""
    answer={}
    width=e.high_ticks-e.low_ticks
    dp=slope(d,e)
    pos=(v(e)-e.low_ticks)/width if width>0 else None

    # T20 value near bar extremes vs central volume value.
    if width>=12 and pos is not None and pos>=Fraction(3,4):
        answer[IDS[0]]=label(CASE,+1)
    elif width>=12 and pos is not None and pos<=Fraction(1,4):
        answer[IDS[0]]=label(CASE,-1)
    elif width>=12 and Fraction(2,5)<=pos<=Fraction(3,5):
        answer[IDS[0]]=label(CONTROL,sign(dp) if abs(dp)>=4 else 0)
    else:
        answer[IDS[0]]=label(OTHER)

    # T21 the prior bar extreme must be broken on only one side.
    highbreak=e.high_ticks>=d.high_ticks+8
    lowbreak=e.low_ticks<=d.low_ticks-8
    if highbreak != lowbreak:
        if highbreak and v(e)<=d.high_ticks-4:
            answer[IDS[1]]=label(CASE,-1)
        elif lowbreak and v(e)>=d.low_ticks+4:
            answer[IDS[1]]=label(CASE,+1)
        elif highbreak and v(e)>=d.high_ticks+4:
            answer[IDS[1]]=label(CONTROL,+1)
        elif lowbreak and v(e)<=d.low_ticks-4:
            answer[IDS[1]]=label(CONTROL,-1)
        else:
            answer[IDS[1]]=label(OTHER)
    else:
        answer[IDS[1]]=label(OTHER)

    # T22 contracts per print, explicitly conditional on directional advance.
    if width>=12 and abs(dp)>=4 and d.prints>0 and e.prints>0 and d.total_qty>0:
        relative=Fraction(e.total_qty*d.prints,d.total_qty*e.prints)
        if relative>=Fraction(3,2):
            answer[IDS[2]]=label(CASE,sign(dp))
        elif Fraction(4,5)<=relative<=Fraction(6,5):
            answer[IDS[2]]=label(CONTROL,sign(dp))
        else:
            answer[IDS[2]]=label(OTHER)
    else:
        answer[IDS[2]]=label(OTHER)

    # T23 next 15min RANGE endpoint, no trade direction.
    dur_d=d.end_timestamp-d.start_timestamp
    dur_e=e.end_timestamp-e.start_timestamp
    if dur_d<=0 or dur_e<=0:
        answer[IDS[3]]=label(MISSING)
    elif 8<=width<=32:
        relative=Fraction(dur_e,dur_d)
        if relative>=2:
            answer[IDS[3]]=label(CASE)
        elif Fraction(4,5)<=relative<=Fraction(5,4):
            answer[IDS[3]]=label(CONTROL)
        else:
            answer[IDS[3]]=label(OTHER)
    else:
        answer[IDS[3]]=label(OTHER)

    # T24 alternation vs two aligned material slopes, direction last.
    prior=slope(c,d)
    if abs(prior)>=6 and abs(dp)>=6:
        answer[IDS[4]]=label(CASE if sign(prior)!=sign(dp) else CONTROL,sign(dp))
    else:
        answer[IDS[4]]=label(OTHER)

    # T25 only completed 233 / 4181 BARS STRICTLY BEFORE anchor.
    if len(small)<2 or len(medium)<2:
        answer[IDS[5]]=label(MISSING)
    else:
        ss=slope(small[-2],small[-1])
        mm=slope(medium[-2],medium[-1])
        if abs(ss)>=4 and abs(mm)>=4:
            answer[IDS[5]]=label(CASE if sign(ss)!=sign(mm) else CONTROL,sign(mm))
        else:
            answer[IDS[5]]=label(OTHER)
    if set(answer)!=set(IDS):
        raise AssertionError('all six questions required')
    return answer


def detect(events,day):
    """PRIVATE case/control decision, with same 10:00 ET anchor for all six.
    Reject sealed day BEFORE iterating potentially sensitive Last input.
    """
    dev_day(day)
    z=completed_bars_by_print_count(events,day,(233,377,4181))
    lo,hi=et_edge(day,10,0),et_edge(day,10,15)
    anchor=next((i for i,b in enumerate(z[377])
                 if lo<=b.end_timestamp<hi),None)
    if anchor is None or anchor<4:
        return {k:label(MISSING) for k in IDS},False
    a,b,c,d,e=z[377][anchor-4:anchor+1]
    if not (a.end_timestamp<b.end_timestamp<c.end_timestamp<
            d.end_timestamp<e.end_timestamp):
        raise ValueError('split or unsorted timestamp groups')
    before={}
    for n in (233,4181):
        pool=z[n]
        ends=[q.end_timestamp for q in pool]
        before[n]=pool[:bisect_left(ends,e.end_timestamp)]
    return classify(a,b,c,d,e,before[233][-2:],before[4181][-2:]),True


def month_stage(root,month):
    if month not in MONTHS:
        raise ValueError('SEALED MONTH DENIED BEFORE FILE READ')
    days=sorted(month_days(root,month))
    statuses=Counter()
    counts={k:Counter() for k in IDS}
    sides={k:Counter() for k in IDS}
    overlaps=Counter()
    anchors=0
    for day in days:
        dev_day(day)
        events=list(source_events(file_for(root,dev_day(day),'Last')))
        qc,_,_=frozen_t05(events,day)  # eligibility only, never T20–T25 signal
        statuses[qc]+=1
        if qc!='READY':
            continue
        out,has_anchor=detect(events,day)
        anchors+=int(has_anchor)
        chosen=[]
        for k in IDS:
            state,side=out[k]
            counts[k][state]+=1
            if state in (CASE,CONTROL):
                sides[k][str(side)]+=1
            if state==CASE:
                chosen.append(k)
        for i,k in enumerate(chosen):
            for next_k in chosen[i+1:]:
                overlaps[k+'__'+next_k]+=1
    source=len(days)
    eligible=statuses['READY']
    if sum(statuses.values())!=source:
        raise AssertionError('source coverage mismatch')
    for k in IDS:
        if sum(counts[k].values())!=eligible:
            raise AssertionError('stage0 classifications not exhaustive')
    return {'status':'T20_T25_FROZEN_STAGE0_CASE_CONTROL_NO_OUTCOMES',
        'month':month,'source_days':source,'eligible_days':eligible,
        'excluded_days':source-eligible,'anchor_days':anchors,
        'by_question':{k:{s:counts[k][s] for s in LABELS} for k in IDS},
        'side_counts_case_or_control':{k:dict(sides[k]) for k in IDS},
        'case_case_overlap_days':dict(overlaps),
        'N_trades':None,'net_usd':None,'CI90':None,'p':None,'q_BH':None,
        'PF':None,'DD':None,'holdouts_opened':False,
        'new_history_acquired':False,'five_second_new_signals':False,
        'outcomes_computed':False,'individual_events_exported':False}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--month',required=True)
    p.add_argument('--out',type=Path,required=True)
    opt=p.parse_args()
    if opt.month not in MONTHS:
        raise SystemExit('SEALED MONTH BEFORE IO')
    result=month_stage(opt.root,opt.month)
    opt.out.parent.mkdir(parents=True,exist_ok=True)
    opt.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('NQ_T20_T25_SAFE='+json.dumps({
        'month':opt.month,'source':result['source_days'],
        'eligible':result['eligible_days'],'anchor':result['anchor_days'],
        'counts':{k:{x:result['by_question'][k][x] for x in (CASE,CONTROL)}
                  for k in IDS},'outcomes':False},sort_keys=True))
