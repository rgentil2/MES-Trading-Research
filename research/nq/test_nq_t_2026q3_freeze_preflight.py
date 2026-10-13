#!/usr/bin/env python3
"""Only syntax/static fixture tests: must not open Last, H OOS or T Q3 data."""
import copy
import unittest
from research.nq.nq_t_2026q3_freeze_preflight import (
    ROOT,FREEZE,prereg_contract,python_dependency_closure,
    fingerprint,prepare
)
import json


class FreezeSafetyTests(unittest.TestCase):
    def test_prereg_holds_two_and_benchmark_without_unseal(self):
        x=json.loads(FREEZE.read_text())
        prereg_contract(x)
        self.assertEqual(len(x["frozen_portfolios"]),3)
        self.assertTrue(x["not_yet_authorized_to_unseal"])

    def test_mutation_of_holdout_and_contracts_fails(self):
        x=json.loads(FREEZE.read_text())
        bad=copy.deepcopy(x)
        bad["temporal_roles"]["single_final_holdout"]["not_read"]=False
        with self.assertRaisesRegex(ValueError,"INTEGRITY"):
            prereg_contract(bad)
        bad=copy.deepcopy(x)
        bad["single_account"]["max_new_trades_per_day"]=3
        with self.assertRaisesRegex(ValueError,"INTEGRITY"):
            prereg_contract(bad)
        bad=copy.deepcopy(x)
        bad["frozen_portfolios"]["B"]["members"].append("T224")
        with self.assertRaisesRegex(ValueError,"INTEGRITY"):
            prereg_contract(bad)

    def test_import_graph_without_importing_market_engines(self):
        x=json.loads(FREEZE.read_text())
        graph=python_dependency_closure(x["source_entrypoints"])
        self.assertTrue(any(p.endswith("qc_tick_day.py") for p in graph))
        self.assertTrue(any(p.endswith("nq_b05h01_trade_expansion_month.py") for p in graph))
        self.assertTrue(all((ROOT/p).is_file() for p in graph))

    def test_hash_stable_and_input_sensitive(self):
        r={"a.py":"aa","b.py":"bb"}
        h=fingerprint(r)
        self.assertEqual(h,fingerprint({"b.py":"bb","a.py":"aa"}))
        self.assertNotEqual(h,fingerprint({"b.py":"cc","a.py":"aa"}))

    def test_pending_freeze_never_authorizes_one_shot(self):
        result=prepare()
        self.assertFalse(result["holdout_authorized_to_unseal"])
        self.assertFalse(result["safe_to_execute_one_shot_holdout"])
        self.assertFalse(result["OOS_prices_opened"])
        self.assertTrue(result["missing_holdout_adapter"])
        self.assertGreaterEqual(result["files_checked"],15)


if __name__=="__main__":
    unittest.main()
