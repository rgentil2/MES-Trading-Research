from research.active.B02_OVERNIGHT.b02_overnight import (
    ENTRY_CUTOFF,
    H028_Q,
    H030_Q,
    H032_EFFICIENCY_MIN,
    H032_Q,
    REF,
)

def test_b02_frozen_parameters():
    assert REF == 60
    assert H028_Q == 0.80
    assert H030_Q == 0.20
    assert H032_Q == 0.70
    assert H032_EFFICIENCY_MIN == 0.60
    assert ENTRY_CUTOFF == 690
