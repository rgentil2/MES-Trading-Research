#!/usr/bin/env python3
"""Synthetic tests only: nine-hypothesis D2 shadow, no licensed market records."""
import unittest
from fractions import Fraction as F
from unittest.mock import patch
from nq_nine_d2_t05_t224_shadow import (
  NINE,MONTHS,MODELED,aggregate,trace_t224_end,replay_account,
  month_stage,dd_closed,stats_trade
)
from nq_t133_t168_d1_engine import model_one
from nq_t209_t228_structural_d0 import registry
from nq_t210_t224_five_economic_shadow import CASES


class D2NineTests(unittest.TestCase):
    def plan(self):
        g=[(101,110,112),(102,114,137),(103,119,140)]
        model=model_one(g,1,F(100),1.5,15,100,True)
        self.assertEqual(model["status"],MODELED)
        self.assertFalse(model["entry_group_ambiguous"])
        return {"timestamp":100,"side":1,"stop":F(100),
                "groups":g,"model":model}

    def test_members_are_exact_nine_and_unique(self):
        self.assertEqual(len(NINE),9)
        self.assertEqual(len(set(NINE)),9)
        self.assertEqual(NINE[-1],"T224")
        self.assertEqual(NINE[0],"H09")

    def test_whitelist_before_file_list(self):
        with patch("nq_nine_d2_t05_t224_shadow.month_days",
                   side_effect=AssertionError("LICENSED_FS_CALLED")):
            with self.assertRaisesRegex(ValueError,"SEALED"):
                month_stage(None,"2026-06",registry())

    def test_exact_t224_model_end_replay(self):
        p=self.plan()
        self.assertEqual(p["model"]["exit_reason"],"TARGET")
        self.assertEqual(trace_t224_end(p),(101,102))
        replay=replay_account([],"2026-03-16",[],[],p)
        self.assertEqual(replay["counter"]["executed_T224"],1)
        self.assertEqual(replay["net"],round(p["model"]["net_usd"],2))
        self.assertEqual(replay["net_plus10"],round(replay["net"]-10,2))

    def test_ambiguous_entry_fails_closed(self):
        z=self.plan()
        z["model"]["entry_group_ambiguous"]=True
        with self.assertRaisesRegex(ValueError,"SAME_TIMESTAMP"):
            trace_t224_end(z)

    def test_stop_first_matches_original_exit(self):
        g=[(101,110,112),(102,90,150)]
        p={"timestamp":100,"side":1,"stop":F(100),
           "groups":g,"model":model_one(g,1,F(100),1.5,15,100,True)}
        self.assertEqual(p["model"]["exit_reason"],"STOP_FIRST")
        self.assertEqual(trace_t224_end(p),(101,102))

    def test_closed_drawdown_not_intratrade(self):
        self.assertEqual(dd_closed([50,-100,200,-120]),120.)
        self.assertEqual(stats_trade([10,-5,10])["N"],3)

    def test_parent_parity_required(self):
        src=(13,20,22,21,20,22,22)
        ready=(13,19,21,21,20,21,20)
        allrows={};dates=[]
        for i,month in enumerate(MONTHS):
            from datetime import date,timedelta
            first=date.fromisoformat(month+"-01")
            days=[(first+timedelta(days=j)).isoformat() for j in range(ready[i])]
            dates+=days
            r=[]
            for day in days:
                r.append({"date":day,"t05_classic_n":0,"t05_classic_net":0,
                          "t224_model":None,
                          "t224_case":False,
                          "only":{"counter":{},"trades":[],"net":0.},
                          "combined":{"counter":{},"trades":[],"net":0.,"net_plus10":0.,"net_t224_stress":0.}})
            allrows[month]={"stage":"PRIVATE_NINE_D2_T05_T224_CHRONOLOGICAL_SHADOW",
              "month":month,"source":src[i],"eligible":ready[i],
              "cases":{k:CASES[k] if i==0 else 0 for k in CASES},
              "days":r,"holdouts_opened":False,"new_history":False,
              "fills_verified":False,"raw_ticks_public":False}
        with self.assertRaisesRegex(AssertionError,"T05_115"):
            aggregate(allrows)
        allrows[MONTHS[0]]["new_history"]=True
        with self.assertRaisesRegex(ValueError,"INVALID_MONTH"):
            aggregate(allrows)

if __name__=="__main__":unittest.main()
