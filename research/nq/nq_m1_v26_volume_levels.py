#!/usr/bin/env python3
"""21 V2.6 volume, volatility, anchored level and pivot prototypes.

Pivots are based on a *causal* explicitly selected completed-bar window:
session = current completed RTH window; previous_completed_session = distinct,
same-contract prior 390-bar RTH session; causal_timestamp requires an explicit
bar anchor known at decision time. No fabricated prior sessions or silent
fallbacks. Multiline bands can choose upper/lower/middle via block['output'].
"""
from __future__ import annotations
import math
import numpy as np
from research.nq.nq_m1_v26_math import (
 series_ema as ema,series_sma as sma,series_atr as atr,
 series_tr as tr,scalar,valid_period,safe_div
)

NAMES=frozenset({
 "Bollinger Bands","Keltner","Chaikin Volatility","Mass Index",
 "Acceleration Bands","Accumulation/Distribution","Chaikin Oscillator",
 "Ease of Movement","Klinger Oscillator","Positive Volume Index",
 "Negative Volume Index","Price Volume Trend","Percentage Volume Oscillator",
 "Anchored VWAP","Central Pivot Range","Classic Pivots","Fibonacci Pivots",
 "Camarilla Pivots","Woodie Pivots","DeMark Pivots","Previous Day High/Low"
})

def _flow(x):
    h,l,c,v=x[:,1],x[:,2],x[:,3],x[:,4]
    width=h-l
    mf=np.divide(2*c-h-l,width,out=np.zeros(len(x)),where=width>0)
    return mf*v

def _get_anchor(x,kind,n,context):
    if kind=="session":
        return x[-n:] if len(x)>=n else None
    if kind=="causal_timestamp":
        if not isinstance(context,dict) or type(context.get("anchor_index")) is not int:
            return None
        start=context["anchor_index"]
        if start<0 or start>=len(x):return None
        return x[max(start,len(x)-n):] if len(x)-max(start,len(x)-n)>=n else None
    if kind=="previous_completed_session":
        if not isinstance(context,dict) or context.get("verified_same_contract") is not True:
            return None
        sessions=context.get("previous_sessions")
        if not isinstance(sessions,(list,tuple)) or not sessions:return None
        previous=sessions[-1]
        if (not isinstance(previous,np.ndarray) or previous.shape!=(390,5)
                or not np.isfinite(previous).all()
                or (previous[:,1]<np.maximum(previous[:,0],previous[:,3])).any()
                or (previous[:,2]>np.minimum(previous[:,0],previous[:,3])).any()):
            return None
        return previous[-n:]
    raise ValueError("Unknown anchor kind")

def _pivot_levels(z,name):
    H=float(np.max(z[:,1]));L=float(np.min(z[:,2]))
    C=float(z[-1,3]);O=float(z[0,0])
    pp=(H+L+C)/3
    if name=="Classic Pivots":
        return {"middle":pp,"upper":2*pp-L,"lower":2*pp-H}
    if name=="Central Pivot Range":
        bc=(H+L)/2;tc=2*pp-bc
        return {"middle":pp,"upper":max(tc,bc),"lower":min(tc,bc)}
    if name=="Fibonacci Pivots":
        return {"middle":pp,"upper":pp+.382*(H-L),"lower":pp-.382*(H-L)}
    if name=="Camarilla Pivots":
        return {"middle":C,"upper":C+1.1*(H-L)/12,"lower":C-1.1*(H-L)/12}
    if name=="Woodie Pivots":
        base=(H+L+2*C)/4
        return {"middle":base,"upper":2*base-L,"lower":2*base-H}
    if name=="DeMark Pivots":
        X=(H+2*L+C if C<O else 2*H+L+C if C>O else H+L+2*C)
        return {"middle":X/4,"upper":X/2-L,"lower":X/2-H}
    raise ValueError("Unknown pivot name")

def _pick(lines,block,default="upper"):
    output=block.get("output",default)
    if output not in lines:
        raise ValueError("Unsupported scalar output line")
    return float(lines[output])

