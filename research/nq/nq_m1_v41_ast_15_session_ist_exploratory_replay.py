#!/usr/bin/env python3
"""S0.36: widen the same frozen 12 AST exploratory M1 replay from 3 to 15 IST sessions.

Sample dates FIRST/MIDDLE/LAST + 12 contract roll sessions are preregistered
by existing S0.33 historical signal QA; they are NOT chosen by observed PnL.
This still is NOT complete 735-session economic backtest or formal G0.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from research.nq.nq_m1_v38_10k_real_ist_signal_smoke import (
    frozen_sample,selected_sessions,EXPECTED_COHORT_SHA
)
from research.nq.nq_m1_v39_ast_ist_exploratory_order_replay import (
    evaluate_fixed_sample
)
from research.nq.nq_m1_v32_real_ist_source_readonly_qa import (
    _gate,_validate_source,sha_file,EXPECTED_SHA256,EXPECTED,ALLOWED_YEARS
)
from research.nq.nq_m1_chrono_discovery import load_years
from research.nq.nq_m1_v23_source_contract_qa import inspect_archive_manifest

STATUS="S0_36_FIRST_12_AST_15_ROLL_SOURCE_IST_SESSIONS_EXPLORATORY_NO_WINNERS"

def compare_15(dates,bars,source,candidates,selection=None):
    _gate()
    _validate_source(dates,bars,source,expected_counts=False)
    chosen=selected_sessions(dates,bars) if selection is None else list(selection)
    if len(chosen)!=15 or chosen!=sorted(set(chosen)):
        raise ValueError("S0.36 requires exactly 15 immutable representative sessions")
    r=evaluate_fixed_sample(dates,bars,source,candidates,chosen=chosen)
    if r["sessions_sampled"]!=15:
        raise AssertionError("15 selected roll/source sessions were not completed")
    r["schema"]="NQ_S036_12_FROZEN_AST_15_IST_EXPLORATORY_REPLAY_V1"
    r["status"]=STATUS
    r["candidate_SHA256"]=EXPECTED_COHORT_SHA
    r["source_index_policy"]="FIRST_MIDDLE_LAST_PLUS_12_ROLL_CONTRACT_BOUNDARIES"
    r["model_trade_results_are_only_sample_15_of_735"]=True
    r["candidate_selection_or_fitness_approval"]=False
    r["portfolio_jointly_simulated"]=False
    r["exact_MFFU_shared_account_rules_certified"]=False
    r["future_N8_ninjatrader_parity_executed"]=False
    return r

def real_archive_pilot_15(path):
    _gate()
    if sha_file(path)!=EXPECTED_SHA256:
        raise PermissionError("Frozen IST original ZIP SHA mismatch BEFORE member read")
    meta=inspect_archive_manifest(path)
    if (meta["source_members"]!=15 or
        meta["allowed_years"]!=list(ALLOWED_YEARS) or
        meta["market_member_contents_opened"]):
        raise PermissionError("Unauthorized price year or nonfrozen member scope")
    days,bars,source=load_years(path,ALLOWED_YEARS)
    _validate_source(days,bars,source,expected_counts=True)
    chosen=selected_sessions(days,bars)
    if len(chosen)!=15:raise RuntimeError("Roll/source calendar changed")
    report=compare_15(days,bars,source,frozen_sample(),selection=chosen)
    if (report["sessions_loaded"]!=EXPECTED["sessions"]
        or report["candidate_count_exploratory"]!=12
        or report["sessions_sampled"]!=15):
        raise RuntimeError("Prerecorded cohort and source coverage changed")
    report["source_zip_sha256"]=EXPECTED_SHA256
    report["IST_total_complete_days"]=EXPECTED["sessions"]
    report["partial_days_excluded"]=EXPECTED["partial_excluded"]
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    r=real_archive_pilot_15(args.zip)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n",
                        encoding="utf8")
    print(json.dumps({k:r[k] for k in
        ("status","candidate_count_exploratory","sessions_sampled","counts",
         "formal_13_gates_verified","all_10k_backtested")},sort_keys=True))

if __name__=="__main__":
    main()
