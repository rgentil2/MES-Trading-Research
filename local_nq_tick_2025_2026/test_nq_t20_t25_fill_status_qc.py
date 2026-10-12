import unittest
from pathlib import Path
from nq_t20_t25_fill_status_qc import STATES,month_stage,aggregate,IDS,MAG
from nq_t20_t25_economic_month import SCREEN_COUNTS

class LastStatusQC(unittest.TestCase):
    def test_exact_whitelisted_simulator_states(self):
        self.assertIn('ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS',STATES)
        self.assertIn('UNRESOLVED_END_OF_LAST_DATA',STATES)
        self.assertIn('CONTROL_WITHOUT_DIRECTION',STATES)
        self.assertEqual(len(STATES),7)
    def test_six_questions_magnitude_is_not_directional_trade(self):
        self.assertEqual(len(IDS),6)
        self.assertIn(MAG,IDS)
        self.assertEqual(SCREEN_COUNTS[MAG],(1,8))
    def test_sealed_month_denied_before_filesystem(self):
        with self.assertRaises(ValueError):
            month_stage(Path('/DO_NOT_TOUCH'),'2026-08')
    def test_missing_months_denied_before_aggregate(self):
        with self.assertRaises(ValueError):
            aggregate({})
    def test_no_cherry_pick_months_ever(self):
        with self.assertRaises(ValueError):
            aggregate({'2026-01':{'status':'fake'}})

if __name__=='__main__':unittest.main()
