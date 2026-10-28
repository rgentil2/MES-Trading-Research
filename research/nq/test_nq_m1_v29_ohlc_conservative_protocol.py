"""S0.24 NQ M1-only deliberately conservative OHLC synthetic reference."""
import unittest
from research.nq import nq_m1_v29_ohlc_conservative_protocol as m
from research.nq.nq_m1_v22_quality_gate import audit

class TestConservativeM1Protocol(unittest.TestCase):
    def test_contract_does_not_release_backtester(self):
        d=m.contract()
        self.assertEqual(d["data_source"],"NQ_M1_IST_2020_2022_ONLY")
        self.assertEqual(d["contracts"],1)
        self.assertFalse(d["M1_backtest_authorized"])
        self.assertFalse(d["tick_certification_claimed"])
        self.assertEqual(d["quality_gate_passed_verified"],0)
        self.assertEqual(audit()["passed_verified"],0)

    def test_next_open_market_entry_with_adverse_slippage_long_short(self):
        b=m.Bar(100,102,98,101)
        self.assertEqual(m.entry(b,1,"MARKET")["fill_price"],100.5)
        self.assertEqual(m.entry(b,-1,"MARKET")["fill_price"],99.5)

    def test_long_short_stop_first_on_dual_touch(self):
        b=m.Bar(100,102,98,101)
        a=m.exit_bar(b,1,99,101)
        self.assertEqual(a["reason"],"SL_STOP_FIRST_AMBIGUOUS")
        self.assertEqual(a["exit_price"],98.5)
        self.assertTrue(a["ambiguous_bar"])
        c=m.exit_bar(b,-1,101,99)
        self.assertEqual(c["exit_price"],101.5)
        self.assertTrue(c["ambiguous_bar"])

    def test_adverse_stop_gap_never_fills_at_better_level(self):
        long=m.exit_bar(m.Bar(95,96,94,95),1,99)
        self.assertEqual(long["exit_price"],94.5)
        short=m.exit_bar(m.Bar(105,106,104,105),-1,101)
        self.assertEqual(short["exit_price"],105.5)

    def test_favorable_target_gap_improvement_is_not_claimed(self):
        self.assertEqual(m.exit_bar(m.Bar(105,106,103,104),1,99,102)["exit_price"],102)
        self.assertEqual(m.exit_bar(m.Bar(95,96,94,95),-1,101,98)["exit_price"],98)

    def test_pending_same_bar_only_target_suppression(self):
        b=m.Bar(100,102,99,101)
        a=m.exit_bar(b,1,98,101,pending_entry_same_bar=True)
        self.assertFalse(a["exited_proxy"])
        self.assertTrue(a["target_suppressed"])
        self.assertEqual(a["reason"],"SAME_BAR_PENDING_TP_SUPPRESSED")

    def test_pending_same_bar_stop_not_suppressed(self):
        b=m.Bar(100,102,98,101)
        a=m.exit_bar(b,1,99,101,pending_entry_same_bar=True)
        self.assertTrue(a["exited_proxy"])
        self.assertEqual(a["reason"],"SL_STOP_FIRST_AMBIGUOUS")

    def test_limit_exact_touch_does_not_assert_fill(self):
        # Exact-touch limit fills are a queue assumption, not evidence.
        b=m.Bar(100,101,99,100)
        a=m.entry(b,1,"LIMIT",99)
        self.assertFalse(a["filled_proxy"])
        self.assertEqual(a["reason"],"LIMIT_TOUCH_ONLY_OR_NOT_CROSSED")
        b=m.Bar(100,101,98.75,100)
        a=m.entry(b,1,"LIMIT",99)
        self.assertTrue(a["filled_proxy"])
        self.assertEqual(a["fill_price"],99)

    def test_limit_market_open_gets_no_favorable_price_improvement(self):
        long=m.entry(m.Bar(98,100,97,99),1,"LIMIT",99)
        self.assertEqual(long["fill_price"],99)
        short=m.entry(m.Bar(102,104,101,103),-1,"LIMIT",101)
        self.assertEqual(short["fill_price"],101)

    def test_buy_stop_adverse_gap_and_sell_stop_adverse_gap(self):
        a=m.entry(m.Bar(103,104,102,103),1,"STOP",101)
        self.assertEqual(a["fill_price"],103.5)
        b=m.entry(m.Bar(97,98,96,97),-1,"STOP",99)
        self.assertEqual(b["fill_price"],96.5)

    def test_pending_stop_only_trigger_no_fill_when_not_reached(self):
        b=m.Bar(100,101,99,100)
        self.assertFalse(m.entry(b,1,"STOP",102)["filled_proxy"])
        self.assertFalse(m.entry(b,-1,"STOP",98)["filled_proxy"])

    def test_time_close_uses_slippage_and_non_future_bar(self):
        a=m.exit_bar(m.Bar(100,101,99,100),1,98,102,forced_time_exit=True)
        self.assertEqual(a["exit_price"],99.5)
        self.assertEqual(a["reason"],"FORCED_CLOSE_WITH_ADVERSE_SLIPPAGE")

    def test_reject_bad_ohlc_off_grid_and_nonfinite(self):
        cases=(m.Bar(100,99,98,101),m.Bar(100.1,102,98,101),
               m.Bar(float("nan"),102,98,101),m.Bar(0,2,1,1))
        for b in cases:
            with self.subTest(b=b),self.assertRaises(ValueError):
                m.entry(b,1,"MARKET")

    def test_reject_unrounded_levels_bad_side_and_negative_slip(self):
        b=m.Bar(100,102,98,101)
        for kwargs in ({"side":0,"kind":"MARKET"},
                       {"side":1,"kind":"STOP","requested":100.1},
                       {"side":1,"kind":"MARKET","requested":100},
                       {"side":1,"kind":"MARKET","slippage_ticks":-1}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                m.entry(b,**kwargs)

    def test_existing_v2_exact_touch_fill_is_not_identical_to_new_model(self):
        # Explicit non-parity is a TODO, not a promoted certification.
        import numpy as np
        from research.nq.nq_m1_v2_orders import _pending_fill
        bars=np.array([[100.,101.,99.,100.,1000.]])
        self.assertEqual(_pending_fill(bars,0,1,"LIMIT",99.),99.)
        self.assertFalse(m.entry(m.Bar(100,101,99,100),1,"LIMIT",99.)["filled_proxy"])

if __name__=="__main__":
    unittest.main()
