from __future__ import annotations

import numpy as np
import pandas as pd


def summarize_returns(series: pd.Series) -> dict:
    """Return basic descriptive statistics for a return series."""
    clean = pd.Series(series).dropna()
    if clean.empty:
        return {
            "n": 0,
            "mean": np.nan,
            "median": np.nan,
            "std": np.nan,
            "win_rate": np.nan,
        }

    return {
        "n": int(clean.size),
        "mean": float(clean.mean()),
        "median": float(clean.median()),
        "std": float(clean.std(ddof=1)),
        "win_rate": float((clean > 0).mean()),
    }
