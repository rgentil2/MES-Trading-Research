#!/usr/bin/env python3
"""T133–T152: 20 executable-plan candidate triggers; ONLY G0/D0, NO FUTURE.

Do not convert Last prints into broker fills. Atomic equal timestamps.
Return public-safe per-day classifications; no signal prices/rows exported.
"""
from __future__ import annotations
from bisect import bisect_left,bisect_right
from fractions import Fraction as F

from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_b05h01_trade_expansion_month import et_edge
from nq_t61_t96_d0_features import first_bars,summary,sign,CASE,CONTROL,OTHER,MISSING

LABELS=(CASE,CONTROL,OTHER,MISSING)
NAMES=(
'break_pm_extreme','break_rth30_extreme','break_prior_377_extreme',
'break_micro_233_extreme','break_macro_4181_extreme',
'pullback_pm_vwap','pullback_rth_vwap','pullback_d377_vwap',
'pullback_micro233_vwap','pullback_macro4181_vwap',
'reject_pm_extreme','reject_rth30_extreme','reject_d377_extreme',
'reject_micro233_extreme','reject_macro4181_extreme',
'regime_micro_momentum','regime_macro_momentum','regime_open_momentum',
'regime_high_pace','regime_377_contraction')

def completed_summary(events,times,bar):
    if bar is None:return None
    lo=bisect_left(times,bar.start_timestamp)
    hi=bisect_right(times,bar.end_timestamp)
    subset=events[lo:hi]
    if len(subset)!=bar.prints:raise AssertionError('TIMESTAMP_BAR_NOT_ATOMIC')
    s=summary(subset)
    if s is None and bar.whole_timestamp_groups==1:
        # A valid bar can exceed 233/4181 prints in ONE atomic timestamp.
        # The earlier summary() helper intentionally returns None for
        # 1 timestamp group; this is missing temporal diversity, not a
        # missing PRICE context. Preserve its complete indivisible group.
        from nq_t61_t96_d0_features import whole_groups
        groups=whole_groups(subset)
        if len(groups)!=1:
            raise AssertionError('BAR_GROUP_ATOMIC_PARITY_FAIL')
        s={'lo':bar.low_ticks,'hi':bar.high_ticks,
           'vwap':F(bar.price_times_qty_ticks,bar.total_qty),
           'open':groups[0][1],'end':groups[0][1],
           'groups':groups}
    if s is None or s['vwap']!=F(bar.price_times_qty_ticks,bar.total_qty):
        raise AssertionError('BAR_QTY_VWAP_PARITY_FAIL')
    s['duration100ns']=bar.end_timestamp-bar.start_timestamp
    return s

def segment(events,times,day,a,b):
    lo,hi=et_edge(day,*a),et_edge(day,*b)
    return summary(events[bisect_left(times,lo):bisect_left(times,hi)])

def plan_stop(family,side,E,micro,ref):
    if side not in (-1,1):return None
    pad=F(1)
    if family=='A_BREAKOUT_RETEST':
        if micro is None:return None
        return F(min(E['lo'],micro['lo'])-1) if side==1 else F(max(E['hi'],micro['hi'])+1)
    if family=='B_PULLBACK_CONTINUATION':
        if micro is None:return None
        return F(micro['lo']-1) if side==1 else F(micro['hi']+1)
    if family=='C_FALSE_BREAK_REVERSAL':
        if ref is None:return None
        return F(min(E['lo'],ref['lo'])-1) if side==1 else F(max(E['hi'],ref['hi'])+1)
    if family=='D_REGIME_RISK_ROUTER':
        return F(E['lo']-1) if side==1 else F(E['hi']+1)
    raise ValueError('UNKNOWN_STRATEGY_FAMILY')

