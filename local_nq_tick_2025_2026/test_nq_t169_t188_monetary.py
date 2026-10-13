#!/usr/bin/env python3
"""Synthetic checks BEFORE licensed DEV files are read."""
import unittest
from nq_b05h_atomic_print_bars import CompletedPrintBar as B
from nq_t169_t188_monetary_month import IDS,CODES,WINDOWS,choose,load_frozen,run_month

def bar(mid,width=12):
    return B(377,377,10,10*mid,mid+width//2,mid-width//2,1,2,1)

class TestT169T188(unittest.TestCase):
    def test_twenty_registered_without_retune(self):
        self.assertEqual(len(IDS),20)
        self.assertEqual(list(IDS),['T'+str(n) for n in range(169,189)])
        x=load_frozen()
        self.assertEqual(len(x['members']),20)
        self.assertEqual(len(WINDOWS),4)
        self.assertFalse(x['holdouts_opened'])

    def test_premarket_momentum_vs_reversion(self):
        self.assertEqual(choose('A_PRE_TREND',bar(105),bar(101),bar(98),[],None),1)
        self.assertEqual(choose('A_PRE_EXHAUST',bar(111),bar(100),bar(99),[],None),-1)
        self.assertEqual(choose('A_PRE_EXHAUST',bar(99),bar(100),bar(100),[],None),0)

    def test_macro_fade_opposite_to_gap(self):
        self.assertEqual(choose('B_OPEN_MACRO_FADE',bar(160),bar(100),bar(99),[],bar(100)), -1)
        self.assertEqual(choose('D_LATE_MACRO_FADE',bar(35),bar(100),bar(99),[],bar(100)), 1)

    def test_micro_disagreement(self):
        self.assertEqual(choose('C_MID_MICRO_DIVERGE',bar(110),bar(100),bar(99),
                        [bar(102),bar(96)],bar(100)),-1)
        self.assertEqual(choose('C_MID_MICRO_ALIGN',bar(110),bar(100),bar(99),
                        [bar(96),bar(102)],bar(100)),1)

    def test_late_large_revert(self):
        self.assertEqual(choose('D_LATE_LARGE_REVERT',bar(110,50),bar(100),bar(90),
                         [bar(95),bar(100)],bar(100)),-1)

    def test_all_codes_defined_and_no_unknown_trigger(self):
        self.assertEqual(len(set(CODES.values())),20)
        with self.assertRaises(ValueError):
            choose('NOT_PREREGISTERED',bar(105),bar(101),bar(98),[],None)

    def test_holdout_gate_before_filesystem(self):
        with self.assertRaises(ValueError):
            run_month(None,'2026-05')
        with self.assertRaises(ValueError):
            run_month(None,'2026-09')

if __name__=='__main__':unittest.main()
