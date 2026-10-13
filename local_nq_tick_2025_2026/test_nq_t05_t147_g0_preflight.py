#!/usr/bin/env python3
"""Synthetic-only invariants for T05/T147 G0 (no licensed market data)."""
import unittest
from copy import deepcopy
from unittest.mock import patch

from nq_tick_short_horizon_month import MONTHS
from nq_t133_t168_d1_engine import model_one
from nq_t05_t147_g0_preflight import aggregate, guard_month, month_stage, ts_to_5s_index
from qc_tick_day import utc_bounds
from nq_tick_short_horizon import STEP_100NS, dev_day


def fake_months(ambiguous=0):
    eligible = (19, 19, 19, 19, 19, 20, 20)
    result = {}
    for i, m in enumerate(MONTHS):
        result[m] = {
            "month": m, "source": 20, "eligible": eligible[i],
            "t05_n": 115 if i == 0 else 0,
            "t05_net": 5102.50 if i == 0 else 0,
            "t05_unknown": 0,
            "t147_cases": 20 if i == 0 else 0,
            "t147_n": 20 if i == 0 else 0,
            "t147_net": 642.25 if i == 0 else 0,
            "t147_ambiguous": ambiguous if i == 0 else 0,
            "t147_instruments": {"NQ": 18, "MNQ": 2} if i == 0 else {},
            "t147_not_modelled": {},
            "both": 5 if i == 0 else 0,
            "licensed_ticks_in_output": False,
            "individual_dates_or_trades_in_output": False,
        }
    return result


class T05T147G0(unittest.TestCase):
    def test_strict_month_gate_before_filesystem(self):
        for m in ("2026-05", "2026-09", "2024-02", "2025-09", ""):
            with self.assertRaisesRegex(ValueError, "SEALED_MONTH"):
                guard_month(m)
        with patch("nq_t05_t147_g0_preflight.month_days",
                   side_effect=AssertionError("file access called")):
            with self.assertRaisesRegex(ValueError, "SEALED_MONTH"):
                month_stage(None, "2026-05", {})

    def test_t05_signal_grid_exact(self):
        day = "2026-04-01"
        start, _ = utc_bounds(dev_day(day))
        ts = start + (1234+1)*STEP_100NS
        self.assertEqual(ts_to_5s_index(day, ts), 1234)
        with self.assertRaisesRegex(AssertionError, "DECISION_NOT_END"):
            ts_to_5s_index(day, ts+1)

    def test_parent_parity_and_safe_schema(self):
        got = aggregate(fake_months())
        self.assertEqual((got["t05_trades"], got["t147_modelled_trades"]), (115, 20))
        self.assertEqual(got["t147_instruments"], {"NQ": 18, "MNQ": 2})
        self.assertEqual(got["days_both_signal_families"], 5)
        self.assertEqual(got["compatibility_state"],
                         "G0_PARENT_PARITY_OK_EXPOSURE_REPLAY_REQUIRED")
        self.assertEqual(got["broker_fills_verified"], False)
        self.assertEqual(got["holdouts_opened"], False)
        self.assertEqual(got["new_data"], False)
        self.assertTrue(all("date" not in key and "price" not in key and
                            "trade_list" not in key for key in got))

    def test_ambiguous_entry_blocks_future_router(self):
        x = aggregate(fake_months(1))
        self.assertEqual(x["compatibility_state"],
                         "G0_PARENT_PARITY_OK_SHARED_ROUTER_BLOCKED")
        # D1 treats an entry-timestamp stop as a modelled LOSS, NOT a
        # reconstructable exchange sequence. Flag blocks joint routing.
        z = model_one([(10, 92, 101), (11, 99, 110)],
                      1, 93, 1.25, 15, 9, True)
        self.assertEqual(z["status"], "MODELLED_EXECUTION_UNVERIFIED")
        self.assertTrue(z["entry_group_ambiguous"])

    def test_reject_incomplete_and_tampered_parents(self):
        z = fake_months()
        del z[MONTHS[-1]]
        with self.assertRaisesRegex(ValueError, "EXACTLY_SEVEN"):
            aggregate(z)
        z = fake_months()
        z[MONTHS[0]]["t05_net"] -= 5
        with self.assertRaisesRegex(AssertionError, "T05_PARENT"):
            aggregate(z)
        z = fake_months()
        z[MONTHS[0]]["t147_net"] -= 10
        with self.assertRaisesRegex(AssertionError, "T147_PARENT"):
            aggregate(z)

    def test_privacy_fail_closed(self):
        z = fake_months()
        z[MONTHS[0]]["individual_dates_or_trades_in_output"] = True
        with self.assertRaisesRegex(AssertionError, "PRIVATE_OUTPUT"):
            aggregate(z)


if __name__ == "__main__":
    unittest.main()
