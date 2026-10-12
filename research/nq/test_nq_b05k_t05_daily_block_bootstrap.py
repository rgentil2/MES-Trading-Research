import unittest
from datetime import date,timedelta
from unittest.mock import patch
from pathlib import Path
from nq_b05k_t05_daily_block_bootstrap import (
    moving_block_stats,calculate,month_stage,MONTHS,MONTH_EXPECTATIONS,
    B,SEED)
from nq_tick_short_horizon import dev_day

class TestB05K(unittest.TestCase):
    def test_block_bootstrap_reproducible_and_separate_lengths(self):
        v=[15.0,-2.0,0.0,7.0,0.0]*27
        a=moving_block_stats(v,5,seed=SEED+5,reps=125)
        b=moving_block_stats(v,5,seed=SEED+5,reps=125)
        self.assertEqual(a,b)
        self.assertEqual(a['resamples'],125)
        self.assertEqual(a['length_sessions'],5)
        self.assertFalse(a['p_is_confirmatory'])
    def test_zero_days_count_in_mean(self):
        v=[0.0]*100+[10.0]*35
        z=moving_block_stats(v,5,seed=SEED+5,reps=100)
        self.assertAlmostEqual(z['mean_daily_usd'],350./135,places=4)
        self.assertGreater(z['ci90_width_usd'],0.)
    def test_bad_bootstrap_rejected(self):
        for v,L in [([1.]*10,5),([1.]*135,136),([1.]*135,1),
                    ([float('nan')]*135,5)]:
            with self.assertRaises(ValueError):
                moving_block_stats(v,L,reps=100)
    def test_month_hard_seal_before_file_iteration(self):
        class Bomb:
            def __fspath__(self):raise AssertionError('sealed filesystem')
        with self.assertRaisesRegex(ValueError,'SEALED'):
            month_stage(Bomb(),'2026-05',Path('/tmp/forbidden'))
    def test_daily_cost_conservation_and_monthly_gate(self):
        # Source-side synthetic data; no actual tick archive read. Every month
        # has only weekdays and count totals frozen but fake individual outcomes.
        cap=[13,20,23,22,20,21,21]
        self.assertEqual(sum(cap),140)
        full={}
        exclusions=[0,1,1,1,1,1,0] # sum5
        for month,size,miss in zip(MONTHS,cap,exclusions):
            y,m=map(int,month.split('-'))
            start=date(y,m,15 if month=='2025-10' else 1)
            days=[]
            while len(days)<size:
                if start.weekday()<5 and start.strftime('%Y-%m')==month:
                    days.append(start.isoformat())
                start+=timedelta(days=1)
            elig=size-miss
            count,total=MONTH_EXPECTATIONS[month]
            self.assertLessEqual(count,2*elig)
            payload=[]
            rest=count;money=total
            for i,d in enumerate(days):
                if i>=elig:
                    payload.append({'day':d,'ready':False})
                    continue
                trades=min(2,rest)  # synthetic construction; never actual fills
                rest-=trades
                pnl=money if trades and rest==0 else 0
                if pnl:money=0
                payload.append({'day':d,'ready':True,
                  'trades':trades,'stress_cents':pnl,
                  'stress_extra_cents':pnl-1000*trades})
            self.assertEqual(rest,0)
            self.assertEqual(money,0)
            full[month]={'month':month,'source':size,'eligible':elig,
                'days':payload,'holdout_read':False,
                'new_history_acquired':False}
        with patch('nq_b05k_t05_daily_block_bootstrap.B',100):
            z=calculate(full)
        self.assertEqual(z['n_source_days'],140)
        self.assertEqual(z['n_eligible_sessions'],135)
        self.assertEqual(z['n_trades'],115)
        self.assertFalse(z['daily_outcomes_publicly_exported'])
        self.assertEqual(z['scenarios']['stress']['total_usd'],5102.5)
        self.assertEqual(z['scenarios']['stress_extra10_fixed_path']['total_usd'],3952.5)
        # No daily array or timestamps in the public aggregate.
        self.assertNotIn("'days':",str(z))
        self.assertNotIn('2025-10-15',str(z))
    def test_aggregate_rejects_implicit_OOS_or_missing_month(self):
        with self.assertRaises(ValueError):calculate({})
        with self.assertRaises(ValueError):calculate({m:{} for m in MONTHS[:-1]})

if __name__=='__main__':
    unittest.main()
