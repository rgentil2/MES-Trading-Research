#!/usr/bin/env python3
"""Pure synthetic tests for post-D0 five-of-20 exploratory economics."""
from __future__ import annotations
import unittest
from copy import deepcopy
from unittest.mock import patch
from fractions import Fraction as F

from nq_t210_t224_five_economic_shadow import (
  FIVE,FAMILY,IDS,MONTHS,MODELED,CASES,month_study,
  aggregate,adjust_bh,adjust_holm,bootstrap,max_drawdown_closed,
)
from nq_t209_t228_structural_d0 import registry


def fake_months():
    src=[13,20,22,21,20,22,22]
    ok=[13,19,21,21,20,21,20]
    rows={}
    for i,month in enumerate(MONTHS):
        daily=[]
        for j in range(ok[i]):
            daily.append({
                "date":f"{month}-{j+1:02d}",
                "results":{k:{"group":"CONTROL","status":"NO_CAUSAL_TRIGGER",
                    "net_usd":0.,"stress_1_5x_usd":0.,"stress_plus_10_rt_usd":0.}
                    for k in FIVE},
            })
        rows[month]={"stage":"PRIVATE_POST_D0_SELECTED_FIVE_ECONOMIC_UNVERIFIED",
                     "month":month,"source":src[i],"eligible":ok[i],
                     "case_counts":{k:CASES[k] if i==0 else 0 for k in IDS},
                     "daily":daily,"holdouts_opened":False,"new_data":False,
                     "broker_fills_verified":False,"public_daily_records":False}
    return rows


class EconomicBridgeTests(unittest.TestCase):
    def test_original_twenty_denominator(self):
        q=adjust_bh([.001]+[1.]*(FAMILY-1))
        self.assertAlmostEqual(q[0],.02)
        self.assertEqual(adjust_holm([.01]+[1.]*(FAMILY-1))[0],.20)
        with self.assertRaisesRegex(ValueError,"TWENTY"):
            adjust_bh([.01]*5)

    def test_whitelist_before_reading_files(self):
        with patch("nq_t210_t224_five_economic_shadow.month_days",
                   side_effect=AssertionError("READ_MARKET_BEFORE_GATE")):
            with self.assertRaisesRegex(ValueError,"SEALED"):
                month_study(None,"2026-06",registry())

    def test_bootstrap_full_135(self):
        a=bootstrap([0.]*135,"T210",5)
        self.assertEqual(a["CI90"],[0.,0.])
        self.assertEqual(a["B"],10000)
        with self.assertRaisesRegex(ValueError,"FULL_READY"):
            bootstrap([1.],"T210",5)

    def test_drawdown_is_closed_only(self):
        self.assertAlmostEqual(max_drawdown_closed([300,-100,-120,60,-200]),360.)

    def test_sealed_metadata_and_parent_mask(self):
        r=fake_months()
        m=aggregate(r,registry())
        self.assertEqual(m["source_days"],140)
        self.assertEqual(m["eligible_days"],135)
        self.assertEqual(len(m["economics"]),5)
        self.assertEqual(m["economics"]["T210"]["N_modelled_trades"],0)
        self.assertEqual(m["economics"]["T210"]["D1_formal"],
                         "BLOCKED_D0_FAMILY_BREADTH_5_OF_20")
        self.assertFalse(m["D2_formal_authorized"])
        self.assertFalse(m["broker_fills_verified"])

    def test_fail_case_parity(self):
        r=fake_months()
        r[MONTHS[0]]["case_counts"]["T210"]-=1
        with self.assertRaisesRegex(AssertionError,"CASE_PARITY"):
            aggregate(r,registry())

    def test_fail_privacy_and_unexpected_group(self):
        r=fake_months()
        r[MONTHS[0]]["public_daily_records"]=True
        with self.assertRaisesRegex(ValueError,"SEALED_SCOPE"):
            aggregate(r,registry())

    def test_modelled_trade_fees_and_ambiguity_block_screen(self):
        r=fake_months()
        m=MONTHS[0]
        r[m]["daily"][0]["results"]["T210"]={
            "group":"CASE","status":MODELED,
            "net_usd":100.,"stress_1_5x_usd":75.,
            "stress_plus_10_rt_usd":90.,
            "instrument":"NQ","exit_reason":"TARGET",
            "entry_group_ambiguous":True,
        }
        result=aggregate(r,registry())
        self.assertEqual(result["economics"]["T210"]["entry_group_ambiguous_trades"],1)
        self.assertEqual(result["economics"]["T210"]["D1_shadow"],
                         "LOW_POWER_BELOW_15_MODELLED_TRADES")

if __name__=="__main__":unittest.main()
