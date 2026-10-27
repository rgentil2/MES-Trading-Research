"""No-price V2 S0 semantic lint: full 132-block universe remains registered."""
import unittest
from research.nq import nq_m1_v2_semantic_lint as s
from research.nq import nq_m1_v2_generator as g


class TestV2SemanticLint(unittest.TestCase):
    def test_all_38_implemented_names_have_explicit_used_parameter_map(self):
        self.assertEqual(len(s.USED),38)
        self.assertEqual(s.USED["SMA"],{"period","source"})
        self.assertEqual(s.USED["RSI"],{"period"})
        self.assertEqual(s.USED["OBV"],set())
        self.assertEqual(s.USED["True Range"],set())

    def test_inactive_thresholds_flagged_not_discarded(self):
        leaf=lambda name,params:{"op":"RISING",
               "indicator":{"name":name,"parameters":params},
               "lag_completed_bars":3}
        strategy={"id":"SYNTH",
                  "long":leaf("RSI",{"period":10,"lower_level":25,"upper_level":75}),
                  "short":leaf("SMA",{"period":12,"source":"hlc3"})}
        v=s.audit_strategy(strategy)
        self.assertEqual(v["economic_promotion"],"BLOCKED_UNUSED_PARAMETERS")
        self.assertEqual(v["inactive"][0]["fields"],["lower_level","upper_level"])
        self.assertEqual(v["counts"]["leaves"],2)

    def test_no_extra_parameters_means_structural_consistency_not_trading_pass(self):
        leaf=lambda name,params:{"op":"ABOVE_LAG",
               "indicator":{"name":name,"parameters":params},
               "lag_completed_bars":3}
        v=s.audit_strategy({"id":"SYNTH",
                           "long":leaf("WMA",{"period":12,"source":"hl2"}),
                           "short":leaf("ATR",{"period":12})})
        self.assertEqual(v["economic_promotion"],
                         "SEMANTICALLY_CONSISTENT_NOT_VALIDATED")
        self.assertEqual(v["counts"]["leaves"],2)
        self.assertNotIn("pnl",str(v))

    def test_frozen_100_semantics_never_reads_prices_or_2025_26(self):
        report=s.audit_frozen_100()
        self.assertEqual(report["registered_blocks"],132)
        self.assertEqual(report["current_scalar_calculators"],38)
        self.assertEqual(report["candidate_count"],100)
        self.assertTrue(report["no_market_data"])
        self.assertFalse(report["formal_gates_run"])
        self.assertEqual(report["compatible_manifest_sha256"],
                          "e05f93e8bd73f9c43a2ed48dbc5b6ac813b9d81400309a026fb4de81389b0bf2")

if __name__=="__main__":
    unittest.main()
