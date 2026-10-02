import pandas as pd

from research.archive.R001.r001_vwap_analysis import prepare_features, rth_mask


def test_rth_mask_uses_ninjatrader_end_of_bar_timestamps():
    ts = pd.Series(pd.to_datetime([
        "2026-01-05 09:30:00-05:00",
        "2026-01-05 09:31:00-05:00",
        "2026-01-05 16:00:00-05:00",
        "2026-01-05 16:01:00-05:00",
    ]))
    assert rth_mask(ts).tolist() == [False, True, True, False]


def _frame(timestamps):
    return pd.DataFrame({
        "timestamp_et": pd.to_datetime(timestamps, utc=True),
        "open": [5000.0] * len(timestamps),
        "high": [5000.25] * len(timestamps),
        "low": [4999.75] * len(timestamps),
        "close": [5000.0 + i * 0.25 for i in range(len(timestamps))],
        "volume": [10] * len(timestamps),
        "contract": ["MES 03-26"] * len(timestamps),
    })


def test_forward_returns_require_exact_elapsed_minutes():
    continuous = _frame([
        "2026-01-05 14:31:00+00:00",
        "2026-01-05 14:32:00+00:00",
        "2026-01-05 14:33:00+00:00",
        "2026-01-05 14:34:00+00:00",
        "2026-01-05 14:35:00+00:00",
        "2026-01-05 14:36:00+00:00",
    ])
    feat = prepare_features(continuous, "2026-01-05", "2026-01-05")
    assert bool(feat.iloc[0]["exact_5m"]) is True
    assert pd.notna(feat.iloc[0]["fwd_5m"])

    with_gap = _frame([
        "2026-01-05 14:31:00+00:00",
        "2026-01-05 14:32:00+00:00",
        "2026-01-05 14:33:00+00:00",
        "2026-01-05 14:34:00+00:00",
        "2026-01-05 14:36:00+00:00",
        "2026-01-05 14:37:00+00:00",
    ])
    feat_gap = prepare_features(with_gap, "2026-01-05", "2026-01-05")
    assert bool(feat_gap.iloc[0]["exact_5m"]) is False
    assert pd.isna(feat_gap.iloc[0]["fwd_5m"])
