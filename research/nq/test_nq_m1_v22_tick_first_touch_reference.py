"""NQ tick first-touch causal fixture tests only; no private Last files."""
import unittest
from research.nq import nq_m1_v22_tick_first_touch_reference as t


class TestSyntheticNQTickVsOHLC(unittest.TestCase):
    def test_tp_first_can_differ_from_conservative_ohlc_stop_first(self):
        # Time-ordered Last ticks: target 105 touched before stop 95.
        ticks=[(0,100.00),(1,102.00),(2,105.00),(3,100.00),(4,95.00)]
        x=t.tick_barrier(ticks,1,95.00,105.00,0,"2021-06-15")
        self.assertEqual(x["result"],"TARGET")
        self.assertEqual(t.ohlc_stop_first(105,95,1,95,105),"STOP")
        self.assertIsNone(x["economic_result"])

    def test_stop_first_reconciles_with_ohlc(self):
        ticks=[(0,100.00),(1,99.00),(2,95.00),(3,105.00)]
        x=t.tick_barrier(ticks,1,95.00,105.00,0,"2021-06-15")
        self.assertEqual(x["result"],"STOP")
        self.assertEqual(t.ohlc_stop_first(105,95,1,95,105),"STOP")

    def test_short_target_first_and_stop_first_differ(self):
        ticks=[(0,100.00),(1,95.00),(2,105.00)]
        x=t.tick_barrier(ticks,-1,105.00,95.00,0,"2021-06-15")
        self.assertEqual(x["result"],"TARGET")
        self.assertEqual(t.ohlc_stop_first(105,95,-1,105,95),"STOP")

    def test_entry_timestamp_excludes_prefill_barrier_prints(self):
        ticks=[(0,105.00),(1,100.00),(2,101.00)]
        x=t.tick_barrier(ticks,1,95.00,105.00,1,"2021-06-15")
        self.assertEqual(x["result"],"NO_BARRIER_TOUCHED")
        self.assertEqual(x["ticks_examined_after_entry"],1)

    def test_gap_at_stop_detects_first_adverse_last_not_favorable_stop(self):
        x=t.tick_barrier([(0,100.00),(1,94.75)],1,95.00,105.00,0,"2021-06-15")
        self.assertEqual(x["result"],"STOP")
        self.assertEqual(x["first_last_price"],94.75)

    def test_monotonic_strict_atomic_tick_timestamps(self):
        with self.assertRaises(ValueError):
            t.tick_barrier([(1,100.00),(1,95.00)],1,95.00,105.00,0,"2021-06-15")

    def test_bad_barriers_and_instrument_grid_rejected(self):
        with self.assertRaises(ValueError):
            t.tick_barrier([(0,100.00),(1,95.00)],1,95.125,105.00,0,"2021-06-15")
        with self.assertRaises(ValueError):
            t.tick_barrier([(0,100.00),(1,95.00)],2,95,105,0,"2021-06-15")

    def test_no_2023_24_25_26(self):
        for year in (2023,2024,2025,2026):
            with self.assertRaises(PermissionError):
                t.tick_barrier([],1,95.,105.,0,f"{year}-06-15")


if __name__=="__main__":
    unittest.main()
