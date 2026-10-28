"""NQ S0.10 artificial trade outcomes ONLY, never actual strategy results."""
import math
import unittest

from research.nq import nq_m1_v22_synthetic_d1_d2_checks as d


def sample(values,year=2021):
    return [{"date":f"{year}-04-06","contract":"NQ","net_usd":v} for v in values]


class TestSyntheticD1D2(unittest.TestCase):
    def test_reference_pnl_pf_dd_exact(self):
        m=d.trade_metrics(sample([100,-50,60,-40]))
        self.assertEqual(m["trades"],4)
        self.assertAlmostEqual(m["net_usd"],70.)
        self.assertAlmostEqual(m["profit_factor"],160./90.)
        self.assertAlmostEqual(m["max_closed_trade_dd_usd"],50.)
        self.assertAlmostEqual(m["expectancy_usd"],17.5)
        self.assertFalse(m["legacy_cohort_g0_d2_parity_certified"])

    def test_sample_adequacy_scaled_from_original_five_year_criterion(self):
        self.assertEqual(d.MIN_TRADES_2020_2024,150)
        self.assertEqual(d.MIN_TRADES,90)
        self.assertEqual(d.MONTHS,36)
        self.assertEqual(d.MIN_TRADES_PER_MONTH,5.)

    def test_empty_or_zero_loss_has_no_fake_infinite_pf(self):
        a=d.trade_metrics([])
        b=d.trade_metrics(sample([100,50]))
        self.assertIsNone(a["profit_factor"])
        self.assertIsNone(b["profit_factor"])
        self.assertIsNone(a["expectancy_usd"])

    def test_premature_ranking_is_explicitly_not_formal(self):
        out=d.sample_screen(sample([100,-50,60,-40]))
        self.assertFalse(out["synthetic_rule_consistency"])
        self.assertIn("LOW_SAMPLE",out["reasons"])
        self.assertIn("LOW_FREQUENCY_ALL_MONTHS",out["reasons"])
        self.assertEqual(out["preliminary_screen"],"NO_CANDIDATE_EVALUATION")

    def test_cost_stress_1_5_and_extra_fees(self):
        x=d.cost_stress(sample([100.,-20.]),1.5,10.)
        self.assertAlmostEqual(x["baseline_round_trip_cost_usd"],24.68)
        self.assertAlmostEqual(x["added_cost_per_trade_usd"],22.34)
        self.assertAlmostEqual(x["net_stressed_usd"],35.32)
        self.assertTrue(x["not_formal_d2"])

    def test_moving_block_bootstrap_reproducible_and_sealed(self):
        trades=sample([80,-20,40,-45,70,-30,10,-15,60,-40]*3)
        a=d.block_bootstrap(trades,seed=19,reps=100,block_size=4)
        b=d.block_bootstrap(trades,seed=19,reps=100,block_size=4)
        self.assertEqual(a,b)
        self.assertGreaterEqual(a["bootstrap_dd_p95"],0)
        self.assertEqual(a["holdouts"],"SEALED")
        self.assertTrue(a["not_formal_d2"])

    def test_no_mnq_and_no_isv_or_holdouts_can_enter(self):
        with self.assertRaises(PermissionError):
            d.trade_metrics([{"date":"2020-01-06","contract":"MNQ","net_usd":100}])
        for year in (2023,2024,2025,2026):
            with self.assertRaises(PermissionError):
                d.trade_metrics(sample([20],year))

    def test_nonfinite_and_unsorted_trades_fail_closed(self):
        with self.assertRaises(ValueError):
            d.trade_metrics(sample([math.inf]))
        x=[{"date":"2022-12-20","contract":"NQ","net_usd":10},
           {"date":"2022-01-03","contract":"NQ","net_usd":10}]
        with self.assertRaises(ValueError):
            d.trade_metrics(x)

    def test_resampling_guard_and_negative_cost_shocks(self):
        with self.assertRaises(ValueError):
            d.block_bootstrap(sample([50,-20,50]),reps=100,block_size=5)
        with self.assertRaises(ValueError):
            d.block_bootstrap(sample([1]*30),reps=20)
        with self.assertRaises(ValueError):
            d.cost_stress(sample([100]),multiplier=.8)
        with self.assertRaises(ValueError):
            d.cost_stress(sample([100]),extra_rt_usd=-10.)


if __name__=="__main__":
    unittest.main()
