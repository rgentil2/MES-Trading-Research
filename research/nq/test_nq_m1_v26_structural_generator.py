"""NQ V2.6 reproducible 132-operator AST generation, no economic fitness."""
import unittest
import numpy as np
from research.nq.nq_m1_v26_structural_generator import (
 block,leaf,tree,strategy,sha,structural_batch,one_per_indicator,
 VERSION,LEVEL_OPS,LAG_OPS,STATUS,SEED
)
from research.nq.nq_m1_v26_all_132_router import value
from research.nq.nq_m1_v2_generator import read_registry
from research.nq.nq_m1_v2_m1_engine import eval_expr
from research.nq.test_nq_m1_v26_all_132 import synthetic
import random

def leaves(x):
    if x["op"] in ("AND","OR"):
        yield from leaves(x["left"])
        yield from leaves(x["right"])
    else:yield x

class TestV26StructuralGeneration(unittest.TestCase):
    def test_one_per_132_exhaustive_and_only_once(self):
        fixture=one_per_indicator()
        self.assertEqual(fixture["count"],132)
        self.assertFalse(fixture["economic_fitness_computed"])
        got=[x["indicator"]["name"] for x in fixture["leaves"]]
        self.assertEqual(len(set(got)),132)
        self.assertEqual(set(got),{e["name"] for e in read_registry()["entries"]})

    def test_thresholds_produce_explicit_zero_level_leaf(self):
        fixture=one_per_indicator()
        for x in fixture["leaves"]:
            p=x["indicator"]["parameters"]
            if set(p)&{"threshold","lower_level","upper_level","z_threshold","ratio_threshold"}:
                self.assertIn(x["op"],LEVEL_OPS)
                self.assertEqual(x["threshold"],0.)
                self.assertNotIn("lag_completed_bars",x)
            else:
                self.assertIn(x["op"],LAG_OPS)
                self.assertNotIn("threshold",x)

    def test_reproducibility_random_plus_genetic_and_distinct_lineage(self):
        a=structural_batch(140,seed=SEED)
        b=structural_batch(140,seed=SEED)
        self.assertEqual(a["candidate_sha256"],b["candidate_sha256"])
        self.assertEqual(a["candidates"],b["candidates"])
        ids={x["id"] for x in a["candidates"]}
        self.assertEqual(len(ids),140)
        kinds={x["lineage"]["operator"] for x in a["candidates"]}
        self.assertEqual(kinds,{"RANDOM","MUTATE","CROSSOVER"})
        self.assertFalse(a["market_data_loaded"])
        self.assertFalse(a["holdouts_opened"])
        self.assertFalse(a["all_132_indicators_certified"])

    def test_no_pnl_in_synthetic_population_and_only_nq(self):
        a=structural_batch(60,seed=27)
        forbidden={"pnl","net_usd","profit_factor","fitness","filled_trades"}
        for row in a["candidates"]:
            self.assertEqual(row["ast_version"],VERSION)
            self.assertEqual(row["universe"],"NQ_M1")
            self.assertEqual(row["position_sizing"],{"instrument":"NQ","contracts":1})
            self.assertEqual(row["market_data_years_permitted_for_discovery"],[2020,2021,2022])
            self.assertFalse(forbidden.intersection(row))
            self.assertTrue(set(row["lineage"])=={"operator","parents"})

    def test_structural_sha_is_independent_of_lineage(self):
        a=structural_batch(2,seed=14)["candidates"][0]
        first=sha(a)
        a["lineage"]={"operator":"UNKNOWN","parents":["any"]}
        a["id"]="IRRELEVANT"
        self.assertEqual(sha(a),first)

    def test_132_registered_sampled_params_are_range_valid(self):
        registry=read_registry()["entries"]
        seen=one_per_indicator()["leaves"]
        for item,x in zip(registry,seen):
            with self.subTest(name=item["name"]):
                self.assertEqual(x["indicator"]["registry_id"],item["id"])
                p=x["indicator"]["parameters"]
                self.assertEqual(set(p),set(item["parameters"])-{"constraint"})
                if item["parameters"].get("constraint"):
                    self.assertLess(p["fast_period"],p["slow_period"])

    def test_causal_reader_executes_nested_v26_typed_predicate(self):
        b=synthetic(390)
        ref={"name":"ADX","parameters":{"period":20,"threshold":30}}
        x={"indicator":ref,"op":"ABOVE_LEVEL","threshold":0.0}
        reader=lambda bars,i,block:value(bars,i,block)
        result=eval_expr(b,230,x,reader=reader)
        self.assertEqual(result,value(b,230,ref)>0)
        self.assertEqual(result,eval_expr(b,230,x,reader=reader))

    def test_generation_invalid_bounds_fail_closed(self):
        with self.assertRaises(ValueError):
            structural_batch(0)
        with self.assertRaises(ValueError):
            structural_batch(5,random_fraction=1.5)
        with self.assertRaises(ValueError):
            structural_batch(4,max_conditions=101)

if __name__=="__main__":
    unittest.main()
