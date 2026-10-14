"""Synthetic-only V2 tests: no market data, no downloaded source, no holdout."""
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

BASE=Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:sys.path.insert(0,str(BASE))
from engine import indicators, _exit
from v2_engine import (LEAVES, build_registry_v2, registry_manifest,validate_ast,
    evaluate_ast, _base_leaf_masks, _trades_for_day,analyze_v2, AND, OR, leaf)


def artificial_market(seed=5):
    rng=np.random.default_rng(seed)
    movements=rng.integers(-8,9,size=390)*.25
    close=20000+np.cumsum(movements)
    op=np.r_[close[0],close[:-1]]
    hi=np.maximum(op,close)+rng.integers(0,4,size=390)*.25
    lo=np.minimum(op,close)-rng.integers(0,4,size=390)*.25
    return np.column_stack([op,hi,lo,close,rng.integers(10,100,size=390)])


class TestStrategyBuilderV2(unittest.TestCase):
    def test_v2_registry_locked_and_96_unique(self):
        a,b=build_registry_v2(),build_registry_v2()
        self.assertEqual(len(a),96)
        self.assertEqual(len({x.id for x in a}),96)
        self.assertEqual([x.digest() for x in a],[x.digest() for x in b])
        self.assertEqual(len({x.mechanism for x in a}),16)
        self.assertEqual(len({x.context for x in a}),6)
        path=BASE/'CANDIDATES_V2_FROZEN.json'
        self.assertEqual(json.loads(path.read_text()),registry_manifest(a))
        self.assertEqual(registry_manifest(a)['total_builder_v1_v2_tests'],144)

    def test_logic_and_or_direction(self):
        x=AND(leaf('ema_align'),OR(leaf('volume_active'),leaf('mfi_align')))
        mask={k:np.array([False,False]) for k in LEAVES}
        mask['ema_align']=np.array([True,True]);mask['volume_active']=np.array([True,False])
        mask['mfi_align']=np.array([False,False])
        np.testing.assert_array_equal(evaluate_ast(x,mask),np.array([True,False]))

    def test_ast_rejects_unsafe_and_excessively_complex(self):
        with self.assertRaisesRegex(ValueError,'RULE_AST'):
            validate_ast({'op':'PYTHON','code':'not_an_allowed_rule'})
        with self.assertRaisesRegex(ValueError,'RULE_AST'):
            validate_ast({'op':'LEAF','name':'unknown'})
        with self.assertRaisesRegex(ValueError,'RULE_AST'):
            validate_ast({'op':'AND','args':[leaf('ema_align')]})
        with self.assertRaisesRegex(ValueError,'RULE_AST'):
            validate_ast(AND(AND(leaf('ema_align'),leaf('ema_oppose'),leaf('macd_align')),
                             OR(leaf('vwap_align'),leaf('vwap_oppose'))))

    def test_all_context_leaves_causal_before_future(self):
        d=artificial_market()
        z=indicators(d)
        changed=d.copy();changed[201:,:4]+=2000
        w=indicators(changed)
        for side in (-1,1):
            src=_base_leaf_masks(z,side)
            dst=_base_leaf_masks(w,side)
            for name in LEAVES:
                np.testing.assert_array_equal(src[name][:200],dst[name][:200],err_msg=name)

    def test_no_2025_or_2026(self):
        d=np.stack([artificial_market()])
        for yyyy in ('2025','2026','2019'):
            with self.assertRaisesRegex(ValueError,'SEALED'):
                analyze_v2(d,[yyyy+'-01-02'],build_registry_v2(),100)

    def test_no_mutations_even_in_allowed_years(self):
        a=build_registry_v2();a[0]=replace(a[0],reward_r=9.0)
        with self.assertRaisesRegex(ValueError,'MUTATION'):
            analyze_v2(np.stack([artificial_market()]),['2022-03-04'],a,100)

    def test_proper_entry_after_signal_and_one_trade_per_day(self):
        ds=_trades_for_day(artificial_market(), '2022-06-01',build_registry_v2())
        self.assertLessEqual(len(ds),96)
        for k,v in ds.items():
            self.assertEqual(v['entry_i'],v['signal_i']+1,k)
            self.assertLessEqual(v['signal_i'],118)
            self.assertGreaterEqual(v['signal_i'],4)
            self.assertGreaterEqual(v['qty'],1)
            self.assertLessEqual(v['qty'],5)
            self.assertAlmostEqual(v['entry']/0.25,round(v['entry']/0.25))

    def test_conservative_ambiguous_bar(self):
        d=artificial_market()
        d[53,:]=[100,104,96,101,80]
        px,k,reason,_=_exit(d,53,1,100,2,2,1)
        self.assertEqual(reason,'AMBIGUOUS_STOP_FIRST')
        self.assertEqual(k,53)
        self.assertAlmostEqual(px,97.5)

    def test_synthetic_analysis_not_independent_edge(self):
        days=np.stack([artificial_market(i) for i in range(8)])
        dates=['2020-01-02','2020-01-03','2020-01-06','2021-01-04',
               '2022-01-04','2023-01-04','2024-01-04','2024-01-05']
        report,work=analyze_v2(days,dates,build_registry_v2(),replications=100)
        self.assertEqual(report['test_family'],96)
        self.assertEqual(len(report['candidate_results']),96)
        self.assertFalse(report['loaded_dates_2025'])
        self.assertFalse(report['loaded_dates_2026'])
        self.assertTrue(all(r['gate']!='VALIDATED' for r in report['candidate_results']))
        self.assertTrue(all(t['year']<2025 for w in work.values() for t in w))

if __name__=='__main__':unittest.main()

# Pure shared-account routing tests; synthetic prices, no market imports.
from v2_router import route_single_account

class TestV2SharedRouter(unittest.TestCase):
    def mk(self,name,day,start,exit_,pnl):
        return dict(candidate=name,day=day,signal_i=start-1,entry_i=start,exit_i=exit_,
                    side=1,year=int(day[:4]),net=pnl,floating_mae_proxy_usd=-20.0)

    def test_overlap_and_tie_priority_shared_account(self):
        date='2022-07-11'
        x=self.mk('A',date,40,50,100)
        y=self.mk('B',date,40,42,999)
        z=self.mk('B',date,55,60,-10)
        routed=route_single_account({'A':[x],'B':[y,z]},['A','B'])
        self.assertEqual(routed['trades'],2)
        self.assertEqual(routed['net_usd'],90)
        self.assertEqual(routed['skipped']['overlap'],1)
        self.assertEqual([r['candidate'] for r in routed['selected_trades']],['A','B'])

    def test_session_cap_enforced(self):
        date='2022-07-11'
        route=route_single_account({'A':[self.mk('A',date,40,41,10),self.mk('A',date,50,51,10),self.mk('A',date,60,61,10)]},['A'])
        self.assertEqual(route['trades'],2)
        self.assertEqual(route['skipped']['daily_entry_cap'],1)

    def test_sealed_date_blocked_router(self):
        with self.assertRaisesRegex(ValueError,'SEALED'):
            route_single_account({'A':[self.mk('A','2026-07-11',40,42,3)]},['A'])

    def test_reference_breach_stops_further_entry(self):
        first=self.mk('A','2022-01-03',40,42,-2010)
        next_day=self.mk('A','2022-01-04',40,42,100)
        route=route_single_account({'A':[first,next_day]},['A'])
        self.assertTrue(route['stopped_after_proxy_breach'])
        self.assertEqual(route['trades'],1)
        self.assertEqual(route['risk_reference_breach'],'2022-01-03')