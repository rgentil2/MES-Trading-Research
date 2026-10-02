import numpy as np
import pandas as pd

from research.archive.R001.r001_vwap_analysis import add_forward_extrema, prepare_features
from research.archive.R003.r003_orb_behavior import build_opening_range_events


def test_first_close_outside_15m_opening_range_is_event():
    timestamps = pd.date_range(
        "2026-01-05 14:31:00+00:00",
        periods=50,
        freq="min",
    )
    n = len(timestamps)
    close = np.full(n, 100.0)
    high = np.full(n, 100.5)
    low = np.full(n, 99.5)

    # 09:46 ET is index 15. First closing breakout is upward.
    close[15:] = 101.25
    high[15:] = 101.5
    low[15:] = 100.75

    df = pd.DataFrame(
        {
            "timestamp_et": timestamps,
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.full(n, 100),
            "contract": ["MES 03-26"] * n,
        }
    )

    features = prepare_features(df, "2026-01-05", "2026-01-05")
    features = add_forward_extrema(features)
    events = build_opening_range_events(features)

    assert len(events) == 1
    assert events.iloc[0]["breakout"] == "UPPER"
    ts = pd.Timestamp(events.iloc[0]["timestamp_et"])
    assert ts.hour == 9 and ts.minute == 46
