from research.active.B03_PREVIOUS_DAY.b03_previous_day import (
    LATE_Q, NARROW_Q, REF, TREND_EFF_MIN, TREND_Q, VWAP_Q, WIDE_Q
)

def test_b03_frozen_parameters():
    assert REF==60
    assert NARROW_Q==0.20
    assert WIDE_Q==0.80
    assert TREND_Q==0.75
    assert TREND_EFF_MIN==0.35
    assert LATE_Q==0.80
    assert VWAP_Q==0.80
