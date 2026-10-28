"""Independent calendar-only QA of the user-frozen NQ futures roll convention.

The chosen continuous-contract selection rolls on the Thursday exactly eight
calendar days before the third Friday of each quarterly expiry. This was an
intentional research decision; these tests are not a recommendation to
replace it with a vendor/CME convention. No price/trades/holdouts read.
"""
import calendar
import unittest
from datetime import date, timedelta

from research.nq.nq_h05_h07_level_volume_screen import roll_contract

YEARS = (2020, 2021, 2022)
QUARTERS = (3, 6, 9, 12)


def independent_expiry(y: int, m: int) -> date:
    # calendar.monthcalendar is independent of the loader's timedelta algorithm
    fridays = [week[calendar.FRIDAY] for week in calendar.monthcalendar(y, m)
               if week[calendar.FRIDAY]]
    return date(y, m, fridays[2])


def policy_oracle(day: date) -> str:
    # Explicit frozen Thursday-before-expiry rule; no import of loader logic.
    y = day.year
    for q in QUARTERS:
        chosen_switch = independent_expiry(y, q) - timedelta(days=8)
        if day < chosen_switch:
            return f"NQ_{q:02d}-{y % 100:02d}"
    return f"NQ_03-{(y + 1) % 100:02d}"


class TestFrozenNQRollPolicy(unittest.TestCase):
    def test_all_ist_dates_match_independent_calendar(self):
        for year in YEARS:
            d = date(year, 1, 1)
            while d.year == year:
                self.assertEqual(roll_contract(d), policy_oracle(d), str(d))
                d += timedelta(days=1)

    def test_exactly_twelve_quarter_switch_dates_frozen(self):
        switches = []
        for year in YEARS:
            for quarter in QUARTERS:
                expiry = independent_expiry(year, quarter)
                chosen = expiry - timedelta(days=8)
                self.assertEqual(chosen.weekday(), calendar.THURSDAY)
                self.assertNotEqual(roll_contract(chosen - timedelta(days=1)),
                                    roll_contract(chosen))
                # The roll date is the first day of the NEXT quarterly contract.
                following = (quarter + 3) if quarter < 12 else 3
                following_year = year if quarter < 12 else year + 1
                self.assertEqual(roll_contract(chosen),
                                 f"NQ_{following:02d}-{following_year % 100:02d}")
                switches.append(chosen)
        self.assertEqual(len(switches), 12)
        self.assertEqual(len(set(switches)), 12)

    def test_weekends_leap_day_and_new_year_are_deterministic(self):
        for d in (date(2020, 2, 29), date(2020, 12, 31),
                  date(2021, 1, 1), date(2022, 12, 31),
                  date(2021, 3, 14), date(2021, 11, 7)):
            self.assertEqual(roll_contract(d), policy_oracle(d))

    def test_this_is_policy_parity_not_external_roll_validation(self):
        # Never promote this test to independent exchange/broker verification.
        from research.nq import nq_m1_v22_quality_gate as release
        result = release.audit()
        self.assertFalse(result["ready_for_economic_execution"])
        self.assertTrue(any(x["id"] == "DATA_PROVENANCE"
                            for x in result["blocked"]))


if __name__ == "__main__":
    unittest.main()
