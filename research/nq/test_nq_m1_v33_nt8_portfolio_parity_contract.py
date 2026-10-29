"""NQ S0.28 NinjaTrader-Python frozen portfolio parity: synthetic CSV protocol only."""
from copy import deepcopy
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo
import unittest

from research.nq import nq_m1_v33_nt8_portfolio_parity_contract as c
from research.nq.nq_h05_h07_level_volume_screen import roll_contract

def manifest(engine):
    return {"schema":c.SCHEMA,"evidence_mode":"ARTIFICIAL_PARITY_FIXTURE_ONLY",
            "engine":engine,"stage":c.ROOT,"source_zip_sha256":c.SOURCE_SHA256,
            "portfolio_sha256":"a"*64,"strategy_ast_bundle_sha256":"b"*64,
            "engine_code_sha256":"c"*64,"ninjatrader_ninjascript_sha256":"d"*64,
            "shared_portfolio_scheduler_sha256":"e"*64,
            "settings":deepcopy(c.EXPECTED_SETTINGS),
            "portfolio_frozen":False,"isv1_2023_opened":False,
            "isv2_2024_opened":False,"sealed_2025_2026_opened":False,
            "historical_backtest_authorized":False}

def stamp(d,hhmm):
    hh,mm=map(int,hhmm.split(":"))
    local=datetime.combine(date.fromisoformat(d),time(hh,mm),ZoneInfo("America/New_York"))
    return local.astimezone(timezone.utc).strftime(c.TIME_FMT)

def row(d="2021-02-02",seq=1,side="LONG",strategy_id="NQ26_"+"a"*16,
        entry="09:36",exit_="09:40",ep=20000.,xp=20001.,reason="TP"):
    net=(xp-ep)*(1 if side=="LONG" else -1)*20-4.68
    return {"session":d,"portfolio_sequence":str(seq),
            "strategy_id":strategy_id,"contract":roll_contract(date.fromisoformat(d)),
            "side":side,"quantity":"1","signal_time_utc":stamp(d,"09:35" if seq==1 else "09:44"),
            "entry_time_utc":stamp(d,entry),"exit_time_utc":stamp(d,exit_),
            "entry_price":str(ep),"exit_price":str(xp),
            "commission_usd":"4.68","net_usd":str(round(net,2)),"exit_reason":reason}

def compare(a=None,b=None):
    a=[row()] if a is None else a
    b=deepcopy(a) if b is None else b
    return c.compare(deepcopy(a),deepcopy(b),manifest("PYTHON"),manifest("NINJATRADER_8"))

