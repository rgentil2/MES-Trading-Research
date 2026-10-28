#!/usr/bin/env python3
"""S0.25 NQ M1 132-indicator AST -> completed-bar signal -> conservative entry PROBE.

TECHNICAL, SYNTHETIC-ONLY. This is NOT a 2020-22 backtest, historical fitness,
trade ledger, broker replay, G0/D0 approval or 132-formula certification.
It accepts caller-supplied OHLCV arrays solely for technical diagnostics.
A separate approved, data-authorized economic evaluator MUST NOT use this
probe as a surrogate for the complete, independently verified order engine.

Signal evaluation uses a prefix copy of *completed* bars. All lookbacks and
predicate branches use three-valued logic: unavailable != False. A candidate
can never enter when the opposite direction is unknown. Optional historical
context must pass the existing same-NQ-contract/session-date provenance guard.
"""
from __future__ import annotations
import hashlib
import json
from datetime import date
import numpy as np
from research.nq.nq_m1_v26_all_132_router import value as indicator
from research.nq.nq_m1_v26_structural_generator import (
    VERSION,sha,LEVEL_OPS,LAG_OPS
)
from research.nq.nq_m1_v28_funnel_ledger import inspect_structure
from research.nq.nq_m1_v2_orders import _validate_context
from research.nq.nq_m1_v29_ohlc_conservative_protocol import (
    Bar,entry as ohlc_entry,TICK,contract
)
from research.nq.nq_m1_v22_quality_gate import audit

STATUS="S0_25_SYNTHETIC_132_AST_SIGNAL_BRIDGE_NO_MARKET_NO_PNL"

def _stage_guard():
    q=audit()
    if (q["decision"]!="EXECUTION_BLOCKED" or q["passed_verified"]!=0
        or q["ready_for_economic_execution"]):
        raise PermissionError("Changed economic gate: technical bridge disabled")
    if contract()["M1_backtest_authorized"]:
        raise PermissionError("Unexpected M1 backtest release")

def _session_guard(day:str):
    if type(day) is not str or len(day)!=10 or date.fromisoformat(day).isoformat()!=day:
        raise ValueError("Require YYYY-MM-DD exact session")
    if date.fromisoformat(day).year not in (2020,2021,2022):
        raise PermissionError("Only IST 2020-2022 dates in synthetic technical bridge")

def _bars_prefix(bars:np.ndarray,i:int):
    if (not isinstance(bars,np.ndarray) or bars.ndim!=2
        or bars.shape[1]!=5 or not 1<=len(bars)<=390
        or type(i) is not int or not 0<=i<len(bars)):
        raise ValueError("Expected caller-supplied M1 OHLCV and completed index")
    x=np.array(bars[:i+1],dtype=float,copy=True)
    if (not np.isfinite(x).all() or (x[:,4]<0).any()
        or (x[:,:4]<=0).any()
        or (x[:,1]<np.maximum(x[:,0],x[:,3])).any()
        or (x[:,2]>np.minimum(x[:,0],x[:,3])).any()
        or (np.abs(x[:,:4]/TICK-np.round(x[:,:4]/TICK))>1e-7).any()):
        raise ValueError("Invalid completed NQ M1 source bar prefix")
    return x

