#!/usr/bin/env python3
"""Predata synthetic tests: atomic 233 mechanisms, time windows and sealed periods."""
import unittest
from nq_b05h_atomic_print_bars import CompletedPrintBar as B
from nq_t189_t208_monetary_month import (
 IDS,CODES,WINDOWS,load_frozen,choose,run_month)

def bar(vwap,width=12,vol=100,duration=20,groups=233,prints=233):
    return B(233,prints,vol,int(vol*vwap),vwap+width//2,vwap-width//2,
             1,1+duration,groups)

class MonetaryBatch(unittest.TestCase):
    def test_frozen_20(self):
        self.assertEqual(list(IDS),[f'T{i}' for i in range(189,209)])
        x=load_frozen()
        self.assertEqual(len(x['members']),20)
        self.assertEqual(len(WINDOWS),4)
        self.assertFalse(x['new_signals_use_five_seconds'])

    def test_fast_prints_and_slow_reversal(self):
        self.assertEqual(choose('A_FAST_BREAK',bar(108,20,100,10),bar(100,12,100,20),bar(95)),1)
        self.assertEqual(choose('A_SLOW_REVERSAL',bar(102,12,100,50),bar(100,12,100,20),bar(94)),-1)

    def test_cluster_and_volume(self):
        self.assertEqual(choose('A_CLUSTER_FADE',bar(110,30,100,20,100),bar(100),bar(90)),-1)
        self.assertEqual(choose('A_VOLUME_SURGE',bar(110,12,200),bar(100,12,100),bar(95)) ,1)
        self.assertEqual(choose('A_VOLUME_DROP_TURN',bar(95,12,40),bar(100,12,100),bar(110)), -1)

    def test_micro_accept_and_sweep(self):
        self.assertEqual(choose('B_ACCEPT_UP',bar(120,8),bar(100,10),bar(104,10)),1)
        self.assertEqual(choose('B_ACCEPT_DOWN',bar(80,8),bar(100,10),bar(104,10)),-1)
        self.assertEqual(choose('B_SWEEP_HIGH',bar(107,30),bar(100,10),bar(104,10)),-1)
        self.assertEqual(choose('B_SWEEP_LOW',bar(97,30),bar(100,10),bar(104,10)),1)

    def test_absorption_is_last_proxy(self):
        self.assertEqual(choose('C_ABSORPTION_PROXY',bar(110,12,180),bar(110,12,100),bar(100)),-1)
        self.assertEqual(choose('C_THIN_DRIFT',bar(108,12,60),bar(100,12,100),bar(95)),1)
        self.assertEqual(choose('C_EXPANSION_CONFIRM',bar(110,28,160),bar(100,12,100),bar(95)),1)

    def test_trend_chop_and_tempo(self):
        self.assertEqual(choose('D_ASCENDING_EXPANSION',bar(115,30),bar(110,20),bar(100,10)),1)
        self.assertEqual(choose('D_DESCENDING_EXPANSION',bar(85,30),bar(90,20),bar(100,10)),-1)
        self.assertEqual(choose('D_ALTERNATION',bar(105,12),bar(100,20),bar(110,10)),1)
        self.assertEqual(choose('D_DECELERATION',bar(102,10,100,90),bar(100,20,100,40),bar(90,15,100,20)),-1)
        self.assertEqual(choose('D_BURST_WITHOUT_PROGRESS',bar(110,10,190,8),bar(110,15,100,20),bar(100)), -1)

    def test_zero_no_future_guesses(self):
        self.assertEqual(choose('C_ABSORPTION_PROXY',bar(110,12,80),bar(110,12,100),bar(100)),0)
        self.assertEqual(choose('D_BURST_WITHOUT_PROGRESS',bar(110,10,100,30),bar(110,15,100,20),bar(100)),0)
        with self.assertRaises(ValueError):
            choose('NOT_REGISTERED',bar(100),bar(90),bar(80))

    def test_sealed_rejected_before_filesystem(self):
        for m in ('2026-05','2026-09','2020-01'):
            with self.assertRaises(ValueError):
                run_month(None,m)

if __name__=='__main__':
    unittest.main()
