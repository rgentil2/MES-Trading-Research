"""Deterministic synthetic-only H73-H78 pre-outcome controls; no development ZIP read."""
import json,sys,unittest,tempfile,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
import nq_h73_h78_joint_state_routers as h

class TestStateRouters(unittest.TestCase):
 def setUp(self):
  self.signal={'NQ-H09':{'hypothesis':'NQ-H09','signal_idx':14,'side':1},
               'NQ-H56':{'hypothesis':'NQ-H56','signal_idx':14,'side':-1}}
 def test_all_pair_rules_explicit(self):self.assertEqual(set(h.PAIR),set(range(73,79)))
 def test_v_high_assigns_h09_h73_and_h56_h74(self):
  reg={'V':'HIGH'}
  self.assertEqual(h.pick(73,reg,self.signal)['hypothesis'],'NQ-H09')
  self.assertEqual(h.pick(74,reg,self.signal)['hypothesis'],'NQ-H56')
 def test_v_low_symmetric(self):
  reg={'V':'LOW'}
  self.assertEqual(h.pick(73,reg,self.signal)['hypothesis'],'NQ-H56')
  self.assertEqual(h.pick(74,reg,self.signal)['hypothesis'],'NQ-H09')
 def test_p_expanded_complementary(self):
  reg={'P':'EXPANDED'}
  self.assertEqual(h.pick(75,reg,self.signal)['hypothesis'],'NQ-H56')
  self.assertEqual(h.pick(76,reg,self.signal)['hypothesis'],'NQ-H09')
 def test_p_contracted_complementary(self):
  reg={'P':'CONTRACTED'}
  self.assertEqual(h.pick(75,reg,self.signal)['hypothesis'],'NQ-H09')
  self.assertEqual(h.pick(76,reg,self.signal)['hypothesis'],'NQ-H56')
 def test_g_aligned_complementary(self):
  reg={'G':'ALIGNED'}
  self.assertEqual(h.pick(77,reg,self.signal)['hypothesis'],'NQ-H09')
  self.assertEqual(h.pick(78,reg,self.signal)['hypothesis'],'NQ-H56')
 def test_g_opposed_complementary(self):
  reg={'G':'OPPOSED'}
  self.assertEqual(h.pick(77,reg,self.signal)['hypothesis'],'NQ-H56')
  self.assertEqual(h.pick(78,reg,self.signal)['hypothesis'],'NQ-H09')
 def test_no_future_fallback_if_admitted_parent_missing(self):
  self.assertIsNone(h.pick(73,{'V':'HIGH'},{'NQ-H56':self.signal['NQ-H56']}))
 def test_missing_state_no_trade(self):
  for j in range(73,79):self.assertIsNone(h.pick(j,{},self.signal))
 def test_absent_signals_no_trade(self):
  for j in range(73,79):self.assertIsNone(h.pick(j,{'V':'HIGH','P':'EXPANDED','G':'ALIGNED'},{}))
 def test_each_pair_covers_parent_uniquely(self):
  for j in (73,75,77):
   a,b=h.PAIR[j],h.PAIR[j+1]
   self.assertEqual({a[2],a[4]},{'NQ-H09','NQ-H56'})
   self.assertEqual({a[1],a[3]},{b[1],b[3]})
   self.assertEqual((a[2],a[4]),(b[2],b[4]));self.assertNotEqual(a[1],b[1]);self.assertNotEqual(a[3],b[3])
 def test_context_missing_no_trade(self):
  dates=['2020-01-02','2020-01-03']
  bars=np.zeros((2,390,5))
  self.assertEqual(h.classifications(1,dates,bars,{},{}),{'V':None,'P':None,'G':None})
 def test_bracket_same_bar_stop_first(self):
  g=np.zeros((48,5));g[:,0]=100;g[:,1]=100;g[:,2]=100
  g[16,1]=105;g[16,2]=95
  outcome=h.bracket(g,14,1,100,20)
  self.assertEqual(outcome[1],'STOP')
 def test_bh_no_cherry_pick(self):
  q=h.bh({'a':.001,'b':.01,'c':.20})
  self.assertEqual(q['a'],.003);self.assertEqual(q['b'],.015)
 def test_attestation_missing_fails(self):
  with self.assertRaises(RuntimeError):h.check_attestation(Path('/tmp'),Path('/tmp/not_a_frozen_manifest_7.json'))
 def test_allowlist_rejects_2025(self):
  from nq_h05_h07_level_volume_screen import permitted_name
  self.assertFalse(permitted_name('development_2025_2026/NQ_03-25_2025_Minute_Last.txt'))
 def test_source_frozen_requirements(self):
  self.assertEqual(len(h.SOURCE_FILES),6)
  self.assertEqual(h.FAMILY,'NQ-DEDUCTIVE-ENSEMBLE-H73-H78-V1')

if __name__=='__main__':unittest.main()