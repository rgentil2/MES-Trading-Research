"""S0 technical tests for NQ M1 staged discovery. No price archive access."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from research.nq import nq_m1_chrono_discovery as m


def demo_bars():
    bars = np.zeros((390, 5), dtype=float)
    for i in range(390):
        p = 100 + i * 1.0
        bars[i] = [p, p + .5, p - .5, p + .25, 1000]
    return bars


class TestNQM1Chrono(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = m.read_config()
        cls.rules = m.catalog(cls.cfg)

    def test_120_distinct_catalog(self):
        self.assertEqual(len(self.rules), 120)
        self.assertEqual(len(set(x["id"] for x in self.rules)), 120)
        self.assertEqual({x["family"] for x in self.rules}, set(m.FAMILIES))
        self.assertEqual({f: sum(x["family"] == f for x in self.rules) for f in m.FAMILIES}, {f: 24 for f in m.FAMILIES})

    def test_manifest_sha_is_deterministic(self):
        self.assertEqual(m.manifest_sha(self.rules), m.manifest_sha(m.catalog(self.cfg)))
        alt = copy.deepcopy(self.rules)
        alt[0]["lookback"] = 99
        self.assertNotEqual(m.manifest_sha(alt), m.manifest_sha(self.rules))

    def test_stage_whitelist(self):
        self.assertEqual(m.stage_years("IST"), (2020, 2021, 2022))
        self.assertEqual(m.stage_years("ISV1"), (2023,))
        self.assertEqual(m.stage_years("ISV2"), (2024,))
        for year in ["2025", "2026", "OOS", "ALL"]:
            with self.assertRaises(ValueError):
                m.stage_years(year)

    def test_archive_member_year_is_immutable(self):
        good = "nq/development_2020_2024/NQ_03-21_2020_Minute_Last.txt"
        later = "nq/development_2020_2024/NQ_03-24_2023_Minute_Last.txt"
        sealed = "nq/holdout_2025_2026/NQ_03-25_2025_Minute_Last.txt"
        self.assertTrue(m.permitted_market_member(good, (2020, 2021, 2022)))
        self.assertFalse(m.permitted_market_member(later, (2020, 2021, 2022)))
        self.assertFalse(m.permitted_market_member(sealed, (2020, 2021, 2022)))
        with self.assertRaises(ValueError):
            m.permitted_market_member(good, (2020, 2025))

    def test_future_price_cannot_change_signal(self):
        bars = demo_bars()
        rule = {"family": "BREAKOUT", "variant": 0, "lookback": 10,
                "stop_model": "ATR", "target_r": 2.}
        side = m.signal(bars, 30, rule)
        bars[31:] = 999999.
        self.assertEqual(m.signal(bars, 30, rule), side)

    def test_forced_1129_exit_without_target(self):
        bars = demo_bars()
        rule = {"family": "CONTINUATION", "variant": 0, "lookback": 10,
                "stop_model": "ATR", "target_r": None}
        trade, error = m.one_trade(bars, 25, 1, rule, self.cfg)
        self.assertIsNone(error)
        self.assertEqual(trade["exit_idx"], m.LAST_BAR_INDEX)
        self.assertEqual(trade["exit_reason"], "TIME_1129")

    def test_both_barriers_touched_stop_first(self):
        bars = demo_bars()
        rule = {"family": "BREAKOUT", "variant": 0, "lookback": 10,
                "stop_model": "ATR", "target_r": 2.}
        bars[26, 1] = 250
        bars[26, 2] = 0
        trade, error = m.one_trade(bars, 25, 1, rule, self.cfg)
        self.assertIsNone(error)
        self.assertEqual(trade["exit_reason"], "SL")

    def test_portfolio_summary_drawdown(self):
        rows = [
            {"session": "2020-01-02", "net": 10.},
            {"session": "2020-01-03", "net": -20.},
            {"session": "2021-01-04", "net": 3.},
        ]
        z = m.summarize(rows, ["2020-01-02", "2021-01-04"])
        self.assertEqual(z["trades"], 3)
        self.assertEqual(z["net_usd"], -7.)
        self.assertEqual(z["closed_trade_dd_usd"], 20.)
        self.assertEqual(z["by_year"], {"2020": -10., "2021": 3.})

    def test_isv_requires_frozen_ist_selected_ids(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "freeze.json"
            path.write_text(json.dumps({
                "stage": "IST_FROZEN",
                "catalog_sha256": m.manifest_sha(self.rules),
                "selected_ids": [self.rules[1]["id"], self.rules[0]["id"]],
            }))
            selected = m.freeze_selection(path, self.rules)
            self.assertEqual([x["id"] for x in selected],
                             [self.rules[0]["id"], self.rules[1]["id"]])
            path.write_text(json.dumps({
                "stage": "IST_FROZEN", "catalog_sha256": "wrong",
                "selected_ids": [self.rules[0]["id"]],
            }))
            with self.assertRaises(RuntimeError):
                m.freeze_selection(path, self.rules)

    def test_config_guards_holdout(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json"
            altered = copy.deepcopy(self.cfg)
            altered["holdout_years_blocked"] = [2026]
            path.write_text(json.dumps(altered))
            with self.assertRaises(RuntimeError):
                m.read_config(path)


if __name__ == "__main__":
    unittest.main()
