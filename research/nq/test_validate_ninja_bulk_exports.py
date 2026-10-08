import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from validate_ninja_bulk_exports import PATTERN,file_qc,audit
class QCTests(unittest.TestCase):
    def test_no_holdout_file_allowed(self):
        self.assertIsNone(PATTERN.fullmatch('NQ_03-26_Minute_Last.txt'))
        self.assertIsNone(PATTERN.fullmatch('MNQ_06-25_Minute_Last.txt'))
    def test_qc_of_tiny_valid_sample_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'NQ_03-24_Minute_Last.txt'
            p.write_text('20240102 143100;17000;17000.25;16999.75;17000;5\n')
            result=file_qc(p)
            self.assertEqual(result['status'],'QC_REVIEW_REQUIRED')
            self.assertEqual(result['bad_rows'],0)
            self.assertEqual(len(audit(Path(d))['missing']),39)
    def test_reject_wrong_price_grid(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'MNQ_12-23_Minute_Last.txt'
            p.write_text('20231201 143100;17000.12;17001;16999;17000;5\n')
            self.assertGreater(file_qc(p)['bad_rows'],0)
    def test_outoforder_and_dups(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'NQ_06-20_Minute_Last.txt'
            p.write_text('20200301 143200;17000;17001;16999;17000;5\n20200301 143200;17000;17001;16999;17000;5\n20200301 143100;17000;17001;16999;17000;5\n')
            r=file_qc(p);self.assertEqual(r['duplicates'],1);self.assertEqual(r['outoforder'],1)
if __name__=='__main__':unittest.main()