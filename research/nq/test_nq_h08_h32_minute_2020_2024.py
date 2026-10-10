import importlib.util,unittest
from datetime import date
import numpy as np
import pandas as pd
from pathlib import Path
spec=importlib.util.spec_from_file_location('nq25',Path(__file__).with_name('nq_h08_h32_minute_2020_2024.py'))
nq=importlib.util.module_from_spec(spec);spec.loader.exec_module(nq)
class TestMinuteRound(unittest.TestCase):
 def test_exact_25_hypothesis_ids(self):
  self.assertEqual(nq.HYPOTHESES,[f'NQ-H{i:02}' for i in range(8,33)])
 def test_free_fee_separate_slippage(self):
  self.assertAlmostEqual(nq.FRICTION,25.74)
 def test_refuses_without_prereg(self):
  with self.assertRaisesRegex(RuntimeError,'preflight'):
   nq.run(Path('/DELIBERATELY_MISSING_ZIP.zip'),Path('/tmp/any'),False)
 def test_fixed_extraction_cannot_open_holdout(self):
  from nq_h05_h07_level_volume_screen import permitted_name
  self.assertTrue(permitted_name('NQMNQ_Research_2020_2026/development_2020_2024/NQ_03-25_2024_Minute_Last.txt'))
  self.assertFalse(permitted_name('NQMNQ_Research_2020_2026/validation_holdout_2025/NQ_03-25_2025_Minute_Last.txt'))
  self.assertFalse(permitted_name('NQMNQ_Research_2020_2026/pseudo_forward_holdout_2026/NQ_06-26_2026_Minute_Last.txt'))
 def test_25_events_only_at_fixed_causal_minutes(self):
  a=np.zeros((24,390,5));a[:,:,0:4]=20000.;a[:,:,4]=100.
  for t in range(24):a[t,:,3]=20000.+t*3
  dates=pd.date_range('2024-01-02',periods=24,freq='B').strftime('%Y-%m-%d').tolist()
  ov=pd.DataFrame({'on_count':[900]*24,'on_high':[20100.]*24,'on_low':[19900.]*24},index=dates)
  sig=nq.local_prices(21,dates,a,ov)
  self.assertLessEqual(len(sig),25)
  self.assertTrue(all(i in (14,29,44,59,74) and side in(-1,1) for i,side in sig.values()))
 def test_bh_and_holm_include_all_tests(self):
  p={f'H{i}':.5 for i in range(25)}; p['H0']=.001
  self.assertEqual(len(nq.bh(p)),25)
  self.assertAlmostEqual(nq.holm(p)['H0'],.025)
if __name__=='__main__':unittest.main()