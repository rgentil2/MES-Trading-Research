"""Independent TA-Lib math parity for THREE incubator averages, no market data."""
import unittest
import numpy as np
import talib

from research.nq import nq_m1_v22_incubator_ma as inc
from research.nq import nq_m1_v2_m1_engine as base


def synthetic():
    rng=np.random.default_rng(20261027)
    mid=20000+np.cumsum(rng.normal(.1,3,size=700))
    op=mid+rng.normal(0,1,size=700)
    h=np.maximum(mid,op)+rng.uniform(.25,2,size=700)
    l=np.minimum(mid,op)-rng.uniform(.25,2,size=700)
    v=rng.integers(100,3000,size=700)
    return np.column_stack([op,h,l,mid,v]).astype(float)


class TestNQMAIncubatorParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=synthetic()

    def test_three_formulas_two_periods_and_three_sources_against_talib(self):
        for name in sorted(inc.PROTOTYPES):
            for period in (5,14,27):
                for source in ("close","high","hlc3"):
                    values=base._causal_price_source(self.b,source)
                    ref=getattr(talib,name)(np.ascontiguousarray(values), timeperiod=period)
                    for i in (150,300,499,699):
                        with self.subTest(indicator=name,period=period,source=source,idx=i):
                            got=inc.calc(self.b,i,{"name":name,"parameters":{
                                "period":period,"source":source}})
                            self.assertIsNotNone(got)
                            self.assertAlmostEqual(got,float(ref[i]),delta=1e-5)

    def test_exact_initial_nan_or_value_bar_follows_reference(self):
        n=12
        for name in sorted(inc.PROTOTYPES):
            ref=getattr(talib,name)(np.ascontiguousarray(self.b[:,3]), timeperiod=n)
            first=int(np.where(np.isfinite(ref))[0][0])
            block={"name":name,"parameters":{"period":n,"source":"close"}}
            self.assertIsNone(inc.calc(self.b,first-1,block),name)
            self.assertAlmostEqual(inc.calc(self.b,first,block),float(ref[first]),delta=1e-5)

    def test_future_bar_edits_cannot_change_past_indicator(self):
        for name in sorted(inc.PROTOTYPES):
            cfg={"name":name,"parameters":{"period":14,"source":"close"}}
            old=inc.calc(self.b,100,cfg)
            modified=self.b.copy()
            modified[101:,:4] += 700
            self.assertEqual(old,inc.calc(modified,100,cfg))
            modified[101:,3]=np.nan
            self.assertEqual(old,inc.calc(modified,100,cfg))

    def test_no_misleading_frozen_v21_registry_integration(self):
        self.assertEqual(len(inc.PROTOTYPES),3)
        self.assertEqual(inc.STATUS,"V22_INCUBATOR_UNRELEASED_FROM_FROZEN_V21_ENGINEERING_AST")
        self.assertTrue(inc.PROTOTYPES.isdisjoint(base.SUPPORTED_INDICATORS))
        self.assertEqual(len(base.SUPPORTED_INDICATORS),38)

    def test_invalid_inputs_and_future_index_fail(self):
        cfg={"name":"DEMA","parameters":{"period":14,"source":"close"}}
        with self.assertRaises(ValueError):
            inc.calc(self.b, len(self.b),cfg)
        with self.assertRaises(ValueError):
            inc.calc(self.b,140,{"name":"DEMA","parameters":{"period":14,"source":"close","unused":1}})
        with self.assertRaises(ValueError):
            inc.calc(self.b,140,{"name":"DEMA","parameters":{"period":14,"source":"mystery"}})
        with self.assertRaises(ValueError):
            inc.calc(self.b,140,{"name":"DEMA","parameters":{"period":1,"source":"close"}})

if __name__=="__main__":
    unittest.main()