def _context_for(day:str,session_context:dict|None,anchor_index:int|None,i:int):
    if anchor_index is not None and (type(anchor_index) is not int or
                                      not 0<=anchor_index<=i):
        raise ValueError("Anchor cannot be from future or negative")
    if session_context is None:
        return {"anchor_index":anchor_index} if anchor_index is not None else None
    # This validates contract identity, dates, ISO year and two prior RTH
    # 390-bar sessions using the established verified same-contract adapter.
    # DOES NOT independently certify identity against CME/broker.
    raw=_validate_context(day,session_context)
    ctx={"verified_same_contract":True,
         "previous_sessions":[np.array(p,copy=True)
             for p in np.split(raw,len(raw)//390)] if len(raw) else []}
    if anchor_index is not None:ctx["anchor_index"]=anchor_index
    return ctx

def _validate_candidate(strategy:dict):
    if not isinstance(strategy,dict):
        raise ValueError("Candidate must be a mapping")
    # Parent references are structural only in this stand-alone probe;
    # authenticated lineage is preserved separately in the frozen 10K ledger.
    l=strategy.get("lineage")
    if not isinstance(l,dict) or not isinstance(l.get("parents"),list):
        raise ValueError("Candidate lineage required")
    inspect_structure(strategy,set(),set(l["parents"]))

def _tri_and(a:bool|None,b:bool|None)->bool|None:
    if a is False or b is False:return False
    if a is None or b is None:return None
    return True

def _tri_or(a:bool|None,b:bool|None)->bool|None:
    if a is True or b is True:return True
    if a is None or b is None:return None
    return False

def _tree(expr:dict,prefix:np.ndarray,ctx:dict|None,
          cached:dict[tuple[int,str],float|None],
          diagnostics:dict[str,int])->bool|None:
    op=expr["op"]
    if op in ("AND","OR"):
        # Evaluate BOTH branches to account for unknowns deterministically.
        left=_tree(expr["left"],prefix,ctx,cached,diagnostics)
        right=_tree(expr["right"],prefix,ctx,cached,diagnostics)
        return _tri_and(left,right) if op=="AND" else _tri_or(left,right)
    block=expr["indicator"]
    key=json.dumps(block,sort_keys=True,separators=(",",":"))
    current=len(prefix)-1
    def read(index:int):
        if index<0:return None
        ident=(index,key)
        if ident not in cached:
            # Routers receive only a slice up to *the evaluated decision*.
            # Each historical lag gets an independently truncated slice.
            try:
                cached[ident]=indicator(prefix[:index+1],index,block,ctx)
            except (ValueError,TypeError,IndexError,KeyError):
                # Bad formula/configuration must FAIL, never be silently
                # treated as a losing or absent trading signal.
                raise
        return cached[ident]
    now=read(current)
    if op in LEVEL_OPS:
        if now is None:
            diagnostics["unavailable_leaves"]+=1;return None
        threshold=expr["threshold"]
        if op=="ABOVE_LEVEL":return bool(now>threshold)
        if op=="BELOW_LEVEL":return bool(now<threshold)
        prev=read(current-1)
        if prev is None:
            diagnostics["unavailable_leaves"]+=1;return None
        return bool(prev<=threshold and now>threshold) if op=="CROSS_ABOVE_LEVEL" else bool(prev>=threshold and now<threshold)
    lag=expr["lag_completed_bars"]
    prior=read(current-lag)
    if now is None or prior is None:
        diagnostics["unavailable_leaves"]+=1;return None
    if op in ("RISING","ABOVE_LAG"):return bool(now>prior)
    if op in ("FALLING","BELOW_LAG"):return bool(now<prior)
    if op=="CROSSES_OWN_LAG":
        prev=read(current-1)
        older=read(current-lag-1)
        if prev is None or older is None:
            diagnostics["unavailable_leaves"]+=1;return None
        return bool(prev<=older and now>prior)
    raise ValueError("Unknown AST predicate")

def signals_at(bars:np.ndarray,index:int,strategy:dict,session:str,
               session_context:dict|None=None,
               anchor_index:int|None=None)->dict:
    """Signal evaluation only; does not look at the bar after index."""
    _stage_guard();_session_guard(session);_validate_candidate(strategy)
    completed=_bars_prefix(bars,index)
    context=_context_for(session,session_context,anchor_index,index)
    cache={}
    diagnostics={"unavailable_leaves":0}
    long=_tree(strategy["long"],completed,context,cache,diagnostics)
    short=_tree(strategy["short"],completed,context,cache,diagnostics)
    if long is True and short is False:
        action="LONG"
    elif short is True and long is False:
        action="SHORT"
    elif long is True and short is True:
        action="BOTH_SIDES_CONFLICT"
    elif long is False and short is False:
        action="NO_SIGNAL"
    else:
        action="UNAVAILABLE_SOME_SIGNAL_DATA"
    return {"status":STATUS,"candidate_id":strategy["id"],
            "ast_sha256":sha(strategy),"decision_bar_index":index,
            "session":session,"long":long,"short":short,"action":action,
            "unavailable_indicator_leaf_evaluations":diagnostics["unavailable_leaves"],
            "indicator_index_cache_hits_unique":len(cache),
            "market_data_loaded_by_module":False,
            "fitness_evaluated":False,"trades_executed":0,
            "model_exit_simulated":False,"holdouts_opened":False}

def entry_probe(bars:np.ndarray,index:int,strategy:dict,session:str,
                session_context:dict|None=None,
                anchor_index:int|None=None)->dict:
    """Synthetic one-bar conservative entry scenario; no SL/TP/trade/PnL.

    STRICT: Cannot peek at next bar for a decision, cannot use minute 11:29
    or later as a fresh entry as forced close 11:29 would conflict.
    M1 end-labeled 09:31->0: 09:35->4, 11:28->117, 11:29->118.
    """
    s=signals_at(bars,index,strategy,session,session_context,anchor_index)
    out=dict(s)
    out.update({"entry_proxy":False,"entry_proxy_price":None,
                "entry_proxy_reason":"NO_ELIGIBLE_DIRECTION",
                "entry_proxy_bar_index":None,
                "economic_backtest_executed":False})
    if s["action"] not in ("LONG","SHORT"):return out
    if not 4<=index<=116:
        out["entry_proxy_reason"]="SIGNAL_OUTSIDE_ALLOWED_ENTRY_WINDOW"
        return out
    if index+1>=len(bars):
        out["entry_proxy_reason"]="NEXT_BAR_NOT_AVAILABLE"
        return out
    # A NEXT bar is visible solely to the technical fill probe. Never passed
    # into signals_at() or the calculator as a signal-time completed bar.
    _bars_prefix(bars,index+1)
    kind=strategy["entry_order"]["kind"]
    side=1 if s["action"]=="LONG" else -1
    close=float(bars[index,3]);offset=strategy["entry_order"]["offset_ticks"]
    requested=None
    if kind=="STOP":requested=close+side*TICK*offset
    elif kind=="LIMIT":requested=close-side*TICK*offset
    bar=Bar(*map(float,bars[index+1,:4]))
    result=ohlc_entry(bar,side,kind,requested)
    out["entry_proxy_bar_index"]=index+1
    out["entry_proxy"]=result["filled_proxy"]
    out["entry_proxy_price"]=result["fill_price"]
    out["entry_proxy_reason"]=result["reason"]
    return out
