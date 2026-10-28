#!/usr/bin/env python3
"""NQ S0.22 first broad structural candidate campaign: NO historical prices, NO PnL.

Purpose: create a reusable, immutable inventory for later IST-only scoring when
the existing 13 evidence gates are all independently passed. A structural
candidate is a potential trade rule, NOT a measured/selected winning strategy.

Both random and genetic STRUCTURAL operators are used. Parent selection is
uniform because historical fitness is unavailable and forbidden at this stage.
No 2023/24 ISV, no 2025/26 sealed data, no tick or OHLC file is opened.
"""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
from research.nq.nq_m1_v26_all_132_router import inventory
from research.nq.nq_m1_v26_structural_generator import (
    VERSION, SEED, structural_batch, one_per_indicator, sha
)
from research.nq.nq_m1_v2_generator import CATALOG_PATH, read_registry
from research.nq.nq_m1_v22_quality_gate import audit as quality_audit

SCHEMA="NQ_V27_S022_PRE_ECONOMIC_STRUCTURAL_CAMPAIGN"
PROHIBITED=frozenset(("profit_factor","profit","pnl","net_usd","drawdown",
                       "trades","fills","equity","score","fitness","rank"))

def walk(expr):
    if expr["op"] in ("AND","OR"):
        yield from walk(expr["left"])
        yield from walk(expr["right"])
    else:
        yield expr

def safe_record(value:dict):
    forbidden=PROHIBITED.intersection(value.keys())
    if forbidden:
        raise PermissionError("Economic metadata forbidden in structural manifest: "+repr(sorted(forbidden)))

def summarize(batch:dict, coverage:dict, *, source_sha:str=""):
    quality=quality_audit()
    if (quality["ready_for_economic_execution"] or
            quality["decision"]!="EXECUTION_BLOCKED" or
            quality["checks_total"]!=13 or
            quality["passed_verified"]!=0):
        raise PermissionError("Campaign safety state changed; explicit reapproval required")
    details=inventory()
    if details["coded"]!=132 or details["economic_execution_authorized"]:
        raise PermissionError("132 registry coverage unavailable or silently promoted")
    rows=batch["candidates"]
    expected={x["name"] for x in read_registry()["entries"]}
    names=Counter()
    operations=Counter()
    orders=Counter()
    stops=Counter()
    targets=Counter()
    conditions=Counter()
    lineage=Counter()
    unknown_names=set()
    hashes=set()
    fingerprints=[]
    for s in rows:
        safe_record(s)
        if (s["universe"]!="NQ_M1" or s["ast_version"]!=VERSION or
            s["position_sizing"]!={"instrument":"NQ","contracts":1} or
            s["market_data_years_permitted_for_discovery"]!=[2020,2021,2022]):
            raise PermissionError("NQ scope, version, one contract or IST-only guarantee lost")
        key=sha(s)
        if key in hashes:
            raise AssertionError("Duplicate raw AST in unique batch")
        hashes.add(key)
        fingerprints.append(key)
        conditions_number=0
        for side in ("long","short"):
            leaves=list(walk(s[side]))
            conditions_number+=len(leaves)
            for node in leaves:
                name=node["indicator"]["name"]
                names[name]+=1
                operations[node["op"]]+=1
                if name not in expected:
                    unknown_names.add(name)
        conditions[conditions_number]+=1
        orders[s["entry_order"]["kind"]]+=1
        stops[s["exit"]["stop_loss_required"]["kind"]]+=1
        targets[s["exit"]["profit_target"]["kind"]]+=1
        lineage[s["lineage"]["operator"]]+=1
        if s["lineage"]["operator"]!="RANDOM" and not s["lineage"]["parents"]:
            raise AssertionError("Missing parent lineage")
    if unknown_names:
        raise AssertionError("Unknown indicator names "+repr(sorted(unknown_names)))
    named_coverage={x["indicator"]["name"] for x in coverage["leaves"]}
    if named_coverage!=expected or len(coverage["leaves"])!=132:
        raise AssertionError("Incomplete 132/132 per-name coverage")
    if not {"RANDOM","MUTATE","CROSSOVER"}.issubset(lineage):
        raise AssertionError("Both structural generation operators required")
    if len(rows)!=batch["count"] or len(hashes)!=batch["count"]:
        raise AssertionError("Inconsistent candidate count")
    # No relative market prices, signals, orders, trades or financial fitness.
    # Missing broad-sample named indicators are still represented in the
    # independent 132-name coverage artifact, not dropped as losers.
    return {
        "schema":SCHEMA,
        "status":"CANDIDATE_STRUCTURES_ONLY_NOT_STRATEGY_ECONOMIC_SEARCH",
        "git_source_commit":source_sha or "UNSPECIFIED_LOCAL",
        "generator_version":VERSION,
        "seed":batch["seed"],
        "candidates_generated":batch["count"],
        "candidate_bundle_sha256":batch["candidate_sha256"],
        "candidate_fingerprints_sha256":hashlib.sha256(
            "\n".join(fingerprints).encode()).hexdigest(),
        "catalogue_sha256":hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(),
        "indicator_routes":details["coded"],
        "per_indicator_coverage_names":len(named_coverage),
        "observed_in_broad_batch":len(names),
        "name_frequencies":dict(sorted(names.items())),
        "predicate_frequencies":dict(sorted(operations.items())),
        "entries":dict(sorted(orders.items())),
        "stop_kinds":dict(sorted(stops.items())),
        "profit_target_kinds":dict(sorted(targets.items())),
        "condition_count_distribution":dict(sorted((str(k),v) for k,v in conditions.items())),
        "structural_operators":dict(sorted(lineage.items())),
        "duplicate_raw_ast_count":0,
        "holdouts_opened":False,
        "real_ist_ohlcv_loaded":False,
        "real_ist_ticks_loaded":False,
        "fitness_computed":False,
        "trade_count_computed":False,
        "historical_ranking_computed":False,
        "candidates_certified_for_trading":0,
        "economic_gate":{"total":13,"passed_verified":0,
                         "ready_for_economic_execution":False,
                         "decision":"EXECUTION_BLOCKED"},
    }