def classify_day(events,day,registry,include_structure=False):
    """First 377 bar completed [10:00,10:15) decision; no outcome price read.

    We parse same licensed events already present in day, but decisions are
    based exclusively on groups <= anchor timestamp. Holdouts are gated by
    month_stage before reading a single row.
    """
    five,anchor=first_bars(events,day)
    e=summary(five[-1]);d=summary(five[-2]);c=summary(five[-3])
    if any(x is None for x in (e,d,c)):raise AssertionError('MISSING_377_CONTEXT')
    side=sign(e['vwap']-d['vwap'])
    times=[z[0] for z in events]
    bar=completed_bars_by_print_count(events,day,(233,4181))
    micro=[completed_summary(events,times,b) for b in bar[233] if b.end_timestamp<=anchor][-3:]
    macro=[completed_summary(events,times,b) for b in bar[4181] if b.end_timestamp<=anchor][-2:]
    last_micro=micro[-1] if micro else None
    prior_micro=micro[-2] if len(micro)>=2 else None
    last_macro=macro[-1] if macro else None
    prior_macro=macro[-2] if len(macro)>=2 else None
    pm=segment(events,times,day,(8,30),(9,30))
    rth=segment(events,times,day,(9,30),(10,0))
    refs={
      'PM_0830_0930_OUTER':pm,
      'RTH_0930_1000_OUTER':rth,
      'PRIOR_CD_377_OUTER':{'hi':max(d['hi'],c['hi']),'lo':min(d['lo'],c['lo'])},
      'PRIOR_3_MICRO_233_OUTER':({'hi':max(x['hi'] for x in micro),'lo':min(x['lo'] for x in micro)} if len(micro)==3 else None),
      # Frozen C146/C147 use explicit aliases without separator.
      # SAME structural context as A136/A137; fix routing ONLY.
      'PRIOR_3_MICRO233_OUTER':({'hi':max(x['hi'] for x in micro),'lo':min(x['lo'] for x in micro)} if len(micro)==3 else None),
      'PRIOR_MACRO_4181_OUTER':last_macro,
      'PRIOR_MACRO4181_OUTER':last_macro,
      'PM_0830_0930_VWAP':pm,
      'RTH_0930_1000_VWAP':rth,
      'D377_VWAP':d,
      'PRIOR_3_MICRO233_VWAP':({'vwap':sum((x['vwap'] for x in micro),F(0))/3} if len(micro)==3 else None),
      'PRIOR_MACRO4181_VWAP':last_macro,
      'D377_OUTER':d,
      'TWO_MICRO_233_SLOPE': {'value':last_micro['vwap']-prior_micro['vwap']} if prior_micro and last_micro else None,
      'TWO_MACRO_4181_SLOPE': {'value':last_macro['vwap']-prior_macro['vwap']} if prior_macro and last_macro else None,
      'RTH_0930_1000_BODY': {'value':rth['end']-rth['open']} if rth else None,
      'MICRO_233_DURATION_CONTRACTION': {'value':prior_micro['duration100ns']-last_micro['duration100ns']} if prior_micro and last_micro else None,
      'E377_VS_D377_RANGE_CONTRACTION': {'value':(d['hi']-d['lo'])-(e['hi']-e['lo'])}
    }
    result={};debug={}
    for member in registry['members']:
        name=member['feature'];family=member['block'];ref=refs.get(member['reference'])
        order_side=side
        if ref is None:
            result[member['id']]=MISSING
            continue
        if family!='C_FALSE_BREAK_REVERSAL' and side==0:
            result[member['id']]=OTHER
            continue
        trigger=False;ambiguous=False
        if family=='A_BREAKOUT_RETEST':
            trigger=(e['end']>=ref['hi']+1 if side>0 else e['end']<=ref['lo']-1)
        elif family=='B_PULLBACK_CONTINUATION':
            if last_micro is None:
                result[member['id']]=MISSING;continue
            v=ref['vwap']
            touched=last_micro['lo']<=v<=last_micro['hi']
            reclaimed=(e['end']>=v+1 if side>0 else e['end']<=v-1)
            trigger=touched and reclaimed
        elif family=='C_FALSE_BREAK_REVERSAL':
            upper=e['hi']>=ref['hi']+1 and e['end']<ref['hi']
            lower=e['lo']<=ref['lo']-1 and e['end']>ref['lo']
            if upper and lower:ambiguous=True
            elif upper:trigger=True;order_side=-1
            elif lower:trigger=True;order_side=1
        elif family=='D_REGIME_RISK_ROUTER':
            x=ref['value']
            if name in ('regime_micro_momentum','regime_macro_momentum','regime_open_momentum'):
                trigger=side*x>0
            else:
                trigger=x>0
        else:raise AssertionError('UNKNOWN_REGISTERED_BLOCK')
        if ambiguous:result[member['id']]=OTHER;continue
        if not trigger:result[member['id']]=CONTROL;continue
        stop=plan_stop(family,order_side,e,last_micro,ref)
        if stop is None:result[member['id']]=MISSING;continue
        dist=order_side*(e['end']-stop)
        if not (registry['minimum_stop_ticks']<=dist<=registry['maximum_stop_ticks_for_MNQ']):
            result[member['id']]=OTHER;continue
        # 1 NQ if risk<=250 USD, otherwise 1 MNQ. This is a RISK
        # FILTER only, NEVER broker execution or a realized fill/PNL.
        instrument='NQ' if F(5)*dist<=registry['max_risk_usd_per_hypothetical_trade'] else 'MNQ'
        if (F(5) if instrument=='NQ' else F(1,2))*dist>registry['max_risk_usd_per_hypothetical_trade']:
            result[member['id']]=OTHER;continue
        result[member['id']]=CASE
        if include_structure:
            debug[member['id']]={'instrument':instrument,'side':order_side,
              'risk_ticks':float(dist),'risk_usd_at_E_reference_only':float(
                  (F(5) if instrument=='NQ' else F(1,2))*dist),
              'target_R':member['take_profit_R'],
              'max_minutes':member['max_minutes'],
              'potential_fill':False}
    if set(result)!={x['id'] for x in registry['members']} or len(result)!=20:
        raise AssertionError('INCOMPLETE_OR_UNREGISTERED_20_STRATEGIES')
    return (result,debug) if include_structure else result
