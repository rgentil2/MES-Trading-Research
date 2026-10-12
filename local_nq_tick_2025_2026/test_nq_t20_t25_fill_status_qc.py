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

    def _complete_fake_months(self, allow_missing=True):
        # Synthetic aggregate only; each family labels the same 135 eligible days.
        from collections import Counter
        from nq_t20_t25_fill_status_qc import GROUPS,STATES
        from nq_t20_t25_fixed_anchor_screen import CASE,CONTROL,OTHER,MISSING
        from nq_tick_short_horizon_month import MONTHS
        source=[13,20,22,21,20,22,22]
        eligible=[13,19,21,21,20,21,20]
        self.assertEqual(sum(source),140)
        self.assertEqual(sum(eligible),135)
        left={k:[*SCREEN_COUNTS[k]] for k in IDS}
        months={}
        for m,n_src,n_elig in zip(MONTHS,source,eligible):
            by={}
            for k in IDS:
                n_case=min(n_elig,left[k][0]); left[k][0]-=n_case
                n_ctrl=min(n_elig-n_case,left[k][1]); left[k][1]-=n_ctrl
                n_other=n_elig-n_case-n_ctrl
                # A NO_EVALUABLE label is still an anchored session.
                n_missing=1 if (allow_missing and k==IDS[-1] and n_other>0) else 0
                n_other-=n_missing
                state='NO_TRADE_MODEL_MAGNITUDE' if k==MAG else 'SYNTHETIC_FILL_MODEL_ONLY'
                by[k]={'labels':{CASE:n_case,CONTROL:n_ctrl,OTHER:n_other,MISSING:n_missing},
                       'status_by_group':{g:{s:(n_case if g==CASE else n_ctrl) if s==state else 0 for s in STATES}
                                          for g in GROUPS}}
            months[m]={'status':'T20_T25_FILL_STATUS_DIAGNOSTIC_ONLY',
                       'month':m,'source':n_src,'eligible':n_elig,
                       'by_question':by,**{flag:False for flag in
                         ('PnL_computed_for_reporting','fill_prices_exported',
                          'trade_rows_exported','holdouts_opened',
                          'new_history_acquired','new_5second_signals',
                          'shared_router_reconstructed')}}
        self.assertTrue(all(all(v==0 for v in rem) for rem in left.values()))
        return months

    def test_no_evaluable_labels_may_coexist_with_all_135_anchors(self):
        x=aggregate(self._complete_fake_months(allow_missing=True))
        self.assertEqual((x['source_days'],x['eligible_days']),(140,135))
        self.assertFalse(x['broker_fill_validated'])

    def test_missing_any_stage0_category_count_is_rejected(self):
        from nq_t20_t25_fixed_anchor_screen import OTHER
        months=self._complete_fake_months(allow_missing=False)
        k=IDS[-1]
        last=list(months)[-1]
        self.assertGreater(months[last]['by_question'][k]['labels'][OTHER],0)
        months[last]['by_question'][k]['labels'][OTHER]-=1
        with self.assertRaisesRegex(AssertionError,'135 eligible sessions'):
            aggregate(months)

if __name__=='__main__':unittest.main()
