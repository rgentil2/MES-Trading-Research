from research.active.B06_HIGH_REGIME_STRATEGIES.b06_high_regime_strategies import (
    H017_ACTIVE_MINUTES,
    UPDATE_MINUTE,
)

def test_b06_frozen_timing():
    assert UPDATE_MINUTE == 585
    assert H017_ACTIVE_MINUTES == 30
