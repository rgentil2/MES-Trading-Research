import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone
from qc_tick_day import check_day, parse_row, utc_bounds, audit

class TestNQTickQC(unittest.TestCase):
    def test_new_scope(self):
        self.assertEqual(str(check_day("2025-10-15")), "2025-10-15")
        self.assertEqual(str(check_day("2026-06-30")), "2026-06-30")

    def test_sealed_dates(self):
        for day in ("2026-07-01", "2026-08-11", "2026-09-30"):
            with self.assertRaises(ValueError):
                check_day(day)

    def test_subsecond(self):
        a = parse_row("20251015 120000 0000000;25000.25;1")
        b = parse_row("20251015 120000 0000001;25000.25;1")
        self.assertEqual(b[0]-a[0], 1)

    def test_elapsed_time(self):
        a = parse_row("20251015 125959;25000.25;1")
        b = parse_row("20251015 130000;25000.25;1")
        self.assertEqual(b[0]-a[0], 10000000)

    def test_timezone(self):
        x, _ = utc_bounds(check_day("2025-10-15"))
        y, _ = utc_bounds(check_day("2026-01-15"))
        self.assertEqual(datetime.fromtimestamp(x/1e7,timezone.utc).hour, 12)
        self.assertEqual(datetime.fromtimestamp(y/1e7,timezone.utc).hour, 13)

if __name__ == "__main__":
    unittest.main()
