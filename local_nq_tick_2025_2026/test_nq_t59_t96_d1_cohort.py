"""Synthetic full-family D1 gates, not live market tests."""
import json,unittest
from pathlib import Path

from nq_t59_t96_d1_cohort import d0_gate,bh38,one_day,aggregate,N_FAMILY,IDS
from nq_t61_t96_d0_cohort import load_registry
from test_nq_t61_t96_d0_cohort import DAY,sample
from nq_b05h01_trade_expansion_month import et_edge

class D1CohortBatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg=load_registry()
    def test_frozen_38_d0_qc_gate(self):
        r=d0_gate()
        self.assertEqual((r['D0_testable_count'],r['D0_diverse_count']),(36,31))
        self.assertEqual(len(r['all_ids']),38)
    def test_family_cannot_drop_two_low_power(self):
        with self.assertRaises(ValueError):bh38([.05]*36)
        self.assertEqual(bh38([.001]+[1.]*37)[0],.038)
    def test_no_future_horizon_truncation_as_success(self):
        e=sample()
        with self.assertRaises(ValueError):
            one_day(e,DAY,self.reg)
    def test_no_partial_7_month_aggregate(self):
        with self.assertRaises(ValueError):
            aggregate({},self.reg,d0_gate())
    def test_sealed_labels_still_part_of_full_family(self):
        a=d0_gate()['case_control_other_missing']
        self.assertEqual((a['T60']['CASE'],a['T60']['CONTROL']),(71,6))
        self.assertEqual((a['T77']['CASE'],a['T77']['CONTROL']),(119,12))
    def test_BH38_all_p_even_nonestimable_sentinels(self):
        p=[1.]*38
        p[2]=.01
        self.assertAlmostEqual(bh38(p)[2],.38,places=6)
    def test_no_money_claim_even_in_synthetic(self):
        self.assertEqual(N_FAMILY,38)
        self.assertIn('T59',IDS)
        self.assertIn('T96',IDS)
if __name__=='__main__':unittest.main()
