import unittest
from nq_t05_month import summarize_month
from nq_t05_fibonacci_bars import FAMILIES
from nq_t04_execution import SCENARIOS

def fake(day='2025-10-15'):
    def stats():
        return {'opportunities':2,'trades':1,'wins':1,'losses':0,
          'net_usd':100.,'total_positive_usd':100.,'total_negative_usd':0.,
          'floating_last_mark_min_vs_day_start_usd':-40.,
          'worst_trade_usd':100.,
          'day_aborted_due_to_ambiguity':False,'unknown_entry_or_exit':0,
          'skipped_max_two_or_daily_stop':1}
    return {'date_et':day,'status':'EXPLORATORY_LAST_FILL_MODEL_NOT_LIVE',
       'holdout_2026_may_sep_opened':False,
       'families':{f:{'parent_opportunities':3,'opportunities_after_filter':2,
                     'cost_scenarios':{s:stats() for s in SCENARIOS}}
                   for f in FAMILIES}}

class T05MonthlyAgg(unittest.TestCase):
    def test_month_info(self):
        o=summarize_month('2025-10',[fake()])
        x=o['families']['T05_233_AND_377']['baseline']
        self.assertEqual((x['opportunities'],x['executed_trades'],x['total_net_usd']),(2,1,100.))
        self.assertIsNone(x['net_profit_factor'])
        self.assertFalse(o['fees_from_funding_company_verified'])
    def test_month_scope_denies_holdout(self):
        for month in ['2026-05','2026-06','2026-07']:
            with self.assertRaises(ValueError):summarize_month(month,[fake()])
    def test_invalid_month_mix(self):
        with self.assertRaises(ValueError):summarize_month('2025-10',[fake('2026-02-11')])
    def test_no_data(self):
        with self.assertRaises(ValueError):summarize_month('2025-10',[])
    def test_sealed_flag(self):
        d=fake();d['holdout_2026_may_sep_opened']=True
        with self.assertRaises(ValueError):summarize_month('2025-10',[d])

if __name__=='__main__':unittest.main()
