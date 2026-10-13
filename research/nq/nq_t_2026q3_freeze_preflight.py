#!/usr/bin/env python3
"""Read-only DEV to T-July-Sep pseudo-forward freeze preparation (NO market reads).

Resolve static LOCAL Python import closure via AST only: do NOT import research
engines or read licensed price files. Output code SHA256 manifest as safe
artifact. This script NEVER opens the sealed pseudo-forward.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Iterable

ROOT=Path(__file__).resolve().parents[2]
FREEZE=ROOT/"research/nq/NQ_T_2026Q3_PSEUDOFORWARD_FINAL_FREEZE_V1.json"
IDENTITY="NQ-T-2026Q3-PSEUDOFORWARD-FREEZE-V1"
DEV="2025-10"
SEALED_MONTHS=("2026-07","2026-08","2026-09")


def get_path_for_module(module:str):
    if module.startswith("research.nq."):
        path=ROOT/("research/nq/"+module.split(".")[-1]+".py")
    elif "." not in module:
        path=ROOT/("local_nq_tick_2025_2026/"+module+".py")
    else:
        return None
    return path if path.is_file() else None


def python_dependency_closure(entrypaths:Iterable[str])->list[str]:
    todo=[str(x) for x in entrypaths]
    seen=set()
    while todo:
        rel=todo.pop()
        if rel in seen:continue
        path=ROOT/rel
        if not path.is_file():
            raise ValueError("FROZEN_MODULE_NOT_FOUND:"+rel)
        seen.add(rel)
        try:
            parsed=ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as e:
            raise ValueError("INVALID_FROZEN_PYTHON_SYNTAX:"+rel) from e
        for node in ast.walk(parsed):
            modules=[]
            if isinstance(node,ast.Import):
                modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module is not None:
                modules=[node.module]
            for name in modules:
                found=get_path_for_module(name)
                if found:
                    child=found.relative_to(ROOT).as_posix()
                    if child not in seen:todo.append(child)
    return sorted(seen)


def fingerprint(records:dict[str,str]):
    return hashlib.sha256(
        "".join(f"{k}\x00{v}\n" for k,v in sorted(records.items())).encode()
    ).hexdigest()


def prereg_contract(data):
    if (data["freeze_protocol_id"]!=IDENTITY
        or data["temporal_roles"]["single_final_holdout"]["start"]!="2026-07-01"
        or data["temporal_roles"]["single_final_holdout"]["end"]!="2026-09-30"
        or data["temporal_roles"]["single_final_holdout"]["not_read"] is not True
        or data["temporal_roles"]["single_final_holdout"]["one_shot"] is not True
        or data["temporal_roles"]["internal_reserved"]["not_read"] is not True
        or data["temporal_roles"]["unrelated_H_holdouts"]["must_remain_sealed"] is not True
        or data["access_control"]["preflight_must_not_open_prices_or_trades"] is not True
        or data["access_control"]["no_new_downloads"] is not True
        or data["single_account"]["max_open_positions"]!=1
        or data["single_account"]["max_new_trades_per_day"]!=2
        or data["single_account"]["strategy_daily_closed_stop_usd"]!=-600
        or data["single_account"]["fees_mffu_rt_usd"]!={"NQ":4.68,"MNQ":1.9}
        or data["official_challenge_assumptions_at_registration"]["max_loss_usd"]!=2000
        or data["official_challenge_assumptions_at_registration"]["target_usd"]!=3000
        or data["frozen_portfolios"]["A"]["members"]!=["T05-377","T215"]
        or data["frozen_portfolios"]["B"]["members"]!=["T05-377","T186","T215"]
        or data["frozen_portfolios"]["benchmark"]["members"]!=["T05-377"]
        or data["not_yet_authorized_to_unseal"] is not True):
        raise ValueError("PSEUDOFORWARD_CONTRACT_INTEGRITY_FAILURE")


def prepare():
    data=json.loads(FREEZE.read_text())
    prereg_contract(data)
    graph=python_dependency_closure(data["source_entrypoints"])
    configs=sorted(set(data["explicit_config_files"]))
    deps=sorted(set(graph+configs))
    if len(deps)<15:
        raise ValueError("SUSPICIOUSLY_SMALL_IMPORT_CLOSURE")
    manifest={}
    for rel in deps:
        path=ROOT/rel
        if not path.is_file():raise ValueError("FROZEN_CONFIG_NOT_FOUND:"+rel)
        manifest[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
    digest=fingerprint(manifest)
    expected=data.get("source_fingerprint_sha256")
    if expected is not None and expected!=digest:
        raise ValueError("SOURCE_CHANGED_AFTER_PSEUDOFORWARD_LOCK")
    # Crucial: the research engine is DEV-only, so running it on July dates
    # would FAIL CLOSED. We must build a separate OOS adapter and verify it
    # on DEV without changing signal algorithms BEFORE sealed data access.
    gates=[
        "research_engine_dev_day_restricts_to_2025_10_15__2026_04_30",
        "qc_tick_day_blocks_july_september_2026",
        "nq_tick_short_horizon_month_month_days_dev_only",
        "nq_t209_t228_structural_d0_month_guard_dev_only",
        "no_oos_adapter_yet",
        "no_private_holdout_presence_or_coverage_verified",
    ]
    for path in ("local_nq_tick_2025_2026/nq_tick_short_horizon.py",
                 "local_nq_tick_2025_2026/qc_tick_day.py",
                 "local_nq_tick_2025_2026/nq_tick_short_horizon_month.py",
                 "local_nq_tick_2025_2026/nq_t209_t228_structural_d0.py"):
        if path not in manifest:
            raise AssertionError("SCOPE_GUARD_MISSING_FROM_CODE_LOCK:"+path)
    return {
        "stage":"FROZEN_SOURCE_INVENTORY_NO_DATA_READ",
        "lock_status":"PINNED_SOURCE_SHA256" if expected else "PENDING_SHA256_PIN",
        "protocol":IDENTITY,
        "source_fingerprint_sha256":digest,
        "config_sha256":hashlib.sha256(FREEZE.read_bytes()).hexdigest(),
        "files_checked":len(deps),"local_python_modules":len(graph),
        "files_sha256":manifest,
        "missing_holdout_adapter":True,
        "holdout_coverage_verified":False,
        "holdout_authorized_to_unseal":False,
        "OOS_prices_opened":False,
        "H_holdouts_opened":False,
        "safe_to_execute_one_shot_holdout":False,
        "blocking_facts":gates,
    }


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--summary",type=Path,required=True)
    args=p.parse_args()
    result=prepare()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    summary={
        k:v for k,v in result.items() if k!="files_sha256"
    }
    args.summary.write_text(
        "# Preflight Pseudo-forward T Jul–Sep2026 SIN DATOS\n\n"
        +"\n".join(f"- **{k}**: {v}" for k,v in summary.items())+"\n"
    )
    print("PSEUDOFORWARD_T_LOCK_MANIFEST_SAFE="+json.dumps({
        "lock":result["lock_status"],
        "sha256":result["source_fingerprint_sha256"],
        "modules":result["local_python_modules"],
        "files":result["files_checked"],
        "OOS_unsealed":False,
        "one_shot_allowed":False,
    },sort_keys=True))
