import numpy as np
import pandas as pd

from research.active.R011_VOLUME_IMPULSE.r011_volume_impulse import (
    EFFICIENCY_MIN,
    ENTRY_CUTOFF_MINUTE,
    START_MINUTE,
    VOLUME_QUANTILE,
    add_impulse_features,
)
from src.research_utils import prepare_rth_features


def test_r011_parameters_and_no_self_reference():
    start = pd.Timestamp(
        "2025-01-02 09:31:00",
        tz="America/New_York",
    ).tz_convert("UTC")
    ts = pd.date_range(start, periods=90, freq="min")
    n = len(ts)
    close = 100.0 * np.exp(np.arange(n) * 0.0001)

    df = pd.DataFrame({
        "timestamp_et": ts,
        "open": close,
        "high": close + 0.01,
        "low": close - 0.01,
        "close": close,
        "volume": np.arange(n) + 100,
        "contract": ["MES 03-25"] * n,
    })

    feat = prepare_rth_features(
        df,
        "2025-01-02",
        "2025-01-02",
        horizons=[15],
    )
    out = add_impulse_features(feat)

    assert START_MINUTE == 576
    assert ENTRY_CUTOFF_MINUTE == 690
    assert VOLUME_QUANTILE == 0.80
    assert EFFICIENCY_MIN == 0.70
    assert out["v5_threshold"].isna().all()
