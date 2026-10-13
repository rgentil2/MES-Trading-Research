#!/usr/bin/env python3
"""Preregistered T153–T168 four new executable-strategy blocks, D0 ONLY.
All references are known at E377's atomic end. Last is NOT broker fills.
"""
from __future__ import annotations
from bisect import bisect_left
from fractions import Fraction as F

from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t61_t96_d0_features import first_bars,summary,sign,CASE,CONTROL,OTHER,MISSING,group_weighted
from nq_t133_t152_executable_d0_features import completed_summary,segment

FEATURES=('fade_e_vs_pm_vwap','fade_e_vs_rth_vwap',
  'fade_e_vs_d377_vwap','fade_e_vs_macro_vwap',
  'align_pm_body','align_rth_open_body',
  'align_d377_body','align_macro4181_body',
  'accept_pm_mid','accept_rth_mid',
  'accept_d377_mid','accept_micro233_mid',
  'recent233_qty_expansion','recent233_range_expansion',
  'e377_qty_frontload','e377_atomic_vwap_progress')
LABELS=(CASE,CONTROL,OTHER,MISSING)

def segment_group_halves(groups):
    """Split only BETWEEN whole equal-timestamp groups; no intra-group order."""
    if len(groups)<2:return None
    cut=len(groups)//2
    if cut<1 or cut>=len(groups):return None
    a,b=groups[:cut],groups[cut:]
    return (sum(x[2] for x in a)-sum(x[2] for x in b),
            group_weighted(b)-group_weighted(a))

def classify_day(events,day,registry):
    five,anchor=first_bars(events,day)
    e=summary(five[-1]);d=summary(five[-2])
    if e is None or d is None:raise AssertionError('FROZEN_377_ANCHOR_MISSING')
    side=sign(e['vwap']-d['vwap'])
    times=[x[0] for x in events]
    bars=completed_bars_by_print_count(events,day,(233,4181))
    micro=[completed_summary(events,times,b)
           for b in bars[233] if b.end_timestamp<=anchor][-3:]
    macro=[completed_summary(events,times,b)
           for b in bars[4181] if b.end_timestamp<=anchor][-2:]
    pm=segment(events,times,day,(8,30),(9,30))
    rth=segment(events,times,day,(9,30),(10,0))
    micro1=micro[-1] if micro else None
    micro0=micro[-2] if len(micro)>1 else None
    macro1=macro[-1] if macro else None
    midmicro=(F(min(x['lo'] for x in micro)+max(x['hi'] for x in micro),2)
              if len(micro)==3 else None)
    halves=segment_group_halves(e['groups'])
    value_refs={'PM_VWAP':pm,'RTH_VWAP':rth,
                'D377_VWAP':d,'MACRO4181_VWAP':macro1}
    body_refs={'PM_BODY':pm,'RTH_BODY':rth,
               'D377_BODY':d,'MACRO4181_BODY':macro1}
    center_refs={'PM_MID':F(pm['lo']+pm['hi'],2) if pm else None,
                 'RTH_MID':F(rth['lo']+rth['hi'],2) if rth else None,
                 'D377_MID':F(d['lo']+d['hi'],2),
                 'MICRO233_MID':midmicro}
    structure_refs={
      'MICRO233_QTY_CHANGE':(sum(z[2] for z in micro1['groups'])-
                              sum(z[2] for z in micro0['groups'])
                              if micro1 and micro0 else None),
      'MICRO233_RANGE_CHANGE':((micro1['hi']-micro1['lo'])-
                                   (micro0['hi']-micro0['lo'])
                                   if micro1 and micro0 else None),
      'E377_QTY_FRONTLOAD':halves[0] if halves else None,
      'E377_ATOMIC_PROGRESS':side*halves[1] if halves and side else None}
    allrefs=(set(value_refs)|set(body_refs)|set(center_refs)|set(structure_refs))
    out={}
    for m in registry['members']:
        k=m['id'];mode=m['mode'];key=m['reference']
        if key not in allrefs:raise AssertionError('UNREGISTERED_REFERENCE_NOT_IMPLEMENTED')
        direction=side
        if mode=='FADE_TO_VWAP':
            val=value_refs[key]
            if val is None:out[k]=MISSING;continue
            displacement=e['end']-val['vwap']
            direction=-sign(displacement)
            trigger=abs(displacement)>=20
        elif mode=='CONTINUATION_ALIGNMENT':
            val=body_refs[key]
            if val is None:out[k]=MISSING;continue
            trigger=side!=0 and sign(val['end']-val['open'])==side
        elif mode=='ACCEPTANCE_SIDE':
            val=center_refs[key]
            if val is None:out[k]=MISSING;continue
            trigger=side!=0 and side*(e['end']-val)>0
        elif mode=='TAPE_CONTEXT_CONTINUATION':
            val=structure_refs[key]
            if val is None:out[k]=MISSING;continue
            trigger=side!=0 and val>0
        else:raise AssertionError('UNREGISTERED_STRATEGY_MODE')
        if direction not in (-1,1):
            out[k]=OTHER;continue
        if not trigger:
            out[k]=CONTROL;continue
        stop=(F(e['lo']-1) if direction>0 else F(e['hi']+1))
        distance=direction*(e['end']-stop)
        if not (registry['min_stop_ticks']<=distance<=registry['max_stop_ticks']):
            out[k]=OTHER;continue
        tick_usd=(F(5) if distance*5<=registry['max_nominal_risk_usd'] else F(1,2))
        if tick_usd*distance>registry['max_nominal_risk_usd']:
            out[k]=OTHER;continue
        out[k]=CASE
    expected={x['id'] for x in registry['members']}
    if len(out)!=16 or set(out)!=expected or any(z not in LABELS for z in out.values()):
        raise AssertionError('D0_16_FAMILY_INCOMPLETE')
    return out
