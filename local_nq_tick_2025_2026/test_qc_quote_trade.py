import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qc_quote_trade import analyze_streams, source_paths
from qc_tick_day import check_day

DAY="2025-10-15"
T=17605296000000000

def stream(*events):
    return iter(events)

class TestQuoteTradeCausality(unittest.TestCase):
    def test_equal_timestamp_quotes_do_not_support_trade(self):
        report=analyze_streams([
            stream((T,"Last",101.0),(T+1,"Last",101.0)),
            stream((T,"Bid",100.75)),stream((T,"Ask",101.0))],day=DAY)
        n=report["counts"]
        self.assertEqual(n["last_rows"],2)
        self.assertEqual(n["last_without_prior_bbo"],1)
        self.assertEqual(n["last_positive_spread_fresh_le_250ms"],1)
        self.assertEqual(report["last_location_for_positive_bbo_le_250ms"]["at_ask"],1)
        self.assertTrue(report["classification_reconciles"])

    def test_updates_on_trade_timestamp_not_used(self):
        report=analyze_streams([
            stream((T+1,"Last",101.0),(T+2,"Last",102.0)),
            stream((T,"Bid",100.75),(T+1,"Bid",101.75)),
            stream((T,"Ask",101.0),(T+1,"Ask",102.0))],day=DAY)
        self.assertEqual(report["counts"]["last_sharing_timestamp_with_quote"],1)
        self.assertEqual(report["last_location_for_positive_bbo_le_250ms"]["at_ask"],2)

    def test_crossed_bid_ask_excluded(self):
        report=analyze_streams([stream((T+1,"Last",101.0)),
            stream((T,"Bid",101.25)),stream((T,"Ask",101.0))],day=DAY)
        self.assertEqual(report["counts"]["last_crossed_bbo"],1)
        self.assertEqual(report["counts"].get("last_positive_spread_fresh_le_250ms",0),0)

    def test_locked_bid_ask_excluded(self):
        report=analyze_streams([stream((T+1,"Last",101.0)),
            stream((T,"Bid",101.0)),stream((T,"Ask",101.0))],day=DAY)
        self.assertEqual(report["counts"]["last_locked_bbo"],1)

    def test_quote_age_uses_staler_side(self):
        report=analyze_streams([stream((T+3_000_001,"Last",101.0)),
            stream((T,"Bid",100.75)),stream((T+3_000_000,"Ask",101.0))],day=DAY)
        self.assertEqual(report["counts"]["last_positive_spread_stale_gt_250ms"],1)
        self.assertEqual(report["counts"].get("last_positive_spread_fresh_le_250ms",0),0)

    def test_same_timestamp_quote_updates_use_final_quote_after_time(self):
        report=analyze_streams([stream((T+1,"Last",101.0)),
            stream((T,"Bid",100.50),(T,"Bid",100.75)),
            stream((T,"Ask",101.0))],day=DAY)
        self.assertEqual(report["counts"]["bid_timestamps_with_multiple_prices"],1)
        self.assertEqual(report["spread_ticks_for_positive_bbo_le_250ms"]["1"],1)

    def test_no_holdout_reads_before_date_check(self):
        class Bomb:
            def __iter__(self): raise AssertionError("market streams accessed")
        with self.assertRaises(ValueError):
            analyze_streams([Bomb()],day="2026-07-01")

    def test_source_contract_agreement(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp)
            for kind,contract in (("Last","12-25"),("Bid","12-25"),("Ask","03-26")):
                p=base/("Tick_"+kind)
                p.mkdir()
                (p/f"NQ_{contract}_2025_20251015_Tick_{kind}_ET0800_1200.txt").touch()
            with self.assertRaisesRegex(ValueError,"contract mismatch"):
                source_paths(base,DAY)

if __name__=="__main__":
    unittest.main()
