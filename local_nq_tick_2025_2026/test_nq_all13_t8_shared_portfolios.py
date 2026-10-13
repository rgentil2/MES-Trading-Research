#!/usr/bin/env python3
"""Synthetic-only 8T exhaustive-engine QA; never accesses private Last."""
import unittest
from fractions import Fraction as F
from unittest.mock import patch
from itertools import combinations

from nq_all13_t8_shared_portfolios import (
    T,PARENT,CASE,atomic_bounds,from_atomic_result,account_day,
    model_summary,month_stage,dd_daily,MAX_DAILY,STOP_DAILY
)
from nq_t133_t168_d1_engine import model_one
from nq_t209_t228_structural_d0 import registry
from nq_t133_t152_executable_d0_batch import load_registry


def intent(ID,decision=10,enter=11,exit=12,net=50):
    return {"ID":ID,"status":"MODELLED","decision":decision,
            "entry":enter,"exit":exit,"net":net,
            "stress_1p5":net-5,"extra10":net-10,"risk_usd":100,
            "instrument":"NQ","ambiguous":False}

class EightTests(unittest.TestCase):
    def test_eight_original_members_including_negative_and_five(self):
        self.assertEqual(len(T),8)
        self.assertEqual(set(T),set(PARENT))
        self.assertEqual(sum(1 for n in range(1,9) for _ in combinations(T,n)),255)
        self.assertIn("T186",T)
        self.assertIn("T217",T)
        self.assertIn("T215",T)
    def test_whitelist_before_file_io(self):
        with patch("nq_all13_t8_shared_portfolios.month_days",
                   side_effect=AssertionError("UNAUTHORIZED_MARKET_IO")):
            with self.assertRaisesRegex(ValueError,"SEALED"):
                month_stage(None,"2026-06",load_registry(),registry())
    def test_stop_first_and_next_timestamp(self):
        groups=[(101,105,108),(102,91,141)]
        z=model_one(groups,1,F(90),1.5,15,100,True)
        self.assertEqual(z["status"],"MODELLED_EXECUTION_UNVERIFIED")
        self.assertEqual(z["exit_reason"],"STOP_FIRST")
        self.assertEqual(atomic_bounds(groups,1,F(90),1.5,z),(101,102))
        out=from_atomic_result("T224",100,groups,1,F(90),1.5,z)
        self.assertEqual(out["entry"],101)
        self.assertEqual(out["exit"],102)
    def test_ambiguous_entry_blocks(self):
        groups=[(101,89,108),(102,105,111)]
        z=model_one(groups,1,F(90),1.5,15,100,True)
        self.assertTrue(z["entry_group_ambiguous"])
        self.assertEqual(atomic_bounds(groups,1,F(90),1.5,z),
                         "ENTRY_TIMESTAMP_ORDER_AMBIGUOUS")
    def test_same_time_T05_priority_and_single_position(self):
        it={x:[] for x in T}
        it["T05-377"]=[intent("T05-377",10,11,20,20)]
        it["T224"]=[intent("T224",10,11,15,100)]
        selected,rej=account_day(it,("T05-377","T224"))
        self.assertEqual([z["ID"] for z in selected],["T05-377"])
        self.assertEqual(rej["overlap"],1)
    def test_all8_eligible_each_day_still_max_two(self):
        it={x:[intent(x,10+i*5,11+i*5,12+i*5,10)]
            for i,x in enumerate(T)}
        chosen,rej=account_day(it,tuple(T))
        self.assertEqual(len(chosen),MAX_DAILY)
        self.assertEqual(rej["capacity"],6)
    def test_fail_closed_invalid_exposure(self):
        it={x:[] for x in T}
        it["T147"]=[{"ID":"T147","decision":10,
                     "status":"ENTRY_TIMESTAMP_ORDER_AMBIGUOUS"}]
        with self.assertRaisesRegex(ValueError,"UNRESOLVED"):
            account_day(it,("T147",))
    def test_closed_dd_and_monthly_stats(self):
        self.assertEqual(dd_daily([50,-100,30,-120]),140.)
        days=[]
        for i in range(7):
            it={x:[] for x in T}
            it["T215"]=[intent("T215",10,11,12,-5 if i==2 else 10)]
            days.append({"day":f"2026-01-{i+1:02d}","intents":it})
        z=model_summary(days,("T215",))
        self.assertEqual(z["N"],7)
        self.assertEqual(z["net_base"],55)
        self.assertEqual(z["net_plus10"],-15)
        self.assertEqual(z["reconciled_parent_count"],8)
        self.assertIsNone(z["floating_DD"])
    def test_closed_day_stop(self):
        it={x:[] for x in T}
        it["T05-377"]=[intent("T05-377",10,11,12,-620),
                        intent("T05-377",20,21,22,300)]
        done,rej=account_day(it,("T05-377",))
        self.assertEqual(len(done),1)
        self.assertEqual(rej["capacity"],1)

if __name__=="__main__":unittest.main()
