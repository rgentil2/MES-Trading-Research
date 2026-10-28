#!/usr/bin/env python3
"""S0.19 additional NQ M1 *isolated* indicator implementations.

Not registered as V2.1 executable, no backtest or historical input is read.
This technical module specifies exact single-scalar conventions; it MUST NOT
be promoted as 132-certified or used for economic selection before independent
reference review, parameter semantic lints, and source-session warmup testing.

Multi-output and previous-session anchored blocks remain fail-closed rather
than silently choosing a favorable line or fabricating missing context.
"""
from __future__ import annotations
import math
import numpy as np

PROTOTYPES=frozenset({
    "HMA","ALMA","ZLEMA","Qstick","VWMA","Linear Regression Slope",
    "Regression R²","Rolling Quantile","Entropy","Opening Range",
    "Initial Balance","Price Volume Rank"
})
STATUS="V25_ISOLATED_TECHNICAL_SCALARS_NOT_V21_CERTIFIED"
SOURCES=frozenset(("open","high","low","close","hl2","hlc3","ohlc4"))


def _wma(x:np.ndarray)->float:
    n=len(x)
    w=np.arange(1,n+1,dtype=float)
    return float(np.dot(w,x)/np.sum(w))


def _source(b:np.ndarray,name:str)->np.ndarray:
    if name not in SOURCES:
        raise ValueError("Unsupported source; never silently default to close")
    o,h,l,c=b[:,0],b[:,1],b[:,2],b[:,3]
    return {"open":o,"high":h,"low":l,"close":c,
            "hl2":(h+l)/2,"hlc3":(h+l+c)/3,"ohlc4":(o+h+l+c)/4}[name]


def value(bars:np.ndarray, idx:int, block:dict)->float|None:
    if not isinstance(bars,np.ndarray) or bars.ndim!=2 or bars.shape[1]!=5:
        raise ValueError("Expected OHLCV matrix")
    if type(idx) is not int or idx>=len(bars):
        raise ValueError("Future/current index unavailable")
    if idx<0:return None
    x=bars[:idx+1]
    if (not np.isfinite(x).all() or (x[:,4]<0).any()
            or (x[:,1]<x[:,2]).any()
            or (x[:,1]<np.maximum(x[:,0],x[:,3])).any()
            or (x[:,2]>np.minimum(x[:,0],x[:,3])).any()):
        raise ValueError("Invalid completed OHLCV")
    name=block.get("name")
    p=block.get("parameters")
    if name not in PROTOTYPES or not isinstance(p,dict):
        raise ValueError("Unregistered incubator")
    expected={
        "HMA":{"period","source"}, "ALMA":{"period","source"},
        "ZLEMA":{"period","source"}, "Qstick":{"period"},
        "VWMA":{"period","anchor"},
        "Linear Regression Slope":{"period"},"Regression R²":{"period"},
        "Rolling Quantile":{"period"},"Entropy":{"period"},
        "Opening Range":{"minutes"},"Initial Balance":{"minutes"},
        "Price Volume Rank":{"period"}
    }[name]
    if set(p)!=expected:
        raise ValueError("Missing or inactive prototype parameter")
    if "anchor" in p and p["anchor"]!="session":
        raise ValueError("Previous-session/timestamp anchors need authenticated source context")
    if "source" in p and p["source"] not in SOURCES:
        raise ValueError("Source must correspond to an implemented price stream")
    parameter="minutes" if "minutes" in p else "period"
    n=p[parameter]
    bounds={
        "Opening Range":(1,60),"Initial Balance":(15,120),
        "HMA":(2,390),"ALMA":(2,390),"ZLEMA":(2,390),
        "VWMA":(2,390),"Qstick":(3,180),
        "Linear Regression Slope":(5,300),"Regression R²":(5,300),
        "Rolling Quantile":(5,300),"Entropy":(5,300),
        "Price Volume Rank":(2,390)
    }[name]
    if type(n) is not int or not bounds[0]<=n<=bounds[1]:
        raise ValueError("Parameter out of catalogue range")
    c=x[:,3]
    if name in ("Opening Range","Initial Balance"):
        # Source must be current RTH session, beginning with end-label 09:31.
        # No value before window completed; output is range WIDTH (one scalar).
        if len(x)>390:
            raise ValueError("Session-anchored range requires current RTH slice")
        return (float(np.max(x[:n,1])-np.min(x[:n,2]))
                if len(x)>=n else None)
    if name=="Entropy":
        if len(c)<n+1:return None
        ret=np.diff(c[-n-1:])
        counts=np.array([(ret<0).sum(),(ret==0).sum(),(ret>0).sum()],dtype=float)
        f=counts[counts>0]/n
        return float(-np.sum(f*np.log(f))/math.log(3.))
    if name=="Price Volume Rank":
        if len(c)<n+1:return None
        signed=np.diff(c[-n-1:])*x[-n:,4]
        return float(100*np.mean(signed<=signed[-1]))
    if name=="HMA":
        raw=_source(x,p["source"])
        k=max(1,n//2)
        tail=max(1,int(math.sqrt(n)))
        if len(raw)<n+tail-1:return None
        diff=np.array([2*_wma(raw[-z-k:-z] if z else raw[-k:])
                       -_wma(raw[-z-n:-z] if z else raw[-n:])
                       for z in range(tail-1,-1,-1)],dtype=float)
        return _wma(diff)
    if name=="ZLEMA":
        raw=_source(x,p["source"])
        lag=(n-1)//2
        if len(raw)<n+lag:return None
        adj=raw.copy() if lag==0 else raw[lag:]+raw[lag:]-raw[:-lag]
        ema=float(np.mean(adj[:n]))
        alpha=2/(n+1)
        for v in adj[n:]:
            ema+=alpha*(float(v)-ema)
        return ema
    if name=="ALMA":
        raw=_source(x,p["source"])
        if len(raw)<n:return None
        # Freeze 0.85 offset / sigma=6; catalog only varies active period/source.
        j=np.arange(n,dtype=float)
        weights=np.exp(-((j-0.85*(n-1))**2)/(2*(n/6)**2))
        return float(np.dot(weights,raw[-n:])/weights.sum())
    if len(c)<n:return None
    if name=="Qstick":
        return float(np.mean(x[-n:,3]-x[-n:,0]))
    if name=="VWMA":
        v=x[-n:,4]
        return float(np.dot(c[-n:],v)/v.sum()) if v.sum()>0 else None
    if name=="Rolling Quantile":
        # Explicit 0.50 quantile/median, NOT a variable optimized quantile.
        return float(np.median(c[-n:]))
    if name in ("Linear Regression Slope","Regression R²"):
        y=c[-n:]
        t=np.arange(n,dtype=float)
        centered=t-t.mean()
        yy=y-y.mean()
        den=float(np.dot(centered,centered))
        slope=float(np.dot(centered,yy)/den)
        if name=="Linear Regression Slope":return slope
        ss=float(np.dot(yy,yy))
        return float(min(1.,max(0.,(slope*slope*den)/ss))) if ss>0 else None
    raise AssertionError("Unknown isolated implementation")