def run(count:int,seed:int,out:Path,max_conditions:int=8,random_fraction:float=.65,
        source_sha:str=""):
    if (type(count) is not int or not 100<=count<=50000
        or type(seed) is not int or not 0<=seed<2**32
        or not 1<=max_conditions<=100
        or not 0<random_fraction<1):
        raise ValueError("Invalid bounded campaign parameters")
    batch=structural_batch(count,seed,random_fraction,max_conditions)
    cover=one_per_indicator(seed)
    summary=summarize(batch,cover,source_sha=source_sha)
    summary["max_conditions"]=max_conditions
    summary["requested_random_fraction"]=random_fraction
    out.mkdir(parents=True,exist_ok=True)
    # gzip created with fixed mtime, deterministic bytes per input, no secrets.
    target=out/"nq_v27_candidate_ast.jsonl.gz"
    with target.open("wb") as sink:
        with gzip.GzipFile(fileobj=sink,mode="wb",filename="",mtime=0,compresslevel=6) as gz:
            for row in batch["candidates"]:
                gz.write((json.dumps(row,sort_keys=True,separators=(",",":"))+"\n").encode())
    path=out/"nq_v27_132_name_coverage.json"
    path.write_text(json.dumps(cover,sort_keys=True,indent=2)+"\n",encoding="utf8")
    summary["artifact_candidate_gzip_sha256"]=hashlib.sha256(target.read_bytes()).hexdigest()
    summary["artifact_132_coverage_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
    (out/"nq_v27_structural_summary.json").write_text(
        json.dumps(summary,sort_keys=True,indent=2)+"\n",encoding="utf8")
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--count",type=int,default=10000)
    p.add_argument("--seed",type=int,default=20261028)
    p.add_argument("--random-fraction",type=float,default=.65)
    p.add_argument("--max-conditions",type=int,default=8)
    p.add_argument("--output",type=Path,default=Path("/tmp/nq_structural_campaign"))
    a=p.parse_args()
    result=run(a.count,a.seed,a.output,a.max_conditions,
               a.random_fraction,os.environ.get("GITHUB_SHA",""))
    # Avoid verbose PII. Report only metadata and zero-market guarantees.
    subset={k:result[k] for k in (
      "candidates_generated","candidate_bundle_sha256","indicator_routes",
      "per_indicator_coverage_names","observed_in_broad_batch",
      "structural_operators","entries","stop_kinds","profit_target_kinds",
      "fitness_computed","holdouts_opened","economic_gate")}
    print(json.dumps(subset,sort_keys=True))
    print("NQ_V27_STRUCTURAL_CAMPAIGN_NO_MARKET_COMPLETED")

if __name__=="__main__":
    main()
