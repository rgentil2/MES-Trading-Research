#!/usr/bin/env python3
"""NQ 132-block inventory gap report, independent of prices and fitness.

IMPORTANT: a registry name or a passing synthetic test is never evidence
of economic readiness. The legacy 38 stay frozen. Isolated incubator formulas
are not executable in the V2.1 strategy engine. No missing blocks are
silently removed from the full search space.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from research.nq.nq_m1_v2_generator import read_registry, CATALOG_PATH
from research.nq.nq_m1_v2_m1_engine import SUPPORTED_INDICATORS
from research.nq.nq_m1_v22_incubator_ma import PROTOTYPES as MA
from research.nq.nq_m1_v22_incubator_oscillators import PROTOTYPES as OSC
from research.nq.nq_m1_v25_extra_scalars import PROTOTYPES as EXTRA
from research.nq.nq_m1_v25_candle_patterns import PATTERNS as CANDLES

STATES={
  "FROZEN_V21_RUNTIME": "mathematical prototype in original frozen engine; external certification incomplete",
  "ISOLATED_20261027": "separate math prototype, not enabled for economic discovery",
  "ISOLATED_20261028": "new scalar prototype, synthetic QA only, not enabled for economic discovery",
  "ISOLATED_CANDLE_20261028": "custom candlestick rules, not externally certified or eligible for economic selection",
  "NOT_IMPLEMENTED": "registry design only; no accepted runtime calculation"
}

def audit()->dict:
    registry=read_registry()
    active=set(SUPPORTED_INDICATORS)
    prior=set(MA)|set(OSC)
    new=set(EXTRA)
    candles=set(CANDLES)
    allnames={x["name"] for x in registry["entries"]}
    if any(not x<=allnames for x in (active,prior,new,candles)):
        raise RuntimeError("Indicator code not present in frozen catalogue")
    if active&prior or active&new or prior&new or candles&(active|prior|new):
        raise RuntimeError("Ambiguous implementation/promotions")
    if len(active)!=38 or len(prior)!=5 or len(new)!=12 or len(candles)!=12 or len(allnames)!=132:
        raise RuntimeError("Coverage changed; require independent audit")
    rows=[]
    for x in registry["entries"]:
        name=x["name"]
        state=("FROZEN_V21_RUNTIME" if name in active
           else "ISOLATED_20261027" if name in prior
           else "ISOLATED_20261028" if name in new
           else "ISOLATED_CANDLE_20261028" if name in candles
           else "NOT_IMPLEMENTED")
        rows.append({
            "id":x["id"],"name":name,"group":x["group"],
            "status":state,
            "catalogue_parameters":sorted(x["parameters"]),
            "verified_external_implementation":False,
            "eligible_for_economic_selection":False
        })
    counts={s:sum(x["status"]==s for x in rows) for s in STATES}
    if counts!={"FROZEN_V21_RUNTIME":38,"ISOLATED_20261027":5,
               "ISOLATED_20261028":12,"ISOLATED_CANDLE_20261028":12,"NOT_IMPLEMENTED":65}:
        raise RuntimeError("Unexpected coverage math")
    return {
        "report_schema":"NQ_V25_INDICATOR_GAPS_NO_ECONOMIC_RELEASE",
        "catalogue_sha256":hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(),
        "universe":"NQ", "registered_blocks":132,
        "counts":counts,"historically_original_external_parity":15,
        "external_certification_not_inferred_from_grouping":True,
        "all_132_certified":False,"economics_executed":False,
        "stage":"PRE_ECONOMIC_TECHNICAL", "holdouts":"SEALED",
        "rows":rows
    }

if __name__=="__main__":
    print(json.dumps(audit(),indent=2,sort_keys=True))
