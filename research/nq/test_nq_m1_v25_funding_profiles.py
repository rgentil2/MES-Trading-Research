"""No financial outcomes: official 2026 MFFU evaluation profile contract tests."""
import unittest
from research.nq.nq_m1_v25_funding_profiles import (
    PLANS, require_specific_plan, technical_preflight
)

class TestFundingProfiles(unittest.TestCase):
    def test_five_distinct_plan_types_not_conflated(self):
        self.assertEqual(len(PLANS),5)
        self.assertEqual(PLANS["BUILDER_50K_DEFAULT"].daily_soft_pause_usd,1000)
        self.assertEqual(PLANS["BUILDER_50K_ADDON_1500"].max_loss_limit_eod_usd,1500)
        self.assertEqual(PLANS["RAPID_INTRADAY_50K"].consistency_fraction,.5)
        self.assertIsNone(PLANS["RAPID_INTRADAY_50K"].daily_soft_pause_usd)
        self.assertEqual(PLANS["RAPID_EOD_50K"].consistency_fraction,.3)
        self.assertEqual(PLANS["RAPID_EOD_50K"].min_trading_days,4)
        self.assertEqual(PLANS["PRO_50K_DEFAULT"].max_minis,3)
        self.assertTrue(all(x.profit_target_usd==3000 for x in PLANS.values()))

    def test_no_inferred_plan_or_stage(self):
        for name in (None,"50K","BUILDER","UNKNOWN","PRO_100K"):
            with self.subTest(name=name),self.assertRaises(PermissionError):
                require_specific_plan(name)
        with self.assertRaises(PermissionError):
            require_specific_plan("BUILDER_50K_DEFAULT","SIM_FUNDED")

    def test_one_nq_contract_allowed_in_each_evaluation_plan(self):
        for name in PLANS:
            result=technical_preflight(name,1)
            self.assertEqual(result["contracts"],1)
            self.assertFalse(result["economic_execution_authorized"])
            self.assertFalse(result["intraday_floating_engine_certified"])
            self.assertFalse(result["market_data_opened"])

    def test_max_contracts_and_negative_or_micro_mode_blocked(self):
        for name,plan in PLANS.items():
            for quantity in (0,-1,plan.max_minis+1,1.0,True):
                with self.subTest(name=name,qty=quantity),self.assertRaises(ValueError):
                    technical_preflight(name,quantity)

    def test_no_daily_limit_does_not_mean_no_maximum_loss(self):
        for name in ("RAPID_INTRADAY_50K","RAPID_EOD_50K","PRO_50K_DEFAULT"):
            p=require_specific_plan(name)
            self.assertIsNone(p.daily_soft_pause_usd)
            self.assertEqual(p.max_loss_limit_eod_usd,2000)

if __name__=="__main__":
    unittest.main()
