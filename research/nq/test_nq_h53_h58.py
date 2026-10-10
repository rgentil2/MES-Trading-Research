import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
import nq_h53_h58 as m
class Tests(unittest.TestCase):
 def test_holdout_reject(self):
  for name in ('root/validation_2025/NQ_03-25_2025_Minute_Last.txt','root/pseudo_forward_2026/NQ_03-26_2026_Minute_Last.txt'):
   self.assertFalse(m.permitted_name(name))
 def test_both_cross_ambiguous(self):
  g=np.zeros((90,5));g[15]=[100,120,80,101,2]
  self.assertIsNone(m.first_reject(g,110,90))
 def test_first_failed_acceptance_no_retry(self):
  g=np.zeros((90,5));g[:,1]=110;g[:,2]=90;g[:,3]=100;g[15]=[110,121,109,121,3];g[16]=[119,122,111,115,3];g[17]=[110,122,101,99,3]
  self.assertIsNone(m.first_reject(g,120,80))
 def test_accepted_volume(self):
  g=np.zeros((90,5));g[:,4]=100;g[15,3]=101;g[16,3]=101
  self.assertEqual(m.accepted_pm_break(g,100,90,np.full(90,50.)),(16,1))
 def test_fee(self):self.assertAlmostEqual(m.FRICTION,25.74)
 def test_bracket_stop_first(self):
  g=np.zeros((390,5));g[:,0]=100;g[:,1]=100;g[:,2]=100;g[15,1]=105;g[15,2]=95
  pnl,why=m.bracket(g,14,1,100,20)
  self.assertEqual(why,'STOP');self.assertAlmostEqual(pnl,-85.74)
 def test_not_frozen_raises_before_load(self):
  with self.assertRaisesRegex(RuntimeError,'BEFORE loading'):m.main('/no/file','/no/out',False)
if __name__=='__main__':unittest.main()