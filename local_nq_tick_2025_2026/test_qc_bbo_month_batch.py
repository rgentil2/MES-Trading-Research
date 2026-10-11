import unittest
from qc_bbo_month_batch import DAYS_BY_MONTH, summarize_day, summarize_month

class TestPredeclaredMonthlySample(unittest.TestCase):
    def test_thirty_six_days_and_scope(self):
        self.assertEqual(len(DAYS_BY_MONTH),9)
        self.assertEqual(sum(len(v) for v in DAYS_BY_MONTH.values()),36)
        self.assertEqual(list(DAYS_BY_MONTH)[0],'2025-10')
        self.assertEqual(list(DAYS_BY_MONTH)[-1],'2026-06')

    def test_mock_aggregate(self):
        s={'trades':10,'valid_prior':10,'outside':3,'same_time_pct':90.,
           'age_thresholds_ms':{'50':{'n':8,'outside':2},
                                '250':{'n':9,'outside':3},
                                '1000':{'n':10,'outside':3}},
           'same_timestamp_alternative_NONCAUSAL':{'prior_outside':3,'prior_outside_alt_inside':2}}
        raw={'date_et':'2025-10-15','status':'DIAGNOSTIC_ONLY',
             'holdout_2026_jul_sep_opened':False,
             'source_qc_counts':{'Last_rows':30,'Bid_rows':100,'Ask_rows':100},
             'segments':{k:s for k in ('open_0930_1000','mid_1000_1030','late_1030_1130')}}
        r=summarize_day(raw)
        self.assertEqual(r['last_events'],30)
        self.assertEqual(r['outside_pct'],30.)
        self.assertEqual(r['same_time_NONCAUSAL_reclassification_pct'],66.667)

    def test_reject_sealed_date(self):
        with self.assertRaises(ValueError):
            summarize_day({'date_et':'2026-07-01','status':'DIAGNOSTIC_ONLY'})

    def test_reject_incomplete_month(self):
        with self.assertRaises(ValueError):
            summarize_month('2026-01',[{'day_et':'2026-01-06','outside_pct':29}])

    def test_reject_sealed_month(self):
        with self.assertRaises(ValueError):
            summarize_month('2026-07',[])

if __name__=='__main__':unittest.main()
