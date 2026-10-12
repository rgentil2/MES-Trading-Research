"""Synthetic guards for preregistered 20 complete strategy plans. Never Last DEV."""
import unittest
from pathlib import Path
from fractions import Fraction as F
from nq_t133_t152_executable_d0_batch import (
    load_registry,month_stage,aggregate,diversity,IDS,BLOCKS)
from nq_t133_t152_executable_d0_features import (
    classify_day,plan_stop,CASE,CONTROL,OTHER,MISSING,LABELS)
from test_nq_t61_t96_d0_cohort import DAY,sample
from nq_b05h01_trade_expansion_month import et_edge

class TwentyCompletePlans(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=load_registry()
    def test_four_blocks_five_each_complete_plans(self):
        self.assertEqual(len(IDS),20)
        self.assertEqual(tuple(x['id'] for x in self.r['members']),IDS)
        self.assertEqual(BLOCKS,tuple(self.r['blocks']))
        self.assertEqual([sum(x['block']==b for x in self.r['members'])
            for b in BLOCKS],[5,5,5,5])
        for x in self.r['members']:
            self.assertGreater(x['take_profit_R'],1)
            self.assertIn(x['max_minutes'],(15,30))
            self.assertIn('UNVERIFIED',x['entry'])
    def test_all_20_labels_fully_at_same_anchor(self):
        a=classify_day(sample(),DAY,self.r)
        self.assertEqual(len(a),20)
        self.assertTrue(set(a.values())<=set(LABELS))
    def test_no_future_rows_affect_D0_trigger(self):
        e=sample()
        before=classify_day(e,DAY,self.r)
        after=classify_day(e+[(et_edge(DAY,10,35),101500,25)],DAY,self.r)
        self.assertEqual(before,after)
    def test_timestamp_tie_permutation_safe(self):
        e=sample()
        e[1460]=(e[1460][0],100144,3)
        e[1461]=(e[1460][0],99973,9)
        a=classify_day(e,DAY,self.r)
        e[1460],e[1461]=e[1461],e[1460]
        self.assertEqual(a,classify_day(e,DAY,self.r))
    def test_defined_stop_uses_prior_extremes(self):
        e={'lo':100,'hi':120}
        micro={'lo':96,'hi':124}
        ref={'lo':94,'hi':126}
        self.assertEqual(plan_stop('A_BREAKOUT_RETEST',1,e,micro,None),F(95))
        self.assertEqual(plan_stop('B_PULLBACK_CONTINUATION',-1,e,micro,None),F(125))
        self.assertEqual(plan_stop('C_FALSE_BREAK_REVERSAL',-1,e,micro,ref),F(127))
        self.assertEqual(plan_stop('D_REGIME_RISK_ROUTER',1,e,micro,None),F(99))
    def test_one_atomic_timestamp_can_fill_entire_233_without_loss(self):
        from nq_b05h_atomic_print_bars import completed_bars_by_print_count
        from nq_t133_t152_executable_d0_features import completed_summary
        tm=et_edge(DAY,10,3)
        rows=[(tm,100000+i%9,2) for i in range(240)]
        bar=completed_bars_by_print_count(rows,DAY,(233,))[233][0]
        self.assertEqual(bar.whole_timestamp_groups,1)
        s=completed_summary(rows,[tm]*len(rows),bar)
        self.assertEqual(s['duration100ns'],0)
        self.assertEqual(s['vwap'],F(bar.price_times_qty_ticks,bar.total_qty))
        self.assertEqual(s['open'],s['end'])
    def test_one_group_zero_duration_never_divides_by_zero(self):
        from nq_t133_t152_executable_d0_features import completed_summary
        from nq_b05h_atomic_print_bars import completed_bars_by_print_count
        tm=et_edge(DAY,10,1)
        rows=[(tm,100009,1) for _ in range(240)]
        bar=completed_bars_by_print_count(rows,DAY,(233,))[233][0]
        self.assertEqual(completed_summary(rows,[tm]*240,bar)['duration100ns'],0)

    def test_sealed_month_rejected_prior_to_io(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/never-used'), '2026-09',self.r)
    def test_seven_month_complete_gate(self):
        with self.assertRaises(ValueError):aggregate({},self.r)
    def test_redundant_case_sets_count_once(self):
        q={'T133':{'N_case':40},'T134':{'N_case':40}}
        r={'members':[{'id':'T133','block':BLOCKS[0]},
                      {'id':'T134','block':BLOCKS[0]}],
           'jaccard_cutoff':.85}
        s,dup=diversity(['T133','T134'],q,{'T133__T134':39},r)
        self.assertEqual(s,['T133'])
        self.assertIn('T134',dup)
    def test_unverified_real_money_restricted_to_future_phases(self):
        self.assertFalse(self.r['D0_may_read_future'])
        self.assertFalse(self.r['broker_fills_verified'])
        self.assertFalse(self.r['chronological_check_is_independent_OOS'])
        self.assertEqual(self.r['max_risk_usd_per_hypothetical_trade'],250)
        self.assertEqual(self.r['D1_min_diverse_testable'],20)
if __name__=='__main__':unittest.main()
