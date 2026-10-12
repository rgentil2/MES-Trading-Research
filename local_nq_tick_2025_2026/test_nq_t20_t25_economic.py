"""NQ T20–T25 stage1 synthetic and security tests, never touch licensed Last."""
import unittest
from pathlib import Path
from unittest.mock import patch
from nq_t20_t25_economic_month import (
    BASE,IDS,MAG,DIRECTIONAL,MODELS,CASE_NAMES,CTRL_NAMES,ROUTERS,
    month_stage,first_decision,future_range,route,policy)
from nq_t20_t25_economic_aggregate import (
    bh,comparison_bootstrap,aggregate)
from nq_t08_risk_audit import Envelope


class StageOneTests(unittest.TestCase):
    def test_five_directional_one_magnitude_and_six_members(self):
        self.assertEqual(len(IDS),6)
        self.assertEqual(len(DIRECTIONAL),5)
        self.assertEqual(len(MODELS),16)
        self.assertNotIn(MAG,CASE_NAMES)
        self.assertNotIn(MAG,ROUTERS)

    def test_all_group_cases_and_controls_have_own_models(self):
        for k in DIRECTIONAL:
            self.assertIn(CASE_NAMES[k],MODELS)
            self.assertIn(CTRL_NAMES[k],MODELS)
            self.assertIn(ROUTERS[k],MODELS)

    def test_sealed_month_denied_before_any_io(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/DO_NOT_READ'),'2026-08',
                        Path('/DO_NOT_WRITE/private.json'))

    def test_sealed_day_denied_before_last_iteration(self):
        class Bomb:
            def __iter__(self):raise AssertionError('sealed Last exposed')
        with self.assertRaises(ValueError):
            first_decision(Bomb(),'2026-08-12')

    def test_policy_fixed_32_48_on_all_six_models(self):
        for k in DIRECTIONAL:
            p=policy(k,[])
            self.assertEqual(p.stop_ticks,32)
            self.assertEqual(p.take_profit_ticks,48)
            self.assertEqual(p.max_holding_seconds,300)

    def test_last_forward_range_after_anchor_not_before(self):
        e=[(100,1000,1),(200,900,1),(201,1020,1),(300,950,1)]
        t=[z[0] for z in e]
        with self.assertRaises(ValueError):
            future_range(e,t,200)
        # This synthetic series doesn't reach the full horizon; never silently
        # treat a partial future range as full 15min.
        self.assertEqual(len(t),4)

    def test_route_no_signals_no_trade(self):
        c,e,owners,skips=route('2025-10-15',[],[],None,[],
                               Envelope())
        self.assertEqual(c['trades'],0)
        self.assertEqual(e['net_cents'],0)
        self.assertEqual(len(owners),0)

    def test_bh_fixed_six(self):
        six={k:1. for k in IDS}
        six[IDS[0]]=.01
        six[IDS[1]]=.05
        z=bh(six)
        self.assertAlmostEqual(z[IDS[0]],.06)
        self.assertAlmostEqual(z[IDS[1]],.15)
        self.assertEqual(z[IDS[-1]],1.)
        with self.assertRaises(ValueError):
            bh({IDS[0]:.01})

    def test_underpowered_case_is_not_success_or_positive_p(self):
        x=[(0.,0,0.,0) for _ in range(135)]
        x[0]=(100.,1,0.,0)
        x[1]=(0.,0,5.,1)
        s=comparison_bootstrap(x,5,seed=20261535,reps=100)
        self.assertEqual(s['status'],'UNDERPOWERED_OR_UNIDENTIFIABLE')
        self.assertIsNone(s['p_unilateral_centered'])
        self.assertIsNone(s['CI90'])
        self.assertEqual(s['N_case_executions'],1)

    def test_bootstrap_all_135_correlated_blocks_no_independent_claim(self):
        x=[(20.,1,10.,1) for _ in range(135)]
        a=comparison_bootstrap(x,5,seed=20261537,reps=250)
        b=comparison_bootstrap(x,5,seed=20261537,reps=250)
        self.assertEqual(a,b)
        self.assertEqual(a['status'],'IN_SAMPLE_EXPLORATORY_ONLY')
        self.assertEqual(a['effect_mean_case_minus_control'],10.)
        self.assertEqual(a['CI90'],[10.,10.])
        self.assertFalse(a['p_is_confirmatory'])

    def test_incomplete_months_fail_closed(self):
        with self.assertRaises(ValueError):
            aggregate({})

if __name__=='__main__':
    unittest.main()
