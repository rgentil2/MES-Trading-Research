import unittest
from datetime import date
from pathlib import Path
from nq_b05h01_trade_expansion_month import et_edge
from nq_t59_t60_d0_premarket import IDS,CASE,CONTROL,OTHER,MISSING,classify,segment_stats,month_stage,aggregate

DAY=date(2025,10,1)
def rows(pre=(100,120),regular=(130,115)):
    a,b,c,d=[et_edge(DAY,h,m) for h,m in ((8,30),(9,29),(9,30),(9,44))]
    return [(a,pre[0],1),(a,pre[0],2),(b,pre[1],1),
            (c,regular[0],1),(c,regular[0],2),(d,regular[1],1)]

class T59T60(unittest.TestCase):
    def test_cases_t59_opposition_and_t60_aligned_dislocation(self):
        x=classify(rows(),DAY)
        self.assertEqual(x[IDS[0]],CASE)
        self.assertEqual(x[IDS[1]],CASE)
    def test_t59_control_aligned_rth(self):
        x=classify(rows(pre=(100,120),regular=(125,140)),DAY)
        self.assertEqual(x[IDS[0]],CONTROL)
    def test_T60_opposed_dislocation_control(self):
        x=classify(rows(pre=(100,120),regular=(102,92)),DAY)
        self.assertEqual(x[IDS[0]],CASE)
        self.assertEqual(x[IDS[1]],CONTROL)
    def test_same_timestamp_reordering_cannot_change_decision(self):
        x=rows()
        y=[x[1],x[0],x[2],x[4],x[3],x[5]]
        self.assertEqual(classify(x,DAY),classify(y,DAY))
    def test_missing_context(self):
        self.assertTrue(all(x==MISSING for x in classify([],DAY).values()))
    def test_narrow_premarket_not_falsely_control(self):
        x=classify(rows(pre=(100,103),regular=(104,99)),DAY)
        self.assertEqual(x[IDS[0]],OTHER)
        self.assertEqual(x[IDS[1]],OTHER)
    def test_sealed_month_denied_before_io(self):
        with self.assertRaises(ValueError):month_stage(Path('/DO_NOT_READ'),'2026-09')
    def test_require_all_seven_months(self):
        with self.assertRaises(ValueError):aggregate({})
if __name__=='__main__':unittest.main()
