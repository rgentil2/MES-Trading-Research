from research.active.B08_MULTI_DAY_CONTEXT.b08_multi_day_context import (
    HIGH_RANGE_Q,LOW_RANGE_Q,OVEREXT_Q,REF,STREAK_Q
)

def test_b08_frozen_parameters():
    assert REF==60
    assert STREAK_Q==0.60
    assert OVEREXT_Q==0.80
    assert HIGH_RANGE_Q==0.80
    assert LOW_RANGE_Q==0.20
