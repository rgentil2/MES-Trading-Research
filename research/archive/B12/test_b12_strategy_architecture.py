from research.archive.B12.b12_strategy_architecture import (
    COMMISSION_RT,
    COST_RT,
    ENTRY_CUTOFF_MINUTE,
    HORIZONS,
    MES_POINT_VALUE,
    PRIMARY_HORIZON,
    PULLBACK_MAX_BARS,
    SLIPPAGE_RT,
)

def test_b12_frozen_parameters():
    assert MES_POINT_VALUE == 5.0
    assert COMMISSION_RT == 1.88
    assert SLIPPAGE_RT == 2.50
    assert COST_RT == 4.38
    assert ENTRY_CUTOFF_MINUTE == 690
    assert PULLBACK_MAX_BARS == 10
    assert PRIMARY_HORIZON == 30
    assert HORIZONS == (15, 30, 60)
