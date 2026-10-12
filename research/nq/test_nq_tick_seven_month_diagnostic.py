import unittest
from nq_tick_seven_month_diagnostic import exact_sign_p,month_diagnostic,run

MONTHS=['2025-10','2025-11','2025-12','2026-01','2026-02','2026-03','2026-04']
B='T05_377'; H='H02_PRINT_VWAP_MEAN_REVERSION'
R='T05_PRIORITY_H02_SHARED_ROUTER';SC='stress_1p5_fee_2ticks_each_side'

def fixture():
    a=[137.5,760,1450,1572.5,-827.5,1372.5,637.5]
    h=[-387.5,-442.5,530,-945,-22.5,307.5,-467.5]
    r=[120,317.5,1102.5,107.5,-1072.5,995,625]
    n=[[15,8,22,19,13,21,17],
       [11,11,16,14,9,5,9],
       [20,19,31,27,21,24,24]]
    mods={}
    for model,vals,nv in zip([B,H,R],[a,h,r],n):
        mods[model]={SC:{'trades':sum(nv),'net_usd':sum(vals),
                   'monthly':[{'month':MONTHS[i],'trades':nv[i],
                               'net_usd':vals[i]} for i in range(7)]}}
    return {'status':'B05H02_FINISHED_DEV_ONLY_NOT_OOS',
      'decision':'B05H02_REJECT_DO_NOT_PROMOTE',
      'source_months':MONTHS,'source_days':140,'eligible_days':135,
      'holdouts_opened':False,'new_history_acquired':False,
      'H02_uses_5s_signals':False,'funded_strategy_approved':False,
      'broker_fills_verified':False,
      'diagnostics':{'T05_retained_router':106,'H02_executed_router':60,
         'H02_stress_net_router':-2530,
         'router_minus_T05_extra10_usd':-3417.5},
      'models':mods}

class TestSevenMonth(unittest.TestCase):
    def test_sign_p_exact(self):
        self.assertEqual(exact_sign_p(7,7),1/128)
        self.assertEqual(exact_sign_p(6,7),8/128)
        self.assertEqual(exact_sign_p(0,7),1)
        self.assertEqual(exact_sign_p(5,7),29/128)
    def test_ci_of_constant_seven_months(self):
        x=month_diagnostic([100]*7)
        self.assertEqual(x['ci90_mean_monthly_usd'],[100,100])
        self.assertIsNone(x['q_BH'])
        self.assertIsNone(x['gate1_statistical_pass'])
    def test_frozen_real_numbers_and_paired_months(self):
        z=run(fixture())
        self.assertEqual(z['stats'][B]['n_positive_months'],6)
        self.assertEqual(z['stats'][H]['n_positive_months'],2)
        self.assertEqual(z['stats']['ROUTER_MINUS_T05_PAIRED']['n_positive_months'],0)
        self.assertEqual(z['stats']['ROUTER_MINUS_T05_PAIRED']['total_usd'],-2907.5)
        self.assertEqual(z['stats']['ROUTER_MINUS_T05_PAIRED']['leave_one_month_out_total_range_usd'],[-2895,-1442.5])
        self.assertIsNone(z['effective_sample_size'])
    def test_missing_month_rejected(self):
        a=fixture()
        a['models'][B][SC]['monthly']=a['models'][B][SC]['monthly'][:-1]
        with self.assertRaises(ValueError):run(a)
    def test_holdout_rejected(self):
        a=fixture()
        a['holdouts_opened']=True
        with self.assertRaises(ValueError):run(a)
    def test_mutated_monetary_benchmark_rejected(self):
        a=fixture()
        a['models'][R][SC]['net_usd']=2194
        with self.assertRaises(ValueError):run(a)

if __name__=='__main__':
    unittest.main()
