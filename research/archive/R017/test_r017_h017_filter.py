import numpy as np
import pandas as pd

from research.archive.R017.r017_h017_filter import (
    COST_RT, ENTRY_CUTOFF, H017_ACTIVE_MINUTES, MES_POINT_VALUE, perf
)

def test_r017_frozen_costs_and_window():
    assert ENTRY_CUTOFF == 690
    assert H017_ACTIVE_MINUTES == 30
    assert MES_POINT_VALUE == 5.0
    assert COST_RT == 4.38

def test_perf_drawdown_and_expectancy():
    d=pd.DataFrame({
        "timestamp_et":pd.date_range("2025-01-01",periods=3,freq="D",tz="UTC"),
        "net_pnl_usd":[10.0,-20.0,5.0],
    })
    r=perf(d)
    assert r["trades"]==3
    assert np.isclose(r["expectancy_usd"],-5/3)
    assert np.isclose(r["max_drawdown_usd"],20.0)
