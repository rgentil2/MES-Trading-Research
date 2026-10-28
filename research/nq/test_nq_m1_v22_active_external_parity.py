"""NQ active-scalar external oracle audit. Pure synthetic data, no trading PnL.

Bollinger Bandwidth and Z-Score are compared against independently
implemented TA-Lib SMA, STDDEV and BBANDS across varied periods. True Range
is a deliberately PARTIAL reference: TA-Lib TRANGE first valid bar is index
1 while this prototype emits high-low at index 0; keep that discrepancy
visible rather than claiming complete startup/warmup parity.

Does NOT upgrade the frozen 38-block runtime or certify other indicators.
"""
import unittest
import numpy as np
import talib
from research.nq import nq_m1_v2_m1_engine as engine


def fixture():
    r=np.random.default_rng(20261028)
    n=600
    c=19500+np.cumsum(r.normal(.12,3.4,n))
    o=c+r.normal(0,.7,n)
    h=np.maximum(o,c)+r.uniform(.25,2.,n)
    l=np.minimum(o,c)-r.uniform(.25,2.,n)
    v=r.integers(5,5000,n)
    return np.column_stack((o,h,l,c,v)).astype(float)


class TestExtraActiveExternalTALibParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=fixture()

    def test_bollinger_bandwidth_external_bbands(self):
        c=np.ascontiguousarray(self.b[:,3],dtype=np.float64)
        for n,k in ((5,.5),(12,2.),(30,3.5),(80,4.)):
            u,m,l=talib.BBANDS(c,timeperiod=n,nbdevup=k,nbdevdn=k,matype=0)
            expected=(u-l)/abs(m)
            block={"name":"Bollinger Bandwidth",
                   "parameters":{"period":n,"std_multiplier":k}}
            for i in (n-1,n,170,360,599):
                with self.subTest(period=n,k=k,index=i):
                    got=engine.indicator_value(self.b,i,block)
                    self.assertAlmostEqual(got,float(expected[i]),delta=1e-8)
            self.assertIsNone(engine.indicator_value(self.b,n-2,block))

    def test_z_score_external_sma_stddev(self):
        c=np.ascontiguousarray(self.b[:,3],dtype=np.float64)
        for n in (8,14,55,200):
            center=talib.SMA(c,timeperiod=n)
            std=talib.STDDEV(c,timeperiod=n,nbdev=1.)
            block={"name":"Z-Score","parameters":{"period":n}}
            for i in (n-1,n,230,450,599):
                with self.subTest(period=n,index=i):
                    want=(c[i]-center[i])/std[i]
                    self.assertAlmostEqual(engine.indicator_value(self.b,i,block),
                                           float(want),delta=1e-6)
            self.assertIsNone(engine.indicator_value(self.b,n-2,block))

    def test_first_valid_and_future_causality_for_both(self):
        for name,p in (("Z-Score",{"period":25}),
                       ("Bollinger Bandwidth",{"period":25,"std_multiplier":2.})):
            x=engine.indicator_value(self.b,130,{"name":name,"parameters":p})
            mutated=self.b.copy()
            mutated[131:,:]=np.nan
            self.assertEqual(x,engine.indicator_value(mutated,130,
                             {"name":name,"parameters":p}))

    def test_true_range_matches_talib_only_after_startup(self):
        h,l,c=(np.ascontiguousarray(self.b[:,i]) for i in (1,2,3))
        oracle=talib.TRANGE(h,l,c)
        block={"name":"True Range","parameters":{}}
        self.assertTrue(np.isnan(oracle[0]))
        self.assertEqual(engine.indicator_value(self.b,0,block),float(h[0]-l[0]))
        for i in (1,2,20,300,599):
            self.assertAlmostEqual(engine.indicator_value(self.b,i,block),
                                   float(oracle[i]),delta=1e-8)

    def test_unregistered_fake_indicator_not_counted_as_certified(self):
        self.assertEqual(len(engine.SUPPORTED_INDICATORS),38)
        self.assertNotIn("APO",engine.SUPPORTED_INDICATORS)
        self.assertNotIn("TRIX",engine.SUPPORTED_INDICATORS)


if __name__=="__main__":
    unittest.main()
