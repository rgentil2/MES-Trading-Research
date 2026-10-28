#!/usr/bin/env python3
"""S0.26: complete single-NQ intraday M1 synthetic model lifecycle (NOT economic IST).

Generation of all inputs occurs INSIDE this module using deterministic artificial
prices. Caller cannot provide a historical OHLCV matrix. The sole purpose is
technical QA of signal->pending order->fill->risk->exit->next signal transitions.

This cannot replace an IST backtest, certify any of 132 formulas, or authorize
the 13-gate economic release. Future historical runners must be separately
versioned and approved; do not change this fixture-only boundary.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
import math
import numpy as np
from research.nq.nq_m1_v26_math import series_atr
from research.nq.nq_m1_v29_ohlc_conservative_protocol import (
    Bar,entry as m1_entry,exit_bar,TICK,POINT_USD,COMMISSION_RT_USD,
    DEFAULT_SLIP_TICKS_SIDE,contract
)
from research.nq.nq_m1_v30_132_signal_m1_bridge import (
    signals_at,_bars_prefix,_context_for,_session_guard,_validate_candidate,
    _stage_guard,STATUS as BRIDGE_STATUS
)

STATUS="S0_26_ARTIFICIAL_ONLY_NQ_M1_FULL_LIFECYCLE_NO_IST_BACKTEST_NO_FITNESS"
CLOSE_IDX=118  # 11:29 New York; 09:31 index0, 11:28 index117
LAST_ENTRY_SIGNAL=116
FIRST_SIGNAL=4
ACCOUNT_INTERNAL={"max_entries_per_day":2,"max_initial_risk_usd":300.0,
                  "closed_daily_pause_usd":-600.0}

@dataclass(frozen=True)
class Fixture:
    seed:int
    kind:str
    patch_sha256:str
    label:str="GENERATED_ARTIFICIAL_OHLC_NOT_MARKET"

def _patch_digest(patches):
    return sha256(json.dumps(patches,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def artificial_m1(seed:int=20261028,kind:str="UP",patches:dict|None=None):
    """Create deterministic synthetic 390x5 fixture from seed and scenario.

    Patches are ONLY for explicit synthetic test scenarios, never market input.
    Data are internally constructed then validation covers all 390 bars.
    """
    if type(seed) is not int or not 0<=seed<2**32 or kind not in ("UP","DOWN","FLAT"):
        raise ValueError("Unrecognized artificial fixture parameters")
    p={} if patches is None else patches
    if not isinstance(p,dict) or any(type(k) is not int or not 0<=k<390
                                      or not isinstance(v,(list,tuple))
                                      or len(v)!=5 for k,v in p.items()):
        raise ValueError("Only indexed 5-field artificial OHLCV changes")
    rng=np.random.default_rng(seed)
    trend={"UP":.25,"DOWN":-.25,"FLAT":0.}[kind]
    close=20000.
    arr=np.empty((390,5),float)
    for i in range(390):
        op=close
        movement=trend+float(rng.choice((-.25,0.,.25))) if kind=="FLAT" else trend
        close=op+movement
        arr[i]=(op,max(op,close)+1.,min(op,close)-1.,close,1000.+i)
    for idx,values in p.items():
        arr[idx]=values
    _bars_prefix(arr,389)
    fixture=Fixture(seed,kind,_patch_digest({str(k):list(v) for k,v in p.items()}))
    return arr,fixture

def _verify_fixture(fixture:Fixture,patches:dict|None)->np.ndarray:
    if not isinstance(fixture,Fixture) or fixture.label!="GENERATED_ARTIFICIAL_OHLC_NOT_MARKET":
        raise PermissionError("NQ S0.26 accepts only generated artificial fixtures")
    b,proof=artificial_m1(fixture.seed,fixture.kind,patches)
    if fixture!=proof:raise PermissionError("Fixture parameter digest mismatch")
    return b

def _ceil(x:float)->float:
    if not np.isfinite(x) or x<=0:raise ValueError("Invalid protective distance")
    return max(TICK,math.ceil(x/TICK-1e-12)*TICK)

def _floor(x:float)->float:
    if not np.isfinite(x) or x<=0:raise ValueError("Invalid target distance")
    return max(TICK,math.floor(x/TICK+1e-12)*TICK)

def _price_grid(x:float,way:str)->float:
    if not np.isfinite(x) or x<=0:raise ValueError("Invalid protective price")
    return (math.floor(x/TICK+1e-10) if way=="DOWN"
            else math.ceil(x/TICK-1e-10))*TICK

def _history(day:str,context):
    # Existing same-contract provenance checks. No raw external IST reader.
    checked=_context_for(day,context,None,0)
    if checked is None:return np.empty((0,5),float)
    items=checked.get("previous_sessions",[])
    return np.concatenate(items,axis=0) if items else np.empty((0,5),float)

def _completed(bars:np.ndarray,i:int,prior:np.ndarray)->np.ndarray:
    return np.concatenate((prior,bars[:i+1]),axis=0) if len(prior) else bars[:i+1]

def _atr(bars:np.ndarray,decision:int,period:int,prior:np.ndarray)->float|None:
    z=_completed(bars,decision,prior)
    if type(period) is not int or period<2 or len(z)<=period:return None
    a=series_atr(z,period)[-1]
    return float(a) if np.isfinite(a) and a>0 else None

def _stop_distance(bars:np.ndarray,decision:int,side:int,entry:float,
                   exit_spec:dict,prior:np.ndarray)->float|None:
    stop=exit_spec["stop_loss_required"];kind=stop["kind"]
    if kind=="FIXED_POINTS":return _ceil(float(stop["points"]))
    if kind=="ATR":
        atr=_atr(bars,decision,stop["period"],prior)
        return _ceil(atr*float(stop["multiple"])) if atr is not None else None
    if kind=="STRUCTURE":
        n=stop["lookback"];c=_completed(bars,decision,prior)
        if len(c)<n:return None
        level=(float(c[-n:,2].min()) if side==1 else float(c[-n:,1].max()))
        distance=side*(entry-level)+float(stop["buffer_ticks"])*TICK
        return _ceil(distance) if distance>0 else None
    if kind=="CHANDELIER":
        n=stop["period"];c=_completed(bars,decision,prior)
        atr=_atr(bars,decision,n,prior)
        if len(c)<n or atr is None:return None
        extreme=float(c[-n:,1].max()) if side==1 else float(c[-n:,2].min())
        level=extreme-side*float(stop["atr_multiple"])*atr
        dist=side*(entry-level)
        return _ceil(dist) if dist>0 else None
    raise ValueError("Unknown stop kind")

def _target_distance(bars:np.ndarray,decision:int,side:int,entry:float,
                     risk:float,exit_spec:dict,prior:np.ndarray)->tuple[float|None,str]:
    spec=exit_spec["profit_target"];kind=spec["kind"]
    if kind=="NONE":return None,"NO_TARGET"
    if kind=="R_MULTIPLE":return _floor(risk*float(spec["risk_multiple"])),"VALID"
    if kind=="FIXED_POINTS":return _floor(float(spec["points"])),"VALID"
    if kind=="ATR":
        atr=_atr(bars,decision,spec["period"],prior)
        return ((_floor(atr*float(spec["multiple"])),"VALID") if atr is not None
                else (None,"NO_ATR_WARMUP"))
    if kind=="CAUSAL_LEVEL":
        ref=spec["reference"]
        if ref!="VWAP":
            # Registry specified a generic level but NO upper/lower or direction
            # selector. Never silently invent a favorable pivot reference.
            return None,"LEVEL_REFERENCE_NEEDS_FORMAL_DEFINITION"
        x=bars[:decision+1]
        vol=float(x[:,4].sum())
        if vol<=0:return None,"VWAP_VOLUME_UNAVAILABLE"
        target=float(np.dot((x[:,1]+x[:,2]+x[:,3])/3,x[:,4])/vol)
        diff=side*(target-entry)
        return ((_floor(diff),"VALID") if diff>=TICK
                else (None,"VWAP_NOT_FAVORABLE"))
    raise ValueError("Unknown target kind")

def _improve_stop(bars:np.ndarray,completed_idx:int,side:int,entry_price:float,
                  risk:float,old_stop:float,policy:dict,prior:np.ndarray):
    prev=bars[completed_idx]
    favorable=float(prev[1] if side==1 else prev[2])
    gain=side*(favorable-entry_price)
    improved=old_stop
    be=policy["break_even"]
    if be is not None and gain>=float(be["start_r"])*risk:
        proposed=entry_price+side*float(be["plus_ticks"])*TICK
        improved=max(improved,proposed) if side==1 else min(improved,proposed)
    trail=policy["trailing"]
    if trail is not None and gain>=float(trail["start_r"])*risk:
        atr=_atr(bars,completed_idx,trail["atr_period"],prior)
        if atr is not None:
            proposed=favorable-side*float(trail["distance_atr"])*atr
            improved=max(improved,proposed) if side==1 else min(improved,proposed)
    # Nearest adverse tick; in case of rounding, never loosen old stop.
    tentative=_price_grid(improved,"DOWN" if side==1 else "UP")
    return max(old_stop,tentative) if side==1 else min(old_stop,tentative)

def _protective_replay(bars:np.ndarray,decision:int,fill_idx:int,kind:str,
                       side:int,entry_price:float,risk:float,target_distance:float|None,
                       exit_spec:dict,prior:np.ndarray):
    stop=_price_grid(entry_price-side*risk,"DOWN" if side==1 else "UP")
    target=(None if target_distance is None else
            _price_grid(entry_price+side*target_distance,
                        "UP" if side==1 else "DOWN"))
    last=min(CLOSE_IDX,fill_idx+exit_spec["exit_after_bars"]-1) if (
        exit_spec["exit_after_bars"] is not None) else CLOSE_IDX
    last=min(last,len(bars)-1)
    updates=0;ambiguous=0;suppressed=0
    for j in range(fill_idx,last+1):
        # Never tighten using entry-bar OHLC before a pending-order fill.
        if j>fill_idx and (kind=="MARKET" or j-1>fill_idx):
            changed=_improve_stop(bars,j-1,side,entry_price,risk,stop,exit_spec,prior)
            if changed!=stop:updates+=1;stop=changed
        row=bars[j]
        bar=Bar(*map(float,row[:4]))
        # A take-profit is a LIMIT order, not a guaranteed fill when M1 only
        # TOUCHES the requested price. Require one-tick trade-through, or a
        # marketable target at the bar open. A protective stop still wins
        # on a bar touching BOTH barriers, including an exact TP touch.
        limit_target_unconfirmed=False
        target_to_check=target
        if target is not None:
            tp_touched=(bar.high>=target if side==1 else bar.low<=target)
            tp_at_open=(bar.open>=target if side==1 else bar.open<=target)
            tp_through=(bar.high>=target+TICK if side==1
                        else bar.low<=target-TICK)
            stop_touched=(bar.low<=stop if side==1 else bar.high>=stop)
            if tp_touched and not tp_at_open and not tp_through and not stop_touched:
                limit_target_unconfirmed=True
                target_to_check=None
        ev=exit_bar(bar,side,stop,target_to_check,
                    pending_entry_same_bar=(j==fill_idx and kind!="MARKET"),
                    forced_time_exit=(j==last))
        if ev["ambiguous_bar"]:ambiguous+=1
        if ev["target_suppressed"] or limit_target_unconfirmed:suppressed+=1
        if ev["exited_proxy"]:
            exit_px=ev["exit_price"]
            return {"exit_idx":j,"exit_price":round(exit_px,5),
                    "exit_reason":ev["reason"],
                    "stop_updates":updates,
                    "last_stop_price":stop,"target_price":target,
                    "ambiguous_bars":ambiguous,"targets_suppressed":suppressed,
                    "synthetic_net_usd":round(
                        side*(exit_px-entry_price)*POINT_USD-COMMISSION_RT_USD,2)}
    # ALL artificial day inputs include the mandatory flat bar index 118.
    raise RuntimeError("No protective or forced-flat exit")

def simulate_synthetic_day(strategy:dict,fixture:Fixture,day:str="2021-05-04",
                           patches:dict|None=None,session_context:dict|None=None,
                           max_entries:int=2)->dict:
    """SYNTHETIC full-session order lifecycle for pre-approval engineering only.

    Strictly constructs its own 390 M1 synthetic prices, never accepts actual
    OHLC data, and never returns a real-strategy backtest. Limit/stop pending
    expire after 1..30 bars; no entries at 11:29 ET, flat at bar 118.
    """
    _stage_guard();_session_guard(day);_validate_candidate(strategy)
    if type(max_entries) is not int or not 1<=max_entries<=2:
        raise ValueError("Reference study permits at most two NQ entries/day")
    bars=_verify_fixture(fixture,patches)
    prior=_history(day,session_context)
    entry_spec=strategy["entry_order"]
    exit_spec=strategy["exit"]
    accepted=[];rejected=Counter()
    sigs=Counter()
    closed=0.;i=FIRST_SIGNAL
    while i<=LAST_ENTRY_SIGNAL and len(accepted)<max_entries:
        if closed<=ACCOUNT_INTERNAL["closed_daily_pause_usd"]:
            rejected["DAILY_CLOSED_PNL_PAUSE"]+=1;break
        # Only this decision bar is exposed to the indicator module.
        decision=signals_at(bars,i,strategy,day,session_context)
        sigs[decision["action"]]+=1
        action=decision["action"]
        if action not in ("LONG","SHORT"):
            i+=1;continue
        side=1 if action=="LONG" else -1
        kind=entry_spec["kind"]
        offset=int(entry_spec["offset_ticks"])
        trigger=(None if kind=="MARKET" else
                 float(bars[i,3])+side*TICK*offset if kind=="STOP" else
                 float(bars[i,3])-side*TICK*offset)
        expiration=min(CLOSE_IDX-1,i+(1 if kind=="MARKET" else entry_spec["expiry_bars"]))
        found_idx=None;entry_px=None;why=None
        for j in range(i+1,expiration+1):
            row=bars[j]
            p=m1_entry(Bar(*map(float,row[:4])),side,kind,trigger)
            if p["filled_proxy"]:
                found_idx=j;entry_px=p["fill_price"];why=p["reason"]
                break
        if found_idx is None:
            rejected["PENDING_ORDER_EXPIRED"]+=1
            i=expiration+1
            continue
        risk=_stop_distance(bars,i,side,entry_px,exit_spec,prior)
        if risk is None:
            rejected["NO_VALID_PROTECTIVE_STOP_CONTEXT"]+=1
            i=found_idx+1;continue
        # A modelled fill rejected by risk *after observing the next open*
        # cannot be counted as a real pre-trade order cancellation.
        # Record such cases as model-only non-executability.
        cap=risk*POINT_USD+DEFAULT_SLIP_TICKS_SIDE*TICK*POINT_USD+COMMISSION_RT_USD
        if cap>ACCOUNT_INTERNAL["max_initial_risk_usd"]:
            rejected["MODEL_ENTRY_RISK_NON_EXECUTABLE"]+=1
            i=found_idx+1;continue
        target,reason=_target_distance(bars,i,side,entry_px,risk,exit_spec,prior)
        if reason not in ("VALID","NO_TARGET"):
            rejected[reason]+=1
            i=found_idx+1;continue
        execution=_protective_replay(
            bars,i,found_idx,kind,side,entry_px,risk,target,exit_spec,prior)
        closed+=execution["synthetic_net_usd"]
        accepted.append({"candidate_id":strategy["id"],
                         "session":day,"signal_idx":i,"entry_idx":found_idx,
                         "entry_kind":kind,"entry_reason":why,
                         "entry_price":round(entry_px,5),"side":side,
                         "requested_price":trigger,
                         "initial_model_risk_usd":round(cap,2),**execution})
        # Exit bar is finished before another signal can be evaluated.
        i=execution["exit_idx"]+1
    return {"status":STATUS,"candidate_id":strategy["id"],"date":day,
            "fixture_seed":fixture.seed,"fixture_kind":fixture.kind,
            "fixture_patch_sha256":fixture.patch_sha256,
            "synthetic_trades":accepted,"synthetic_entries":len(accepted),
            "synthetic_closed_net_usd":round(closed,2),
            "rejections":dict(rejected),"signal_actions":dict(sigs),
            "complete_forced_flat":all(t["exit_idx"]<=CLOSE_IDX for t in accepted),
            "account_reference_plan_confirmed":False,
            "historical_data_used":False,"economic_fitness_computed":False,
            "G0_D0_D1_D2_verified":False,"M1_backtest_authorized":False,
            "holdouts_opened":False,"broker_fills_claimed":False}
