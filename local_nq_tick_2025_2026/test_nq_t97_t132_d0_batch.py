import unittest
from pathlib import Path
from nq_t97_t132_d0_batch import load_registry,month_stage,aggregate,shortlist,IDS
from nq_t97_t132_d0_features import classify_day,FEATURES,CASE,CONTROL,OTHER,MISSING
from test_nq_t61_t96_d0_cohort import DAY,sample
from nq_b05h01_trade_expansion_month import et_edge

class MultiScaleCohort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg=load_registry()
    def test_full_36_preregistered_six_mechanisms(self):
        self.assertEqual(tuple(z['id'] for z in self.reg['members']),IDS)
        self.assertEqual(tuple(z['feature'] for z in self.reg['members']),FEATURES)
        self.assertEqual(len(set(z['block'] for z in self.reg['members'])),6)
    def test_no_outcomes_all_36_classify(self):
        z=classify_day(sample(),DAY,self.reg)
        self.assertEqual(len(z),36)
        self.assertTrue(set(z.values())<=set((CASE,CONTROL,OTHER,MISSING)))
        self.assertEqual(z['T103'],MISSING) # not 2 full macro 4181
    def test_future_trade_cannot_change_D0(self):
        x=sample();s=classify_day(x,DAY,self.reg)
        y=x+[(et_edge(DAY,10,31),101000,100)]
        self.assertEqual(s,classify_day(y,DAY,self.reg))
    def test_tied_timestamp_order_cannot_flip_signal(self):
        e=sample()
        e[1450]=(e[1450][0],99915,8)
        e[1451]=(e[1450][0],100115,4)
        a=classify_day(e,DAY,self.reg)
        e[1450],e[1451]=e[1451],e[1450]
        self.assertEqual(a,classify_day(e,DAY,self.reg))
    def test_new_D0_must_fail_closed_in_sealed_month(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/NO_FILES'), '2026-09',self.reg)
    def test_aggregate_requires_all_months(self):
        with self.assertRaises(ValueError):aggregate({},self.reg)
    def test_case_overlap_duplicates_not_distinct(self):
        z={'T97':{'N_case':50},'T98':{'N_case':50}}
        reg={'members':[{'id':'T97','block':self.reg['blocks'][0]},
            {'id':'T98','block':self.reg['blocks'][0]}]}
        keep,dups=shortlist(['T97','T98'],z,{'T97__T98':49},reg)
        self.assertEqual(keep,['T97'])
        self.assertEqual(len(dups),1)
    def test_registry_has_no_sealed_months(self):
        self.assertEqual(self.reg['source_dev_months'][-1],'2026-04')
        self.assertFalse(self.reg['OOS_opened'])
        self.assertFalse(self.reg['future_outcomes_in_D0'])
if __name__=='__main__':unittest.main()
