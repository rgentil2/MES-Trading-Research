#!/usr/bin/env python3
"""S0.23: reproducible event-ready tracking ledger for the frozen 10k NQ cohort.

STRICT: No market data, no signals/trades/fills, no performance values and
no "G0 pass" claims. Each row is an immutable candidate AST fingerprint
plus technical-only scope diagnostics. Formal funnel stages remain WAITING
until independently signed and approved economic evaluation. Files contain
only generated rules and metadata, never prices.

Regenerates the S0.22 cohort from the exact seed and verifies its pinned
candidate SHA: avoids dependence on a 30-day Actions artifact. Does not
regenerate a NEW cohort or mutate its parent/parameter rules.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from research.nq.nq_m1_v26_all_132_router import catalogue,inventory,_parameters
from research.nq.nq_m1_v26_structural_generator import (
    VERSION,LEVEL_OPS,LAG_OPS,OUTPUTS,structural_batch,sha
)
from research.nq.nq_m1_v27_first_structural_campaign import walk
from research.nq.nq_m1_v22_quality_gate import audit as quality_audit

HERE=Path(__file__).resolve().parent
FROZEN=HERE/"NQ_M1_V27_10K_STRUCTURAL_QA_2026_10_28.json"
SCHEMA="NQ_V28_FROZEN_COHORT_FUNNEL_LEDGER_S023_PRE_ECONOMIC"
STAGES=("G0","D0","D1","D2","ISV1_2023","ISV2_2024","PORTFOLIO","MFFU_50K")
STATUS="BLOCKED_PRE_ECONOMIC_RELEASE"
FORBIDDEN_KEYS={"net_usd","pnl","profit_factor","drawdown","fitness",
                "equity","trades","orders_executed","rank","score"}

def _sha_data(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def _fail(condition:bool,reason:str)->None:
    if not condition:raise ValueError(reason)

def inspect_structure(s:dict,all_ids:set[str],seen:set[str])->dict:
    """Check known generator AST contracts; NOT a substitute for formal G0."""
    _fail(isinstance(s,dict),"NOT_MAPPING")
    _fail(not FORBIDDEN_KEYS.intersection(s),"UNAUTHORIZED_ECONOMIC_FIELDS")
    sid=s.get("id")
    _fail(isinstance(sid,str) and sid.startswith("NQ26_") and
          sid=="NQ26_"+sha(s)[:16],"CANDIDATE_ID_HASH_INCONSISTENT")
    _fail(sid not in seen,"DUPLICATE_CANDIDATE_ID")
    _fail(s.get("ast_version")==VERSION and
          s.get("schema")=="NQ_M1_V26_AST_PRE_ECONOMIC",
          "UNKNOWN_AST_VERSION")
    _fail(s.get("universe")=="NQ_M1" and
          s.get("position_sizing")=={"instrument":"NQ","contracts":1},
          "WRONG_UNIVERSE_OR_CONTRACT_SIZE")
    _fail(s.get("market_data_years_permitted_for_discovery")==[2020,2021,2022],
          "YEAR_SCOPE_VIOLATION")
    _fail(s.get("signal_clock")=="America/New_York" and
          s.get("bars_are_end_labeled") is True and
          s.get("signal_uses_completed_bars_only") is True,
          "CLOCK_OR_CAUSAL_BAR_POLICY")
    _fail(s.get("exit",{}).get("flat_at_et")=="11:29" and
          isinstance(s["exit"].get("stop_loss_required"),dict) and
          isinstance(s["exit"].get("profit_target"),dict),
          "INVALID_EXIT_ENVELOPE")
    _fail(s.get("entry_order",{}).get("kind") in ("MARKET","LIMIT","STOP"),
          "INVALID_ENTRY_ORDER_TYPE")
    entry=s["entry_order"]
    expected_entry={"kind","offset_ticks","expiry_bars"}
    _fail(set(entry)==expected_entry,"ENTRY_UNRECOGNIZED_FIELDS")
    _fail(type(entry["offset_ticks"]) is int and 0<=entry["offset_ticks"]<=32
          and type(entry["expiry_bars"]) is int
          and 1<=entry["expiry_bars"]<=30,"ENTRY_PARAMS_OUTSIDE_GENERATOR")
    _fail((entry["kind"]!="MARKET" or
           (entry["offset_ticks"]==0 and entry["expiry_bars"]==1)),
          "MARKET_ORDER_OFFSET_NOT_ZERO")
    lin=s.get("lineage")
    _fail(isinstance(lin,dict) and set(lin)=={"operator","parents"} and
          lin["operator"] in ("RANDOM","MUTATE","CROSSOVER") and
          isinstance(lin["parents"],list),"INVALID_LINEAGE")
    expected_parents={"RANDOM":0,"MUTATE":1,"CROSSOVER":2}[lin["operator"]]
    _fail(len(lin["parents"])==expected_parents and
          len(set(lin["parents"]))==expected_parents and
          all(p in seen for p in lin["parents"]),"PARENT_NOT_PREVIOUS_VALID_ID")
    # Verify the exact registered domains, operations and chosen scalar output.
    lengths=[]
    families=set()
    named=set()
    for side in ("long","short"):
        tree=s.get(side)
        _fail(isinstance(tree,dict),"TREE_NOT_MAPPING")
        leaves=list(walk(tree))
        _fail(1<=len(leaves)<=8,"INVALID_CONDITION_COUNT")
        lengths.append(len(leaves))
        for node in leaves:
            b=node["indicator"]
            _fail(isinstance(b,dict) and
                  set(b) in ({"name","registry_id","parameters"},
                             {"name","registry_id","parameters","output"}),
                  "INDICATOR_BLOCK_FIELDS")
            name=b["name"]
            entrymeta=catalogue().get(name)
            _fail(entrymeta is not None and
                  b["registry_id"]==entrymeta["id"],"UNREGISTERED_INDICATOR")
            _parameters(entrymeta,b["parameters"])
            selections=OUTPUTS.get(name)
            if selections:
                _fail(b.get("output") in selections,"INVALID_OUTPUT_LINE")
            else:
                _fail("output" not in b,"INACTIVE_OUTPUT_LINE")
            if node["op"] in LEVEL_OPS:
                _fail(set(node)=={"op","indicator","threshold"} and
                      type(node["threshold"]) in (int,float) and
                      node["threshold"]==0 and
                      bool(set(b["parameters"])&
                           {"threshold","lower_level","upper_level",
                            "z_threshold","ratio_threshold"}),
                      "INVALID_TYPED_LEVEL_OP")
            elif node["op"] in LAG_OPS:
                _fail(set(node)=={"op","indicator","lag_completed_bars"} and
                      type(node["lag_completed_bars"]) is int and
                      1<=node["lag_completed_bars"]<=20 and
                      not bool(set(b["parameters"])&
                          {"threshold","lower_level","upper_level",
                           "z_threshold","ratio_threshold"}),
                      "INVALID_LAG_PREDICATE")
            else:
                raise ValueError("UNKNOWN_PREDICATE")
            named.add(name)
            families.add(entrymeta["group"])
    return {"id":sid,"ast_sha256":sha(s),"operator":lin["operator"],
            "parent_ids":"|".join(lin["parents"]),
            "entry_kind":entry["kind"],
            "stop_kind":s["exit"]["stop_loss_required"]["kind"],
            "target_kind":s["exit"]["profit_target"]["kind"],
            "long_conditions":lengths[0],"short_conditions":lengths[1],
            "indicator_names_count":len(named),"indicator_groups_count":len(families),
            "status":"STRUCTURALLY_CHECKED_NO_MARKET",
            "formal_stage":"PRE_G0_WAITING","formal_g0_pass":False,
            "formal_d0_pass":False,"formal_d1_pass":False,
            "formal_d2_pass":False,"isv1_opened":False,"isv2_opened":False,
            "portfolio_approved":False,"economic_fitness_measured":False,
            "blocker":"QUALITY_13_GATES_NOT_VERIFIED",
            "reason":"NO_HISTORICAL_FILLS_OR_CERTIFIED_INDICATOR_PARITY"}

def regenerate_and_track(count:int=10000,seed:int=20261028):
    pinned=json.loads(FROZEN.read_text(encoding="utf8"))
    _fail(pinned["candidate_count"]==10000 and
          pinned["nq_indicator_routes"]==132 and
          pinned["seed"]==20261028,"SOURCE_EVIDENCE_CHANGED")
    _fail(count==10000 and seed==20261028,"COHORT_SPECIFICATION_MUST_STAY_FROZEN")
    gate=quality_audit()
    if (gate["decision"]!="EXECUTION_BLOCKED"
        or gate["passed_verified"]!=0
        or gate["ready_for_economic_execution"]):
        raise PermissionError("Cannot use technical-only ledger under changed gate state")
    _fail(inventory()["coded"]==132,"LIBRARY_INVENTORY_CHANGED")
    batch=structural_batch(count=count,seed=seed,random_fraction=.65,max_conditions=8)
    _fail(batch["candidate_sha256"]==pinned["candidate_bundle_canonical_sha256"],
          "FROZEN_10K_SOURCE_SHA_MISMATCH")
    rows=[]
    seen=set()
    failed=[]
    for s in batch["candidates"]:
        try:
            row=inspect_structure(s,set(),seen)
        except (ValueError,KeyError,TypeError,IndexError) as exc:
            # NEVER discard failures or treat untested candidates as passes.
            failed.append({"id":s.get("id"),"reason":str(exc)})
            row={"id":s.get("id"),"ast_sha256":sha(s),
                 "status":"FAILED_STRUCTURAL_PRECHECK",
                 "formal_stage":"PRE_G0_WAITING","formal_g0_pass":False,
                 "economic_fitness_measured":False,
                 "blocker":"INVALID_STRUCTURE","reason":str(exc)}
        seen.add(s["id"])
        rows.append(row)
    status=Counter(r["status"] for r in rows)
    result={"schema":SCHEMA,"date":"2026-10-28",
            "frozen_source_sha256":pinned["candidate_bundle_canonical_sha256"],
            "source_run_url":pinned["run_url"],
            "cohort_seed":seed,"cohort_candidates":len(rows),
            "structural_precheck_pass":status["STRUCTURALLY_CHECKED_NO_MARKET"],
            "structural_precheck_fail":status["FAILED_STRUCTURAL_PRECHECK"],
            "failure_causes":dict(Counter(x["reason"] for x in failed)),
            "formal_funnel_stages":[{"stage":k,"passed":0,"rejected":0,
                                     "unstarted":len(rows)}
                                    for k in STAGES],
            "release_gates_total":13,"release_gates_verified":0,
            "ready_for_economic_execution":False,
            "holdouts":"SEALED",
            "market_prices_read":False,"economic_fitness_computed":False,
            "strategies_ranked":False,"portfolio_released":False,
            "status":STATUS}
    return rows,result

def export(out:Path,rows:list[dict],summary:dict)->dict:
    out.mkdir(parents=True,exist_ok=True)
    csv_path=out/"nq_v28_candidate_funnel_ledger.csv"
    fields=("id","ast_sha256","operator","parent_ids","entry_kind",
            "stop_kind","target_kind","long_conditions","short_conditions",
            "indicator_names_count","indicator_groups_count","status",
            "formal_stage","formal_g0_pass","formal_d0_pass","formal_d1_pass",
            "formal_d2_pass","isv1_opened","isv2_opened","portfolio_approved",
            "economic_fitness_measured","blocker","reason")
    with csv_path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",
                         lineterminator="\n")
        w.writeheader()
        for row in rows:w.writerow(row)
    summary=dict(summary)
    summary["csv_sha256"]=_sha_data(csv_path.read_bytes())
    summary["field_names"]=list(fields)
    summary_path=out/"nq_v28_funnel_stage_summary.json"
    summary_path.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=Path("/tmp/nq_v28_funnel_ledger"))
    a=p.parse_args()
    rows,report=regenerate_and_track()
    final=export(a.out,rows,report)
    print(json.dumps({k:final[k] for k in ("cohort_candidates",
        "structural_precheck_pass","structural_precheck_fail",
        "release_gates_verified","ready_for_economic_execution",
        "csv_sha256")},sort_keys=True))
    print("NQ_V28_FUNNEL_10K_TRACKED_WITHOUT_PNL")

if __name__=="__main__":
    main()
