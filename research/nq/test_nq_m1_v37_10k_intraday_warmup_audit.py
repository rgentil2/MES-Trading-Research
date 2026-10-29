"""S0.32 frozen 10K static feasibility; never prices or economic ranks."""
import unittest
from research.nq import nq_m1_v37_10k_intraday_warmup_audit as a

def leaf(name,n,op="RISING",lag=1):
    return {"op":op,"indicator":{"name":name,"parameters":{"period":n}},
            **({"lag_completed_bars":lag} if op in ("RISING","FALLING",
                                                  "ABOVE_LAG","BELOW_LAG",
                                                  "CROSSES_OWN_LAG")
               else {"threshold":0.})}

class TestV37WarmupBounds(unittest.TestCase):
    def test_long_tema_and_t3_cannot_fit_eligible_signal_hours(self):
        self.assertFalse(a._could_be_true(leaf("TEMA",80,lag=1)))
        self.assertFalse(a._could_be_true(leaf("T3",50,lag=1)))
        self.assertTrue(a._could_be_true(leaf("SMA",20,lag=1)))
    def test_3_valued_branch_static_positive_potential_never_eliminates_OR(self):
        yes=leaf("SMA",20)
        no=leaf("TEMA",80)
        self.assertFalse(a._could_be_true({"op":"AND","left":yes,"right":no}))
        self.assertTrue(a._could_be_true({"op":"OR","left":yes,"right":no}))
    def test_unknown_math_never_declared_impossible(self):
        self.assertTrue(a._could_be_true(leaf("Hilbert Phase",240)))
    def test_intraday_risk_includes_lag_at_edge(self):
        self.assertTrue(a._could_be_true(leaf("SMA",115,lag=2)))
        self.assertFalse(a._could_be_true(leaf("SMA",116,lag=2)))
    def test_full_10k_frozen_regenerates_identical_source_sha_without_prices(self):
        r=a.evaluate_frozen_10k()
        self.assertEqual(r["candidate_count"],10000)
        self.assertEqual(len(r["rows"]),10000)
        self.assertEqual(r["candidate_bundle_canonical_sha256"],
                         "b9d2915fc55f86546ef63d74a588df5244d094eeecb4a7c900a4000d47660be9")
        self.assertFalse(r["economic_profit_or_fitness_computed"])
        self.assertEqual(r["strategies_excluded_or_ranked"],0)
        self.assertEqual(sum(r["lower_bound_status_counts"].values()),10000)
        self.assertEqual(r["gate_13_verified_count"],0)

if __name__=="__main__":unittest.main()
