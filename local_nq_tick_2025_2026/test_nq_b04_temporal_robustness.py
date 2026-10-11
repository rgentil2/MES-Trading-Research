"""B04 synthetic week merge, temporal summarization and sealed gate tests."""
import unittest
from nq_b04_temporal_month import week_id,assemble_month,empty,add_trade
from nq_b04_temporal_aggregate import summarize_weekly,maximum_streak,aggregate,totals,view

class TestB04(unittest.TestCase):
    def test_iso_week_merges_month_boundary(self):
        self.assertEqual(week_id('2026-03-30'),week_id('2026-04-01'))
        self.assertEqual(week_id('2025-12-31'),week_id('2026-01-01'))
        self.assertNotEqual(week_id('2025-10-19'),week_id('2025-10-20'))

    def test_weekly_sums_and_loss_streak(self):
        a=empty();b=empty();c=empty();d=empty()
        for amount in (100.0,-30.0):add_trade(a,amount)
        add_trade(b,-20.0)
        add_trade(c,-10.0)
        add_trade(d,40.0)
        vals={'2025-W41':a,'2025-W42':b,'2025-W43':c,'2025-W44':d}
        summary=summarize_weekly(vals)
        self.assertEqual(summary['source_weeks'],4)
        self.assertEqual(summary['positive_weeks'],2)
        self.assertEqual(summary['negative_weeks'],2)
        self.assertEqual(summary['longest_streak_of_negative_active_weeks'],2)
        self.assertEqual(summary['sum_all_weeks_net_usd'],80.0)
        self.assertEqual(view(totals(vals.values()))['net_usd'],80.0)

    def test_zero_weeks_are_not_profitable(self):
        a=empty();b=empty();add_trade(a,-15)
        summary=summarize_weekly({'2026-W01':a,'2026-W02':b})
        self.assertEqual(summary['positive_weeks'],0)
        self.assertEqual(summary['weeks_without_trades'],1)
        self.assertEqual(summary['worst_week_net_usd'],-15)

    def test_month_firewall_before_root_lookup(self):
        class Poison:
            def __fspath__(self):raise AssertionError('Sealed data accessed')
        with self.assertRaises(ValueError):assemble_month(Poison(),'2026-07')
        with self.assertRaises(ValueError):assemble_month(Poison(),'2026-05')

    def test_missing_periods_rejected(self):
        with self.assertRaises(ValueError):aggregate({})

    def test_negative_streak(self):
        self.assertEqual(maximum_streak([False,True,True,False,True]),2)
        self.assertEqual(maximum_streak([]),0)

if __name__=="__main__":unittest.main()
