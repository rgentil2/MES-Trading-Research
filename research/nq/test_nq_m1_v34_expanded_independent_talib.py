"""S0.29 expansion of independently implemented TA-Lib numerical oracles.

These comparisons run on MADE-UP OHLCV arrays, not private IST price data.
Matching TA-Lib for a named scalar and a limited subset of parameter points
does not prove all 132 formula conventions, broker behavior, or fitness.
No strategy AST, trades or NinjaTrader platform is executed here.
"""
import unittest
import numpy as np
import talib
from research.nq.nq_m1_v26_all_132_router import value as router
from research.nq.test_nq_m1_v26_all_132 import synthetic

def block(name,params,output=None):
    return {"name":name,"parameters":params,**({"output":output} if output else {})}

class TestS029ExpandedIndependentReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples=[synthetic(1024,seed) for seed in (41,42,43)]
        cls.points=(440,720,980)

    def check(self,one,refs,precision=.001):
        for idx in self.points:
            x=router(one,idx,refs[0])
            reference=float(refs[1][idx])
            self.assertIsNotNone(x)
            self.assertTrue(np.isfinite(reference))
            self.assertAlmostEqual(x,reference,delta=precision)

    def test_dema_tema_trima_against_independent_talib(self):
        for bars in self.samples:
            close=bars[:,3]
            for n in (5,13,30):
                for name,fun in (("DEMA",talib.DEMA),("TEMA",talib.TEMA),
                                 ("TRIMA",talib.TRIMA)):
                    with self.subTest(name=name,n=n):
                        self.check(bars,(block(name,{"period":n,"source":"close"}),
                                         fun(close,timeperiod=n)),precision=.00002)

    def test_all_basic_ma_with_non_close_sources(self):
        for bars in self.samples:
            for source,series in (("open",bars[:,0]),
                                  ("hl2",(bars[:,1]+bars[:,2])/2)):
                for n in (7,20,37):
                    for name,fun in (("SMA",talib.SMA),("EMA",talib.EMA),
                                     ("WMA",talib.WMA),("DEMA",talib.DEMA),
                                     ("TEMA",talib.TEMA),("TRIMA",talib.TRIMA)):
                        with self.subTest(name=name,source=source,n=n):
                            self.check(bars,(block(name,{"period":n,"source":source}),
                                             fun(series,timeperiod=n)),.00002)

    def test_apo_two_ema_difference_and_trix_against_talib(self):
        for bars in self.samples:
            c=bars[:,3]
            for f,s in ((5,21),(12,26),(18,39)):
                with self.subTest(f=f,s=s):
                    self.check(bars,(block("APO",{"fast_period":f,"slow_period":s}),
                                     talib.APO(c,fastperiod=f,slowperiod=s,matype=1)),.00005)
            for n in (5,12,26):
                with self.subTest(n=n):
                    self.check(bars,(block("TRIX",{"period":n}),
                                     talib.TRIX(c,timeperiod=n)),.00005)

    def test_atr_natr_on_true_ohlc_wilder_talib(self):
        for bars in self.samples:
            h,l,c=bars[:,1],bars[:,2],bars[:,3]
            for n in (5,14,31):
                atr=talib.ATR(h,l,c,timeperiod=n)
                natr=talib.NATR(h,l,c,timeperiod=n)
                with self.subTest(n=n):
                    self.check(bars,(block("ATR",{"period":n}),atr),.00002)
                    self.check(bars,(block("NATR",{"period":n,"multiplier":1.0}),natr),.00002)

    def test_adxr_against_talib_independent_adx_lag_definition(self):
        for bars in self.samples:
            h,l,c=bars[:,1],bars[:,2],bars[:,3]
            for n in (5,14,20):
                ref=talib.ADXR(h,l,c,timeperiod=n)
                for i in self.points:
                    with self.subTest(n=n,index=i):
                        v=router(bars,i,block("ADXR",{"period":n,"threshold":10}))
                        self.assertIsNotNone(v)
                        self.assertAlmostEqual(v+10,float(ref[i]),delta=.12)

    def test_rsi_no_lookahead_and_unavailable_composite_warmup(self):
        bars=self.samples[0]
        n=240
        for name,needed in (("DEMA",2*n-1),("TEMA",3*n-2)):
            params={"period":n,"source":"close"}
            self.assertIsNone(router(bars,needed-2,block(name,params)))
            # This index is evaluated on an artificial series of 1024 bars,
            # checking start-of-signal warmup not peeking at future samples.
            self.assertIsNotNone(router(bars,needed-1,block(name,params)))
        extra=bars.copy();extra[711:,0:4]=np.nan
        for name in ("SMA","EMA","DEMA","TEMA","TRIMA"):
            params={"period":20,"source":"close"}
            self.assertEqual(router(bars,710,block(name,params)),
                             router(extra,710,block(name,params)))

if __name__=="__main__":
    unittest.main()
