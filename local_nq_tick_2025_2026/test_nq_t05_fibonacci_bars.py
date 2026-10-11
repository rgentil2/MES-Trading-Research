import unittest
from qc_tick_day import utc_bounds,check_day
from nq_tick_short_horizon import STEP_100NS
from nq_t05_fibonacci_bars import filters_for_signals,selected_families,FAMILIES

DAY='2025-10-15'
LO=utc_bounds(check_day(DAY))[0]
I=1200
CUTOFF=LO+(I+1)*STEP_100NS

def event_bars_233_reversal_377_older_trend():
    # 932 Last trades before signal: 4 complete 233 bars + 2 complete 377 bars
    first=CUTOFF-1000000
    out=[]
    for k in range(932):
        p=250
        if k==376:p=300
        if k==753:p=200
        if k==698:p=190
        if k==931:p=210
        out.append((first+k*100,p,1))
    return out

class TestNQ233And377CountBars(unittest.TestCase):
    def test_233_reversal_plus_377_prior_downtrend(self):
        data=event_bars_233_reversal_377_older_trend()
        x=filters_for_signals(data,DAY,[(I,1)])
        self.assertEqual(x,[(True,True)])
        portfolios=selected_families([(I,1)],x)
        self.assertEqual(len(portfolios['T05_233_AND_377']),1)
        self.assertEqual(len(portfolios['T02_PARENT']),1)
    def test_inverse_side_not_both(self):
        x=filters_for_signals(event_bars_233_reversal_377_older_trend(),DAY,[(I,-1)])
        self.assertEqual(x,[(False,False)])
    def test_ticks_at_signal_close_cannot_update_past_bars(self):
        data=event_bars_233_reversal_377_older_trend()
        # Remaining data at cutoff should be unavailable to the decision
        data.extend((CUTOFF+j,999,1) for j in range(1000))
        self.assertEqual(filters_for_signals(data,DAY,[(I,1)]),[(True,True)])
    def test_incomplete_count_bar_is_not_a_signal(self):
        data=event_bars_233_reversal_377_older_trend()[:350]
        self.assertEqual(filters_for_signals(data,DAY,[(I,1)]),[(False,False)])
    def test_unsorted_events_rejected(self):
        data=event_bars_233_reversal_377_older_trend()
        data[500],data[501]=data[501],data[500]
        with self.assertRaises(ValueError):
            filters_for_signals(data,DAY,[(I,1)])
    def test_sealed_rejected_before_iterating(self):
        class Bomb:
            def __len__(self):raise AssertionError('Read sealed')
        with self.assertRaises(ValueError):
            filters_for_signals(Bomb(),'2026-07-01',[(I,1)])
    def test_monthly_validation_denied(self):
        for d in ('2026-05-01','2026-06-16','2026-07-01'):
            with self.assertRaises(ValueError):
                filters_for_signals([],d,[])
    def test_family_four_variants_no_frequency_invention(self):
        signals=[(I,1),(I+60,-1)]
        flags=[(True,False),(True,True)]
        out=selected_families(signals,flags)
        self.assertEqual(tuple(out),FAMILIES)
        self.assertEqual((len(out['T02_PARENT']),len(out['T05_233']),
                         len(out['T05_377']),len(out['T05_233_AND_377'])),
                         (2,2,1,1))
    def test_no_duplicate_flags(self):
        with self.assertRaises(ValueError):selected_families([(I,1)],[])
    def test_bar_count_not_volume_quantity(self):
        x=event_bars_233_reversal_377_older_trend()
        x=[(ts,px,999) for ts,px,_ in x]
        self.assertEqual(filters_for_signals(x,DAY,[(I,1)]),[(True,True)])

if __name__=='__main__':unittest.main()
