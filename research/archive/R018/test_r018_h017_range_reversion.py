from research.archive.R018.r018_h017_range_reversion import (
    ACTIVE_MINUTES, COST_RT, EDGE_HIGH, EDGE_LOW, ENTRY_CUTOFF, HORIZON
)

def test_r018_frozen_rules():
    assert ACTIVE_MINUTES == 30
    assert ENTRY_CUTOFF == 690
    assert EDGE_LOW == 0.10
    assert EDGE_HIGH == 0.90
    assert HORIZON == 15
    assert COST_RT == 4.38
