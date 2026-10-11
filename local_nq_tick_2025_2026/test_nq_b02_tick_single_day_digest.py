"""B02 synthetic source-isolation/canonical OHLCV tests; no private ticks."""
import unittest
from datetime import date
from qc_tick_day import utc_bounds
from nq_b02_tick_single_day_digest import aggregate_events

class B02Tests(unittest.TestCase):
    def test_240_bar_normalization(self):
        lo,_=utc_bounds(date(2025,10,15))
        events=[]
        for minute in range(240):
            t=lo+minute*60*10000000
            events.append((t+10,400+minute,1))
            events.append((t+20,402+minute,2))
        result=aggregate_events(events)
        self.assertEqual(result['source_rows'],240)
        self.assertEqual(result['total_volume_contracts'],720)
        self.assertEqual(len(result['canonical_ohlcv_sha256']),64)
        self.assertFalse(result['raw_prices_emitted'])
    def test_selected_date_only_before_iterator(self):
        class Poison:
            def __iter__(self):raise AssertionError('Read sealed iterator')
        with self.assertRaises(ValueError):
            aggregate_events(Poison(),'2026-07-01')
        with self.assertRaises(ValueError):
            aggregate_events(Poison(),'2025-10-16')
    def test_missing_minute_fails(self):
        lo,_=utc_bounds(date(2025,10,15))
        with self.assertRaises(ValueError):
            aggregate_events([(lo+10,400,1)])
    def test_out_of_order_fails(self):
        lo,_=utc_bounds(date(2025,10,15))
        with self.assertRaises(ValueError):
            aggregate_events([(lo+100,400,1),(lo+50,400,1)])
if __name__=='__main__':unittest.main()
