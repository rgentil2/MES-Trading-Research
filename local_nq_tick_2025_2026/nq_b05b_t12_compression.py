#!/usr/bin/env python3
"""T12 independent prior-range compression and completed 5s print acceleration.
NO VWAP or opening-range signal. Exact pre-registered T12, DEV only.
"""
from __future__ import annotations
from nq_tick_short_horizon import dev_day,complete,LAST_SIGNAL

FAMILIES=('T12_FULL','A12_NO_ACTIVITY','A12_NO_COMPRESSION')
FIRST_SIGNAL=1200  # 09:40 ET, anchored 08:00
HISTORY=60
COOLDOWN=60

def signal_at(bars,i,side,without_activity=False,without_compression=False):
    if i<FIRST_SIGNAL or i>=LAST_SIGNAL or side not in (-1,1):
        return False
    window=complete(bars,i-HISTORY,i+1)
    if window is None:return False
    previous=window[:48]          # [i-60, i-13] inclusive
    compressed=window[48:60]      # [i-12, i-1] inclusive
    current=window[-1]            # i complete, NEVER in compression high/low
    older_range=max(b[1] for b in previous)-min(b[2] for b in previous)
    recent_hi=max(b[1] for b in compressed)
    recent_lo=min(b[2] for b in compressed)
    recent_range=recent_hi-recent_lo
    if older_range<32 or recent_range<2:
        return False
    if not without_compression and 5*recent_range>max(40,2*older_range):
        # 5*Rshort <= max(40,2*Rprev) == max(8,floor(0.4*Rprev))
        return False
    if side==1:
        breakout=(current[3]>=recent_hi+2 and current[3]>current[0])
    else:
        breakout=(current[3]<=recent_lo-2 and current[3]<current[0])
    if not breakout:return False
    if not without_activity:
        previous_prints=sum(b[4] for b in window[49:55])  # i-11...i-6
        current_prints=sum(b[4] for b in window[55:61])   # i-5...i
        if previous_prints<20 or 100*current_prints<125*previous_prints:
            return False
    return True

def candidates_t12(bars,day):
    """Every decision uses only completed bars <= i; cooldown global by model."""
    dev_day(day)
    output={k:[] for k in FAMILIES}
    last={k:-100000 for k in FAMILIES}
    both=0
    for i in range(FIRST_SIGNAL,LAST_SIGNAL):
        if complete(bars,i-HISTORY,i+1) is None:
            continue
        for name in FAMILIES:
            if i-last[name]<COOLDOWN:continue
            sides=[side for side in (-1,1) if signal_at(
                bars,i,side,
                without_activity=(name=='A12_NO_ACTIVITY'),
                without_compression=(name=='A12_NO_COMPRESSION'))]
            if len(sides)==1:
                output[name].append((i,sides[0]))
                last[name]=i
            elif sides:
                both+=1
    return output,both
