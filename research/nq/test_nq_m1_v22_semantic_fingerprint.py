"""NQ canonical search mechanism IDs: synthetic logic tests, no market data."""
import copy
import unittest
from research.nq import nq_m1_v22_semantic_fingerprint as f
from research.nq import nq_m1_v21_semantic_generator as v


def leaf(op="RISING", period=12, lag=3, threshold=None):
    x={"op":op,"indicator":{"name":"RSI","parameters":{"period":period}}}
    if threshold is None:x["lag_completed_bars"]=lag
    else:x["threshold"]=threshold
    return x


class TestNQSemanticGroups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template=next(r["strategy"] for r in
            v.generate(100,seed=20261027,supported_only=True)["rows"]
            if r["audit"]["semantic_status"]=="SEMANTICALLY_EXECUTABLE_UNCERTIFIED")

    def valid(self):
        return copy.deepcopy(self.template)

    def test_alias_equivalent_rising_and_above_lag(self):
        s=self.valid()
        s["long"]=leaf("RISING")
        a=f.semantic_fingerprint(s)
        s["long"]=leaf("ABOVE_LAG")
        self.assertEqual(a,f.semantic_fingerprint(s))

    def test_nested_and_commutative_associative_idempotent(self):
        a,b,c=leaf("RISING",12),leaf("FALLING",13),leaf("ABOVE_LAG",14)
        s=self.valid()
        s["long"]={"op":"AND","left":a,"right":{"op":"AND","left":b,"right":c}}
        h=f.semantic_fingerprint(s)
        s["long"]={"op":"AND","left":{"op":"AND","left":c,"right":a},
                   "right":{"op":"AND","left":b,"right":a}}
        self.assertEqual(h,f.semantic_fingerprint(s))

    def test_or_is_not_and_and_threshold_is_active(self):
        a,b=leaf("ABOVE_LEVEL",10,threshold=30.),leaf("BELOW_LEVEL",10,threshold=70.)
        s=self.valid()
        s["long"]={"op":"AND","left":a,"right":b}
        h=f.semantic_fingerprint(s)
        s["long"]={"op":"OR","left":a,"right":b}
        self.assertNotEqual(h,f.semantic_fingerprint(s))
        s["long"]=a
        h=f.semantic_fingerprint(s)
        s["long"]=leaf("ABOVE_LEVEL",10,threshold=31.)
        self.assertNotEqual(h,f.semantic_fingerprint(s))

    def test_identity_metadata_must_not_change_semantics(self):
        s=self.valid()
        a=f.semantic_fingerprint(s)
        s["id"]="ARBITRARY"
        s["lineage"]={"method":"changed"}
        self.assertEqual(a,f.semantic_fingerprint(s))

    def test_distinct_stop_policy_alters_hash(self):
        s=self.valid()
        a=f.semantic_fingerprint(s)
        s["exit"]["exit_after_bars"]=18
        self.assertNotEqual(a,f.semantic_fingerprint(s))

    def test_inert_indicator_parameter_cannot_pass(self):
        s=self.valid()
        x=next(v._iter_leaves(s["long"]))
        x["indicator"]["parameters"]["decorative"]=88
        with self.assertRaises(ValueError):
            f.semantic_fingerprint(s)

    def test_one_contract_nq_only(self):
        s=self.valid()
        s["position_sizing"]={"instrument":"MNQ","contracts":1}
        with self.assertRaises((ValueError,PermissionError)):
            f.semantic_fingerprint(s)

    def test_reproducible_frozen_100_cohort_no_market(self):
        a=f.audit_frozen_100()
        b=f.audit_frozen_100()
        self.assertEqual(a,b)
        self.assertEqual(a["cohort_n"],100)
        self.assertEqual(a["executably_semantic_n"],82)
        self.assertEqual(a["registered_blocks"],132)
        self.assertEqual(a["holdouts"],"SEALED")
        self.assertIsNone(a["economic_metrics"])

if __name__=="__main__":
    unittest.main()
