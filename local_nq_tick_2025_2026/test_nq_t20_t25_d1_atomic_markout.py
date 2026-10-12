import unittest
from pathlib import Path
from fractions import Fraction
from nq_t20_t25_d1_atomic_markout import (
    first_post_horizon_atomic_vwap, range_at_900, bh_six,
    bootstrap_delta, aggregate, month_stage, N_SESSIONS, IDS, MAG,
    CASE, CONTROL, OTHER)

class TestAtomicPredictiveD1(unittest.TestCase):
    def test_first_complete_group_strictly_after_300s_is_atomic(self):
        t=10_000_000_000
        rows=[(t,100,1),(t+300*10_000_000,110,3),
              (t+300*10_000_000+1,130,1),
              (t+300*10_000_000+1,110,3),
              (t+300*10_000_000+2,160,2)]
        result=first_post_horizon_atomic_vwap(rows,[r[0] for r in rows],
                                               t+300*10_000_000)
        self.assertEqual(result,Fraction(115,1))
        shuffled=rows[:2]+[rows[3],rows[2]]+rows[4:]
        self.assertEqual(result,first_post_horizon_atomic_vwap(
            shuffled,[r[0] for r in shuffled],t+300*10_000_000))

    def test_no_future_group_fails_closed(self):
        t=1000
        rows=[(t,10,1),(t,11,2)]
        with self.assertRaises(ValueError):
            first_post_horizon_atomic_vwap(rows,[t,t],t)

    def test_horizon_15min_requires_observable_complete_future(self):
        t=1_000_000_000
        rows=[(t+1,100,1),(t+3,120,1)]
        with self.assertRaises(ValueError):
            range_at_900(rows,[r[0] for r in rows],t)

    def test_sealed_month_fails_before_filesystem_io(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/DO_NOT_ACCESS'),'2026-08',
                        Path('/DO_NOT_ACCESS/private.json'))

    def test_six_member_BH_including_ineligible(self):
        q=bh_six([1.,0.01,1.,1.,0.04,0.08])
        self.assertEqual(len(q),6)
        self.assertAlmostEqual(q[1],0.06)
        self.assertAlmostEqual(q[4],0.12)
        self.assertAlmostEqual(q[5],0.16)
        with self.assertRaises(ValueError):
            bh_six([0.001]*3)

    def test_group_effect_bootstrap_units_sessions_not_trades(self):
        k=IDS[1]
        rows=[{k:{'group':CASE,'side':1,'value':2.}} for _ in range(45)]
        rows += [{k:{'group':CONTROL,'side':1,'value':-1.}} for _ in range(45)]
        rows += [{k:{'group':OTHER,'side':0,'value':None}} for _ in range(45)]
        self.assertEqual(len(rows),N_SESSIONS)
        a=bootstrap_delta(rows,k,5,repeats=50)
        self.assertEqual(a['reason'],None)
        self.assertEqual(a['valid_replicates'],50)
        self.assertAlmostEqual(a['ci90'][0],3.)
        self.assertAlmostEqual(a['ci90'][1],3.)

    def test_weak_n_not_made_into_p_value(self):
        k=IDS[2]
        rows=[{k:{'group':CASE,'side':1,'value':2.}}]+[
          {k:{'group':CONTROL,'side':1,'value':1.}} for _ in range(134)]
        a=bootstrap_delta(rows,k,5,repeats=10)
        self.assertEqual(a['reason'],'LOW_GROUP_N')
        self.assertIsNone(a['p_exploratory'])

    def test_aggregate_rejects_missing_months(self):
        with self.assertRaises(ValueError):
            aggregate({})

if __name__=='__main__':unittest.main()
