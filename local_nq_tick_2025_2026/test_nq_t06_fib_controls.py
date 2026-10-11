import unittest
from qc_tick_day import check_day,utc_bounds
from nq_tick_short_horizon import STEP_100NS
from nq_t05_fibonacci_bars import filters_for_signals
from nq_t06_fib_controls import context_flags,select_families,FAMILIES

DAY='2025-10-15'
T=utc_bounds(check_day(DAY))[0]
SIGNAL=(1200,1)
CUTOFF=T+(SIGNAL[0]+1)*STEP_100NS

def events(n=1600):
    return [(CUTOFF-5000000+i*100,100+(i//250)*3+(i%7),1) for i in range(n)]

class TestT06PreregisteredControl(unittest.TestCase):
    def test_preserves_parent_and_four_explicit_counts(self):
        v=context_flags(events(),DAY,[SIGNAL])
        self.assertEqual(set(v[0]),{233,250,377,400})
        selected=select_families([SIGNAL],v)
        self.assertEqual(len(selected['T02_PARENT']),1)
        self.assertEqual(tuple(selected),FAMILIES)
    def test_233_377_flags_same_as_prior_T05(self):
        x=events()
        old=filters_for_signals(x,DAY,[SIGNAL])[0]
        new=context_flags(x,DAY,[SIGNAL])[0]
        self.assertEqual(old,(new[233],new[377]))
    def test_no_partial_bar(self):
        self.assertTrue(all(not a for a in context_flags(events(100),DAY,[SIGNAL])[0].values()))
    def test_same_time_and_future_data_not_used(self):
        x=events()
        a=context_flags(x,DAY,[SIGNAL])
        b=context_flags(x+[(CUTOFF,999,1)]*1000,DAY,[SIGNAL])
        self.assertEqual(a,b)
    def test_volume_not_a_tick_count(self):
        x=events()
        y=[(ts,price,10000) for ts,price,_ in x]
        self.assertEqual(context_flags(x,DAY,[SIGNAL]),context_flags(y,DAY,[SIGNAL]))
    def test_validation_and_sealed_blocked_before_reads(self):
        class Bomb:
            def __len__(self):raise AssertionError('sealed source read')
        for day in ('2026-05-01','2026-06-16','2026-07-01'):
            with self.assertRaises(ValueError):context_flags(Bomb(),day,[SIGNAL])
    def test_invalid_side_rejected(self):
        with self.assertRaises(ValueError):context_flags(events(),DAY,[(1200,0)])
    def test_missing_flags_rejected(self):
        with self.assertRaises(ValueError):select_families([SIGNAL],[])
    def test_source_order_guard(self):
        x=events();x[2],x[3]=x[3],x[2]
        with self.assertRaises(ValueError):context_flags(x,DAY,[SIGNAL])
if __name__=='__main__':unittest.main()
