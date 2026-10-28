"""NQ source identity guards; synthetic metadata only, no price/PnL."""
import unittest
from pathlib import Path
import tempfile
import zipfile
from research.nq import nq_m1_v23_source_contract_qa as qa

PREFIX="root/development_2020_2024/"

class TestNQISTSourceContractQA(unittest.TestCase):
    def test_real_source_filename_must_match_expected_contract(self):
        member=PREFIX+"NQ_03-21_2021_Minute_Last.txt"
        out=qa.validate_member(member,"2021-02-02")
        self.assertTrue(out["selected"])
        self.assertEqual(out["source_contract"],"NQ_03-21")
        self.assertTrue(out["is_nq"])

    def test_wrong_expiry_visible_in_report_but_not_selected(self):
        member=PREFIX+"NQ_06-21_2021_Minute_Last.txt"
        out=qa.validate_member(member,"2021-02-02")
        self.assertFalse(out["selected"])

    def test_no_2023_24_or_sealed_25_26(self):
        for year in (2023,2024,2025,2026):
            with self.assertRaises(PermissionError):
                qa.validate_member(
                    PREFIX+"NQ_03-21_2021_Minute_Last.txt",
                    f"{year}-01-03")
        with self.assertRaises(PermissionError):
            qa.validate_member(PREFIX+"NQ_03-23_2023_Minute_Last.txt","2023-01-03")

    def test_manifest_only_scans_whitelisted_member_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"archive.zip"
            with zipfile.ZipFile(f,"w") as out:
                for year in (2020,2021,2022):
                    for contract_year,quarter in ((year,3),(year,6),
                                                  (year,9),(year,12),(year+1,3)):
                        name=f"NQ_{quarter:02d}-{contract_year%100:02d}_{year}_Minute_Last.txt"
                        out.writestr(PREFIX+name,"DO_NOT_OPEN_CONTENTS")
                out.writestr("root/holdout_2025/NQ_03-25_2025_Minute_Last.txt","SEALED")
            a=qa.inspect_archive_manifest(f)
            self.assertEqual(a["source_members"],15)
            self.assertEqual(a["allowed_years"],[2020,2021,2022])
            self.assertTrue(a["market_member_contents_opened"] is False)
            self.assertFalse(a["pnl_or_trades_calculated"])
            self.assertEqual(a["holdouts"],"SEALED")

    def test_missing_member_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"broken.zip"
            with zipfile.ZipFile(f,"w") as z:
                z.writestr(PREFIX+"NQ_03-21_2021_Minute_Last.txt","")
            with self.assertRaises(ValueError):
                qa.inspect_archive_manifest(f)

if __name__=="__main__":
    unittest.main()
