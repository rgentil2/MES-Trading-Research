import unittest
from collections import Counter
from datetime import date
from qc_tick_day import utc_bounds
from nq_tick_short_horizon import STEP_100NS
from nq_t05_fibonacci_bars import filters_for_signals
from nq_b05g_same_timestamp_month import VARIANTS,tie_variants,run_month

DAY='2025-10-15'
LO=utc_bounds(date.fromisoformat(DAY))[0]
INDEX=1200
CUTOFF=LO+(INDEX+1)*STEP_100NS

class B05GTests(unittest.TestCase):
    def test_preserve_exact_multiset_and_cross_timestamp_order(self):
        a=[(1,100,2),(1,101,1),(1,100,4),(2,95,3),
           (3,102,8),(3,105,1),(3,100,2)]
        out,stats=tie_variants(a)
        self.assertEqual(out[VARIANTS[0]],a)
        for v in VARIANTS:
            self.assertEqual(Counter(out[v]),Counter(a))
            self.assertEqual([r[0] for r in out[v]],[r[0] for r in a])
            self.assertEqual(sum(r[2] for r in out[v]),sum(r[2] for r in a))
        self.assertEqual(out[VARIANTS[1]][:3],list(reversed(a[:3])))
        self.assertEqual(out[VARIANTS[2]][:3],[(1,100,2),(1,100,4),(1,101,1)])
        self.assertEqual(out[VARIANTS[3]][:3],[(1,101,1),(1,100,2),(1,100,4)])
        self.assertEqual(stats['multi_print_groups'],2)
        self.assertEqual(stats['adjacent_same_ts_prints'],3)
        self.assertEqual(stats['multi_price_groups'],2)
    def test_keep_single_print_groups_unchanged(self):
        src=[(1,10,1),(2,20,99),(3,30,1)]
        variants,stats=tie_variants(src)
        self.assertTrue(all(z==src for z in variants.values()))
        self.assertEqual(stats['multi_print_groups'],0)
    def test_change_in_count_bar_close_is_just_sensitivity(self):
        # Two completed 377-print bars at two timestamps: original close
        # falls; descending price order may change the first bar close.
        src=[(CUTOFF-1000000,100,1)]*376
        src.extend([(CUTOFF-1000000,220,1)])
        src.extend([(CUTOFF-500000,100,1)]*377)
        variants,stats=tie_variants(src)
        chosen=[]
        for variant in VARIANTS:
            selected=filters_for_signals(variants[variant],DAY,[(INDEX,1)])
            chosen.append(selected[0][1])
        self.assertTrue(chosen[0])
        self.assertFalse(chosen[3])
        self.assertEqual(stats['adjacent_same_ts_prints'],752)
    def test_at_exact_signal_cutoff_not_available(self):
        src=[(CUTOFF-500000,100,1)]*754
        src.extend((CUTOFF,200,1) for _ in range(1000))
        out,_=tie_variants(src)
        original=filters_for_signals(out[VARIANTS[0]],DAY,[(INDEX,1)])
        reversed_=filters_for_signals(out[VARIANTS[1]],DAY,[(INDEX,1)])
        self.assertEqual(original,reversed_)
    def test_holdout_denied_before_file_access(self):
        class Bomb:
            def __getattr__(self,key):raise AssertionError('Accessed filesystem')
        with self.assertRaisesRegex(ValueError,'SEALED'):
            run_month(Bomb(),'2026-05')
        with self.assertRaisesRegex(ValueError,'SEALED'):
            run_month(Bomb(),'2026-09')

if __name__=='__main__':unittest.main()
