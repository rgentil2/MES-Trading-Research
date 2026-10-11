"""B03 synthetic causality / surcharge / inter-month chronological DD regression."""
from __future__ import annotations
import unittest
from nq_b03_execution_headroom import (surcharge_usd,adjusted_trade,audit_month,
    day_audit,SURCHARGE_TICKS_PER_SIDE)
from nq_b03_aggregate import stitch,aggregate
from nq_t08_risk_audit import Envelope
from dataclasses import replace

class B03Tests(unittest.TestCase):
    def test_fixed_surcharge_usd(self):
        self.assertEqual([surcharge_usd(i) for i in SURCHARGE_TICKS_PER_SIDE],
                         [0,10,20,40])
        with self.assertRaises(ValueError):surcharge_usd(3)

    def test_adjusted_trade_never_changes_frozen_path(self):
        r={'entry_timestamp':10,'exit_timestamp':100,'entry_price_ticks':400,
            'exit_price_ticks':410,'exit_reason':'TAKE_PROFIT',
            'estimated_net_usd':45.0,'side':1}
        original=dict(r)
        a=adjusted_trade(r,20)
        self.assertEqual(a['estimated_net_usd'],25.0)
        for k in ('entry_timestamp','exit_timestamp','entry_price_ticks',
                  'exit_price_ticks','exit_reason','side'):
            self.assertEqual(a[k],r[k])
        self.assertEqual(r,original)

    def test_sealed_month_rejected_before_filesystem(self):
        class NoRoot:
            def __fspath__(self):raise AssertionError('Sealed path touched')
        with self.assertRaises(ValueError):audit_month(NoRoot(),'2026-07')
        with self.assertRaises(ValueError):audit_month(NoRoot(),'2026-05')

    def test_chronological_stitch_conserves_local_equity(self):
        a={'trades':1,'frozen_path_adjusted_net_usd':100.0,
           'gross_positive_net_usd':100.0,'gross_negative_net_usd':0.0,
           'last_envelope_segment':{'equity':100,'low':-20,'high':110,
            'max_dd':30,'closed_low':0,'closed_high':100,'closed_dd':0}}
        b={'trades':1,'frozen_path_adjusted_net_usd':-20.0,
           'gross_positive_net_usd':0.0,'gross_negative_net_usd':20.0,
           'last_envelope_segment':{'equity':-20,'low':-80,'high':0,
            'max_dd':80,'closed_low':-20,'closed_high':0,'closed_dd':20}}
        v=stitch([a,b])
        self.assertEqual(v['trades'],2)
        self.assertEqual(v['adjusted_net_usd_FROZEN_PATH_ONLY'],80.0)
        self.assertEqual(v['last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH'],90.0)
        self.assertEqual(v['closed_trade_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH'],20.0)

    def test_missing_dev_month_fails_completeness(self):
        with self.assertRaises(ValueError):aggregate({})

if __name__=='__main__':
    unittest.main()
