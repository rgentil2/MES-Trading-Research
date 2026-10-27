"""V2.1 synthetic only: real active thresholds, broad research preserved, NQ-only."""
import copy
import unittest
import numpy as np
from research.nq import nq_m1_v21_semantic_generator as v
from research.nq import nq_m1_v2_generator as old
from research.nq import nq_m1_v2_orders as orders
from research.nq import nq_m1_v2_m1_engine as engine


def fixture():
    rows=np.empty((390,5), dtype=float)
    for i in range(390):
        p=100.+.25*i
        rows[i] = [p,p+1,p-1,p+.25,100.]
    return rows


class TestV21(unittest.TestCase):
    def test_broad_132_unrestricted_alongside_eng_38(self):
        broad=v.generate(300,seed=7,supported_only=False)
        eng=v.generate(100,seed=7,supported_only=True)
        self.assertEqual(broad["search_scope"],"BROAD_132")
        self.assertEqual(eng["search_scope"],"ENGINEERING_38")
        self.assertEqual(broad["registered_blocks_total"],132)
        self.assertEqual(eng["registered_blocks_total"],132)
        self.assertEqual(eng["implemented_scalar_blocks"],38)
        self.assertEqual(len(broad["rows"]),300)
        self.assertEqual(len(eng["rows"]),100)
        self.assertTrue(all(r["strategy"]["position_sizing"]==
                            {"instrument":"NQ","contracts":1} for r in eng["rows"]))
        self.assertEqual(eng["holdouts"],"2023_2024_NO_FIT__2025_2026_SEALED")
        self.assertGreater(eng["semantic_executable_count"],0)
        seen=set()
        for row in broad["rows"]:
            for direction in ("long","short"):
                seen.update(leaf["indicator"]["name"] for leaf in
                            v._iter_leaves(row["strategy"][direction]))
        self.assertEqual(len(seen),132)

    def test_engineering_has_no_inert_indicator_fields_or_level_lag(self):
        eng=v.generate(75,seed=27,supported_only=True)
        self.assertTrue(any(row["strategy"]["lineage"]["method"]!="RANDOM"
                            for row in eng["rows"]))
        self.assertTrue(any(row["strategy"]["lineage"]["method"]=="RANDOM"
                            for row in eng["rows"]))
        for row in eng["rows"]:
            s=row["strategy"]
            self.assertEqual(s["schema"],old.STRATEGY_SCHEMA)
            self.assertEqual(s["ast_version"],v.AST_VERSION)
            for direction in ("long","short"):
                for leaf in v._iter_leaves(s[direction]):
                    name=leaf["indicator"]["name"]
                    params=leaf["indicator"]["parameters"]
                    self.assertFalse(set(params)-v.USED[name])
                    if leaf["op"] in v.PREDICATES_LEVEL:
                        self.assertNotIn("lag_completed_bars",leaf)
                        self.assertIn("threshold",leaf)
                    else:
                        self.assertNotIn("threshold",leaf)
                        self.assertIn("lag_completed_bars",leaf)

    def test_active_relative_volume_crossing_is_causal_and_threshold_matters(self):
        x=fixture()
        x[20,4]=500.
        leaf={"op":"CROSS_ABOVE_LEVEL",
              "indicator":{"name":"Relative Volume","parameters":{"period":5}},
              "threshold":1.5}
        self.assertTrue(engine.eval_expr(x,20,leaf))
        higher=dict(leaf, threshold=6.)
        self.assertFalse(engine.eval_expr(x,20,higher))
        changed=x.copy()
        changed[21:,4]=100000.
        self.assertEqual(engine.eval_expr(x,20,leaf),engine.eval_expr(changed,20,leaf))
        self.assertNotEqual(old.fingerprint({"long":leaf}),
                            old.fingerprint({"long":higher}))

    def test_rsi_level_active_and_no_threshold_in_calculator_params(self):
        x=fixture()
        gt={"op":"ABOVE_LEVEL","threshold":60.,
            "indicator":{"name":"RSI","parameters":{"period":8}}}
        lt=dict(gt,op="BELOW_LEVEL")
        self.assertTrue(engine.eval_expr(x,30,gt))
        self.assertFalse(engine.eval_expr(x,30,lt))
        self.assertNotIn("upper_level",gt["indicator"]["parameters"])

    def test_unsupported_level_indicator_and_inert_lag_are_rejected(self):
        from research.nq.test_nq_m1_v2_orders import strategy
        s=strategy()
        s["long"]={"op":"ABOVE_LEVEL",
                   "indicator":{"name":"RSI","parameters":{"period":8}},
                   "threshold":52.}
        orders.validate_supported(s)
        invalid=copy.deepcopy(s)
        invalid["long"]["lag_completed_bars"]=3
        with self.assertRaises(engine.UnsupportedV2Feature):
            orders.validate_supported(invalid)
        invalid=copy.deepcopy(s)
        invalid["long"]["indicator"]={"name":"SMA","parameters":{"period":8,"source":"close"}}
        with self.assertRaises(engine.UnsupportedV2Feature):
            orders.validate_supported(invalid)

    def test_manifest_reproducible_and_v20_sha_is_unchanged(self):
        a=v.generate(65,seed=81,supported_only=True)
        b=v.generate(65,seed=81,supported_only=True)
        self.assertEqual(a,b)
        self.assertEqual(len(set(x["strategy"]["lineage"]["fingerprint_sha256"]
                                 for x in a["rows"])),65)
        from research.nq.nq_m1_v2_ist_engineering_pilot import frozen_batch
        original=frozen_batch()
        self.assertEqual(original["compatible_manifest_sha256"],
                         "e05f93e8bd73f9c43a2ed48dbc5b6ac813b9d81400309a026fb4de81389b0bf2")

    def test_bad_sizing_or_inert_indicator_field_never_promotes(self):
        s=v.generate(1,seed=4,supported_only=True)["rows"][0]["strategy"]
        s["position_sizing"]={"instrument":"MNQ","contracts":1}
        self.assertNotEqual(v.semantic_audit(s)["semantic_status"],
                            "SEMANTICALLY_EXECUTABLE_UNCERTIFIED")
        s["position_sizing"]={"instrument":"NQ","contracts":1}
        for direction in ("long","short"):
            node=next(v._iter_leaves(s[direction]))
            node["indicator"]["parameters"]["FAKE_INERT"]=34
        self.assertNotEqual(v.semantic_audit(s)["semantic_status"],
                            "SEMANTICALLY_EXECUTABLE_UNCERTIFIED")


if __name__ == "__main__":
    unittest.main()
