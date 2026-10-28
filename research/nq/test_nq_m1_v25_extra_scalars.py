"""S0.19 numerical, causal and semantic checks for isolated NQ scalars.

Tests MUST NOT replace active 38 V2.1 or certify market performance.
"""
import unittest
import numpy as np
import talib
from research.nq import nq_m1_v25_extra_scalars as new
from research.nq.nq_m1_v2_m1_engine import SUPPORTED_INDICATORS
from research.nq.nq_m1_v2_generator import read_registry


def bars():
    rng=np.random.default_rng(20261028)
    close=19000+np.cumsum(rng.normal(.25,2.9,850))
    opening=close+rng.normal(0,.7,len(close))
    high=np.maximum(opening,close)+1.
    low=np.minimum(opening,close)-1.
    v=rng.integers(50,900,len(close)).astype(float)
    return np.column_stack((opening,high,low,close,v))


PARAMETERS={
    "HMA":{"period":20,"source":"close"},
    "ALMA":{"period":30,"source":"hl2"},
    "ZLEMA":{"period":18,"source":"close"},
    "Qstick":{"period":12},
    "VWMA":{"period":18,"anchor":"session"},
    "Linear Regression Slope":{"period":30},
    "Regression R²":{"period":30},
    "Rolling Quantile":{"period":26},
    "Entropy":{"period":40},
    "Opening Range":{"minutes":20},
    "Initial Balance":{"minutes":45},
    "Price Volume Rank":{"period":35}
}


