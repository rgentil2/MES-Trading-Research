#!/usr/bin/env python3
"""V2.6 UNRELEASED causal numeric primitives for remaining 65 NQ M1 indicators.

No market reads, no fills, no economic evaluation. Numeric conventions must
be independently compared to external platforms before trading certification.
All arrays are completed OHLCV bars, in chronological order.
"""
from __future__ import annotations
import math
import numpy as np

def input_frame(bars,idx):
    if not isinstance(bars,np.ndarray) or bars.ndim!=2 or bars.shape[1]!=5:
        raise ValueError("Expected NQ OHLCV matrix")
    if type(idx) is not int or idx>=len(bars):
        raise ValueError("Index unavailable or lookahead")
    if idx<0:return None
    a=np.asarray(bars[:idx+1],dtype=float)
    if (not np.isfinite(a).all() or (a[:,4]<0).any() or
            (a[:,1]<np.maximum(a[:,0],a[:,3])).any() or
            (a[:,2]>np.minimum(a[:,0],a[:,3])).any()):
        raise ValueError("Invalid completed OHLCV")
    return a

def series_ema(a,n):
    a=np.asarray(a,dtype=float); out=np.full(len(a),np.nan)
    if len(a)<n:return out
    if not np.isfinite(a[:n]).all():return out
    out[n-1]=np.mean(a[:n])
    alpha=2./(n+1)
    for i in range(n,len(a)):
        if np.isfinite(a[i]):
            out[i]=out[i-1]+alpha*(a[i]-out[i-1])
        else:out[i]=np.nan
    return out

def series_sma(a,n):
    a=np.asarray(a,dtype=float); out=np.full(len(a),np.nan)
    if len(a)<n:return out
    for i in range(n-1,len(a)):
        x=a[i-n+1:i+1]
        if np.isfinite(x).all():out[i]=float(np.mean(x))
    return out

def series_rma(a,n):
    a=np.asarray(a,dtype=float);out=np.full(len(a),np.nan)
    if len(a)<n:return out
    if not np.isfinite(a[:n]).all():return out
    out[n-1]=float(np.mean(a[:n]))
    for i in range(n,len(a)):
        if np.isfinite(a[i]):out[i]=out[i-1]+(a[i]-out[i-1])/n
    return out

def series_tr(x):
    c=x[:,3];prev=np.r_[c[0],c[:-1]]
    return np.maximum.reduce((x[:,1]-x[:,2],abs(x[:,1]-prev),abs(x[:,2]-prev)))

def series_atr(x,n):
    # TA-Lib style seed: first TR needs previous close; ATR index=n
    arr=series_tr(x)
    w=series_rma(arr[1:],n)
    return np.r_[np.nan,w]

def series_rsi(a,n):
    a=np.asarray(a,dtype=float)
    dx=np.diff(a)
    ups=np.maximum(dx,0)
    downs=np.maximum(-dx,0)
    if len(a)<=n:return np.full(len(a),np.nan)
    up=series_rma(ups,n)
    dn=series_rma(downs,n)
    out=np.full(len(a),np.nan)
    for i in range(n,len(a)):
        u,d=up[i-1],dn[i-1]
        out[i]=(100*u/(u+d)) if u+d>0 else 50.
    return out

def scalar(x):
    return float(x) if np.isscalar(x) and np.isfinite(x) else None

def diff(a,b):
    return a-b if np.isfinite(a) and np.isfinite(b) else np.nan

def ema_last(a,n):
    z=series_ema(a,n)
    return scalar(z[-1]) if len(z) else None

def rolling_sum(a,n):
    return series_sma(a,n)*n

def sign(a):
    return np.sign(np.asarray(a,dtype=float))

def valid_period(p, key, low, high):
    n=p.get(key)
    if type(n) is not int or not low<=n<=high:
        raise ValueError(f"{key} must be integer {low}..{high}")
    return n

def fully_finite(*values):
    return all(v is not None and np.isfinite(v) for v in values)

def safe_div(x,y):
    return float(x/y) if np.isfinite(x) and np.isfinite(y) and abs(y)>1e-12 else None

def signed_threshold(result,p,name):
    """Registry 'threshold' is a zero-crossing level, NOT an inert calculator arg.

    Legacy catalogue overloads mathematical and predicate fields. V2.6 maps
    threshold to explicit raw-minus-threshold numeric output. New typed ASTs
    must compare this output with zero; no indicator can silently discard it.
    """
    if result is None:return None
    if 'threshold' not in p:return result
    return float(result-float(p['threshold']))

def require_context(context,key):
    if not isinstance(context,dict) or key not in context:
        return None
    return context[key]
