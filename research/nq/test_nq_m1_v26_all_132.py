"""V2.6 S0.21 132/132 CODE coverage + causal and parameter checks (synthetic only).

All 132 names are actually invoked, never merely counted in a registry.
Full economic release requires external mathematical parity, parameter
lineage, historical data, broker fill certification and separate approval.
"""
import unittest
import copy
import numpy as np
from research.nq.nq_m1_v2_generator import read_registry
from research.nq.nq_m1_v2_m1_engine import SUPPORTED_INDICATORS
from research.nq.nq_m1_v26_all_132_router import value,inventory
from research.nq.nq_m1_v26_trend_momentum import NAMES as TREND
from research.nq.nq_m1_v26_volume_levels import NAMES as VOL
from research.nq.nq_m1_v26_cycles_gaps import NAMES as CYCLES


def synthetic(size=390,seed=26):
    rng=np.random.default_rng(seed)
    c=19000+np.cumsum(rng.normal(.07,4,size))
    o=c+rng.normal(0,.8,size)
    h=np.maximum(o,c)+rng.uniform(.3,2,size)
    l=np.minimum(o,c)-rng.uniform(.3,2,size)
    v=rng.integers(100,3000,size).astype(float)
    return np.column_stack([o,h,l,c,v])


def parameters(entry):
    p={}
    for k,r in entry["parameters"].items():
        if k=="constraint":continue
        if len(r)==2 and all(type(x) in (int,float) for x in r):
            p[k]=max(int(r[0]),min(int(r[1]),20)) if all(type(x) is int for x in r) else (r[0]+r[1])/2
        elif isinstance(r,list):
            p[k]="close" if "close" in r else "session" if "session" in r else r[0]
        else:raise AssertionError(k)
    if p.get("fast_period",0)>=p.get("slow_period",10**9):
        p["fast_period"]=p["slow_period"]-1
    return p


class TestV26All132(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=synthetic()
        cls.prev=synthetic(390,27)
        cls.context={"verified_same_contract":True,
            "previous_sessions":[synthetic(390,k+30) for k in range(20)],
            "anchor_index":100}
        cls.entries=read_registry()["entries"]

    def test_cover_65_new_indicators_exclusive(self):
        self.assertEqual(len(TREND),27)
        self.assertEqual(len(VOL),21)
        self.assertEqual(len(CYCLES),17)
        self.assertEqual(len(TREND|VOL|CYCLES),65)
        self.assertTrue((TREND|VOL|CYCLES).isdisjoint(SUPPORTED_INDICATORS))
        self.assertEqual(inventory()["coded"],132)
        self.assertEqual(inventory()["frozen_original"],38)
        self.assertEqual(inventory()["new_isolated"],65)
        self.assertFalse(inventory()["economic_execution_authorized"])

    def test_invoke_every_catalogue_block_on_realistic_ohlcv(self):
        reached=set()
        unavailable=[]
        for e in self.entries:
            p=parameters(e)
            block={"registry_id":e["id"],"name":e["name"],"parameters":p}
            with self.subTest(name=e["name"]):
                result=value(self.b,360,block,self.context)
                reached.add(e["name"])
                if result is None:unavailable.append(e["name"])
                else:self.assertTrue(np.isfinite(result),str(result))
        self.assertEqual(len(reached),132)
        # A complete synthetic 390-bar current session and 20 previous 390-bar
        # sessions provide realistic minimal warmups for period <=20.
        self.assertFalse(unavailable,"Unimplemented/unavailable with full context: "+repr(unavailable))

    def test_all_132_future_mutation_invariant(self):
        changed=self.b.copy()
        changed[361:,:]=np.nan
        for e in self.entries:
            with self.subTest(name=e["name"]):
                block={"name":e["name"],"parameters":parameters(e)}
                before=value(self.b,360,block,self.context)
                after=value(changed,360,block,self.context)
                self.assertEqual(before,after)

    def test_all_132_refuse_inert_extraneous_or_wrong_registry_id(self):
        for e in self.entries:
            p=parameters(e)
            p["unregistered_param"]=3.14159
            with self.subTest(name=e["name"]):
                with self.assertRaises(ValueError):
                    value(self.b,360,{"name":e["name"],"parameters":p},self.context)
                with self.assertRaises(ValueError):
                    value(self.b,360,{"name":e["name"],"registry_id":"FORGED",
                                      "parameters":parameters(e)},self.context)

    def test_same_contract_context_absence_never_imputed(self):
        anchors=[
          ("Anchored VWAP",{"anchor":"causal_timestamp"}),
          ("Previous Day High/Low",{"sessions_back":2}),
          ("Opening Gap",{"period":20}),
          ("Classic Pivots",{"period":20,"anchor":"previous_completed_session"})
        ]
        for name,p in anchors:
            with self.subTest(name=name):
                self.assertIsNone(value(self.b,350,{"name":name,"parameters":p},None))

    def test_bad_timestamp_never_reads_future(self):
        block={"name":"Anchored VWAP","parameters":{"anchor":"causal_timestamp"}}
        self.assertIsNone(value(self.b,200,block,{"anchor_index":250}))
        self.assertIsNotNone(value(self.b,250,block,{"anchor_index":250}))

    def test_pattern_three_bar_warmup_not_imputed(self):
        b=synthetic(1)
        block={"name":"Morning Star","parameters":{"body_ratio":.5,"shadow_ratio":.4}}
        self.assertIsNone(value(b,0,block))

    def test_distinct_output_line_selector_and_guard(self):
        p={"period":20,"std_multiplier":2.}
        b={"name":"Bollinger Bands","parameters":p}
        upper=value(self.b,200,b)
        lower=value(self.b,200,dict(b,output="lower"))
        self.assertGreater(upper,lower)
        with self.assertRaises(ValueError):
            value(self.b,200,dict(b,output="favorable_only"))
        with self.assertRaises(ValueError):
            value(self.b,200,{"name":"MACD","parameters":{
                "fast_period":5,"slow_period":20,"signal_period":9},"output":"upper"})

    def test_high_level_threshold_changes_signed_scalar(self):
        b={"name":"ADX","parameters":{"period":20,"threshold":10}}
        v10=value(self.b,360,b)
        v60=value(self.b,360,{"name":"ADX","parameters":{"period":20,"threshold":60}})
        self.assertAlmostEqual(v10-v60,50,places=6)

    def test_frozen_v21_38_untouched(self):
        from research.nq.nq_m1_v2_m1_engine import SUPPORTED_INDICATORS
        self.assertEqual(len(SUPPORTED_INDICATORS),38)
        self.assertNotIn("MACD",SUPPORTED_INDICATORS)
        self.assertNotIn("Hurst Exponent",SUPPORTED_INDICATORS)

    def test_nonfinite_or_invalid_high_low_refused(self):
        b=self.b.copy();b[90,2]=b[90,1]+1
        with self.assertRaises(ValueError):
            value(b,100,{"name":"MACD","parameters":{"fast_period":6,"slow_period":25,
                         "signal_period":9}})
        with self.assertRaises(ValueError):
            value(self.b,len(self.b),{"name":"MACD","parameters":{
                  "fast_period":6,"slow_period":25,"signal_period":9}})

if __name__=="__main__":
    unittest.main()
