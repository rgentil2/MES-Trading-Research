import numpy as np
import pandas as pd

from research.active.R009_OVERNIGHT_GAP.r009_overnight_gap import (
    GAP_QUANTILE,
    REFERENCE_SESSIONS,
    build_session_gaps,
)
from src.research_utils import prepare_rth_features


def _session(date, contract, start_price, drift=0.0):
    start = pd.Timestamp(
        f"{date} 09:31:00",
        tz="America/New_York",
    ).tz_convert("UTC")
    ts = pd.date_range(start, periods=390, freq="min")
    close = start_price + np.arange(len(ts)) * drift
    return pd.DataFrame(
        {
            "timestamp_et": ts,
            "open": close,
            "high": close + 0.25,
            "low": close - 0.25,
            "close": close,
            "volume": np.full(len(ts), 100),
            "contract": [contract] * len(ts),
        }
    )


def test_gap_reference_requires_history_and_same_contract():
    raw = pd.concat(
        [
            _session("2025-01-02", "MES 03-25", 100.0),
            _session("2025-01-03", "MES 03-25", 101.0),
        ],
        ignore_index=True,
    )

    feat = prepare_rth_features(
        raw,
        "2025-01-02",
        "2025-01-03",
        horizons=[30],
    )
    sessions = build_session_gaps(feat)

    assert REFERENCE_SESSIONS == 60
    assert GAP_QUANTILE == 0.70
    assert sessions["gap_threshold"].isna().all()
    assert sessions.loc[
        sessions["session_date"] == "2025-01-03",
        "rth_close",
    ].notna().all()
