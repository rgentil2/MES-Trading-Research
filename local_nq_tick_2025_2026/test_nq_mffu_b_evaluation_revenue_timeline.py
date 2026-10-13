#!/usr/bin/env python3
"""Synthetic month-only timeline; no licensed tick or holdout access."""
import unittest
from decimal import Decimal
from nq_mffu_b_evaluation_revenue_timeline import B,stage_monthly,report,money
from nq_tick_short_horizon_month import MONTHS

def row(day,amounts):
    return {"day":day,"fee_router":{B:[{"net_mffu":m} for m in amounts]}}

class TestSafeTimeline(unittest.TestCase):
    def test_stage_reset_same_month(self):
        data=[
            row("2025-10-15",[100,100]),
            row("2025-10-16",[-30]),
            row("2025-10-17",[10,20]),
            row("2025-11-03",[50]),
        ]
        out=stage_monthly(data,2)
        self.assertEqual(out[0]["eval_cumulative_usd"],170.0)
        self.assertEqual(out[0]["funded_cumulative_usd"],30.0)
        self.assertEqual(out[1]["funded_cumulative_usd"],80.0)
        self.assertEqual(out[1]["research_no_reset_cumulative_usd"],250.0)
        self.assertEqual(out[0]["eval_trades"],3)
        self.assertEqual(out[0]["funded_trades"],2)
        self.assertEqual(len(out),len(MONTHS))

    def test_reject_missing_month(self):
        with self.assertRaises(AssertionError):
            stage_monthly([row("2026-07-01",[200]),row("2026-07-02",[])],1)

    def test_reject_bad_cutoff(self):
        with self.assertRaises(ValueError):
            stage_monthly([row("2025-10-15",[5])],1)

    def test_money_exact(self):
        self.assertEqual(money(3152.61)+money(4899.74),Decimal("8052.35"))

if __name__=="__main__":unittest.main()
