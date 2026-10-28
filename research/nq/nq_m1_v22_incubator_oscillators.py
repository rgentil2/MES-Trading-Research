#!/usr/bin/env python3
"""NQ V2.2 indicator incubator: APO and TRIX, not V2.1 execution.

Implement formulas independently from TA-Lib, which CI uses only as an
external numerical oracle. Do not count as one of the frozen 38 runtime
calculators, and never use the formulas to select trading strategies yet.

APO: EMA(fast) - EMA(slow), SMA-seeded EMA, fast < slow.
TRIX: percentage ROC of triple EMA(period), SMA-seeded each stage.
"""
from __future__ import annotations
import math
import numpy as np
from research.nq.nq_m1_v2_m1_engine import _causal_price_source

PROTOTYPES=frozenset(("APO","TRIX"))
STATUS="ISOLATED_MATH_PARITY_ONLY_NOT_ACTIVE_IN_V21"


def _ema_valid(values:np.ndarray,n:int)->np.ndarray:
    """EMA output starting at first available sample index n-1."""
    if len(values)<n:
        return np.empty(0,dtype=float)
    res=np.empty(len(values)-n+1,dtype=float)
    res[0]=float(np.mean(values[:n]))
    alpha=2./(n+1)
    for i,value in enumerate(values[n:],1):
        res[i]=res[i-1]+alpha*(float(value)-res[i-1])
    return res


def indicator_value(bars:np.ndarray,idx:int,block:dict)->float|None:
    if not isinstance(bars,np.ndarray) or bars.ndim!=2 or bars.shape[1]!=5:
        raise ValueError("Expected NQ M1 five-column OHLCV")
    if idx<0:return None
    if idx>=len(bars):raise ValueError("Indicator lookahead")
    if not np.isfinite(bars[:idx+1]).all() or (bars[:idx+1,4]<0).any():
        raise ValueError("Invalid completed OHLCV")
    name=block.get("name")
    params=block.get("parameters")
    if name not in PROTOTYPES or not isinstance(params,dict):
        raise ValueError("Not an incubated technical indicator")
    c=np.ascontiguousarray(bars[:idx+1,3],dtype=float)
    if name=="APO":
        if set(params)!={"fast_period","slow_period"}:
            raise ValueError("APO requires only effective fast and slow periods")
        fast,slow=params["fast_period"],params["slow_period"]
        if (type(fast) is not int or type(slow) is not int
                or not 2<=fast<slow<=240):
            raise ValueError("APO periods out of range")
        if len(c)<slow:return None
        # Two independent EMA histories, same completed close source.
        ema_fast=_ema_valid(c,fast)
        ema_slow=_ema_valid(c,slow)
        return float(ema_fast[-1]-ema_slow[-1])
    if set(params)!={"period"}:
        raise ValueError("TRIX has one active period only")
    n=params["period"]
    if type(n) is not int or not 2<=n<=240:
        raise ValueError("TRIX period out of range")
    # Three EMA stages plus previous EMA3 value, no present-bar lookahead.
    first=_ema_valid(c,n)
    second=_ema_valid(first,n)
    third=_ema_valid(second,n)
    if len(third)<2:return None
    previous=third[-2]
    return float(100.*(third[-1]/previous-1.)) if previous!=0 else None
