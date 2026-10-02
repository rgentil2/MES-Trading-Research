import numpy as np
import pandas as pd

from research.archive.R006.r006_vol_compression import (
    ENTRY_CUTOFF_MINUTE,
    START_MINUTE,
    add_volatility_features,
)
from src.research_utils import prepare_rth_features


def test_r006_window_and_no_lookahead_reference():
    start = pd.Timestamp("2025-01-02 09:31:00", tz="America/New_York").tz_convert("UTC")
    ts = pd.date_range(start, periods=90, freq="min")
    n = len(ts)
    close = 100.0 * np.exp(np.arange(n) * 0.0001)

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

    feat = prepare_rth_features(df, "2025-01-02", "2025-01-02", horizons=[30])
    out = add_volatility_features(feat)

    assert START_MINUTE == 601
    assert ENTRY_CUTOFF_MINUTE == 690
    # One session cannot create its own 60-session historical reference.
    assert out["compression_threshold_bps"].isna().all()
