import numpy as np
import pandas as pd

from research.archive.R008.r008_opening_drive import (
    DRIVE_QUANTILE,
    REFERENCE_SESSIONS,
    SIGNAL_MINUTE,
    build_opening_drives,
)
from src.research_utils import prepare_rth_features


def test_opening_drive_uses_30_bars_and_prior_reference():
    start = pd.Timestamp("2025-01-02 09:31:00", tz="America/New_York").tz_convert("UTC")
    ts = pd.date_range(start, periods=70, freq="min")
    close = 100.0 + np.arange(len(ts)) * 0.01
    df = pd.DataFrame({
        "timestamp_et": ts,
        "open": close - 0.005,
        "high": close + 0.02,
        "low": close - 0.02,
        "close": close,
        "volume": np.full(len(ts), 100),
        "contract": ["MES 03-25"] * len(ts),
    })

    feat = prepare_rth_features(df, "2025-01-02", "2025-01-02", horizons=[30])
    drives = build_opening_drives(feat)

    assert REFERENCE_SESSIONS == 60
    assert DRIVE_QUANTILE == 0.70
    assert SIGNAL_MINUTE == 600
    assert len(drives) == 1
    assert drives["drive_threshold"].isna().all()
