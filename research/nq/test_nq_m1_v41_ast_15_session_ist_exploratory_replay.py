"""S0.36 15-sample AST order-replay QA, generated M1 ONLY."""
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
import numpy as np
from research.nq import nq_m1_v41_ast_15_session_ist_exploratory_replay as s
from research.nq.nq_m1_v31_full_synthetic_lifecycle import artificial_m1
from research.nq.test_nq_m1_v31_full_synthetic_lifecycle import strat

def fixture15():
    days=["2021-05-"+f"{i:02d}" for i in range(1,16)]
    bars=np.stack([artificial_m1(seed=20261029+i,kind="UP")[0]
                   for i in range(15)])
    source={"years_opened":[2020,2021,2022],
            "holdout_2025_opened":False,"holdout_2026_opened":False,
            "complete_rth_sessions":15,
            "partial_sessions_excluded":0,"members_opened":15}
    return days,bars,source

class TestV41Limited15RolloverSessionReplay(unittest.TestCase):
    def test_15_fixed_days_full_order_cycle_and_no_formal_approval(self):
        d,b,meta=fixture15()
        r=s.compare_15(d,b,meta,[strat()],selection=list(range(15)))
        self.assertEqual(r["sessions_sampled"],15)
        self.assertEqual(r["candidate_count_exploratory"],1)
        self.assertEqual(r["candidates"][0]["sampled_days"],15)
        self.assertGreater(r["candidates"][0]["model_trades"],0)
        self.assertFalse(r["portfolio_jointly_simulated"])
        self.assertFalse(r["candidate_selection_or_fitness_approval"])
        self.assertFalse(r["exact_MFFU_shared_account_rules_certified"])
        self.assertEqual(r["formal_13_gates_verified"],0)
        self.assertEqual(r["counts"]["post_fill_unmodelled"],0)

    def test_unknown_or_truncated_samples_fail_closed(self):
        d,b,meta=fixture15()
        for bad in (list(range(14)),list(range(1,15))+[14],
                    list(range(14))+[999]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                s.compare_15(d,b,meta,[strat()],selection=bad)

    def test_2023_2026_never_accepted(self):
        d,b,meta=fixture15()
        for year in ("2023","2024","2025","2026"):
            changed=d.copy();changed[-1]=f"{year}-05-15"
            with self.subTest(year=year),self.assertRaises(PermissionError):
                s.compare_15(changed,b,meta,[strat()],selection=list(range(15)))

    def test_archive_must_match_frozen_original_sha(self):
        with TemporaryDirectory() as td:
            p=Path(td)/"unauth.zip";p.write_bytes(b"not frozen")
            with self.assertRaises(PermissionError):
                s.real_archive_pilot_15(p)

if __name__=="__main__": unittest.main()
