#!/usr/bin/env python3
"""17 causal V2.6 cycle/statistics/gap prototypes.

Hilbert-family formulas here use a finite-window FFT analytic signal, NOT
TA-Lib's recursive Hilbert transforms. Ehlers-family formulas are explicitly
specified causal discrete filters. All remain uncertified research prototypes.
"""
from __future__ import annotations
import math
import numpy as np
from research.nq.nq_m1_v26_math import (
 series_ema as ema,series_sma as sma,series_atr as atr,
 series_tr as tr,scalar,valid_period
)

NAMES=frozenset({
 "Hurst Exponent","Hilbert Dominant Cycle Period","Hilbert Phase",
 "Hilbert Sine","Hilbert Trend Mode","Hilbert Phasor",
 "Ehlers Cyber Cycle","Ehlers Sinewave","Ehlers Roofing Filter",
 "Even Better Sinewave","Center of Gravity Oscillator",
 "Autocorrelation Periodogram","Dominant Cycle Period",
 "Opening Gap","Previous Close Gap","NR4/NR7","Volatility Squeeze"
})

def _analytic(x):
    n=len(x)
    wave=np.asarray(x,dtype=float)
    wave=wave-np.mean(wave)
    freq=np.fft.fft(wave)
    scale=np.zeros(n);scale[0]=1
    if n%2==0:scale[n//2]=1;scale[1:n//2]=2
    else:scale[1:(n+1)//2]=2
    return np.fft.ifft(freq*scale)

def _cycle_window(x,n):
    if len(x)<n:return None
    return np.asarray(x[-n:],dtype=float)

def _autocorr_dominant(x,n):
    seg=_cycle_window(x,n)
    if seg is None or n<6:return None
    seg=seg-np.mean(seg)
    best=None
    for lag in range(2,max(3,n//2)+1):
        a,b=seg[:-lag],seg[lag:]
        den=float(np.linalg.norm(a)*np.linalg.norm(b))
        coeff=float(a@b/den) if den>0 else 0.
        if best is None or coeff>best[1]:best=(lag,coeff)
    return float(best[0]) if best and best[1]>0 else None

def _roofing(c,n):
    if len(c)<n+3:return None
    p=max(5,n)
    alpha=2/(p+1)
    hp=np.zeros(len(c),dtype=float)
    for i in range(2,len(c)):
        hp[i]=(1-alpha)**2*(c[i]-2*c[i-1]+c[i-2]) + (
            2*(1-alpha)*hp[i-1]-(1-alpha)**2*hp[i-2])
    filt=ema(hp,max(2,n//4))
    return filt

def _phase(wave,n):
    if len(wave)<n:return None
    z=_analytic(wave[-n:])
    if abs(z[-1])<1e-9:return None
    return float(np.angle(z[-1]))

def _prev_session(context):
    if not isinstance(context,dict) or context.get("verified_same_contract") is not True:
        return None
    a=context.get("previous_sessions")
    if not isinstance(a,(list,tuple)) or not a:return None
    last=a[-1]
    if (not isinstance(last,np.ndarray) or last.shape!=(390,5)
            or not np.isfinite(last).all()
            or (last[:,1]<np.maximum(last[:,0],last[:,3])).any()
            or (last[:,2]>np.minimum(last[:,0],last[:,3])).any()):
        return None
    return last

def value(x,name,p,context=None):
    c,o,h,l,v=x[:,3],x[:,0],x[:,1],x[:,2],x[:,4]
    L=len(c)
    n=valid_period(p,"period",2,390)
    if name=="Opening Gap":
        previous=_prev_session(context)
        if previous is None or n>len(previous):return None
        last=float(previous[-1,3])
        baseline=float(np.mean(tr(previous)[-n:]))
        return float((o[0]-last)/baseline) if baseline>0 else None
    if name=="Previous Close Gap":
        if L<=n:return None
        prev=c[-2]
        meantr=float(np.mean(tr(x)[-n-1:-1]))
        return float((o[-1]-prev)/meantr) if meantr>0 else None
    if name=="NR4/NR7":
        if L<n:return None
        widths=h[-n:]-l[-n:]
        width=float(widths[-1])
        prior=float(np.min(widths[:-1]))
        return float(prior/width-1) if width>0 else None
    if name=="Volatility Squeeze":
        if L<=n:return None
        seg=c[-n:]
        sigma=float(np.std(seg));mid=float(np.mean(seg))
        at=atr(x,n)[-1]
        if not np.isfinite(at) or at<=0:return None
        # positive = Bollinger 2σ lies INSIDE Keltner 1.5 ATR
        return float((1.5*at-2*sigma)/(1.5*at))
    if name=="Hurst Exponent":
        if n<8 or L<n:return None
        window=c[-n:]
        scales=sorted({max(4,n//8),max(5,n//4),max(6,n//2),n})
        xs,ys=[],[]
        for size in scales:
            part=np.diff(window[-size:])
            mean=float(np.mean(part))
            cumulative=np.cumsum(part-mean)
            R=float(np.max(cumulative)-np.min(cumulative))
            S=float(np.std(part))
            if R>0 and S>0:
                xs.append(math.log(size));ys.append(math.log(R/S))
        if len(xs)<2:return None
        return float(np.polyfit(xs,ys,1)[0])
    if name=="Center of Gravity Oscillator":
        if L<n:return None
        a=c[-n:]
        total=float(a.sum())
        if total<=0:return None
        weights=np.arange(1,n+1,dtype=float)
        return float(-(a@weights)/total+(n+1)/2)
    if name=="Autocorrelation Periodogram":
        if L<n or n<6:return None
        window=c[-n:]
        residual=window-np.linspace(window[0],window[-1],n)
        freq=np.fft.rfft(residual)
        powers=abs(freq)**2
        if len(powers)<3 or float(powers[1:].max())<=1e-12:return None
        idx=int(np.argmax(powers[1:])+1)
        return float(n/idx)
    if name=="Dominant Cycle Period":
        if L<n or n<6:return None
        return _autocorr_dominant(c,n)
    if name.startswith("Hilbert"):
        if L<n or n<8:return None
        window=c[-n:]
        # Full trailing-window linear detrend for stable finite-window phase.
        trend=np.linspace(window[0],window[-1],n)
        z=_analytic(window-trend)
        ph=np.angle(z[-1]);amp=float(abs(z[-1]))
        if amp<=1e-9:return None
        if name=="Hilbert Phase":return float(ph)
        if name=="Hilbert Sine":return float(math.sin(ph))
        if name=="Hilbert Phasor":return float(z[-1].imag)
        if name=="Hilbert Trend Mode":
            slope=(window[-1]-window[0])/(n-1)
            strength=abs(slope)*n/(float(np.std(window-trend))+1e-9)
            return float(min(1.,strength/10.))
        if name=="Hilbert Dominant Cycle Period":
            if n<12:return None
            phase=np.unwrap(np.angle(z[-max(3,n//4):]))
            diffs=np.diff(phase)
            advance=float(np.median(diffs))
            return float(max(2,min(n,2*math.pi/abs(advance)))) if abs(advance)>1e-8 else None
    if name in ("Ehlers Roofing Filter","Even Better Sinewave","Ehlers Sinewave"):
        filt=_roofing(c,n)
        if filt is None or not np.isfinite(filt[-1]):return None
        if name=="Ehlers Roofing Filter":return float(filt[-1])
        if name=="Even Better Sinewave":
            if L<2*n:return None
            energy=math.sqrt(float(np.mean(filt[-n:]**2)))
            return float(filt[-1]/energy) if energy>1e-9 else None
        if L<n+3:return None
        cycle=_autocorr_dominant(c,n)
        if cycle is None:return None
        analytic=_analytic(filt[-n:])
        return float(math.sin(float(np.angle(analytic[-1]))))
    if name=="Ehlers Cyber Cycle":
        if L<n+3:return None
        alpha=2/(n+1)
        smooth=sma(c,max(2,n//4))
        # Unavailable prefix is zero but no future values are ever imputed.
        cleaned=np.where(np.isfinite(smooth),smooth,0)
        z=np.zeros(L)
        for i in range(max(3,n//4),L):
            z[i]=(.25*(1-.5*alpha)**2*(cleaned[i]-2*cleaned[i-1]+cleaned[i-2])
                  +2*(1-alpha)*z[i-1]-(1-alpha)**2*z[i-2])
        return float(z[-1])
    raise ValueError("Unknown cycle/gap name")