class TestNQNT8ParityContract(unittest.TestCase):
    def test_synthetic_same_trade_pass_not_certification(self):
        r=compare()
        self.assertEqual(r["verdict"],"PASS_SYNTHETIC_FORMAT_AND_VALUES_ONLY")
        self.assertEqual(r["python"]["net_usd"],15.32)
        self.assertFalse(r["real_winner_portfolio_exists"])
        self.assertFalse(r["formal_funnel_or_parity_approval"])
        self.assertFalse(r["real_ninjatrader_strategy_analyzer_run_verified"])

    def test_two_sequential_portfolio_trades_do_not_overlap(self):
        a=[row(),row(seq=2,entry="09:45",exit_="09:50",
                     strategy_id="NQ26_"+"b"*16,side="SHORT",ep=20001,xp=20000)]
        r=compare(a)
        self.assertEqual(r["python"]["trades"],2)
        self.assertEqual(r["shared_trade_keys"],2)

    def test_pnl_and_fee_mismatch_detected_as_distinct_types(self):
        a=[row()]
        b=deepcopy(a);b[0]["commission_usd"]="5.68";b[0]["net_usd"]="14.32"
        r=compare(a,b)
        self.assertEqual(r["verdict"],"FAIL_DIFFERENCES_REQUIRE_INVESTIGATION")
        self.assertEqual(r["mismatch_categories"]["COSTS"],1)
        self.assertEqual(r["mismatch_categories"]["PNL_ARITHMETIC_OR_COSTS"],1)

    def test_entry_fill_and_exit_reason_categories(self):
        a=[row()]
        b=deepcopy(a);b[0]["entry_price"]="20000.25";b[0]["net_usd"]="10.32"
        b[0]["exit_reason"]="SL"
        r=compare(a,b)
        self.assertIn("ENTRY_FILL_PRICE",r["mismatch_categories"])
        self.assertIn("EXIT_LOGIC",r["mismatch_categories"])

    def test_missing_one_side_trade_fails(self):
        a=[row()]
        self.assertEqual(compare(a,[])["missing_in_ninjatrader"],1)
        self.assertEqual(compare([],a)["missing_in_python"],1)

    def test_two_empty_ledger_files_inconclusive_not_success(self):
        self.assertEqual(compare([],[])["verdict"],"INCONCLUSIVE_NO_TRADES")

    def test_future_periods_2023_to_2026_rejected(self):
        for year in (2023,2024,2025,2026):
            with self.subTest(year=year),self.assertRaises(PermissionError):
                compare([row(d=f"{year}-02-02")])

    def test_dst_ny_clock_exact_utc(self):
        a=row(d="2021-04-05")
        self.assertEqual(a["signal_time_utc"],"2021-04-05T13:35:00Z")
        self.assertEqual(a["contract"],"NQ_06-21")
        self.assertEqual(compare([a])["shared_trade_keys"],1)

    def test_non_nq_contract_or_untouched_roll_map_rejected(self):
        a=row();a["contract"]="NQ_06-21"
        with self.assertRaises(ValueError):
            compare([a])

    def test_utc_timezone_and_session_crossing_rejected(self):
        a=row();a["signal_time_utc"]="2021-02-02T09:35:00Z"
        with self.assertRaises(ValueError):
            compare([a])
        b=row();b["entry_time_utc"]="2021-02-02T14:36:00-05:00"
        with self.assertRaises(ValueError):
            compare([b])

    def test_bad_tick_price_and_bad_account_math_rejected(self):
        a=row();a["entry_price"]="20000.1"
        with self.assertRaises(ValueError):
            compare([a])
        b=row();b["net_usd"]="100000.00"
        with self.assertRaises(ValueError):
            compare([b])

    def test_strategies_cannot_overlap_shared_nq_account(self):
        a=[row(),row(seq=2,entry="09:38",exit_="09:44",
                     strategy_id="NQ26_"+"b"*16)]
        with self.assertRaises(ValueError):
            compare(a)

    def test_minute_entry_cutoff_and_late_signal_rejected(self):
        a=row(entry="11:30",exit_="11:31")
        with self.assertRaises(ValueError):
            compare([a])
        b=row();b["signal_time_utc"]=stamp("2021-02-02","11:29")
        b["entry_time_utc"]=stamp("2021-02-02","11:29")
        with self.assertRaises(ValueError):
            compare([b])

    def test_manifest_frozen_winner_and_later_year_gate_rejected(self):
        a=manifest("PYTHON")
        b=manifest("NINJATRADER_8")
        a["portfolio_frozen"]=True
        with self.assertRaises(PermissionError):
            c.compare([row()],[row()],a,b)
        a=manifest("PYTHON");a["isv1_2023_opened"]=True
        with self.assertRaises(PermissionError):
            c.compare([row()],[row()],a,b)

    def test_manifest_settings_change_is_not_silent(self):
        a=manifest("PYTHON");b=manifest("NINJATRADER_8")
        b["settings"]["fill_limit_orders_on_touch"]=True
        with self.assertRaises(ValueError):
            c.compare([row()],[row()],a,b)

    def test_different_portfolio_immutable_hash_rejected(self):
        a=manifest("PYTHON");b=manifest("NINJATRADER_8")
        b["portfolio_sha256"]="f"*64
        with self.assertRaises(ValueError):
            c.compare([row()],[row()],a,b)

    def test_wrong_quantity_and_position_sequence_rejected(self):
        a=row();a["quantity"]="2"
        with self.assertRaises(ValueError):
            compare([a])
        b=row(seq=2)
        with self.assertRaises(ValueError):
            compare([b])

    def test_price_difference_requires_full_explanation_not_forgiven_tick(self):
        a=[row()]
        b=deepcopy(a)
        b[0]["exit_price"]="20000.75"
        b[0]["net_usd"]="10.32"
        x=compare(a,b)
        self.assertEqual(x["mismatch_categories"]["EXIT_FILL_PRICE"],1)
        self.assertNotEqual(x["verdict"],"PASS_SYNTHETIC_FORMAT_AND_VALUES_ONLY")

    def test_no_double_count_for_same_session_sequence(self):
        a=[row(),row()]
        with self.assertRaises(ValueError):
            compare(a)

if __name__=="__main__":
    unittest.main()
