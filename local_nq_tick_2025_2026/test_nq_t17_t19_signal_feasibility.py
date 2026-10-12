import unittest
from unittest.mock import patch
from types import SimpleNamespace
from nq_b05h_atomic_print_bars import CompletedPrintBar
from nq_b05h01_trade_expansion_month import et_edge
from nq_t17_t19_signal_feasibility import (
    t17,t18,t19,detect,IDS,preopen_pairs)
DAY='2025-10-15'
T=et_edge(DAY,10,12)
SEC=10_000_000
def bar(v,lo,hi,ts,duration=3):
    return CompletedPrintBar(377,377,377,v*377,hi,lo,ts-duration*SEC,ts,7)
def pseudo(v):return SimpleNamespace(total_qty=100,price_times_qty_ticks=100*v)
class NewQuestions(unittest.TestCase):
    def test_acceleration_without_current_range_expansion(self):
        b=bar(1000,990,1010,T-9*SEC,8)
        c=bar(1003,997,1007,T,3)
        self.assertTrue(t17(b,c))
        self.assertFalse(t17(b,bar(1003,980,1020,T,3)))
    def test_premarket_auction_causal_signal(self):
        a,b=pseudo(1000),pseudo(1010)
        c0=bar(1012,1005,1020,T-9*SEC)
        c1=bar(1020,1015,1025,T)
        self.assertTrue(t18(a,b,c0,c1,1))
        self.assertFalse(t18(a,b,c0,c1,-1))
    def test_inefficient_path_not_direction(self):
        times=[T-30*SEC,T-25*SEC,T-20*SEC,T-15*SEC,T]
        xs=[bar(v,v-5,v+5,t) for v,t in zip((1000,1010,1000,1010,1000),times)]
        self.assertTrue(t19(xs))
        ys=[bar(v,v-5,v+5,t) for v,t in zip((1000,1006,1012,1018,1024),times)]
        self.assertFalse(t19(ys))
    def test_signal_one_each_and_magnitude_not_trade_side(self):
        times=[T-30*SEC,T-25*SEC,T-20*SEC,T-15*SEC,T]
        bars=[bar(v,v-5,v+5,t,3) for v,t in zip((1000,1010,1000,1010,1000),times)]
        a,b=pseudo(990),pseudo(1000)
        with patch('nq_t17_t19_signal_feasibility.completed_bars_by_print_count',
                   return_value={377:bars}),patch(
                       'nq_t17_t19_signal_feasibility.preopen_pairs',
                       return_value=(a,b)):
            z,n=detect([],DAY)
        self.assertEqual(z[IDS[2]],(T,0))
        self.assertEqual(n,1)
    def test_oos_before_access(self):
        class Bomb:
            def __iter__(self):raise AssertionError('sealed touched')
        with self.assertRaises(ValueError):detect(Bomb(),'2026-08-17')
    def test_aggregate_no_alpha(self):
        from nq_t17_t19_signal_screen_aggregate import aggregate
        ms=['2025-10','2025-11','2025-12','2026-01','2026-02','2026-03','2026-04']
        ns=[13,20,22,21,20,22,22]
        es=[13,19,21,21,20,21,20]
        x={m:{'month':m,'status':'T17_T19_MECHANISM_SCREEN_ONLY_NO_RETURNS',
          'source_days':n,'eligible_days':e,'excluded_days':n-e,
          'hypotheses':{k:{'signal_days':1,'economic_trades':None,
                      'net_usd':None,'IC90':None,'q_BH':None,'validated':False} for k in IDS},
          'overlap_days':{},'oos_read':False,'new_history_acquired':False,
          'five_second_new_signals':False,'PnL_calculated':False}
          for m,n,e in zip(ms,ns,es)}
        out=aggregate(x)
        self.assertEqual(out['eligible_sessions'],135)
        self.assertIsNone(out['PF'])
if __name__=='__main__':unittest.main()
