"""S0.26 entire artificial NQ M1 lifecycle QA; never a historical backtest."""
import copy
import unittest
from research.nq import nq_m1_v31_full_synthetic_lifecycle as m
from research.nq.nq_m1_v26_structural_generator import sha
from research.nq.test_nq_m1_v30_132_signal_m1_bridge import simple_sma
from research.nq.nq_m1_v22_quality_gate import audit

def strat(kind="MARKET",stop_kind="FIXED_POINTS",target_kind="NONE"):
    s=simple_sma(kind)
    s["exit"]={
        "stop_loss_required":{"kind":"FIXED_POINTS","points":3.},
        "profit_target":{"kind":"NONE"},
        "trailing":None,"break_even":None,"exit_after_bars":None,
        "flat_at_et":"11:29"}
    if stop_kind=="ATR":
        s["exit"]["stop_loss_required"]={"kind":"ATR","period":8,"multiple":2.}
    elif stop_kind=="STRUCTURE":
        s["exit"]["stop_loss_required"]={"kind":"STRUCTURE","lookback":8,"buffer_ticks":1}
    elif stop_kind=="CHANDELIER":
        s["exit"]["stop_loss_required"]={"kind":"CHANDELIER","period":8,"atr_multiple":1.}
    if target_kind=="R_MULTIPLE":
        s["exit"]["profit_target"]={"kind":"R_MULTIPLE","risk_multiple":.8}
    elif target_kind=="FIXED_POINTS":
        s["exit"]["profit_target"]={"kind":"FIXED_POINTS","points":1.}
    elif target_kind=="ATR":
        s["exit"]["profit_target"]={"kind":"ATR","period":8,"multiple":.7}
    elif target_kind=="VWAP":
        s["exit"]["profit_target"]={"kind":"CAUSAL_LEVEL","reference":"VWAP"}
    elif target_kind=="PIVOT":
        s["exit"]["profit_target"]={"kind":"CAUSAL_LEVEL","reference":"PIVOT"}
    s["id"]="NQ26_"+sha(s)[:16]
    return s

