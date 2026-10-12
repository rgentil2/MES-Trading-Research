"""Synthetic policy regression tests; NEVER open market observations."""
import copy
import json
import unittest
from pathlib import Path
from validate_nq_discovery_staged_gates import check_policy

FILE = Path(__file__).resolve().parents[1] / "research/nq/NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.json"

class DiscoveryPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(FILE.read_text())

    def test_authorized_v1_structure(self):
        x = check_policy(copy.deepcopy(self.base))
        self.assertEqual(x["status"], "SAFE_VALIDATED")
        self.assertEqual(x["DEV_months"], 7)
        self.assertFalse(x["market_outcomes_loaded"])

    def test_never_open_holdout(self):
        for key, val in [("holdouts_opened", True), ("new_market_history_acquisition", True),
                         ("new_five_second_signals", True)]:
            x = copy.deepcopy(self.base)
            x["authorized_data"][key] = val
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_policy(x)

    def test_legacy_alphas_cannot_be_relaxed(self):
        x = copy.deepcopy(self.base)
        x["legacy_controls"]["gate1_new_prospective"]["bh_q_max"] = 0.2
        with self.assertRaises(ValueError):
            check_policy(x)
        x = copy.deepcopy(self.base)
        x["legacy_controls"]["holm_family_alpha"] = "0.05"
        with self.assertRaises(ValueError):
            check_policy(x)

    def test_d0_never_reads_outcomes(self):
        x = copy.deepcopy(self.base)
        x["stages"][1]["outcomes_allowed"] = True
        with self.assertRaises(ValueError):
            check_policy(x)

    def test_no_invented_independence(self):
        x = copy.deepcopy(self.base)
        x["exploratory_inference"]["n_effective_inferred_from_trade_count"] = True
        with self.assertRaises(ValueError):
            check_policy(x)

    def test_robust_bootstrap_not_silently_edited(self):
        x = copy.deepcopy(self.base)
        x["exploratory_inference"]["moving_block_bootstrap"]["main_block_sessions"] = 1
        with self.assertRaises(ValueError):
            check_policy(x)

    def test_funding_needs_full_gate(self):
        x = copy.deepcopy(self.base)
        x["legacy_controls"]["no_live_trading_or_funding_from_D0_D1_D2"] = False
        with self.assertRaises(ValueError):
            check_policy(x)

    def test_twenty_diverse_candidates_required_before_new_d1(self):
        x = copy.deepcopy(self.base)
        x["batch_discovery_gate"]["minimum_diverse_d0_candidates_before_new_D1"] = 10
        with self.assertRaises(ValueError):
            check_policy(x)

    def test_no_relaxed_batch_rules_after_d0_count(self):
        for key, value in [
            ("allow_retuning_if_below_20", True),
            ("adaptive_DEV_pq_confirmatory", True),
            ("all_original_family_members_remain_in_D1_BH", False),
            ("holdouts_opened", True),
        ]:
            x = copy.deepcopy(self.base)
            x["batch_discovery_gate"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_policy(x)

    def test_disallow_individual_hypothesis_stage_shortcut(self):
        x = copy.deepcopy(self.base)
        x["cohort_funnel_reference"]["transition_unit"] = "INDIVIDUAL_HYPOTHESIS"
        with self.assertRaises(ValueError):
            check_policy(x)

    def test_no_unbacked_D1_or_D2_advancement(self):
        for name in ("D0_to_D1_requires_20_distinct_viable",
                     "D1_measures_all_original_members",
                     "D2_collects_only_economically_executable_survivors"):
            x = copy.deepcopy(self.base)
            x["cohort_funnel_reference"][name] = False
            with self.subTest(gate=name), self.assertRaises(ValueError):
                check_policy(x)

    def test_no_2026_reserved_month_in_dev(self):
        x = copy.deepcopy(self.base)
        x["authorized_data"]["dev_T_months"].append("2026-08")
        with self.assertRaises(ValueError):
            check_policy(x)

if __name__ == "__main__":
    unittest.main()
