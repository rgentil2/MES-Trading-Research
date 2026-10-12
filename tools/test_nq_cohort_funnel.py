"""Source-only regression protections for NQ research funnel; NO market data."""
import copy,json,unittest
from pathlib import Path
from nq_cohort_funnel import validate,render,POLICY,LEDGER

class NQCohortFunnelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads(POLICY.read_text())
        cls.l=json.loads(LEDGER.read_text())

    def mutated(self):
        return copy.deepcopy(self.p),copy.deepcopy(self.l)

    def test_active_four_cohort_snapshot(self):
        z=validate(*self.mutated())
        self.assertEqual(z["status"],"FUNNEL_VALIDATED")
        self.assertEqual(z["new_D0_diverse_candidates"],31)
        self.assertEqual(z["new_D0_gap_to_next_D1"],0)
        self.assertEqual(z["D2_batch_size"],0)

    def test_cannot_pass_new_batch_D1_with_one_idea(self):
        p,l=self.mutated()
        q=next(x for x in l["cohorts"] if x["id"]=="NQ-C59-NEXT")
        q["D0"]["diverse_ids"]=["T59"]
        with self.assertRaises(ValueError):validate(p,l)

    def test_D1_must_include_all_30_original_family_ids(self):
        p,l=self.mutated()
        l["cohorts"][0]["D1"]["evaluated_ids"].remove("T48")
        with self.assertRaises(ValueError):validate(p,l)

    def test_no_promote_D0_low_power_to_D1_survivor(self):
        p,l=self.mutated()
        l["cohorts"][0]["D1"]["statistical_screen_pass_ids"]=["T48"]
        with self.assertRaises(ValueError):validate(p,l)

    def test_no_false_statistical_pass_for_q_0212(self):
        p,l=self.mutated()
        l["cohorts"][0]["D1"]["statistical_screen_pass_ids"]=["T29"]
        with self.assertRaises(ValueError):validate(p,l)

    def test_no_economic_D2_for_range_observation(self):
        p,l=self.mutated()
        l["pooled_D2"]["d2_batch_ids"]=["T29","T45"]
        with self.assertRaises(ValueError):validate(p,l)

    def test_one_hypothesis_D2_is_forbidden(self):
        p,l=self.mutated()
        l["cohorts"][0]["D1"]["economic_screen_pass_ids"]=["T29"]
        l["pooled_D2"]["economically_eligible_ids"]=["T29"]
        l["pooled_D2"]["d2_batch_ids"]=["T29"]
        with self.assertRaises(ValueError):validate(p,l)

    def test_holdouts_cannot_open_to_fill_shortlist(self):
        p,l=self.mutated()
        l["holdouts_opened"]=True
        with self.assertRaises(ValueError):validate(p,l)

    def test_legacy_T05_benchmark_never_qualifies(self):
        p,l=self.mutated()
        l["separate_baselines"][0]["qualifies_D1_to_D2"]=True
        with self.assertRaises(ValueError):validate(p,l)

    def test_d0_mask_near_duplicate_cannot_be_diverse(self):
        p,l=self.mutated()
        l["cohorts"][0]["D0"]["diverse_ids"].append("T53")
        with self.assertRaises(ValueError):validate(p,l)

    def test_no_double_count_across_cohorts(self):
        p,l=self.mutated()
        l["cohorts"][-1]["all_preregistered_ids"].append("T29")
        with self.assertRaises(ValueError):validate(p,l)

    def test_dashboard_reports_real_stages_not_predicted_profit(self):
        txt=render(*self.mutated())
        for v in ("31", "T59", "T60", "38", "0", "T05"):
            self.assertIn(v,txt)
        self.assertNotIn("validada para fondeo",txt.lower())

if __name__=="__main__":
    unittest.main()
