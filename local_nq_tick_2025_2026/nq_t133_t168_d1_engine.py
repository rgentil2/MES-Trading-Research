#!/usr/bin/env python3
"""Frozen full-family T133-T168 economic proxy, NOT broker fills.

One entry after whole E377 timestamp, worst Last price within NEXT atomic
timestamp +2 ticks adverse; group-level barrier checks stop-first on ties.
Stops and targets are frozen at decision; never infer within-timestamp order.
"""
from __future__ import annotations
from bisect import bisect_right
from fractions import Fraction as F
from itertools import groupby

from nq_b05h01_trade_expansion_month import et_edge
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t61_t96_d0_features import first_bars,summary,sign,whole_groups
from nq_t133_t152_executable_d0_features import completed_summary,segment
from nq_t133_t168_combined_D0_batch import OLD_IDS,NEW_IDS,IDS

COST_RT_USD={'NQ':4.0,'MNQ':1.50}
TICK_USD={'NQ':5.,'MNQ':0.5}
ENTRY_SLIP_TICKS=2
EXIT_SLIP_TICKS=2
MAX_RISK_USD=250.

def prepare_context(events,day):
    five,anchor=first_bars(events,day)
    e=summary(five[-1]);d=summary(five[-2]);c=summary(five[-3])
    if any(z is None for z in (e,d,c)):raise AssertionError('D1_E_ANCHOR_MISSING')
    side=sign(e['vwap']-d['vwap'])
    times=[x[0] for x in events]
    bars=completed_bars_by_print_count(events,day,(233,4181))
    micro=[completed_summary(events,times,b) for b in bars[233] if b.end_timestamp<=anchor][-3:]
    macro=[completed_summary(events,times,b) for b in bars[4181] if b.end_timestamp<=anchor][-2:]
    pm=segment(events,times,day,(8,30),(9,30))
    rth=segment(events,times,day,(9,30),(10,0))
    return {'anchor':anchor,'e':e,'d':d,'c':c,'side':side,
       'micro':micro,'macro':macro,'pm':pm,'rth':rth}

def stop_and_side(member,ctx):
    family=member['block'];e=ctx['e'];d=ctx['d'];c=ctx['c']
    lastmicro=ctx['micro'][-1] if ctx['micro'] else None
    side=ctx['side']
    if member['id'] in OLD_IDS:
        if family=='A_BREAKOUT_RETEST':
            if lastmicro is None:return None
            stop=F(min(e['lo'],lastmicro['lo'])-1) if side>0 else F(max(e['hi'],lastmicro['hi'])+1)
        elif family=='B_PULLBACK_CONTINUATION':
            if lastmicro is None:return None
            stop=F(lastmicro['lo']-1) if side>0 else F(lastmicro['hi']+1)
        elif family=='C_FALSE_BREAK_REVERSAL':
            refs={'PM_0830_0930_OUTER':ctx['pm'],
              'RTH_0930_1000_OUTER':ctx['rth'],
              'D377_OUTER':d,
              'PRIOR_3_MICRO233_OUTER':(
                {'hi':max(v['hi'] for v in ctx['micro']),
                 'lo':min(v['lo'] for v in ctx['micro'])}
                if len(ctx['micro'])==3 else None),
              'PRIOR_MACRO4181_OUTER':ctx['macro'][-1] if ctx['macro'] else None}
            ref=refs.get(member['reference'])
            if ref is None:return None
            upper=e['hi']>=ref['hi']+1 and e['end']<ref['hi']
            lower=e['lo']<=ref['lo']-1 and e['end']>ref['lo']
            if upper==lower:return None
            side=-1 if upper else 1
            stop=F(max(e['hi'],ref['hi'])+1) if side<0 else F(min(e['lo'],ref['lo'])-1)
        elif family=='D_REGIME_RISK_ROUTER':
            stop=F(e['lo']-1) if side>0 else F(e['hi']+1)
        else:raise AssertionError('UNKNOWN_ORIGINAL_PLAN')
    else:
        if family=='E_VWAP_COUNTERMOVE':
            refs={'PM_VWAP':ctx['pm'],'RTH_VWAP':ctx['rth'],
                  'D377_VWAP':d,
                  'MACRO4181_VWAP':ctx['macro'][-1] if ctx['macro'] else None}
            ref=refs.get(member['reference'])
            if ref is None:return None
            side=-sign(e['end']-ref['vwap'])
        elif family not in ('F_AUCTION_ALIGNMENT','G_AUCTION_LOCATION',
                           'H_TAPE_STRUCTURE'):
            raise AssertionError('UNKNOWN_ADDED_PLAN')
        stop=F(e['lo']-1) if side>0 else F(e['hi']+1)
    if side not in (-1,1):return None
    return (side,stop,member.get('take_profit_R',member.get('target_R')),
         member.get('max_minutes',member.get('timeout_minutes')))

