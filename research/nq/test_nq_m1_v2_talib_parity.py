"""S0.5 external numerical parity against TA-Lib; NO market data.

A pinned third-party reference protects against self-confirming duplicate formulas.
Exact indexing (first valid sample, Wilder seeding, session initial states)
matters for trading. When reference differs, FAIL the build; never quietly
adjust sample indices or tolerance to claim parity.
"""
from __future__ import annotations
import unittest
import numpy as np
import talib

from research.nq import nq_m1_v2_m1_engine as core

PERIOD = 14
FLOAT_TOL_ABS = 1e-5  # double-precision rolling moments at NQ ~20000 differ by ~1e-7 absolute
CLOSE = [
    "SMA", "EMA", "WMA", "ROC", "Momentum", "RSI", "ATR", "NATR",
    "Standard Deviation", "Variance", "CCI", "Williams %R",
    "Aroon", "MFI", "OBV"
]


def reproducible_ohlcv():
    rng = np.random.default_rng(20261027)
    prices = 20000. + np.cumsum(rng.normal(.15, 6., size=390))
    opens = prices + rng.normal(0., 1., size=390)
    highs = np.maximum(opens, prices) + rng.uniform(.5, 4., size=390)
    lows = np.minimum(opens, prices) - rng.uniform(.5, 4., size=390)
    volume = rng.integers(50, 3000, size=390).astype(float)
    return np.column_stack((opens, highs, lows, prices, volume))


def reference(bars, name, period=PERIOD):
    h, l, c, v = (np.ascontiguousarray(bars[:,i], dtype=np.float64)
                  for i in (1, 2, 3, 4))
    defs = {
        "SMA": lambda: talib.SMA(c, timeperiod=period),
        "EMA": lambda: talib.EMA(c, timeperiod=period),
        "WMA": lambda: talib.WMA(c, timeperiod=period),
        "ROC": lambda: talib.ROC(c, timeperiod=period),
        "Momentum": lambda: talib.MOM(c, timeperiod=period),
        "RSI": lambda: talib.RSI(c, timeperiod=period),
        "ATR": lambda: talib.ATR(h, l, c, timeperiod=period),
        "NATR": lambda: talib.NATR(h, l, c, timeperiod=period),
        "Standard Deviation": lambda: talib.STDDEV(c, timeperiod=period, nbdev=1.),
        "Variance": lambda: talib.VAR(c, timeperiod=period, nbdev=1.),
        "CCI": lambda: talib.CCI(h, l, c, timeperiod=period),
        "Williams %R": lambda: talib.WILLR(h, l, c, timeperiod=period),
        "Aroon": lambda: talib.AROONOSC(h, l, timeperiod=period),
        "MFI": lambda: talib.MFI(h, l, c, v, timeperiod=period),
        "OBV": lambda: talib.OBV(c, v)
    }
    return defs[name]()


class TestIndependentTALibParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bars = reproducible_ohlcv()

    def test_all_15_named_formulas_agree_on_mature_bars(self):
        for name in CLOSE:
            ref = reference(self.bars, name)
            p = {"period": PERIOD}
            with self.subTest(name=name):
                for i in (30, 45, 100, 175, 250, 389):
                    expected = float(ref[i])
                    got = core.indicator_value(self.bars, i,
                                               {"name": name, "parameters": p})
                    self.assertIsNotNone(got)
                    self.assertTrue(np.isfinite(expected), (name, i))
                    self.assertAlmostEqual(float(got), expected, delta=FLOAT_TOL_ABS,
                                           msg=f"{name} end-label index {i}")

    def test_first_valid_bar_and_no_leakage(self):
        for name in ("EMA", "RSI", "ATR", "NATR", "MFI", "Aroon"):
            p = {"name": name, "parameters": {"period": PERIOD}}
            ref = reference(self.bars, name)
            valid = int(np.flatnonzero(np.isfinite(ref))[0])
            with self.subTest(name=name):
                self.assertIsNone(core.indicator_value(self.bars, valid-1, p))
                self.assertAlmostEqual(core.indicator_value(self.bars, valid, p),
                                       ref[valid], delta=FLOAT_TOL_ABS)

    def test_parity_is_causal_for_all_15_indicators(self):
        for name in CLOSE:
            original = self.bars
            changed = original.copy()
            changed[120:, :4] *= 1.1
            changed[120:, 4] *= 2.
            cfg = {"name": name, "parameters": {"period": PERIOD}}
            with self.subTest(name=name):
                self.assertAlmostEqual(core.indicator_value(original, 119, cfg),
                                       core.indicator_value(changed, 119, cfg),
                                       delta=FLOAT_TOL_ABS)


if __name__ == "__main__":
    unittest.main()
