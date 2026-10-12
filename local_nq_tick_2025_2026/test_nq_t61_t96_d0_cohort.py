"""Synthetic-only 38-member D0 batch tests. NO licensed market Last."""
import unittest
from fractions import Fraction as Q
from pathlib import Path

from nq_b05h01_trade_expansion_month import et_edge
from nq_t61_t96_d0_features import classify_day,bar_votes,summary,CASE,CONTROL,OTHER,MISSING
from nq_t61_t96_d0_cohort import (
    load_registry,month_stage,aggregate,shortlist,IDS,EXPECTED_BLOCKS)

DAY='2025-10-15'
def sample():
    # Exactly 5 complete bar candidates by shortly after 10:00.
    # Every timestamp whole; no post-E response as part of CASE label.
    def t(h,m):return et_edge(DAY,h,m)
    e=[
      (t(8,30),100000,2),(t(8,30)+200000,100008,4),
      (t(8,59),100006,3),(t(9,0),100002,2),
      (t(9,29),100012,4),(t(9,30),100010,3),
      (t(9,44),100005,3),(t(9,45),100009,3),
      (t(9,59),100012,4)]
    base=t(9,59)+440000000  # 09:59:44
    for i in range(2100):
        # 10ms timestamps; 2100 prints -> at least 5 complete bars
        ts=base+i*100000
        px=100000+(i//160)*3+(i%13)
        e.append((ts,px,(i%5)+1))
    return sorted(e)

class SixBlockD0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=load_registry()
    def test_36_stable_new_ids_six_blocks(self):
        self.assertEqual(len(self.r['hypotheses']),36)
        self.assertEqual(tuple(x['id'] for x in self.r['hypotheses']),
                         tuple(f'T{i}' for i in range(61,97)))
        self.assertEqual(len(EXPECTED_BLOCKS),6)
        self.assertEqual(len(IDS),38)
    def test_all_new_labels_are_d0_only(self):
        d=classify_day(sample(),DAY,self.r)
        self.assertEqual(len(d),36)
        self.assertTrue(set(d.values())<=set((CASE,CONTROL,OTHER,MISSING)))
        self.assertIn(d['T61'],(CASE,CONTROL,OTHER,MISSING))
    def test_post_anchor_events_do_not_change_any_vote(self):
        e=sample();expected=classify_day(e,DAY,self.r)
        future=(et_edge(DAY,10,30),100600,22)
        self.assertEqual(expected,classify_day(e+[future],DAY,self.r))
    def test_same_timestamp_tie_permutation(self):
        e=sample()
        # add one adjacent identical-timestamp pair before the final E bar
        ix=1500
        e[ix]=(e[ix][0],100111,2)
        e[ix+1]=(e[ix][0],99991,4)
        v=classify_day(e,DAY,self.r)
        e[ix],e[ix+1]=e[ix+1],e[ix]
        self.assertEqual(v,classify_day(e,DAY,self.r))
    def test_price_weight_exact_and_poc_tie_mean(self):
        x=[(1,100,2),(1,110,2),(2,110,1),(2,100,1)]
        s=summary(x)
        self.assertEqual(s['poc'],Q(105))
        self.assertEqual(s['vwap'],Q(105))
        self.assertEqual(len(s['groups']),2)
    def test_one_frozen_diversity_redundancy(self):
        r={'hypotheses':[
          {'id':'T61','block':EXPECTED_BLOCKS[0]},
          {'id':'T62','block':EXPECTED_BLOCKS[0]}]}
        q={'T61':{'N_case':30},'T62':{'N_case':30}}
        s,dup=shortlist(['T61','T62'],q,{'T61__T62':29},r)
        self.assertEqual(len(s),1)
        self.assertEqual(len(dup),1)
    def test_sealed_month_denied_before_IO(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/DO_NOT_READ'), '2026-09',self.r)
    def test_partial_month_aggregate_forbidden(self):
        with self.assertRaises(ValueError):aggregate({},self.r)
    def test_no_new_registry_including_hidden_holdout(self):
        reg=dict(self.r);reg['holdouts_opened']=True
        # basic validation is in load_registry using immutable JSON; no mutation
        self.assertTrue(reg['holdouts_opened'])
        self.assertFalse(self.r['holdouts_opened'])

if __name__=='__main__': unittest.main()
