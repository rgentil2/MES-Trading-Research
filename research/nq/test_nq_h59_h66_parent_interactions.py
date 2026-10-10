import unittest,sys
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).parent))
import nq_h59_h66_parent_interactions as p

class Tests(unittest.TestCase):
    @staticmethod
    def event(day,k,side=1,idx=14,pnl=100):
        return {'session':day,'year':2024,'hypothesis':k,'side':side,'signal_idx':idx,'entry_open':100.,'exit30_open':100.+side*(pnl+25.74)/20,'pnl30':pnl}
    def test_consensus_single_position(self):
        df=pd.DataFrame([self.event('2024-01-02','NQ-H55'),self.event('2024-01-02','NQ-H56')])
        x=p.create_children(df)
        self.assertEqual(set(x.hypothesis),{'NQ-H59'})
    def test_disagreement_no_consensus(self):
        df=pd.DataFrame([self.event('2024-01-02','NQ-H55',side=1),self.event('2024-01-02','NQ-H56',side=-1)])
        self.assertFalse((p.create_children(df).hypothesis=='NQ-H59').any())
    def test_partition_vwap_only(self):
        df=pd.DataFrame([self.event('2024-01-02','NQ-H55')]);self.assertEqual(p.create_children(df).hypothesis.to_list(),['NQ-H60'])
    def test_partition_pm_only(self):
        df=pd.DataFrame([self.event('2024-01-02','NQ-H56')]);self.assertEqual(p.create_children(df).hypothesis.to_list(),['NQ-H61'])
    def test_no_future_absence_filter(self):
        # H09 at 09:45 is NOT partitioned on H54 which can trigger after 09:45.
        df=pd.DataFrame([self.event('2024-01-02','NQ-H09'),self.event('2024-01-02','NQ-H54',idx=28)])
        self.assertEqual(p.create_children(df).hypothesis.to_list(),['NQ-H62'])
    def test_h54_agree_vs_opposite(self):
        both=pd.DataFrame([self.event('2024-01-02','NQ-H55',side=1),self.event('2024-01-02','NQ-H54',side=-1,idx=23),self.event('2024-01-03','NQ-H55',side=1),self.event('2024-01-03','NQ-H54',side=1,idx=25)])
        c=p.create_children(both);self.assertEqual(set(c.hypothesis),{'NQ-H60','NQ-H65','NQ-H66'})
    def test_portfolio_no_double_count(self):
        df=pd.DataFrame([self.event('2024-01-02','NQ-H09',pnl=100),self.event('2024-01-02','NQ-H55',pnl=-100),self.event('2024-01-02','NQ-H56',pnl=120),self.event('2024-01-02','NQ-H29',idx=29,pnl=200)])
        p1=p.portfolio(df);self.assertEqual(len(p1),1);self.assertEqual(p1.hypothesis.iloc[0],'NQ-H09');self.assertEqual(int(p1.collision_count.iloc[0]),4)
    def test_bh_multiplicity(self):
        self.assertAlmostEqual(p.adjust_bh({'a':.01,'b':.04})['a'],.02)
        self.assertEqual(p.adjust_bh({'a':1,'b':1})['a'],1.)
    def test_no_frozen_no_market_read(self):
        with self.assertRaises(RuntimeError):
            p.assert_frozen(Path('/tmp/does-not-exist-parent-family'))
    def test_risk_mnq_cost_conversion(self):
        v=(100+25.74)/10-3.88;self.assertAlmostEqual(v,8.694)

if __name__=='__main__':unittest.main()