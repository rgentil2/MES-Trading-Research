"""S0 synthetic technical checks for explicitly limited M1 OHLC calculator/executor."""
import copy
import unittest
import numpy as np

from research.nq import nq_m1_v2_m1_engine as m
from research.nq import nq_m1_v2_generator as g


def demo_bars():
    bars = np.zeros((390, 5), dtype=float)
    for i in range(390):
        price = 100. + i*.1
        bars[i] = [price, price+1., price-1., price+.25, 1000.+(i%5)]
    return bars


def base_strategy():
    return {
        "schema": g.STRATEGY_SCHEMA,
        "universe": "NQ_M1",
        "market_data_years_permitted_for_discovery": [2020, 2021, 2022],
        "signal_clock": "America/New_York",
        "bars_are_end_labeled": True, "signal_uses_completed_bars_only": True,
        "long": {"op": "RISING",
                 "indicator": {"name": "EMA", "parameters": {"period": 5}},
                 "lag_completed_bars": 1},
        "short": {"op": "FALLING",
                  "indicator": {"name": "EMA", "parameters": {"period": 5}},
                  "lag_completed_bars": 1},
        "entry_order": {"kind": "MARKET", "offset_ticks": 0, "expiry_bars": 1},
        "exit": {"stop_loss_required": {"kind": "FIXED_POINTS", "points": 3.},
                 "profit_target": {"kind": "NONE"},
                 "trailing": None, "break_even": None,
                 "exit_after_bars": 3, "flat_at_et": "11:29"}
    }


class TestNQM1V2M1Engine(unittest.TestCase):
    def test_rising_predicate_uses_predeclared_lag_not_only_previous_bar(self):
        bars = demo_bars()
        for ix, price in [(56, 102), (57, 102), (58, 100), (59, 100.5), (60, 100.75)]:
            bars[ix, 0] = price
            bars[ix, 1] = price + 1
            bars[ix, 2] = price - 1
            bars[ix, 3] = price
        one = {"op": "RISING", "indicator": {
            "name": "SMA", "parameters": {"period": 2}}, "lag_completed_bars": 1}
        three = dict(one, lag_completed_bars=3)
        self.assertTrue(m.eval_expr(bars, 60, one))
        self.assertFalse(m.eval_expr(bars, 60, three))

    def test_38_supported_not_132(self):
        self.assertEqual(len(m.SUPPORTED_INDICATORS), 38)
        r = g.read_registry()
        self.assertTrue(m.SUPPORTED_INDICATORS.issubset({x["name"] for x in r["entries"]}))
        self.assertNotIn("MACD", m.SUPPORTED_INDICATORS)

    def test_indicator_causality_future_mutation(self):
        original = demo_bars()
        alternate = original.copy()
        alternate[65:, :4] *= 2
        cases = [
            ("SMA", {"period": 15}),
            ("EMA", {"period": 15}),
            ("WMA", {"period": 15}),
            ("RMA", {"period": 15}),
            ("ROC", {"period": 15}),
            ("Momentum", {"period": 15}),
            ("ATR", {"period": 15}),
            ("NATR", {"period": 15}),
            ("True Range", {"period": 15}),
            ("VWAP", {"anchor": "session"}),
            ("Relative Volume", {"period": 15}),
            ("Z-Score", {"period": 15}),
            ("Standard Deviation", {"period": 15}),
            ("Variance", {"period": 15}),
            ("Volume Z-Score", {"period": 15}),
            ("Donchian", {"period": 15}),
            ("OBV", {"period": 15}),
            ("Bollinger Bandwidth", {"period": 15, "std_multiplier": 2.0}),
        ]
        for name, params in cases:
            item = {"name": name, "parameters": params}
            self.assertAlmostEqual(m.indicator_value(original, 64, item),
                                   m.indicator_value(alternate, 64, item),
                                   places=7, msg=name)

    def test_warmup_no_future(self):
        x = demo_bars()
        self.assertIsNone(m.indicator_value(x, 4, {"name": "SMA", "parameters": {"period": 15}}))
        self.assertIsNone(m.indicator_value(x, 14, {"name": "ROC", "parameters": {"period": 15}}))
        self.assertIsNone(m.indicator_value(x, 14, {"name": "Relative Volume", "parameters": {"period": 15}}))
        with self.assertRaises(ValueError):
            m.indicator_value(x, len(x), {"name": "SMA", "parameters": {"period": 15}})

    def test_technical_market_trade_and_limits(self):
        result = m.simulate_day(demo_bars(), base_strategy(), "2020-02-12")
        self.assertEqual(len(result["trades"]), 2)
        self.assertTrue(all(t["side"] == 1 for t in result["trades"]))
        self.assertTrue(all(t["net_usd"] == round(t["net_usd"], 2) for t in result["trades"]))
        self.assertTrue(all(t["initial_risk_usd"] <= 300 for t in result["trades"]))
        self.assertEqual(result["H2025_H2026"], "SEALED")

    def test_signal_does_not_read_future_bar(self):
        bars = demo_bars()
        a = m.eval_expr(bars, 40, base_strategy()["long"])
        bars[41:, 3] = -1_000_000
        b = m.eval_expr(bars, 40, base_strategy()["long"])
        self.assertEqual(a, b)

    def test_stop_first_when_same_bar_target_and_stop(self):
        x = demo_bars()
        x[21, 1] = 120.
        x[21, 2] = 50.
        s = base_strategy()
        s["exit"]["profit_target"] = {"kind": "R_MULTIPLE", "risk_multiple": 1.}
        res = m.simulate_day(x, s, "2021-08-12")
        self.assertTrue(res["trades"])
        self.assertEqual(res["trades"][0]["exit_reason"], "SL_STOP_FIRST")
        self.assertLess(res["trades"][0]["net_usd"], 0)

    def test_unsupported_features_fail_closed_not_silently_simulated(self):
        for edit in ["limit", "trailing", "macd"]:
            s = base_strategy()
            if edit == "limit":
                s["entry_order"]["kind"] = "LIMIT"
            if edit == "trailing":
                s["exit"]["trailing"] = {"start_r": 1., "distance_atr": 2.}
            if edit == "macd":
                s["long"]["indicator"]["name"] = "MACD"
            with self.assertRaises(m.UnsupportedV2Feature, msg=edit):
                m.simulate_day(demo_bars(), s, "2021-06-12")

    def test_2025_denied(self):
        with self.assertRaises(PermissionError):
            m.simulate_day(demo_bars(), base_strategy(), "2025-01-01")


if __name__ == "__main__":
    unittest.main()
