#!/usr/bin/env python3
"""NQ M1 quality release gate: fail-closed before any economic evaluation.

The --require-ready flag is for future economic job entrypoints and MUST
fail until each mandatory control has PASSED_VERIFIED, immutable evidence
and code health checks. A human review of evidence is still required.
No price archives are read.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from research.nq import nq_m1_v2_generator as legacy_gen
from research.nq import nq_m1_v2_m1_engine as scalar

HERE=Path(__file__).resolve().parent
MATRIX=HERE/"NQ_M1_V22_PRE_EXECUTION_QUALITY_MATRIX_2026_10_27.json"
EXPECTED_IDS=frozenset((
    "DATA_PROVENANCE","INDICATOR_LIBRARY_132","PARAMETER_SEMANTICS",
    "SAME_CONTRACT_WARMUP","SESSION_CLOCK_AND_DST","ORDER_FILL_PARITY",
    "RISK_AND_ACCOUNT","MULTIPLE_TESTS_AND_LINEAGE","G0_D0_ADAPTERS",
    "D1_ECONOMIC_ADAPTER","D2_ROBUSTNESS","PORTFOLIO_SHARED_ACCOUNT",
    "FROZEN_TIME_STAGES"
))
CERTIFIED="PASSED_VERIFIED"
HASH_RE=re.compile(r"^[0-9a-f]{64}$")
PERMITTED_STATES=frozenset(("PASSED_VERIFIED","PASSED_TECHNICAL","PARTIAL","BLOCKED"))


def _quality_digest(matrix:dict)->str:
    """Bind manual release signoff to exact scope and all gate evidence."""
    signed={"schema":matrix["schema"],"asset":matrix["asset"],
            "contracts":matrix["contracts"],"no_mnq":matrix["no_mnq"],
            "holdouts":matrix["holdouts"],"criteria":matrix["criteria"],
            "current_evidence":matrix["current_evidence"]}
    return hashlib.sha256(json.dumps(signed,sort_keys=True,
                 separators=(",",":")).encode("utf8")).hexdigest()


def _approval_valid(matrix:dict, expected_digest:str)->bool:
    approval=matrix.get("final_release_approval")
    if not isinstance(approval,dict) or approval.get("approved") is not True:
        return False
    if approval.get("approved_scope")!="ONE_NQ_IST_2020_2022_ECONOMICS_ONLY":
        return False
    if (approval.get("reviewed_quality_sha256")!=expected_digest
            or not HASH_RE.fullmatch(str(approval.get("frozen_evaluator_sha256","")))):
        return False
    reviewer=approval.get("reviewer")
    run=approval.get("approved_run_url")
    return (isinstance(reviewer,str) and bool(reviewer.strip())
            and isinstance(run,str)
            and run.startswith("https://github.com/rgentil2/"))


def audit(matrix_path:Path=MATRIX)->dict:
    r=json.loads(matrix_path.read_text(encoding="utf-8"))
    if (r.get("schema")!="NQ_M1_V22_PRE_ECONOMIC_QUALITY_GATE_V1"
            or r.get("asset")!="NQ"
            or r.get("contracts")!=1
            or r.get("no_mnq") is not True
            or r.get("holdouts")!="ISV1_2023_ISV2_2024_NO_FIT_H2025_H2026_T_SEALED"):
        raise ValueError("Invalid NQ-only research protocol")
    criteria=r.get("criteria",[])
    if len(criteria)!=13 or {x["id"] for x in criteria}!=EXPECTED_IDS:
        raise ValueError("Mandatory quality checks missing, duplicated or renamed")
    blocked=[]
    for x in criteria:
        if x.get("mandatory") is not True or x.get("state") not in PERMITTED_STATES:
            raise ValueError("Mandatory gate invalid")
        if x["state"]!=CERTIFIED:
            blocked.append({"id":x["id"],"status":x["state"],
                            "remaining":x["remaining"]})
        elif not isinstance(x.get("verified_evidence_ref"),dict):
            blocked.append({"id":x["id"],"status":"MISSING_IMMUTABLE_PROOF",
                            "remaining":["A verified artifact hash and CI job are mandatory"]})
        elif not (HASH_RE.fullmatch(str(x["verified_evidence_ref"].get("sha256","")))
                  and str(x["verified_evidence_ref"].get("run_url","")).startswith(
                      "https://github.com/rgentil2/")):
            blocked.append({"id":x["id"],"status":"INVALID_EVIDENCE_REFERENCE",
                            "remaining":["Provide verifiable SHA256 and GitHub CI run"]})
    registry=legacy_gen.read_registry()
    coverage=len(scalar.SUPPORTED_INDICATORS)
    if registry["total_blocks"]!=132 or coverage!=38:
        raise RuntimeError("Unreviewed indicator coverage change; recreate QA proofs")
    base=r["current_evidence"]
    if (base.get("registered_blocks")!=132 or
            base.get("implemented_blocks")!=38 or
            base.get("externally_parity_tested")!=15 or
            base.get("economically_evaluated") is not False):
        raise ValueError("Historical baseline evidence mismatch")
    if r.get("decision")!="DO_NOT_RUN_ECONOMIC_BACKTEST_UNTIL_ALL_MANDATORY_GATES_PASSED_WITH_EVIDENCE":
        raise ValueError("Hard stop policy changed without preregistration")
    technical_pass=(len(blocked)==0)
    release_digest=_quality_digest(r)
    approval_valid=_approval_valid(r,release_digest)
    # A listing of 13 plausible hashes is not independent proof. A separate
    # explicitly scoped, version-bound manual approval is REQUIRED, and
    # future jobs still need to check the real artifacts in the source repo.
    ready=technical_pass and approval_valid
    return {"schema":r["schema"],"asset":"NQ","contracts":1,
            "registered_blocks":132,"computed_blocks":coverage,
            "external_parity_baseline":15,
            "checks_total":13,
            "passed_verified":13-len(blocked),
            "blocked":blocked,
            "technical_quality_checks_complete":technical_pass,
            "final_manual_release_approved":approval_valid,
            "release_evidence_digest":release_digest,
            "ready_for_economic_execution":ready,
            "decision":("ECONOMIC_IST_SCOPE_AUTHORIZED" if ready
                        else "EXECUTION_BLOCKED" if blocked
                        else "REQUIRES_FINAL_MANUAL_APPROVAL"),
            "holdouts":"SEALED","no_market_data_read":True}


def require_ready(matrix_path:Path=MATRIX):
    summary=audit(matrix_path)
    if not summary["ready_for_economic_execution"]:
        errors=[x["id"] for x in summary["blocked"]]
        if not summary["final_manual_release_approved"]:
            errors.append("FINAL_RELEASE_APPROVAL")
        raise PermissionError("NQ ECONOMIC BACKTEST BLOCKED: "+", ".join(errors))
    return summary


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--require-ready",action="store_true")
    p.add_argument("--matrix",type=Path,default=MATRIX)
    a=p.parse_args()
    result=audit(a.matrix)
    print(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True))
    if a.require_ready and not result["ready_for_economic_execution"]:
        raise SystemExit(2)


if __name__=="__main__":
    main()
