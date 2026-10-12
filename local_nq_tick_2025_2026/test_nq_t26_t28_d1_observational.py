import unittest
from pathlib import Path
from nq_t26_t28_d1_observational import (
    EXPECTED,IDS,bh_three,aggregate,month_stage)
from nq_t20_t25_d1_atomic_markout import bootstrap_delta

class TestT26D1(unittest.TestCase):
    def test_predeclared_counts_all_three(self):
        self.assertEqual(EXPECTED[IDS[0]],(18,36))
        self.assertEqual(EXPECTED[IDS[1]],(6,65))
        self.assertEqual(EXPECTED[IDS[2]],(3,0))
    def test_BH_cannot_drop_sparse_family(self):
        self.assertEqual(bh_three([.01,1,1]),[.03,1,1])
        with self.assertRaises(ValueError):bh_three([.01])
    def test_not_estimable_with_six_cases(self):
        k=IDS[1]
        rows=[{k:{'group':'CASE','value':7.}} for _ in range(6)]
        rows += [{k:{'group':'CONTROL','value':2.}} for _ in range(65)]
        rows += [{k:{'group':'OTHER','value':None}} for _ in range(64)]
        s=bootstrap_delta(rows,k,5,repeats=20)
        self.assertIsNone(s['ci90'])
    def test_sealed_month_rejected_before_io(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/NOT_READ'),'2026-09',Path('/NOT_WRITTEN'))
    def test_incomplete_aggregate_denied(self):
        with self.assertRaises(ValueError):
            aggregate({})
    def test_no_confuse_trades_with_observations(self):
        self.assertEqual(sum(1 for k in IDS if EXPECTED[k][0]>=15 and EXPECTED[k][1]>=15),1)

if __name__=='__main__':unittest.main()
