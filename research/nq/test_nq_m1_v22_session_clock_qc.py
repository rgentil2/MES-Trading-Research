"""Independent NY RTH minute end clock checks with DST; synthetic only."""
import unittest
from datetime import datetime, timedelta, timezone
from research.nq import nq_m1_v22_session_clock_qc as q


class TestNQSessionClock(unittest.TestCase):
    def test_winter_and_summer_utc_offset_changes(self):
        winter=q.synthetic_utc_ends("2020-03-06")
        summer=q.synthetic_utc_ends("2020-03-09")
        a=q.verify_rth_end_labels("2020-03-06",winter)
        b=q.verify_rth_end_labels("2020-03-09",summer)
        self.assertEqual(winter[0].hour,14)
        self.assertEqual(summer[0].hour,13)
        self.assertEqual(a["flat_after_index"],118)
        self.assertEqual(b["bars"],390)

    def test_duplicate_missing_and_misaligned_bar_fail(self):
        times=q.synthetic_utc_ends("2021-03-15")
        cases=[
            times[:-1],
            times[:100]+[times[99]]+times[101:],
            times[:30]+[times[30]+timedelta(seconds=30)]+times[31:],
        ]
        for seq in cases:
            with self.assertRaises(ValueError):
                q.verify_rth_end_labels("2021-03-15",seq)

    def test_date_and_utc_type_mismatch_fails(self):
        times=q.synthetic_utc_ends("2021-01-05")
        with self.assertRaises(ValueError):
            q.verify_rth_end_labels("2021-01-06",times)
        wrong=times.copy()
        wrong[0]=wrong[0].replace(tzinfo=None)
        with self.assertRaises(ValueError):
            q.verify_rth_end_labels("2021-01-05",wrong)

    def test_incomplete_early_close_fails_without_fake_fill(self):
        seq=q.synthetic_utc_ends("2021-11-26")[:210]
        with self.assertRaises(ValueError):
            q.verify_rth_end_labels("2021-11-26",seq)

    def test_2023_24_and_sealed_years_fail(self):
        for year in (2023,2024,2025,2026):
            with self.assertRaises(PermissionError):
                q.verify_rth_end_labels(f"{year}-03-15",q.synthetic_utc_ends(f"{year}-03-15"))


if __name__=="__main__":
    unittest.main()
