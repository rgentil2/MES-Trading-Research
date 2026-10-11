import unittest
from qc_tick_day import check_day, utc_bounds
from qc_tick_to_minutes import audit_last_events,consolidate_bars,Bar,MINUTE_100NS
DAY="2025-10-15"
T=utc_bounds(check_day(DAY))[0]

class TestTickToMinuteSource(unittest.TestCase):
    def test_internal_ohlcv_volume_and_events(self):
        x=[(T,400,2),(T+100,401,3),
           (T+MINUTE_100NS,399,4),(T+5*MINUTE_100NS,405,2)]
        r=audit_last_events(x,DAY)
        self.assertEqual(r["ticks_last"],4)
        self.assertEqual(r["total_last_contracts"],11)
        self.assertEqual(r["minutes_with_last"],3)
        self.assertEqual(r["five_minutes_with_last"],2)
        self.assertTrue(r["cross_resolution_consistency"])
        self.assertEqual(r["independent_minute_source_comparison"],"NOT_PERFORMED_NO_AUTHORIZED_INDEPENDENT_NQ_MINUTE_SOURCE")
    def test_same_stamp_different_price_count(self):
        x=[(T,400,1),(T,401,1),(T,401,1)]
        r=audit_last_events(x,DAY)
        self.assertEqual(r["duplicate_timestamp_event_count"],2)
        self.assertEqual(r["same_timestamp_price_change_event_count"],1)
    def test_unordered_rejected(self):
        with self.assertRaisesRegex(ValueError,"out-of-order"):
            audit_last_events([(T+1,400,1),(T,400,1)],DAY)
    def test_zero_volume_rejected(self):
        with self.assertRaisesRegex(ValueError,"size"):
            audit_last_events([(T,400,0)],DAY)
    def test_negative_price_tick_rejected(self):
        with self.assertRaises(ValueError):
            audit_last_events([(T,-4,1)],DAY)
    def test_outside_window_rejected(self):
        with self.assertRaises(ValueError):
            audit_last_events([(T-1,400,1)],DAY)
    def test_empty_stream_rejected(self):
        with self.assertRaises(ValueError):
            audit_last_events([],DAY)
    def test_sealed_never_reads_input(self):
        class Bomb:
            def __iter__(self):raise AssertionError("read sealed market data")
        with self.assertRaises(ValueError):
            audit_last_events(Bomb(),"2026-07-01")
    def test_daylight_saving_window_stays_four_hours(self):
        from qc_tick_day import utc_bounds
        p,q=utc_bounds(check_day("2026-03-09"))
        self.assertEqual(q-p,4*60*60*10000000)
    def test_minute_aggregate_reconstructs_ohlc5(self):
        b={0:Bar(400,402,403,399,12,3,T,T+100),
           1:Bar(402,405,406,402,7,2,T+MINUTE_100NS,T+MINUTE_100NS+1)}
        x=consolidate_bars(b)
        self.assertEqual((x[0].first,x[0].last,x[0].high,x[0].low,x[0].qty,x[0].events),
                         (400,405,406,399,19,5))

if __name__=="__main__":unittest.main()
