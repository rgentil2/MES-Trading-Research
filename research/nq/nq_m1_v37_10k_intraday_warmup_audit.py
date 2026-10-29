#!/usr/bin/env python3
"""S0.32 — Audit frozen 10K AST intraday signal warmup without market prices.

This is a STATIC, LOWER-BOUND feasibility diagnostic; it is neither a certified
formula screen nor a formal G0 admission, economic search, elimination, or
performance ranking. It flags only cases where a supported indicator's
minimum intraday history plus predicate lookback is too long for the 09:35–
11:27 completed-bar decision window, ASSUMING no cross-session warmup
for that named scalar. Other indicators remain UNKNOWN/POSSIBLE and are NOT
discarded. All 10,000 candidates and lineage SHA remain untouched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from collections import Counter
from research.nq.nq_m1_v26_structural_generator import (
    structural_batch,SEED,LEVEL_OPS,LAG_OPS
)
from research.nq.nq_m1_v28_funnel_ledger import FROZEN
from research.nq.nq_m1_v22_quality_gate import audit

STATUS="S0_32_FROZEN_10K_NO_PRICE_STATIC_INTRADAY_WARMUP_BOUND_ONLY"
MAX_BARS=117 # 09:31 index 0 through last eligible signal 11:27 index 116
CHECKABLE=frozenset((
    "SMA","EMA","WMA","RMA","DEMA","TEMA","TRIMA","T3",
    "APO","TRIX","KAMA","ATR","NATR","True Range","Donchian",
    "MACD","HMA","ALMA","ZLEMA","Standard Deviation","Variance"
))

def _needed(block):
    n=block["name"]
    p=block["parameters"]
    if n not in CHECKABLE:return None
    k=p.get("period")
    if n=="T3":return 6*(k-1)+1
    if n=="KAMA":return k+1
    if n=="DEMA":return 2*k-1
    if n=="TEMA":return 3*k-2
    if n=="TRIX":return 3*k-1
    if n=="MACD":return p["slow_period"]+p["signal_period"]-1
    if n=="APO":return p["slow_period"]
    if n in ("ATR","NATR","Donchian"):return k+1
    if n=="HMA":return k+max(1,int(math.sqrt(k)))-1
    if n=="ZLEMA":return k+(k-1)//2
    return k

def _leaves(tree):
    if tree["op"] in ("AND","OR"):
        yield from _leaves(tree["left"])
        yield from _leaves(tree["right"])
    else:
        yield tree

def _could_be_true(tree):
    if tree["op"] in ("AND","OR"):
        a=_could_be_true(tree["left"])
        b=_could_be_true(tree["right"])
        return (a and b) if tree["op"]=="AND" else (a or b)
    basic=_needed(tree["indicator"])
    if basic is None:
        return True # Unknown formulas MUST NOT be declared impossible.
    extra=(tree["lag_completed_bars"] if tree["op"] in LAG_OPS else
           1 if tree["op"] in ("CROSS_ABOVE_LEVEL","CROSS_BELOW_LEVEL") else 0)
    if tree["op"]=="CROSSES_OWN_LAG":
        extra+=1
    return basic+extra<=MAX_BARS

def _audit_gate():
    q=audit()
    if (q["checks_total"]!=13 or q["passed_verified"]!=0 or
        q["decision"]!="EXECUTION_BLOCKED" or
        q["ready_for_economic_execution"]):
        raise PermissionError("Frozen static audit cannot promote economic release")

def evaluate_frozen_10k():
    _audit_gate()
    pin=json.loads(FROZEN.read_text(encoding="utf8"))
    if (pin["candidate_count"]!=10000 or pin["nq_indicator_routes"]!=132 or
        pin["seed"]!=20261028):
        raise RuntimeError("Frozen 10K cohort metadata changed")
    batch=structural_batch(count=10000,seed=SEED,
                           random_fraction=.65,max_conditions=8)
    if batch["candidate_sha256"]!=pin["candidate_bundle_canonical_sha256"]:
        raise RuntimeError("10K original candidate SHA mismatch")
    counts=Counter();names=Counter()
    rows=[]
    for s in batch["candidates"]:
        yeslong=_could_be_true(s["long"])
        yesshort=_could_be_true(s["short"])
        leaves=list(_leaves(s["long"]))+list(_leaves(s["short"]))
        impossible=[
            x["indicator"]["name"] for x in leaves
            if (_needed(x["indicator"]) is not None and
                _needed(x["indicator"])+(
                  x["lag_completed_bars"] if x["op"] in LAG_OPS else
                  1 if x["op"] in ("CROSS_ABOVE_LEVEL","CROSS_BELOW_LEVEL")
                  else 0)+(1 if x["op"]=="CROSSES_OWN_LAG" else 0)>MAX_BARS)
        ]
        names.update(impossible)
        category=("BOTH_SIGNAL_SIDES_STATICALLY_UNREACHABLE"
                  if not yeslong and not yesshort
                  else "ONE_SIDE_STATICALLY_UNREACHABLE"
                  if not yeslong or not yesshort
                  else "NO_STATICALLY_PROVEN_TWO_SIDE_BARRIER")
        counts[category]+=1
        rows.append({"id":s["id"],"category":category,
                     "known_long_could_be_true":yeslong,
                     "known_short_could_be_true":yesshort,
                     "unreachable_leaf_instances":len(impossible)})
    assert sum(counts.values())==10000
    return {"schema":"NQ_S032_FROZEN_10K_STATIC_INTRADAY_WARMUP_AUDIT_V1",
            "status":STATUS,"candidate_count":10000,"seed":SEED,
            "candidate_bundle_canonical_sha256":batch["candidate_sha256"],
            "signal_window":"09:35..11:27_NY_END_LABELED",
            "max_completed_RTH_bars_at_last_signal":MAX_BARS,
            "known_formula_warmup_names":sorted(CHECKABLE),
            "lower_bound_status_counts":dict(sorted(counts.items())),
            "names_with_known_insufficient_session_bars":dict(sorted(names.items())),
            "rows":rows,"formal_G0_passed":0,
            "strategies_excluded_or_ranked":0,
            "market_IST_prices_loaded":False,
            "economic_profit_or_fitness_computed":False,
            "gate_13_verified_count":0,
            "holdouts_2023_2024_2025_2026_opened":False,
            "original_cohort_modified":False,
            "warning":"May be false alarms if later authenticated same-contract cross-session warmup is defined; no candidate is removed or declared winner."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=evaluate_frozen_10k()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:r[k] for k in
        ("status","candidate_count","lower_bound_status_counts",
         "market_IST_prices_loaded","formal_G0_passed",
         "strategies_excluded_or_ranked")},sort_keys=True))

if __name__=="__main__":main()
