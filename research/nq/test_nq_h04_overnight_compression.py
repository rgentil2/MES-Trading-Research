"""Source-only tests for preregistered NQ-H04; no historical holdout content."""
import importlib.util
import sys
import unittest
import tempfile
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
SRC=HERE/'nq_h04_overnight_compression_2020_2024.py'
spec=importlib.util.spec_from_file_location('nq_h04_module',SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class FixedH04Tests(unittest.TestCase):
    def test_quarterly_rollovers(self):
        self.assertEqual(m.roll_contract(date(2024,3,6)),'NQ_03-24')
        self.assertEqual(m.roll_contract(date(2024,3,7)),'NQ_06-24')
        self.assertEqual(m.roll_contract(date(2024,12,11)),'NQ_12-24')
        self.assertEqual(m.roll_contract(date(2024,12,12)),'NQ_03-25')

    def test_bh_adjustment(self):
        q=m.bh_fdr({'a':.01,'b':.03,'c':.3,'d':.8})
        self.assertEqual(q['a'],.04)
        self.assertEqual(q['b'],.06)
        self.assertEqual(q['c'],.4)
        self.assertEqual(q['d'],.8)

    def test_never_open_holdout_zip_members(self):
        with tempfile.TemporaryDirectory() as d:
            fn=Path(d)/'source.zip'
            with zipfile.ZipFile(fn,'w') as z:
                for symbol in ['NQ']:
                    for y in range(2020,2025):
                        for month in (3,6,9,12):
                            name=f'NQ_{month:02d}-{y%100:02d}_{y}_Minute_Last.txt'
                            z.writestr('root/development_2020_2024/'+name,
                                       f'{y}0102 143100;12000;12000.25;11999.75;12000;100\n')
                        name=f'NQ_03-{(y+1)%100:02d}_{y}_Minute_Last.txt'
                        z.writestr('root/development_2020_2024/'+name,
                                   f'{y}1215 143100;12000;12000.25;11999.75;12000;100\n')
                z.writestr('root/validation_holdout_2025/NQ_03-25_2025_Minute_Last.txt',b'SEALED HOLDOUT 2025')
                z.writestr('root/pseudo_forward_holdout_2026/NQ_03-26_2026_Minute_Last.txt',b'SEALED HOLDOUT 2026')
            original=zipfile.ZipFile.open
            opened=[]
            def audit_open(self,name,*a,**k):
                opened.append(str(name))
                if 'holdout_' in str(name):
                    raise AssertionError('HOLDOUT OPENED')
                return original(self,name,*a,**k)
            with patch.object(zipfile.ZipFile,'open',audit_open):
                with self.assertRaisesRegex(ValueError,'No permitted data'):
                    m.read_selected(fn)
            self.assertEqual(len(opened),25)
            self.assertTrue(all('development_2020_2024' in name for name in opened))

if __name__=='__main__':unittest.main()