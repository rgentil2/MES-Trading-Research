"""Synthetic D1 full-cohort 36 enforcement. No market data, no OOS."""
import unittest
from nq_t97_t132_d1_batch import d0_gate,bh36,one_day,aggregate,IDS
from nq_t97_t132_d0_batch import load_registry
from test_nq_t61_t96_d0_cohort import DAY,sample
from nq_b05h01_trade_expansion_month import et_edge

class T97D1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry=load_registry()
    def test_preregistered_D0_frozen_before_futures(self):
        d=d0_gate()
        self.assertEqual((d['family_size'],d['D0_testable_count'],d['D0_diverse_count']),(36,30,26))
        self.assertFalse(d['D1_executed'])
        self.assertEqual((d['source'],d['eligible']),(140,135))
    def test_BH_must_include_ALL36_including_low_power(self):
        with self.assertRaises(ValueError):bh36([.005]*30)
        self.assertAlmostEqual(bh36([.001]+[1.]*35)[0],.036)
    def test_sealed_D0_unidentifiable_still_in_family(self):
        z=d0_gate()['case_control_other_missing']
        self.assertEqual(z['T125']['CONTROL'],0)
        self.assertEqual(len(z),36)
        self.assertEqual(len(IDS),36)
    def test_D1_cannot_sample_truncated_future(self):
        with self.assertRaises(ValueError):
            one_day(sample(),DAY,self.registry)
    def test_one_day_future_only_changes_Y_not_D0_labels(self):
        e=sample()
        e=e+[(et_edge(DAY,10,7),100300,4)]
        r=one_day(e,DAY,self.registry)
        self.assertEqual(len(r),36)
        self.assertTrue(all(set(x)=={'group','value','side'} for x in r.values()))
        self.assertIsNone(r['T125']['value'] if r['T125']['group'] not in ('CASE','CONTROL') else None)
    def test_no_partial_aggregate_as_confirmation(self):
        with self.assertRaises(ValueError):
            aggregate({},self.registry,d0_gate())
if __name__=='__main__':unittest.main()
