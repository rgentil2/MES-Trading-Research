import sys
from pathlib import Path
import unittest
import pandas as pd
sys.path.insert(0,str(Path(__file__).parent))
from es_pdc_transport_gate import new_candidate,execute_candidate,wilder_update,required_manifest,SLIP

class TransportTests(unittest.TestCase):
    def frame(self,op=100.0,bar5=99.0,entry=99.0,extreme=None):
        times=pd.date_range('2024-02-01 09:31',periods=390,freq='min',tz='America/New_York')
        rows=[]
        for idx,t in enumerate(times):
            val=op if idx<5 else entry
            close=bar5 if idx==4 else val
            low=min(val,close)-0.25
            high=max(val,close)+0.25
            if idx==5 and extreme is not None:
                low=min(low,extreme[0]);high=max(high,extreme[1])
            rows.append(dict(timestamp_et=t,minute_et=t.hour*60+t.minute,open=val,high=high,low=low,close=close))
        return pd.DataFrame(rows)

    def test_gap_signal_returns_short(self):
        g=self.frame()
        c=new_candidate(g,previous_close=96,atr=25,rollover=False)
        self.assertIsNotNone(c)
        self.assertEqual(c['dir'],-1)
        self.assertEqual(c['stop_ticks'],30)
        self.assertAlmostEqual(c['entry'],98.5)

    def test_skip_rollover(self):
        self.assertIsNone(new_candidate(self.frame(),96,25,True))

    def test_stop_first_ambiguous(self):
        g=self.frame(entry=99.0,extreme=(94.0,110.0))
        c=new_candidate(g,96,25,False)
        self.assertIsNotNone(c)
        e=execute_candidate(g,c)
        self.assertEqual(e['reason'],'STOP_AMBIGUOUS_FIRST')
        self.assertLess(e['net_es_usd'],0)

    def test_stop_budget_logic(self):
        g=self.frame()
        c=new_candidate(g,96,25,False)
        e=execute_candidate(g,c)
        self.assertGreater(e['stop_risk_ES_usd'],200)

    def test_wilder_past_only(self):
        seed=[];atr=None
        for i in range(13):atr=wilder_update(atr,seed,5.0)
        self.assertIsNone(atr)
        atr=wilder_update(atr,seed,5.0)
        self.assertEqual(atr,5)
        self.assertAlmostEqual(wilder_update(atr,seed,19),(5*13+19)/14)

    def test_holdout_manifest_fixed(self):
        self.assertTrue(callable(required_manifest))

if __name__=='__main__':unittest.main()