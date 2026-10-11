"""T08 synthetic guardrails: reuse T04 fills, no holdouts, stitched equity."""
import unittest
from datetime import date
from qc_tick_day import utc_bounds
from nq_tick_short_horizon import OR_START,OR_END,N_BARS,STEP_100NS
from nq_t04_execution import simulate_portfolio
from nq_t08_risk_audit import (Envelope,trace_portfolio,
    mark_trade_envelope,run_month,summarize_month,FAMILIES,SCENARIOS)
from nq_t08_risk_aggregate import aggregate,EXPECTED_BASELINE,EXPECTED_STRESS
from nq_tick_short_horizon_month import MONTHS

DAY='2025-10-15'

def opening():
    bars=[None]*N_BARS
    for i in range(OR_START,OR_END):
        bars[i]=[400,420,380,400,5,10]
    return bars

class TestT08(unittest.TestCase):
    def test_envelope_has_same_timestamp_adverse_order_and_stitched_closed(self):
        e=Envelope()
        e.mark(0.,10.)
        e.mark(-20.,5.)
        self.assertEqual(e.max_dd,30.)
        e.close(15.)
        e.mark(0.,25.)
        self.assertEqual(e.max_dd,30.)
        self.assertEqual(e.closed_dd,0.)

    def test_one_stop_trade_parity_with_frozen_t04(self):
        start,_=utc_bounds(date.fromisoformat(DAY))
        i=OR_END+60
        signal_time=start+(i+1)*STEP_100NS
        events=[(signal_time+100000,400,1),
                (signal_time+200000,399,1),
                (signal_time+300000,380,1)]
        bars=opening()
        for sc in SCENARIOS:
            reference=simulate_portfolio(DAY,events,bars,[(i,1)],sc)
            env=Envelope()
            actual=trace_portfolio(DAY,events,bars,[(i,1)],sc,env)
            for k,v in actual.items():
                self.assertEqual(reference[k],v,k)
            self.assertEqual(env.equity,reference['net_usd'])
            self.assertGreaterEqual(env.max_dd,-reference['net_usd'])
            self.assertEqual(actual['trades'],1)

    def test_holdout_blocked_before_iteration(self):
        class Poison:
            def __iter__(self):raise AssertionError('Illegal iterator touch')
        with self.assertRaises(ValueError):
            trace_portfolio('2026-05-01',Poison(),None,None,'baseline',Envelope())
        with self.assertRaises(ValueError):
            run_month(None,'2026-09')
        with self.assertRaises(ValueError):
            summarize_month('2026-07',[],{})

    def test_cannot_omit_month_or_include_holdout(self):
        with self.assertRaises(ValueError):
            aggregate({})
        with self.assertRaises(ValueError):
            aggregate({m:None for m in MONTHS+('2026-07',)})

    def test_aggregation_retains_preexisting_totals_and_seven_months(self):
        months={}
        for i,month in enumerate(MONTHS):
            fams={}
            for fam in FAMILIES:
                fams[fam]={}
                for sc in SCENARIOS:
                    n,net=(EXPECTED_BASELINE if sc=='baseline'
                       else EXPECTED_STRESS)[fam]
                    trades=n if i==0 else 0
                    value=net if i==0 else 0.
                    fams[fam][sc]={
                        'trades':trades,'net_usd':value,
                        'gross_positive_net_usd':value,
                        'gross_negative_net_usd':0.,
                        'ambiguous_or_unknown':0,'aborted_days':0,
                        'last_envelope_segment':{
                            'equity':value,'high':value,'low':0.,
                            'max_dd':0.,'closed_high':value,
                            'closed_low':0.,'closed_dd':0.}}
            months[month]={
                'month':month,'status':'T08_DEV_RISK_DIAGNOSTIC_NOT_BROKER_OR_OOS',
                'holdouts_opened':False,'funded_rules_verified':False,
                'costs_verified':False,'eligible_days':1,'source_days':1,
                'families':fams}
        result=aggregate(months)
        self.assertEqual(result['eligible_days'],7)
        self.assertEqual(result['candidates']['T02_PARENT']['baseline']['trades'],190)
        self.assertFalse(result['candidates']['T05_377']['baseline']
                         ['risk_gate_preliminary_pass'])

if __name__=='__main__':unittest.main()
