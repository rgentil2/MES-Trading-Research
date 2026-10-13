"""Synthetic shadow D2 tests; never opens market or OOS data."""
import unittest,copy
from datetime import date,timedelta
from nq_t133_t168_shadow_d2_portfolios import (
    load_policy,priority,decide,portfolio_stats,dd_metrics,
    validate_d1_parity,IDS,READY)

class ShadowD2PortfolioExercise(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg=load_policy()
    def test_exact_six_preset_and_36_total(self):
        self.assertEqual(len(self.reg['cases']),6)
        self.assertEqual(len(self.reg['all36']),36)
        self.assertEqual(len(self.reg['d0_diverse27']),27)
        self.assertEqual(self.reg['account_start_usd'],50000)
        self.assertFalse(self.reg['broker_fills_verified'])
        self.assertTrue(self.reg['one_daily_entry_max'])
    def test_ordered_priority_chooses_first_case_at_anchor(self):
        x=self.reg['cases'][0]
        d={'T133':{'group':'CASE','status':'REJECTED_RISK_AT_PROXY_ENTRY'},
           'T145':{'group':'CASE','status':'MODELLED_EXECUTION_UNVERIFIED'}}
        self.assertEqual(decide(x,'2025-10-10',d),'T133')
    def test_rotate_pure_calendar_no_future(self):
        x=self.reg['cases'][1]
        a=priority(x,'2025-10-10');b=priority(x,'2025-10-10')
        self.assertEqual(a,b)
        self.assertEqual(set(a),set(IDS))
        self.assertEqual(len(a),36)
    def test_no_fallback_even_if_second_case_is_winner(self):
        entries=[]
        base=date(2025,10,1)
        for i in range(READY):
            d=(base+timedelta(days=i)).isoformat()
            proxy={k:{'group':'CONTROL','status':'NO_CAUSAL_TRIGGER'} for k in IDS}
            proxy['T133']={'group':'CASE','status':'REJECTED_RISK_AT_PROXY_ENTRY'}
            proxy['T145']={'group':'CASE','status':'MODELLED_EXECUTION_UNVERIFIED',
              'net_usd':100.,'stress_1_5x_usd':90.,'stress_plus_10_rt_usd':90.,
              'instrument':'MNQ','risk_nominal_usd':60.,'direction':1}
            entries.append({'date':d,'proxies':proxy})
        z=portfolio_stats(self.reg['cases'][0],entries,self.reg)
        self.assertEqual(z['selected_CASE_at_anchor_days'],135)
        self.assertEqual(z['proxy_trades_in_one_account'],0)
        self.assertEqual(z['model_net_usd'],0)
        self.assertEqual(z['days_with_anchor_selection_but_no_modelled_trade'],135)
    def test_stress_closed_equity_breaches_detected(self):
        z=dd_metrics([1000,-2501,1000],50000,500,2000,1500,3000)
        self.assertTrue(z['closed_equity_dd_gt_2000_ever'])
        self.assertTrue(z['dd_gt_1500_ever'])
        self.assertEqual(z['model_daily_loss_below_minus500_count'],1)
        self.assertEqual(z['worst_model_daily_usd'],-2501)
    def test_no_false_profit_goal_for_negative_sequence(self):
        z=dd_metrics([-100,-100,-100],50000,500,2000,1500,3000)
        self.assertFalse(z['reference_goal_3000_reached_ever'])
    def test_reject_invalid_original_parity(self):
        with self.assertRaises(ValueError):
            validate_d1_parity([],{})
    def test_lookahead_flag_never_treated_as_promotion(self):
        self.assertEqual(self.reg['governance'],'D1_NO_APPROVED_CANDIDATES_FORMAL_D2_REMAINS_EMPTY')
        for x in self.reg['cases'][3:]:
            self.assertIn('RETROSPECTIVE_IN_SAMPLE',x['selection_source'])
if __name__=='__main__':unittest.main()
