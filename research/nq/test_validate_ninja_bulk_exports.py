import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from validate_ninja_bulk_exports import PATTERN,file_qc,audit,holdout_inventory_metadata_only

class QCTests(unittest.TestCase):
    def test_dev_year_partition_and_holdout_rejection(self):
        self.assertIsNotNone(PATTERN.fullmatch('NQ_03-25_2024_Minute_Last.txt'))
        self.assertIsNone(PATTERN.fullmatch('NQ_03-25_2025_Minute_Last.txt'))
        self.assertIsNone(PATTERN.fullmatch('MNQ_06-26_2026_Minute_Last.txt'))

    def test_tiny_valid_development_sample_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'NQ_03-24_2024_Minute_Last.txt'
            p.write_text('20240102 143100;17000;17000.25;16999.75;17000;5\n')
            result=file_qc(p)
            self.assertEqual(result['status'],'QC_REVIEW_REQUIRED')
            self.assertEqual(result['bad_rows'],0)
            self.assertEqual(len(audit(Path(d))['missing']),49)

    def test_reject_wrong_price_grid(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'MNQ_12-23_2023_Minute_Last.txt'
            p.write_text('20231201 143100;17000.12;17001;16999;17000;5\n')
            self.assertGreater(file_qc(p)['bad_rows'],0)

    def test_outoforder_and_dups(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'NQ_06-20_2020_Minute_Last.txt'
            p.write_text('20200301 143200;17000;17001;16999;17000;5\n20200301 143200;17000;17001;16999;17000;5\n20200301 143100;17000;17001;16999;17000;5\n')
            result=file_qc(p)
            self.assertEqual(result['duplicates'],1)
            self.assertEqual(result['outoforder'],1)

    def test_holdout_price_content_never_read(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            dev=root/'development_2020_2024'
            held=root/'validation_holdout_2025'
            fwd=root/'pseudo_forward_holdout_2026'
            dev.mkdir();held.mkdir();fwd.mkdir()
            (dev/'NQ_03-24_2024_Minute_Last.txt').write_text('20240102 143100;17000;17000.25;16999.75;17000;5\n')
            (held/'NQ_03-25_2025_Minute_Last.txt').write_bytes(b'INTENTIONALLY INVALID SECRET 2025 OUTCOME')
            (fwd/'NQ_12-26_2026_Minute_Last.txt').write_bytes(b'INTENTIONALLY INVALID SECRET 2026 OUTCOME')
            report=audit(root)
            self.assertEqual(report['received'],1)
            self.assertEqual(report['expected_contract_partitions'],50)
            inventory=holdout_inventory_metadata_only(root)
            self.assertEqual(inventory['validation_holdout_2025'][0]['bytes'],len(b'INTENTIONALLY INVALID SECRET 2025 OUTCOME'))
            self.assertEqual(inventory['pseudo_forward_holdout_2026'][0]['file'],'NQ_12-26_2026_Minute_Last.txt')

if __name__=='__main__':unittest.main()
