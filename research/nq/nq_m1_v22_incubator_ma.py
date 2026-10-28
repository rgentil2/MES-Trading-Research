#!/usr/bin/env python3
"""NQ S0 incubator: DEMA, TEMA and TRIMA price-source variants.

MUST NOT be added to V2.1 frozen 38 calculator set without a new registered
campaign and independent TA-Lib parity. No price files opened by module.
"""
from __future__ import annotations
import math
import numpy as np
from research.nq.nq_m1_v2_m1_engine import _causal_price_source

PROTOTYPES=frozenset(("DEMA","TEMA","TRIMA"))
STATUS="V22_INCUBATOR_UNRELEASED_FROM_FROZEN_V21_ENGINEERING_AST"


def _ema(series:np.ndarray,n:int)->np.ndarray:
    out=np.full(len(series),np.nan,dtype=float)
    if len(series)<n:return out
    out[n-1]=float(np.mean(series[:n]))
    for j in range(n,len(series)):
        out[j] = out[j-1] + (2./(n+1))*(series[j]-out[j-1])
    return out


def _sma(series:np.ndarray,n:int)->np.ndarray:
    out=np.full(len(series),np.nan,dtype=float)
    if len(series)<n:return out
    c=np.cumsum(np.insert(series,0,0.))
    out[n-1:] = (c[n:]-c[:-n])/n
    return out


def calc(bars:np.ndarray, idx:int, block:dict)->float|None:
    if (not isinstance(bars,np.ndarray) or bars.ndim!=2
            or bars.shape[1]!=5):
        raise ValueError("Complete finite M1 OHLCV required for incubator")
    if idx<0:return None
    if idx>=len(bars):raise ValueError("Future not available")
    if not np.isfinite(bars[:idx+1]).all():
        raise ValueError("Nonfinite completed price")
    name=block["name"]
    if name not in PROTOTYPES:
        raise ValueError("Unreleased technical indicator name")
    p=block["parameters"]
    if set(p)!={"period","source"}:
        raise ValueError("No inactive parameters allowed for new moving averages")
    n=p["period"]
    if type(n) is not int or not 2<=n<=390:
        raise ValueError("Period must be integer 2..390")
    source=_causal_price_source(bars[:idx+1],p["source"])
    # Composite EMA requires 2n-1 (DEMA) or 3n-2 (TEMA)
    # COMPLETED samples. Before this warmup, the old TEMA could index
    # an empty third EMA array and crash instead of returning None.
    minimum = (3*n-2 if name=="TEMA" else
               2*n-1 if name=="DEMA" else n)
    if len(source)<minimum:
        return None
    if name=="TRIMA":
        # Explicit TA-Lib convention:
        # odd n=2*k+1 -> SMA(k+1) of SMA(k+1);
        # even n=2*k  -> SMA(k) of SMA(k+1).
        a=(n+1)//2
        b=n//2+1
        first=_sma(source,a)
        valid=first[a-1:]
        second=_sma(valid,b)
        res=second[-1]
    else:
        one=_ema(source,n)
        two_valid=_ema(one[n-1:],n)
        if name=="DEMA":
            res=2*one[-1]-two_valid[-1]
        else:
            three_valid=_ema(two_valid[n-1:],n)
            res=3*one[-1]-3*two_valid[-1]+three_valid[-1]
    return float(res) if np.isfinite(res) else None
