import unittest
from datetime import date
from qc_tick_day import utc_bounds
from nq_tick_short_horizon import OR_START,OR_END,N_BARS,STEP_100NS
from nq_t04_execution import simulate_portfolio,SCENARIOS
from nq_t10_t05_bbo_endpoints import (quote_snapshots,classify_quote,
    replay_frozen,analyze_pairs,run_month,aggregate_month)
from sim_nq_last_execution_skeleton import simulate_single_trade,FillPolicy,Signal

DAY='2025-10-15'

def opening():
    bars=[None]*N_BARS
    for i in range(OR_START,OR_END):
        bars[i]=[400,420,380,400,2,2]
    return bars

class TestT10(unittest.TestCase):
    def test_same_timestamp_quote_is_never_available(self):
        class NoRead:
            def __iter__(self):raise AssertionError('Holdout iterator read')
        with self.assertRaises(ValueError):
            quote_snapshots('2026-07-01',[NoRead()], [1])
        snapshots=quote_snapshots(DAY,[
            iter([(10,'Bid',100.0),(20,'Bid',101.0)]),
            iter([(10,'Ask',100.25),(20,'Ask',101.25)])
        ],[10,11,20,21])
        self.assertEqual(snapshots[10],(None,None))
        self.assertEqual(snapshots[11],((10,100.0),(10,100.25)))
        self.assertEqual(snapshots[20],((10,100.0),(10,100.25)))
        self.assertEqual(snapshots[21],((20,101.0),(20,101.25)))

    def test_250ms_age_and_valid_spread(self):
        at=10000000
        valid=((at-2500000,100.0),(at-2500000,100.25))
        self.assertEqual(classify_quote(valid,at),('VALID_STRICT_PRIOR_BBO',1))
        old=((at-2500001,100.0),(at-2500001,100.25))
        self.assertEqual(classify_quote(old,at)[0],'STALE_GT_250MS')
        self.assertEqual(classify_quote(((at-1,100.),(at-1,100.)),at)[0],
                         'LOCKED_OR_CROSSED')
        with self.assertRaises(AssertionError):
            classify_quote(((at,100.),(at-1,100.25)),at)

    def test_long_and_short_quote_algebra(self):
        at=10000000
        a=(at-10000,100.0);b=(at-10000,100.25)
        exit_bid=(at+1000000,104.75);exit_ask=(at+1000000,105.0)
        snapshots={at:(a,b),at+1010000:(exit_bid,exit_ask)}
        trade={'side':1,'entry_timestamp':at,'exit_timestamp':at+1010000,
          'entry_price_ticks':400,'exit_price_ticks':420,
          'estimated_net_usd':95.,'gross_usd':100.}
        c,entry,exit,delta=analyze_pairs([trade],snapshots)
        self.assertEqual(c['valid_quote_pairs'],1)
        self.assertEqual(delta,[-10.])
        self.assertEqual(entry,[1]);self.assertEqual(exit,[1])
        # short: entry at Bid and exit at Ask; if original exit is 380,
        # buyback 95.25 versus 95.00 modeled => -1 tick adverse.
        snapshots[at]=((at-1,100.0),(at-1,100.25))
        snapshots[at+1010000]=((at+1000000,95.0),(at+1000000,95.25))
        trade.update(side=-1,exit_price_ticks=380)
        c,_,_,delta=analyze_pairs([trade],snapshots)
        self.assertEqual(delta,[-5.])

    def test_frozen_last_replay_exact_parity(self):
        start,_=utc_bounds(date.fromisoformat(DAY))
        i=OR_END+60
        t=start+(i+1)*STEP_100NS
        events=[(t+100000,400,1),(t+200000,399,1),(t+300000,378,1)]
        for sc in SCENARIOS:
            expected=simulate_portfolio(DAY,events,opening(),[(i,1)],sc)
            ts,result=replay_frozen(DAY,events,opening(),[(i,1)],sc)
            for key,val in result.items():
                self.assertEqual(val,expected[key])
            self.assertEqual(len(ts),1)

    def test_sealed_month_blocked_before_filesystem(self):
        with self.assertRaises(ValueError):
            run_month(None,'2026-05')
        with self.assertRaises(ValueError):
            aggregate_month('2026-07',[])

if __name__=='__main__':unittest.main()
