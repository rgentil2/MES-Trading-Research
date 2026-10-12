#!/usr/bin/env python3
"""Offline, source-only validation of the adopted NQ discovery-stage policy.

Never loads market ticks, strategy outcomes, releases or holdouts.
Not a replacement for original research_governance.py family preflight.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

EXPECTED_STAGES = ("G0", "D0", "D1", "D2", "CONFIRMATION")
EXPECTED_DEV = ("2025-10", "2025-11", "2025-12", "2026-01",
                "2026-02", "2026-03", "2026-04")
OUTPUTS = {
    "G0": {"QC_OK", "BLOCKED_DATA"},
    "D0": {"TESTABLE", "LOW_POWER", "UNIDENTIFIABLE"},
    "D1": {"PROMISING_IN_SAMPLE_ONLY", "INCONCLUSIVE",
           "FAIL_ECONOMIC", "NOT_ESTIMABLE"},
    "D2": {"EXECUTION_RESEARCH_ONLY", "ROBUST_EXPLORATORY",
           "BLOCKED_EXECUTION", "FAIL_RISK"},
    "CONFIRMATION": {"REFER_TO_FROZEN_LEGACY_POLICY"},
}
REQUIRED_FIELDS = {"id", "question", "family", "N_case", "N_control",
                   "N_sessions", "N_trades", "N_effective",
                   "CI90_units_method", "BH_q_family_status",
                   "Holm_status", "router_paired_delta", "G0", "D0",
                   "D1", "D2", "legacy_gate1_status", "decision",
                   "workflow_run", "artifact_digest"}

def require(value, detail: str) -> None:
    if not value:
        raise ValueError(detail)

def check_policy(data: dict) -> dict:
    require(data.get("policy_id") == "NQ-DISCOVERY-STAGED-GATES-V1",
            "wrong immutable policy_id")
    require(data.get("schema_version") == 1, "wrong schema_version")
    require(data.get("status") == "ACTIVE_USER_APPROVED", "not active policy")
    require(data.get("policy_type") == "PROSPECTIVE_ADDITIVE_RESEARCH_TRIAGE",
            "policy must be additive and prospective")
    require(set(data.get("scope", ())) == {"NQ", "MNQ"}, "scope changed")
    for flag in ("prior_experiments_reclassified", "original_frozen_gates_changed",
                 "original_holm_budget_changed", "original_economic_hurdle_changed",
                 "broker_executability_assumed"):
        require(data.get(flag) is False, "forbidden true flag: " + flag)

    authorized = data.get("authorized_data", {})
    for flag in ("new_market_history_acquisition", "new_five_second_signals",
                 "holdouts_opened"):
        require(authorized.get(flag) is False, "unsafe data permission " + flag)
    for flag in ("source_only_existing_stored_NQ_MNQ", "legacy_T05_frozen_comparator_only",
                 "raw_last_private_and_cleanup_required", "atomic_same_timestamp_groups"):
        require(authorized.get(flag) is True, "missing source safety " + flag)
    require(tuple(authorized.get("dev_T_months", ())) == EXPECTED_DEV,
            "DEV whitelist altered")
    require((authorized.get("expected_source_sessions"),
             authorized.get("expected_eligible_sessions")) == (140, 135),
            "DEV session reconciliation altered")
    require(authorized.get("holdout_T_internal") == ["2026-05", "2026-06"],
            "T internal holdout altered")
    require(authorized.get("holdout_T_sealed") == ["2026-07", "2026-08", "2026-09"],
            "T final holdout altered")
    require(authorized.get("holdout_H_years") == [2025, 2026],
            "H holdout years altered")

    stages = data.get("stages", ())
    require(tuple(x["id"] for x in stages) == EXPECTED_STAGES,
            "stages and their order changed")
    for stage in stages:
        require(set(stage.get("outputs", ())) == OUTPUTS[stage["id"]],
                "unknown or missing stage status: " + stage["id"])
        require(bool(stage.get("required")), "missing required stage gates")
    require(stages[0].get("requires") == [], "G0 cannot skip to returns")
    require(stages[1].get("requires") == ["G0"], "D0 order")
    require(stages[2].get("requires") == ["G0", "D0"], "D1 order")
    require(stages[3].get("requires") == ["G0", "D0", "D1"], "D2 order")
    require("separate_authorization" in stages[4].get("requires", ()),
            "confirmation cannot unseal itself")
    require(all(x["outcomes_allowed"] is False for x in stages[:2]),
            "G0/D0 may not read future outcomes")

    infer = data.get("exploratory_inference", {})
    bootstrap = infer.get("moving_block_bootstrap", {})
    require(bootstrap.get("type") == "non_circular"
            and bootstrap.get("n_replicates_min", 0) >= 10000
            and bootstrap.get("main_block_sessions") == 5
            and bootstrap.get("sensitivity_block_sessions") == [3, 10]
            and bootstrap.get("ci_two_sided") == 0.9, "bootstrap contract mismatch")
    require(infer.get("sample_unit") == "eligible_session_including_zero_trades",
            "invalid inference sample unit")
    require(infer.get("n_effective_inferred_from_trade_count") is False,
            "N trades is not independent N")
    require(infer.get("p_values_existing_adaptive_dev_confirmatory") is False,
            "adaptive-DEV p cannot confirm")
    require(infer.get("holm_requires_independent_valid_inference") is True,
            "Holm cannot repair selection")
    require(infer.get("bh_q_if_complete_family_only") is True,
            "BH denominator not preserved")
    require(infer.get("endpoints_non_directional_not_relabelled_as_trades") is True,
            "magnitude cannot be spoofed as trading")
    require(infer.get("min_n_independent_events_for_initial_D1") is None
            and infer.get("yearly_positive_years_required_for_initial_D1") is None,
            "historical gate mistakenly imposed on T-D1")

    # Prospective user-requested research CADENCE gate. This is not Gate1.
    batch = data.get("batch_discovery_gate", {})
    require(batch.get("adopted_on") == "2026-10-12"
            and batch.get("scope") == "PROSPECTIVE_NEW_BATCHES_ONLY"
            and batch.get("policy_type") == "ADDITIVE_RESEARCH_CADENCE_NOT_PROFIT_GATE",
            "batch cadence provenance or scope changed")
    require(batch.get("minimum_diverse_d0_candidates_before_new_D1") == 20
            and batch.get("minimum_CASE_sessions_for_TESTABLE") == 15
            and batch.get("minimum_CONTROL_sessions_for_TESTABLE") == 15
            and batch.get("case_jaccard_near_duplicate_at_or_above") == 0.85,
            "batch minimum or diversity preconditions changed")
    for flag in ("preregister_hypotheses_and_thresholds_before_D0",
                 "freeze_new_D1_endpoints_before_outcomes",
                 "diversified_shortlist_must_exclude_near_duplicates",
                 "all_original_family_members_remain_in_D1_BH",
                 "original_Gate1_Holm_unchanged"):
        require(batch.get(flag) is True, "batch governance missing: " + flag)
    for flag in ("adaptive_DEV_pq_confirmatory","allow_retuning_if_below_20",
                 "holdouts_opened","live_trading_authorized"):
        require(batch.get(flag) is False, "batch governance unsafe: " + flag)

    # 2026-10-12 explicit user request: WHOLE COHORT is the unit.
    funnel = data.get("cohort_funnel_reference", {})
    require(funnel.get("adopted_on")=="2026-10-12"
            and funnel.get("policy_id")=="NQ-COHORT-FUNNEL-V1"
            and funnel.get("transition_unit")=="BATCH_ONLY_NO_INDIVIDUAL_HYPOTHESIS_RUNS",
            "cohort funnel cannot be bypassed")
    for flag in ("D0_to_D1_requires_20_distinct_viable",
                 "D1_measures_all_original_members",
                 "D2_collects_only_economically_executable_survivors",
                 "prior_gates_unchanged"):
        require(funnel.get(flag) is True, "missing cohort funnel gate "+flag)
    require(funnel.get("holdouts_opened") is False,
            "funnel cannot open holdouts")
    require(funnel.get("machine_policy") ==
            "research/nq/NQ_COHORT_FUNNEL_POLICY_2026_10_12.json"
            and funnel.get("cohort_ledger") ==
            "research/nq/NQ_COHORT_FUNNEL_LEDGER_2026_10_12.json"
            and funnel.get("stage_dashboard") ==
            "research/nq/NQ_COHORT_FUNNEL_STATUS_2026_10_12.md",
            "funnel source of truth changed")

    legacy = data.get("legacy_controls", {})
    g = legacy.get("gate1_new_prospective", {})
    frozen = legacy.get("older_frozen_when_applicable", {})
    require((g.get("min_independent_events_exclusive"), g.get("two_sided_ci"),
             g.get("bh_q_max"), g.get("positive_dev_years_min"),
             g.get("dev_years_total")) == (150, 0.9, 0.1, 3, 5),
            "original exploratory Gate1 altered")
    require((frozen.get("min_events"), frozen.get("two_sided_ci"),
             frozen.get("bh_q_max"), frozen.get("positive_dev_years_min"),
             frozen.get("dev_years_total")) == (300, 0.95, 0.05, 4, 5),
            "original strict Gate1 altered")
    require(legacy.get("holm_family_alpha") == "0.05/[k*(k+1)]",
            "Holm budget altered")
    require(legacy.get("no_live_trading_or_funding_from_D0_D1_D2") is True,
            "D gates cannot authorize trading")
    require(REQUIRED_FIELDS.issubset(data.get("required_report_fields", ())),
            "scorecard contract missing required fields")
    gov = data.get("governance", {})
    require(gov.get("preflight_original_required") is True
            and gov.get("freeze_before_outcome") is True
            and gov.get("change_gates_after_outcomes_allowed") is False,
            "freeze governance broken")
    return {"policy_id": data["policy_id"],
            "status": "SAFE_VALIDATED",
            "stages": len(stages),
            "DEV_months": len(EXPECTED_DEV),
            "market_outcomes_loaded": False,
            "holdouts_opened": False}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", type=Path,
                    default=Path("research/nq/NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.json"))
    args = ap.parse_args()
    print(json.dumps(check_policy(json.loads(args.policy.read_text())),
                     sort_keys=True))
