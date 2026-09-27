from research.active.R012_LOW_VOL_PERSISTENCE.r012_low_vol_persistence import REF as R012_REF, Q as R012_Q
from research.active.R013_BULL_MOMENTUM.r013_bull_momentum import REF as R013_REF, Q as R013_Q, ER_MIN
from research.active.R014_STREAK_EXHAUSTION.r014_streak_exhaustion import REF as R014_REF, Q as R014_Q
from research.active.R015_PREV_CLOSE_STRENGTH.r015_prev_close_strength import LOW, HIGH

def test_b01_frozen_parameters():
    assert (R012_REF,R012_Q)==(60,0.10)
    assert (R013_REF,R013_Q,ER_MIN)==(60,0.90,0.70)
    assert (R014_REF,R014_Q)==(60,0.80)
    assert (LOW,HIGH)==(0.20,0.80)
