"""B05 synthetic VWAP, no-lookahead, model ablations and priority tests."""
from __future__ import annotations
import unittest
from qc_tick_day import utc_bounds
from nq_tick_short_horizon import STEP_100NS,OR_START,dev_day
from nq_b05_t11_vwap import (causal_vwap,vwapside_signal,
                             FIRST_SIGNAL,COOLDOWN_BARS)
from nq_b05_t11_month import tagged_signals,monthly_audit
from nq_b05_t11_aggregate import aggregate

DAY='2025-10-15'

def synthetic(i=1200):
    bars=[[20010,20012,20008,20010,10,10] for _ in range(2880)]
    den=[100]*2880;num=[20000*100]*2880
    bars[i-6]=[20008,20009,20006,20008,10,10]
    bars[i-3]=[20004,20007,20002,20004,20,20]
    bars[i-1]=[20002,20004,19999,20001,20,20]
    bars[i]=[20002,20005,20001,20004,20,20]
    for k in range(i-5,i+1):bars[k][4]=20
    return bars,num,den

class T11Tests(unittest.TestCase):
    def test_valid_long_causal_signal(self):
        bars,num,den=synthetic()
        self.assertTrue(vwapside_signal(bars,num,den,1200,1))
        self.assertFalse(vwapside_signal(bars,num,den,1200,-1))
    def test_activity_ablation(self):
        bars,num,den=synthetic()
        for k in range(1195,1201):bars[k][4]=1
        self.assertFalse(vwapside_signal(bars,num,den,1200,1))
        self.assertTrue(vwapside_signal(bars,num,den,1200,1,no_activity=True))
    def test_pullback_ablation(self):
        bars,num,den=synthetic()
        for k in range(1194,1200):bars[k][2]=20004
        self.assertFalse(vwapside_signal(bars,num,den,1200,1))
        self.assertTrue(vwapside_signal(bars,num,den,1200,1,no_pullback=True))
    def test_previous_close_and_acceptance_failclosed(self):
        bars,num,den=synthetic()
        bars[1199][3]=20008
        self.assertFalse(vwapside_signal(bars,num,den,1200,1))
        bars,num,den=synthetic()
        for k in range(1170,1194):bars[k][3]=20000
        self.assertFalse(vwapside_signal(bars,num,den,1200,1))
    def test_vwap_source_future_print_no_lookahead(self):
        base,_=utc_bounds(dev_day(DAY))
        e=[
          (base+OR_START*STEP_100NS+1000,20001,3),
          (base+(OR_START+1)*STEP_100NS+1000,20003,7)]
        n,d=causal_vwap(e,DAY)
        j=OR_START+1
        self.assertEqual(n[j],20001*3+20003*7)
        self.assertEqual(d[j],10)
        future=(base+(OR_START+5)*STEP_100NS+1000,30000,500)
        n2,d2=causal_vwap(e+[future],DAY)
        self.assertEqual((n[j],d[j]),(n2[j],d2[j]))
        self.assertNotEqual((n[j+5],d[j+5]),(n2[j+5],d2[j+5]))
    def test_stale_missing_bar_rejected(self):
        bars,num,den=synthetic()
        bars[1190]=None
        self.assertFalse(vwapside_signal(bars,num,den,1200,1))
    def test_t05_tie_is_fixed_priority(self):
        v,t=tagged_signals([(1200,-1),(1220,1)],[(1200,1),(1210,1)])
        self.assertEqual(t,1)
        self.assertEqual(v,[(1200,-1,'T05_377'),
                            (1210,1,'T11_FULL'),(1220,1,'T05_377')])
    def test_sealed_month_disallowed_without_root_lookup(self):
        class Poison:
            def __fspath__(self):raise AssertionError('Accessed sealed root')
        with self.assertRaises(ValueError):monthly_audit(Poison(),'2026-07')
        with self.assertRaises(ValueError):monthly_audit(Poison(),'2026-05')
    def test_missing_all_months_is_not_a_result(self):
        with self.assertRaises(ValueError):aggregate({})

if __name__=='__main__':unittest.main()
