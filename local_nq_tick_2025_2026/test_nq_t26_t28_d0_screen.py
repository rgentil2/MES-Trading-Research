import unittest
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from nq_b05h_atomic_print_bars import CompletedPrintBar
from nq_t26_t28_d0_screen import (
    IDS,CASE,CONTROL,OTHER,MISSING,grouped_atomic,metrics,classify,
    month_stage,aggregate)

def feature(chop=Fraction(1),vwap=Fraction(100),
            mean=Fraction(100),cv2=Fraction(2),width=20,groups=50):
    return {'chop':chop,'vwap':vwap,'print_mean':mean,
            'cv2':cv2,'width':width,'n_groups':groups}

class T26ToT28D0Tests(unittest.TestCase):
    def test_exact_three_distinct_members(self):
        self.assertEqual(len(IDS),3)
        self.assertEqual(len(set(IDS)),3)

    def test_t26_path_efficiency_case_control_and_other(self):
        d=feature(chop=Fraction(2))
        self.assertEqual(classify(d,feature(chop=Fraction(4)))[IDS[0]],
                         (CASE,0))
        self.assertEqual(classify(d,feature(chop=Fraction(2)))[IDS[0]],
                         (CONTROL,0))
        self.assertEqual(classify(d,feature(chop=Fraction(5,2)))[IDS[0]],
                         (OTHER,0))
        self.assertEqual(classify(d,feature(width=0))[IDS[0]],(MISSING,0))

    def test_t27_volume_price_premium_case_control_and_other(self):
        d=feature(vwap=Fraction(100))
        self.assertEqual(classify(d,feature(vwap=Fraction(110),mean=Fraction(106)))[IDS[1]],
                         (CASE,+1))
        self.assertEqual(classify(d,feature(vwap=Fraction(90),mean=Fraction(94)))[IDS[1]],
                         (CASE,-1))
        self.assertEqual(classify(d,feature(vwap=Fraction(110),mean=Fraction(110)))[IDS[1]],
                         (CONTROL,+1))
        self.assertEqual(classify(d,feature(vwap=Fraction(102),mean=Fraction(99)))[IDS[1]],
                         (OTHER,0))
        self.assertEqual(classify(d,feature(vwap=Fraction(110),mean=Fraction(114)))[IDS[1]],
                         (OTHER,0))

    def test_t28_bursty_vs_smooth_and_missing(self):
        d=feature()
        self.assertEqual(classify(d,feature(cv2=Fraction(5)))[IDS[2]],(CASE,0))
        self.assertEqual(classify(d,feature(cv2=Fraction(1)))[IDS[2]],(CONTROL,0))
        self.assertEqual(classify(d,feature(cv2=Fraction(2)))[IDS[2]],(OTHER,0))
        self.assertEqual(classify(d,feature(groups=29))[IDS[2]],(MISSING,0))

    def test_timestamp_group_reordering_is_invariant(self):
        a=[(11,100,2),(11,110,1),(12,105,2),
           (13,120,1),(13,100,3)]
        b=[a[1],a[0],a[2],a[4],a[3]]
        self.assertEqual(grouped_atomic(a),grouped_atomic(b))
        bar=CompletedPrintBar(min_print_threshold=5,prints=5,total_qty=9,
             price_times_qty_ticks=2*100+110+2*105+120+3*100,
             high_ticks=120,low_ticks=100,start_timestamp=11,end_timestamp=13,
             whole_timestamp_groups=3)
        self.assertEqual(metrics(a,bar),metrics(b,bar))
        self.assertGreater(metrics(a,bar)['chop'],0)

    def test_incomplete_atomic_group_denied(self):
        rows=[(11,100,1),(11,102,1)]
        bar=CompletedPrintBar(3,3,3,304,102,100,11,11,1)
        with self.assertRaises(AssertionError):
            metrics(rows,bar)

    def test_negative_unsorted_timestamp_denied(self):
        with self.assertRaises(ValueError):
            grouped_atomic([(12,100,1),(11,100,1)])

    def test_sealed_month_denied_before_any_market_io(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/DO_NOT_READ'),"2026-09")

    def test_reject_noncomplete_7_month_aggregate(self):
        with self.assertRaises(ValueError):
            aggregate({})

    def test_feature_classification_has_no_future_or_pnl(self):
        x=classify(feature(),feature())
        self.assertEqual(set(x),set(IDS))
        self.assertNotIn('P&L',x)
        self.assertTrue(all(isinstance(g,tuple) and len(g)==2 for g in x.values()))

if __name__=='__main__':
    unittest.main()
