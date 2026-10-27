"""NQ S0.8 contract metadata adapter tests: no market reads."""
import unittest
import numpy as np
from research.nq import nq_m1_v22_contract_provenance as cp
from research.nq.nq_h05_h07_level_volume_screen import roll_contract
from datetime import date


def bars(n=4):
    x=np.empty((n,390,5))
    for day in range(n):
        p=20000.+np.arange(390)*.25+day*10.
        x[day,:,0]=p
        x[day,:,1]=p+1.
        x[day,:,2]=p-1.
        x[day,:,3]=p+.25
        x[day,:,4]=1000.
    return x


class TestNQContractWarmup(unittest.TestCase):
    def test_metadata_follows_identical_roll_map_as_archive_loader(self):
        dates=["2020-03-10","2020-03-11","2020-03-12","2020-03-13"]
        labels=cp.metadata_for_sessions(dates,bars(4))
        self.assertEqual([m.contract_id for m in labels],
                         [roll_contract(date.fromisoformat(d)) for d in dates])
        self.assertEqual(labels[0].symbol,"NQ")

    def test_rolled_contract_must_not_splice_old_into_new(self):
        dates=["2020-03-10","2020-03-11","2020-03-12","2020-03-13"]
        labels=cp.metadata_for_sessions(dates,bars(4))
        changes=[i for i in range(1,4) if labels[i].contract_id!=labels[i-1].contract_id]
        self.assertEqual(len(changes),1)
        x=cp.prior_same_contract(dates,bars(4),changes[0])
        self.assertEqual(x["prior_bars"].shape,(0,5))
        self.assertTrue(x["contract_boundary_detected"])
        y=cp.prior_same_contract(dates,bars(4),changes[0]+1)
        self.assertEqual(y["prior_bars"].shape,(390,5))
        self.assertEqual(y["source_contract"],labels[-1].contract_id)

    def test_two_prior_same_contract_sessions_are_supported(self):
        dates=["2021-05-03","2021-05-04","2021-05-05","2021-05-06"]
        x=cp.prior_same_contract(dates,bars(4),3)
        self.assertEqual(x["prior_bars"].shape,(780,5))
        self.assertEqual(x["prior_session_dates"],dates[1:3])

    def test_no_2023_24_and_no_2025_26(self):
        for year in (2023,2024,2025,2026):
            with self.assertRaises(PermissionError):
                cp.metadata_for_sessions([f"{year}-01-02"],bars(1))

    def test_unsorted_and_duplicate_and_partial_rejected(self):
        for dates in (["2021-05-04","2021-05-03"],["2021-05-04","2021-05-04"]):
            with self.assertRaises(ValueError):
                cp.metadata_for_sessions(dates,bars(2))
        with self.assertRaises(ValueError):
            cp.metadata_for_sessions(["2021-05-04"],np.zeros((1,389,5)))

    def test_roll_audit_has_exact_allowed_years_and_no_raw_values(self):
        dates=["2020-03-10","2020-03-11","2020-03-12","2020-03-13"]
        a=cp.audit_roll_coverage(dates,bars(4))
        self.assertEqual(a["sessions"],4)
        self.assertEqual(a["holdouts"],"SEALED")
        self.assertEqual(a["years_allowed"],[2020,2021,2022])
        self.assertEqual(len(a["changes"]),1)
        self.assertNotIn("prices",str(a))


if __name__=="__main__":
    unittest.main()
