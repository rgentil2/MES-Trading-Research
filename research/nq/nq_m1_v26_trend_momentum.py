#!/usr/bin/env python3
"""27 isolated V2.6 trend/momentum prototypes (not TA-Lib certified).
Each name maps to an explicit, distinct causal scalar convention. A
registered 'threshold' becomes an active zero-crossing offset, not ignored
metadata. Never use as broker-validated fill or trading evidence.
"""
from __future__ import annotations
import math
import numpy as np
from research.nq.nq_m1_v26_math import (
    series_ema as ema,series_sma as sma,series_rma as rma,
    series_atr as atr,series_tr as tr,series_rsi as rsi,
    scalar,signed_threshold,valid_period,safe_div
)

NAMES=frozenset({
 "KAMA","T3","ADX","ADXR","Vortex","SuperTrend","Parabolic SAR",
 "Ichimoku","Chande Kroll Stop","Trend Intensity Index","TTM Trend",
 "Stochastic","Stochastic RSI","TSI","Ultimate Oscillator",
 "Connors RSI","Relative Vigor Index","MACD","PPO",
 "Schaff Trend Cycle","Know Sure Thing","Awesome Oscillator",
 "Accelerator Oscillator","Fisher Transform","Coppock Curve",
 "QQE","SMI Ergodic"
})

def _stochastic(a,n,smooth,signal):
    result=np.full(len(a),np.nan)
    for i in range(n-1,len(a)):
        window=a[i-n+1:i+1]
        mn,mx=float(np.min(window)),float(np.max(window))
        result[i]=100*(a[i]-mn)/(mx-mn) if mx>mn else 50.
    sm=sma(result[slice(n-1,None)],smooth)
    final=sma(sm[slice(smooth-1,None)],signal)
    first=n-1+smooth-1+signal-1
    return float(final[-1]) if len(a)>first else None

def _macd(c,f,s,signal):
    ef=ema(c,f);es=ema(c,s);main=ef-es
    if len(main)<s:return None
    sig=ema(main[s-1:],signal)
    if not np.isfinite(sig[-1]):return None
    return float(main[-1]),float(sig[-1])

def _adx(x,n):
    if len(x)<2*n+1:return np.full(len(x),np.nan)
    h,l=x[:,1],x[:,2]
    up=np.diff(h);down=-np.diff(l)
    plus=np.where((up>down)&(up>0),up,0.)
    minus=np.where((down>up)&(down>0),down,0.)
    true=tr(x)[1:]
    smtr=rma(true,n);smplus=rma(plus,n);smminus=rma(minus,n)
    dx=np.full(len(true),np.nan)
    for i in range(n-1,len(true)):
        if smtr[i]>0:
            pos=100*smplus[i]/smtr[i]
            neg=100*smminus[i]/smtr[i]
            dx[i]=100*abs(pos-neg)/(pos+neg) if pos+neg>0 else 0.
    out=np.full(len(x),np.nan)
    adx=rma(dx[n-1:],n)
    out[(2*n-1):]=adx[n-1:]
    return out

def _sar(x,p):
    n=p["period"]
    if len(x)<n:return None
    h,l,c=x[:,1],x[:,2],x[:,3]
    trend=1 if c[n-1]>=c[0] else -1
    sar=float(np.min(l[:n]) if trend>0 else np.max(h[:n]))
    extreme=float(np.max(h[:n]) if trend>0 else np.min(l[:n]))
    step=float(p["threshold"])/1000.
    af=step
    for i in range(n,len(x)):
        proposal=sar+af*(extreme-sar)
        if trend>0:
            proposal=min(proposal,float(l[i-1]),float(l[i-2]))
            if l[i]<proposal:
                trend=-1;sar=extreme;extreme=float(l[i]);af=step
            else:
                sar=proposal
                if h[i]>extreme:extreme=float(h[i]);af=min(.20,af+step)
        else:
            proposal=max(proposal,float(h[i-1]),float(h[i-2]))
            if h[i]>proposal:
                trend=1;sar=extreme;extreme=float(h[i]);af=step
            else:
                sar=proposal
                if l[i]<extreme:extreme=float(l[i]);af=min(.20,af+step)
    return float(c[-1]-sar)

