"""S0.22 no-market broad-candidate campaign guard tests."""
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from research.nq.nq_m1_v27_first_structural_campaign import run,summarize
from research.nq.nq_m1_v26_structural_generator import structural_batch,one_per_indicator

class TestNQV27StructuralCampaign(unittest.TestCase):
    def test_140_candidate_campaign_and_independent_132_name_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            report=run(140,20261028,Path(d))
            self.assertEqual(report["candidates_generated"],140)
            self.assertEqual(report["indicator_routes"],132)
            self.assertEqual(report["per_indicator_coverage_names"],132)
            self.assertFalse(report["holdouts_opened"])
            self.assertFalse(report["real_ist_ohlcv_loaded"])
            self.assertFalse(report["real_ist_ticks_loaded"])
            self.assertFalse(report["fitness_computed"])
            self.assertEqual(report["candidates_certified_for_trading"],0)
            self.assertEqual(report["economic_gate"]["passed_verified"],0)
            self.assertEqual(sum(report["structural_operators"].values()),140)
            self.assertEqual(sum(report["entries"].values()),140)
            self.assertEqual(sum(report["stop_kinds"].values()),140)
            self.assertEqual(sum(report["profit_target_kinds"].values()),140)
            self.assertGreaterEqual(sum(report["name_frequencies"].values()),280)
            with gzip.open(Path(d)/"nq_v27_candidate_ast.jsonl.gz","rt") as file:
                rows=[json.loads(x) for x in file]
            self.assertEqual(len(rows),140)
            self.assertTrue(all(x["market_data_years_permitted_for_discovery"]==[2020,2021,2022] for x in rows))
            coverage=json.loads((Path(d)/"nq_v27_132_name_coverage.json").read_text())
            self.assertEqual(len({z["indicator"]["name"] for z in coverage["leaves"]}),132)
            self.assertEqual(json.loads((Path(d)/"nq_v27_structural_summary.json").read_text()),report)

    def test_output_bitwise_determinism_across_directories(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            first=run(120,31415,Path(a))
            second=run(120,31415,Path(b))
            self.assertEqual(first,second)
            for name in ("nq_v27_candidate_ast.jsonl.gz","nq_v27_132_name_coverage.json",
                         "nq_v27_structural_summary.json"):
                self.assertEqual((Path(a)/name).read_bytes(),(Path(b)/name).read_bytes())

    def test_summary_refuses_hidden_financial_fields(self):
        b=structural_batch(100)
        b["candidates"][0]["profit_factor"]=999
        with self.assertRaises(PermissionError):
            summarize(b,one_per_indicator())

    def test_bounded_generation_parameter_validation(self):
        with tempfile.TemporaryDirectory() as d:
            for n in (0,99,50001):
                with self.subTest(n=n),self.assertRaises(ValueError):
                    run(n,42,Path(d))
            with self.assertRaises(ValueError):
                run(100,-1,Path(d))
            with self.assertRaises(ValueError):
                run(100,2,Path(d),random_fraction=0)

    def test_broad_sample_all_132_at_scale(self):
        # 2000 is a small smoke probe for campaign composition.
        with tempfile.TemporaryDirectory() as d:
            report=run(2000,20261028,Path(d))
            self.assertEqual(report["candidates_generated"],2000)
            self.assertEqual(report["observed_in_broad_batch"],132)
            self.assertTrue(all(report["structural_operators"].get(x,0)>0
                                for x in ("RANDOM","MUTATE","CROSSOVER")))
            self.assertGreater(report["condition_count_distribution"].get("2",0),0)

if __name__=="__main__":
    unittest.main()