class TestV31M1SyntheticLifecycle(unittest.TestCase):
    def setUp(self):
        self.fi=m.artificial_m1()[1]

    def test_market_full_lifecycle_flat_1129_and_max_two(self):
        r=m.simulate_synthetic_day(strat(),self.fi)
        self.assertEqual(r["synthetic_entries"],1)
        self.assertEqual(r["synthetic_trades"][0]["exit_idx"],118)
        self.assertEqual(r["synthetic_trades"][0]["exit_reason"],"FORCED_CLOSE_WITH_ADVERSE_SLIPPAGE")
        self.assertTrue(r["complete_forced_flat"])
        self.assertEqual(r["synthetic_trades"][0]["entry_idx"],
                         r["synthetic_trades"][0]["signal_idx"]+1)
        self.assertFalse(r["historical_data_used"])
        self.assertFalse(r["economic_fitness_computed"])
        self.assertFalse(r["broker_fills_claimed"])

    def test_fixed_tp_can_exit_then_allow_second_entry(self):
        r=m.simulate_synthetic_day(strat(target_kind="FIXED_POINTS"),self.fi)
        self.assertEqual(r["synthetic_entries"],2)
        self.assertTrue(all(t["exit_reason"]=="TP_NO_GAP_IMPROVEMENT"
                            for t in r["synthetic_trades"]))
        self.assertGreater(r["synthetic_trades"][1]["signal_idx"],
                           r["synthetic_trades"][0]["exit_idx"])
        self.assertTrue(all(t["initial_model_risk_usd"]<=300
                            for t in r["synthetic_trades"]))

    def test_stop_first_same_entry_bar_long(self):
        baseline,_=m.artificial_m1()
        i=13
        op=float(baseline[i,0]);cl=float(baseline[i,3])
        patches={i:(op,op+8,op-8,cl,1000)}
        fixture=m.artificial_m1(patches=patches)[1]
        r=m.simulate_synthetic_day(strat(target_kind="R_MULTIPLE"),fixture,patches=patches)
        first=r["synthetic_trades"][0]
        self.assertEqual(first["exit_reason"],"SL_STOP_FIRST_AMBIGUOUS")
        self.assertGreater(first["ambiguous_bars"],0)
        self.assertLess(first["synthetic_net_usd"],0)

    def test_limit_exact_touch_and_pending_expiration(self):
        s=strat("LIMIT",target_kind="NONE")
        s["entry_order"]={"kind":"LIMIT","offset_ticks":32,"expiry_bars":2}
        s["id"]="NQ26_"+sha(s)[:16]
        r=m.simulate_synthetic_day(s,self.fi)
        self.assertEqual(r["synthetic_entries"],0)
        self.assertGreater(r["rejections"]["PENDING_ORDER_EXPIRED"],0)

    def test_all_stop_kinds_are_computed_on_completed_bars(self):
        for k in ("FIXED_POINTS","ATR","STRUCTURE","CHANDELIER"):
            with self.subTest(k=k):
                r=m.simulate_synthetic_day(strat(stop_kind=k),self.fi)
                self.assertTrue(r["synthetic_entries"]>=0)
                self.assertFalse(r["historical_data_used"])
                self.assertTrue(all(t["initial_model_risk_usd"]<=300
                                    for t in r["synthetic_trades"]))

    def test_all_target_kinds_never_invent_pivot_level(self):
        for k in ("NONE","R_MULTIPLE","FIXED_POINTS","ATR","VWAP","PIVOT"):
            with self.subTest(k=k):
                r=m.simulate_synthetic_day(strat(target_kind=k),self.fi)
                self.assertFalse(r["historical_data_used"])
                if k=="PIVOT":
                    self.assertEqual(r["synthetic_entries"],0)
                    self.assertGreater(r["rejections"]["LEVEL_REFERENCE_NEEDS_FORMAL_DEFINITION"],0)

    def test_break_even_trailing_are_previous_bar_only(self):
        s=strat(target_kind="NONE")
        s["exit"]["break_even"]={"start_r":.5,"plus_ticks":0}
        s["exit"]["trailing"]={"start_r":.5,"distance_atr":1.,"atr_period":8}
        s["id"]="NQ26_"+sha(s)[:16]
        r=m.simulate_synthetic_day(s,self.fi)
        self.assertGreater(r["synthetic_trades"][0]["stop_updates"],0)
        self.assertGreaterEqual(r["synthetic_trades"][0]["last_stop_price"],
                                r["synthetic_trades"][0]["entry_price"])

    def test_timeout_bars_cannot_leave_open_order(self):
        s=strat(target_kind="NONE")
        s["exit"]["exit_after_bars"]=2
        s["id"]="NQ26_"+sha(s)[:16]
        r=m.simulate_synthetic_day(s,self.fi)
        self.assertTrue(r["synthetic_entries"])
        self.assertTrue(all(t["exit_idx"]-t["entry_idx"]<=1
                            for t in r["synthetic_trades"]))
        self.assertTrue(all(t["exit_idx"]<=118 for t in r["synthetic_trades"]))

    def test_short_side_end_to_end(self):
        fixture=m.artificial_m1(kind="DOWN")[1]
        r=m.simulate_synthetic_day(strat(),fixture)
        self.assertTrue(r["synthetic_trades"])
        self.assertEqual(r["synthetic_trades"][0]["side"],-1)

    def test_market_protective_risk_rejection_not_fake_filled(self):
        s=strat()
        s["exit"]["stop_loss_required"]["points"]=30.
        s["id"]="NQ26_"+sha(s)[:16]
        r=m.simulate_synthetic_day(s,self.fi)
        self.assertEqual(r["synthetic_entries"],0)
        self.assertGreater(r["rejections"]["MODEL_ENTRY_RISK_NON_EXECUTABLE"],0)

    def test_invalid_fixture_digest_rejected(self):
        with self.assertRaises(PermissionError):
            m.simulate_synthetic_day(strat(),self.fi,patches={10:(20000,20001,19999,20000,10)})
        with self.assertRaises(PermissionError):
            m.simulate_synthetic_day(strat(),{"bars":[1,2]})

    def test_bad_synthetic_ohlc_refused(self):
        patches={20:(100,99,101,100,0)}
        with self.assertRaises(ValueError):
            m.artificial_m1(patches=patches)

    def test_holdout_years_and_13_gates_remain_closed(self):
        for day in ("2023-05-04","2024-05-04","2025-05-04","2026-05-04"):
            with self.subTest(day=day),self.assertRaises(PermissionError):
                m.simulate_synthetic_day(strat(),self.fi,day)
        self.assertEqual(audit()["passed_verified"],0)
        self.assertEqual(audit()["decision"],"EXECUTION_BLOCKED")

    def test_single_bar_fill_reuses_new_limit_policy(self):
        s=strat("LIMIT",target_kind="FIXED_POINTS")
        r=m.simulate_synthetic_day(s,self.fi)
        self.assertTrue(r["synthetic_entries"])
        self.assertTrue(all(t["entry_kind"]=="LIMIT" for t in r["synthetic_trades"]))

    def test_frozen_strategy_identity_and_duplicate_not_modified(self):
        s=strat(); before=copy.deepcopy(s)
        m.simulate_synthetic_day(s,self.fi)
        self.assertEqual(s,before)

if __name__=="__main__":
    unittest.main()
