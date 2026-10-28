"""S0.25 synthetic-only AST signals, 132/132 real formula routes and M1 entry probes."""
import copy
import unittest
import numpy as np
from research.nq import nq_m1_v30_132_signal_m1_bridge as b
from research.nq.nq_m1_v26_structural_generator import (
    structural_batch,one_per_indicator,sha
)
from research.nq.nq_m1_v22_contract_provenance import prior_same_contract

def series(n=390):
    x=np.empty((n,5),dtype=float)
    for i in range(n):
        p=20000+i*.25
        x[i]=[p,p+1,p-1,p+.25,1000+i]
    return x

def simple_sma(kind="MARKET", long_op="RISING", short_op="FALLING"):
    s=copy.deepcopy(structural_batch(1)["candidates"][0])
    z={"registry_id":"I001","name":"SMA",
       "parameters":{"period":12,"source":"close"}}
    # Resolve actual catalog ID to avoid dependence on registry ordering.
    from research.nq.nq_m1_v26_all_132_router import catalogue
    z["registry_id"]=catalogue()["SMA"]["id"]
    s["long"]={"op":long_op,"indicator":copy.deepcopy(z),"lag_completed_bars":1}
    s["short"]={"op":short_op,"indicator":copy.deepcopy(z),"lag_completed_bars":1}
    s["entry_order"]={"kind":kind,"offset_ticks":0,"expiry_bars":1}
    s["id"]="NQ26_"+sha(s)[:16]
    s["lineage"]={"operator":"RANDOM","parents":[]}
    return s

