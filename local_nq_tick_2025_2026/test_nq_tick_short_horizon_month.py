import unittest
from nq_tick_short_horizon import FAMILIES,HORIZONS
from nq_tick_short_horizon_month import MONTHS,summarize_month,month_days

class TestDevelopmentMonthAggregates(unittest.TestCase):
    def sample(self,day):
        f={k:{'opportunities':2,'forward_ticks':{
            str(h):{'n':2,'mean':4.,'median':4.,'positive_pct':50.}
            for h in HORIZONS}} for k in FAMILIES}
        return {'date_et':day,'status':'DIAGNOSTIC_ONLY','families':f,
                'holdout_2026_may_sep_opened':False}

    def test_frozen_seven_development_months(self):
        self.assertEqual(len(MONTHS),7)
        self.assertEqual(MONTHS[0],'2025-10')
        self.assertEqual(MONTHS[-1],'2026-04')

    def test_no_validation_or_sealed(self):
        for month in ('2026-05','2026-06','2026-07','2026-10'):
            with self.assertRaises(ValueError):
                summarize_month(month,[self.sample('2026-05-01')])
            with self.assertRaises(ValueError):
                month_days(None,month)  # date guard before path use

    def test_month_mismatch_fail_closed(self):
        with self.assertRaises(ValueError):
            summarize_month('2025-10',[self.sample('2026-04-15')])

    def test_aggregate_without_invented_fills(self):
        x=summarize_month('2025-10',[self.sample('2025-10-15'),self.sample('2025-10-21')])
        self.assertEqual(x['families']['T03_router']['total_opportunities'],4)
        self.assertEqual(x['families']['T03_router']['forward_ticks']['5']['opportunity_weighted_mean_gross_ticks'],4.0)
        self.assertFalse(x['trades_executed_or_costs_applied'])

    def test_prohibit_holdout_access_flag(self):
        d=self.sample('2025-10-15')
        d['holdout_2026_may_sep_opened']=True
        with self.assertRaises(ValueError):
            summarize_month('2025-10',[d])

    def test_no_data_rejected(self):
        with self.assertRaises(ValueError):
            summarize_month('2025-10',[])

if __name__=='__main__':unittest.main()
