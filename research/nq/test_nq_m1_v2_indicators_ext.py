"""S0.3 synthetic tests for 20 additional causal scalar indicator formulas."""
import unittest
import numpy as np
from research.nq import nq_m1_v2_indicators_ext as e
from research.nq import nq_m1_v2_m1_engine as m
from research.nq import nq_m1_v2_generator as g


def bars():
    b = np.empty((390, 5), dtype=float)
    for i in range(390):
        p = 100. + .25*i
        b[i] = [p, p+1., p-1., p+.25, 1000.+(i%7)*100.]
    return b


class TestV2ExtendedIndicators(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = g.read_registry()
        cls.by_name = {x["name"]: x for x in cls.registry["entries"]}

    def test_exactly_20_new_registered_blocks(self):
        self.assertEqual(len(e.EXTENDED), 20)
        self.assertEqual(len(m.SUPPORTED_INDICATORS), 38)
        self.assertTrue(e.EXTENDED.issubset(set(self.by_name)))

    def test_all_extended_formulas_finite_for_valid_warmup(self):
        b = bars()
        for name in e.EXTENDED:
            z = m.indicator_value(b, 350, {"name": name, "parameters": {"period": 20}})
            self.assertIsNotNone(z, name)
            self.assertTrue(np.isfinite(z), name)

    def test_future_prices_cannot_change_indicator(self):
        old = bars()
        new = old.copy()
        new[180:, :4] += 500.
        new[180:, 4] += 50000.
        for name in e.EXTENDED:
            block = {"name": name, "parameters": {"period": 20}}
            before = m.indicator_value(old, 179, block)
            after = m.indicator_value(new, 179, block)
            self.assertAlmostEqual(before, after, places=10, msg=name)

    def test_rsi_cmo_and_efficiency_trending_market(self):
        x = bars()
        for name, target in (("RSI", 100.), ("CMO", 100.),
                             ("Efficiency Ratio", 1.)):
            z = m.indicator_value(x, 100, {"name": name, "parameters": {"period": 20}})
            self.assertAlmostEqual(z, target, places=9)
        y = x.copy()
        y[:, 3] = y[0, 3]
        z = m.indicator_value(y, 100, {"name": "RSI", "parameters": {"period": 20}})
        self.assertAlmostEqual(z, 50., places=9)

    def test_bounds_of_bounded_scalars(self):
        x = bars()
        for name, lower, upper in (
            ("RSI", 0., 100.), ("MFI", 0., 100.),
            ("Williams %R", -100., 0.), ("Aroon", -100., 100.),
            ("CMF", -1., 1.), ("Range Percentile", 0., 100.),
            ("True Range Percentile", 0., 100.),
            ("Efficiency Ratio", 0., 1.), ("VHF", 0., 1.)):
            z = m.indicator_value(x, 110, {"name": name, "parameters": {"period": 30}})
            self.assertTrue(lower-1e-6 <= z <= upper+1e-6, (name,z))

    def test_warmup_and_zero_variance_handling(self):
        x = bars()
        for name in e.EXTENDED:
            z = m.indicator_value(x, 2, {"name": name, "parameters": {"period": 50}})
            self.assertIsNone(z, name)
        flat = x.copy()
        flat[:, 3] = 100.
        flat[:, 1] = 101.
        flat[:, 2] = 99.
        self.assertAlmostEqual(
            m.indicator_value(flat, 80, {"name": "Autocorrelation", "parameters": {"period": 20}}), 0.)
        self.assertAlmostEqual(
            m.indicator_value(flat, 80, {"name": "Skewness", "parameters": {"period": 20}}), 0.)

    def test_s0_order_engine_can_compile_extended_indicator(self):
        from research.nq import nq_m1_v2_orders as orders
        from research.nq.test_nq_m1_v2_orders import strategy
        s = strategy()
        s["long"]["indicator"] = {"name": "RSI", "parameters": {"period": 5}}
        s["short"]["indicator"] = {"name": "MFI", "parameters": {"period": 5}}
        orders.validate_supported(s)
        r = orders.simulate_day(bars(), s, "2022-10-10")
        self.assertEqual(r["status"], orders.STATUS)
        self.assertEqual(r["holdouts"], "SEALED")

if __name__ == "__main__":
    unittest.main()
