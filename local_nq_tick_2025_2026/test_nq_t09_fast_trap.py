"""Synthetic tests: NQ T09 timing, prereg controls, shared router and holds."""
import unittest
from datetime import date
from qc_tick_day import utc_bounds
from nq_tick_short_horizon import OR_START,OR_END,N_BARS,STEP_100NS
from nq_t04_execution import simulate_portfolio,SCENARIOS
from nq_t09_fast_trap import (fast_trap_signals,combine_signals,
                             replay_router_attribution,analyze_events)
from nq_t09_month import summarize_month
DAY='2025-10-15'

def bars_fixture():
    bars=[None]*N_BARS
    for i in range(OR_START,OR_END):
        bars[i]=[400,420,380,400,4,10]
    return bars

class T09Tests(unittest.TestCase):
    def test_waits_for_complete_later_bar_inside_opening(self):
        b=bars_fixture();i=OR_END+60
        b[i+1]=[424,426,422,423,3,3]
        b[i+2]=[422,423,417,418,4,4]
        self.assertEqual(fast_trap_signals(b,[(i,1)]),[(i+2,-1)])
        b[i+2]=None
        self.assertEqual(fast_trap_signals(b,[(i,1)]),[])
    def test_cannot_use_13th_bar_after_sixty_seconds(self):
        b=bars_fixture();i=OR_END+60
        for j in range(i+1,i+14):b[j]=[424,425,422,423,3,3]
        b[i+13]=[419,419,417,418,4,4]
        self.assertEqual(fast_trap_signals(b,[(i,1)]),[])
    def test_downside_breakout_reentry(self):
        b=bars_fixture();i=OR_END+60
        b[i+1]=[379,379,377,378,3,3]
        b[i+2]=[382,383,379,382,2,3]
        self.assertEqual(fast_trap_signals(b,[(i,-1)]),[(i+2,1)])
    def test_same_timestamp_t05_priority_and_owner(self):
        x,n=combine_signals([(1200,-1),(1300,1)],[(1200,1),(1400,-1)])
        self.assertEqual(n,1)
        self.assertEqual(x,[(1200,-1,'T05_377'),(1300,1,'T05_377'),
                            (1400,-1,'T09_FAST_TRAP_60S')])
    def test_replay_exact_simulator_parity(self):
        d=DAY;start,_=utc_bounds(date.fromisoformat(d))
        i=OR_END+60
        t=start+(i+1)*STEP_100NS
        data=[(t+100000,400,1),(t+200000,399,1),(t+300000,378,1)]
        b=bars_fixture()
        for sc in SCENARIOS:
            reference=simulate_portfolio(d,data,b,[(i,1)],sc)
            actual=replay_router_attribution(d,data,b,[(i,1,'T09_FAST_TRAP_60S')],sc)
            for key in ('trades','net_usd','wins','losses','total_positive_usd',
                        'total_negative_usd','skipped_overlap',
                        'skipped_max_two_or_daily_stop',
                        'unknown_entry_or_exit','day_aborted_due_to_ambiguity'):
                self.assertEqual(reference[key],actual[key],key)
            self.assertEqual(actual['contributions']['T09_FAST_TRAP_60S']['trades'],1)
            self.assertEqual(actual['contributions']['T05_377']['trades'],0)
    def test_cannot_open_2026_holdout(self):
        class NeverRead:
            def __iter__(self):raise AssertionError('Read holdout')
        with self.assertRaises(ValueError):
            analyze_events(NeverRead(),'2026-07-01')
        with self.assertRaises(ValueError):
            summarize_month('2026-09',[],[])
    def test_bad_signal_fails_closed(self):
        with self.assertRaises(ValueError):
            combine_signals([(1200,0)],[])
        with self.assertRaises(ValueError):
            fast_trap_signals(bars_fixture(),[(1200,0)])

if __name__=='__main__':unittest.main()
