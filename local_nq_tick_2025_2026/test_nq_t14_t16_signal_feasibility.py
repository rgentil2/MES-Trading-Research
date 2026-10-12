import unittest
from unittest.mock import patch
from nq_b05h_atomic_print_bars import CompletedPrintBar
from nq_b05h01_trade_expansion_month import et_edge
from nq_t14_t16_signal_feasibility import t14,t15,t16,detect,IDS

DAY='2025-10-15'
T=et_edge(DAY,10,10)
SECOND=10_000_000
def make(px,low,high,ts,qty=377):
    if not (low<=px<=high):raise ValueError('inconsistent test bar')
    return CompletedPrintBar(377,377,qty,px*qty,high,low,ts-2*SECOND,ts,7)

class ScreenTests(unittest.TestCase):
    def test_persistent_drift_not_expansion(self):
        a=make(1000,994,1006,T-12*SECOND)
        b=make(1003,997,1009,T-8*SECOND)
        c=make(1006,1001,1011,T)
        self.assertTrue(t14(a,b,c,1))
        self.assertFalse(t14(a,b,c,-1))
        self.assertFalse(t14(a,b,make(1006,980,1035,T),1))
    def test_psychological_level_is_100_price_ticks(self):
        b=make(994,988,999,T-8*SECOND)
        c=make(1006,1000,1012,T)
        self.assertTrue(t15(b,c,1))
        self.assertFalse(t15(b,c,-1))
        self.assertFalse(t15(b,make(1006,995,1012,T),1))
        bz=make(1006,1001,1012,T-8*SECOND)
        cz=make(994,988,1000,T)
        self.assertTrue(t15(bz,cz,-1))
    def test_relative_qty_per_print_and_small_range(self):
        a=make(1000,990,1010,T-12*SECOND)
        b=make(1005,995,1015,T-8*SECOND)
        c=make(1006,1004,1009,T,qty=754)
        self.assertTrue(t16(a,b,c,-1))
        self.assertFalse(t16(a,b,c,1))
        self.assertFalse(t16(a,b,make(1006,1004,1009,T,qty=377),-1))
    def test_one_signal_per_question_and_no_lookahead(self):
        a=make(1000,994,1006,T-12*SECOND)
        b=make(1003,997,1009,T-8*SECOND)
        c=make(1006,1001,1011,T)
        with patch('nq_t14_t16_signal_feasibility.completed_bars_by_print_count',
                   return_value={377:[a,b,c]}):
            sig,_=detect([],DAY)
        self.assertEqual(sig[IDS[0]],(T,1))
        self.assertEqual(len([k for k in sig if k==IDS[0]]),1)
    def test_guard_reject_sealed_before_iterable_read(self):
        class Bomb:
            def __iter__(self):raise AssertionError('OOS iterable touched')
        with self.assertRaises(ValueError):
            detect(Bomb(),'2026-07-15')
    def test_no_false_q_or_p_result(self):
        import nq_t14_t16_signal_screen_aggregate as agg
        x={m:{'month':m,'status':'T14_T16_FROZEN_SIGNAL_SCREEN_ONLY_NO_RETURNS',
          'source_days':n,'eligible_days':e,'excluded_days':n-e,
          'hypotheses':{k:{'candidate_signal_days':1,'candidate_signals':1,
                'executed_trades':None,'net_pnl':None,'IC90':None,
                'q_BH':None,'economically_validated':False} for k in IDS},
          'pairwise_candidate_days':{},
          'holdouts_opened':False,'new_data_acquired':False,
          'new_5second_signals':False,'returns_or_fills_computed':False,
          'tick_or_trade_rows_exported':False}
           for m,n,e in zip(['2025-10','2025-11','2025-12','2026-01',
                             '2026-02','2026-03','2026-04'],
                            [13,20,23,22,20,21,21],
                            [13,19,22,21,19,20,21])}
        z=agg.reconcile(x)
        self.assertEqual(z['N_eligible_sessions'],135)
        self.assertIsNone(z['q_BH_family'])
        self.assertIsNone(z['economic_PnL'])
if __name__=='__main__':unittest.main()