def value(x,name,p,context=None,block=None):
    block=block or {"name":name,"parameters":p}
    c,h,l,o,v=x[:,3],x[:,1],x[:,2],x[:,0],x[:,4]
    L=len(c)
    if name=="Bollinger Bands":
        n=valid_period(p,"period",5,240)
        if L<n:return None
        mean=float(np.mean(c[-n:]));sigma=float(np.std(c[-n:]))
        mult=float(p["std_multiplier"])
        return _pick({"upper":mean+mult*sigma,"lower":mean-mult*sigma,
                     "middle":mean,"width":2*mult*sigma},block)
    if name=="Keltner":
        n=valid_period(p,"ema_period",3,240)
        a=valid_period(p,"atr_period",2,120)
        m=ema(c,n)[-1];at=atr(x,a)[-1]
        if not np.isfinite(m) or not np.isfinite(at):return None
        width=float(p["atr_multiplier"])*at
        return _pick({"upper":m+width,"lower":m-width,"middle":m,"width":2*width},block)
    if name=="Chaikin Volatility":
        n=valid_period(p,"period",2,240)
        rang=h-l
        data=ema(rang,n)
        if L<2*n or not np.isfinite(data[-n-1]):return None
        base=data[-n-1]
        return float(100*(data[-1]/base-1)*float(p["multiplier"])) if base>0 else None
    if name=="Mass Index":
        n=valid_period(p,"period",2,240)
        rang=h-l
        e1=ema(rang,9);e2=ema(e1[8:],9)
        if len(e2)<n or not np.isfinite(e2[-n:]).all():return None
        ratios=e1[8:][-n:]/e2[-n:]
        return float(ratios.sum()*float(p["multiplier"])) if (e2[-n:]>0).all() else None
    if name=="Acceleration Bands":
        n=valid_period(p,"period",2,240)
        if L<n:return None
        mid=(h[-n:]+l[-n:])
        spread=np.divide(h[-n:]-l[-n:],mid,out=np.zeros(n),where=mid!=0)
        factor=float(p["multiplier"])
        upper=np.mean(h[-n:]*(1+factor*spread))
        lower=np.mean(l[-n:]*(1-factor*spread))
        return _pick({"upper":upper,"lower":lower,
                      "middle":np.mean(c[-n:]),"width":upper-lower},block)
    if name in ("Accumulation/Distribution","Chaikin Oscillator"):
        n=valid_period(p,"period",2,240)
        flows=_flow(x)
        if name=="Accumulation/Distribution":
            return float(flows[-n:].sum()) if L>=n else None
        adl=np.cumsum(flows)
        f=max(2,n//3)
        first=ema(adl,f)[-1];second=ema(adl,n)[-1]
        return scalar(first-second)
    if name=="Ease of Movement":
        n=valid_period(p,"period",2,240)
        if L<=n:return None
        midpoint=(h+l)/2
        movement=np.diff(midpoint)
        span=h[1:]-l[1:]
        # Report standardized volume in units of one million.
        effort=np.divide(movement*span,np.maximum(v[1:]/1e6,1e-12))
        return float(effort[-n:].mean())
    if name=="Klinger Oscillator":
        n=valid_period(p,"period",2,240)
        if L<n+2:return None
        direction=np.sign(np.diff((h+l+c)/3))
        flow=direction*v[1:]*(h[1:]-l[1:])
        f=max(2,n//3)
        long=ema(flow,n)[-1];short=ema(flow,f)[-1]
        return scalar(short-long)
    if name in ("Positive Volume Index","Negative Volume Index","Price Volume Trend"):
        n=valid_period(p,"period",2,240)
        if L<=n:return None
        start=L-n-1
        level=1000. if name!="Price Volume Trend" else 0.
        for i in range(start+1,L):
            ret=(c[i]/c[i-1]-1) if c[i-1]!=0 else 0.
            if name=="Positive Volume Index" and v[i]>v[i-1]:level*=1+ret
            elif name=="Negative Volume Index" and v[i]<v[i-1]:level*=1+ret
            elif name=="Price Volume Trend":level+=v[i]*ret
        return float(level)
    if name=="Percentage Volume Oscillator":
        n=valid_period(p,"period",2,240)
        short=max(2,n//3)
        f=ema(v,short)[-1];s=ema(v,n)[-1]
        return float(100*(f/s-1)) if np.isfinite(f+s) and s>0 else None
    if name=="Anchored VWAP":
        kind=p["anchor"]
        if kind=="session":z=x
        elif kind=="causal_timestamp":
            if not isinstance(context,dict) or type(context.get("anchor_index")) is not int:
                return None
            start=context["anchor_index"]
            if start<0 or start>=L:return None
            z=x[start:]
        else:raise ValueError("Unknown VWAP anchor")
        total=z[:,4].sum()
        return float(np.dot((z[:,1]+z[:,2]+z[:,3])/3,z[:,4])/total) if total>0 else None
    if name in ("Central Pivot Range","Classic Pivots","Fibonacci Pivots",
                "Camarilla Pivots","Woodie Pivots","DeMark Pivots"):
        n=valid_period(p,"period",2,390)
        z=_get_anchor(x,p["anchor"],n,context)
        if z is None:return None
        return _pick(_pivot_levels(z,name),block,default="middle")
    if name=="Previous Day High/Low":
        k=valid_period(p,"sessions_back",1,20)
        if not isinstance(context,dict) or context.get("verified_same_contract") is not True:
            return None
        sessions=context.get("previous_sessions")
        if not isinstance(sessions,(tuple,list)) or len(sessions)<k:return None
        past=sessions[-k]
        if (not isinstance(past,np.ndarray) or past.shape!=(390,5)
                or not np.isfinite(past).all()):return None
        hi=float(max(past[:,1]));lo=float(min(past[:,2]))
        return _pick({"upper":hi,"lower":lo,"middle":(hi+lo)/2,
                      "width":hi-lo},block,default="upper")
    raise ValueError("Unknown volatility/volume/pivot indicator")
