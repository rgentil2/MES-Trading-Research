#!/usr/bin/env python3
"""T13: high-qty Last shock with subsequent PRICE RETRACE, no BBO aggressor/delta.

Independently preregistered B05C after T11/T12 failures, DEV-only, one signal
per model per day to protect limited shared capacity. No VWAP, OR breakout,
signed flow, or future ticks.
"""
from __future__ import annotations
from nq_tick_short_horizon import dev_day,complete,LAST_SIGNAL

FAMILIES=('T13_FULL','A13_NO_VOLUME','A13_WEAK_RETRACE')
FIRST_SIGNAL=1440 # 10:00 ET from 08:00 start, index=7200sec/5
HISTORY=30

def impulse_signal(bars,i,side,no_volume=False,weak_retrace=False):
    """Causal closed-bar snapshot [i-30:i+1], shock i-6..i-3, retrace i-2..i."""
    if not FIRST_SIGNAL<=i<LAST_SIGNAL or side not in (-1,1):
        return False
    window=complete(bars,i-HISTORY,i+1)
    if window is None:
        return False
    context=window[:24]    # i-30..i-7, 24 5s bars
    shock=window[24:28]    # i-6..i-3, 4 bars
    current=window[30]    # i, last fully closed decision bar
    prior_qty=sum(b[5] for b in context)
    shock_qty=sum(b[5] for b in shock)
    if prior_qty<24:return False
    if not no_volume and 24*shock_qty<8*prior_qty:
        return False
    displacement=shock[-1][3]-context[-1][3]  # 4-bar impact since pre-shock close
    if abs(displacement)<12:return False
    shock_dir=(1 if displacement>0 else -1)
    if side!=-shock_dir:return False
    retrace=shock_dir*(shock[-1][3]-current[3])
    needed=2 if weak_retrace else max(6,(abs(displacement)+1)//2)
    if retrace<needed:return False
    if shock_dir*(current[3]-current[0])>=0:
        return False
    return True

def candidates_t13(bars,day):
    """Return FIRST eligible completed 5s-bar signal per model for entire day."""
    dev_day(day)
    result={k:[] for k in FAMILIES}
    for i in range(FIRST_SIGNAL,LAST_SIGNAL):
        if complete(bars,i-HISTORY,i+1) is None:
            continue
        for name in FAMILIES:
            if result[name]:continue # at most ONE candidate/day per strategy
            directions=[side for side in (-1,1) if impulse_signal(
                bars,i,side,no_volume=(name=='A13_NO_VOLUME'),
                weak_retrace=(name=='A13_WEAK_RETRACE'))]
            if len(directions)==1:
                result[name].append((i,directions[0]))
            elif len(directions)>1:
                raise AssertionError('Simultaneous opposing shock direction')
    return result,0
