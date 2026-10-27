"""V2 S0 tests: synthetic only, no archive, no market outcomes, no holdouts."""
import copy
import random
import unittest

from research.nq import nq_m1_v2_generator as g
from research.nq import nq_m1_v2_pipeline as p


class TestNQM1V2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = g.read_registry()

    def test_132_registered_not_132_certified(self):
        r = self.registry
        self.assertEqual((r["total_blocks"], r["indicator_count"], r["pattern_count"]), (132, 120, 12))
        self.assertEqual(len(r["entries"]), 132)
        self.assertTrue(all(x["status"] == "REGISTERED_NOT_YET_CERTIFIED" for x in r["entries"]))
        self.assertEqual(len(set(x["name"] for x in r["entries"])), 132)
        self.assertEqual(len(r["groups"]), 11)

    def test_parameter_sampling_numeric_boundaries_and_macd_fast_less_slow(self):
        rng = random.Random(27)
        for entry in self.registry["entries"]:
            for _ in range(15):
                sampled = g.sample_parameters(rng, entry["parameters"])
                for key, values in entry["parameters"].items():
                    if key == "constraint":
                        continue
                    value = sampled[key]
                    if len(values) == 2 and all(type(x) in (int, float) for x in values):
                        self.assertGreaterEqual(value, values[0])
                        self.assertLessEqual(value, values[1])
                    else:
                        self.assertIn(value, values)
                if entry["parameters"].get("constraint"):
                    self.assertLess(sampled["fast_period"], sampled["slow_period"])

    def test_catalog_only_generation_is_repeatable_and_diverse(self):
        a = g.generate_batch(80, seed=2007, registry=self.registry)
        b = g.generate_batch(80, seed=2007, registry=self.registry)
        self.assertEqual(a, b)
        self.assertEqual(len(set(g.fingerprint(x) for x in a)), 80)
        self.assertTrue(any(x["lineage"]["method"] == "RANDOM" for x in a))
        self.assertTrue(any(x["lineage"]["method"] != "RANDOM" for x in a))
        self.assertTrue(all(x["exit"]["stop_loss_required"] for x in a))
        self.assertTrue(all(x["exit"]["flat_at_et"] == "11:29" for x in a))
        for x in a:
            p.validate_candidate_envelope(x)

    def test_immutable_fingerprint_catches_mutation(self):
        item = g.generate_batch(1, registry=self.registry)[0]
        altered = copy.deepcopy(item)
        altered["entry_order"]["kind"] = "FAKE_ORDER"
        with self.assertRaises(ValueError):
            p.validate_candidate_envelope(altered)

    def test_sealed_dates_and_internal_validation_need_freeze(self):
        with self.assertRaises(PermissionError):
            g.permitted_years_for_generation((2020, 2021, 2022, 2025))
        for stage, years in (("IST", (2020, 2021, 2022, 2025)), ("ISV1", (2024,)), ("HOLDOUT", (2025,))):
            with self.assertRaises(PermissionError):
                p.stage_contract(stage, years, None)
        with self.assertRaises(PermissionError):
            p.stage_contract("ISV1", (2023,), None)
        with self.assertRaises(PermissionError):
            g.pareto_front_ist_only([], "ISV2")
        self.assertEqual(p.stage_contract("IST", (2020, 2021, 2022), None)["H2025_H2026"], "SEALED")

    def test_legacy_cohort_gates_fail_closed_not_fake_pass(self):
        statuses = p.adapter_state()
        self.assertEqual(set(statuses), {"G0", "D0", "D1", "D2"})
        self.assertTrue(all(x["state"] == "PENDING_ADAPTER" for x in statuses.values()))
        self.assertTrue(all(x["legacy_sources"] for x in statuses.values()))

    def test_pareto_objective_not_net_only(self):
        rows = [
            {"id": "A", "net": 100, "profit_factor": 1.4, "drawdown": 500, "trades": 50},
            {"id": "B", "net": 110, "profit_factor": 1.3, "drawdown": 600, "trades": 60},
            {"id": "C", "net": 80, "profit_factor": 1.2, "drawdown": 700, "trades": 40},
        ]
        self.assertEqual(set(g.pareto_front_ist_only(rows, "IST")), {"A", "B"})

    def test_structural_portfolio_reproducible(self):
        ids = ["S1", "S2", "S3", "S4", "S5"]
        a = p.portfolio_candidates(ids, 6, seed=123)
        self.assertEqual(a, p.portfolio_candidates(ids, 6, seed=123))
        self.assertTrue(all(2 <= len(x["members"]) <= 5 for x in a))
        self.assertEqual(len(set(tuple(x["members"]) for x in a)), 6)
        self.assertTrue(all(x["status"] == "STRUCTURAL_NOT_BACKTESTED" for x in a))

    def test_shadow_router_same_timestamp_and_daily_pause(self):
        proposals = [
            {"date": "2021-06-15", "strategy_id": "S2", "signal_idx": 20, "entry_idx": 21, "exit_idx": 25,
             "initial_risk_usd": 200., "net_usd": +200.},
            {"date": "2021-06-15", "strategy_id": "S1", "signal_idx": 20, "entry_idx": 21, "exit_idx": 29,
             "initial_risk_usd": 200., "net_usd": -650.},
            {"date": "2021-06-15", "strategy_id": "S2", "signal_idx": 30, "entry_idx": 31, "exit_idx": 40,
             "initial_risk_usd": 200., "net_usd": +500.},
        ]
        out = p.simulate_shadow_router(proposals, ["S1", "S2"])
        self.assertEqual(out["entries"], 1)
        self.assertEqual(out["net_usd"], -650.)
        self.assertEqual(out["rejected"].get("SAME_TIMESTAMP_LOWER_PRIORITY"), 1)
        self.assertEqual(out["rejected"].get("CLOSED_DAILY_PAUSE"), 1)

    def test_nq_router_can_skip_risky_priority_candidate_without_future_information(self):
        rejected = {"date": "2021-06-15", "strategy_id": "NQ_HIGH",
                    "signal_idx": 20, "entry_idx": 21, "exit_idx": 25,
                    "initial_risk_usd": 400., "net_usd": +999999.}
        accepted = {"date": "2021-06-15", "strategy_id": "NQ_LOW",
                    "signal_idx": 20, "entry_idx": 21, "exit_idx": 25,
                    "initial_risk_usd": 200., "net_usd": -50.}
        out = p.simulate_shadow_router([rejected,accepted],["NQ_HIGH","NQ_LOW"])
        self.assertEqual(out["entries"],1)
        self.assertEqual(out["accepted"][0]["strategy_id"],"NQ_LOW")
        self.assertEqual(out["rejected"].get("RISK_CAP"),1)
        self.assertEqual(out["net_usd"],-50.)
        self.assertNotIn("SAME_TIMESTAMP_LOWER_PRIORITY",out["rejected"])

    def test_shadow_router_never_opens_holdout(self):
        future = [{"date": "2025-01-08", "strategy_id": "S1", "signal_idx": 20, "entry_idx": 21,
                   "exit_idx": 25, "initial_risk_usd": 100., "net_usd": 5.}]
        with self.assertRaises(PermissionError):
            p.simulate_shadow_router(future, ["S1"])

    def test_exploratory_metrics_not_broker_drawdown(self):
        m = p.exploratory_trade_metrics([120., -200., 50., -10.])
        self.assertEqual(m["n"], 4)
        self.assertEqual(m["closed_trade_drawdown"], 200.)
        self.assertIn("NOT_FLOATING_MLL", m["gate"])


if __name__ == "__main__":
    unittest.main()
