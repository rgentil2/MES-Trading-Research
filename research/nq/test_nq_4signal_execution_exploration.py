import unittest
import numpy as np
from nq_4signal_execution_exploration import simulate_bar_path, PRIORITY, STOPS, TARGETS, TIMEOUTS

class ExecutionTests(unittest.TestCase):
 def bars(self):
  x=np.zeros((64,5));x[:,0]=100.;x[:,1]=100.25;x[:,2]=99.75;x[:,3]=100.;x[:,4]=100.
  return x
 def test_stop_first_ambiguous_bar(self):
  b=self.bars();b[0,1]=103.;b[0,2]=97.
  x=simulate_bar_path(b,0,1,2.,1.,30,5.74,20.)
  self.assertEqual(x['exit_reason'],'STOP');self.assertTrue(x['ambiguous_bar_stop_first'])
 def test_target_hits(self):
  b=self.bars();b[1,1]=106.
  x=simulate_bar_path(b,0,1,2.,2.,30,5.74,20.)
  self.assertEqual(x['exit_reason'],'TARGET')
 def test_loss_gap_through_stop(self):
  b=self.bars();b[1,0]=94; b[1,1]=95; b[1,2]=93
  x=simulate_bar_path(b,0,1,2.,1.,30,5.74,20.)
  self.assertTrue(x['stop_gap_through']);self.assertEqual(x['exit_fill'],93.5)
 def test_short_stop_and_target(self):
  b=self.bars();b[1,1]=103
  x=simulate_bar_path(b,0,-1,2,2,30,5.74,20.)
  self.assertEqual(x['exit_reason'],'STOP')
 def test_minute_time_exit(self):
  b=self.bars();b[30,0]=102
  x=simulate_bar_path(b,0,1,2.,1.,30,5.74,20.)
  self.assertEqual(x['exit_reason'],'TIME');self.assertAlmostEqual(x['pnl'],14.26)
 def test_nq_mnq_contract_scaling(self):
  b=self.bars();b[30,0]=102
  nq=simulate_bar_path(b,0,1,2.,1.,30,5.74,20.)
  mnq=simulate_bar_path(b,0,1,2.,1.,30,1.88,2.)
  self.assertAlmostEqual(nq['pnl'],14.26)
  self.assertAlmostEqual(mnq['pnl'],-1.88+2)
 def test_fixed_grid_and_tie_priority(self):
  self.assertEqual(len(STOPS)*len(TARGETS)*len(TIMEOUTS),18)
  self.assertEqual(PRIORITY['NQ-H09'],0)
if __name__=='__main__':unittest.main()