class TestV30SignalBridge(unittest.TestCase):
    def test_true_long_false_short_from_closed_ema_sma(self):
        z=b.signals_at(series(),75,simple_sma(),"2021-05-04")
        self.assertEqual(z["action"],"LONG")
        self.assertIs(z["long"],True)
        self.assertIs(z["short"],False)
        self.assertFalse(z["fitness_evaluated"])
        self.assertEqual(z["trades_executed"],0)

    def test_future_390_bar_mutation_does_not_change_prior_signal(self):
        x=series()
        s=simple_sma()
        first=b.signals_at(x,60,s,"2021-05-04")
        other=x.copy();other[61:,:]=float("nan")
        self.assertEqual(first,b.signals_at(other,60,s,"2021-05-04"))
        self.assertEqual(first["action"],"LONG")

    def test_unknown_is_not_false_nor_valid_other_side(self):
        s=simple_sma()
        x=series()
        s["short"]["indicator"]["parameters"]["period"]=300
        s["id"]="NQ26_"+sha(s)[:16]
        z=b.signals_at(x,80,s,"2021-05-04")
        self.assertIs(z["long"],True)
        self.assertIsNone(z["short"])
        self.assertEqual(z["action"],"UNAVAILABLE_SOME_SIGNAL_DATA")
        self.assertGreater(z["unavailable_indicator_leaf_evaluations"],0)
        self.assertFalse(b.entry_probe(x,80,s,"2021-05-04")["entry_proxy"])

    def test_false_and_unknown_and_true_or_unknown(self):
        self.assertIs(b._tri_and(False,None),False)
        self.assertIsNone(b._tri_and(True,None))
        self.assertIs(b._tri_or(True,None),True)
        self.assertIsNone(b._tri_or(False,None))

    def test_both_sides_true_not_entered(self):
        s=simple_sma(short_op="RISING")
        z=b.entry_probe(series(),50,s,"2021-05-04")
        self.assertEqual(z["action"],"BOTH_SIDES_CONFLICT")
        self.assertFalse(z["entry_proxy"])

    def test_next_bar_market_long_entry_without_looking_ahead(self):
        x=series();s=simple_sma()
        z=b.entry_probe(x,45,s,"2021-05-04")
        self.assertEqual(z["action"],"LONG")
        self.assertTrue(z["entry_proxy"])
        self.assertEqual(z["entry_proxy_bar_index"],46)
        self.assertAlmostEqual(z["entry_proxy_price"],x[46,0]+.5)
        self.assertFalse(z["economic_backtest_executed"])

    def test_limit_exact_touch_not_filled_with_new_m1_policy(self):
        s=simple_sma("LIMIT")
        x=series()
        # Signal 44: close = 20011.25. Set next bar open higher;
        # low exactly equals requested -> limit touch, no queue evidence.
        i=44;req=float(x[i,3])
        x[i+1]=[req+.25,req+1.,req,req+.25,1000.]
        z=b.entry_probe(x,i,s,"2021-05-04")
        self.assertEqual(z["action"],"LONG")
        self.assertFalse(z["entry_proxy"])
        self.assertEqual(z["entry_proxy_reason"],"LIMIT_TOUCH_ONLY_OR_NOT_CROSSED")
        x[i+1,2]=req-.25
        self.assertTrue(b.entry_probe(x,i,s,"2021-05-04")["entry_proxy"])

    def test_stop_entry_proxy_with_adverse_gap(self):
        s=simple_sma("STOP")
        x=series()
        z=b.entry_probe(x,43,s,"2021-05-04")
        self.assertTrue(z["entry_proxy"])
        self.assertEqual(z["entry_proxy_reason"],"STOP_ADVERSE_GAP_OR_TRIGGER_SLIPPAGE")

    def test_no_entry_at_or_after_cutoff_and_early_bar(self):
        s=simple_sma();x=series()
        for i in (2,117,118,119):
            with self.subTest(i=i):
                z=b.entry_probe(x,i,s,"2021-05-04")
                self.assertFalse(z["entry_proxy"])
                self.assertEqual(z["entry_proxy_reason"],"SIGNAL_OUTSIDE_ALLOWED_ENTRY_WINDOW")

    def test_no_future_bar_results_in_no_hypothetical_fill(self):
        s=simple_sma()
        z=b.entry_probe(series(51),50,s,"2021-05-04")
        self.assertEqual(z["entry_proxy_reason"],"NEXT_BAR_NOT_AVAILABLE")

    def test_refuses_non_ist_session_and_foreign_contract_context(self):
        s=simple_sma();x=series()
        for day in ("2023-05-04","2025-05-04","2026-05-04"):
            with self.assertRaises(PermissionError):
                b.signals_at(x,40,s,day)
        ctx=prior_same_contract(["2021-05-03","2021-05-04"],
                                np.stack([x,x]),1)
        broken=dict(ctx,source_contract="NQ_09-22")
        with self.assertRaises(PermissionError):
            b.signals_at(x,40,s,"2021-05-04",broken)

    def test_anchor_future_rejected_even_if_other_indicator_does_not_use_it(self):
        s=simple_sma()
        with self.assertRaises(ValueError):
            b.signals_at(series(),30,s,"2021-05-04",anchor_index=100)

    def test_internal_price_not_trusted_when_future_side_changed(self):
        s=simple_sma()
        x=series()
        with self.assertRaises(ValueError):
            b.signals_at(x,500,s,"2021-05-04")
        bad=x.copy();bad[20,3]+=0.1
        with self.assertRaises(ValueError):
            b.signals_at(bad,30,s,"2021-05-04")

    def test_all_132_leaf_paths_invoked_using_synthetic_m1(self):
        x=series()
        previous=series()
        ctx=prior_same_contract(["2021-05-03","2021-05-04"],
                                np.stack([previous,x]),1)
        # Not certification. 132 generated names -> AST predicate bridge
        # -> original 132 calculator routes, returns bool or unavailable.
        routed=set();outcomes={"available":0,"unavailable":0}
        for node in one_per_indicator()["leaves"]:
            with self.subTest(name=node["indicator"]["name"]):
                item=b._context_for("2021-05-04",ctx,0,360)
                d={"unavailable_leaves":0}
                v=b._tree(node,x[:361],item,{},d)
                self.assertIn(v,(True,False,None))
                routed.add(node["indicator"]["name"])
                outcomes["unavailable" if v is None else "available"]+=1
        self.assertEqual(len(routed),132)
        self.assertGreater(outcomes["available"],0)
        self.assertGreater(outcomes["unavailable"],0)

    def test_frozen_random_sample_ast_automatically_bridgeable(self):
        x=series()
        candidates=structural_batch(30)["candidates"]
        outcomes=set()
        for s in candidates:
            z=b.signals_at(x,360,s,"2021-05-04")
            outcomes.add(z["action"])
            self.assertEqual(z["ast_sha256"],sha(s))
            self.assertEqual(z["trades_executed"],0)
            self.assertIn(z["action"],
                {"LONG","SHORT","BOTH_SIDES_CONFLICT","NO_SIGNAL","UNAVAILABLE_SOME_SIGNAL_DATA"})
        self.assertTrue(outcomes)

if __name__=="__main__":
    unittest.main()
