"""Synthetic tests ONLY; no licensed Last or sealed period opened."""
import unittest
from pathlib import Path
from nq_t29_t58_d1_batch import (
    EXPECTED,EXPECTED_PAIRS,bh_frozen_family,month_stage,aggregate,load_registry)
from nq_t20_t25_d1_atomic_markout import bootstrap_delta

class TestT29T58D1(unittest.TestCase):
    def test_thirty_frozen_pairs_and_ids(self):
        self.assertEqual(len(EXPECTED),30)
        self.assertEqual(len(EXPECTED_PAIRS),30)
        self.assertEqual(EXPECTED['T29'],(80,31))
        self.assertEqual(EXPECTED['T58'],(58,58))

    def test_BH_requires_full_30_and_preserves_missing_sentinel(self):
        with self.assertRaises(ValueError): bh_frozen_family([0.01]*25)
        q=bh_frozen_family([0.01,0.02]+[1.]*28)
        self.assertAlmostEqual(q[0],.3)
        self.assertAlmostEqual(q[1],.3)
        self.assertEqual(q[-1],1.)

    def test_no_pvalue_for_five_cases(self):
        k='T50'
        rows=[{k:{'group':'CASE','side':0,'value':35.}} for _ in range(14)]
        rows+=[{k:{'group':'CONTROL','side':0,'value':25.}} for _ in range(93)]
        rows+=[{k:{'group':'OTHER','side':0,'value':None}} for _ in range(28)]
        self.assertEqual(len(rows),135)
        out=bootstrap_delta(rows,k,5,repeats=20)
        self.assertIsNone(out['p_exploratory'])
        self.assertEqual(out['reason'],'LOW_GROUP_N')

    def test_zero_outcome_group_not_falsely_zero_return(self):
        k='T29'
        rows=[{k:{'group':'CASE','side':0,'value':33.}} for _ in range(60)]
        rows+=[{k:{'group':'CONTROL','side':0,'value':20.}} for _ in range(35)]
        rows+=[{k:{'group':'OTHER','side':0,'value':None}} for _ in range(40)]
        out=bootstrap_delta(rows,k,5,repeats=30)
        self.assertIsNone(out['reason'])
        self.assertAlmostEqual(out['ci90'][0],13.)
        self.assertAlmostEqual(out['ci90'][1],13.)

    def test_sealed_month_rejected_before_io(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/DO_NOT_READ'), '2026-08',
                        Path('/DO_NOT_WRITE'),load_registry())

    def test_aggregate_requires_seven_months_and_all_30(self):
        with self.assertRaises(ValueError):
            aggregate({},load_registry())

    def test_no_future_or_funding_in_source_prereg(self):
        x=load_registry()
        self.assertIs(x['d1_authorized_now'],False)
        self.assertIs(x['new_history_acquisition'],False)
        self.assertIs(x['holdouts_opened'],False)

if __name__=='__main__':
    unittest.main()
