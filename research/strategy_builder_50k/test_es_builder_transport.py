"""Synthetic-only tests: no ES prices and no LFS interactions."""
import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
BUILDER=Path(__file__).resolve().parent
for p in (str(ROOT),str(BUILDER)):
    if p not in sys.path:sys.path.insert(0,p)
from run_es_builder_transport import set_mes_policy,check_precommit
import engine,v2_engine

class TestESTransport(unittest.TestCase):
    def test_frozen_144(self):
        v1,v2=check_precommit()
        self.assertEqual((len(v1),len(v2)),(48,96))
    def test_mes_economic_only(self):
        before=[x.digest() for x in check_precommit()[0]]
        set_mes_policy()
        self.assertEqual(engine.POINT_MNQ,5)
        self.assertEqual(v2_engine.POINT_MNQ,5)
        self.assertEqual(engine.FEE_MNQ_RT,1.90)
        self.assertEqual(v2_engine.FEE_MNQ_RT,1.90)
        after=[x.digest() for x in check_precommit()[0]]
        self.assertEqual(before,after)
    def test_guard_rejects_future_content_before_market_read(self):
        from engine import analyze
        import numpy as np
        toy=np.ones((1,390,5))*100
        with self.assertRaisesRegex(ValueError,'SEALED'):
            analyze(toy,['2025-01-01'],check_precommit()[0][:1],replications=100)