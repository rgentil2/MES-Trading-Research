"""Tests for S0.23 10k frozen cohort funnel tracking, no prices/performance."""
import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path
from research.nq.nq_m1_v28_funnel_ledger import (
    inspect_structure,regenerate_and_track,export,STAGES
)
from research.nq.nq_m1_v26_structural_generator import structural_batch,sha

class TestV28FunnelLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.summary=regenerate_and_track()

    def test_full_frozen_10k_sha_and_complete_tracking(self):
        self.assertEqual(len(self.rows),10000)
        self.assertEqual(self.summary["cohort_candidates"],10000)
        self.assertEqual(self.summary["structural_precheck_fail"],0)
        self.assertEqual(self.summary["structural_precheck_pass"],10000)
        self.assertEqual(len({x["id"] for x in self.rows}),10000)
        self.assertEqual(len({x["ast_sha256"] for x in self.rows}),10000)
        self.assertEqual(self.summary["frozen_source_sha256"],
            "b9d2915fc55f86546ef63d74a588df5244d094eeecb4a7c900a4000d47660be9")
        self.assertTrue(all(r["status"]=="STRUCTURALLY_CHECKED_NO_MARKET"
                            for r in self.rows))

    def test_zero_formal_pass_even_if_structurally_valid(self):
        self.assertEqual(self.summary["release_gates_verified"],0)
        self.assertFalse(self.summary["ready_for_economic_execution"])
        self.assertFalse(self.summary["economic_fitness_computed"])
        self.assertFalse(self.summary["market_prices_read"])
        self.assertFalse(self.summary["strategies_ranked"])
        self.assertFalse(self.summary["portfolio_released"])
        self.assertEqual([x["stage"] for x in self.summary["formal_funnel_stages"]],list(STAGES))
        for stage in self.summary["formal_funnel_stages"]:
            self.assertEqual(stage["passed"],0)
            self.assertEqual(stage["unstarted"],10000)
            self.assertEqual(stage["rejected"],0)

    def test_export_csv_and_manifest_are_stable(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            first=export(Path(a),self.rows,self.summary)
            second=export(Path(b),self.rows,self.summary)
            self.assertEqual(first,second)
            self.assertEqual((Path(a)/"nq_v28_candidate_funnel_ledger.csv").read_bytes(),
                             (Path(b)/"nq_v28_candidate_funnel_ledger.csv").read_bytes())
            with (Path(a)/"nq_v28_candidate_funnel_ledger.csv").open() as f:
                rec=list(csv.DictReader(f))
            self.assertEqual(len(rec),10000)
            self.assertEqual(rec[0]["formal_stage"],"PRE_G0_WAITING")
            self.assertEqual(rec[0]["economic_fitness_measured"],"False")
            self.assertNotIn("net_usd",rec[0])
            self.assertEqual(json.loads((Path(a)/"nq_v28_funnel_stage_summary.json").read_text()),first)

    def test_broken_candidate_cannot_be_marked_precheck_ok(self):
        original=structural_batch(2,seed=20261028)["candidates"][0]
        changes=[
            ("market year contamination",lambda s:s.update(market_data_years_permitted_for_discovery=[2025])),
            ("contract contamination",lambda s:s.update(position_sizing={"instrument":"MNQ","contracts":1})),
            ("future offset",lambda s:s.update(signal_uses_completed_bars_only=False)),
            ("commercial position",lambda s:s.update(net_usd=1000)),
            ("tampered identifier",lambda s:s.update(id="NQ26_FAKE")),
            ("changed stop close time",lambda s:s["exit"].update(flat_at_et="15:59")),
            ("faked parent",lambda s:s["lineage"].update(operator="MUTATE",parents=["INVENTED_PARENT"]))
        ]
        for title,make in changes:
            with self.subTest(case=title):
                item=copy.deepcopy(original);make(item)
                with self.assertRaises((ValueError,KeyError)):
                    inspect_structure(item,set(),set())

    def test_no_pnl_fields_from_executable_rows(self):
        forbidden={"net","pnl","trades","fitness","profit_factor",
                   "drawdown","gross_profit","gross_loss"}
        for x in self.rows:
            self.assertFalse(forbidden.intersection(x.keys()))
            self.assertEqual(x["formal_g0_pass"],False)
            self.assertEqual(x["formal_d2_pass"],False)
            self.assertEqual(x["reason"],"NO_HISTORICAL_FILLS_OR_CERTIFIED_INDICATOR_PARITY")

    def test_wrong_frozen_cohort_not_relabelled(self):
        with self.assertRaises(ValueError):
            regenerate_and_track(9999)
        with self.assertRaises(ValueError):
            regenerate_and_track(10000,seed=20261029)

    def test_parent_lineage_existing_before_child(self):
        indices={r["id"]:i for i,r in enumerate(self.rows)}
        for i,r in enumerate(self.rows):
            for parent in r["parent_ids"].split("|") if r["parent_ids"] else []:
                self.assertIn(parent,indices)
                self.assertLess(indices[parent],i)

if __name__=="__main__":
    unittest.main()
