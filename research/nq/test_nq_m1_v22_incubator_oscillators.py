"""Independent TA-Lib comparisons for APO and TRIX incubators, no market."""
import unittest
import numpy as np
import talib
from research.nq import nq_m1_v22_incubator_oscillators as inc
from research.nq import nq_m1_v2_m1_engine as frozen


def synthetic():
    rng=np.random.default_rng(20261028)
    close=19000+np.cumsum(rng.normal(.16,5.1,850))
    opening=close+rng.normal(0,1.,len(close))
    high=np.maximum(close,opening)+2
    low=np.minimum(close,opening)-2
    volume=rng.integers(10,2000,len(close))
    return np.column_stack((opening,high,low,close,volume)).astype(float)


class TestNQMomentumIncubator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=synthetic()

    def test_trix_talib_parity_across_periods_and_mature_indices(self):
        for n in (3,5,14,27):
            ref=talib.TRIX(self.b[:,3].copy(),timeperiod=n)
            for idx in (120,240,500,849):
                with self.subTest(n=n,idx=idx):
                    result=inc.indicator_value(self.b,idx,{"name":"TRIX","parameters":{"period":n}})
                    self.assertAlmostEqual(result,float(ref[idx]),delta=1e-7)

    def test_apo_talib_ema_parity(self):
        for fast,slow in ((2,6),(5,26),(12,30),(40,100)):
            ref=talib.APO(self.b[:,3].copy(),fastperiod=fast,slowperiod=slow,matype=1)
            for idx in (145,250,510,849):
                with self.subTest(fast=fast,slow=slow,idx=idx):
                    result=inc.indicator_value(self.b,idx,{"name":"APO",
                        "parameters":{"fast_period":fast,"slow_period":slow}})
                    self.assertAlmostEqual(result,float(ref[idx]),delta=1e-5)

    def test_first_valid_output_and_warmup_none(self):
        for name,params in (
            ("TRIX",{"period":12}),
            ("APO",{"fast_period":5,"slow_period":26})):
            if name=="TRIX":
                ref=talib.TRIX(self.b[:,3].copy(),timeperiod=12)
            else:
                ref=talib.APO(self.b[:,3].copy(),fastperiod=5,slowperiod=26,matype=1)
            first=int(np.flatnonzero(np.isfinite(ref))[0])
            block={"name":name,"parameters":params}
            with self.subTest(name=name):
                self.assertIsNone(inc.indicator_value(self.b,first-1,block))
                self.assertAlmostEqual(inc.indicator_value(self.b,first,block),float(ref[first]),delta=1e-5)

    def test_future_mutation_does_not_affect_completed_bar(self):
        for name,params in (
            ("TRIX",{"period":14}),
            ("APO",{"fast_period":5,"slow_period":26})):
            block={"name":name,"parameters":params}
            before=inc.indicator_value(self.b,170,block)
            changed=self.b.copy()
            changed[171:,3]=np.nan
            self.assertEqual(before,inc.indicator_value(changed,170,block))

    def test_inactive_parameter_unknown_or_bad_period_fail_closed(self):
        for name,params in (
            ("TRIX",{"period":14,"unused":90}),
            ("APO",{"fast_period":14,"slow_period":10}),
            ("APO",{"fast_period":5,"slow_period":26,"signal_period":9})):
            with self.subTest(name=name,params=params):
                with self.assertRaises(ValueError):
                    inc.indicator_value(self.b,170,{"name":name,"parameters":params})

    def test_frozen_engine_still_38_and_incubator_disjoint(self):
        self.assertEqual(len(frozen.SUPPORTED_INDICATORS),38)
        self.assertTrue(inc.PROTOTYPES.isdisjoint(frozen.SUPPORTED_INDICATORS))
        self.assertEqual(inc.STATUS,"ISOLATED_MATH_PARITY_ONLY_NOT_ACTIVE_IN_V21")

if __name__=="__main__":
    unittest.main()
