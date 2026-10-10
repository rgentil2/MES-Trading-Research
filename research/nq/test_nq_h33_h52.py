import unittest, numpy as np
from datetime import date
import nq_h33_h52_minute_2020_2024 as m
from nq_h05_h07_level_volume_screen import permitted_name

class Sanity(unittest.TestCase):
 def test_family(self):
  self.assertEqual(len(m.HYPOTHESES),20)
  self.assertEqual(m.HYPOTHESES[0],'NQ-H33')
  self.assertEqual(m.HYPOTHESES[-1],'NQ-H52')
 def test_fee(self):self.assertAlmostEqual(m.FRICTION,25.74,places=4)
 def test_bh(self):
  x=m.bh({'a':.01,'b':.04,'c':.5});self.assertAlmostEqual(x['a'],.03)
  self.assertAlmostEqual(x['b'],.06)
 def test_holm(self):
  x=m.holm({'a':.01,'b':.04,'c':.5});self.assertAlmostEqual(x['a'],.03)
 def test_holdout_firewall(self):
  self.assertTrue(permitted_name('NQMNQ_Research_2020_2026/development_2020_2024/NQ_03-21_2021_Minute_Last.txt'))
  self.assertFalse(permitted_name('NQMNQ_Research_2020_2026/validation_holdout_2025/NQ_03-25_2025_Minute_Last.txt'))
  self.assertFalse(permitted_name('NQMNQ_Research_2020_2026/pseudo_forward_holdout_2026/NQ_03-26_2026_Minute_Last.txt'))
 def test_geometry(self):
  a=np.array([[1,2,0,1,1],[1,3,1,2,1]])
  self.assertEqual(m.range_in(a,0,1),3.)
  self.assertEqual(m.cloc(1,0,2),.5)
 def test_no_data_before_preflight(self):
  with self.assertRaisesRegex(RuntimeError,'preflight'):
   m.run('/nonexistent','/nonexistent',False)
if __name__=='__main__':unittest.main()