def value(x,name,p):
    c,h,l,o,v=x[:,3],x[:,1],x[:,2],x[:,0],x[:,4]
    L=len(c)
    if name in ("KAMA","T3"):
        n=valid_period(p,"period",2,390)
        a=np.asarray({"open":o,"high":h,"low":l,"close":c,"hl2":(h+l)/2,
            "hlc3":(h+l+c)/3,"ohlc4":(o+h+l+c)/4}[p["source"]])
        if name=="KAMA":
            if L<=n:return None
            z=float(a[n]);fast=2./3;slow=2./31
            for i in range(n+1,L):
                movement=abs(a[i]-a[i-n]);noise=float(np.sum(np.abs(np.diff(a[i-n:i+1]))))
                efficiency=movement/noise if noise>0 else 0.
                k=(efficiency*(fast-slow)+slow)**2
                z+=k*(float(a[i])-z)
            return z
        if L<6*(n-1)+1:return None
        # T3 volume factor 0.7; c1..c4 convention
        z=.7
        c1=-z**3;c2=3*z*z+3*z**3
        c3=-6*z*z-3*z-3*z**3;c4=1+3*z+3*z*z+z**3
        e1=ema(a,n)[n-1:];e2=ema(e1,n)[n-1:]
        e3=ema(e2,n)[n-1:];e4=ema(e3,n)[n-1:]
        e5=ema(e4,n)[n-1:];e6=ema(e5,n)[n-1:]
        return scalar(c1*e6[-1]+c2*e5[-1]+c3*e4[-1]+c4*e3[-1])
    if name in ("ADX","ADXR"):
        n=valid_period(p,"period",3,120 if name=="ADX" else 180)
        data=_adx(x,n)
        if name=="ADXR":
            if L<=n or not np.isfinite(data[-n-1]):return None
            out=(data[-1]+data[-n-1])/2
        else:out=data[-1]
        return signed_threshold(scalar(out),p,name)
    if name=="Vortex":
        n=valid_period(p,"period",3,180)
        if L<=n:return None
        vmplus=np.abs(h[1:]-l[:-1])
        vmminus=np.abs(l[1:]-h[:-1])
        den=np.sum(tr(x)[-n:])
        output=100*(np.sum(vmplus[-n:])-np.sum(vmminus[-n:]))/den if den>0 else None
        return signed_threshold(output,p,name)
    if name=="SuperTrend":
        n=valid_period(p,"atr_period",3,120)
        multiple=float(p["atr_multiplier"])
        a=atr(x,n)
        if not np.isfinite(a[-1]):return None
        upper=(h+l)/2+multiple*a
        lower=(h+l)/2-multiple*a
        last_lower=float(lower[n]);last_upper=float(upper[n])
        trend=1 if c[n]>=last_lower else -1
        for i in range(n+1,L):
            final_lower=float(lower[i]) if lower[i]>last_lower or c[i-1]<last_lower else last_lower
            final_upper=float(upper[i]) if upper[i]<last_upper or c[i-1]>last_upper else last_upper
            if trend>0 and c[i]<final_lower:trend=-1
            elif trend<0 and c[i]>final_upper:trend=1
            last_lower,last_upper=final_lower,final_upper
        return float(c[-1]-(last_lower if trend>0 else last_upper))
    if name=="Parabolic SAR":
        n=valid_period(p,"period",3,180)
        return _sar(x,p)
    if name=="Ichimoku":
        n=valid_period(p,"period",3,180);displacement=int(p["threshold"])
        target=L-1-displacement
        if target<2*n-1:return None
        tenkan=max(2,n//3)
        conv=(max(h[target-tenkan+1:target+1])+min(l[target-tenkan+1:target+1]))/2
        base=(max(h[target-n+1:target+1])+min(l[target-n+1:target+1]))/2
        spanb=(max(h[target-2*n+1:target+1])+min(l[target-2*n+1:target+1]))/2
        cloud=((conv+base)/2+spanb)/2
        return float(c[-1]-cloud)
    if name=="Chande Kroll Stop":
        n=valid_period(p,"period",3,180)
        a=atr(x,n)
        if L<n+1 or not np.isfinite(a[-1]):return None
        longstop=float(max(h[-n:])-2*a[-1])
        return signed_threshold(float(c[-1]-longstop),p,name)
    if name=="Trend Intensity Index":
        n=valid_period(p,"period",3,180)
        if L<2*n-1:return None
        mean=sma(c,n)
        d=c[-n:]-mean[-n:]
        up=float(np.maximum(d,0).sum());down=float(np.maximum(-d,0).sum())
        raw=100*up/(up+down) if up+down>0 else 50.
        return signed_threshold(raw,p,name)
    if name=="TTM Trend":
        n=valid_period(p,"period",3,180)
        if L<n+1:return None
        above=(c[-n:]>(h[-n-1:-1]+l[-n-1:-1])/2)
        return signed_threshold(float(100*np.mean(above)),p,name)
    if name=="Stochastic":
        k=valid_period(p,"k_period",3,120)
        ks=valid_period(p,"k_smooth",1,20)
        d=valid_period(p,"d_period",1,20)
        raw=np.full(L,np.nan)
        for i in range(k-1,L):
            hi=float(max(h[i-k+1:i+1]));lo=float(min(l[i-k+1:i+1]))
            raw[i]=100*(c[i]-lo)/(hi-lo) if hi>lo else 50.
        z=sma(raw[k-1:],ks)
        q=sma(z[ks-1:],d)
        return scalar(q[-1]) if len(q) else None
    if name=="Stochastic RSI":
        n=valid_period(p,"period",2,120)
        ks=valid_period(p,"k_smooth",1,20)
        d=valid_period(p,"d_period",1,20)
        r=rsi(c,n)
        if L<n+1:return None
        return _stochastic(r[n:],n,ks,d)
    if name in ("MACD","PPO"):
        f=valid_period(p,"fast_period",2,60);s=valid_period(p,"slow_period",6,240)
        sig=valid_period(p,"signal_period",2,60)
        if f>=s:raise ValueError("fast must be < slow")
        pair=_macd(c,f,s,sig)
        if pair is None:return None
        main,signal=pair
        if name=="MACD":return main-signal
        slow=ema(c,s)[-1]
        return float(100*(main-signal)/slow) if slow else None
    if name in ("TSI","SMI Ergodic"):
        n=valid_period(p,"period",2,180 if name=="TSI" else 240)
        if L<2*n:return None
        d=np.diff(c)
        second=max(2,n//2)
        one=ema(d,n)[n-1:];two=ema(one,second)
        ab=ema(abs(d),n)[n-1:];ab2=ema(ab,second)
        if not np.isfinite(two[-1]) or not np.isfinite(ab2[-1]):return None
        val=100*two[-1]/ab2[-1] if ab2[-1]>0 else 0.
        if name=="TSI":return signed_threshold(float(val),p,name)
        scaled=np.divide(100*two,ab2,out=np.full(len(two),np.nan),where=ab2>0)
        valid=scaled[np.isfinite(scaled)]
        if len(valid)<5:return None
        reference=ema(valid,5)[-1]
        return float(val-reference) if np.isfinite(reference) else None
    if name=="Ultimate Oscillator":
        n=valid_period(p,"period",2,180)
        if L<=4*n:return None
        prev=c[:-1]
        bp=c[1:]-np.minimum(l[1:],prev)
        true=np.maximum(h[1:],prev)-np.minimum(l[1:],prev)
        def ratio(k):
            den=float(np.sum(true[-k:]))
            return float(np.sum(bp[-k:])/den) if den>0 else 0.
        raw=100*(4*ratio(n)+2*ratio(2*n)+ratio(4*n))/7
        return signed_threshold(raw,p,name)
    if name=="Connors RSI":
        n=valid_period(p,"period",2,180)
        if L<=n+3:return None
        streak=np.zeros(L)
        for i in range(1,L):
            delta=c[i]-c[i-1]
            streak[i]=(streak[i-1]+1 if streak[i-1]>0 else 1) if delta>0 else (
                (streak[i-1]-1 if streak[i-1]<0 else -1) if delta<0 else 0)
        a=rsi(c,n)[-1];b=rsi(streak,n)[-1]
        changes=np.diff(c[-n-2:])
        rank=100*float(np.mean(changes[:-1]<=changes[-1]))
        return signed_threshold(float((a+b+rank)/3),p,name) if np.isfinite(a+b) else None
    if name=="Relative Vigor Index":
        n=valid_period(p,"period",2,180)
        if L<n:return None
        numerator=np.sum(c[-n:]-o[-n:])
        den=np.sum(h[-n:]-l[-n:])
        raw=100*numerator/den if den>0 else None
        return signed_threshold(raw,p,name)
    if name=="Schaff Trend Cycle":
        n=valid_period(p,"period",2,240)
        if L<3*n+30:return None
        slow=max(4,n);fast=max(2,slow//2)
        macd=ema(c,fast)-ema(c,slow)
        arr=macd[slow-1:]
        if len(arr)<n:return None
        first=np.full(len(arr),np.nan)
        for i in range(n-1,len(arr)):
            a=arr[i-n+1:i+1];span=max(a)-min(a)
            first[i]=100*(arr[i]-min(a))/span if span>0 else 50.
        finite=first[n-1:]
        result=_stochastic(finite,n,3,3)
        return result
    if name=="Know Sure Thing":
        n=valid_period(p,"period",2,240)
        periods=(n,2*n,3*n,4*n);smoothed=[]
        for k in periods:
            if L<=k+9:return None
            roc=100*(c[k:]/c[:-k]-1)
            smoothed.append(ema(roc,10)[-1])
        return scalar(sum((i+1)*z for i,z in enumerate(smoothed)))
    if name in ("Awesome Oscillator","Accelerator Oscillator"):
        n=valid_period(p,"period",2,240)
        midpoint=(h+l)/2
        fast=max(2,n//3)
        s=sma(midpoint,fast);slow=sma(midpoint,n)
        ao=s-slow
        if not np.isfinite(ao[-1]):return None
        if name=="Awesome Oscillator":return float(ao[-1])
        if L<n+4:return None
        finite=ao[n-1:]
        return scalar(finite[-1]-sma(finite,5)[-1])
    if name=="Fisher Transform":
        n=valid_period(p,"period",2,240)
        if L<n+1:return None
        med=(h+l)/2
        z=0.;fish=0.
        for i in range(n-1,L):
            chunk=med[i-n+1:i+1]
            span=float(max(chunk)-min(chunk))
            norm=2*(med[i]-min(chunk))/span-1 if span>0 else 0.
            z=max(-.999,min(.999,.66*norm+.67*z))
            fish=.5*math.log((1+z)/(1-z))+.5*fish
        return float(fish)
    if name=="Coppock Curve":
        n=valid_period(p,"period",2,240)
        k=int(math.ceil(1.4*n))
        if L<=k+n:return None
        r1=100*(c[n:]/c[:-n]-1)
        r2=100*(c[k:]/c[:-k]-1)
        joined=r1[k-n:]+r2
        tail=joined[-n:];weights=np.arange(1,n+1,dtype=float)
        return float(tail@weights/weights.sum())
    if name=="QQE":
        n=valid_period(p,"period",2,240)
        if L<=3*n:return None
        r=rsi(c,n)[n:]
        smooth=ema(r,max(2,n//2))
        valid=smooth[max(2,n//2)-1:]
        if len(valid)<n+1:return None
        dynamic=rma(abs(np.diff(valid)),n)
        if not np.isfinite(dynamic[-1]):return None
        # RSI distance to its own trailing volatility-adjusted EMA.
        reference=ema(valid,n)
        return float(valid[-1]-reference[-1]-4.236*dynamic[-1])
    raise ValueError("Unsupported trend/momentum name")
