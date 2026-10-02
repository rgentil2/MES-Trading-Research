from research.archive.R016.r016_h017_price_behavior import (
    REF, RV_Q, R5_Q, START_MINUTE, ENTRY_CUTOFF
)

def test_r016_frozen_parameters():
    assert REF == 60
    assert RV_Q == 0.10
    assert R5_Q == 0.70
    assert START_MINUTE == 601
    assert ENTRY_CUTOFF == 690
