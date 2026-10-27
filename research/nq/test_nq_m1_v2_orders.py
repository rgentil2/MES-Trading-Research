"""V2 S0.2 synthetic-only M1 pending orders and protective exit tests."""
import copy
import unittest
import numpy as np
from research.nq import nq_m1_v2_orders as m
from research.nq import nq_m1_v2_generator as g


def bars_fixture():
    b = np.empty((390, 5), dtype=float)
    for i in range(390):
        p = 100.+i*.25
        b[i] = [p, p+1, p-1, p+.25, 1000]
    return b


def strategy():
    leaf = lambda op: {"op": op, "indicator": {
        "name": "EMA", "parameters": {"period": 5}},
        "lag_completed_bars": 1}
    return {
        "schema": g.STRATEGY_SCHEMA,
        "market_data_years_permitted_for_discovery": [2020, 2021, 2022],
        "universe": "NQ_M1", "signal_clock": "America/New_York",
        "bars_are_end_labeled": True, "signal_uses_completed_bars_only": True,
        "long": leaf("RISING"), "short": leaf("FALLING"),
        "entry_order": {"kind": "MARKET", "offset_ticks": 0, "expiry_bars": 1},
        "exit": {"stop_loss_required": {"kind": "FIXED_POINTS", "points": 3.},
                 "profit_target": {"kind": "NONE"}, "trailing": None,
                 "break_even": None, "exit_after_bars": 5,
                 "flat_at_et": "11:29"}
    }


