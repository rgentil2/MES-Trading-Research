from research.active.B07_CROSS_SESSION_DIRECTION.b07_cross_session_direction import (
    MAG_Q,
    REF,
)

def test_b07_frozen_parameters():
    assert REF == 60
    assert MAG_Q == 0.60
