"""S0.34 complete-order exploratory model technical tests; ALL GENERATED OHLC."""
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
import copy
import numpy as np
from research.nq import nq_m1_v39_ast_ist_exploratory_order_replay as m
from research.nq.nq_m1_v31_full_synthetic_lifecycle import artificial_m1,simulate_synthetic_day
from research.nq.test_nq_m1_v31_full_synthetic_lifecycle import strat

def mock():
    days=["2021-05-03","2021-05-04","2021-05-05"]
    bars=np.stack([artificial_m1(seed=20261029+i,kind="UP")[0] for i in range(3)])
    meta={"years_opened":[2020,2021,2022],
          "holdout_2025_opened":False,"holdout_2026_opened":False,
          "complete_rth_sessions":3,"partial_sessions_excluded":0,
          "members_opened":15}
    return days,bars,meta

class TestV39HistoricalASTPreliminaryReplay(unittest.TestCase):
    def test_generated_ascending_market_exits_and_flat_policy(self):
        days,bars,_=mock()
        result=m.replay_one_day(bars[1],days[1],strat())
        self.assertGreaterEqual(len(result["trades"]),1)
        for t in result["trades"]:
            self.assertGreater(t["entry_idx"],t["signal_idx"])
            self.assertLessEqual(t["entry_idx"],117)
            self.assertLessEqual(t["exit_idx"],118)
            self.assertLessEqual(t["initial_model_risk_usd"],300)
        self.assertAlmostEqual(result["net_usd"],
            sum(t["exploratory_net_usd"] for t in result["trades"]))

    def test_same_math_as_synthetic_lifecycle_on_fixture_with_no_prior(self):
        bars,fixture=artificial_m1(seed=20261028,kind="UP")
        s=strat(target_kind="R_MULTIPLE")
        a=m.replay_one_day(bars,"2021-05-04",s)
        b=simulate_synthetic_day(s,fixture,day="2021-05-04")
        self.assertEqual(len(a["trades"]),len(b["synthetic_trades"]))
        self.assertAlmostEqual(a["net_usd"],b["synthetic_closed_net_usd"])
        for x,y in zip(a["trades"],b["synthetic_trades"]):
            self.assertEqual(x["entry_idx"],y["entry_idx"])
            self.assertEqual(x["exit_idx"],y["exit_idx"])
            self.assertEqual(x["exit_reason"],y["exit_reason"])
            self.assertEqual(x["entry_price"],y["entry_price"])

    def test_three_day_fixed_exploratory_summary_not_portfolio(self):
        days,bars,meta=mock()
        s=strat()
        report=m.evaluate_fixed_sample(days,bars,meta,[s])
        self.assertEqual(report["candidate_count_exploratory"],1)
        self.assertEqual(report["sessions_sampled"],3)
        self.assertEqual(report["candidates"][0]["sampled_days"],3)
        self.assertFalse(report["portfolio_jointly_simulated"])
        self.assertFalse(report["formal_G0_D0_D1_D2_approved"])
        self.assertFalse(report["sample_sufficient_for_strategy_selection"])
        self.assertFalse(report["all_10k_backtested"])

    def test_limited_scope_and_duplicate_strategy_refused(self):
        days,bars,meta=mock()
        with self.assertRaises(ValueError):
            m.evaluate_fixed_sample(days,bars,meta,[strat(),strat()])
        with self.assertRaises(ValueError):
            m.evaluate_fixed_sample(days,bars,meta,[strat()],chosen=[1,1,2])
        for yr in ("2023","2024","2025","2026"):
            bad=days.copy();bad[-1]=yr+"-05-05"
            with self.subTest(yr=yr),self.assertRaises(PermissionError):
                m.evaluate_fixed_sample(bad,bars,meta,[strat()])

    def test_original_zip_sha_enforced_prior_to_source_read(self):
        with TemporaryDirectory() as t:
            p=Path(t)/"untrusted.zip";p.write_bytes(b"fake")
            with self.assertRaises(PermissionError):
                m.real_archive_pilot(p)

    def test_no_trade_is_inconclusive_not_infinite_pf(self):
        days,bars,meta=mock()
        s=strat(stop_kind="FIXED_POINTS")
        s["exit"]["stop_loss_required"]["points"]=30
        from research.nq.nq_m1_v26_structural_generator import sha
        s["id"]="NQ26_"+sha(s)[:16]
        x=m.evaluate_fixed_sample(days,bars,meta,[s])["candidates"][0]
        self.assertEqual(x["model_trades"],0)
        self.assertIsNone(x["model_pf"])
        self.assertEqual(x["post_fill_unmodelled"],0)
        self.assertGreater(x["pre_order_rejected"],0)
        self.assertTrue(x["research_only_insufficient_three_day_sample"])

    def test_unavailable_causal_target_is_rejected_before_any_order(self):
        dates,bars,meta=mock()
        s=strat(target_kind="PIVOT")
        day=m.replay_one_day(bars[0],dates[0],s)
        self.assertEqual(day["trades"],[])
        self.assertGreater(day["counts"].get(
            "PRE_ORDER_TARGET_LEVEL_REFERENCE_NEEDS_FORMAL_DEFINITION",0),0)
        self.assertEqual(sum(v for k,v in day["counts"].items()
                             if k.startswith("POST_FILL_")),0)

    def test_pretrade_risk_uses_completed_close_not_future_open(self):
        dates,bars,meta=mock()
        s=strat()
        s["exit"]["stop_loss_required"]["points"]=40.
        from research.nq.nq_m1_v26_structural_generator import sha
        s["id"]="NQ26_"+sha(s)[:16]
        baseline=m.replay_one_day(bars[0],dates[0],s)
        changed=bars[0].copy()
        changed[13:,:4]+=1000.
        future_changed=m.replay_one_day(changed,dates[0],s)
        self.assertEqual(baseline["trades"],[])
        self.assertEqual(future_changed["trades"],[])
        self.assertGreater(baseline["counts"].get("PRE_ORDER_RISK_CAP",0),0)
        self.assertGreater(future_changed["counts"].get("PRE_ORDER_RISK_CAP",0),0)

if __name__=="__main__":unittest.main()
