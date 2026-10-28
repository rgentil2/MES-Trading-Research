#!/usr/bin/env python3
"""S0.20 12 causal NQ candlestick-pattern prototype scalar classifiers.

Returns -1/0/+1 for completed RTH candles; custom thresholds, NOT equivalent
to TA-Lib / StrategyQuant candle pattern conventions. Both catalogue fields
(body_ratio, shadow_ratio) participate in each rule. Technical incubator only.
No historical data read; not promoted to frozen V2.1 or used for trading.
"""
from __future__ import annotations
import math
import numpy as np

PATTERNS=frozenset((
    "Doji","Hammer","Shooting Star","Engulfing","Harami",
    "Morning Star","Evening Star","Three White Soldiers",
    "Three Black Crows","Inside Bar","Outside Bar","Marubozu"
))
STATUS="S0_20_PATTERN_PROTOTYPES_CUSTOM_CONVENTIONS_UNCERTIFIED"


def _geometry(candle:np.ndarray):
    o,h,l,c=(float(x) for x in candle[:4])
    length=h-l
    if length<=0:
        return {"body":0.,"upper":0.,"lower":0.,"up":False,"down":False}
    return {"body":abs(c-o)/length,
            "upper":(h-max(c,o))/length,
            "lower":(min(c,o)-l)/length,
            "up":c>o,"down":c<o}


def classify(bars:np.ndarray,idx:int,block:dict)->int|None:
    if not isinstance(bars,np.ndarray) or bars.ndim!=2 or bars.shape[1]!=5:
        raise ValueError("Expected 5-field OHLCV matrix")
    if type(idx) is not int or idx>=len(bars):
        raise ValueError("No future/invalid bar")
    if idx<0:return None
    if idx>=390:
        raise ValueError("Pass only current RTH session; no cross-session patterns")
    x=bars[:idx+1]
    if (not np.isfinite(x).all() or (x[:,4]<0).any()
            or (x[:,1]<np.maximum(x[:,0],x[:,3])).any()
            or (x[:,2]>np.minimum(x[:,0],x[:,3])).any()):
        raise ValueError("Invalid OHLCV")
    name=block.get("name")
    p=block.get("parameters")
    if name not in PATTERNS or not isinstance(p,dict):
        raise ValueError("Not a registered pattern prototype")
    if set(p)!={"body_ratio","shadow_ratio"}:
        raise ValueError("Every pattern parameter must be active")
    body,shadow=p["body_ratio"],p["shadow_ratio"]
    if (type(body) not in (int,float) or type(shadow) not in (int,float)
            or not math.isfinite(body) or not math.isfinite(shadow)
            or not 0.05<=body<=0.95 or not 0.05<=shadow<=0.95):
        raise ValueError("Invalid pattern thresholds")
    cur=_geometry(x[-1])
    prev=_geometry(x[-2]) if idx>=1 else None
    old=_geometry(x[-3]) if idx>=2 else None
    c=x[-1]
    if name=="Doji":
        return int(cur["body"]<=body and
                   min(cur["upper"],cur["lower"])>=shadow/2)
    if name=="Hammer":
        return int(cur["body"]<=body and cur["lower"]>=shadow
                   and cur["upper"]<=cur["body"])
    if name=="Shooting Star":
        return -int(cur["body"]<=body and cur["upper"]>=shadow
                    and cur["lower"]<=cur["body"])
    if name=="Marubozu":
        yes=cur["body"]>=body and max(cur["upper"],cur["lower"])<=shadow
        return (1 if cur["up"] else -1 if cur["down"] else 0) if yes else 0
    if prev is None:return None
    if name=="Engulfing":
        # Prior body entirely inside current body; wick tolerance active.
        engulf=(min(c[0],c[3])<=min(x[-2,0],x[-2,3])
                and max(c[0],c[3])>=max(x[-2,0],x[-2,3]))
        yes=engulf and cur["body"]>=body and max(cur["upper"],cur["lower"])<=shadow
        if yes and cur["up"] and prev["down"]:return 1
        if yes and cur["down"] and prev["up"]:return -1
        return 0
    if name=="Harami":
        internal=(min(c[0],c[3])>=min(x[-2,0],x[-2,3])
                  and max(c[0],c[3])<=max(x[-2,0],x[-2,3]))
        yes=internal and cur["body"]<=body and max(cur["upper"],cur["lower"])<=shadow
        return (1 if cur["up"] else -1 if cur["down"] else 0) if yes else 0
    if name=="Inside Bar":
        yes=(c[1]<x[-2,1] and c[2]>x[-2,2]
             and cur["body"]<=body and max(cur["upper"],cur["lower"])<=shadow)
        return (1 if cur["up"] else -1 if cur["down"] else 0) if yes else 0
    if name=="Outside Bar":
        yes=(c[1]>x[-2,1] and c[2]<x[-2,2]
             and cur["body"]>=body and max(cur["upper"],cur["lower"])<=shadow)
        return (1 if cur["up"] else -1 if cur["down"] else 0) if yes else 0
    if old is None:return None
    if name=="Morning Star":
        yes=(old["down"] and old["body"]>=body
             and prev["body"]<=body and cur["up"] and cur["body"]>=body
             and c[3]>=(x[-3,0]+x[-3,3])/2 and cur["upper"]<=shadow)
        return int(yes)
    if name=="Evening Star":
        yes=(old["up"] and old["body"]>=body
             and prev["body"]<=body and cur["down"] and cur["body"]>=body
             and c[3]<=(x[-3,0]+x[-3,3])/2 and cur["lower"]<=shadow)
        return -int(yes)
    if name in ("Three White Soldiers","Three Black Crows"):
        trio=[_geometry(y) for y in x[-3:]]
        bullish=name=="Three White Soldiers"
        trend=(x[-3,3]<x[-2,3]<x[-1,3]) if bullish else (
               x[-3,3]>x[-2,3]>x[-1,3])
        yes=(trend and all(z["body"]>=body for z in trio)
             and all((z["upper"] if bullish else z["lower"])<=shadow for z in trio)
             and all(z["up"] if bullish else z["down"] for z in trio))
        return (1 if bullish else -1) if yes else 0
    raise AssertionError("Unknown pattern")
