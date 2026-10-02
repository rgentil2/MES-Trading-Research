import numpy as np
import pandas as pd

from research.archive.R010.r010_prev_day_levels import (
    ENTRY_CUTOFF_MINUTE,
    add_previous_levels,
)
from src.research_utils import prepare_rth_features


def _session(date, contract, base):
    start = pd.Timestamp(
        f"{date} 09:31:00",
        tz="America/New_York",
    ).tz_convert("UTC")
    ts = pd.date_range(start, periods=390, freq="min")
    close = np.full(len(ts), base)
    return pd.DataFrame({
        "timestamp_et": ts,
        "open": close,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": np.full(len(ts), 100),
        "contract": [contract] * len(ts),
    })


def test_previous_levels_require_same_contract():
    raw = pd.concat([
        _session("2025-01-02", "MES 03-25", 100.0),
        _session("2025-01-03", "MES 03-25", 101.0),
        _session("2025-01-06", "MES 06-25", 102.0),
    ], ignore_index=True)

    feat = prepare_rth_features(
        raw,
        "2025-01-02",
        "2025-01-06",
        horizons=[30],
    )
    out = add_previous_levels(feat)

    assert ENTRY_CUTOFF_MINUTE == 690

    jan3 = out[out["session_date"] == "2025-01-03"]
    assert jan3["pdh"].notna().all()
    assert jan3["pdl"].notna().all()

    jan6 = out[out["session_date"] == "2025-01-06"]
    assert jan6["pdh"].isna().all()
    assert jan6["pdl"].isna().all()
