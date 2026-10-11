import unittest
from qc_tick_day import check_day,utc_bounds
from sim_nq_last_execution_skeleton import FillPolicy,Signal,simulate_single_trade,NQ_USD_PER_TICK
T=utc_bounds(check_day("2025-10-15"))[0]+90*60*10000000
MS=10000
DAY="2025-10-15"
def policy(**kw):
    p=dict(latency_ms=100,entry_slippage_ticks=1,exit_slippage_ticks=1,
           stop_ticks=4,take_profit_ticks=6,max_holding_seconds=1800,
           commission_round_trip_usd=4.5)
    p.update(kw)
    return FillPolicy(**p)
def ev(t,px,size=1):return(t,px,size)
def sig(side=1):return Signal(DAY,T,side)

class TestHypotheticalLastExecution(unittest.TestCase):
    def test_entry_must_be_strictly_after_signal_and_latency(self):
        rows=[ev(T,999),ev(T+50*MS,998),
              ev(T+100*MS,400),ev(T+200*MS,407)]
        r=simulate_single_trade(rows,sig(),policy())
        self.assertEqual(r["entry_price_ticks"],401)
        self.assertEqual(r["exit_reason"],"TAKE_PROFIT")
        self.assertEqual(r["estimated_net_usd"],20.5)
        self.assertFalse(r["trading_outcomes_valid"])

    def test_stop_versus_target_in_same_timestamp_stop_first(self):
        rows=[ev(T+100*MS,400),ev(T+200*MS,410),ev(T+200*MS,395)]
        r=simulate_single_trade(rows,sig(),policy())
        self.assertEqual(r["exit_reason"],"STOP")
        self.assertEqual(r["exit_price_ticks"],394)
        self.assertEqual(r["gross_ticks"],-7)

    def test_gap_avoids_optimistic_stop_price(self):
        r=simulate_single_trade([ev(T+100*MS,400),ev(T+200*MS,390)],
                                sig(),policy())
        self.assertEqual(r["exit_reason"],"STOP")
        self.assertEqual(r["exit_price_ticks"],389)

    def test_short_conservative_takeprofit(self):
        r=simulate_single_trade([ev(T+100*MS,400),ev(T+200*MS,390)],
                                sig(-1),policy())
        self.assertEqual(r["entry_price_ticks"],399)
        self.assertEqual(r["exit_price_ticks"],394)
        self.assertEqual(r["gross_ticks"],5)

    def test_entry_timestamp_price_range_stop_ambiguous(self):
        r=simulate_single_trade([ev(T+100*MS,400),ev(T+100*MS,390)],
                                sig(),policy())
        self.assertEqual(r["status"],"ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS")

    def test_stop_without_future_exit_data_is_unresolved(self):
        r=simulate_single_trade([ev(T+100*MS,400)],sig(),policy())
        self.assertEqual(r["status"],"UNRESOLVED_END_OF_LAST_DATA")

    def test_session_end_blocks_entries(self):
        r=simulate_single_trade([ev(T+120*60*10000000,400)],
                                sig(),policy())
        self.assertEqual(r["status"],"NO_ENTRY_BEFORE_SESSION_CUTOFF")

    def test_timeout_exit(self):
        r=simulate_single_trade([ev(T+100*MS,400),ev(T+1801*10000000,399)],
                                sig(),policy(max_holding_seconds=1800))
        self.assertEqual(r["exit_reason"],"TIMEOUT_OR_SESSION")

    def test_out_of_order_rejected(self):
        with self.assertRaises(ValueError):
            simulate_single_trade([ev(T+200*MS,400),ev(T+100*MS,400)],sig(),policy())

    def test_sealed_signal_rejected_before_market_read(self):
        with self.assertRaises(ValueError):
            Signal("2026-07-01",T,1)

    def test_broker_commission_must_be_explicit(self):
        with self.assertRaises(TypeError):
            FillPolicy(latency_ms=100,entry_slippage_ticks=1,exit_slippage_ticks=1,
                stop_ticks=4,take_profit_ticks=6,max_holding_seconds=1800)

    def test_position_size_fails_closed(self):
        with self.assertRaises(ValueError):
            policy(contracts=2)

    def test_signal_window_rejects_preopen(self):
        with self.assertRaises(ValueError):
            Signal(DAY,T-10*60*10000000,1)

if __name__=="__main__":unittest.main()
