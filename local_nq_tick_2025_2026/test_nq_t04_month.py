import unittest
from nq_t04_month import summarize_month
from nq_t04_execution import PORTFOLIOS,SCENARIOS

class T04MonthAggregationTests(unittest.TestCase):
    def sample(self):
        row={'trades':2,'opportunities':3,'wins':1,'losses':1,'net_usd':100.,
             'total_positive_usd':220.,'total_negative_usd':120.,
             'floating_last_mark_min_vs_day_start_usd':-160.,
             'worst_trade_usd':-120.,
             'unknown_entry_or_exit':0,'day_aborted_due_to_ambiguity':False,
             'skipped_max_two_or_daily_stop':1,'skipped_overlap':0}
        return {'date_et':'2025-10-15','status':'EXPLORATORY_SIM_ONLY',
                'holdout_2026_may_sep_opened':False,
                'results':{p:{s:row for s in SCENARIOS} for p in PORTFOLIOS}}

    def test_month_risk_statistics(self):
        r=summarize_month('2025-10',[self.sample()])
        x=r['portfolio_scenarios']['T02_combined']['baseline']
        self.assertEqual((x['trades'],x['net_usd'],x['profit_factor_net']),(2,100.0,1.833))
        self.assertFalse(r['actual_fills_or_payouts'])
        self.assertFalse(r['funded_fee_schedule_verified'])

    def test_monthly_holdout_gate(self):
        for m in ('2026-05','2026-06','2026-07','2026-10'):
            with self.assertRaises(ValueError):summarize_month(m,[self.sample()])

    def test_empty_month_rejected(self):
        with self.assertRaises(ValueError):summarize_month('2025-10',[])

    def test_holdout_leak_flag_rejected(self):
        x=self.sample();x['holdout_2026_may_sep_opened']=True
        with self.assertRaises(ValueError):summarize_month('2025-10',[x])

if __name__=='__main__':unittest.main()
