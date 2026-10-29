"""S0.38 adversarial gap trades must be charged, not erased, on manufactured NQ M1."""
import unittest
import numpy as np
from research.nq.nq_m1_v31_full_synthetic_lifecycle import artificial_m1
from research.nq.test_nq_m1_v31_full_synthetic_lifecycle import strat
from research.nq import nq_m1_v39_ast_ist_exploratory_order_replay as r

class TestS038ExecutedGapRiskViolation(unittest.TestCase):
    def test_long_gap_after_preorder_submit_charges_full_loss(self):
        bars,_=artificial_m1(kind="UP")
        gap=bars.copy()
        gap[13,:4]+=50.
        strategy=strat(stop_kind="STRUCTURE",target_kind="NONE")
        a=r.replay_one_day(gap,"2021-05-04",strategy)
        self.assertGreater(a["counts"].get("FILLED_RISK_CAP_BREACH",0),0)
        invalid=[x for x in a["trades"] if x["risk_cap_breach"]]
        self.assertGreater(len(invalid),0)
        self.assertTrue(all(x["risk_cap_excess_usd"]>0 for x in invalid))
        self.assertTrue(all(x["initial_model_risk_usd"]>300 for x in invalid))
        self.assertLess(a["net_usd"],0)
        self.assertEqual(a["net_usd"],round(sum(
            x["exploratory_net_usd"] for x in a["trades"]),2))

    def test_non_portfolio_results_always_flag_risk_violation_ineligible(self):
        bars,_=artificial_m1(kind="UP")
        gap=bars.copy();gap[13,:4]+=50.
        days=["2021-05-03","2021-05-04","2021-05-05"]
        b=np.stack([gap,bars,bars])
        meta={"years_opened":[2020,2021,2022],
              "holdout_2025_opened":False,"holdout_2026_opened":False,
              "complete_rth_sessions":3,
              "partial_sessions_excluded":0,"members_opened":15}
        x=r.evaluate_fixed_sample(days,b,meta,
            [strat(stop_kind="STRUCTURE",target_kind="NONE")])
        self.assertGreater(x["counts"]["FILLED_RISK_CAP_BREACH"],0)
        self.assertEqual(x["counts"]["post_fill_unmodelled"],0)
        self.assertTrue(x["risk_cap_breaches_are_disqualifying_not_deleted"])
        self.assertTrue(x["any_filled_position_violated_risk_cap"])
        self.assertFalse(x["candidate_fitness_or_winner_selection_permitted"])
        self.assertFalse(x["portfolio_jointly_simulated"])
        self.assertEqual(x["formal_13_gates_verified"],0)

if __name__=="__main__":unittest.main()
