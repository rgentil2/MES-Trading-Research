import unittest
from datetime import date
from qc_tick_day import utc_bounds
from nq_tick_short_horizon import OR_START,OR_END,N_BARS,STEP_100NS
from nq_t04_execution import stop_ticks,risk_policy,simulate_portfolio,MAX_TRADES_PER_DAY
DAY='2025-10-15'

def opening():
    bars=[None]*N_BARS
    for i in range(OR_START,OR_END):
        bars[i]=[400,420,380,400,5,10]
    return bars

class TestNQT04(unittest.TestCase):
    def test_preregistered_stop_bounds_and_fixed_tp(self):
        self.assertEqual(stop_ticks(4),16)
        self.assertEqual(stop_ticks(80),20)
        self.assertEqual(stop_ticks(500),48)
        b=risk_policy(80,'baseline')
        self.assertEqual((b.stop_ticks,b.take_profit_ticks,b.contracts,b.commission_round_trip_usd),(20,40,1,5.0))
        s=risk_policy(80,'stress_1p5_fee_2ticks_each_side')
        self.assertEqual((s.entry_slippage_ticks,s.exit_slippage_ticks,s.commission_round_trip_usd),(2,2,7.5))
    def test_invalid_cost_mode(self):
        with self.assertRaises(ValueError):risk_policy(80,'guessed_fee')
    def test_no_opportunity_no_pnl(self):
        x=simulate_portfolio(DAY,[],opening(),[],'baseline')
        self.assertEqual(x['trades'],0)
        self.assertEqual(x['net_usd'],0)
    def test_stop_after_strictly_later_entry(self):
        start,_=utc_bounds(date.fromisoformat(DAY))
        i=OR_END+60
        t=start+(i+1)*STEP_100NS
        # Future ticks 10ms & 20ms after signal. Stop worse than barrier.
        x=simulate_portfolio(DAY,[(t+100000,400,1),(t+200000,370,1)],
                     opening(),[(i,1)],'baseline')
        self.assertEqual(x['trades'],1)
        self.assertEqual(x['losses'],1)
        self.assertLess(x['net_usd'],-100)
        self.assertLess(x['floating_last_mark_min_vs_day_start_usd'],0)
    def test_sealed_before_iterator(self):
        with self.assertRaises(ValueError):
            simulate_portfolio('2026-05-01',None,None,None,'baseline')
    def test_daily_two_trade_cap(self):
        self.assertEqual(MAX_TRADES_PER_DAY,2)

if __name__=='__main__':unittest.main()
