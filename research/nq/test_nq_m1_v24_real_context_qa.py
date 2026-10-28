"""Synthetic-only fixtures for private IST real-context QC. No ZIP or PnL."""
import unittest
import numpy as np
from research.nq.nq_m1_v24_real_context_qa import check_selected_sessions

def _day(price: float=10000.) -> np.ndarray:
    b=np.zeros((390,5), dtype=float)
    b[:,0]=price
    b[:,1]=price+1.
    b[:,2]=price-1.
    b[:,3]=price
    b[:,4]=100.
    return b

class TestActualContextTechnicalQA(unittest.TestCase):
    def test_three_synthetic_sessions_three_contexts(self):
        dates=["2020-01-02","2020-01-03","2020-01-06"]
        data=np.stack((_day(),_day(10000.25),_day(10000.50)))
        result=check_selected_sessions(dates,data)
        self.assertEqual(result["selected_contexts"],3)
        self.assertEqual(result["indicator_context_comparisons"],45)
        self.assertEqual(result["future_bar_mutation_checks"],30)
        self.assertEqual(result["roll_boundaries"],0)
        self.assertTrue(result["holdouts"]=="SEALED")
        self.assertFalse(result["signals_or_trades_evaluated"])
        self.assertFalse(result["pnl_or_fills_evaluated"])

    def test_roll_boundary_resets_context(self):
        dates=["2020-03-11","2020-03-12","2020-03-13"]
        data=np.stack((_day(),_day(10010.),_day(10011.)))
        result=check_selected_sessions(dates,data)
        self.assertEqual(result["roll_boundaries"],1)
        self.assertEqual(result["selected_contexts"],3)

    def test_mismatched_lengths_rejected(self):
        with self.assertRaises(ValueError):
            check_selected_sessions(["2020-01-02"],np.stack([_day()]*3))

    def test_reserved_year_rejected_without_prices(self):
        with self.assertRaises(PermissionError):
            check_selected_sessions(["2020-01-02","2023-01-03","2025-01-02"],
                                    np.stack([_day()]*3))

if __name__=="__main__":
    unittest.main()
