import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from nq_h67_h72_combined_strategies import select,ordered_records,bracket,active_regime,COST,portfolio_equity
class Tests(unittest.TestCase):
 def sig(self,h,idx=14,side=1):return {'hypothesis':h,'signal_idx':idx,'side':side}
 def test_consensus(self):
  p,c=ordered_records([self.sig('NQ-H55'),self.sig('NQ-H56')]);self.assertEqual(c['hypothesis'],'CONSENSUS55_56')
 def test_no_consensus_on_conflict(self):
  _,c=ordered_records([self.sig('NQ-H55'),self.sig('NQ-H56',side=-1)]);self.assertIsNone(c)
 def test_h67_follows_h09_priority(self):
  p,c=ordered_records([self.sig('NQ-H09'),self.sig('NQ-H55'),self.sig('NQ-H56')]);self.assertEqual(select(67,p,c)['hypothesis'],'NQ-H09')
 def test_h68_h55_only(self):
  p,c=ordered_records([self.sig('NQ-H55')]);self.assertIsNone(select(67,p,c));self.assertEqual(select(68,p,c)['hypothesis'],'NQ-H55')
 def test_h69_h56_only(self):
  p,c=ordered_records([self.sig('NQ-H56')]);self.assertEqual(select(69,p,c)['hypothesis'],'NQ-H56')
 def test_h70_late_fallback(self):
  p,c=ordered_records([self.sig('NQ-H29',29)]);self.assertEqual(select(70,p,c)['signal_idx'],29)
 def test_h71_late_fallback(self):
  p,c=ordered_records([self.sig('NQ-H54',16)]);self.assertEqual(select(71,p,c)['signal_idx'],16)
 def test_h72_regime_and_lookahead(self):
  p,c=ordered_records([self.sig('NQ-H09'),self.sig('NQ-H55'),self.sig('NQ-H56'),self.sig('NQ-H29',29),self.sig('NQ-H54',16)])
  self.assertEqual(select(72,p,c,'HIGH')['hypothesis'],'NQ-H09');self.assertEqual(select(72,p,c,'LOW')['hypothesis'],'CONSENSUS55_56');self.assertIsNone(select(72,p,c,None))
 def test_older_h54_cannot_veto_early_trade(self):
  p,c=ordered_records([self.sig('NQ-H09'),self.sig('NQ-H54',16,side=-1)]);self.assertEqual(select(71,p,c)['hypothesis'],'NQ-H09')
 def test_stop_first_ohlc_tie(self):
  a=np.zeros((60,5));a[:,0]=100;a[:,1]=100;a[:,2]=100
  a[15,1]=103;a[15,2]=96
  pnl,status,_,_,_=bracket(a,14,1,100,10)
  self.assertEqual(status,'STOP');self.assertAlmostEqual(pnl,-6.88)
 def test_worse_gap_at_stop(self):
  a=np.zeros((60,5));a[:,0]=100;a[:,1]=100;a[:,2]=100
  a[15,0]=96;a[15,1]=100;a[15,2]=96
  pnl,status,_,_,_=bracket(a,14,1,100,10)
  self.assertEqual(status,'STOP');self.assertAlmostEqual(pnl,-11.88)
 def test_time_exit(self):
  a=np.zeros((60,5));a[:,0]=100;a[:,1]=100;a[:,2]=100;a[45,0]=102
  pnl,status,_,_,_=bracket(a,14,1,100,10)
  self.assertEqual(status,'TIME');self.assertAlmostEqual(pnl,0.12)
 def test_costs(self):self.assertAlmostEqual(COST,3.88)
 def test_frozen_required(self):
  from nq_h67_h72_combined_strategies import assert_frozen
  with self.assertRaises(RuntimeError):assert_frozen(Path('/tmp/fake-nonexistent-h67-repo'))
 def test_price_input_uses_only_2020_to_2024(self):
  from nq_h05_h07_level_volume_screen import permitted_name
  self.assertFalse(permitted_name('x/development_2020_2024/NQ_03-26_2026_Minute_Last.txt'))
  self.assertFalse(permitted_name('x/holdout_2025/NQ_03-25_2025_Minute_Last.txt'))
if __name__=='__main__':unittest.main()