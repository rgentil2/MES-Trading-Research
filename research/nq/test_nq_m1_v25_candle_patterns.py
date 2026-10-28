"""S0.20 causal candle prototype fixtures: no prices or market data."""
import unittest
import numpy as np
from research.nq.nq_m1_v25_candle_patterns import PATTERNS,classify
from research.nq.nq_m1_v2_m1_engine import SUPPORTED_INDICATORS
from research.nq.nq_m1_v2_generator import read_registry


def candle(o,h,l,c,v=100):
    assert h>=max(o,c) and l<=min(o,c)
    return (o,h,l,c,v)


class TestCandles(unittest.TestCase):
    def setUp(self):
        self.seed=np.array([candle(100,103,98,101)]*16,dtype=float)
        self.p={"body_ratio":.60,"shadow_ratio":.30}

    def value(self,name,records=None,params=None):
        b=self.seed if records is None else np.array(records,dtype=float)
        return classify(b,len(b)-1,{"name":name,"parameters":params or self.p})

    def test_twelve_in_registered_catalogue_not_promoted(self):
        self.assertEqual(len(PATTERNS),12)
        self.assertTrue(PATTERNS.isdisjoint(SUPPORTED_INDICATORS))
        catalog={e["name"] for e in read_registry()["entries"]}
        self.assertTrue(PATTERNS<=catalog)

    def test_every_pattern_returns_signed_integer_or_unknown_warmup(self):
        for name in PATTERNS:
            with self.subTest(name=name):
                got=self.value(name)
                self.assertIsInstance(got,int)
                self.assertIn(got,(-1,0,1))

    def test_engulfing_bull_and_bear(self):
        bearish=candle(103,104,99,100)
        bullish=candle(99.5,104.5,99,104)
        bearish2=candle(104.5,105,98.5,99)
        self.assertEqual(self.value("Engulfing",[bearish,bullish]),1)
        self.assertEqual(self.value("Engulfing",[bullish,bearish2]),-1)

    def test_hammer_and_shooting_star(self):
        hammer=candle(100,101.05,95,101)
        shooting=candle(100,106,99.95,99.98)
        self.assertEqual(self.value("Hammer",[hammer]),1)
        self.assertEqual(self.value("Shooting Star",[shooting]),-1)

    def test_three_candles_follow_completed_direction(self):
        up=[candle(100,105,99.8,104),candle(103,108,102.8,107),
            candle(106,111,105.8,110)]
        down=[candle(110,110.2,105,106),candle(107,107.2,102,103),
              candle(104,104.2,99,100)]
        self.assertEqual(self.value("Three White Soldiers",up),1)
        self.assertEqual(self.value("Three Black Crows",down),-1)

    def test_morning_and_evening_star(self):
        morning=[candle(110,111,99,100),candle(100,101,99,100.3),
                 candle(100.2,107.5,100,107)]
        evening=[candle(100,111,99,110),candle(110,111,109,109.8),
                 candle(109.8,110,102,103)]
        self.assertEqual(self.value("Morning Star",morning),1)
        self.assertEqual(self.value("Evening Star",evening),-1)

    def test_inside_outside_and_harami(self):
        prev=candle(100,110,99,108)
        inside=candle(106,107,103,104)
        outside=candle(109,111,98,99)
        self.assertEqual(self.value("Harami",[prev,inside]),-1)
        self.assertEqual(self.value("Inside Bar",[prev,inside]),-1)
        self.assertEqual(self.value("Outside Bar",[prev,outside]),-1)

    def test_parameters_have_effect_for_doji_and_marubozu(self):
        doji=candle(100,104.5,95.5,100.1)
        self.assertEqual(self.value("Doji",[doji],{"body_ratio":.05,"shadow_ratio":.5}),1)
        self.assertEqual(self.value("Doji",[doji],{"body_ratio":.05,"shadow_ratio":.95}),0)
        trend=candle(100,108,99,107)
        self.assertEqual(self.value("Marubozu",[trend],{"body_ratio":.6,"shadow_ratio":.2}),1)
        self.assertEqual(self.value("Marubozu",[trend],{"body_ratio":.9,"shadow_ratio":.2}),0)
        self.assertEqual(self.value("Marubozu",[trend],{"body_ratio":.6,"shadow_ratio":.05}),0)

    def test_causal_future_mutation_does_not_change_output(self):
        for name in PATTERNS:
            for idx in (3,5,10):
                first=classify(self.seed,idx,{"name":name,"parameters":self.p})
                mutated=self.seed.copy()
                mutated[idx+1:,:4]=np.nan
                second=classify(mutated,idx,{"name":name,"parameters":self.p})
                self.assertEqual(first,second)

    def test_missing_bars_not_fabricated(self):
        for name in ("Morning Star","Evening Star","Three White Soldiers","Three Black Crows"):
            self.assertIsNone(self.value(name,[candle(100,102,99,101)]))
        for name in ("Engulfing","Harami","Inside Bar","Outside Bar"):
            self.assertIsNone(self.value(name,[candle(100,102,99,101)]))

    def test_inactive_fields_and_bad_thresholds_fail_closed(self):
        for name in PATTERNS:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.value(name,params={"body_ratio":.5,"shadow_ratio":.5,"unused":4})
                with self.assertRaises(ValueError):
                    self.value(name,params={"body_ratio":.01,"shadow_ratio":.5})

    def test_cross_session_boundary_refused(self):
        b=np.tile(self.seed[:1],(391,1))
        with self.assertRaises(ValueError):
            classify(b,390,{"name":"Doji","parameters":self.p})

if __name__=="__main__":
    unittest.main()
