"""NQ V2.2 synthetic-only warmup integration, including signal, SL, TP and trailing."""
import copy
import unittest
import numpy as np

from research.nq import nq_m1_v2_orders as engine
from research.nq import nq_m1_v2_m1_engine as scalar
from research.nq import nq_m1_v22_contract_provenance as cp
from research.nq.test_nq_m1_v2_orders import strategy


def fixture(base=100.):
    result=np.empty((390,5),float)
    for i in range(390):
        p=base+.25*i
        result[i]=[p,p+1.,p-1.,p+.25,1000.]
    return result


def context():
    older=fixture(100)
    today=fixture(197.5)
    prior=cp.prior_same_contract(["2021-05-03","2021-05-04"],
                                  np.stack([older,today]),1)
    return today,prior


class TestNQIntegratedWarmup(unittest.TestCase):
    def test_old_session_local_legacy_interface_still_works(self):
        day,_=context()
        old=engine.simulate_day(day,strategy(),"2021-05-04")
        self.assertFalse(old["validated_same_contract_warmup"])
        self.assertEqual(old["warmup_prior_bars"],0)
        self.assertGreater(old["filled"],0)

    def test_atr_initial_stop_no_history_vs_validated_history(self):
        day,proven=context()
        s=strategy()
        s["exit"]["stop_loss_required"]={"kind":"ATR","period":180,"multiple":1.}
        no=engine.simulate_day(day,s,"2021-05-04")
        with_history=engine.simulate_day(day,s,"2021-05-04",session_context=proven)
        self.assertEqual(no["filled"],0)
        self.assertGreater(no["rejected"]["missing_stop_context"],0)
        self.assertGreater(with_history["filled"],0)
        self.assertEqual(with_history["warmup_prior_bars"],390)
        self.assertTrue(with_history["validated_same_contract_warmup"])

    def test_causal_signal_uses_same_contract_history(self):
        day,proven=context()
        history=engine._validate_context("2021-05-04",proven)
        reader=engine._causal_reader(history)
        block={"name":"SMA","parameters":{"period":180,"source":"close"}}
        self.assertIsNone(scalar.indicator_value(day,20,block))
        self.assertIsNotNone(reader(day,20,block))
        changed=day.copy()
        changed[21:,:4]+=500.
        self.assertEqual(reader(day,20,block),reader(changed,20,block))

    def test_lag_can_reach_previous_completed_same_contract_session(self):
        day,proven=context()
        hist=engine._validate_context("2021-05-04",proven)
        reader=engine._causal_reader(hist)
        cfg={"name":"SMA","parameters":{"period":180,"source":"close"}}
        self.assertAlmostEqual(reader(day,-1,cfg),
                               scalar.indicator_value(hist,len(hist)-1,cfg))
        # Prior session VWAP and OBV must not leak under a new RTH anchor.
        self.assertIsNone(reader(day,-1,{"name":"VWAP","parameters":{"anchor":"session"}}))
        self.assertIsNone(reader(day,-1,{"name":"OBV","parameters":{}}))
        altered=day.copy()
        altered[:,3]+=400.
        self.assertEqual(reader(day,-1,cfg),reader(altered,-1,cfg))

    def test_all_signal_operators_keep_future_data_out(self):
        day,proven=context()
        reader=engine._causal_reader(engine._validate_context("2021-05-04",proven))
        x={"op":"RISING","indicator":{"name":"SMA",
            "parameters":{"period":200,"source":"close"}},"lag_completed_bars":4}
        a=scalar.eval_expr(day,40,x,reader)
        changed=day.copy()
        changed[41:,:4]+=300.
        self.assertEqual(a,scalar.eval_expr(changed,40,x,reader))

    def test_vwap_and_obv_restart_at_current_rth_open(self):
        day,proven=context()
        reader=engine._causal_reader(engine._validate_context("2021-05-04",proven))
        for ind in ({"name":"VWAP","parameters":{"anchor":"session"}},
                    {"name":"OBV","parameters":{}}):
            self.assertAlmostEqual(reader(day,10,ind),
                                   scalar.indicator_value(day,10,ind))

    def test_atr_target_and_atr_trailing_get_prior_bars(self):
        day,proven=context()
        s=strategy()
        s["exit"]["profit_target"]={"kind":"ATR","period":180,"multiple":3.}
        s["exit"]["stop_loss_required"]={"kind":"ATR","period":180,"multiple":1.}
        s["exit"]["trailing"]={"start_r":.25,"distance_atr":1.,"atr_period":120}
        yes=engine.simulate_day(day,s,"2021-05-04",session_context=proven)
        no=engine.simulate_day(day,s,"2021-05-04")
        self.assertGreater(yes["filled"],0)
        self.assertEqual(no["filled"],0)
        self.assertTrue(all(t["target_price"] is not None for t in yes["trades"]))

    def test_fail_closed_on_foreign_contract_or_future_prior_day(self):
        day,proven=context()
        for field,bad_value in (("source_contract","NQ_09-21"),("holdouts","OPEN")):
            bad=dict(proven, **{field:bad_value})
            with self.assertRaises((PermissionError,ValueError)):
                engine.simulate_day(day,strategy(),"2021-05-04",session_context=bad)
        fake=dict(proven, prior_session_dates=["2022-05-03"])
        with self.assertRaises(PermissionError):
            engine.simulate_day(day,strategy(),"2021-05-04",session_context=fake)

    def test_roll_boundary_has_zero_carryover_bars(self):
        before=fixture(100)
        after=fixture(197.5)
        cont=cp.prior_same_contract(["2021-03-10","2021-03-11"],
                                    np.stack([before,after]),1)
        self.assertEqual(cont["prior_bars"].shape,(0,5))
        out=engine.simulate_day(after,strategy(),"2021-03-11",
                                 session_context=cont)
        self.assertEqual(out["warmup_prior_bars"],0)
        self.assertTrue(out["validated_same_contract_warmup"])

    def test_current_strategy_no_mnq_relabel(self):
        day,proven=context()
        s=strategy()
        s["position_sizing"]={"instrument":"NQ","contracts":1}
        good=engine.simulate_day(day,s,"2021-05-04",session_context=proven)
        self.assertEqual(good["session"],"2021-05-04")

if __name__=="__main__":
    unittest.main()
