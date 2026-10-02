import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import research_governance as search


class SearchControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "research").mkdir()
        (self.root / "tools").mkdir()
        self.doc = "research/B15_DEMO_PRE_REGISTRATION.md"
        (self.root / self.doc).write_text("## H082 — A\n## H083 — B\n")
        self.code = "tools/run_mes_b15_demo.py"
        (self.root / self.code).write_text("# fixed definition\n")
        self.family = {"id": "FLOW-F01", "index": 1, "question": "one scientific question",
                       "origin_units": ["H064"], "data_role": "REUSED_DEVELOPMENT",
                       "members": [{"id": k, "preregistration_path": self.doc,
                                    "definition": "fixed variant " + k, "alternative": "positive",
                                    "endpoint": "next-open +30m", "research_instrument": "MES", "analysis_kind": "DIRECTIONAL", "execution_instrument": None} for k in ["H082", "H083"]],
                       "definition_files": [self.doc, self.code],
                       "result_artifacts": ["results/development/MES_B15_DEMO_RESULTS.json"],
                       "independent_inference_justification": None}
        self.ledger = {"schema_version": 1, "historical_baseline_commit": "known",
                       "recording_limit": "recorded only", "historical_file_snapshots": [],
                       "historical_entrypoints": [], "historical_experiments": [], "historical_hypotheses": [], "planned_es_units": [], "baseline_definition_paths": [],
                       "future_families": [self.family], "version_changes": []}
        self.write_controls()

    def tearDown(self):
        self.temp.cleanup()

    def write_controls(self):
        (self.root / search.LEDGER).write_text(json.dumps(self.ledger))
        p = self.root / search.FREEZES
        if not p.exists():
            p.write_text(json.dumps({"schema_version": 1, "families": {}}))

    def test_holm_known_reference_and_monotonicity(self):
        actual = search.holm_adjust({"a": .01, "b": .03, "c": .04, "d": .2})
        self.assertEqual(actual, {"a": .04, "b": .09, "c": .09, "d": .2})

    def test_invalid_pvalues_rejected(self):
        for p in [math.nan, math.inf, -.1, 1.1, True, None]:
            with self.assertRaises(ValueError):
                search.holm_adjust({"a": p})

    def test_budget_sum_bounded_without_family_reset(self):
        self.assertAlmostEqual(search.alpha_for_index(1), .025)
        self.assertAlmostEqual(search.alpha_for_index(2), .05 / 6)
        self.assertAlmostEqual(sum(search.alpha_for_index(k) for k in range(1, 10001)), .05 * (1 - 1 / 10001))

    def test_whole_family_missing_member_cannot_pass(self):
        with self.assertRaises(ValueError):
            search.evaluate_metrics(self.family, {"H082": {"p_value_two_sided": .001, "effect": 10}})

    def test_non_estimable_member_counts_in_denominator(self):
        actual = search.evaluate_metrics(self.family, {
            "H082": {"p_value_two_sided": .02, "effect": 10},
            "H083": {"status": "NOT_ESTIMABLE"}})
        self.assertEqual(actual["holm_adjusted_p"]["H082"], .04)
        self.assertEqual(actual["full_member_count"], 2)
        self.assertEqual(actual["status"], "NOT_SUPPORTED_EXPLORATORY")

    def test_small_p_on_reused_data_remains_exploratory(self):
        actual = search.evaluate_metrics(self.family, {
            k: {"p_value_two_sided": .001, "effect": 20} for k in ["H082", "H083"]})
        self.assertEqual(actual["status"], "PROMISING_EXPLORATORY")
        self.assertFalse(actual["strategy_authorized"])

    def test_negative_effect_cannot_support_preregistered_direction(self):
        actual = search.evaluate_metrics(self.family, {
            k: {"p_value_two_sided": .001, "effect": -20} for k in ["H082", "H083"]})
        self.assertEqual(actual["supported_members"], [])

    def test_unfrozen_family_blocked_then_frozen_preflight_passes(self):
        with self.assertRaises(ValueError):
            search.preflight_family(self.root, self.family["id"])
        search.freeze_family(self.root, self.family["id"])
        self.assertEqual(search.preflight_family(self.root, self.family["id"]), self.family)
        self.assertEqual(search.build_registry(self.root)["summary"]["future_families"], 1)

    def test_definition_change_after_freeze_blocked(self):
        search.freeze_family(self.root, self.family["id"])
        (self.root / self.code).write_text("# changed threshold\n")
        with self.assertRaises(ValueError):
            search.preflight_family(self.root, self.family["id"])

    def test_member_or_alpha_change_after_freeze_blocked(self):
        search.freeze_family(self.root, self.family["id"])
        self.family["members"].pop()
        self.write_controls()
        with self.assertRaises(ValueError):
            search.preflight_family(self.root, self.family["id"])

    def test_cannot_freeze_after_outcome_report_exists(self):
        p = self.root / self.family["result_artifacts"][0]
        p.parent.mkdir(parents=True)
        p.write_text("{}")
        with self.assertRaises(ValueError):
            search.freeze_family(self.root, self.family["id"])

    def test_spent_family_cannot_be_deleted_or_recycled(self):
        search.freeze_family(self.root, self.family["id"])
        with self.assertRaises(ValueError):
            search.freeze_family(self.root, self.family["id"])
        self.ledger["future_families"] = []
        self.write_controls()
        with self.assertRaises(ValueError):
            search.build_registry(self.root)

    def test_new_hypothesis_outside_registered_family_is_rejected(self):
        search.freeze_family(self.root, self.family["id"])
        (self.root / "research/B16_DEMO_PRE_REGISTRATION.md").write_text("## H084 — unregistered\n")
        with self.assertRaises(ValueError):
            search.build_registry(self.root)

    def test_holdout_and_escape_paths_refused_before_read(self):
        for path in ["artifacts/holdout/result.json", "artifacts/research/BTC_B31_OOS.json",
                     "artifacts/research/result_2026.json", "artifacts/research/../../private.json"]:
            with self.assertRaises(ValueError):
                search.report_path(self.root, path)

    def test_report_years_and_stages_are_checked(self):
        p = self.root / self.family["result_artifacts"][0]
        p.parent.mkdir(parents=True)
        report = {"stage": "DEVELOPMENT", "loaded_years": [2020, 2025],
                  "holdout_2025_loaded": False, "holdout_2026_loaded": False}
        p.write_text(json.dumps(report))
        with self.assertRaises(ValueError):
            search.read_development_report(self.root, self.family["result_artifacts"][0])

    def test_independent_adapter_is_not_authorized_by_registry(self):
        self.family["data_role"] = "INDEPENDENT_EVALUATION"
        self.family["independent_inference_justification"] = "separate untouched evaluation and valid inference"
        self.write_controls()
        search.freeze_family(self.root, self.family["id"])
        with self.assertRaises(ValueError):
            search.evaluate_family(self.root, self.family["id"])

    def test_evaluate_multiblock_family_requires_every_declared_artifact(self):
        search.freeze_family(self.root, self.family["id"])
        p = self.root / self.family["result_artifacts"][0]
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({"stage": "DEVELOPMENT", "loaded_years": [2020, 2021, 2022, 2023, 2024],
                                "holdout_2025_loaded": False, "holdout_2026_loaded": False,
                                "family_metrics": {k: {"p_value_two_sided": .001, "effect": 10}
                                                   for k in ["H082", "H083"]}}))
        actual = search.evaluate_family(self.root, self.family["id"])
        self.assertEqual(actual["full_member_count"], 2)
        self.assertEqual(actual["status"], "PROMISING_EXPLORATORY")
        registry = search.build_registry(self.root)
        self.assertEqual(registry["future_family_evaluations"][0], actual)
        partial = json.loads(p.read_text())
        del partial["family_metrics"]["H083"]
        p.write_text(json.dumps(partial))
        with self.assertRaises(ValueError):
            search.build_registry(self.root)

    def test_declarations_do_not_count_context_references(self):
        text = "Motivated by H064.\n## H082 — variant\n- **H083:** second variant\n"
        self.assertEqual(set(search.declared_units(text)), {"H082", "H083"})

    def test_cross_commit_budget_cannot_be_deleted_or_rewritten(self):
        search.freeze_family(self.root, self.family["id"])
        ledger, locks = search.load_controls(self.root)
        for replacement in [{}, {self.family["id"]: {"alpha": .05}}]:
            changed = {"schema_version": 1, "families": replacement}
            with self.assertRaises(ValueError):
                search.validate_control_history(ledger, locks, ledger, changed)

    def test_cross_commit_historical_baseline_cannot_be_replaced(self):
        ledger, locks = search.load_controls(self.root)
        changed = copy.deepcopy(ledger)
        changed["historical_baseline_commit"] = "new baseline to hide earlier trials"
        with self.assertRaises(ValueError):
            search.validate_control_history(ledger, locks, changed, locks)

    def test_cross_commit_version_history_must_be_append_only(self):
        ledger, locks = search.load_controls(self.root)
        ledger["version_changes"] = [{"path": self.code, "reason": "known change"}]
        changed = copy.deepcopy(ledger)
        changed["version_changes"] = []
        with self.assertRaises(ValueError):
            search.validate_control_history(ledger, locks, changed, locks)
        changed["version_changes"] = ledger["version_changes"] + [{"reason": "next recorded change"}]
        search.validate_control_history(ledger, locks, changed, locks)

    def test_git_history_bootstrap_and_joint_reset_are_checked(self):
        def git(*args):
            return subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                                   *args], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()
        git("init")
        git("add", self.doc)
        git("commit", "-m", "Before controls")
        search.check_history_ref(self.root, git("rev-parse", "HEAD"))
        search.freeze_family(self.root, self.family["id"])
        git("add", "research", "tools")
        git("commit", "-m", "Frozen controls")
        baseline = git("rev-parse", "HEAD")
        search.check_history_ref(self.root, baseline)
        self.ledger["future_families"] = []
        self.write_controls()
        (self.root / search.FREEZES).write_text(json.dumps({"schema_version": 1, "families": {}}))
        with self.assertRaises(ValueError):
            search.check_history_ref(self.root, baseline)

    def test_strategy_instrument_costs_cannot_be_copied_silently(self):
        member = self.family['members'][0]
        member.update(analysis_kind='STRATEGY', research_instrument='ES', execution_instrument='ES',
                      costs={'point_value_usd':5, 'commission_round_trip_usd':1.88, 'slippage_round_trip_usd':2.5})
        with self.assertRaises(ValueError):
            search.validate_family(self.root, self.family)
        member['costs']['point_value_usd'] = 50
        search.validate_family(self.root, self.family)
        member['execution_instrument'] = 'MES'
        member['costs']['point_value_usd'] = 5
        with self.assertRaises(ValueError):
            search.validate_family(self.root, self.family)
        member['transfer_validation_plan'] = 'Freeze and evaluate ES signal against MES execution prices and costs separately'
        search.validate_family(self.root, self.family)

    def test_two_instruments_share_one_family_denominator(self):
        self.family['members'][1]['research_instrument'] = 'ES'
        result = search.evaluate_metrics(self.family, {
            'H082': {'p_value_two_sided':.02, 'effect':1},
            'H083': {'p_value_two_sided':.03, 'effect':1}})
        self.assertEqual(result['holm_adjusted_p']['H082'], .04)
        self.assertEqual(result['alpha_allocation'], .025)
        self.assertEqual(result['status'], 'NOT_SUPPORTED_EXPLORATORY')


if __name__ == "__main__":
    unittest.main()