class TestNQM1V2Orders(unittest.TestCase):
    def test_reject_off_tick_ohlc_prices(self):
        b = bars_fixture()
        b[21, 3] += 0.125
        with self.assertRaises(ValueError):
            m.simulate_day(b, strategy(), "2021-06-16")

    def test_signal_counts_are_distinct_from_fills_and_risk_rejections(self):
        r = m.simulate_day(bars_fixture(), strategy(), "2021-06-16")
        info = r["signal_diagnostics"]
        self.assertGreater(info["decision_bars_checked"], 0)
        self.assertGreater(info["raw_long_at_decision"], 0)
        self.assertEqual(info["raw_short_at_decision"], 0)
        self.assertEqual(info["both_sides_at_decision"], 0)
        self.assertLessEqual(r["filled"], info["raw_long_at_decision"])

    def test_reject_reasons_sum_to_distinct_signal_occasions(self):
        result = m.simulate_day(bars_fixture(), strategy(), "2021-06-16")
        sig = result["signal_diagnostics"]
        unique_signals = sig["raw_long_at_decision"]+sig["raw_short_at_decision"]-sig["both_sides_at_decision"]
        self.assertEqual(unique_signals, result["filled"] + sum(result["rejected"].values()))

    def test_one_mnq_feasibility_does_not_change_nq_fills(self):
        s = strategy()
        s["exit"]["stop_loss_required"] = {"kind": "FIXED_POINTS", "points": 30.0}
        r = m.simulate_day(bars_fixture(), s, "2021-06-16")
        self.assertEqual(r["filled"], 0)
        self.assertGreater(r["rejected"]["risk_ineligible"], 0)
        self.assertEqual(r["signal_diagnostics"]["nq_risk_reject_feasible_as_1mnq"],
                         r["rejected"]["risk_ineligible"])
        self.assertEqual(r["signal_diagnostics"]["nq_risk_reject_not_feasible_as_1mnq"], 0)

    def test_initial_atr_warmup_and_invalid_vwap_tp_are_separate(self):
        first = strategy()
        first["exit"]["stop_loss_required"] = {"kind":"ATR", "period":240, "multiple":1.}
        r1 = m.simulate_day(bars_fixture(), first, "2021-06-16")
        self.assertGreater(r1["rejected"]["missing_stop_context"], 0)
        self.assertEqual(r1["rejected"]["invalid_or_unavailable_target"], 0)
        second = strategy()
        second["exit"]["profit_target"] = {"kind":"CAUSAL_LEVEL", "reference":"VWAP"}
        r2 = m.simulate_day(bars_fixture(), second, "2021-06-16")
        self.assertGreater(r2["rejected"]["invalid_or_unavailable_target"], 0)

    def test_market_fills_and_daily_limit(self):
        r = m.simulate_day(bars_fixture(), strategy(), "2021-06-16")
        self.assertEqual(r["filled"], 2)
        self.assertTrue(all(t["entry_order_kind"] == "MARKET" for t in r["trades"]))
        self.assertTrue(all(t["initial_risk_usd"] <= 300 for t in r["trades"]))

    def test_limit_touch_no_slippage_beyond_limit(self):
        b, s = bars_fixture(), strategy()
        s["entry_order"] = {"kind": "LIMIT", "offset_ticks": 0, "expiry_bars": 1}
        r = m.simulate_day(b, s, "2021-06-16")
        self.assertTrue(r["trades"])
        t = r["trades"][0]
        self.assertEqual(t["entry_order_kind"], "LIMIT")
        self.assertEqual(t["entry_price"], t["requested_price"])

    def test_limit_order_expiry_without_fictitious_fill(self):
        s = strategy()
        s["entry_order"] = {"kind": "LIMIT", "offset_ticks": 32, "expiry_bars": 2}
        r = m.simulate_day(bars_fixture(), s, "2020-06-16")
        self.assertEqual(r["filled"], 0)
        self.assertGreater(r["rejected"]["expired_pending"], 0)

    def test_stop_order_gap_adverse_fill_and_slippage(self):
        b = bars_fixture()
        buy_trigger = 105.
        b[21] = [106., 107., 104., 106.25, 1000]
        self.assertEqual(m._pending_fill(b, 21, 1, "STOP", buy_trigger), 106.5)
        self.assertIsNone(m._pending_fill(b, 22, -1, "STOP", 90.))

    def test_pending_orders_respect_bar_expiry(self):
        s = strategy()
        s["entry_order"] = {"kind": "STOP", "offset_ticks": 32, "expiry_bars": 1}
        r = m.simulate_day(bars_fixture(), s, "2020-10-12")
        self.assertEqual(r["filled"], 0)
        self.assertGreater(r["rejected"]["expired_pending"], 0)

    def test_intra_entry_bar_pending_tp_is_suppressed(self):
        b, s = bars_fixture(), strategy()
        s["entry_order"] = {"kind": "LIMIT", "offset_ticks": 0, "expiry_bars": 1}
        s["exit"]["profit_target"] = {"kind": "R_MULTIPLE", "risk_multiple": .5}
        s["exit"]["exit_after_bars"] = 1
        b[21, 1] = 160.  # favorable high may have happened before limit touch
        r = m.simulate_day(b, s, "2021-06-16")
        self.assertEqual(r["trades"][0]["exit_reason"], "TIMEOUT_BARS")

    def test_stop_first_in_same_bar_when_both_levels_touched(self):
        b, s = bars_fixture(), strategy()
        s["entry_order"] = {"kind": "STOP", "offset_ticks": 0, "expiry_bars": 1}
        s["exit"]["profit_target"] = {"kind": "R_MULTIPLE", "risk_multiple": .5}
        b[21, 1], b[21, 2] = 150., 50.
        r = m.simulate_day(b, s, "2020-06-16")
        self.assertEqual(r["trades"][0]["exit_reason"], "SL_FIRST_OR_GAP")
        self.assertLess(r["trades"][0]["net_usd"], 0.)

    def test_break_even_only_after_prior_completed_bar(self):
        b, s = bars_fixture(), strategy()
        s["exit"]["break_even"] = {"start_r": .5, "plus_ticks": 0}
        b[22, 1] = 112.
        first_entry = b[21, 0] + m.SLIP
        b[23, 2] = first_entry - 1
        r = m.simulate_day(b, s, "2022-06-16")
        self.assertEqual(r["trades"][0]["exit_idx"], 23)
        self.assertEqual(r["trades"][0]["exit_reason"], "SL_FIRST_OR_GAP")
        self.assertGreaterEqual(r["trades"][0]["final_stop_price"], first_entry)
        self.assertGreater(r["trades"][0]["stop_updates"], 0)

    def test_trailing_stop_uses_closed_bar_only(self):
        b, s = bars_fixture(), strategy()
        s["exit"]["trailing"] = {"start_r": .25, "distance_atr": 1.,
                                 "atr_period": 3}
        b[22, 1] = 112.
        first_entry = b[21, 0] + m.SLIP
        b[23, 2] = first_entry - 1.
        r = m.simulate_day(b, s, "2020-06-16")
        self.assertEqual(r["trades"][0]["exit_idx"], 23)
        self.assertGreater(r["trades"][0]["final_stop_price"], first_entry)

    def test_favorable_future_move_cannot_change_old_signal(self):
        b, s = bars_fixture(), strategy()
        first = m.base.eval_expr(b, 20, s["long"])
        b[21:, 3] = 99.
        second = m.base.eval_expr(b, 20, s["long"])
        self.assertEqual(first, second)

    def test_unsupported_previous_session_level_fails_closed(self):
        s = strategy()
        s["exit"]["profit_target"] = {"kind": "CAUSAL_LEVEL",
                                      "reference": "PREVIOUS_COMPLETED_SESSION_LEVEL"}
        with self.assertRaises(m.base.UnsupportedV2Feature):
            m.simulate_day(bars_fixture(), s, "2021-06-16")

    def test_2023_2025_disallowed_for_ist_simulator(self):
        for year in ["2023", "2025", "2026"]:
            with self.assertRaises(PermissionError):
                m.simulate_day(bars_fixture(), strategy(), year+"-06-16")

    def test_shadow_router_contract_keys(self):
        from research.nq import nq_m1_v2_pipeline as p
        s = strategy()
        s["id"] = "S1"
        r = m.simulate_day(bars_fixture(), s, "2021-06-16")
        portfolio = p.simulate_shadow_router(r["trades"], ["S1"])
        self.assertEqual(portfolio["entries"], r["filled"])

if __name__ == "__main__":
    unittest.main()
