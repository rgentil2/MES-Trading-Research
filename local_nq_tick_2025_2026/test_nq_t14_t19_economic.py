import unittest
from unittest.mock import patch
from pathlib import Path
from nq_t14_t19_economic_and_magnitude import (
    combined,future_range,month_stage,trace,DIRECTIONAL,MODELS,ROUTERS)
from nq_t14_t19_economic_aggregate import bh,aggregate
from nq_t08_risk_audit import Envelope
class Tests(unittest.TestCase):
    def test_four_new_models_predeclared(self):
        self.assertEqual(len(DIRECTIONAL),4)
        self.assertEqual(len(MODELS),9)
    def test_t05_priority_same_timestamp(self):
        t05=[(10,1,'T05_377')]
        new=[(10,-1,'T14_PERSISTENT_DRIFT')]
        self.assertEqual(combined(t05,new),t05)
        self.assertEqual(combined(t05,[(20,-1,'T14_PERSISTENT_DRIFT')]),
                         t05+[(20,-1,'T14_PERSISTENT_DRIFT')])
    def test_magnitude_strictly_after_decision(self):
        a=[(100,1000,1),(200,900,1),(201,1020,1),(300,950,1)]
        ts=[x[0] for x in a]
        self.assertEqual(future_range(a,ts,200),70)
        self.assertIsNone(future_range(a,ts,1000))
    def test_bh_four_member_family_with_zero_signal(self):
        q=bh({'a':.01,'b':.04,'c':.20,'zero':1.})
        self.assertAlmostEqual(q['a'],.04)
        self.assertAlmostEqual(q['b'],.08)
        self.assertEqual(q['zero'],1.)
    def test_sealed_guard_before_any_filesystem(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/DO_NOT_ACCESS'),'2026-08',
                Path('/DO_NOT_WRITE/private.json'))
    def test_incomplete_or_untrusted_months_fail_closed(self):
        with self.assertRaises(ValueError):aggregate({})
    def test_no_false_trade_when_no_signals(self):
        self.assertEqual(combined([(10,1,'T05_377')],[]),[(10,1,'T05_377')])
if __name__=='__main__':unittest.main()
