"""S0.31 genuine search engine protocol tests with GENERATED artificial bars only.

Actual IST source is opened only by separately pinned SHA private workflow.
"""
import tempfile
from pathlib import Path
import unittest
import numpy as np
from research.nq import nq_m1_v36_ist_exploratory_120 as s
from research.nq.nq_m1_v31_full_synthetic_lifecycle import artificial_m1
from research.nq.nq_m1_chrono_discovery import signal

class TestS031Exploratory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,_=s.guard()
        cls.days=["2021-03-10","2021-03-11","2021-03-12"]
        cls.arr=np.stack([artificial_m1(seed=20261029+i,
                                        kind=("UP","DOWN","FLAT")[i])[0]
                          for i in range(3)])
        cls.src={"years_opened":[2020,2021,2022],
                 "holdout_2025_opened":False,"holdout_2026_opened":False,
                 "complete_rth_sessions":3,"partial_sessions_excluded":0,
                 "members_opened":15}

    def test_catalog_complete_and_stratified_small(self):
        self.assertEqual(len(s.choose_rules(self.cfg,120)),120)
        self.assertEqual(len(s.choose_rules(self.cfg,12)),12)
        self.assertEqual(len(set(x["family"] for x in s.choose_rules(self.cfg,12))),5)
        with self.assertRaises(ValueError):
            s.choose_rules(self.cfg,121)

    def test_ist_small_real_runner_on_artificial_price_and_closed_risk(self):
        result=s.run_exploratory(self.days,self.arr,self.src,max_candidates=12)
        self.assertEqual(result["rules_exploratory_evaluated"],12)
        self.assertTrue(result["first_control_search_ran"])
        self.assertEqual(result["original_10000_132_ast_evaluated"],0)
        self.assertEqual(result["days"],3)
        self.assertFalse(result["formal_G0_D0_D1_D2_approved"])
        self.assertFalse(result["shared_account_portfolio_simulated"])
        self.assertEqual(result["economic_13_quality_gates_passed_verified"],0)
        self.assertTrue(all(x["trades"]>=0 and
                            x["closed_trade_max_dd_usd"]>=0
                            for x in result["rules"]))

    def test_ends_no_later_than_1129_and_entry_next_bar(self):
        from research.nq.nq_m1_chrono_discovery import catalog
        rule=next(z for z in catalog(self.cfg)
                  if z["family"]=="CONTINUATION" and z["target_r"] is None)
        trades,_=s.run_day(self.arr[0],rule,self.cfg)
        self.assertTrue(trades)
        for tr in trades:
            self.assertEqual(tr["entry_idx"],tr["signal_idx"]+1)
            self.assertLessEqual(tr["entry_idx"],117)
            self.assertLessEqual(tr["exit_idx"],118)
            self.assertLessEqual(tr["model_initial_risk_usd"],300.)
        self.assertLessEqual(len(trades),2)

    def test_model_stop_before_tp_on_ambiguous_market_entry_minute(self):
        from research.nq.nq_m1_chrono_discovery import catalog
        r=next(x for x in catalog(self.cfg)
               if x["family"]=="CONTINUATION" and x["target_r"]==2.)
        sample=self.arr[0].copy()
        idx=30
        side=signal(sample[:idx+1],idx,r)
        self.assertEqual(side,1)
        op=float(sample[idx+1,0]);c=float(sample[idx+1,3])
        # Single minute traverses both target and stop from entry.
        sample[idx+1]=[op,op+40.,op-40.,c,1000.]
        trade,reason=s._model_trade(sample,idx,side,r,self.cfg)
        self.assertIsNone(reason)
        self.assertEqual(trade["reason"],"SL_STOP_FIRST_AMBIGUOUS")
        self.assertLess(trade["model_net_usd"],0)

    def test_future_mutation_does_not_affect_current_signal(self):
        r=s.choose_rules(self.cfg,120)[48]
        bars=self.arr[1]
        index=40
        old=signal(bars[:index+1],index,r)
        changed=bars.copy()
        changed[index+1:]=np.nan
        new=signal(changed[:index+1],index,r)
        self.assertEqual(old,new)

    def test_reserved_years_rejected(self):
        for yr in (2023,2024,2025,2026):
            d=self.days.copy();d[-1]=f"{yr}-03-12"
            with self.assertRaises(PermissionError):
                s.run_exploratory(d,self.arr,self.src,12)

    def test_sha_guard_rejects_untrusted_archive(self):
        with tempfile.TemporaryDirectory() as td:
            x=Path(td)/"fake.zip";x.write_bytes(b"fake source")
            with self.assertRaises(PermissionError):
                s.audit_real_archive(x,max_candidates=12)

    def test_no_false_very_high_pf_from_zero_loss(self):
        rows=[{"session":"2020-03-10","model_net_usd":5.,
               "ambiguous_stop_first":False,
               "target_exact_touch_unconfirmed":False}]
        rule=s.choose_rules(self.cfg,120)[0]
        result=s.stats_by_rule(rows,["2020-03-10"],rule,{"signals":1})
        self.assertIsNone(result["pf"])
        self.assertEqual(result["gross_loss_usd"],0)

if __name__=="__main__":unittest.main()
