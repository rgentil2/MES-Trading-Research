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
        require(d1["status"] in ("COMPLETE","LOCKED_WAITING_FOR_20_DIVERSE_D0",
                                  "RUNNING_FULL36_ECONOMIC_PROXY_UNVERIFIED"),
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
        elif d1["status"]=="RUNNING_FULL36_ECONOMIC_PROXY_UNVERIFIED":
            require(b["stage"]=="D0_COMPLETE_D1_RUNNING"
                    and len(d0["diverse_ids"])>=20
                    and len(d1["evaluated_ids"])==0
                    and d1["workflow_run"] is not None
                    and d1["q_min"] is None
                    and not d1["statistical_screen_pass_ids"]
                    and not d1["economic_screen_pass_ids"],
                    "running D1 cannot claim results or bypass 20+ D0 gate")
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
            {"NQ-C29-58","NQ-C20-25","NQ-C26-28","NQ-C59-NEXT","NQ-C97-132","NQ-C133-168"},
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
    strategy=next(x for x in cohorts if x["id"]=="NQ-C133-168")
    require(strategy["all_preregistered_ids"]==[f"T{i}" for i in range(133,169)]
            and strategy["origin"]=="NEW_BATCH_20_PLUS"
            and strategy["stage"] in ("D0_COMPLETE_D1_RUNNING","D1_CLOSED")
            and len(strategy["D0"]["testable_ids"])==29
            and len(strategy["D0"]["diverse_ids"])==27
            and set(strategy["D0"]["low_power_ids"])==
                {"T134","T138","T139","T143","T144","T153","T154"}
            and set(strategy["D0"]["near_duplicate_ids"])==
                {"T150","T164"}
            and strategy["D0"]["workflow_run"]==38325498797
            and strategy["original_20_frozen_seed"]["source_action"]==38324292967
            and strategy["original_20_frozen_seed"]["seed_20_masks_reproduced_exactly"] is True
            and strategy["stage"]=="D1_CLOSED"
            and strategy["D1"]["status"]=="COMPLETE"
            and strategy["D1"]["evaluated_ids"]==strategy["all_preregistered_ids"]
            and strategy["D1"]["workflow_run"]==38326216082
            and strategy["D1"]["q_min"]==1.0
            and not strategy["D1"]["individual_ci90_positive_ids"]
            and len(strategy["D1"]["statistical_screen_pass_ids"])==0
            and len(strategy["D1"]["economic_screen_pass_ids"])==0,
            "36 member full strategy original plus prospective 16 D0/D1 zero-alpha was rewritten")
    shadow=strategy.get("shadow_D2",{})
    portfolios=shadow.get("six_portfolios",[])
    require(shadow.get("status")=="COMPLETED_POSTHOC_EDUCATIONAL_ONLY_NO_PROMOTION"
            and shadow.get("action_run")==38335007318
            and shadow.get("review_action_run")==38335648618
            and shadow.get("same_D1_36_reproduced_exactly") is True
            and shadow.get("official_D2_promoted_count")==0
            and shadow.get("holdouts_opened") is False
            and len(portfolios)==6
            and [z["id"] for z in portfolios]==[
              "ALL36_ID_PRIORITY","ALL36_CALENDAR_ROTATION",
              "DIVERSE27_CALENDAR_ROTATION","POSITIVE10_ID_PRIORITY_POSTHOC",
              "POSITIVE5_N15_ID_PRIORITY_POSTHOC","T147_ONLY_POSTHOC"]
            and [round(z["net_usd"],2) for z in portfolios]==
                [-1063.0,-1840.62,-2164.38,774.50,683.12,642.25]
            and strategy["D2"]["promoted_ids"]==[]
            and strategy["D2"]["status"]=="NOT_STARTED_ZERO_ELIGIBLE_EXECUTABLE_STRATEGIES",
            "SHADOW educational result must not be used to forge formal D2 approval")
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
               else "**D1 en ejecución (SIN RESULTADOS AÚN)**" if b["stage"]=="D0_COMPLETE_D1_RUNNING"
               else "D1 cerrado (sin calificadas)")
        diverse=(str(len(d["diverse_ids"])) if b["origin"]=="NEW_BATCH_20_PLUS"
                 else "N/D (legacy)")
        lines.append(f"| {b['id']} | {len(b['all_preregistered_ids'])} → "
          f"{len(d['testable_ids'])} → {diverse} "
          f"| {scored} → {surv} | {len(b['D2']['promoted_ids'])} | {state} |")
    strategy=next(b for b in ledger["cohorts"] if b["id"]=="NQ-C133-168")
    lines.extend(["",
      "## Estado del NUEVO EMBUDO ECONÓMICO de 36 miembros T133–T168 — D1 CERRADA",
      "",
      "- **Ocho bloques de estrategias completas**, 20 originales "
      "T133–T152 INMUTABLES +16 nuevas T153–T168 registradas antes D0. "
      "**D0 36→29 TESTABLE→27 diversas**, supera gate20; "
      "semilla original CASE/CONTROL reproducida EXACTA.",
      "- **D1 ECONÓMICA PROXY completada en los 36** "
      "([Action 38326216082](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38326216082)). "
      "**q BH36 mínima=1,0, 0/36 con IC90 L5 enteramente positivo, "
      "0/36 aprueban los filtros.** 26 netos negativos, 5 positivos pero "
      "inconclusos, 5 insuficientes (<15 operaciones proxy).",
      "- **Ejemplos que NO son alfa:** T133 +US$606,75 "
      "pero año 2026 DEV negativo, T145 +US$788 pero PF≈1,238 "
      "y q1, T147 +US$642,25 con Q4 2025 negativo. "
      "Todos son PnL de MODELO HIPOTÉTICO y sin confirmación broker.",
      "- **Ejecución** en Last: peores precios atómicos, "
      "2 ticks de fricción entrada/salida, stop primero si "
      "barreras coinciden, fees SUPUESTAS NQ/MNQ, estrés 1,5x "
      "y +US$10 RT. 10k bootstrap bloque por día, BH familiar k36.",
      "- **Cortes cronológicos 53/82 DEV**, previamente explorados "
      "y NO un OOS nuevo; holdouts mayo–septiembre 2026 SELLADOS.",
      f"- **Bandeja D2:** {a['D2_batch_size']} candidatas, "
      "no permite fondeo ni una cartera monetizada. "
      "No sumar PnL de hipótesis solapadas.",
      "- **Cohortes observacionales anteriores T29–T58/T59–T96/T97–T132:** "
      "104 estudios D1 en bloques y ninguna sobrevivió BH familiar; "
      "T05 solo baseline legacy congelado.",
      "",
      "## D2 SHADOW — ejercicio solicitado, NO aprobación D2 oficial",
      "",
      "- **Action SHADOW 38335007318 SUCCESS**: seis carteras independientes, "
      "una sola señal por día/cuenta, 135 DEV. Reproducción exacta de "
      "36 D1 en N/neto y costes estresados. Auditoría SAFE 38335648618.",
      "- **Tres carteras sin selección por ganancias** perdieron: "
      "36 prioridad −$1.063 PF0,895 DD$2.947; "
      "36 rotación −$1.840,62 PF0,826 DD$3.379,62; "
      "27 diversas −$2.164,38 PF0,795 DD$3.454,12. "
      "Todas rebasan DD cerrado $2.000 ilustrativo.",
      "- **Ganadoras RETROSPECTIVAS**: top10 +$774,50 y top5 "
      "+$683,12 (PF1,098 y 1,086), pero los dos escenarios "
      "de costes ESTRESADOS resultan NEGATIVOS. "
      "Elegidas tras mirar la MISMA DEV: sobreajuste.",
      "- **T147 sola RETROSPECTIVA**: +$642,25 PF1,499, "
      "estrés positivo, pero Q4 2025 −$567 y solo20 trades "
      "(2,86 al mes). No aprobada como cartera de fondeo.",
      "- **D2 FORMAL=0** y 0 fills reales. "
      "Las cifras son proxies Last con fees asumidas, "
      "DD de equity cerrada NO trailing intradía real.",
      "",
      "**[Informe SHADOW D2 de seis carteras](NQ_T133_T168_SHADOW_D2_SIX_PORTFOLIOS_RESULTS_2026_10_12.md)** · "
      "[Action original](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38335007318) · "
      "[Auditoría SAFE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38335648618).",
      "",
      "**Próxima prioridad:** en lugar de incrementar miles de "
      "contrastes en las mismas 135 DEV, examinar si se puede "
      "validar ejecución/costos reales y planificar una muestra "
      "verdaderamente independiente antes de otro bloque.",
      "",
      "**Fuentes:** [Reporte D0 completo](NQ_T133_T168_FULL36_EXECUTABLE_D0_RESULTS_2026_10_12.md) · "
      "[Reporte D1 económico](NQ_T133_T168_ECONOMIC_D1_FULL36_RESULTS_2026_10_12.md) · "
      "[Prerregistro de D1](NQ_T133_T168_36_MEMBER_ECONOMIC_D1_PREREG_2026_10_12.md).",
      "",
      "El ledger resume únicamente agregados seguros; "
      "sin filas de mercado ni operaciones privadas.",
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
