"""S0.30 real-IST adapter oracle protocol on synthetic samples only."""
import unittest
import tempfile
from pathlib import Path
import numpy as np
from research.nq import nq_m1_v35_real_ist_talib_oracles_qa as qa
from research.nq.nq_m1_v31_full_synthetic_lifecycle import artificial_m1

def sample():
    dates=["2021-03-10","2021-03-11","2021-03-12"]
    bars=np.stack([artificial_m1(seed=20261029+i)[0] for i in range(3)])
    source={"years_opened":[2020,2021,2022],
            "holdout_2025_opened":False,"holdout_2026_opened":False,
            "complete_rth_sessions":3,"partial_sessions_excluded":0,
            "members_opened":15}
    return dates,bars,source

class TestV35ISTExternalOracle(unittest.TestCase):
    def test_independent_11_names_66_comparisons(self):
        d,b,meta=sample()
        report=qa.compare_selected_ist(d,b,meta)
        self.assertEqual(len(report["compared_formula_names"]),11)
        self.assertEqual(report["external_formula_comparisons"],66)
        self.assertEqual(report["error_categories"],{})
        self.assertFalse(report["financial_metrics_or_fitness_computed"])
        self.assertFalse(report["strategies_or_signals_evaluated"])
        self.assertFalse(report["ninjatrader_parity_completed"])
        self.assertEqual(report["formal_quality_gates_passed"],0)

    def test_prohibit_reserved_years(self):
        d,b,meta=sample()
        for year in ("2023","2024","2025","2026"):
            day=d.copy()
            day[-1]=year+"-03-12"
            with self.subTest(year=year),self.assertRaises(PermissionError):
                qa.compare_selected_ist(day,b,meta)

    def test_fail_closed_on_untrusted_archive_before_zip_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"not_provenanced.zip"
            path.write_bytes(b"unauthorized")
            with self.assertRaises(PermissionError):
                qa.audit_archive(path)

    def test_missing_source_claim_refused(self):
        d,b,meta=sample()
        with self.assertRaises(PermissionError):
            qa.compare_selected_ist(d,b,dict(meta,holdout_2025_opened=True))

if __name__=="__main__":
    unittest.main()
