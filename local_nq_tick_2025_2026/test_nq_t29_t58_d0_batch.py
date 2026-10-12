"""Synthetic G0/D0 contract test suite: no licensed market or future read."""
from __future__ import annotations
import json,unittest
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

from nq_b05h_atomic_print_bars import CompletedPrintBar
from nq_t29_t58_d0_features import (
    histogram_features,rolling_features,classify_features,
    CASE,CONTROL,OTHER,MISSING)
from nq_t29_t58_d0_batch import (
    load_registry,month_stage,aggregate,diverse_shortlist,REGISTRY,BLOCKS)

def small_bar(rows):
    return CompletedPrintBar(
      min_print_threshold=5,prints=len(rows),total_qty=sum(e[2] for e in rows),
      price_times_qty_ticks=sum(e[1]*e[2] for e in rows),
      high_ticks=max(e[1] for e in rows),low_ticks=min(e[1] for e in rows),
      start_timestamp=rows[0][0],end_timestamp=rows[-1][0],
      whole_timestamp_groups=len({e[0] for e in rows}))

class T29ToT58D0Safety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=load_registry()

    def test_complete_family_five_equal_blocks(self):
        self.assertEqual(len(self.r['hypotheses']),30)
        self.assertEqual([sum(x['block']==b for x in self.r['hypotheses'])
                          for b in BLOCKS],[6]*5)
        self.assertEqual(self.r['min_diversified_TESTABLE_before_D1'],20)

    def test_atomic_reordering_same_timestamp_invariant(self):
        rows=[(11,100,2),(11,100,1),(12,104,2),(12,108,1),
              (13,105,3),(13,105,2)]
        swap=[rows[1],rows[0],rows[3],rows[2],rows[5],rows[4]]
        features=histogram_features(rows,small_bar(rows))
        self.assertEqual(features,histogram_features(swap,small_bar(swap)))
        self.assertEqual(features['same_price_multifill_share'],Fraction(4,6))
        self.assertEqual(features['qty_per_print'],Fraction(11,6))

    def test_all_30_classifications_match_one_frozen_rule(self):
        features={x['feature'] for x in self.r['hypotheses']}
        mock=[{k:Fraction(i+1) for k in features} for i in range(5)]
        for f in mock:
            f.update({'_v':Fraction(100),'_bar_range':20,'_high':110,'_low':90})
        result=classify_features(mock,self.r)
        self.assertEqual(set(result),{x['id'] for x in self.r['hypotheses']})
        self.assertTrue(all(g in (CASE,CONTROL,OTHER,MISSING)
                            for g in result.values()))

    def test_missing_baseline_is_not_a_control(self):
        attr={x['feature'] for x in self.r['hypotheses']}
        mock=[{k:Fraction(0) for k in attr} for _ in range(5)]
        for f in mock:
            f.update({'_v':Fraction(100),'_bar_range':20,'_high':110,'_low':90})
        result=classify_features(mock,self.r)
        self.assertEqual(result['T29'],MISSING)

    def test_feature_context_has_no_future_endpoints(self):
        x=[{'_v':Fraction(i+1),'_bar_range':10,
            '_high':i+20,'_low':i+1} for i in range(5)]
        a,b=rolling_features(x)
        self.assertEqual(a['vwap_curvature'],Fraction(0))
        self.assertEqual(b['vwap_curvature'],Fraction(0))
        self.assertEqual(a['trend_sign_concordance'],Fraction(3))
        self.assertEqual(b['trend_sign_concordance'],Fraction(3))

    def test_locked_whitelist_sealed_month_rejected_before_io(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/NEVER_OPEN'),'2026-08',self.r)

    def test_partial_month_aggregate_denied(self):
        with self.assertRaises(ValueError):
            aggregate({},self.r)

    def test_no_registry_respecification(self):
        altered=deepcopy(self.r)
        altered['hypotheses'][0]['case_ratio_min']='1'
        p=Path('/tmp/t29_unsafe_test_registry.json')
        try:
            p.write_text(json.dumps(altered))
            with self.assertRaises(ValueError):
                load_registry(p)
        finally:
            p.unlink(missing_ok=True)

    def test_dedup_case_masks_deterministic(self):
        full={'T29':{'N_case':30},'T35':{'N_case':30},
              'T41':{'N_case':29}}
        inter={'T29__T35':30,'T29__T41':0,'T35__T41':0}
        selected,rejected=diverse_shortlist(['T29','T35','T41'],
                                             full,inter,self.r)
        self.assertEqual(selected,['T29','T41'])
        self.assertEqual(rejected['T35']['near_duplicate_of'],'T29')

    def test_no_new_data_permissions(self):
        self.assertFalse(self.r['new_history_acquisition'])
        self.assertFalse(self.r['new_five_second_signals'])
        self.assertFalse(self.r['holdouts_opened'])
        self.assertFalse(self.r['d1_authorized_now'])
        self.assertFalse(self.r['outcomes_read'])

if __name__=='__main__':
    unittest.main()
