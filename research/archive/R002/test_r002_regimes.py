import pandas as pd

from research.archive.R002.r002_vwap_regimes import (
    assign_volatility_regime,
    benjamini_hochberg,
)


def test_benjamini_hochberg_is_monotone_in_rank():
    p = pd.Series([0.01, 0.04])
    q = benjamini_hochberg(p)
    assert q.iloc[0] == 0.02
    assert q.iloc[1] == 0.04


def test_volatility_regime_uses_frozen_cutoffs():
    df = pd.DataFrame({"rv30_bps": [5.0, 10.0, 15.0]})
    out = assign_volatility_regime(df, q1=7.5, q2=12.5)
    assert out["vol_regime"].tolist() == ["LOW", "MID", "HIGH"]
