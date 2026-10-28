"""Cross-check two independent synthetic NQ account arithmetic modules."""
import unittest
from research.nq import nq_m1_v23_shared_account_event_qa as book
from research.nq import nq_m1_v22_account_risk_reference as ref

def ent(d,i=21):
    return {"kind":"ENTRY","date":d,"idx":i,"signal_idx":i-1,
            "instrument":"NQ","contracts":1,"strategy_id":"A",
            "price":20000.,"stop":19990.,"side":1}
def close(d,price,i=25,confirmed=False):
    return {"kind":"EXIT","date":d,"idx":i,"instrument":"NQ","contracts":1,
            "strategy_id":"A","price":price,"stop_execution_confirmed":confirmed}
def mark(d,price,i=22):
    return {"kind":"MARK","date":d,"idx":i,
            "instrument":"NQ","contracts":1,"price":price}


class TestNQSharedAccountIndependentReference(unittest.TestCase):
    def test_eod_trailing_floor_matches_independent_reference(self):
        d1="2021-06-15";d2="2021-06-16"
        result=book.replay([ent(d1),close(d1,20051.25),
                            ent(d2),close(d2,20100.)],["A"])
        eod=result["days"]
        baseline=ref.synthetic_account_path([
            {"date":d1,"path":[{"equity":50000.,"closed_balance":50000.},
                               {"equity":eod[0]["eod_balance"],"closed_balance":eod[0]["eod_balance"]}]},
            {"date":d2,"path":[{"equity":eod[0]["eod_balance"],"closed_balance":eod[0]["eod_balance"]},
                               {"equity":eod[1]["eod_balance"],"closed_balance":eod[1]["eod_balance"]}]},
        ])
        for r,e in zip(eod,baseline["date_rows"]):
            self.assertAlmostEqual(r["eod_balance"],e["eod_closed_balance"])
            self.assertAlmostEqual(r["hard_floor_after_close"],e["hard_floor_after_close"])
        self.assertFalse(result["official_account_plan_verified"])

    def test_gap_exit_is_included_in_worst_floating_equity(self):
        d="2021-06-15"
        out=book.replay([ent(d),close(d,19945.,confirmed=True)],["A"])
        trade=out["trades"][0]
        self.assertAlmostEqual(trade["min_floating_equity"],48975.32)
        self.assertEqual(trade["min_floating_equity"],out["days"][0]["eod_balance"])
        self.assertTrue(out["days"][0]["soft_pause_triggered"])

    def test_hard_breach_matches_reference_when_mark_confirmed(self):
        d="2021-06-15"
        e=[ent(d),mark(d,19895.),close(d,19895.,confirmed=True)]
        out=book.replay(e,["A"])
        p0={"equity":50000.,"closed_balance":50000.}
        p1={"equity":47875.32,"closed_balance":50000.}
        p2={"equity":47875.32,"closed_balance":47875.32}
        ref_out=ref.synthetic_account_path([{"date":d,"path":[p0,p1,p2]}])
        self.assertEqual(out["hard_breach"],ref_out["hard_breach"])
        self.assertTrue(out["hard_breach"])
        self.assertTrue(out["days"][0]["soft_pause_triggered"])

    def test_mark_only_cannot_raise_closed_balance(self):
        d="2021-06-15"
        x=book.replay([ent(d),mark(d,20055.),close(d,20000.)],["A"])
        self.assertAlmostEqual(x["days"][0]["eod_balance"],49975.32)
        self.assertLess(x["days"][0]["eod_balance"],50000)
        self.assertNotEqual(x["days"][0]["eod_balance"],51075.32)

if __name__=="__main__":
    unittest.main()
