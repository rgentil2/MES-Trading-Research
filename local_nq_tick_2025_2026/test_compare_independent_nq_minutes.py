import unittest
from datetime import datetime,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from qc_tick_day import check_day,utc_bounds
from compare_independent_nq_minutes import compare_events,source_paths,iter_minute_file
from qc_tick_to_minutes import MINUTE_100NS

DAY="2025-10-15"
T=utc_bounds(check_day(DAY))[0]

def full_day(offset=MINUTE_100NS):
    ticks=[(T+i*MINUTE_100NS+3,400+i,2) for i in range(240)]
    minutes=[(T+i*MINUTE_100NS+offset,(400+i,400+i,400+i,400+i,2)) for i in range(240)]
    return ticks,minutes

class TestIndependentMinuteQC(unittest.TestCase):
    def test_end_label_full_240_matches(self):
        a,b=full_day()
        r=compare_events(a,b,DAY,"end")
        self.assertEqual(r["status"],"INDEPENDENT_MINUTE_MATCH")
        self.assertEqual(r["minutes_compared"],240)
        self.assertTrue(r["verified_fully_240_minutes"])
        self.assertFalse(r["raw_prices_emitted"])
    def test_start_label_when_explicitly_requested(self):
        a,b=full_day(offset=0)
        self.assertEqual(compare_events(a,b,DAY,"start")["status"],"INDEPENDENT_MINUTE_MATCH")
    def test_wrong_clock_convention_fails_closed(self):
        a,b=full_day()
        with self.assertRaises(ValueError):
            compare_events(a,b,DAY,"start")
    def test_price_mismatch_is_aggregate_only(self):
        a,b=full_day()
        stamp,x=b[42];b[42]=(stamp,(x[0]+1,x[1]+1,x[2]+1,x[3]+1,x[4]))
        r=compare_events(a,b,DAY,"end")
        self.assertEqual(r["difference_minutes_by_field"]["close"],1)
        self.assertEqual(r["maximum_abs_difference_ticks_or_contracts"]["close"],1)
        self.assertNotIn("400",str(r))
        self.assertEqual(r["status"],"SOURCE_MISMATCH_OR_INCOMPLETE")
    def test_volume_mismatch(self):
        a,b=full_day();stamp,x=b[0];b[0]=(stamp,(*x[:4],3))
        r=compare_events(a,b,DAY,"end")
        self.assertEqual(r["difference_minutes_by_field"]["volume"],1)
    def test_missing_independent_minute_is_not_pass(self):
        a,b=full_day();b.pop()
        r=compare_events(a,b,DAY,"end")
        self.assertFalse(r["verified_fully_240_minutes"])
    def test_extra_tick_out_of_session(self):
        a,b=full_day();a.append((T+240*MINUTE_100NS,401,1))
        with self.assertRaises(ValueError):
            compare_events(a,b,DAY,"end")
    def test_sealed_date_no_iterator_access(self):
        class Bomb:
            def __iter__(self):raise AssertionError("sealed data iterated")
        with self.assertRaises(ValueError):
            compare_events(Bomb(),Bomb(),"2026-07-01","end")
    def test_wrong_file_contract_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"Tick_Last").mkdir();(root/"Minute_Last").mkdir()
            (root/"Tick_Last"/"NQ_12-25_2025_20251015_Tick_Last_ET0800_1200.txt").touch()
            (root/"Minute_Last"/"NQ_03-26_2025_20251015_Minute_Last_ET0800_1200.txt").touch()
            with self.assertRaises(ValueError):
                source_paths(root,DAY)
    def test_minute_parse_original_nt_export(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"NQ_12-25_2025_20251015_Minute_Last_ET0800_1200.txt"
            p.write_text("20251015 120100;25100.25;25101;25100;25100.5;132\n")
            d=list(iter_minute_file(p))
            self.assertEqual(len(d),1)
            self.assertEqual(d[0][1][0],100401)
            self.assertEqual(d[0][1][4],132)
    def test_daylight_saving_et_window(self):
        from datetime import date
        a=utc_bounds(date(2026,3,9))[0]
        self.assertEqual(datetime.fromtimestamp(a/10000000,timezone.utc).hour,12)
if __name__=="__main__":unittest.main()
