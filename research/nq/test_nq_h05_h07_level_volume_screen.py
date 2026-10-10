import importlib.util
import unittest
from pathlib import Path
from datetime import date
from unittest.mock import patch
import io
import zipfile
import tempfile
import numpy as np

SCRIPT=Path(__file__).with_name('nq_h05_h07_level_volume_screen.py')
spec=importlib.util.spec_from_file_location('nq_level_screen',SCRIPT)
screen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)

class LevelTests(unittest.TestCase):
    def test_stage_firewall(self):
        self.assertTrue(screen.permitted_name('research/development_2020_2024/NQ_03-25_2024_Minute_Last.txt'))
        self.assertFalse(screen.permitted_name('research/validation_holdout_2025/NQ_03-25_2025_Minute_Last.txt'))
        self.assertFalse(screen.permitted_name('research/pseudo_forward_holdout_2026/NQ_03-26_2026_Minute_Last.txt'))
        self.assertFalse(screen.permitted_name('research/development_2020_2024/NQ_03-25_2025_Minute_Last.txt'))

    def test_holdout_member_never_opened(self):
        # A sealed holdout with deliberately invalid bytes is never opened even
        # when the development loader is invoked and rejects incomplete sources.
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'source.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('research/validation_holdout_2025/NQ_06-25_2025_Minute_Last.txt',b'RESTRICTED')
                z.writestr('research/pseudo_forward_holdout_2026/NQ_09-26_2026_Minute_Last.txt',b'RESTRICTED')
                z.writestr('research/development_2020_2024/NQ_03-20_2020_Minute_Last.txt','20200102 143100;1;1;1;1;1\n')
            with self.assertRaisesRegex(ValueError,'25 NQ development files required'):
                screen.load_development(p)

    def test_rollover_dates(self):
        self.assertEqual(screen.roll_contract(date(2020,3,11)),'NQ_03-20')
        self.assertEqual(screen.roll_contract(date(2020,3,12)),'NQ_06-20')
        self.assertEqual(screen.roll_contract(date(2024,12,12)),'NQ_03-25')

    def test_h05_causal_sweep(self):
        self.assertEqual(screen.choose_h05(np.array([100,111.25,104,109,20]),111,90),-1)
        self.assertEqual(screen.choose_h05(np.array([100,105,89.75,92,20]),111,90),1)
        self.assertEqual(screen.choose_h05(np.array([100,112,89,100,20]),111,90),0)
        self.assertIsNone(screen.choose_h05(np.array([100,110,94,103,20]),111,90))

    def test_h06_volume_confirmation(self):
        a=np.zeros((390,5));a[:,3]=99
        a[16,3]=101;a[17,3]=102;a[17,4]=30
        self.assertEqual(screen.choose_h06(a,17,100,80,20),1)
        self.assertIsNone(screen.choose_h06(a,17,100,80,25))
        a[16,3]=99
        self.assertIsNone(screen.choose_h06(a,17,100,80,20))

    def test_h07_first_breach_consumes_day_and_window(self):
        a=np.column_stack([np.ones(390)*100]*5)
        a[:,1]=105;a[:,2]=95;a[:,3]=100
        a[15,1]=110.25; a[15,3]=111;a[16,3]=109
        self.assertEqual(screen.choose_h07(a,110,90),(16,-1))
        a[0,1]=110.25
        self.assertIsNone(screen.choose_h07(a,110,90))
        a[0,1]=105;a[15,1]=110.25;a[15:19,3]=111
        self.assertIsNone(screen.choose_h07(a,110,90))

    def test_friction_and_bh(self):
        self.assertAlmostEqual(screen.FRICTION,25.74)
        q=screen.bh({'H05':0.01,'H06':0.04,'H07':0.8})
        self.assertEqual(q['H05'],0.03)
        self.assertEqual(q['H06'],0.06)
        self.assertEqual(q['H07'],0.8)

if __name__=='__main__':unittest.main()