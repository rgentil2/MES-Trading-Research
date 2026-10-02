from research.archive.B10.b10_regime_decay import (
    ANCHOR_BLOCKS,
    HIGH_Q,
    LOW_Q,
    MAX_FUTURE_BLOCK,
    PRACTICAL_THRESHOLD_PCT,
    REF,
)

def test_b10_frozen_parameters():
    assert REF == 60
    assert LOW_Q == 0.20
    assert HIGH_Q == 0.80
    assert ANCHOR_BLOCKS == tuple(range(0, 8))
    assert MAX_FUTURE_BLOCK == 8
    assert PRACTICAL_THRESHOLD_PCT == 10.0
