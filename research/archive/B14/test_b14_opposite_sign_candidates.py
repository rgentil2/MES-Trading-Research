from research.archive.B14.b14_opposite_sign_candidates import (
    STRESS_COST_RT,
)
from research.archive.B12.b12_strategy_architecture import COST_RT

def test_b14_frozen_cost_stress():
    assert COST_RT == 4.38
    assert round(STRESS_COST_RT, 2) == 6.57