class TestIsolatedScalars(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=bars()

    def test_twelve_registry_members_not_promoted(self):
        self.assertEqual(len(new.PROTOTYPES),12)
        allnames={x["name"] for x in read_registry()["entries"]}
        self.assertTrue(new.PROTOTYPES<=allnames)
        self.assertTrue(new.PROTOTYPES.isdisjoint(SUPPORTED_INDICATORS))
        self.assertEqual(len(SUPPORTED_INDICATORS),38)

    def test_all_twelve_mature_values_and_causality(self):
        for name,p in PARAMETERS.items():
            with self.subTest(name=name):
                b=self.b[:390] if name in ("Opening Range","Initial Balance") else self.b
                idx=170
                block={"name":name,"parameters":p}
                first=new.value(b,idx,block)
                self.assertIsNotNone(first)
                self.assertTrue(np.isfinite(first))
                changed=b.copy()
                changed[idx+1:,3]=float("nan")
                self.assertAlmostEqual(first,new.value(changed,idx,block),places=9)

    def test_linear_regression_slope_talib_oracle(self):
        ref=talib.LINEARREG_SLOPE(self.b[:,3].copy(),timeperiod=30)
        for idx in (29,110,440,849):
            result=new.value(self.b,idx,{"name":"Linear Regression Slope",
                                            "parameters":{"period":30}})
            self.assertAlmostEqual(result,float(ref[idx]),delta=1e-7)

    def test_qstick_direct_oracle(self):
        b=self.b
        for n in (3,10,55):
            p={"name":"Qstick","parameters":{"period":n}}
            for idx in (n-1,140,840):
                self.assertAlmostEqual(new.value(b,idx,p),
                    float(np.mean(b[idx-n+1:idx+1,3]-b[idx-n+1:idx+1,0])))

    def test_vwma_independent_reference_and_no_volume(self):
        p={"name":"VWMA","parameters":{"period":18,"anchor":"session"}}
        b=self.b
        result=new.value(b,100,p)
        self.assertAlmostEqual(result,float(np.average(b[83:101,3],
                                                       weights=b[83:101,4])))
        altered=b.copy()
        altered[83:101,4]=0
        self.assertIsNone(new.value(altered,100,p))

    def test_alma_constant_price_has_exact_constant(self):
        b=self.b.copy()
        b[:,:4]=10000.
        for n in (2,9,40,120):
            x=new.value(b,350,{"name":"ALMA",
                             "parameters":{"period":n,"source":"close"}})
            self.assertAlmostEqual(x,10000.,delta=1e-8)

    def test_hma_linear_trend_matches_last_close(self):
        b=self.b.copy()
        b[:,3]=10000+np.arange(len(b))*.25
        b[:,0]=b[:,3]
        b[:,1]=b[:,3]+1
        b[:,2]=b[:,3]-1
        for n in (8,20,44):
            h=new.value(b,400,{"name":"HMA",
                             "parameters":{"period":n,"source":"close"}})
            self.assertAlmostEqual(h,b[400,3],delta=.5)

    def test_warmup_not_filled(self):
        p={"name":"HMA","parameters":{"period":32,"source":"close"}}
        self.assertIsNone(new.value(self.b,7,p))
        self.assertIsNone(new.value(self.b,31,p))
        self.assertIsNone(new.value(self.b,35,p))
        self.assertIsNotNone(new.value(self.b,40,p))
        for name in ("Opening Range","Initial Balance"):
            p=PARAMETERS[name]
            self.assertIsNone(new.value(self.b,5,{"name":name,"parameters":p}))

    def test_no_inert_fields_or_unsupported_anchors(self):
        for name,p in PARAMETERS.items():
            bad=dict(p)
            bad["unused"]="ignored"
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    new.value(self.b,140,{"name":name,"parameters":bad})
        for anchor in ("previous_completed_session","causal_timestamp"):
            with self.assertRaises(ValueError):
                new.value(self.b,145,{"name":"VWMA",
                                 "parameters":{"period":15,"anchor":anchor}})

    def test_out_of_bounds_and_future_rows_fail(self):
        for name,p in PARAMETERS.items():
            key="minutes" if "minutes" in p else "period"
            bad=dict(p)
            bad[key]=999
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    new.value(self.b,100,{"name":name,"parameters":bad})
        with self.assertRaises(ValueError):
            new.value(self.b,len(self.b),{"name":"Qstick","parameters":{"period":10}})
        with self.assertRaises(ValueError):
            new.value(self.b,400,{"name":"Opening Range","parameters":{"minutes":20}})

    def test_regression_r2_bounds_and_constant_none(self):
        q={"name":"Regression R²","parameters":{"period":50}}
        self.assertTrue(0<=new.value(self.b,300,q)<=1)
        b=self.b.copy()
        b[:,3]=19000.
        b[:,0]=19000.
        b[:,1]=19001.
        b[:,2]=18999.
        self.assertIsNone(new.value(b,200,q))

    def test_entropy_sign_changes_and_single_direction(self):
        p={"name":"Entropy","parameters":{"period":15}}
        b=self.b.copy()
        b[:,3]=19000+np.arange(len(b))*0.25
        b[:,0]=b[:,3]
        b[:,1]=b[:,3]+1.
        b[:,2]=b[:,3]-1.
        self.assertAlmostEqual(new.value(b,90,p),0.,places=9)
        r=new.value(self.b,90,p)
        self.assertGreater(r,0.)
        self.assertLessEqual(r,1.)

    def test_opening_and_ib_do_not_read_future_bars(self):
        for name in ("Opening Range","Initial Balance"):
            p=PARAMETERS[name]
            n=p["minutes"]
            b=self.b[:390]
            value=new.value(b,n-1,{"name":name,"parameters":p})
            expected=float(max(b[:n,1])-min(b[:n,2]))
            self.assertAlmostEqual(value,expected)
            self.assertAlmostEqual(value,new.value(b,118,
                           {"name":name,"parameters":p}))
            modified=b.copy()
            modified[n:,1]+=1000.
            self.assertEqual(value,new.value(modified,118,
                           {"name":name,"parameters":p}))

    def test_price_volume_rank_has_bounded_output(self):
        p={"name":"Price Volume Rank","parameters":{"period":20}}
        for idx in (30,90,270):
            z=new.value(self.b,idx,p)
            self.assertGreaterEqual(z,0)
            self.assertLessEqual(z,100)

if __name__=="__main__":
    unittest.main()
