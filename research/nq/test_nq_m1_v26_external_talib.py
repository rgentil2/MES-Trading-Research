"""External TA-Lib reference checks for a limited V2.6 mainstream subset.

This does not certify custom Klinger, Hilbert, Ichimoku, price/volume, Ehlers,
multi-output/anchor or 132/132 equivalence to StrategyQuant. Synthetic only.
"""
import unittest
import numpy as np
import talib
from research.nq.nq_m1_v26_all_132_router import value
from research.nq.test_nq_m1_v26_all_132 import synthetic


class TestV26IndependentReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=synthetic(850,seed=9876)

    def test_adx_talib_mature(self):
        close=self.b[:,3];high=self.b[:,1];low=self.b[:,2]
        for period in (5,14,20):
            ref=talib.ADX(high,low,close,timeperiod=period)
            for idx in (170,350,550,800):
                calc=value(self.b,idx,{"name":"ADX",
                                     "parameters":{"period":period,"threshold":10}})
                with self.subTest(period=period,index=idx):
                    self.assertAlmostEqual(calc+10,float(ref[idx]),delta=.10)

    def test_macd_hist_talib_mature(self):
        for f,s,signal in ((5,20,9),(12,26,9),(7,31,11)):
            main,sgn,hist=talib.MACD(self.b[:,3],
                   fastperiod=f,slowperiod=s,signalperiod=signal)
            for idx in (200,390,800):
                with self.subTest(f=f,s=s,signal=signal,idx=idx):
                    out=value(self.b,idx,{"name":"MACD",
                         "parameters":{"fast_period":f,"slow_period":s,
                                       "signal_period":signal}})
                    self.assertAlmostEqual(out,float(hist[idx]),delta=.005)

    def test_kama_talib_with_fixed_fast_slow_convention(self):
        for n in (5,10):
            ref=talib.KAMA(self.b[:,3],timeperiod=n)
            for idx in (350,550,800):
                with self.subTest(period=n,idx=idx):
                    out=value(self.b,idx,{"name":"KAMA",
                         "parameters":{"period":n,"source":"close"}})
                    self.assertAlmostEqual(out,float(ref[idx]),delta=.5)

    def test_t3_talib_volume_factor_point_seven(self):
        for n in (5,12):
            ref=talib.T3(self.b[:,3],timeperiod=n,vfactor=.7)
            for idx in (350,550,800):
                with self.subTest(period=n,idx=idx):
                    out=value(self.b,idx,{"name":"T3",
                         "parameters":{"period":n,"source":"close"}})
                    self.assertAlmostEqual(out,float(ref[idx]),delta=.005)

    def test_stochastic_talib_d_output(self):
        for k,s,d in ((8,3,3),(14,5,3),(20,3,9)):
            slowk,slowd=talib.STOCH(
                self.b[:,1],self.b[:,2],self.b[:,3],
                fastk_period=k,slowk_period=s,slowk_matype=0,
                slowd_period=d,slowd_matype=0)
            for idx in (170,350,800):
                out=value(self.b,idx,{"name":"Stochastic",
                          "parameters":{"k_period":k,"k_smooth":s,
                                        "d_period":d}})
                with self.subTest(k=k,s=s,d=d,idx=idx):
                    self.assertAlmostEqual(out,float(slowd[idx]),delta=1e-6)

    def test_bollinger_output_lines_talib(self):
        for n,m in ((15,1.5),(20,2.),(38,3.)):
            upper,middle,lower=talib.BBANDS(self.b[:,3],
                        timeperiod=n,nbdevup=m,nbdevdn=m,matype=0)
            for idx in (160,360,800):
                p={"period":n,"std_multiplier":m}
                with self.subTest(n=n,m=m,idx=idx):
                    got=value(self.b,idx,{"name":"Bollinger Bands","parameters":p})
                    gotlo=value(self.b,idx,{"name":"Bollinger Bands",
                                             "parameters":p,"output":"lower"})
                    self.assertAlmostEqual(got,float(upper[idx]),delta=.001)
                    self.assertAlmostEqual(gotlo,float(lower[idx]),delta=.001)

if __name__=="__main__":
    unittest.main()
