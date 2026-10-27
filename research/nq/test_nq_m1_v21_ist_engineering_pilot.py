"""V2.1 IST only engineering smoke: all market reads mocked in public CI."""
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from research.nq import nq_m1_v21_ist_engineering_pilot as v


def session():
    b=np.empty((390,5),float)
    for i in range(390):
        p=19000.+i*.25
        b[i]=[p,p+1,p-1,p+.25,1000.]
    return b


class TestV21NQISTPilot(unittest.TestCase):
    def test_registered_100_are_frozen_and_nq_only(self):
        s=v.registered()
        self.assertEqual(len(s),82)
        self.assertTrue(all(x["position_sizing"]=={"instrument":"NQ","contracts":1}
                            for x in s))
        self.assertTrue(all(x["market_data_years_permitted_for_discovery"]==
                            [2020,2021,2022] for x in s))

    def test_invalid_pilot_sizes_fail_before_data_access(self):
        for d,n in ((0,1),(1,0),(11,1),(1,11)):
            with patch.object(v,"load_years",side_effect=AssertionError("MUST_NOT_READ")):
                with self.assertRaises(ValueError):
                    v.pilot(Path("/MUST_NOT_READ.zip"),d,n)

    def test_reproducible_ist_only_mocked_no_economic_output(self):
        x=session()
        meta={"years_opened":[2020,2021,2022],
              "holdout_2025_opened":False,"holdout_2026_opened":False,
              "members_opened":15,"complete_rth_sessions":735,
              "partial_sessions_excluded":39}
        with patch.object(v,"load_years",return_value=(
            ["2020-01-02","2020-01-03"],np.stack((x,x)),meta)):
            out=v.pilot(Path("/DOES_NOT_EXIST.zip"),2,2)
        self.assertEqual(out["status"],v.STATUS)
        self.assertEqual(out["universe"],"NQ_1_CONTRACT_ONLY")
        self.assertEqual(len(out["strategies"]),2)
        self.assertEqual(out["days_per_strategy"],2)
        self.assertFalse(out["multi_session_warmup_wired"])
        self.assertFalse(out["formal_g0_d0_d1_d2_applied"])
        self.assertFalse(out["outcomes_or_pnl_exported"])
        self.assertNotIn("net_usd",str(out))

    def test_future_year_in_source_fails_closed(self):
        bad={"years_opened":[2020,2021,2022,2025],
             "holdout_2025_opened":True,"holdout_2026_opened":False}
        with patch.object(v,"load_years",return_value=(
            ["2020-01-02"],np.stack((session(),)),bad)):
            with self.assertRaises(RuntimeError):
                v.pilot(Path("/DOES_NOT_EXIST.zip"),1,1)

if __name__=="__main__":
    unittest.main()
