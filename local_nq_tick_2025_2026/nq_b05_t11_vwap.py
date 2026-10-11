#!/usr/bin/env python3
"""B05 T11 independent causal RTH VWAP acceptance, pullback and print activity.

Research-only signals from *completed* 5s Last bars and exact trade-qty VWAP.
No selected thresholds from results. No prices or signals ever printed.
"""
from __future__ import annotations
from collections import Counter
from qc_tick_day import utc_bounds
from nq_tick_short_horizon import (
    dev_day,STEP_100NS,N_BARS,OR_START,OR_END,LAST_SIGNAL,complete)

MODELS=('T11_FULL','A11_NO_ACTIVITY','A11_NO_PULLBACK')
COOLDOWN_BARS=60
FIRST_SIGNAL=1200 # 09:40 ET
HIST_BARS=30
ACCEPT_BARS=24
NEEDED_ACCEPT=18
MIN_OLD_PRINTS=20
ACTIVITY_PCT=115

def causal_vwap(events,day):
    """RTH session-anchored VWAP: cumulative integer tick*quantity / quantity.

    All snapshots at end of own 5s bar, never later, no fill claim.
    """
    d=dev_day(day)
    lo,_=utc_bounds(d)
    notional=0
    volume=0
    num=[0]*N_BARS
    den=[0]*N_BARS
    last_index=OR_START-1
    for ts,px,qty in events:
        if ts<lo+OR_START*STEP_100NS:
            continue
        i=(ts-lo)//STEP_100NS
        if not OR_START<=i<N_BARS:
            raise ValueError('Event outside declared ET source')
        if i<last_index:
            raise ValueError('Unsorted VWAP source')
        if not isinstance(qty,int) or qty<1 or not isinstance(px,int) or px<1:
            raise ValueError('Invalid VWAP print')
        if i>last_index:
            # Carry forward previous snapshot through empty 5s intervals;
            # empty bars remain None elsewhere and can never pass signal QC.
            for b in range(max(OR_START,last_index+1),i):
                num[b]=notional;den[b]=volume
        notional+=px*qty
        volume+=qty
        num[i]=notional
        den[i]=volume
        last_index=i
    if last_index>=OR_START:
        for i in range(last_index+1,N_BARS):
            num[i]=notional
            den[i]=volume
    return num,den

def favorable(price_ticks,i,side,threshold,num,den):
    if not den[i]:
        return False
    return side*(price_ticks*den[i]-num[i])>=threshold*den[i]

def not_too_far_wrong(price_ticks,i,side,limit,num,den):
    if not den[i]:
        return False
    return side*(price_ticks*den[i]-num[i])>=-limit*den[i]

def vwapside_signal(bars,num,den,i,side,no_activity=False,no_pullback=False):
    """Only [i-30:i+1] closed; VWAP at each closed bar index."""
    if side not in (-1,1) or not FIRST_SIGNAL<=i<LAST_SIGNAL:
        return False
    history=complete(bars,i-HIST_BARS,i+1)
    if history is None:return False
    if any(den[k]<=0 for k in range(i-30,i+1)):return False
    # 24 bars immediately before six-bar pullback (i-30...i-7).
    accepted=sum(favorable(bars[k][3],k,side,2,num,den)
                 for k in range(i-30,i-6))
    if accepted<NEEDED_ACCEPT:return False
    if not favorable(bars[i-6][3],i-6,side,6,num,den):
        return False
    # Pullback bars are all completed before the current trigger bar.
    if not all(not_too_far_wrong(bars[k][3],k,side,8,num,den)
               for k in range(i-6,i)):
        return False
    if not no_pullback:
        if side==1:
            touched=any(bars[k][2]*den[k]<=num[k]+3*den[k]
                        for k in range(i-6,i))
        else:
            touched=any(bars[k][1]*den[k]>=num[k]-3*den[k]
                        for k in range(i-6,i))
        if not touched:return False
    if not favorable(bars[i][3],i,side,2,num,den):
        return False
    if side*(bars[i][3]-bars[i][0])<=0:
        return False
    # Previous close was at/below the +2 tick trigger threshold (mirror short).
    if side*(bars[i-1][3]*den[i-1]-num[i-1])>2*den[i-1]:
        return False
    if not no_activity:
        now=sum(bars[k][4] for k in range(i-5,i+1))
        previous=sum(bars[k][4] for k in range(i-11,i-5))
        if previous<MIN_OLD_PRINTS or 100*now<ACTIVITY_PCT*previous:
            return False
    return True

def t11_signals(events,bars,day):
    dev_day(day)
    num,den=causal_vwap(events,day)
    result={m:[] for m in MODELS}
    previous={m:-100000 for m in MODELS}
    conflicts=Counter()
    for i in range(FIRST_SIGNAL,LAST_SIGNAL):
        if complete(bars,i-HIST_BARS,i+1) is None:continue
        for model in MODELS:
            if i-previous[model]<COOLDOWN_BARS:continue
            kw={'no_activity':model=='A11_NO_ACTIVITY',
                'no_pullback':model=='A11_NO_PULLBACK'}
            sides=[s for s in (1,-1) if vwapside_signal(bars,num,den,i,s,**kw)]
            if len(sides)==1:
                result[model].append((i,sides[0]))
                previous[model]=i
            elif sides:
                conflicts[model]+=1
    return result,dict(conflicts)
