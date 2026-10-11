"""No market data. Test NQ 233/4181/10946 multi-context bars versus controls."""
import unittest
from qc_tick_day import check_day,utc_bounds
from qc_nq_multiscale_tick_bars import Builder,analyze_events,summarize_month,FIB,ROUND,SCALES,MINUTE

DAY="2025-10-15"
T=utc_bounds(check_day(DAY))[0]

class TestMultiscaleResearchQC(unittest.TestCase):
    def test_trade_print_count_not_quantity(self):
        v=analyze_events(((T+i*10_000_000,400+i%3,7) for i in range(500)),DAY)
        self.assertEqual(v["last_print_rows"],500)
        self.assertEqual(v["scales"]["233"]["complete_bars_0800_1200"],2)
        self.assertEqual(v["scales"]["233"]["final_incomplete_events"],34)
        self.assertEqual(v["scales"]["4181"]["complete_bars_0800_1200"],0)
        self.assertFalse(v["tested_strategy_returns"])

    def test_bar_ohlc_and_volume_internal(self):
        b=Builder(3)
        self.assertIsNone(b.add(T,100,10))
        self.assertIsNone(b.add(T+1,102,2))
        done=b.add(T+2,99,4)
        self.assertEqual(done[0],2/10000000)
        self.assertEqual((b.o,b.h,b.l,b.c,b.qty),(100,102,99,99,16))
        self.assertEqual(b.count,0)

    def test_open_snapshot_does_not_use_bar_completed_exactly_at_open(self):
        events=[(T+i,400,1) for i in range(232)]
        events.append((T+90*MINUTE,400,1))
        v=analyze_events(events,DAY)
        self.assertFalse(v["scales"]["233"]["closed_context_exists_at_0930_1030_1130"][0])
        self.assertTrue(v["scales"]["233"]["closed_context_exists_at_0930_1030_1130"][1])

    def test_bars_reset_counts_and_duplicate_boundary(self):
        b=Builder(2)
        b.add(T,400,1)
        duration,duplicates=b.add(T,401,1)
        self.assertEqual(duplicates,1)
        b.add(T,402,1)
        self.assertEqual(b.same,0)  # first print of next bar is not a within-bar duplicate

    def test_out_of_scope_before_stream_read(self):
        class Bomb:
            def __iter__(self): raise AssertionError("sealed data accessed")
        with self.assertRaises(ValueError):analyze_events(Bomb(),"2026-07-01")

    def test_out_of_order_rejected(self):
        with self.assertRaisesRegex(ValueError,"Unordered"):
            analyze_events([(T+1,400,1),(T,400,1)],DAY)

    def test_bad_last_price_and_volume_rejected(self):
        with self.assertRaises(ValueError):analyze_events([(T,400,0)],DAY)
        with self.assertRaises(ValueError):analyze_events([(T,-1,1)],DAY)

    def test_missing_and_empty(self):
        with self.assertRaises(ValueError):analyze_events([],DAY)

    def test_frozen_counts_not_optimized(self):
        self.assertEqual(FIB,(233,4181,10946))
        self.assertEqual(ROUND,(240,4200,11000))
        self.assertEqual(len(SCALES),6)

    def test_aggregate_month_guard(self):
        with self.assertRaises(ValueError):summarize_month("2026-07",[])

    def test_does_not_claim_full_daily_context(self):
        v=analyze_events([(T,400,1)],DAY)
        self.assertFalse(v["full_daily_context_available"])
        self.assertFalse(v["raw_prices_emitted"])

if __name__=="__main__":unittest.main()
