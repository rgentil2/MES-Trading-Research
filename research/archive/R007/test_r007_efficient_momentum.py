import numpy as np
import pandas as pd

from research.active.R007_EFFICIENT_MOMENTUM.r007_efficient_momentum import (
    EFFICIENCY_MIN,
    ENTRY_CUTOFF_MINUTE,
    START_MINUTE,
    add_momentum_features,
)
from src.research_utils import prepare_rth_features


def test_r007_parameters_and_reference_are_frozen():
    start = pd.Timestamp("2025-01-02 09:31:00", tz="America/New_York").tz_convert("UTC")
    ts = pd.date_range(start, periods=90, freq="min")
    n = len(ts)
    close = 100.0 * np.exp(np.arange(n) * 0.0002)

    df = pd.DataFrame(
        {
            "timestamp_et": ts,
            "open": close,
            "high": close + 0.01,
            "low": close - 0.01,
            "close": close,
            "volume": np.full(n, 100),
            "contract": ["MES 03-25"] * n,
        }
    )

    feat = prepare_rth_features(df, "2025-01-02", "2025-01-02", horizons=[15])
    out = add_momentum_features(feat)

    assert START_MINUTE == 586
    assert ENTRY_CUTOFF_MINUTE == 690
    assert EFFICIENCY_MIN == 0.70
    assert out["abs_r15_threshold"].isna().all()
