"""B05B T12 synthetic no-lookahead, nonredundant controls and holdout firewall."""
import unittest
from nq_b05b_t12_compression import signal_at,candidates_t12,FAMILIES
from nq_b05b_t12_month import shared_signals,analyze_month
from nq_b05b_t12_aggregate import aggregate

DAY="2025-10-15"
INDEX=1200

def fixture():
    b=[[20010,20020,20000,20010,10,10] for _ in range(2880)]
    for i in range(INDEX-60,INDEX-12):
        b[i]=[20030,20100,19900,20030,10,10]
    for i in range(INDEX-12,INDEX):
        b[i]=[20016,20020,20010,20016,20,20]
    b[INDEX]=[20018,20025,20015,20024,40,40]
    return b

class B05BT12Tests(unittest.TestCase):
    def test_long_compression_breakout_acceleration(self):
        b=fixture()
        self.assertTrue(signal_at(b,INDEX,1))
        self.assertFalse(signal_at(b,INDEX,-1))
    def test_no_lookahead_causal_future(self):
        b=fixture()
        yes=signal_at(b,INDEX,1)
        b[INDEX+1]=[30000,40000,10,10,100000,100000]
        self.assertEqual(signal_at(b,INDEX,1),yes)
    def test_activity_ablation_is_not_identical_by_logic(self):
        b=fixture()
        for i in range(INDEX-5,INDEX+1):b[i][4]=1
        self.assertFalse(signal_at(b,INDEX,1))
        self.assertTrue(signal_at(b,INDEX,1,without_activity=True))
    def test_compression_ablation_independent_condition(self):
        b=fixture()
        for i in range(INDEX-12,INDEX):
            b[i]=[20040,20110,19940,20040,20,20]
        b[INDEX]=[20110,20114,20108,20113,40,40]
        self.assertFalse(signal_at(b,INDEX,1))
        self.assertTrue(signal_at(b,INDEX,1,without_compression=True))
    def test_trigger_not_inside_compressed_range(self):
        b=fixture()
        b[INDEX]=[20017,20030,20015,20020,40,40]
        self.assertFalse(signal_at(b,INDEX,1))
    def test_gap_between_history_and_trigger_rejected(self):
        b=fixture()
        b[INDEX-4]=None
        self.assertFalse(signal_at(b,INDEX,1))
    def test_global_cooldown(self):
        b=fixture()
        all_sigs,both=candidates_t12(b,DAY)
        self.assertEqual(both,0)
        for model,items in all_sigs.items():
            self.assertTrue(all(j[0]-i[0]>=60 for i,j in zip(items,items[1:])),model)
    def test_router_t05_fixed_priority(self):
        r,t=shared_signals([(1200,-1),(1202,1)],[(1200,1),(1201,-1)])
        self.assertEqual(t,1)
        self.assertEqual(r,[(1200,-1,'T05_377'),(1201,-1,'T12_FULL'),(1202,1,'T05_377')])
    def test_sealed_data_rejected_before_filesystem_access(self):
        class Poison:
            def __fspath__(self):raise AssertionError('Private holdout touched')
        with self.assertRaises(ValueError):analyze_month(Poison(),"2026-05")
        with self.assertRaises(ValueError):analyze_month(Poison(),"2026-07")
    def test_missing_dev_months_gate(self):
        with self.assertRaises(ValueError):aggregate({})

if __name__=="__main__":unittest.main()
