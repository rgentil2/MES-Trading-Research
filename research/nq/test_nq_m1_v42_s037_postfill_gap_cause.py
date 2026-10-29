"""S0.37 isolate count-only post-fill root cause, no market source."""
import unittest
import numpy as np
from research.nq.nq_m1_v31_full_synthetic_lifecycle import artificial_m1
from research.nq.test_nq_m1_v31_full_synthetic_lifecycle import strat
from research.nq import nq_m1_v39_ast_ist_exploratory_order_replay as r

class TestS037PostFillRootCause(unittest.TestCase):
    def test_large_adverse_entry_gap_remains_visible_after_preorder_check(self):
        bars,_=artificial_m1(kind="UP")
        gap=bars.copy()
        # A prospective LONG entry at the next open gaps upward 50 points.
        # PRE_ORDER uses prior close, while POST_FILL must reject new exposure,
        # never pretend the fill did not exist.
        gap[13,:4]+=50.
        strategy=strat(stop_kind="STRUCTURE",target_kind="NONE")
        result=r.replay_one_day(gap,"2021-05-04",strategy)
        self.assertGreater(result["counts"].get(
            "FILLED_RISK_CAP_BREACH",0),0)
        self.assertTrue(any(t["risk_cap_breach"] for t in result["trades"]))
        self.assertTrue(any(t["risk_cap_excess_usd"]>0 for t in result["trades"]))

    def test_postfill_reason_categories_mark_derived_fitness_unusable(self):
        bars,_=artificial_m1(kind="UP")
        gap=bars.copy();gap[13,:4]+=50.
        dates=["2021-05-03","2021-05-04","2021-05-05"]
        tensor=np.stack((gap,bars,bars))
        source={"years_opened":[2020,2021,2022],
                "holdout_2025_opened":False,"holdout_2026_opened":False,
                "complete_rth_sessions":3,
                "partial_sessions_excluded":0,"members_opened":15}
        s=strat(stop_kind="STRUCTURE",target_kind="NONE")
        report=r.evaluate_fixed_sample(dates,tensor,source,[s])
        item=report["candidates"][0]
        self.assertEqual(item["post_fill_unmodelled"],0)
        self.assertGreater(item["executed_risk_cap_breaches"],0)
        self.assertGreater(item["max_model_excess_risk_usd"],0)
        self.assertTrue(report["historical_sample_order_model_complete"])
        self.assertFalse(report["any_AST_provisional_PnL_incomplete"])
        self.assertTrue(report["any_filled_position_violated_risk_cap"])
        self.assertTrue(report["risk_cap_breaches_are_disqualifying_not_deleted"])
        self.assertFalse(report["candidate_fitness_or_winner_selection_permitted"])
        self.assertEqual(report["formal_13_gates_verified"],0)

if __name__=="__main__":unittest.main()