def first_future_groups(events,anchor,timeout_minutes):
    """Read ONLY whole atomic Last groups within predeclared 15/30min horizon."""
    times=[x[0] for x in events]
    i=bisect_right(times,anchor)
    end=anchor+int(timeout_minutes)*60*10_000_000
    j=bisect_right(times,end)
    if i>=j:return []
    return [ (ts,min(x[1] for x in items),max(x[1] for x in items))
      for ts,itr in groupby(events[i:j],lambda z:z[0])
      for items in [list(itr)] ]

def model_one(groups,side,stop,target_R,timeout,anchor):
    """Worst group prints at ENTRY; adverse slip; adversarial group exits.

    Signal must be CASE and risk-qualified by D0. Recheck actual model risk.
    """
    if not groups:return {'status':'NO_NEXT_GROUP'}
    first=groups[0]
    ref_entry=F(first[2]) if side>0 else F(first[1])
    entry=ref_entry+side*ENTRY_SLIP_TICKS
    risk=side*(entry-stop)
    if not 8<=risk<=400:return {'status':'REJECTED_RISK_AT_PROXY_ENTRY'}
    instrument='NQ' if risk*5<=MAX_RISK_USD else 'MNQ'
    if risk*TICK_USD[instrument]>MAX_RISK_USD:
        return {'status':'REJECTED_RISK_AT_PROXY_ENTRY'}
    target=entry+side*F(str(target_R))*risk
    # Entry group itself has unknown transaction sequence: conservative stop
    # if any touch at that same timestamp; do NOT infer a same-group target win.
    touched_entry_stop=(first[1]<=stop if side>0 else first[2]>=stop)
    exit_ref=None;reason=None
    if touched_entry_stop:
        exit_ref=(F(min(stop,first[1])) if side>0 else F(max(stop,first[2])))
        reason='AMBIGUOUS_ENTRY_GROUP_STOP_FIRST'
    else:
        for ts,lo,hi in groups[1:]:
            hit_stop=lo<=stop if side>0 else hi>=stop
            hit_target=hi>=target if side>0 else lo<=target
            if hit_stop:
                exit_ref=(F(min(stop,lo)) if side>0 else F(max(stop,hi)))
                reason='STOP_FIRST' if hit_target else 'STOP'
                break
            if hit_target:
                exit_ref=target
                reason='TARGET'
                break
    if exit_ref is None:
        last=groups[-1]
        if last[0] < anchor+int(timeout)*60*10_000_000:
            return {'status':'HORIZON_NOT_FULLY_OBSERVED'}
        exit_ref=F(last[1]) if side>0 else F(last[2])
        reason='TIME_EXIT_ADVERSE_GROUP'
    # Exit at adverse price +2 tick slippage; entry +2 already included.
    exit_px=exit_ref-side*EXIT_SLIP_TICKS
    raw_ticks=float(side*(exit_ref-ref_entry))
    net_ticks=float(side*(exit_px-entry))
    tickusd=TICK_USD[instrument]
    fee=COST_RT_USD[instrument]
    gross=raw_ticks*tickusd
    base=gross-(ENTRY_SLIP_TICKS+EXIT_SLIP_TICKS)*tickusd-fee
    stress15=gross-1.5*((ENTRY_SLIP_TICKS+EXIT_SLIP_TICKS)*tickusd+fee)
    stress10=base-10.
    if abs(base-(net_ticks*tickusd-fee))>1e-6:
        raise AssertionError('P_AND_L_UNIT_CONVERSION_PARITY')
    return {'status':'MODELLED_EXECUTION_UNVERIFIED','instrument':instrument,
      'net_usd':base,'stress_1_5x_usd':stress15,
      'stress_plus_10_rt_usd':stress10,
      'gross_usd':gross,'risk_nominal_usd':float(risk)*tickusd,
      'exit_reason':reason,'entry_group_ambiguous':touched_entry_stop,
      'risk_ticks':float(risk),'direction':side}

def day_sim(events,day,old,new):
    from nq_t133_t152_executable_d0_features import classify_day as classify_old
    from nq_t153_t168_executable_d0_features import classify_day as classify_new
    a,b=classify_old(events,day,old),classify_new(events,day,new)
    labels={**a,**b}
    if set(labels)!=set(IDS):raise AssertionError('D1_MISSING_HYPOTHESES')
    ctx=prepare_context(events,day)
    members={m['id']:m for m in old['members']+new['members']}
    cache={}
    output={}
    for k in IDS:
        label=labels[k]
        if label!= 'CASE':
            output[k]={'group':label,'status':'NO_CAUSAL_TRIGGER',
                        'net_usd':0.,'stress_1_5x_usd':0.,
                        'stress_plus_10_rt_usd':0.}
            continue
        plan=stop_and_side(members[k],ctx)
        if plan is None:
            raise AssertionError('D0_CASE_WITHOUT_CAUSAL_ENTRY_STOP_PLAN: '+k)
        side,stop,target,timeout=plan
        if not target or not timeout:raise AssertionError('NO_TP_OR_TIME_FOR_CASE')
        if timeout not in cache:
            cache[timeout]=first_future_groups(events,ctx['anchor'],timeout)
        result=model_one(cache[timeout],side,stop,target,timeout,ctx['anchor'])
        output[k]={'group':label,**result}
    return output
