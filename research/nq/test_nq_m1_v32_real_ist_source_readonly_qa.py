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

if __name__=="__main__":
    unittest.main()
