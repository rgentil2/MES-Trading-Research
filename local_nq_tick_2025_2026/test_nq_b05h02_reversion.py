import unittest
from unittest.mock import patch
from datetime import date
from qc_tick_day import utc_bounds
from nq_b05h_atomic_print_bars import CompletedPrintBar
from nq_b05h02_reversion_month import (
    h02_candidates,near_flat,share_signals,risk_trace,BASE,NEW,
    STRESS,run_month,owner_policy)
from nq_b05h01_trade_expansion_month import et_edge
from nq_t08_risk_audit import Envelope

DAY='2025-10-15'
SEC=10_000_000
T=et_edge(DAY,10,30)

def bar(n,vwap,lo,hi,s,e):
    return CompletedPrintBar(n,n,n,n*vwap,hi,lo,s,e,3)

def src():
    b=bar(377,982,960,1002,T-70*SEC,T-40*SEC)
    c=bar(377,987,963,999,T-30*SEC,T)
    m0=bar(4181,998,960,1010,T-45*60*SEC,T-30*60*SEC)
    m1=bar(4181,1000,970,1020,T-25*60*SEC,T-15*60*SEC)
    l0=bar(10946,1000,945,1050,T-60*60*SEC,T-40*60*SEC)
    l1=bar(10946,1001,955,1055,T-39*60*SEC,T-30*60*SEC)
    return {377:[b,c],4181:[m0,m1],10946:[l0,l1]}

class H02Tests(unittest.TestCase):
    def test_long_mean_reversion_not_H01_breakout(self):
        with patch('nq_b05h02_reversion_month.completed_bars_by_print_count',return_value=src()):
            sig,diag=h02_candidates([],DAY)
        self.assertEqual(sig,[(T,1)])
        self.assertEqual(diag['h02_opportunities'],1)
    def test_medium_context_at_decision_is_not_prior(self):
        data=src()
        m1=data[4181][1]
        data[4181][1]=bar(4181,1000,970,1020,m1.start_timestamp,T)
        with patch('nq_b05h02_reversion_month.completed_bars_by_print_count',return_value=data):
            sig,diag=h02_candidates([],DAY)
        self.assertEqual(sig,[])
        self.assertEqual(diag['ready_context_decisions'],0)
    def test_context_flatness_strict_and_integer_vwap(self):
        d=src()
        self.assertTrue(near_flat(*d[4181],24))
        self.assertTrue(near_flat(*d[10946],36))
        self.assertFalse(near_flat(*d[4181],1))
    def test_never_more_than_one_candidate_per_day(self):
        d=src()
        old=d[377][-1]
        d[377].extend([old,old])
        with patch('nq_b05h02_reversion_month.completed_bars_by_print_count',return_value=d):
            sig,_=h02_candidates([],DAY)
        self.assertEqual(sig,[(T,1)])
    def test_router_same_timestamp_T05_priority(self):
        out,ties=share_signals([(T,-1,BASE)],[(T,1),(T+SEC,1)])
        self.assertEqual(out,[(T,-1,BASE),(T+SEC,1,NEW)])
        self.assertEqual(ties,1)
    def test_h02_stop_is_32_tp48_and_only_fill_after_decision(self):
        pol=owner_policy(NEW,None,STRESS)
        self.assertEqual((pol.stop_ticks,pol.take_profit_ticks),(32,48))
        events=[(T+20000,1000,1),(T+SEC,1060,1)]
        track=Envelope();extra=Envelope()
        x,y,z=risk_trace(DAY,events,None,[(T,1,NEW)],STRESS,track,extra)
        self.assertEqual(x[NEW]['trades'],1)
        self.assertEqual(x[NEW]['net_cents']-y[NEW]['net_cents'],1000)
        self.assertAlmostEqual(track.equity,x[NEW]['net_cents']/100,places=2)
        self.assertEqual(z['no_entry'],0)
    def test_H02_ambiguous_entry_fails_closed(self):
        events=[(T+20000,1000,1),(T+20000,900,1),(T+SEC,1000,1)]
        with self.assertRaisesRegex(ValueError,'HARD_FILL_AMBIGUOUS'):
            risk_trace(DAY,events,None,[(T,1,NEW)],STRESS,Envelope())
    def test_timestamp_tie_order_invariant_new_signal(self):
        from nq_b05h02_reversion_month import h02_candidates
        from nq_b05g_same_timestamp_month import tie_variants
        from test_nq_b05h_atomic_print_bars import toy_source
        source=toy_source()
        variants,_=tie_variants(source)
        observations=[h02_candidates(x,DAY) for x in variants.values()]
        self.assertTrue(all(v==observations[0] for v in observations))
    def test_oos_guard_before_data_read(self):
        class Bomb:
            def __iter__(self):raise AssertionError('read sealed')
            def __getattr__(self,name):raise AssertionError('fs accessed')
        with self.assertRaises(ValueError):h02_candidates(Bomb(),'2026-05-01')
        with self.assertRaises(ValueError):run_month(Bomb(),'2026-07')
if __name__=='__main__':unittest.main()
