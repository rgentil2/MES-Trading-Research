import unittest
from datetime import date
from unittest.mock import patch
from qc_tick_day import utc_bounds
from nq_b05h_atomic_print_bars import CompletedPrintBar
from nq_b05h01_trade_expansion_month import (
    h01_candidates,slope_at_least,et_edge,shared_router,trace,
    BASE,NEW,STRESS,run_month)
from nq_t08_risk_audit import Envelope

DAY='2025-10-15'
SECOND=10000000
T=et_edge(DAY,9,35)

def bar(n,vwap,lo,hi,start,end):
    return CompletedPrintBar(n,n,n,n*vwap,hi,lo,start,end,3)

def eligible_set():
    # A and B historical short bars, C new bar finishes 09:35,
    # med/long both strictly earlier, coherent upward VWAP.
    a=bar(233,100,94,110,T-9*60*SECOND,T-6*60*SECOND)
    b=bar(233,104,99,115,T-3*60*SECOND,T-2*60*SECOND)
    c=bar(233,110,102,126,T-40*SECOND,T)
    m0=bar(4181,100,92,110,T-30*60*SECOND,T-20*60*SECOND)
    m1=bar(4181,103,95,113,T-20*60*SECOND,T-10*60*SECOND)
    l0=bar(10946,100,90,120,T-60*60*SECOND,T-45*60*SECOND)
    l1=bar(10946,102,93,125,T-40*60*SECOND,T-15*60*SECOND)
    return {233:[a,b,c],4181:[m0,m1],10946:[l0,l1]}

class B05H01(unittest.TestCase):
    def test_frozen_233_expansion_continuation_is_causal(self):
        with patch('nq_b05h01_trade_expansion_month.completed_bars_by_print_count',return_value=eligible_set()):
            out,counts=h01_candidates([],DAY)
        self.assertEqual(out,[(T,1)])
        self.assertEqual(counts['context_ready_closures'],1)
        self.assertEqual(counts['structural_expansion_closures'],1)
    def test_no_medium_context_timestamp_equal_decision(self):
        s=eligible_set()
        old=s[4181][1]
        s[4181][1]=bar(4181,103,95,113,old.start_timestamp,T)
        with patch('nq_b05h01_trade_expansion_month.completed_bars_by_print_count',return_value=s):
            out,counts=h01_candidates([],DAY)
        self.assertEqual(out,[])
        self.assertEqual(counts['context_ready_closures'],0)
    def test_exact_rational_vwap_slope_not_last_price(self):
        s=eligible_set()
        self.assertTrue(slope_at_least(s[233][-1],s[233][-2],1,2))
        self.assertFalse(slope_at_least(s[233][-1],s[233][-2],-1,2))
        self.assertTrue(slope_at_least(s[10946][-1],s[10946][-2],1,1))
    def test_router_same_timestamp_prioritizes_frozen_t05(self):
        result,ties=shared_router([(T,1,BASE)],[(T,-1),(T+SECOND,1)])
        self.assertEqual(result,[(T,1,BASE),(T+SECOND,1,NEW)])
        self.assertEqual(ties,1)
    def test_new_signal_is_absolute_tick_timestamp_not_time_bar(self):
        # no 5s signal formation; conservative first eligible timestamp fill.
        entry=T+2*10_000
        exit_=T+SECOND
        events=[(entry,1000,1),(exit_,1050,1)]
        base=Envelope();extra=Envelope()
        z,x,sk=trace(DAY,events,None,[(T,1,NEW)],STRESS,base,extra)
        self.assertEqual(z[NEW]['trades'],1)
        self.assertEqual(x[NEW]['trades'],1)
        self.assertEqual(z[NEW]['net_cents']-x[NEW]['net_cents'],1000)
        self.assertAlmostEqual(base.equity,z[NEW]['net_cents']/100)
        self.assertEqual(sk['no_valid_entry'],0)
    def test_sealed_month_denied_before_fs(self):
        class Bomb:
            def __getattr__(self,name):raise AssertionError('Touched sealed data')
        with self.assertRaisesRegex(ValueError,'SEALED'):
            run_month(Bomb(),'2026-05')
        with self.assertRaisesRegex(ValueError,'SEALED'):
            run_month(Bomb(),'2026-09')
    def test_sealed_signal_rejected_before_events_consumed(self):
        class Bomb:
            def __iter__(self):raise AssertionError('read sealed')
        with self.assertRaises(ValueError):h01_candidates(Bomb(),'2026-07-15')

if __name__=='__main__':unittest.main()
