"""Synthetic only: never read licensed historical Last or sealed months."""
import unittest
from unittest.mock import patch
from nq_b05h_atomic_print_bars import CompletedPrintBar
from nq_b05h01_trade_expansion_month import et_edge
from nq_t20_t25_fixed_anchor_screen import (
    IDS,CASE,CONTROL,OTHER,MISSING, classify, detect, v)

DAY='2025-10-15'
SEC=10_000_000
T=et_edge(DAY,10,0)+2*SEC


def bar(vwap,lo=None,hi=None,t=T,qty=377,prints=377,dur=3):
    lo=vwap-10 if lo is None else lo
    hi=vwap+10 if hi is None else hi
    return CompletedPrintBar(377,prints,qty,vwap*qty,hi,lo,
                             t-dur*SEC,t,1)


class Cases(unittest.TestCase):
    def test_t20_case_and_center_control(self):
        a,b,c,d=(bar(1000),bar(1000),bar(1000),bar(1000))
        x=classify(a,b,c,d,bar(1018,1000,1020))
        self.assertEqual(x[IDS[0]],(CASE,+1))
        y=classify(a,b,c,d,bar(1010,1000,1020))
        self.assertEqual(y[IDS[0]][0],CONTROL)

    def test_t21_rejection_and_acceptance(self):
        a,b,c=bar(1000),bar(1000),bar(1000)
        d=bar(1000,990,1010)
        x=classify(a,b,c,d,bar(1005,999,1020))
        self.assertEqual(x[IDS[1]],(CASE,-1))
        y=classify(a,b,c,d,bar(1020,1005,1030))
        self.assertEqual(y[IDS[1]],(CONTROL,+1))

    def test_t22_higher_qty_and_stable_controls(self):
        a,b,c,d=(bar(1000),)*4
        e=bar(1008,998,1020,qty=754)
        self.assertEqual(classify(a,b,c,d,e)[IDS[2]],(CASE,+1))
        self.assertEqual(classify(a,b,c,d,bar(1008,998,1020))[IDS[2]],
                         (CONTROL,+1))

    def test_t23_speed_drop_vs_stable(self):
        a,b,c=bar(1000),bar(1000),bar(1000)
        d=bar(1000,dur=4)
        e=bar(1000,dur=9)
        self.assertEqual(classify(a,b,c,d,e)[IDS[3]][0],CASE)
        self.assertEqual(classify(a,b,c,d,bar(1000,dur=4))[IDS[3]][0],CONTROL)

    def test_t24_alternation_vs_alignment(self):
        a=b=bar(1000)
        c=bar(1000);d=bar(1010);e=bar(1000)
        self.assertEqual(classify(a,b,c,d,e)[IDS[4]],(CASE,-1))
        self.assertEqual(classify(a,b,c,d,bar(1020))[IDS[4]],(CONTROL,+1))

    def test_t25_cross_scale_and_missing(self):
        a=b=c=d=e=bar(1000)
        sm=[bar(1000),bar(1010)]
        med=[bar(1020),bar(1010)]
        self.assertEqual(classify(a,b,c,d,e,sm,med)[IDS[5]],(CASE,-1))
        self.assertEqual(classify(a,b,c,d,e,sm,[])[IDS[5]][0],MISSING)

    def test_only_fixed_first_anchor_not_best_signal(self):
        x=[bar(1000,t=T-(10-i)*SEC) for i in range(10)]
        x[4]=bar(1000,t=T)
        x[5]=bar(1000,t=T+3*SEC)
        # Monotone timestamps for synthetic array; first eligible bar is x[4].
        prev=[bar(1000,t=T-10*SEC),bar(1010,t=T-9*SEC)]
        ctxt=[bar(1010,t=T-8*SEC),bar(1000,t=T-7*SEC)]
        with patch('nq_t20_t25_fixed_anchor_screen.completed_bars_by_print_count',
                   return_value={233:prev,377:x,4181:ctxt}):
            out,ok=detect([],DAY)
        self.assertTrue(ok)
        self.assertEqual(set(out),set(IDS))

    def test_sealed_denied_before_iteration(self):
        class Bomb:
            def __iter__(self):raise AssertionError('sealed Last touched')
        with self.assertRaises(ValueError):
            detect(Bomb(),'2026-08-17')

    def test_aggregate_all_seven_and_no_alpha(self):
        from nq_t20_t25_stage0_aggregate import aggregate,STATUS
        months=['2025-10','2025-11','2025-12','2026-01',
                '2026-02','2026-03','2026-04']
        src=[15,20,22,21,20,22,20]
        elig=[14,19,21,21,20,21,19]
        self.assertEqual(sum(src),140)
        self.assertEqual(sum(elig),135)
        months_data={}
        for m,n,e in zip(months,src,elig):
            months_data[m]={'month':m,'status':STATUS,
                'source_days':n,'eligible_days':e,'excluded_days':n-e,
                'anchor_days':e,
                'by_question':{k:{CASE:1,CONTROL:1,OTHER:e-2,MISSING:0}
                               for k in IDS},
                'side_counts_case_or_control':{k:{'1':2} for k in IDS},
                'case_case_overlap_days':{},'N_trades':None,'net_usd':None,
                'CI90':None,'p':None,'q_BH':None,'PF':None,'DD':None,
                'holdouts_opened':False,'new_history_acquired':False,
                'five_second_new_signals':False,'outcomes_computed':False,
                'individual_events_exported':False}
        out=aggregate(months_data)
        self.assertEqual(out['eligible_sessions'],135)
        self.assertIsNone(out['q_BH'])
        months_data[months[0]]['net_usd']=12
        with self.assertRaises(ValueError):aggregate(months_data)

if __name__=='__main__':
    unittest.main()
