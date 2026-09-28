from research.active.B04_OPENING_MICROSTRUCTURE.b04_opening_microstructure import (
    H038_BODY_MIN,H038_Q,H039_RANGE_Q,H039_WICK_MIN,H040_Q,H041_Q,H042_VOLUME_Q,REF
)
def test_b04_frozen_parameters():
    assert REF==60
    assert H038_Q==0.80
    assert H038_BODY_MIN==0.70
    assert H039_RANGE_Q==0.70
    assert H039_WICK_MIN==0.50
    assert H040_Q==0.80
    assert H041_Q==0.20
    assert H042_VOLUME_Q==0.70
