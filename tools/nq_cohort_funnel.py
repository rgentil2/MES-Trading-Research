#!/usr/bin/env python3
"""Offline audit + dashboard for the NQ cohort research funnel.

NEVER reads licensed market data, session-level returns or holdouts.
Source: research/nq/NQ_COHORT_FUNNEL_POLICY_2026_10_12.json
        research/nq/NQ_COHORT_FUNNEL_LEDGER_2026_10_12.json
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

POLICY = Path("research/nq/NQ_COHORT_FUNNEL_POLICY_2026_10_12.json")
LEDGER = Path("research/nq/NQ_COHORT_FUNNEL_LEDGER_2026_10_12.json")
REPORT = Path("research/nq/NQ_COHORT_FUNNEL_STATUS_2026_10_12.md")

def require(ok, reason):
    if not ok:
        raise ValueError("NQ_FUNNEL_BLOCKED: " + reason)

def unique(seq):
    return len(seq) == len(set(seq))

def subset(a,b):
    return set(a) <= set(b)

def validate(policy,ledger):
    require(policy.get("policy_id") == "NQ-COHORT-FUNNEL-V1"
            and ledger.get("policy_id") == policy["policy_id"], "wrong policy")
    require(policy.get("schema_version")==1 and ledger.get("schema_version")==1,
            "schema version")
    require(policy.get("status")=="ACTIVE_USER_DIRECTED"
            and policy.get("extends_policy")=="NQ-DISCOVERY-STAGED-GATES-V1",
            "existing gates cannot be silently replaced")
    require(policy.get("stages")==["IDEAS","G0","D0","D1","D2","CONFIRMATION"],
            "stage routing")
    require(policy.get("transition_unit")=="BATCH_ONLY_NO_INDIVIDUAL_HYPOTHESIS_RUNS",
            "individual-stage shortcuts prohibited")
    rules=policy["stage_rules"]
    require(rules["D0"]["testable_min_case"]==15
            and rules["D0"]["testable_min_control"]==15
            and rules["D0"]["diversity_case_jaccard_below"]==0.85
            and rules["D0"]["minimum_diverse_testable_for_new_D1_cohort"]==20,
            "D0 batch entry thresholds")
    require(rules["D2"]["minimum_nonredundant_survivors_to_start_economic_batch"]==2,
            "do not research single D2 survivor")
    f=policy["permanent_invariants"]
    require(all(f.values()), "a permanently forbidden action was re-enabled")
    require(policy["previous_completed_batches_are_not_retroactively_qualified"] is True,
            "closed families cannot be requalified")
    require(ledger.get("holdouts_opened") is False
            and ledger.get("new_data_acquired") is False,
            "sealed holdout/new data flag changed")
    cohorts=ledger.get("cohorts",[])
    require(len(cohorts)>=4, "missing historical stage cohorts")
    all_seen=set()
    stat_survivors=set()
    econ_survivors=set()
    for b in cohorts:
        ids=b["all_preregistered_ids"]
        require(bool(ids) and unique(ids), "bad original family members")
        require(not (all_seen & set(ids)), "same hypothesis inserted in two cohorts")
        all_seen.update(ids)
        require(b["G0"]["status"]=="PASS"
                and b["G0"]["source"]==140
                and b["G0"]["eligible"]==135,
                "G0 source coverage failed: "+b["id"])
        d0=b["D0"];d1=b["D1"];d2=b["D2"]
        require(set(d0["evaluated_ids"])==set(ids),
                "D0 omitted original family member: "+b["id"])
        for key in ("testable_ids","diverse_ids","low_power_ids","near_duplicate_ids"):
            require(unique(d0[key]) and subset(d0[key],ids), "invalid D0 "+key)
        require(subset(d0["diverse_ids"],d0["testable_ids"]), "a non-testable was included as diverse")
        require(not set(d0["testable_ids"]) & set(d0["low_power_ids"]),
                "D0 testable and low power contradict")
        require(not set(d0["diverse_ids"]) & set(d0["near_duplicate_ids"]),
                "near-duplicate counted as independent")
        require(d0["workflow_run"] and d0["report"], "missing reproducible D0 proof")
        require(d1["status"] in ("COMPLETE","LOCKED_WAITING_FOR_20_DIVERSE_D0"),
                "unknown D1 state")
        if d1["status"]=="COMPLETE":
            require(b["stage"]=="D1_CLOSED"
                    and set(d1["evaluated_ids"])==set(ids),
                    "ALL original IDs must be evaluated together in D1")
            if b["origin"]=="NEW_BATCH_20_PLUS":
                require(len(d0["diverse_ids"])>=20,
                        "cannot advance solitary NEW idea to D1")
            require(d1["workflow_run"] and d1["report"], "D1 evidence missing")
            require(subset(d1["individual_ci90_positive_ids"],ids),
                    "unregistered D1 outcome")
            require(subset(d1["statistical_screen_pass_ids"],d0["testable_ids"]),
                    "D1 statistical survivor did not pass D0")
            require(subset(d1["economic_screen_pass_ids"],d0["testable_ids"]),
                    "D1 economic survivor did not pass D0")
            if d1["q_min"] is not None and d1["q_min"] > .1:
                require(not d1["statistical_screen_pass_ids"],
                        "BH q>0.10 cohort cannot claim statistical PASS")
            stat_survivors.update(d1["statistical_screen_pass_ids"])
            econ_survivors.update(d1["economic_screen_pass_ids"])
        else:
            require(b["stage"]=="D0_POOL_FORMING"
                    and len(d0["diverse_ids"])<20
                    and d1["evaluated_ids"]==[]
                    and d1["workflow_run"] is None
                    and d1["q_min"] is None,
                    "D1 started individually before 20+ D0")
            require(not d1["statistical_screen_pass_ids"]
                    and not d1["economic_screen_pass_ids"],
                    "unrun D1 fabricated survivors")
        require(not d2["assessed_ids"] and not d2["promoted_ids"],
                "D2 not actually performed; cannot be marked PASS")
    pool=ledger["pooled_D2"]
    require(set(pool["statistically_eligible_ids"])==stat_survivors
            and set(pool["economically_eligible_ids"])==econ_survivors,
            "D2 promotion queue does not reconcile with D1")
    require(set(pool["d2_batch_ids"]) <= econ_survivors,
            "non-economic predictive markout cannot enter execution D2")
    require(not pool["d2_batch_ids"]
            or len(pool["d2_batch_ids"]) >= 2,
            "no one-at-a-time D2")
    require(pool["monetary_validated_strategies"]==0,
            "cannot declare monetization via D0/D1 ledger")
    baseline=ledger["separate_baselines"]
    require(any(x["id"]=="T05-377"
                and x["status"]=="FROZEN_LEGACY_BENCHMARK_ONLY"
                and x["qualifies_D1_to_D2"] is False for x in baseline),
            "T05 benchmark cannot shortcut cohort progression")
    require("T05-377" not in all_seen, "legacy benchmark enrolled as new alpha")
    require(set(ledger["nonportable_historical_reference_ids"]) ==
            {"H69","H74","H77"}, "historical incompatible refs cannot be revived")
    require({b["id"] for b in cohorts} ==
            {"NQ-C29-58","NQ-C20-25","NQ-C26-28","NQ-C59-NEXT","NQ-C97-132","NQ-C133-152"},
            "unexpected cohort roster; version ledger before adding one")
    latest=next(x for x in cohorts if x["id"]=="NQ-C29-58")
    require(len(latest["all_preregistered_ids"])==30
            and len(latest["D0"]["testable_ids"])==27
            and len(latest["D0"]["diverse_ids"])==25
            and len(latest["D1"]["individual_ci90_positive_ids"])==3
            and not latest["D1"]["statistical_screen_pass_ids"],
            "audited existing main batch was rewritten")
    seed=next(x for x in cohorts if x["id"]=="NQ-C59-NEXT")
    require(seed["all_preregistered_ids"] == ["T59","T60"] +
            [f"T{i}" for i in range(61,97)]
            and len(seed["D0"]["testable_ids"]) == 36
            and len(seed["D0"]["diverse_ids"]) == 31
            and seed["D0"]["low_power_ids"] == ["T60","T77"]
            and seed["D0"]["near_duplicate_ids"] ==
                ["T71","T81","T82","T83","T84"]
            and seed["D0"]["workflow_run"] == 38313046875
            and seed["D1"]["status"] == "COMPLETE"
            and len(seed["D1"]["evaluated_ids"]) == 38
            and seed["D1"]["workflow_run"] == 38313582820
            and .239 < seed["D1"]["q_min"] < .240
            and len(seed["D1"]["individual_ci90_positive_ids"]) == 7
            and not seed["D1"]["statistical_screen_pass_ids"]
            and not seed["D1"]["economic_screen_pass_ids"],
            "completed 38-member cohort or its D1 no-pass audit rewritten")
    current=next(x for x in cohorts if x["id"]=="NQ-C97-132")
    require(current["all_preregistered_ids"]==[f"T{i}" for i in range(97,133)]
            and current["origin"]=="NEW_BATCH_20_PLUS"
            and current["stage"]=="D1_CLOSED"
            and len(current["D0"]["testable_ids"])==30
            and len(current["D0"]["diverse_ids"])==26
            and set(current["D0"]["low_power_ids"])==
                 {"T110","T125","T127","T128","T129","T132"}
            and set(current["D0"]["near_duplicate_ids"])==
                 {"T102","T114","T115","T120"}
            and current["D0"]["workflow_run"]==38318189842
            and len(current["D1"]["evaluated_ids"])==36
            and current["D1"]["workflow_run"]==38318511015
            and .263 < current["D1"]["q_min"] < .265
            and set(current["D1"]["individual_ci90_positive_ids"])==
                 {"T100","T103","T108","T111","T112","T119","T130"}
            and not current["D1"]["statistical_screen_pass_ids"]
            and not current["D1"]["economic_screen_pass_ids"],
            "new T97–T132 cohort 36→30→26→36→0 was altered")
    strategy=next(x for x in cohorts if x["id"]=="NQ-C133-152")
    require(strategy["all_preregistered_ids"]==[f"T{i}" for i in range(133,153)]
            and strategy["origin"]=="NEW_BATCH_20_PLUS"
            and strategy["stage"]=="D0_POOL_FORMING"
            and len(strategy["D0"]["testable_ids"])==15
            and len(strategy["D0"]["diverse_ids"])==15
            and set(strategy["D0"]["low_power_ids"])==
                {"T134","T138","T139","T143","T144"}
            and not strategy["D0"]["near_duplicate_ids"]
            and strategy["D0"]["workflow_run"]==38324292967
            and strategy["D1"]["status"]=="LOCKED_WAITING_FOR_20_DIVERSE_D0"
            and strategy["D1"]["evaluated_ids"]==[]
            and strategy["D1"]["workflow_run"] is None
            and strategy["D1"]["q_min"] is None
            and not strategy["D1"]["statistical_screen_pass_ids"]
            and not strategy["D1"]["economic_screen_pass_ids"],
            "latest complete strategy cohort D0 20→15 and locked D1 tampered")
    return {"status":"FUNNEL_VALIDATED","cohorts":len(cohorts),
            "new_D0_diverse_candidates":len(strategy["D0"]["diverse_ids"]),
            "new_D0_gap_to_next_D1":max(0,20-len(strategy["D0"]["diverse_ids"])),
            "D1_statistical_survivors":len(stat_survivors),
            "D1_economic_survivors":len(econ_survivors),
            "D2_batch_size":len(pool["d2_batch_ids"]),
            "holdouts_opened":False}

def render(policy,ledger):
    a=validate(policy,ledger)
    lines=["# NQ — Tablero del embudo por COHORTES",
           "", "**Control de flujo:** unidad operativa = BLOQUE COMPLETO. "
               "D1 nueva exige ≥20 candidatas D0 diversas, y el universo BH "
               "sigue incluyendo todos los miembros prerregistrados.",
           "",
           "| Cohorte | D0: registradas → testables → diversas | D1: medidas → selección familiar | D2: calificadas | Estado |",
           "|---|---:|---:|---:|---|"]
    for b in ledger["cohorts"]:
        d=b["D0"];s=b["D1"]
        scored=len(s["evaluated_ids"])
        surv=len(set(s["statistical_screen_pass_ids"]) |
                 set(s["economic_screen_pass_ids"]))
        state=("**ESPERA:** completar bloque D0" if b["stage"]=="D0_POOL_FORMING"
               else "D1 cerrado (sin calificadas)")
        diverse=(str(len(d["diverse_ids"])) if b["origin"]=="NEW_BATCH_20_PLUS"
                 else "N/D (legacy)")
        lines.append(f"| {b['id']} | {len(b['all_preregistered_ids'])} → "
          f"{len(d['testable_ids'])} → {diverse} "
          f"| {scored} → {surv} | {len(b['D2']['promoted_ids'])} | {state} |")
    lines.extend(["",
      "## Estado actual: T133–T152 — estrategias completas D0, D1 BLOQUEADA",
      "",
      "- **Nueva cohorte de cuatro familias operativas:** 20 originales "
      "(ruptura, pullback, barrida/reversión y régimen), con entrada "
      "teórica, stop físico y objetivo R, horizonte y riesgo prefijados. "
      "**D0: 20→15 TESTABLE→15 diversas**; gate mínimo **20 NO cumplido**, "
      "faltan **5 nuevas estrategias distintivas y viables**. "
      "LOW_POWER: T134/T138/T139/T143/T144. Sin near duplicates.",
      "- **No D1 T133–T152:** ningún outcome futuro, IC90, "
      "p/q BH, N operaciones realmente ejecutadas, coste, PF/DD ni P&L. "
      "Son **N/D**, nunca rellenar como cero, positivo o aprobado.",
      "- **Corte cronológico interno:** 53 READY oct–dic 2025 y 82 "
      "ene–abr 2026, ambos YA explorados; no equivale a OOS independiente.",
      "- **T97–T132 D1 cerrada:** 36 miembros, 30 D0 testables, 26 "
      "diversas, q BH36 mínima 0,264, **0 supervivientes**.",
      "- **T59–T96 D1 cerrada:** 38 miembros, q BH38 mínima 0,239376, "
      "0 supervivientes; **T29–T58** 30 D1 con qmin0,212229 y 0.",
      "- **T20–T25/T26–T28 históricas:** D1 cerradas, sin "
      "estrategia monetariamente validada.",
      f"- **Bandeja económica D2:** {a['D2_batch_size']} candidatas; "
      "vacía. T05 sigue baseline congelado, no promocionar.",
      "",
      "## Siguiente acción metodológicamente válida",
      "",
      "Prerregistrar otro **BLOQUE DE MECANISMOS EJECUTABLES DIFERENTES** "
      "con nuevos IDs, sin retocar T134/T138/T139/T143/T144 para inflar N. "
      "Cuando el inventario acumule >=20 TESTABLE y diversas, "
      "prerregistrar D1 ECONÓMICA de la **familia completa ORIGINAL** "
      "con comisiones, slippage, manejo adverso de fills, coste "
      "y cortes cronológicos, ANTES de cualquier resultado.",
      "",
      "**Fuentes:** [T133–T152 D0 CORREGIDO](NQ_T133_T152_FOUR_COMPLETE_STRATEGIES_BLOCKS_D0_RESULTS_2026_10_12.md) · "
      "[T133–T152 prereg](NQ_T133_T152_EXECUTABLE_D0_PREREG_2026_10_12.md) · "
      "[Política económica de cohortes](NQ_EXECUTABLE_STRATEGY_COHORT_POLICY_2026_10_12.md) · "
      "[T97–T132 D1](NQ_T97_T132_36_MEMBER_D1_RESULTS_2026_10_12.md).",
      "",
      "Estado generado desde ledger **seguro**; no abre "
      "mercado licenciado ni lee ningún dato futuro.",
      ""])
    return "\n".join(lines)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--policy",type=Path,default=POLICY)
    p.add_argument("--ledger",type=Path,default=LEDGER)
    p.add_argument("--output",type=Path,default=REPORT)
    p.add_argument("--verify-report",action="store_true")
    a=p.parse_args()
    policy=json.loads(a.policy.read_text())
    ledger=json.loads(a.ledger.read_text())
    status=validate(policy,ledger)
    report=render(policy,ledger)
    if a.verify_report:
        require(a.output.read_text()==report,"committed dashboard is stale")
    else:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(report)
    print(json.dumps(status,sort_keys=True))
