import json,unittest
from pathlib import Path
from nq_gate1_statistical_scorecard import bh_adjust,holm_family,evaluation

ROOT=Path(__file__).resolve().parents[2]
class Gate1ScorecardTests(unittest.TestCase):
    def test_bh_all_declared_including_losers(self):
        a=bh_adjust({'a':.01,'b':.04,'c':.20,'d':1.})
        self.assertAlmostEqual(a['a'],.04)
        self.assertAlmostEqual(a['b'],.08)
        self.assertAlmostEqual(a['c'],.2666666666667)
        self.assertAlmostEqual(a['d'],1.)
    def test_holm_family_alpha_not_screen_q(self):
        c=holm_family({'a':.0001,'b':.05,'c':.2},.001)
        self.assertTrue(c['a'])
        self.assertFalse(c['b'])
        self.assertFalse(c['c'])
    def test_no_bad_input(self):
        for bad in ({},{'a':-1},{'a':float('nan')},{'a':1.1}):
            with self.assertRaises(ValueError):bh_adjust(bad)
    def test_source_exact_parity_and_holdouts(self):
        z=evaluation(ROOT)
        self.assertEqual(len(z['H67_H78_historical_screen']),12)
        self.assertEqual(z['historical_gate1_n_pass'],0)
        self.assertEqual(len(z['T_recent_missing_statistical_evidence']),9)
        d={r['id']:r for r in z['H67_H78_historical_screen']}
        self.assertAlmostEqual(d['NQ-H69']['q_BH_six'],.115188,5)
        self.assertAlmostEqual(d['NQ-H77']['q_BH_six'],.046795,5)
        self.assertTrue(d['NQ-H77']['gates']['BH_q_le_0_10'])
        self.assertFalse(d['NQ-H77']['gates']['N_gt_150'])
        self.assertFalse(d['NQ-H69']['gates']['BH_q_le_0_10'])
        self.assertTrue(all(not r['Holm_descriptive_family_pass'] for r in d.values()))
        self.assertTrue(all(x['gate1_exploratory_pass'] is None
                            and x['q_BH'] is None
                            for x in z['T_recent_missing_statistical_evidence']))
    def test_fail_closed_modified_family_membership(self):
        from nq_gate1_statistical_scorecard import family_rows
        a=json.loads((ROOT/'results/nq_h67_h72/NQ_H67_H72_REPORT_2020_2024.json').read_text())
        b=json.loads((ROOT/'results/development/nq_h67_h72_family.json').read_text())
        del a['hypotheses']['NQ-H71']
        with self.assertRaises(ValueError):family_rows(a,b,6)
    def test_fail_closed_holdout_loaded(self):
        from nq_gate1_statistical_scorecard import family_rows
        a=json.loads((ROOT/'results/nq_h73_h78/NQ_H73_H78_REPORT_2020_2024.json').read_text())
        b=json.loads((ROOT/'results/development/nq_h73_h78_family.json').read_text())
        a['holdout_2025_loaded']=True
        with self.assertRaises(ValueError):family_rows(a,b,7)
if __name__=='__main__':unittest.main()
