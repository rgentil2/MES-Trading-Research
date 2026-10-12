import unittest
from datetime import date
from qc_tick_day import utc_bounds
from nq_b05h_atomic_print_bars import (
    LENGTHS,completed_bars_by_print_count,prior_completed_context)

DAY="2025-10-15"
LO=utc_bounds(date.fromisoformat(DAY))[0]
SECOND=10_000_000

def toy_source():
    # Same-time 235 print group MUST close first 233-minimum bar in one piece.
    rows=[]
    rows.extend([(LO+SECOND,400+i%3,1+i%5) for i in range(235)])
    rows.extend([(LO+2*SECOND,500+i%7,2) for i in range(378)])
    rows.extend([(LO+3*SECOND,600+i%9,3) for i in range(4190)])
    rows.extend([(LO+4*SECOND,700+i%11,1+i%7) for i in range(10960)])
    return rows

class B05HAtomicTests(unittest.TestCase):
    def test_invariant_bar_series_under_all_frozen_tie_permutations(self):
        events=toy_source()
        variants={}
        from nq_b05g_same_timestamp_month import tie_variants,VARIANTS
        transformed,_=tie_variants(events)
        for v in VARIANTS:
            variants[v]=completed_bars_by_print_count(transformed[v],DAY)
        for v in VARIANTS:
            self.assertEqual(variants[v],variants[VARIANTS[0]])
        self.assertEqual(set(variants[VARIANTS[0]]),set(LENGTHS))
    def test_overshoot_whole_timestamp_group_never_split(self):
        z=completed_bars_by_print_count(toy_source(),DAY,(233,377))
        b=z[233][0]
        self.assertEqual(b.prints,235)
        self.assertEqual(b.overshoot_prints,2)
        self.assertEqual(b.whole_timestamp_groups,1)
        self.assertEqual(b.start_timestamp,b.end_timestamp)
        self.assertEqual(b.total_qty,sum(x[2] for x in toy_source()[:235]))
    def test_vwap_is_exact_integer_ratio_not_arbitrary_close(self):
        e=[(LO+SECOND,100,2),(LO+SECOND,104,1),
           (LO+2*SECOND,102,3)]
        b=completed_bars_by_print_count(e,DAY,(2,))[2]
        self.assertEqual(b[0].prints,2)
        self.assertEqual((b[0].vwap_numerator,b[0].vwap_denominator),(304,3))
        self.assertEqual((b[0].low_ticks,b[0].high_ticks),(100,104))
        self.assertEqual(b[0].end_timestamp,LO+SECOND)
    def test_context_requires_prior_completed_bars_strictly_earlier(self):
        e=[(LO+SECOND,100,1),(LO+2*SECOND,200,1),
           (LO+3*SECOND,300,1),(LO+4*SECOND,400,1)]
        a=completed_bars_by_print_count(e,DAY,(1,))[1]
        self.assertIsNone(prior_completed_context(a,LO+2*SECOND))
        old=prior_completed_context(a,LO+3*SECOND)
        self.assertEqual([x.end_timestamp for x in old],
                         [LO+SECOND,LO+2*SECOND])
    def test_seconds_are_not_trigger_grid(self):
        e=[(LO+SECOND,100,1),(LO+15*SECOND,101,2),
           (LO+182*SECOND,103,3)]
        z=completed_bars_by_print_count(e,DAY,(2,))
        self.assertEqual(len(z[2]),1)
        self.assertEqual(z[2][0].start_timestamp,LO+SECOND)
        self.assertEqual(z[2][0].end_timestamp,LO+15*SECOND)
    def test_invalid_rows_and_unsorted_rejected(self):
        e=[(LO+2*SECOND,100,1),(LO+SECOND,101,2)]
        with self.assertRaises(ValueError):
            completed_bars_by_print_count(e,DAY,(2,))
        with self.assertRaises(ValueError):
            completed_bars_by_print_count([(LO+SECOND,100,0)],DAY,(1,))
        with self.assertRaises(ValueError):
            completed_bars_by_print_count([(LO+SECOND,100.2,1)],DAY,(1,))
        with self.assertRaises(ValueError):
            completed_bars_by_print_count([(LO+SECOND,100,1)],DAY,(1,1))
    def test_sealed_rejected_before_iterating_tick_source(self):
        class Bomb:
            def __iter__(self):
                raise AssertionError("sealed ticks opened")
        for day in ("2026-05-01","2026-06-02","2026-07-08",
                    "2025-09-01","2026-10-01"):
            with self.assertRaises(ValueError):
                completed_bars_by_print_count(Bomb(),day)

if __name__=="__main__":
    unittest.main()
