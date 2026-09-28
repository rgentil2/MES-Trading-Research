from research.active.B05_VOLATILITY_REGIME_FORECAST.b05_volatility_regime_forecast import (
    ENTRY_CUTOFF,
    HIGH_Q,
    H017_Q,
    LOW_Q,
    REF,
    label_state,
)

def test_b05_frozen_parameters():
    assert REF == 60
    assert LOW_Q == 0.20
    assert HIGH_Q == 0.80
    assert H017_Q == 0.10
    assert ENTRY_CUTOFF == 690
    assert label_state(-1) == "LOW"
    assert label_state(0) == "NORMAL"
    assert label_state(1) == "HIGH"
