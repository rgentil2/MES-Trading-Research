from research.active.B13_HIGH_DIRECTIONAL_TRIGGERS.b13_high_directional_triggers import (
    BODY_RATIO_MIN,
    CLV_LOWER,
    CLV_UPPER,
    VWAP_Q,
    VWAP_REF,
    WICK_MIN,
)

def test_b13_frozen_parameters():
    assert BODY_RATIO_MIN == 0.60
    assert CLV_UPPER == 0.80
    assert CLV_LOWER == 0.20
    assert VWAP_Q == 0.60
    assert VWAP_REF == 60
    assert WICK_MIN == 0.50
