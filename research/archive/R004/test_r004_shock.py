import numpy as np
import pandas as pd

from research.archive.R001.r001_vwap_analysis import prepare_features
from research.archive.R004.r004_shock_reversion import add_shock_features


def test_shock_z_requires_exact_60m_history():
    timestamps = pd.date_range(
        "2026-01-05 14:31:00+00:00",
        periods=80,
        freq="min",
    )
    close = 100.0 * np.exp(np.arange(len(timestamps)) * 0.0001)
    df = pd.DataFrame(
        {
            "timestamp_et": timestamps,
            "open": close,
            "high": close + 0.01,
            "low": close - 0.01,
            "close": close,
            "volume": np.full(len(timestamps), 100),
            "contract": ["MES 03-26"] * len(timestamps),
        }
    )
    features = prepare_features(df, "2026-01-05", "2026-01-05")
    out = add_shock_features(features)

    assert out.iloc[59]["exact_history_60m"] == False
    assert out.iloc[60]["exact_history_60m"] == True
    assert pd.notna(out.iloc[60]["shock_z"])
