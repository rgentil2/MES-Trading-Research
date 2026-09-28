import numpy as np

from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import (
    DYNAMIC_MULTIPLIER,
    H017_NEXT30_MULTIPLIER,
    OPEN15_MULTIPLIER,
    PREOPEN_MULTIPLIER,
    classify_numeric,
    label_numeric,
    support_label,
)

def test_r063_frozen_classification():
    assert classify_numeric(1.0, 2.0, 8.0) == -1
    assert classify_numeric(5.0, 2.0, 8.0) == 0
    assert classify_numeric(9.0, 2.0, 8.0) == 1
    assert np.isnan(classify_numeric(np.nan, 2.0, 8.0))
    assert label_numeric(-1) == "LOW"
    assert label_numeric(0) == "NORMAL"
    assert label_numeric(1) == "HIGH"

def test_r063_support_rule():
    assert support_label("HIGH", 1) == "ALIGNED"
    assert support_label("LOW", -1) == "ALIGNED"
    assert support_label("HIGH", -1) == "CONFLICT"
    assert support_label("LOW", 1) == "CONFLICT"
    assert support_label("NORMAL", 1) == "NEUTRAL"

def test_r063_frozen_calibration_values():
    assert PREOPEN_MULTIPLIER == {"LOW": 0.704, "NORMAL": 0.950, "HIGH": 1.419}
    assert OPEN15_MULTIPLIER == {"LOW": 0.693, "NORMAL": 0.954, "HIGH": 1.438}
    assert DYNAMIC_MULTIPLIER[15]["HIGH"] == 1.5423
    assert DYNAMIC_MULTIPLIER[240]["LOW"] == 0.7455
    assert H017_NEXT30_MULTIPLIER == 0.611
