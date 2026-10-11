import unittest
from qc_tick_day import check_day,utc_bounds
from nq_tick_short_horizon import (
    dev_day,build_bars,complete,candidates,analyze_bars,
    OR_START,OR_END,N_BARS,STEP_100NS,FAMILIES
)
DAY='2025-10-15'

class TestNQ5SecondJointFamilies(unittest.TestCase):
    def test_holdouts_blocked(self):
        for day in ('2026-05-01','2026-06-16','2026-07-01','2026-10-09','2025-10-14'):
            with self.assertRaises(ValueError):dev_day(day)
    def test_holdout_guard_before_any_tick_access(self):
        class Bomb:
            def __iter__(self):raise AssertionError('sealed iterator opened')
        with self.assertRaises(ValueError):build_bars(Bomb(),'2026-05-06')
    def test_5second_price_trade_count_and_qty(self):
        start=utc_bounds(check_day(DAY))[0]
        bars=build_bars([(start,400,2),(start+1,404,3),
                         (start+STEP_100NS,401,5)],DAY)
        self.assertEqual(bars[0],[400,404,400,404,2,5])
        self.assertEqual(bars[1][5],5)
    def test_invalid_last_row(self):
        start=utc_bounds(check_day(DAY))[0]
        with self.assertRaises(ValueError):
            build_bars([(start,400,0)],DAY)
        with self.assertRaises(ValueError):
            build_bars([(start+1,400,1),(start,400,1)],DAY)
    def test_dst_zone_stays_4hours(self):
        for day in ('2025-10-15','2025-11-03','2026-03-09'):
            x,y=utc_bounds(dev_day(day))
            self.assertEqual(y-x,4*3600*10000000)
    def test_missing_opening_range_is_skipped(self):
        r=analyze_bars([None]*N_BARS,DAY)
        self.assertEqual(r['status'],'SKIP_MISSING_OPENING_RANGE')
    def test_complete_disallows_forward_filled(self):
        b=[None]*N_BARS
        self.assertIsNone(complete(b,OR_START,OR_END))
    def test_crossing_plus_trade_rate_creates_joint_signal(self):
        bars=[None]*N_BARS
        for i in range(OR_START,OR_END+200):
            bars[i]=[110,111,109,110,10,50]
        bars[OR_START]=[110,120,100,110,10,50]
        i=OR_END+65
        for j in range(i-5,i+1):bars[j][4]=20
        bars[i-12][3]=110
        bars[i-1][3]=120
        bars[i][3]=125;bars[i][1]=125
        c,status=candidates(bars,DAY)
        self.assertEqual(status,'READY')
        self.assertIn((i,1),c['T01_combined'])
        self.assertIn((i,1),c['C01_breakout_no_rate'])
    def test_five_frozen_variants(self):
        self.assertEqual(len(FAMILIES),5)
        self.assertIn('T03_router',FAMILIES)
    def test_no_fabricated_outcomes_on_missing_bars(self):
        b=[None]*N_BARS
        for i in range(OR_START,OR_END):b[i]=[110,120,100,110,5,20]
        o=analyze_bars(b,DAY)
        self.assertEqual(o['families']['T03_router']['opportunities'],0)
        self.assertIsNone(o['families']['T03_router']['forward_ticks']['5']['mean'])
        self.assertFalse(o['execution_or_pnl_simulated'])

if __name__=='__main__':unittest.main()
