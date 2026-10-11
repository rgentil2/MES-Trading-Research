import unittest
from qc_tick_day import check_day,utc_bounds
from nq_tick_short_horizon import STEP_100NS
from nq_t07_three_scale import SIZES,FAMILIES,flags_before_signals,split_signals
from nq_t05_fibonacci_bars import filters_for_signals

DAY='2025-10-15'
LOW=utc_bounds(check_day(DAY))[0]
SIGNAL=(1200,1)
END=LOW+(SIGNAL[0]+1)*STEP_100NS

def events(n=24000):
    return [(END-20000000+i*100,200+(i//4181)*3+(i%11),1) for i in range(n)]

class TestT07StrictPredeclaredContexts(unittest.TestCase):
    def test_frozen_scales(self):
        self.assertEqual(SIZES,(233,377,4181,10946,240,4200,11000))
    def test_prior_T05_233_377_flag_parity(self):
        x=events(1000)
        old=filters_for_signals(x,DAY,[SIGNAL])[0]
        new=flags_before_signals(x,DAY,[SIGNAL])[0]
        self.assertEqual(old,(new[0],new[1]))
    def test_source_quantity_not_number_of_bars(self):
        x=events(23000)
        bigqty=[(t,p,999) for t,p,q in x]
        self.assertEqual(flags_before_signals(x,DAY,[SIGNAL]),flags_before_signals(bigqty,DAY,[SIGNAL]))
    def test_equal_or_future_timestamp_no_lookahead(self):
        x=events(1000)
        a=flags_before_signals(x,DAY,[SIGNAL])
        b=flags_before_signals(x+[(END,999,1)]*20000,DAY,[SIGNAL])
        self.assertEqual(a,b)
    def test_incomplete_10946_unavailable(self):
        x=events(1200)
        self.assertFalse(flags_before_signals(x,DAY,[SIGNAL])[0][3])
    def test_five_locked_portfolios(self):
        chosen=split_signals([SIGNAL],[(True,)*7])
        self.assertEqual(tuple(chosen),FAMILIES)
        self.assertTrue(all(len(v)==1 for v in chosen.values()))
    def test_months_validation_and_sealed_rejected(self):
        class Bomb:
            def __len__(self):raise AssertionError('opened sealed market data')
        for d in ('2026-05-01','2026-06-02','2026-07-01'):
            with self.assertRaises(ValueError):flags_before_signals(Bomb(),d,[SIGNAL])
    def test_out_of_order_last_rejected(self):
        x=events(300);x[0],x[1]=x[1],x[0]
        with self.assertRaises(ValueError):flags_before_signals(x,DAY,[SIGNAL])
    def test_short_direction(self):
        x=events(22000)
        self.assertEqual(len(flags_before_signals(x,DAY,[(SIGNAL[0],-1)])[0]),7)
    def test_flag_length_mismatch(self):
        with self.assertRaises(ValueError):split_signals([SIGNAL],[])
if __name__=='__main__':unittest.main()
