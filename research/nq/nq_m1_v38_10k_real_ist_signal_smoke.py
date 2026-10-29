#!/usr/bin/env python3
"""S0.33 first adapter for REAL IST NQ M1 -> frozen 10K AST G0 signal evaluator.

This is ONLY a diagnostic smoke test of exactly 12 predeclared 10K ASTs,
15 representative real 2020-22 NQ sessions, and 5 completed M1 decisions.
No orders, PnL, drawdown, strategy ranking, portfolio or formal G0 approval.
A later independently authorized economic engine must be separately versioned.

Historical data may be read only by audit_original_archive() after SHA256 and
source-member validation. 2023/24 validation and 2025/26 sealed stages never
open. Output contains ONLY aggregated signal categories and diagnostics.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np
from research.nq.nq_m1_v26_structural_generator import structural_batch,SEED
from research.nq.nq_m1_v28_funnel_ledger import FROZEN
from research.nq.nq_m1_v30_132_signal_m1_bridge import signals_at
from research.nq.nq_m1_v22_contract_provenance import prior_same_contract,metadata_for_sessions
from research.nq.nq_m1_v32_real_ist_source_readonly_qa import (
    _gate,_validate_source,sha_file,EXPECTED_SHA256,EXPECTED,ALLOWED_YEARS
)
from research.nq.nq_m1_chrono_discovery import load_years
from research.nq.nq_m1_v23_source_contract_qa import inspect_archive_manifest

STATUS="S0_33_REAL_IST_FROZEN_10K_AST_FIRST_SIGNAL_SMOKE_NOT_G0_APPROVAL"
CANDIDATE_INDICES=(0,909,1818,2727,3636,4545,5454,6363,7272,8181,9090,9999)
BAR_INDICES=(4,25,50,85,116)
EXPECTED_COHORT_SHA="b9d2915fc55f86546ef63d74a588df5244d094eeecb4a7c900a4000d47660be9"
ACTIONS=frozenset((
    "LONG","SHORT","BOTH_SIDES_CONFLICT","NO_SIGNAL",
    "UNAVAILABLE_SOME_SIGNAL_DATA"
))

def frozen_sample():
    _gate()
    frozen=json.loads(FROZEN.read_text(encoding="utf8"))
    batch=structural_batch(count=10000,seed=SEED,random_fraction=.65,max_conditions=8)
    if (batch["candidate_sha256"]!=EXPECTED_COHORT_SHA
        or batch["candidate_sha256"]!=frozen["candidate_bundle_canonical_sha256"]
        or batch["count"]!=10000):
        raise RuntimeError("Frozen 10K AST cohort or lineage hash changed")
    return [batch["candidates"][i] for i in CANDIDATE_INDICES]

def selected_sessions(dates,bars):
    meta=metadata_for_sessions(dates,bars)
    rolls=[i for i in range(1,len(meta))
           if meta[i].contract_id!=meta[i-1].contract_id]
    sample=sorted(set((0,len(dates)//2,len(dates)-1,*rolls)))
    if len(dates)==EXPECTED["sessions"] and (
        len(rolls)!=EXPECTED["roll_boundaries"] or len(sample)!=15):
        raise RuntimeError("Previously verified real IST source roll/sample changed")
    return sample

def diagnostic(dates,bars,source,candidates,indices=None):
    """Caller-arrays ONLY for synthetic unit tests. Real entry must audit SHA."""
    _gate()
    _validate_source(dates,bars,source,expected_counts=False)
    if (not isinstance(candidates,list) or not 1<=len(candidates)<=12
        or len({r["id"] for r in candidates})!=len(candidates)):
        raise ValueError("Require a small unique frozen-candidate sample")
    sample=selected_sessions(dates,bars) if indices is None else indices
    if (not isinstance(sample,list) or not sample or
        any(type(i) is not int or not 0<=i<len(dates) for i in sample)
        or sample!=sorted(set(sample))):
        raise ValueError("Invalid fixed session indexes")
    counts=Counter()
    candidate_counts={}
    for candidate in candidates:
        outcome=Counter()
        for idx in sample:
            context=prior_same_contract(dates,bars,idx)
            if context["target"].contract_id!=context["source_contract"]:
                raise ValueError("Cross-contract context not allowed")
            for k in BAR_INDICES:
                try:
                    decision=signals_at(
                        bars[idx],k,candidate,dates[idx],session_context=context)
                except (ValueError,KeyError,TypeError,IndexError,
                        FloatingPointError,ZeroDivisionError) as exc:
                    # Never quietly convert an implementation exception to a
                    # losing strategy or missing signal.
                    raise RuntimeError(
                        "G0_AST_SIGNAL_IMPLEMENTATION_"+type(exc).__name__) from exc
                if (decision["action"] not in ACTIONS or
                    decision["decision_bar_index"]!=k or
                    decision["candidate_id"]!=candidate["id"] or
                    decision["trades_executed"]!=0 or decision["fitness_evaluated"]):
                    raise RuntimeError("Signal evaluator returned economic or invalid state")
                outcome[decision["action"]]+=1
                outcome["unavailable_leaf_checks"]+=decision[
                    "unavailable_indicator_leaf_evaluations"]
        counts.update({k:v for k,v in outcome.items() if k in ACTIONS})
        candidate_counts[candidate["id"]]=dict(sorted(outcome.items()))
    return {
        "schema":"NQ_S033_FROZEN_10K_FIRST_IST_AST_SIGNAL_SMOKE_V1",
        "status":STATUS,
        "data_source":"NQ_M1_IST_2020_2022_ONLY",
        "sessions_loaded":len(dates),
        "sessions_sampled":len(sample),
        "completed_end_label_bar_indices":list(BAR_INDICES),
        "sampled_frozen_candidate_indices":list(CANDIDATE_INDICES)
            if len(candidates)==len(CANDIDATE_INDICES) else None,
        "candidate_count_exploratory":len(candidates),
        "signal_evaluations":len(candidates)*len(sample)*len(BAR_INDICES),
        "aggregate_actions":dict(sorted(counts.items())),
        "per_candidate_signal_counts_not_fitness":candidate_counts,
        "original_10k_frozen_cohort_changed":False,
        "all_10k_historical_evaluated":False,
        "full_session_trade_lifecycle_evaluated":False,
        "orders_or_market_fills_evaluated":False,
        "real_pnl_or_pf_computed":False,
        "G0_D0_D1_D2_formally_passed":False,
        "economic_quality_gates_verified":0,
        "ninjatrader_winner_backtest_performed":False,
        "ISV1_2023_ISV2_2024_2025_2026_opened":False}

def audit_original_archive(path:Path):
    _gate()
    if sha_file(path)!=EXPECTED_SHA256:
        raise PermissionError("Source SHA mismatch BEFORE ZIP member read")
    m=inspect_archive_manifest(path)
    if (m["source_members"]!=15
        or m["allowed_years"]!=list(ALLOWED_YEARS)
        or m["market_member_contents_opened"]):
        raise PermissionError("Unexpected archive contents or source member scope")
    dates,bars,source=load_years(path,ALLOWED_YEARS)
    _validate_source(dates,bars,source,expected_counts=True)
    candidates=frozen_sample()
    result=diagnostic(dates,bars,source,candidates)
    if (result["sessions_sampled"]!=15 or result["signal_evaluations"]!=900
        or result["candidate_count_exploratory"]!=12):
        raise RuntimeError("Actual fixed smoke-test cardinality changed")
    result["real_market_source_zip_sha256"]=EXPECTED_SHA256
    result["full_IST_session_count"]=EXPECTED["sessions"]
    result["original_cohort_sha256"]=EXPECTED_COHORT_SHA
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=audit_original_archive(a.zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                     encoding="utf8")
    print(json.dumps({k:result[k] for k in (
        "status","sessions_sampled","signal_evaluations","aggregate_actions",
        "G0_D0_D1_D2_formally_passed","real_pnl_or_pf_computed"
    )},sort_keys=True))

if __name__=="__main__":
    main()
