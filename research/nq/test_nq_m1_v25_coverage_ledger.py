"""No market; verify honest 132-block coverage and immutable catalogue."""
import unittest
from collections import Counter
from research.nq.nq_m1_v25_coverage_ledger import audit

class TestCoverageLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=audit()

    def test_explicit_complete_catalogue_and_unique_ids(self):
        rows=self.result["rows"]
        self.assertEqual(len(rows),132)
        self.assertEqual(len({x["id"] for x in rows}),132)
        self.assertEqual(len({x["name"] for x in rows}),132)

    def test_honest_prototype_numbers(self):
        self.assertEqual(self.result["counts"],{
            "FROZEN_V21_RUNTIME":38,"ISOLATED_20261027":5,
            "ISOLATED_20261028":12,"NOT_IMPLEMENTED":77
        })
        self.assertEqual(self.result["historically_original_external_parity"],15)

    def test_no_prototype_claims_performance_or_certification(self):
        self.assertFalse(self.result["all_132_certified"])
        self.assertFalse(self.result["economics_executed"])
        self.assertEqual(self.result["holdouts"],"SEALED")
        self.assertTrue(all(not row["eligible_for_economic_selection"]
                            for row in self.result["rows"]))
        self.assertTrue(all(not row["verified_external_implementation"]
                            for row in self.result["rows"]))

    def test_every_candlestick_requires_real_implementation(self):
        pattern_names={"Doji","Hammer","Shooting Star","Engulfing",
          "Harami","Morning Star","Evening Star","Three White Soldiers",
          "Three Black Crows","Inside Bar","Outside Bar","Marubozu"}
        pending={r["name"] for r in self.result["rows"]
                 if r["status"]=="NOT_IMPLEMENTED"}
        self.assertTrue(pattern_names<=pending)

    def test_no_duplicate_anchor_semantics_claims(self):
        rows={x["name"]:x for x in self.result["rows"]}
        self.assertEqual(rows["Opening Range"]["status"],"ISOLATED_20261028")
        self.assertEqual(rows["Initial Balance"]["status"],"ISOLATED_20261028")
        # These share a scalar range-width formula, not independent alpha proof.
        self.assertTrue(self.result["external_certification_not_inferred_from_grouping"])

if __name__=="__main__":
    unittest.main()
