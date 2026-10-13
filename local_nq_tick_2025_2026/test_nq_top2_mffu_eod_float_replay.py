#!/usr/bin/env python3
"""Synthetic-only MFFU Rapid EOD 50k source/floor/fee/Last risk invariants."""
import unittest
from datetime import date,timedelta
from unittest.mock import patch
from nq_top2_mffu_eod_float_replay import (
    MASKS,STAGE,FEES,EXPECTED,month_stage,fee_for,old_fee,
    cost_corrected,router_mffu,last_adverse_envelope,
    stage_replay,eval_then_funded,aggregate,portfolio_metrics,
)
from nq_t209_t228_structural_d0 import registry as new_registry

def atom(ident,ts,entry,exit,net,fee="NQ"):
    return {"ID":ident,"decision":ts,"entry":entry,"exit":exit,
            "status":"MODELLED","net":net,"instrument":fee}

def projection(ident,net,minimum=-20,maximum=20,inst="NQ"):
    return {"ID":ident,"instrument":inst,"net_original":net,
            "net_mffu":net,"envelope":{
                "worst_rel_usd":minimum,
                "best_rel_usd":maximum,
                "local_upper_DD_usd":maximum-minimum,
                "observed_whole_timestamp_bound":True}}

def fake_months():
    from nq_tick_short_horizon_month import MONTHS
    src=[13,20,22,21,20,22,22]
    ready=[13,19,21,21,20,21,20]
    rows={}
    for i,month in enumerate(MONTHS):
        first=date.fromisoformat(month+"-01")
        days=[(first+timedelta(days=j)).isoformat() for j in range(ready[i])]
        records=[{"day":d,
           "fixed":{name:[] for name in MASKS},
           "fee_router":{name:[] for name in MASKS},
           "T215_frozen_CASE":0} for d in days]
        rows[month]={"month":month,"source":src[i],"ready":ready[i],
                     "stage":STAGE,"days":records,
                     "holdouts_opened":False,"new_data":False,
                     "broker_fills_verified":False,"public_trade_details":False}
    return rows


class TestMFFUTop2(unittest.TestCase):
    def test_masks_and_fees_are_frozen(self):
        self.assertEqual(tuple(MASKS),("A_T05_T215","B_T05_T186_T215"))
        self.assertEqual(FEES,{"NQ":4.68,"MNQ":1.90})
        a=atom("T05-377",10,11,12,50.)
        b=atom("T215",10,11,12,50.,fee="MNQ")
        self.assertEqual(cost_corrected(a),52.82)
        self.assertEqual(cost_corrected(b),49.6)

    def test_gate_before_any_io(self):
        with patch("nq_top2_mffu_eod_float_replay.month_days",
                   side_effect=AssertionError("READ_BEFORE_GATE")):
            with self.assertRaisesRegex(ValueError,"SEALED"):
                month_stage(None,"2026-06",new_registry(),{})

    def test_fee_router_one_position_priority(self):
        a=atom("T05-377",100,101,111,100.)
        b=atom("T186",102,103,108,100.)
        c=atom("T215",112,113,114,100.)
        inp={"T05-377":[a],"T186":[b],"T215":[c]}
        result,reasons=router_mffu(inp,MASKS["B_T05_T186_T215"])
        self.assertEqual([r["ID"] for r in result],["T05-377","T215"])
        self.assertEqual(reasons["overlap"],1)

    def test_fee_router_honors_negative_closed_day_stop(self):
        a=atom("T05-377",100,101,102,-605.)
        b=atom("T215",103,104,105,30.)
        result,reasons=router_mffu({"T05-377":[a],"T215":[b]},
                    MASKS["A_T05_T215"])
        self.assertEqual(len(result),1)
        self.assertEqual(reasons["capacity"],1)

    def test_last_adverse_group_bound_mixed_contract(self):
        x=atom("T215",9,10,30,5.,fee="MNQ")
        rows=[(10,1000,2),(10,999,1),(20,1002,1),(30,998,1)]
        times=[r[0] for r in rows]
        z=last_adverse_envelope(rows,times,x,1,1002)
        self.assertAlmostEqual(z["worst_rel_usd"],-4.90)
        self.assertAlmostEqual(z["best_rel_usd"],0.00)  # Includes initial flat equity mark
        self.assertTrue(z["observed_whole_timestamp_bound"])

    def test_eval_pass_requires_4_days_consistency(self):
        # Four successive +$750 days, total 3000, max = 25% total.
        start=date(2026,1,1)
        rows=[{"day":(start+timedelta(days=i)).isoformat(),
               "trades":[projection("T05-377",750,-40,200)]}
              for i in range(4)]
        z=stage_replay(rows)
        self.assertEqual(z["first_eval_target_and_consistency_session_index"],4)
        self.assertIsNone(z["first_adverse_envelope_floor_touch_session_index"])

    def test_eval_intraday_can_touch_floor_before_close(self):
        rows=[{"day":"2026-01-05","trades":[projection("T215",450,-2101,500)]}]
        z=stage_replay(rows)
        self.assertEqual(z["first_adverse_envelope_floor_touch_session_index"],1)
        self.assertIsNone(z["first_eval_target_and_consistency_session_index"])

    def test_funded_lock_100_relative_after_2100(self):
        days=[{"day":f"2026-01-{i+1:02d}",
               "trades":[projection("T05-377",700,-20,80)]} for i in range(4)]
        z=stage_replay(days,funded=True)
        self.assertEqual(z["first_funded_2100_buffer_session_index"],3)
        self.assertIsNone(z["first_adverse_envelope_floor_touch_session_index"])

    def test_funded_starts_after_eval_as_fresh_zero(self):
        start=date(2026,1,1)
        rows=[{"day":(start+timedelta(days=i)).isoformat(),
              "trades":[projection("T215",750,-20,100)]}
             for i in range(6)]
        z=eval_then_funded(rows)
        self.assertEqual(z["evaluation"]["first_eval_target_and_consistency_session_index"],4)
        self.assertEqual(z["post_eval_funded_fresh_zero"]["current_balance_if_no_bound_failure"],1500.)

    def test_fail_closed_if_original_trade_parity_wrong(self):
        rows=fake_months()
        with self.assertRaisesRegex(AssertionError,"FROZEN_TWO_PARENT"):
            aggregate(rows)
        rows=fake_months()
        from nq_tick_short_horizon_month import MONTHS
        rows[MONTHS[0]]["new_data"]=True
        with self.assertRaisesRegex(AssertionError,"PRIVATE_RUN"):
            aggregate(rows)

if __name__=="__main__":
    unittest.main()
