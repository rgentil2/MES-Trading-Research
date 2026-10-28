#!/usr/bin/env python3
"""S0.27: read-only NQ IST M1 source adapter technical quality audit.

Validated real archive MAY be opened by this technical-only tool, using its
previously frozen SHA-256 and exact 2020-2022 whitelist. It NEVER evaluates
strategy AST, entries, exits, model fills, returns, PnL, PF, DD, fitness,
candidate ranking, or portfolio signals. ALL output is counts, timestamps
ranges (without day-level or price records), cryptographic root hashes and
formula availability diagnostics. No prices or per-candidate outcomes leave
the private GitHub runner. No 2023+ archive member may be opened.

130+ indicator calls are to detect runtime/warmup/casual consistency, NOT to
certify formulas against independent oracles. It does not promote any of the
13 formal quality gates or bypass the later approved economic adapter.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import math
import numpy as np

from research.nq.nq_m1_chrono_discovery import load_years
from research.nq.nq_m1_v23_source_contract_qa import inspect_archive_manifest
from research.nq.nq_m1_v22_contract_provenance import (
    metadata_for_sessions,prior_same_contract
)
from research.nq.nq_m1_v26_structural_generator import one_per_indicator
from research.nq.nq_m1_v26_all_132_router import value as numeric_value
from research.nq.nq_m1_v22_quality_gate import audit as gate_audit

STATUS="S0_27_NQ_IST_M1_ACTUAL_SOURCE_ONLY_TECHNICAL_QA_NO_STRATEGY_OR_PNL"
ALLOWED_YEARS=(2020,2021,2022)
EXPECTED_SHA256="a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8"
EXPECTED={"sessions":735,"partial_excluded":39,"roll_boundaries":12,
          "opened_member_files":15}
EXPECTED_SOURCE_LABEL="NQ M1 OHLCV Minute_Last 2020-2022"
ROOT_PREFIX=b"NQ_IST_2020_2022_1M_READ_ONLY_SOURCE_QA_S027_V1"

def _gate():
    g=gate_audit()
    if (g["decision"]!="EXECUTION_BLOCKED" or
        g["passed_verified"]!=0 or g["checks_total"]!=13 or
        g["ready_for_economic_execution"]):
        raise PermissionError("Cannot run source-only technical QA after gate state change")
    return g

def sha_file(path:Path)->str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def _validate_source(dates:list[str],bars:np.ndarray,source:dict,
                     expected_counts:bool)->list:
    if (not isinstance(dates,list) or len(dates)==0 or
        not isinstance(bars,np.ndarray) or bars.shape!=(len(dates),390,5) or
        not np.isfinite(bars).all() or (bars[:,:,4]<0).any()
        or (bars[:,:,:4]<=0).any() or
        (bars[:,:,1]<np.maximum(bars[:,:,0],bars[:,:,3])).any() or
        (bars[:,:,2]>np.minimum(bars[:,:,0],bars[:,:,3])).any() or
        np.any(np.abs(bars[:,:,:4]/.25-np.round(bars[:,:,:4]/.25))>1e-7)):
        raise ValueError("Invalid complete 390-end-labeled NQ tick-grid M1 sessions")
    if (source.get("years_opened")!=list(ALLOWED_YEARS)
        or source.get("holdout_2025_opened") is not False
        or source.get("holdout_2026_opened") is not False
        or source.get("complete_rth_sessions")!=len(dates)):
        raise PermissionError("IST-only loader evidence not valid")
    if any(type(s) is not str or len(s)!=10 or
           date.fromisoformat(s).isoformat()!=s or
           date.fromisoformat(s).year not in ALLOWED_YEARS for s in dates):
        raise PermissionError("2023+ or invalid source session date")
    if dates!=sorted(set(dates)):
        raise ValueError("Non-unique or unsorted sessions")
    meta=metadata_for_sessions(dates,bars)
    if expected_counts:
        if (len(dates)!=EXPECTED["sessions"] or
            source["partial_sessions_excluded"]!=EXPECTED["partial_excluded"] or
            source["members_opened"]!=EXPECTED["opened_member_files"]):
            raise ValueError("Frozen historical 735-session IST source count changed")
    return meta

def _same(a,b)->bool:
    return (a is None and b is None or
            a is not None and b is not None and
            math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-10))

def source_qa(dates:list[str],bars:np.ndarray,source:dict,
              expected_counts:bool=False,full_indicator_probe:bool=True)->dict:
    """Strictly technical summary from already loaded, whitelisted NQ OHLCV.

    Caller-supplied arrays are accepted for TESTS only; the production entry
    must use audit_archive with exact SHA pre-verification and 15-member list.
    """
    _gate()
    meta=_validate_source(dates,bars,source,expected_counts)
    rolls=[i for i in range(1,len(meta)) if
           meta[i].contract_id!=meta[i-1].contract_id]
    if expected_counts and len(rolls)!=EXPECTED["roll_boundaries"]:
        raise ValueError("Frozen rollover count changed")
    sel=sorted(set((0,len(dates)//2,len(dates)-1,*rolls)))
    # Root fingerprint for integrity only, never record individual prices/days.
    h=hashlib.sha256(ROOT_PREFIX)
    for i,(day,session) in enumerate(zip(dates,bars)):
        h.update(day.encode("ascii"))
        h.update(meta[i].contract_id.encode("ascii"))
        h.update(np.asarray(session,dtype="<f8",order="C").tobytes())
    context_count=0
    complete_previous_count=0
    empty_roll_contexts=0
    for i in sel:
        c=prior_same_contract(dates,bars,i)
        if c["target"].contract_id!=meta[i].contract_id or (
            c["source_contract"]!=meta[i].contract_id or
            c["holdouts"]!="SEALED"):
            raise ValueError("Selected session contract mismatch")
        if i in rolls and len(c["prior_bars"])!=0:
            raise ValueError("Cross-contract context leaked at rollover")
        if i in rolls:empty_roll_contexts+=1
        if len(c["prior_session_dates"])>0:complete_previous_count+=1
        context_count+=1
    counts=Counter()
    error_categories=Counter()
    # In the *actual-source private runner* this technically probes 132
    # registered numerical routes at selected indices, NEVER AST predicates.
    # No candidate logic, historical market trades, fitness or PnL.
    if full_indicator_probe:
        rows=one_per_indicator(seed=20261028)["leaves"]
        if len(rows)!=132 or len({r["indicator"]["name"] for r in rows})!=132:
            raise RuntimeError("Indicator inventory or sampling changed")
        for i in sel:
            previous=prior_same_contract(dates,bars,i)
            historical=previous["prior_bars"]
            ctx={"verified_same_contract":True,
                 "previous_sessions":list(np.split(historical,len(historical)//390))
                 if len(historical) else [],
                 "anchor_index":0}
            for bar_idx in (118,389):
                for r in rows:
                    block=r["indicator"]
                    # Entire completed RTH day passed to router; router itself
                    # truncates to completed bar index (no future dependence).
                    try:
                        observed=numeric_value(bars[i],bar_idx,block,ctx)
                    except (ValueError,IndexError,KeyError,TypeError,FloatingPointError,ZeroDivisionError) as exc:
                        error_categories[type(exc).__name__]+=1
                        continue
                    counts["indicator_calls"]+=1
                    counts["unavailable" if observed is None else "finite"]+=1
                    if observed is not None and not np.isfinite(observed):
                        error_categories["NONFINITE_UNCERTIFIED"]=1
                # Causality check: mutate future data while retaining all
                # previously completed rows and unmodified contract context.
                if bar_idx==118:
                    changed=bars[i].copy()
                    changed[bar_idx+1:,:]=np.nan
                    for r in rows:
                        block=r["indicator"]
                        try:
                            expected=numeric_value(bars[i],bar_idx,block,ctx)
                            actual=numeric_value(changed,bar_idx,block,ctx)
                        except (ValueError,IndexError,KeyError,TypeError,
                                FloatingPointError,ZeroDivisionError) as exc:
                            error_categories["FUTURE_TEST_"+type(exc).__name__]+=1
                            continue
                        counts["future_mutation_probes"]+=1
                        if not _same(actual,expected):
                            error_categories["FUTURE_BAR_CHANGED_OLD_INDICATOR"]+=1
        if error_categories:
            raise AssertionError("Indicator numeric QA fault categories only: "+
                                 json.dumps(dict(sorted(error_categories.items()))))
    return {"schema":"NQ_M1_V32_S027_REAL_IST_SOURCE_READ_ONLY_QA",
            "status":STATUS,"source_label":EXPECTED_SOURCE_LABEL,
            "sessions_checked":len(dates),
            "year_counts":dict(sorted(Counter(d[:4] for d in dates).items())),
            "source_members":source["members_opened"],
            "excluded_partial_sessions":source["partial_sessions_excluded"],
            "roll_boundaries":len(rolls),"context_sessions_probed":context_count,
            "selected_contexts_with_prior_same_contract":complete_previous_count,
            "roll_contexts_confirmed_empty":empty_roll_contexts,
            "indicator_names_routed":132 if full_indicator_probe else 0,
            "indicator_calls":counts["indicator_calls"],
            "indicator_finite_results":counts["finite"],
            "indicator_unavailable_results":counts["unavailable"],
            "future_mutation_probes":counts["future_mutation_probes"],
            "numerical_error_categories":dict(error_categories),
            "source_root_sha256":h.hexdigest(),
            "opened_only_IST_years":list(ALLOWED_YEARS),
            "isv1_2023_opened":False,"isv2_2024_opened":False,
            "sealed_2025_2026_opened":False,
            "contract_roll_policy_modified":False,
            "full_132_external_formula_parity_certified":False,
            "financial_fills_or_signals_evaluated":False,
            "historical_strategy_backtest_executed":False,
            "net_pnl_or_fitness_computed":False,
            "portfolio_stage_opened":False,
            "formal_g0_d0_d1_d2_passed":False,
            "thirteen_quality_gates_verified":0}

def audit_archive(zip_path:Path,expected_sha256:str=EXPECTED_SHA256)->dict:
    _gate()   # Hard lock before ANY historical source file read
    if expected_sha256!=EXPECTED_SHA256:
        raise PermissionError("Do not replace frozen private minute source")
    actual=sha_file(zip_path)
    if actual!=EXPECTED_SHA256:
        raise PermissionError("NQ M1 source SHA mismatch BEFORE archive member reads")
    manifest=inspect_archive_manifest(zip_path)
    if (manifest["source_members"]!=15 or manifest["allowed_years"]!=list(ALLOWED_YEARS)
        or manifest["market_member_contents_opened"]):
        raise ValueError("NQ source member whitelist mismatch")
    dates,bars,source=load_years(zip_path,ALLOWED_YEARS)
    report=source_qa(dates,bars,source,expected_counts=True,
                     full_indicator_probe=True)
    report["source_archive_sha256"]=actual
    report["frozen_15_source_members_verified"]=True
    return report

def main():
    p=argparse.ArgumentParser(description="read-only source QA, no strategy runner")
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=audit_archive(args.zip)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({k:result[k] for k in
        ("status","sessions_checked","excluded_partial_sessions",
         "roll_boundaries","indicator_calls","future_mutation_probes",
         "historical_strategy_backtest_executed","net_pnl_or_fitness_computed",
         "thirteen_quality_gates_verified")},sort_keys=True))

if __name__=="__main__":
    main()
