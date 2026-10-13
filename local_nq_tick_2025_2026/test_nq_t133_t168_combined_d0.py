"""Synthetic checks on complete 36 member cohort. Never fetch licensed data."""
import copy
import unittest
from pathlib import Path
from nq_t133_t168_combined_D0_batch import (
    load_new,frozen_seed,old_registry,OLD_IDS,NEW_IDS,IDS,MONTHS,
    month_stage,aggregate,diversity)
from nq_t153_t168_executable_d0_features import classify_day,LABELS
from nq_t133_t152_executable_d0_features import classify_day as old_day
from test_nq_t61_t96_d0_cohort import DAY,sample
from nq_b05h01_trade_expansion_month import et_edge

class Batch36(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o=old_registry();cls.n=load_new();cls.seed=frozen_seed()
    def test_frozen_preregistered_20_plus16(self):
        self.assertEqual(len(OLD_IDS),20);self.assertEqual(len(NEW_IDS),16)
        self.assertEqual(len(IDS),36)
        self.assertEqual(tuple(z['id'] for z in self.n['members']),NEW_IDS)
        self.assertEqual(len(set(z['block'] for z in self.n['members'])),4)
        self.assertEqual(self.n['whole_family_for_eventual_D1'],36)
    def test_synthetic_all_36_complete(self):
        sample_events=sample()
        a=old_day(sample_events,DAY,self.o)
        b=classify_day(sample_events,DAY,self.n)
        self.assertEqual(set(a),set(OLD_IDS))
        self.assertEqual(set(b),set(NEW_IDS))
        self.assertTrue(set(b.values())<=set(LABELS))
    def test_post_anchor_future_has_no_effect_in_d0(self):
        e=sample()
        before=classify_day(e,DAY,self.n)
        after=classify_day(e+[(et_edge(DAY,10,40),101234,999)],DAY,self.n)
        self.assertEqual(before,after)
    def test_same_timestamp_permutation_no_effect(self):
        e=sample()
        e[1450]=(e[1450][0],99999,11)
        e[1451]=(e[1450][0],100111,3)
        first=classify_day(e,DAY,self.n)
        e[1450],e[1451]=e[1451],e[1450]
        self.assertEqual(first,classify_day(e,DAY,self.n))
    def test_missing_reference_fails_closed_not_silent(self):
        r=copy.deepcopy(self.n)
        r['members'][0]['reference']='NOT_A_REAL_CONTEXT'
        with self.assertRaises(AssertionError):
            classify_day(sample(),DAY,r)
    def test_no_sealed_month_even_before_file_io(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/does-not-exist'),'2026-09',self.o,self.n)
    def test_aggregate_requires_seven_months(self):
        with self.assertRaises(ValueError):
            aggregate({},self.o,self.n,self.seed)
    def test_original_seed_baseline_t133_15_viable(self):
        self.assertEqual(self.seed['D0_diverse_count'],15)
        self.assertEqual(self.seed['case_control_other_missing']['T146']['CASE'],32)
        self.assertEqual(self.seed['case_control_other_missing']['T147']['CONTROL'],113)
    def test_cross_family_diversity_removes_redundant(self):
        q={'T133':{'N_case':50},'T153':{'N_case':50}}
        old={'members':[{'id':'T133','block':'A_BREAKOUT_RETEST'}]}
        new={'members':[{'id':'T153','block':'E_VWAP_COUNTERMOVE'}]}
        selected,dupes=diversity(['T133','T153'],q,{'T133__T153':49},new,old)
        self.assertEqual(selected,['T133']);self.assertIn('T153',dupes)
    def test_no_future_or_economic_results_in_registry(self):
        self.assertFalse(self.n['outcome_reads_in_D0'])
        self.assertFalse(self.n['broker_fills_claim'])
        self.assertFalse(self.n['chronological_sensitivity_is_OOS'])
        self.assertFalse(self.n['open_sealed_holdouts'])

if __name__=='__main__':unittest.main()
