from research.archive.B09.b09_regime_persistence import (
    ANCHOR_BLOCKS,
    HIGH_Q,
    LOW_Q,
    MAX_FUTURE_BLOCK,
    REF,
)

def test_b09_frozen_parameters():
    assert REF == 60
    assert LOW_Q == 0.20
    assert HIGH_Q == 0.80
    assert ANCHOR_BLOCKS == tuple(range(0, 8))
    assert MAX_FUTURE_BLOCK == 4
