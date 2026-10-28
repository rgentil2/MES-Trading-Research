"""NQ shared-account artificial event invariants; no historical trading data."""
import unittest
from research.nq import nq_m1_v23_shared_account_event_qa as a

DAY="2021-06-15"
D2="2021-06-16"
def entry(s="A", idx=21, signal=20, price=20000., stop=19990., date=DAY, side=1):
    return {"date":date,"idx":idx,"kind":"ENTRY","strategy_id":s,
            "signal_idx":signal,"instrument":"NQ","contracts":1,
            "price":price,"stop":stop,"side":side}
def mark(idx=22,price=20002.,date=DAY):
    return {"date":date,"idx":idx,"kind":"MARK","instrument":"NQ",
            "contracts":1,"price":price}
def exit(idx=25,price=20005.,date=DAY,s="A",confirmed=False):
    return {"date":date,"idx":idx,"kind":"EXIT","strategy_id":s,
            "instrument":"NQ","contracts":1,
            "price":price,"stop_execution_confirmed":confirmed}


class TestOneNQEventBook(unittest.TestCase):
    def test_single_account_one_nq_priority_selection(self):
        x=a.replay([entry("B"),entry("A"),exit(s="A")],["A","B"])
        self.assertEqual(len(x["trades"]),1)
        self.assertEqual(x["trades"][0]["strategy_id"],"A")
        self.assertEqual(x["rejections"]["SAME_MINUTE_LOWER_PRIORITY"],1)
        self.assertEqual(x["trades"][0]["synthetic_net_usd"],75.32)
        self.assertEqual(x["status"],a.STATUS)
        self.assertFalse(x["actual_trades_backtested"])

    def test_risky_priority_intent_cannot_block_valid_second(self):
        events=[entry("A",stop=19980.),entry("B",stop=19990.),exit(s="B")]
        result=a.replay(events,["A","B"])
        self.assertEqual(result["rejections"]["NQ_INITIAL_RISK_CAP"],1)
        self.assertEqual([x["strategy_id"] for x in result["trades"]],["B"])
        # Exchanging future exit prices cannot change which order is accepted.
        other=a.replay(events[:-1]+[exit(s="B",price=19995.)],["A","B"])
        self.assertEqual(result["days"][0]["accepted_entry_intents"],
                         other["days"][0]["accepted_entry_intents"])

    def test_busy_position_and_max_two_entries(self):
        e=[entry("A"),entry("B",idx=22,signal=21),
           exit(25),
           entry("B",idx=27,signal=26),exit(29,price=20006.,s="B"),
           entry("A",idx=31,signal=30)]
        out=a.replay(e,["A","B"])
        self.assertEqual(out["days"][0]["entries"],2)
        self.assertEqual(out["rejections"]["SHARED_POSITION_BUSY"],1)
        self.assertEqual(out["rejections"]["MAX_ENTRIES_PER_DAY"],1)

    def test_marked_equity_is_not_realized_closed_profit(self):
        out=a.replay([entry("A"),mark(price=20012.),
                      exit(price=20005.)],["A"])
        t=out["trades"][0]
        self.assertEqual(t["mark_count"],1)
        self.assertEqual(t["synthetic_net_usd"],75.32)
        self.assertEqual(out["days"][0]["closed_pnl_usd"],75.32)
        self.assertLess(t["min_floating_equity"],50000.)

    def test_missing_stop_fill_is_not_silently_assumed(self):
        e=[entry(),mark(price=19985.),exit(price=19984.75)]
        with self.assertRaisesRegex(ValueError,"STOP_CROSSED"):
            a.replay(e,["A"])
        out=a.replay(e[:-1]+[exit(price=19984.75,confirmed=True)],["A"])
        self.assertTrue(out["trades"][0]["stop_crossed_unreconciled"])
        self.assertEqual(out["days"][0]["entries"],1)
        with self.assertRaisesRegex(ValueError,"Stop execution evidence"):
            a.replay([entry(),exit(confirmed=True)],["A"])

    def test_floating_soft_pause_and_hard_breach_are_distinct(self):
        e=[entry(),mark(price=19945.),exit(price=19945.,confirmed=True),
           entry("A",idx=27,signal=26)]
        result=a.replay(e,["A"])
        self.assertTrue(result["days"][0]["soft_pause_triggered"])
        self.assertFalse(result["hard_breach"])
        self.assertEqual(result["rejections"]["SOFT_EQUITY_PAUSE"],1)
        bad=[entry(),mark(price=19895.),exit(price=19895.,confirmed=True)]
        breached=a.replay(bad,["A"])
        self.assertTrue(breached["hard_breach"])
        self.assertTrue(breached["days"][0]["hard_breach_triggered"])
        with self.assertRaises(PermissionError):
            a.replay(bad+[entry(date=D2),exit(date=D2)],["A"])

    def test_eod_trailing_floor_updates_only_after_session_close(self):
        day1=[entry(),mark(price=20100.),
              exit(price=20051.25)]
        day2=[entry(date=D2),exit(date=D2,price=20100.)]
        r=a.replay(day1+day2,["A"])
        self.assertAlmostEqual(r["days"][0]["hard_floor_after_close"],49000.32)
        self.assertAlmostEqual(r["days"][1]["hard_floor_after_close"],50100.)
        self.assertFalse(r["official_account_plan_verified"])
        self.assertEqual(r["holdouts"],"SEALED")

    def test_no_future_bar_entry_and_no_overnight_and_no_unsupported_market(self):
        x=entry()
        x["signal_idx"]=21
        with self.assertRaises(ValueError):
            a.replay([x],["A"])
        with self.assertRaises(ValueError):
            a.replay([entry()],["A"])
        with self.assertRaises(PermissionError):
            a.replay([entry(date="2025-01-02")],["A"])
        mnq=entry()
        mnq["instrument"]="MNQ"
        with self.assertRaises(PermissionError):
            a.replay([mnq],["A"])

    def test_duplicate_priority_and_bad_tick_grid_fail_closed(self):
        with self.assertRaises(ValueError):
            a.replay([],["A","A"])
        b=entry()
        b["stop"]=19990.1
        with self.assertRaises(ValueError):
            a.replay([b],["A"])
        with self.assertRaises(ValueError):
            a.replay([mark()],["A"])
        with self.assertRaises(ValueError):
            a.replay([entry(),exit(idx=21)],["A"])

    def test_stop_gap_at_exit_requires_reconciliation_even_without_prior_mark(self):
        with self.assertRaisesRegex(ValueError,"STOP_CROSSED"):
            a.replay([entry(),exit(price=19980.)],["A"])
        outcome=a.replay([entry(),exit(price=19980.,confirmed=True)],["A"])
        self.assertTrue(outcome["trades"][0]["stop_crossed_unreconciled"])

    def test_reject_rewound_input_event_order(self):
        bad=[entry(idx=25,signal=24),mark(idx=23),exit(idx=27)]
        with self.assertRaisesRegex(ValueError,"out of bar order"):
            a.replay(bad,["A"])

    def test_internal_closed_loss_pause_independent_of_official_soft_pause(self):
        # Large discontinuity in synthetic exit is explicitly modeled,
        # not treated as a valid stop at the nominal protective level.
        # Here the soft pause is also triggered; first rejection reason
        # is soft-equity, as required by conservative controls.
        r=a.replay([entry(),exit(price=19945.,confirmed=True),
                    entry(idx=27,signal=26)],["A"])
        self.assertEqual(r["days"][0]["entries"],1)
        self.assertTrue(r["days"][0]["soft_pause_triggered"])
        self.assertEqual(r["rejections"]["SOFT_EQUITY_PAUSE"],1)

if __name__=="__main__":
    unittest.main()
