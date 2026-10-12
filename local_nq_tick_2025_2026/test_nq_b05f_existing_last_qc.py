import unittest
from qc_tick_day import utc_bounds
from nq_b05f_existing_last_qc import (
    audit_stream,month_summary,aggregate,MONTHS,WINDOW_START,LENGTHS)
from nq_tick_short_horizon import STEP_100NS

DAY='2025-10-15'
LO=utc_bounds(__import__('datetime').date.fromisoformat(DAY))[0]

def at(i,delta=1):
    return LO+i*STEP_100NS+delta

def opening_events():
    # Exactly one print in each OR 5s slot; 4 ticks opening width, so READY.
    return [(at(i),100+(4 if i==1139 else 0),1)
            for i in range(1080,1140)]

class B05F(unittest.TestCase):
    def test_no_future_at_five_second_cutoff(self):
        # 465 Last before 09:40:05, the 466th print exactly at 09:40:05
        # may not be observed on 09:40:00-09:40:05 decision.
        e=opening_events()
        e += [(at(1200,k+1),200,1) for k in range(405)]
        e.append((at(1201,0),200,1))
        z=audit_stream(e,DAY)
        self.assertEqual(z['state'],'READY')
        self.assertEqual(z['readiness']['233']['ready_window_5s_decisions'],
                         1079)
        self.assertEqual(z['readiness']['233']['ready_at_0930'],0)
        self.assertEqual(z['readiness']['233']['ready_at_1000'],1)
    def test_n_counts_prints_not_qty(self):
        e=opening_events()+[(at(1200),200,50000)]
        z=audit_stream(e,DAY)
        self.assertEqual(z['counters']['last_events'],61)
        self.assertEqual(z['counters']['last_contracts'],50060)
        self.assertEqual(z['readiness']['233']['ready_window_5s_decisions'],0)
    def test_all_four_print_lengths_complete_with_sufficient_rows(self):
        e=opening_events()
        e.extend((at(1200,k+1),300,1) for k in range(22000))
        z=audit_stream(e,DAY)
        self.assertEqual(z['state'],'READY')
        for n in LENGTHS:
            self.assertEqual(z['readiness'][str(n)]['ready_window_5s_decisions'],
                             1080)
        self.assertEqual(z['counters']['same_timestamp'],0)
    def test_gaps_are_not_assumed_bad_ticks_or_auto_deleted(self):
        e=opening_events()+[(at(1200),100,1)]
        z=audit_stream(e,DAY)
        self.assertGreater(z['counters']['missing_5s_0940_1110'],0)
        self.assertGreater(z['counters']['gaps_ge_60s'],0)
        self.assertEqual(z['state'],'READY')
    def test_invalid_timestamp_and_qty_fail_closed(self):
        e=opening_events()
        with self.assertRaisesRegex(ValueError,'decreasing'):
            audit_stream(e+[e[-2]],DAY)
        with self.assertRaisesRegex(ValueError,'quantity'):
            audit_stream(e+[(at(1200),300,0)],DAY)
        with self.assertRaisesRegex(ValueError,'out of ET session'):
            audit_stream([(LO-1,100,1)],DAY)
    def test_sealed_rejected_before_source_generator_is_read(self):
        class Bomb:
            def __iter__(self):
                raise AssertionError('opened sealed source')
        for day in ('2026-05-01','2026-06-01','2026-07-01'):
            with self.assertRaises(ValueError):
                audit_stream(Bomb(),day)
    def test_same_timestamp_not_invalid(self):
        e=opening_events()+[(at(1200),200,1),(at(1200),201,2)]
        z=audit_stream(e,DAY)
        self.assertEqual(z['counters']['same_timestamp'],1)
        self.assertEqual(z['counters']['same_timestamp_price_changes'],1)
        self.assertEqual(z['state'],'READY')
    def test_month_safety_contract(self):
        x=audit_stream(opening_events(),DAY)
        z=month_summary('2025-10',[x])
        self.assertEqual(z['eligible_days'],1)
        self.assertEqual(z['qc_counters']['last_events'],60)
        self.assertFalse(z['trade_results_computed'])
        with self.assertRaises(ValueError):
            month_summary('2026-05',[x])
    def test_aggregate_requires_seven_frozen_months(self):
        x=month_summary('2025-10',[audit_stream(opening_events(),DAY)])
        with self.assertRaisesRegex(ValueError,'7 DEV'):
            aggregate({'2025-10':x})
        bad={m:dict(x,month=m) for m in MONTHS}
        with self.assertRaisesRegex(ValueError,'140 source /135 ready'):
            aggregate(bad)
        bad[MONTHS[0]]=dict(bad[MONTHS[0]],holdouts_opened=True)
        with self.assertRaisesRegex(ValueError,'unsafe'):
            aggregate(bad)

if __name__=='__main__':unittest.main()
