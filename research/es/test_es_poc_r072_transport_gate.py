import unittest
import pandas as pd
from es_poc_r072_transport_gate import execute, SPEC, SLIP, stats, report_gap

class TransportInvariantTests(unittest.TestCase):
    def sample(self, side='LONG', stop_hit=False):
        ts=pd.date_range('2023-10-12 09:31',periods=90,freq='min',tz='America/New_York')
        rows=[]
        for i,t in enumerate(ts):
            hi=100.5;lo=99.5
            if stop_hit and i==1:
                if side=='LONG': lo=80
                else: hi=120
            rows.append({'timestamp_et':t,'open':100.,'high':hi,'low':lo,'close':100.,'contract':'ES 12-23',
                         'session_date':'2023-10-12','year':2023})
        return pd.DataFrame(rows)
    def test_frozen_parameters(self):
        self.assertEqual(SPEC['POC']['stop_atr'],.45)
        self.assertEqual(SPEC['R072']['stop_atr'],.70)
    def test_time_exit_h15_is_signal_plus_16_bar(self):
        g=self.sample()
        t=execute(g,0,'SHORT',atr=20,strategy='POC')
        self.assertEqual(t['exit_type'],'TIME')
        self.assertEqual(t['exit_et'],str(g.timestamp_et.iloc[16]))
    def test_time_exit_h30_is_signal_plus_31_bar(self):
        g=self.sample()
        t=execute(g,0,'LONG',atr=20,strategy='R072')
        self.assertEqual(t['exit_type'],'TIME')
        self.assertEqual(t['exit_et'],str(g.timestamp_et.iloc[31]))
    def test_stop_short(self):
        g=self.sample('SHORT',stop_hit=True)
        t=execute(g,0,'SHORT',atr=20,strategy='POC')
        self.assertEqual(t['exit_type'],'STOP')
        self.assertLess(t['net_es'],0)
    def test_stop_long(self):
        g=self.sample('LONG',stop_hit=True)
        t=execute(g,0,'LONG',atr=20,strategy='R072')
        self.assertEqual(t['exit_type'],'STOP')
        self.assertLess(t['net_es'],0)
    def test_gap_or_missing_middle_bar_is_rejected(self):
        g=self.sample().drop(index=5).reset_index(drop=True)
        self.assertIsNone(execute(g,0,'SHORT',20,'POC'))
    def test_fee_point_value_and_stops(self):
        g=self.sample();t=execute(g,0,'SHORT',20,'POC')
        self.assertAlmostEqual(t['net_es'],(t['exit_price']-t['entry_price'])*(-50)-4.68,places=2)
        self.assertGreater(t['stop_risk_es'],t['stop_risk_mes']*8)
    def test_gap_statistics(self):
        x=pd.DataFrame({'date':['2021-01-01','2021-01-11']})
        r=report_gap(x)
        self.assertEqual(r['gaps_gt_7'],1)
if __name__=='__main__': unittest.main()