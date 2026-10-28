"""NQ V2.2 registry range and typed threshold structural checks only."""
import copy
import unittest
from research.nq import nq_m1_v22_structural_preflight as g
from research.nq import nq_m1_v21_semantic_generator as v


class TestNQPreD0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        batch=v.generate(100,seed=20261027,supported_only=True)
        cls.example=next(x["strategy"] for x in batch["rows"]
                         if x["audit"]["semantic_status"]=="SEMANTICALLY_EXECUTABLE_UNCERTIFIED")

    def _clone(self):
        s=copy.deepcopy(self.example)
        s.pop("lineage",None)
        return s

    def test_frozen_100_report_is_not_economic_or_formal_g0(self):
        d=g.frozen_cohort_diagnostic()
        self.assertEqual(d["rows"],100)
        self.assertEqual(d["holdouts"],"SEALED")
        self.assertTrue(d["not_legacy_g0_d0_parity"])
        self.assertFalse(d["market_data_opened"])
        self.assertGreater(d["structurally_executable_count"],0)

    def test_one_supported_semantic_ast_with_registry_valid_params(self):
        x=g.validate_registry_parameters(self._clone())
        self.assertTrue(x["executable_mechanics"])
        self.assertEqual(len(x["semantic_hash"]),64)
        self.assertFalse(x["economics_certified"])

    def test_inert_parameter_is_rejected_by_registry(self):
        s=self._clone()
        node=next(v._iter_leaves(s["long"]))
        node["indicator"]["parameters"]["fake_decorative_param"]=12
        x=g.validate_registry_parameters(s)
        self.assertFalse(x["executable_mechanics"])
        self.assertTrue(any("UNREGISTERED_PARAMETER:" in r for r in x["reason_codes"]))

    def test_indicator_period_below_catalogue_range_fail_closed(self):
        s=self._clone()
        s["long"]={"op":"ABOVE_LAG",
                   "indicator":{"name":"RSI","parameters":{"period":1}},
                   "lag_completed_bars":1}
        out=g.validate_registry_parameters(s)
        self.assertFalse(out["executable_mechanics"])
        self.assertTrue(any(r=="OUT_OF_RANGE_PARAMETER:RSI:period" for r in out["reason_codes"]))

    def test_typed_rsi_level_out_of_declared_domain_is_rejected(self):
        s=self._clone()
        s["long"]={"op":"ABOVE_LEVEL","threshold":500.,
                   "indicator":{"name":"RSI","parameters":{"period":14}}}
        x=g.validate_registry_parameters(s)
        self.assertFalse(x["executable_mechanics"])
        self.assertTrue(any(r.startswith("OUTSIDE_DECLARED_TYPED_LEVEL") for r in x["reason_codes"]))

    def test_unimplemented_broad_indicators_not_promoted(self):
        s=self._clone()
        s["long"]={"op":"RISING","lag_completed_bars":2,
                   "indicator":{"name":"Hilbert Trend Mode","parameters":{"period":21}}}
        r=g.validate_registry_parameters(s)
        self.assertFalse(r["executable_mechanics"])
        self.assertIsNone(r["semantic_hash"])


if __name__=="__main__":
    unittest.main()
