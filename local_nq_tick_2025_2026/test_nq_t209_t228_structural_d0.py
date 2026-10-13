#!/usr/bin/env python3
"""T209-T228 synthetic-only gates; absolutely no licensed Last data."""
import unittest
from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
from unittest.mock import patch

from nq_t209_t228_structural_d0 import (
    BLOCKS,IDS,CASE,CONTROL,OTHER,MISSING,MONTHS,
    registry,month_guard,month_stage,groups,profile,stats,
    regime_signal,aggregate
)


def fixtures():
    e=[]
    t=2_000_000_000
    for i in range(24):
        px=50000+i//2 if i<12 else 50014-(i-12)//2
        for j in range(15):
            e.append((t+i*10000000,px+j%3,1+(j%5)))
    d=[(ts-400_000_000, px-3, qty) for ts,px,qty in e]
    m=[(ts-900_000_000, px-6,qty) for ts,px,qty in e]
    lng=[(ts-1_500_000_000, px-9,qty) for ts,px,qty in e]
    return stats(e),stats(d),stats(m),stats(lng)


def month_rows():
    sources=[13,20,22,21,20,22,22]
    ready=[13,19,21,21,20,21,20]
    all_rows={}
    for ix,m in enumerate(MONTHS):
        all_rows[m]={
            "month":m,"source_sessions":sources[ix],"eligible_sessions":ready[ix],
            "counts":{k:{CASE:0,CONTROL:ready[ix],OTHER:0,MISSING:0}
                      for k in IDS},
            "case_joint_counts":{},
            "future_outcomes_read":False,"PNL":None,"PF":None,"DD":None,
            "bid_ask_execution_verified":False,"holdouts_opened":False,
            "new_data":False,"private_rows_or_event_dates_emitted":False,
        }
    return all_rows


class CohortD0(unittest.TestCase):
    def test_20_registered_and_frozen_thresholds(self):
        r=registry()
        self.assertEqual(len(r["members"]),20)
        self.assertEqual(set(r["trigger_definitions"]),set(IDS))
        self.assertEqual([len(z["ids"]) for z in r["blocks"]],[5]*4)
        self.assertEqual(r["status_gates"]["D1"],"NOT_AUTHORIZED")
        self.assertEqual(r["status_gates"]["D2"],"NOT_AUTHORIZED")

    def test_month_denied_before_filesystem(self):
        with patch("nq_t209_t228_structural_d0.month_days",
                   side_effect=AssertionError("FILESYSTEM_TOUCHED")):
            for month in ("2025-09","2026-05","2026-09","2024-01",""):
                with self.assertRaisesRegex(ValueError,"SEALED"):
                    month_stage(None,month,registry())

    def test_per_timestamp_not_raw_last_and_permutation_invariance(self):
        rows=[(10,50000,2),(10,50004,6),(20,50002,3),
              (20,49998,3),(30,50001,2),(40,50006,2)]
        perm=[rows[1],rows[0],rows[3],rows[2]]+rows[4:]
        self.assertEqual(groups(rows),groups(perm))
        self.assertEqual(profile(rows),profile(perm))
        self.assertEqual(stats(rows)["net"],stats(perm)["net"])

    def test_all_twenty_mechanisms_dispatch_without_future(self):
        e,d,m,lng=fixtures()
        for ident in IDS:
            with self.subTest(ident=ident):
                x=regime_signal(ident,e,d,m,lng)
                self.assertIn(x,(None,1,-1))
        self.assertEqual(len(e["groups"]),24)

    def test_optional_macro_degrades_to_none(self):
        e,d,m,lng=fixtures()
        for k in ("T224","T225","T226"):
            with self.subTest(k=k):
                self.assertIsNone(regime_signal(k,e,d,None,None))

    def test_safe_aggregates_and_strict_d0_gate(self):
        z=aggregate(month_rows(),registry())
        self.assertEqual((z["source_sessions"],z["eligible_sessions"]),(140,135))
        self.assertEqual(z["N_testable"],0)
        self.assertEqual(z["N_distinct_testable"],0)
        self.assertEqual(z["D0"],"D0_COHORT_INSUFFICIENT_DISTINCT_TESTABLE_NO_D1")
        self.assertIsNone(z["PNL"])
        self.assertIsNone(z["PF"])
        self.assertIsNone(z["DD"])
        self.assertFalse(z["D1_authorized"])
        self.assertFalse(z["holdouts_opened"])

    def test_joint_case_overlap_deduplicates(self):
        q=month_rows()
        # 20 CASE days and 20 CONTROL days for T209 and T210, all same days.
        # The script only persists aggregate intersections, not specific dates.
        m=MONTHS[0]
        q[m]["counts"]["T209"]={CASE:10,CONTROL:3,OTHER:0,MISSING:0}
        q[m]["counts"]["T210"]={CASE:10,CONTROL:3,OTHER:0,MISSING:0}
        q[m]["case_joint_counts"]={"T209__T210":10}
        n=MONTHS[1]
        q[n]["counts"]["T209"]={CASE:10,CONTROL:9,OTHER:0,MISSING:0}
        q[n]["counts"]["T210"]={CASE:10,CONTROL:9,OTHER:0,MISSING:0}
        q[n]["case_joint_counts"]={"T209__T210":10}
        out=aggregate(q,registry())
        self.assertEqual(out["N_testable"],2)
        self.assertEqual(out["N_distinct_testable"],1)
        self.assertEqual(out["near_duplicate_pairs"][0]["jaccard"],1)

    def test_incomplete_and_private_data_fail_closed(self):
        q=month_rows()
        del q[MONTHS[-1]]
        with self.assertRaisesRegex(AssertionError,"SEVEN"):
            aggregate(q,registry())
        q=month_rows()
        q[MONTHS[0]]["PNL"]=100
        with self.assertRaisesRegex(AssertionError,"UNSAFE"):
            aggregate(q,registry())
        q=month_rows()
        q[MONTHS[0]]["private_rows_or_event_dates_emitted"]=True
        with self.assertRaisesRegex(AssertionError,"UNSAFE"):
            aggregate(q,registry())


if __name__=="__main__":
    unittest.main()
