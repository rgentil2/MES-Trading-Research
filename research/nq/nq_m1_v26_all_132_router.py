#!/usr/bin/env python3
"""S0.21 isolated 132/132 NQ M1 research calculator router.

This is a NEW EXPERIMENTAL implementation track, not a modification of the
frozen 38 V2.1 engine or a broker/backtester release. Every registry name has
a deterministic code route, with typed parameter checks, causal bar slicing,
and explicit unavailable context -> None. A returned number is NOT financial
parity/certification. V2.1 generated candidates remain unchanged.

Catalogue has historical mixed formula + predicate fields. In this new track,
'threshold' and '*_level' are normalized as explicit offsets, 'multiplier'
scales the output for the four pre-existing scalar calculators, and multiline
outputs require an explicit optional 'output' selector (default documented).
"""
from __future__ import annotations
from functools import lru_cache
import math
import numpy as np
from research.nq.nq_m1_v2_generator import read_registry
from research.nq.nq_m1_v2_m1_engine import (
 SUPPORTED_INDICATORS as FROZEN,indicator_value as frozen_calc
)
from research.nq.nq_m1_v2_semantic_lint import USED
from research.nq.nq_m1_v22_incubator_ma import PROTOTYPES as OLD_MA,calc as ma_calc
from research.nq.nq_m1_v22_incubator_oscillators import PROTOTYPES as OLD_OSC,indicator_value as osc_calc
from research.nq.nq_m1_v25_extra_scalars import PROTOTYPES as EXTRA,value as extra_value
from research.nq.nq_m1_v25_candle_patterns import PATTERNS,classify as candle_value
from research.nq.nq_m1_v26_trend_momentum import NAMES as TREND,value as trend_value
from research.nq.nq_m1_v26_volume_levels import NAMES as VOL,value as vol_value
from research.nq.nq_m1_v26_cycles_gaps import NAMES as CYCLES,value as cycle_value
from research.nq.nq_m1_v26_math import input_frame,series_tr

STATUS="S0_21_132_MATHEMATICAL_IMPLEMENTATIONS_UNCERTIFIED_ECONOMIC_GATE_CLOSED"
SOURCE_PARAMS=frozenset(("open","high","low","close","hl2","hlc3","ohlc4"))
PREDICATE_FIELDS=frozenset(("threshold","lower_level","upper_level",
                             "z_threshold","ratio_threshold"))
OUTPUT_LINES=frozenset(("upper","lower","middle","width"))
CATEGORIES=(FROZEN,OLD_MA,OLD_OSC,EXTRA,PATTERNS,TREND,VOL,CYCLES)

@lru_cache(maxsize=1)
def catalogue():
    entries=read_registry()["entries"]
    return {e["name"]:e for e in entries}

def inventory():
    names=set(catalogue())
    routed=set()
    for group in CATEGORIES:
        if routed&group:raise RuntimeError("Duplicate formula route")
        routed.update(group)
    if len(names)!=132 or names!=routed:
        raise RuntimeError("132 names not all routed; refusing certification")
    return {
      "registered":132,"coded":132,"frozen_original":len(FROZEN),
      "previous_isolated":len(OLD_MA)+len(OLD_OSC)+len(EXTRA)+len(PATTERNS),
      "new_isolated":len(TREND)+len(VOL)+len(CYCLES),
      "independent_certified_132":False,"economic_execution_authorized":False,
      "roll_contract_changed":False,"holdouts_opened":False
    }

def _parameters(entry,params):
    fields=entry["parameters"]
    needed=set(fields)-{"constraint"}
    if set(params)!=needed:raise ValueError("Missing/extra registered fields")
    for key,domain in fields.items():
        if key=="constraint":continue
        value=params[key]
        if (isinstance(domain,list) and len(domain)==2 and
           all(type(z) in (int,float) for z in domain)):
            integer=all(type(z) is int for z in domain)
            if (integer and type(value) is not int) or (
                 not integer and type(value) not in (int,float)):
                raise ValueError(f"Invalid parameter type: {key}")
            if not domain[0]<=value<=domain[1] or not math.isfinite(value):
                raise ValueError(f"Parameter {key} outside catalogue")
        elif isinstance(domain,list) and all(type(z) is str for z in domain):
            if value not in domain:raise ValueError(f"Invalid enum {key}")
        else:raise ValueError(f"Unrecognized domain: {key}")
    if fields.get("constraint")=="fast_period < slow_period":
        if params["fast_period"]>=params["slow_period"]:
            raise ValueError("fast period must be smaller than slow period")

