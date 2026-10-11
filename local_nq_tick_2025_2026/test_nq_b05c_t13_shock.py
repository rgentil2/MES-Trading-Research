"""T13 prereg causal Last qty shock/retrace: no lookahead and capacity guards."""
import unittest
from nq_b05c_t13_shock import impulse_signal,candidates_t13,FAMILIES,FIRST_SIGNAL
from nq_b05c_t13_month import shared_signals,analyze_month
from nq_b05c_t13_aggregate import aggregate

DAY="2025-10-15"
I=1440

def fixture():
    b=[[20000,20002,19998,20000,3,10] for _ in range(2880)]
    for k in range(I-6,I-2):
        b[k]=[20001,20019,19999,20016,4,30] # qty 30 x4 =120, >=80
    b[I-2]=[20016,20017,20010,20013,4,10]
    b[I-1]=[20013,20015,20008,20010,4,10]
    b[I]=[20010,20011,20005,20007,4,10] # shock 16, retrace 9 >=8
    return b

class T13Causality(unittest.TestCase):
    def test_shock_direction_qty_and_retrace(self):
        b=fixture()
        self.assertTrue(impulse_signal(b,I,-1))
        self.assertFalse(impulse_signal(b,I,1))
    def test_change_future_cannot_change_signal(self):
        b=fixture()
        result=impulse_signal(b,I,-1)
        b[I+1]=[1,1,1,1,100000,100000]
        self.assertEqual(result,impulse_signal(b,I,-1))
    def test_no_volume_control_differs_on_same_price_bars(self):
        b=fixture()
        for k in range(I-6,I-2):
            b[k][5]=1
        self.assertFalse(impulse_signal(b,I,-1))
        self.assertTrue(impulse_signal(b,I,-1,no_volume=True))
    def test_weak_retrace_control_differs(self):
        b=fixture()
        b[I]=[20015,20016,20012,20013,4,10] # 3 ticks against shock
        self.assertFalse(impulse_signal(b,I,-1))
        self.assertTrue(impulse_signal(b,I,-1,weak_retrace=True))
    def test_price_not_trade_count(self):
        b=fixture()
        b[I-3][3]=20011  # D becomes 11 price ticks < 12
        self.assertFalse(impulse_signal(b,I,-1))
    def test_missing_5_second_bar_fail_closed(self):
        b=fixture()
        b[I-5]=None
        self.assertFalse(impulse_signal(b,I,-1))
    def test_only_first_signal_of_day_per_family(self):
        b=fixture()
        for k in range(I+60,I+64):
            b[k]=[20001,20019,19999,20016,4,30]
        b[I+64]=[20016,20017,20010,20013,4,10]
        b[I+65]=[20013,20015,20008,20010,4,10]
        b[I+66]=[20010,20011,20005,20007,4,10]
        result,both=candidates_t13(b,DAY)
        self.assertEqual(both,0)
        self.assertEqual(set(result),set(FAMILIES))
        self.assertTrue(all(len(r)<=1 for r in result.values()))
        self.assertEqual(result['T13_FULL'],[(I,-1)])
    def test_t05_priority_at_same_bar(self):
        tagged,tied=shared_signals([(I,1),(I+12,-1)],[(I,-1)])
        self.assertEqual(tied,1)
        self.assertEqual(tagged,[(I,1,'T05_377'),(I+12,-1,'T05_377')])
    def test_holdout_rejected_before_root(self):
        class Poison:
            def __fspath__(self):raise AssertionError('Sealed root touched')
        with self.assertRaises(ValueError):analyze_month(Poison(),'2026-05')
        with self.assertRaises(ValueError):analyze_month(Poison(),'2026-07')
    def test_seven_month_aggregation_required(self):
        with self.assertRaises(ValueError):aggregate({})

if __name__=='__main__':unittest.main()
