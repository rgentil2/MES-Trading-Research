"""First 10K AST IST historical G0 signal smoke checks, synthetic source ONLY."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np

from research.nq import nq_m1_v38_10k_real_ist_signal_smoke as s
from research.nq.nq_m1_v31_full_synthetic_lifecycle import artificial_m1
from research.nq.test_nq_m1_v30_132_signal_m1_bridge import simple_sma

def sample():
    dates=["2021-05-03","2021-05-04","2021-05-05"]
    arr=np.stack([artificial_m1(seed=20261029+i,kind="UP")[0]
                  for i in range(3)])
    src={"years_opened":[2020,2021,2022],
         "holdout_2025_opened":False,"holdout_2026_opened":False,
         "complete_rth_sessions":3,"partial_sessions_excluded":0,
         "members_opened":15}
    return dates,arr,src

class TestV38FirstFrozenISTSignalDiagnostic(unittest.TestCase):
    def test_known_ascending_sma_long_in_artificial_M1(self):
        dates,bars,src=sample()
        report=s.diagnostic(dates,bars,src,[simple_sma()],indices=[0,1,2])
        self.assertEqual(report["candidate_count_exploratory"],1)
        self.assertEqual(report["signal_evaluations"],15)
        self.assertGreater(report["aggregate_actions"].get("LONG",0),0)
        self.assertEqual(report["economic_quality_gates_verified"],0)
        self.assertFalse(report["real_pnl_or_pf_computed"])
        self.assertFalse(report["all_10k_historical_evaluated"])
        self.assertFalse(report["full_session_trade_lifecycle_evaluated"])

    def test_frozen_10k_sha_and_12_preregistered_indices(self):
        candidates=s.frozen_sample()
        self.assertEqual(len(candidates),12)
        self.assertEqual(len(set(c["id"] for c in candidates)),12)
        self.assertTrue(all(c["id"].startswith("NQ26_") for c in candidates))
        self.assertEqual(s.EXPECTED_COHORT_SHA,
          "b9d2915fc55f86546ef63d74a588df5244d094eeecb4a7c900a4000d47660be9")

    def test_2023_plus_immediately_refused(self):
        dates,bars,src=sample()
        for year in (2023,2024,2025,2026):
            d=dates.copy();d[-1]=f"{year}-05-05"
            with self.subTest(year=year),self.assertRaises(PermissionError):
                s.diagnostic(d,bars,src,[simple_sma()],indices=[0,1])

    def test_invalid_session_order_and_bad_scope_denied(self):
        dates,bars,src=sample()
        with self.assertRaises(ValueError):
            s.diagnostic(dates,bars,src,[simple_sma()],indices=[1,0])
        with self.assertRaises(PermissionError):
            s.diagnostic(dates,bars,dict(src,holdout_2025_opened=True),
                         [simple_sma()],indices=[0,1])
        with self.assertRaises(ValueError):
            s.diagnostic(dates,bars,src,[simple_sma(),simple_sma()],
                         indices=[0,1])

    def test_sha_required_before_zip_member_read(self):
        with TemporaryDirectory() as temp:
            p=Path(temp)/"fake.zip";p.write_bytes(b"fake")
            with self.assertRaises(PermissionError):
                s.audit_original_archive(p)

if __name__=="__main__": unittest.main()
