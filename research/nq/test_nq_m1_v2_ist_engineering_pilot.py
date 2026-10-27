"""Safe V2 IST pilot tests: NEVER open archives, mock market arrays only."""
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np

from research.nq import nq_m1_v2_ist_engineering_pilot as p


class TestV2ISTPilot(unittest.TestCase):
    def test_frozen_candidate_hashes_match_registered_public_manifest(self):
        manifest = p.frozen_batch()
        self.assertEqual(manifest["compatible_manifest_sha256"], p.FROZEN_COMPATIBLE_SHA256)
        self.assertEqual(manifest["broad_manifest_sha256"], p.FROZEN_BROAD_SHA256)
        self.assertEqual(len(manifest["compatible"]), 100)

    def test_undeclared_sizes_fail_before_data_access(self):
        for days, strategies in [(0, 1), (1, 0), (11, 1), (1, 11)]:
            with patch.object(p, "load_years", side_effect=AssertionError("NO_READ")):
                with self.assertRaises(ValueError):
                    p.pilot(Path("/DO_NOT_OPEN.zip"), days, strategies)

    def test_earliest_ist_mocked_market_smoke_only_reports_counts(self):
        x = np.empty((390, 5), dtype=float)
        for k in range(390):
            c = 100+k*.25
            x[k] = [c, c+1., c-1., c+.25, 1000.]
        source = {
            "years_opened": [2020, 2021, 2022], "members_opened": 15,
            "complete_rth_sessions": 2, "partial_sessions_excluded": 0,
            "holdout_2025_opened": False, "holdout_2026_opened": False
        }
        with patch.object(p, "load_years", return_value=(
                ["2020-01-02", "2020-01-03"], np.stack((x,x)), source)):
            out = p.pilot(Path("/MUST_NOT_ACCESS.zip"), 2, 2)
        self.assertEqual(out["status"], "IST_ENGINEERING_PILOT_ONLY")
        self.assertEqual(out["ist_sessions_evaluated"], 2)
        self.assertEqual(out["strategy_count"], 2)
        self.assertEqual(out["holdouts"], "H2025_H2026_T_SEALED")
        self.assertFalse(out["market_pnl_published"])
        self.assertFalse(out["formal_G0_D0_D1_D2_passed"])
        self.assertNotIn("net_usd", str(out))

    def test_rejected_or_corrupt_source_metadata_fails_closed(self):
        source = {
            "years_opened": [2020, 2021, 2022, 2025],
            "holdout_2025_opened": True,
            "holdout_2026_opened": False
        }
        with patch.object(p, "load_years", return_value=(
                ["2020-01-02"], np.zeros((1, 390, 5)), source)):
            with self.assertRaises(RuntimeError):
                p.pilot(Path("/DO_NOT_OPEN.zip"), 1, 1)


if __name__ == "__main__":
    unittest.main()
