"""NQ Builder 50K reference arithmetic, synthetic only, never market PnL."""
import unittest
from dataclasses import replace
from research.nq import nq_m1_v22_account_risk_reference as r


def pt(e,b=None):
    return {"equity":float(e),"closed_balance":float(e if b is None else b)}


class TestNQAccountReference(unittest.TestCase):
    def test_intraday_high_does_not_trail_eod_floor(self):
        out=r.synthetic_account_path([{
            "date":"2021-03-01",
            "path":[pt(50000),pt(52500,50000),pt(50000)]
        }])
        self.assertEqual(out["date_rows"][0]["hard_floor_after_close"],48000)
        self.assertFalse(out["hard_breach"])
        self.assertFalse(out["plan_identity_confirmed"])

    def test_eod_profit_trails_floor_then_locks_at_50100(self):
        out=r.synthetic_account_path([
            {"date":"2021-03-01","path":[pt(50000),pt(51000)]},
            {"date":"2021-03-02","path":[pt(51000),pt(53000)]},
        ])
        self.assertEqual(out["date_rows"][0]["hard_floor_after_close"],49000)
        self.assertEqual(out["date_rows"][1]["hard_floor_after_close"],50100)
        self.assertTrue(out["date_rows"][1]["end_day_profit_target_reached"])

    def test_hard_floor_breach_detects_floating_intraday(self):
        out=r.synthetic_account_path([{
            "date":"2021-03-01",
            "path":[pt(50000),pt(47999,50000),pt(50000)]
        }])
        self.assertTrue(out["hard_breach"])
        self.assertTrue(out["date_rows"][0]["hard_breach_touched"])

    def test_soft_daily_loss_is_separate_from_eod_maximum_loss(self):
        out=r.synthetic_account_path([{
            "date":"2021-03-01",
            "path":[pt(50000),pt(48999,50000),pt(50000)]
        }])
        self.assertTrue(out["date_rows"][0]["soft_pause_touched"])
        self.assertFalse(out["date_rows"][0]["hard_breach_touched"])
        self.assertEqual(out["official_daily_loss_usd"],1000)
        self.assertEqual(out["internal_closed_pnl_pause_usd"],-600)

    def test_closed_balance_must_start_where_prior_day_ended(self):
        with self.assertRaises(ValueError):
            r.synthetic_account_path([
                {"date":"2021-03-01","path":[pt(50000),pt(51000)]},
                {"date":"2021-03-02","path":[pt(50000),pt(52000)]},
            ])

    def test_no_open_position_at_end_day_or_non_ist(self):
        with self.assertRaises(ValueError):
            r.synthetic_account_path([{
                "date":"2021-03-01",
                "path":[pt(50000),pt(50050,50000)]}])
        with self.assertRaises(PermissionError):
            r.synthetic_account_path([{"date":"2025-03-01","path":[pt(50000)]}])

    def test_plan_is_research_reference_not_user_entitlement(self):
        p=replace(r.AccountProfile(),verified_user_plan=True)
        with self.assertRaises(ValueError):
            r.synthetic_account_path([],p)
        with self.assertRaises(ValueError):
            r.synthetic_account_path([],replace(r.AccountProfile(),instrument="MNQ"))


if __name__=="__main__":
    unittest.main()
