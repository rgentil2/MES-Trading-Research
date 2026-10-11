"""Synthetic tests for segmented BBO dislocation; no private tick files."""
import unittest
from datetime import datetime, timezone
from qc_bbo_dislocation import aggregate_events, classify, window_edges

DAY="2025-10-15"
def stamp(h,m,ms=0):
    dt=datetime(2025,10,15,h,m,tzinfo=timezone.utc)
    return int(dt.timestamp())*10000000 + ms*10000
def st(*args):return iter(args)

class TestSegmentedDislocation(unittest.TestCase):
    def test_same_time_update_not_prior(self):
        t=stamp(13,30)
        r=aggregate_events([st((t+10000,"Last",102.0)),
            st((t,"Bid",100.0),(t+10000,"Bid",101.75)),
            st((t,"Ask",101.0),(t+10000,"Ask",102.25))],DAY)
        v=r["segments"]["open_0930_1000"]
        self.assertEqual(v["outside"],1)
        self.assertEqual(v["same_timestamp_alternative_NONCAUSAL"]["prior_outside_alt_inside"],1)
        self.assertEqual(v["age_thresholds_ms"]["50"]["outside"],1)

    def test_old_quotes_do_not_enter_fresh_age(self):
        t=stamp(13,30)
        r=aggregate_events([st((t+5000000,"Last",102.0)),
            st((t,"Bid",100.0)),st((t,"Ask",101.0))],DAY)
        v=r["segments"]["open_0930_1000"]
        self.assertEqual(v["age_thresholds_ms"]["250"]["n"],0)
        self.assertEqual(v["age_thresholds_ms"]["1000"]["n"],1)

    def test_time_windows_and_dst(self):
        t=stamp(13,30)
        r=aggregate_events([st((t-500000,"Last",101.0),(t+500000,"Last",101.0)),
            st((t-1000000,"Bid",100.0)),st((t-1000000,"Ask",101.0))],DAY)
        self.assertEqual(r["segments"]["pre_0800_0930"]["trades"],1)
        self.assertEqual(r["segments"]["open_0930_1000"]["trades"],1)
        from datetime import date
        j=[x for x in window_edges(date(2026,6,16)) if x[0]=="open_0930_1000"][0]
        d=datetime.fromtimestamp(j[1]/10000000,timezone.utc)
        self.assertEqual((d.hour,d.minute),(13,30))

    def test_sealed_guard(self):
        class Explode:
            def __iter__(self):raise AssertionError("accessed sealed")
        with self.assertRaises(ValueError):
            aggregate_events([Explode()],"2026-07-01")

    def test_zero_denominator_remains_unknown(self):
        r=aggregate_events([],DAY)
        self.assertIsNone(r["segments"]["open_0930_1000"]["outside_pct"])

    def test_crossed_and_locked_books_not_tradeable(self):
        self.assertEqual(classify(101,102,101),"invalid_book")
        self.assertEqual(classify(101,101,101),"invalid_book")

if __name__=="__main__":unittest.main()
