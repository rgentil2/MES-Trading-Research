"""NQ minute source integrity tests with internally manufactured fixtures."""
import unittest
import numpy as np
from research.nq import nq_m1_v32_real_ist_source_readonly_qa as q
from research.nq.nq_m1_v31_full_synthetic_lifecycle import artificial_m1

def sample():
    dates=["2021-03-10","2021-03-11","2021-03-12"]
    arrays=np.stack([artificial_m1(seed=20261028+i)[0] for i in range(3)])
    source=dict(years_opened=[2020,2021,2022],
                holdout_2025_opened=False,holdout_2026_opened=False,
                complete_rth_sessions=3,partial_sessions_excluded=0,
                members_opened=15)
    return dates,arrays,source

class TestV32(unittest.TestCase):
    def test_provenance(self):
        dates,arrays,source=sample()
        result=q.source_qa(dates,arrays,source,full_indicator_probe=False)
        self.assertEqual(result["roll_boundaries"],1)
        self.assertEqual(result["roll_contexts_confirmed_empty"],1)
        self.assertFalse(result["historical_strategy_backtest_executed"])

    def test_all_formula_paths(self):
        dates,arrays,source=sample()
        result=q.source_qa(dates,arrays,source)
        self.assertEqual(result["indicator_names_routed"],132)
        self.assertEqual(result["indicator_calls"],792)
        self.assertEqual(result["future_mutation_probes"],396)
        self.assertEqual(result["numerical_error_categories"],{})

    def test_future_years_rejected_by_source_boundary(self):
        dates,arrays,source=sample()
        for year in ("2023","2024","2025","2026"):
            bad=dates.copy()
            bad[-1]=year+"-03-12"
            with self.assertRaises(PermissionError):
                q.source_qa(bad,arrays,source,full_indicator_probe=False)

    def test_corrupted_ohlc_or_loader_provenance_rejected(self):
        dates,arrays,source=sample()
        wrong=arrays.copy()
        wrong[0,0,0]+=.125
        with self.assertRaises(ValueError):
            q.source_qa(dates,wrong,source,full_indicator_probe=False)
        wrong=arrays.copy()
        wrong[0,0,1]=wrong[0,0,2]-.25
        with self.assertRaises(ValueError):
            q.source_qa(dates,wrong,source,full_indicator_probe=False)
        with self.assertRaises(PermissionError):
            q.source_qa(dates,arrays,dict(source,holdout_2025_opened=True),
                        full_indicator_probe=False)
        with self.assertRaises(PermissionError):
            q.source_qa(dates,arrays,dict(source,complete_rth_sessions=2),
                        full_indicator_probe=False)

    def test_source_hash_rejects_unknown_input_before_zip_open(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"sample-source.zip"
            p.write_bytes(b"not-an-authorized-archive")
            with self.assertRaises(PermissionError):
                q.audit_archive(p)

    def test_duplicate_session_dates_are_rejected(self):
        dates,arrays,source=sample()
        dates[1]=dates[0]
        with self.assertRaises(ValueError):
            q.source_qa(dates,arrays,source,full_indicator_probe=False)

    def test_economic_gates_remain_closed(self):
        from research.nq.nq_m1_v22_quality_gate import audit
        x=audit()
        self.assertEqual(x["checks_total"],13)
        self.assertEqual(x["passed_verified"],0)
        self.assertEqual(x["decision"],"EXECUTION_BLOCKED")

if __name__=="__main__":
    unittest.main()
