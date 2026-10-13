"""Synthetic D2 SHADOW audit; no licensed Last and no hidden outcomes."""
import unittest
from nq_t133_t168_d2_shadow_portfolio import (
    ROUTERS,IDS,select_causal,aggregate,bci,N_SESSIONS)
from nq_t133_t168_economic_d1_batch import gate

class ShadowD2(unittest.TestCase):
    def test_prospective_router_order_fixed_and_family_complete(self):
        self.assertEqual(len(ROUTERS),5)
        self.assertEqual(len(ROUTERS['R0_ALL36_ID']),36)
        self.assertEqual(ROUTERS['R1_POSITIVE5_ID'],
                         ('T133','T135','T137','T145','T147'))
        self.assertEqual(ROUTERS['R4_T147_ONLY'],('T147',))
        self.assertEqual(gate()['D0_diverse_count'],27)
    def sample_day(self):
        return {k:{'group':'CONTROL','status':'NO_CAUSAL_TRIGGER',
                   'net_usd':0} for k in IDS}
    def test_priority_selects_first_CAUSAL_CASE_not_best_pnl(self):
        day=self.sample_day()
        day['T133']={'group':'CASE','status':'MODELLED_EXECUTION_UNVERIFIED','net_usd':-30}
        day['T147']={'group':'CASE','status':'MODELLED_EXECUTION_UNVERIFIED','net_usd':99999}
        self.assertEqual(select_causal(day,ROUTERS['R1_POSITIVE5_ID']),('T133',2))
        self.assertEqual(select_causal(day,ROUTERS['R2_POSITIVE5_REVERSAL_FIRST']),('T147',2))
        self.assertEqual(select_causal(day,ROUTERS['R4_T147_ONLY']),('T147',1))
    def test_no_substitute_after_risk_rejection(self):
        d=self.sample_day()
        d['T133']={'group':'CASE','status':'REJECTED_RISK_AT_PROXY_ENTRY'}
        d['T145']={'group':'CASE','status':'MODELLED_EXECUTION_UNVERIFIED','net_usd':100}
        self.assertEqual(select_causal(d,ROUTERS['R1_POSITIVE5_ID']),('T133',2))
    def test_only_one_contract_in_one_day(self):
        d=self.sample_day()
        for k in IDS:d[k]={'group':'CASE','status':'MODELLED_EXECUTION_UNVERIFIED'}
        self.assertEqual(select_causal(d,ROUTERS['R0_ALL36_ID']),('T133',36))
    def test_absent_family_member_rejected(self):
        day=self.sample_day();del day['T139']
        with self.assertRaises(AssertionError):
            select_causal(day,ROUTERS['R0_ALL36_ID'])
    def test_daily_bootstrap_requires_exact_135(self):
        with self.assertRaises(AssertionError):bci([1]*20,1)
        x=bci([1]*N_SESSIONS,2)
        self.assertAlmostEqual(x[0],1)
        self.assertAlmostEqual(x[1],1)
    def test_seven_months_required_for_aggregate(self):
        with self.assertRaises(AssertionError):
            aggregate({},None,gate())
if __name__=='__main__':unittest.main()
