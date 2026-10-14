from datetime import date, timedelta
from pathlib import Path
import sys
import unittest
import numpy as np

# Works both via `unittest discover` from repository root and locally.
BUILDER_ROOT = Path(__file__).resolve().parents[1]
if str(BUILDER_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILDER_ROOT))

from engine import (FAMILIES,FEATURES,build_registry,indicators,directional_signal,
                    filter_mask,_exit,metrics,analyze,trade_for_day)


def synthetic_day(seed=42):
    # Synthetic random price path on tick grid; only testing software mechanics.
    rng=np.random.default_rng(seed)
    changes=rng.choice([-2,-1,0,1,2],size=390)*.25
    close=15000.+np.cumsum(changes)
    open_=np.r_[close[0],close[:-1]]
    high=np.maximum(close,open_)+rng.choice([0,.25,.5],size=390)
    low=np.minimum(close,open_)-rng.choice([0,.25,.5],size=390)
    vol=rng.integers(10,150,size=390)
    return np.column_stack((open_,high,low,close,vol))


class BuilderTests(unittest.TestCase):
    def test_cohort_frozen(self):
        a=build_registry();b=build_registry()
        self.assertEqual(len(a),48)
        self.assertEqual([x.digest() for x in a],[x.digest() for x in b])
        self.assertEqual(len(set(x.id for x in a)),48)
        self.assertEqual(set(x.mechanism for x in a),set(FAMILIES))
        self.assertGreaterEqual(len(FEATURES),15)

    def test_feature_no_future_leak(self):
        day=synthetic_day()
        f=indicators(day)
        altered=day.copy()
        altered[201:,:4] += 100
        g=indicators(altered)
        for col in f.columns:
            np.testing.assert_allclose(f[col].to_numpy()[:200],g[col].to_numpy()[:200],equal_nan=True,err_msg=col)

    def test_all_families_emit_valid_signals(self):
        f=indicators(synthetic_day())
        for fam in FAMILIES:
            s=directional_signal(f,fam)
            self.assertTrue(set(s.tolist()).issubset({-1,0,1}),fam)
        for name in ('volume_confirm','adx_confirm','regime_quiet'):
            self.assertEqual(filter_mask(f,name).dtype,np.dtype(bool))

    def test_stop_first_in_ambiguous_bar(self):
        day=synthetic_day()
        day[52,:]=[100.,103.,97.,100.,40.]
        px,j,reason,mae=_exit(day,52,1,100.,2.,2.,1)
        self.assertEqual(reason,'AMBIGUOUS_STOP_FIRST')
        self.assertAlmostEqual(px,97.5)
        self.assertGreaterEqual(mae,3)

    def test_both_gates_prevent_2025_2026(self):
        day=synthetic_day()
        with self.assertRaisesRegex(ValueError,'SEALED'):
            analyze(np.stack([day]),['2025-06-01'],build_registry()[:1],replications=100)
        with self.assertRaisesRegex(ValueError,'SEALED'):
            analyze(np.stack([day]),['2026-01-01'],build_registry()[:1],replications=100)

    def test_no_execution_same_bar(self):
        day=synthetic_day()
        record=trade_for_day(day,'2022-01-04',build_registry()[0])
        if record:self.assertEqual(record['entry_i'],record['signal_i']+1)

    def test_toy_pipeline_no_edge_claims(self):
        days=np.stack([synthetic_day(i) for i in range(8)])
        dates=['2020-01-02','2020-01-03','2020-01-06','2021-01-04',
               '2022-01-04','2023-01-04','2024-01-04','2024-01-05']
        report,trades=analyze(days,dates,build_registry()[:2],replications=100)
        self.assertEqual(report['n_candidates'],2)
        self.assertEqual(report['status'],'REUSED_DEV_EXPLORATORY_NOT_INDEPENDENT_VALIDATION')
        self.assertFalse(any(x['gate']=='VALIDATED' for x in report['candidates']))
        self.assertEqual(report['date_windows']['validation_2025'],'SEALED')

if __name__=='__main__':unittest.main()