def _metadata(result,p,block):
    if result is None:return None
    if type(result) not in (int,float,np.float64,np.float32) or not np.isfinite(result):
        raise ValueError("Nonfinite mathematical output")
    raw=float(result)
    thresholds=PREDICATE_FIELDS.intersection(p)
    if thresholds:
        if {"lower_level","upper_level"}<=thresholds:
            choice=block.get("output","lower_level")
            if choice not in ("lower_level","upper_level"):
                raise ValueError("Two-level indicator needs recognized threshold output")
            return raw-float(p[choice])
        if len(thresholds)!=1:raise ValueError("Ambiguous indicator thresholds")
        return raw-float(p[next(iter(thresholds))])
    return raw

def _original(bars,idx,name,p,context):
    used=set(USED[name])
    actual={k:p[k] for k in used if k in p}
    if name=="VWAP" and p["anchor"]=="previous_completed_session":
        if (not isinstance(context,dict) or
             context.get("verified_same_contract") is not True or
             not context.get("previous_sessions")):return None
        z=context["previous_sessions"][-1]
        if not isinstance(z,np.ndarray) or z.shape!=(390,5) or not np.isfinite(z).all():
            return None
        vol=float(z[:,4].sum())
        return float(np.dot((z[:,1]+z[:,2]+z[:,3])/3,z[:,4])/vol) if vol>0 else None
    if name=="OBV":
        n=p["period"]
        if idx<n:return None
        x=bars[:idx+1]
        # New windowed signed volume index; frozen engine's global OBV unchanged.
        return float(x[-n,4]+np.dot(np.sign(np.diff(x[-n:,3])),x[-n+1:,4]))
    if name=="True Range":
        n=p["period"]
        if idx<n-1:return None
        ranges=series_tr(bars[:idx+1])[-n:]
        # Relative TR (last / rolling mean), otherwise 'period' would be inert.
        baseline=float(np.mean(ranges))
        return float(ranges[-1]/baseline)*float(p["multiplier"]) if baseline>0 else None
    value=frozen_calc(bars,idx,{"name":name,"parameters":actual})
    if value is None:return None
    if "multiplier" in p:
        value=float(value)*float(p["multiplier"])
    return value

def value(bars:np.ndarray,idx:int,block:dict,context:dict|None=None):
    inv=inventory()
    if inv["coded"]!=132:raise RuntimeError("Uncovered registry")
    if not isinstance(block,dict) or set(block)-{"name","parameters","output","registry_id"}:
        raise ValueError("Unknown indicator fields")
    name=block.get("name")
    if name not in catalogue():raise ValueError("Unknown registered indicator")
    p=block.get("parameters")
    if not isinstance(p,dict):raise ValueError("Indicator parameters required")
    entry=catalogue()[name]
    if "registry_id" in block and block["registry_id"]!=entry["id"]:
        raise ValueError("Registry ID does not match formula name")
    _parameters(entry,p)
    if "output" in block and name not in (
       "Bollinger Bands","Keltner","Acceleration Bands",
       "Central Pivot Range","Classic Pivots","Fibonacci Pivots",
       "Camarilla Pivots","Woodie Pivots","DeMark Pivots",
       "Previous Day High/Low","RSI"):
        raise ValueError("Output selector not registered for this name")
    x=input_frame(bars,idx)
    if x is None:return None
    if name in FROZEN:
        val=_original(bars,idx,name,p,context)
    elif name in OLD_MA:
        val=ma_calc(bars,idx,{"name":name,"parameters":p})
    elif name in OLD_OSC:
        val=osc_calc(bars,idx,{"name":name,"parameters":p})
    elif name in EXTRA:
        # All names in this prior incubator have no predicate fields except none.
        val=extra_value(bars,idx,{"name":name,"parameters":{k:v for k,v in p.items() if k not in PREDICATE_FIELDS}})
    elif name in PATTERNS:
        val=candle_value(bars,idx,{"name":name,"parameters":p})
    elif name in TREND:
        val=trend_value(x,name,p)
    elif name in VOL:
        val=vol_value(x,name,p,context,block)
    elif name in CYCLES:
        val=cycle_value(x,name,p,context)
    else:raise RuntimeError("Unreachable uncovered name")
    # New trend formulas already apply 'threshold' internally, avoiding double subtraction.
    if name in TREND:return _metadata(val,{},block)
    # Registered 'threshold' and other level fields on original scalar/prototypes
    # are never ignored; a positive signed output is the above-level predicate.
    return _metadata(val,p,block)
