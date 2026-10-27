#!/usr/bin/env python3
"""20 extra causal scalar M1 indicators for V2 (S0.3 synthetic tests only).
Conventions: population moments (ddof=0), SMA seeded Wilder/EMA,
finite OHLCV nonnegative volumes, RTH-only rolling windows; see module tests.
Not an independent TA-Lib or StrategyQuant parity certification.
"""
from __future__ import annotations
import math
import numpy as np

EXTENDED = frozenset({
    "RSI", "CMO", "CCI", "Williams %R", "Aroon", "VHF",
    "Efficiency Ratio", "Historical Volatility", "MFI", "CMF",
    "Elder Force Index", "Ulcer Index", "Price/Volume Correlation",
    "Skewness", "Kurtosis", "Median Absolute Deviation",
    "Realized Volatility", "Autocorrelation", "Range Percentile",
    "True Range Percentile",
})


def _ema(a: np.ndarray, n: int) -> float | None:
    if len(a) < n:
        return None
    z = float(np.mean(a[:n]))
    for x in a[n:]:
        z += 2. / (n + 1) * (float(x) - z)
    return z


def _wilder(a: np.ndarray, n: int) -> float | None:
    if len(a) < n:
        return None
    z = float(np.mean(a[:n]))
    for x in a[n:]:
        z += (float(x)-z) / n
    return z


def calc(bars: np.ndarray, idx: int, block: dict) -> float | None:
    """Every result depends only on bars with index <= idx."""
    name = block["name"]
    if name not in EXTENDED:
        raise ValueError("Unknown extended indicator")
    if bars.ndim != 2 or bars.shape[1] != 5 or idx >= len(bars):
        raise ValueError("Expected 5-column OHLCV and an existing index")
    if idx < 0:
        return None
    d = bars[:idx+1]
    if not np.isfinite(d).all() or (d[:, 4] < 0).any():
        raise ValueError("Invalid OHLCV")
    n = int(block["parameters"].get("period", 0))
    if n < 2 or n > 390:
        raise ValueError("Indicator period outside 2..390")
    op, h, l, c, v = (d[:,j] for j in range(5))
    if name in {"RSI", "CMO", "VHF", "Efficiency Ratio",
                "Historical Volatility", "MFI", "Realized Volatility"}:
        if len(c) < n+1:
            return None
    elif name == "Autocorrelation":
        if len(c) < n+2:
            return None
    elif name in {"Range Percentile", "True Range Percentile"}:
        if len(c) < n+1:
            return None
    elif name == "Elder Force Index":
        if len(c) < n+1:
            return None
    elif len(c) < n:
        return None

    if name in ("RSI", "CMO"):
        dif = np.diff(c)
        gains = np.maximum(dif, 0.)
        losses = np.maximum(-dif, 0.)
        if name == "RSI":
            g = _wilder(gains, n)
            loss = _wilder(losses, n)
        else:
            g = float(np.sum(gains[-n:]))
            loss = float(np.sum(losses[-n:]))
        if g + loss == 0:
            return 50. if name == "RSI" else 0.
        return float((100.*g/(g+loss)) if name == "RSI"
                     else 100.*(g-loss)/(g+loss))
    if name == "CCI":
        typical = (h[-n:]+l[-n:]+c[-n:])/3.
        mean = float(np.mean(typical))
        mad = float(np.mean(abs(typical-mean)))
        return float((typical[-1]-mean)/(.015*mad)) if mad > 0 else 0.
    if name == "Williams %R":
        hi, lo = float(np.max(h[-n:])), float(np.min(l[-n:]))
        return float(-100.*(hi-c[-1])/(hi-lo)) if hi > lo else 0.
    if name == "Aroon":
        if len(c) < n+1:
            return None
        # Oscillator: Aroon Up minus Aroon Down, latest equal extreme wins.
        hi_since = int(np.argmax(h[-n-1:][::-1]))
        lo_since = int(np.argmin(l[-n-1:][::-1]))
        return float(100.*(lo_since-hi_since)/n)
    if name in ("VHF", "Efficiency Ratio"):
        window = c[-n-1:]
        denom = float(np.sum(abs(np.diff(window))))
        if denom == 0:
            return 0.
        numerator = ((np.max(window)-np.min(window)) if name == "VHF"
                     else abs(window[-1]-window[0]))
        return float(numerator/denom)
    if name in ("Historical Volatility", "Realized Volatility"):
        window = c[-n-1:]
        if (window <= 0).any():
            return None
        logret = np.diff(np.log(window))
        if name == "Historical Volatility":
            return float(np.std(logret)*math.sqrt(252*390)*100)
        return float(math.sqrt(float(np.dot(logret, logret)))*100)
    if name == "MFI":
        tp = (h+l+c)/3.
        money = tp*v
        diff = np.diff(tp[-n-1:])
        flows = money[-n:]
        positive = float(np.sum(flows[diff > 0]))
        negative = float(np.sum(flows[diff < 0]))
        if positive+negative == 0:
            return 50.
        return float(100.*positive/(positive+negative))
    if name == "CMF":
        den = h[-n:]-l[-n:]
        mult = np.divide(2*c[-n:]-h[-n:]-l[-n:], den,
                         out=np.zeros(n), where=den>0)
        vol = float(np.sum(v[-n:]))
        return float(np.dot(mult, v[-n:])/vol) if vol > 0 else None
    if name == "Elder Force Index":
        return _ema(np.diff(c)*v[1:], n)
    if name == "Ulcer Index":
        values = c[-n:]
        running = np.maximum.accumulate(values)
        dd = 100.*(values-running)/np.where(running != 0, running, 1.)
        return float(math.sqrt(np.mean(dd**2)))
    if name == "Price/Volume Correlation":
        values, volumes = c[-n:], v[-n:]
        if float(np.std(values))*float(np.std(volumes)) == 0:
            return 0.
        return float(np.corrcoef(values, volumes)[0,1])
    if name in ("Skewness", "Kurtosis"):
        values = c[-n:]
        centered = values-np.mean(values)
        mu2 = float(np.mean(centered**2))
        if mu2 == 0:
            return 0.
        if name == "Skewness":
            return float(np.mean(centered**3)/mu2**1.5)
        return float(np.mean(centered**4)/mu2**2-3.)
    if name == "Median Absolute Deviation":
        values = c[-n:]
        return float(np.median(abs(values-np.median(values))))
    if name == "Autocorrelation":
        diffs = np.diff(c[-n-2:])
        left, right = diffs[:-1], diffs[1:]
        if float(np.std(left))*float(np.std(right)) == 0:
            return 0.
        return float(np.corrcoef(left, right)[0,1])
    if name == "Range Percentile":
        widths = h-l
        previous = widths[-n-1:-1]
        return float(np.mean(previous <= widths[-1])*100.)
    if name == "True Range Percentile":
        prev = np.concatenate(([c[0]], c[:-1]))
        tr = np.maximum.reduce((h-l, abs(h-prev), abs(l-prev)))
        return float(np.mean(tr[-n-1:-1] <= tr[-1])*100.)
    raise AssertionError("Unreachable extended indicator")
