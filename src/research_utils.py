from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

DEFAULT_HORIZONS = [5, 10, 15, 30]


def rth_mask(ts_et: pd.Series) -> pd.Series:
    minute = ts_et.dt.hour * 60 + ts_et.dt.minute
    return (minute > 9 * 60 + 30) & (minute <= 16 * 60)


def prepare_rth_features(df, start, end, horizons=DEFAULT_HORIZONS):
    data = df.copy()
    data["timestamp_et"] = pd.to_datetime(data["timestamp_et"], utc=True).dt.tz_convert("America/New_York")
    start_date = pd.Timestamp(start).date()
    end_date = pd.Timestamp(end).date()
    et_date = data["timestamp_et"].dt.date
    data = data.loc[(et_date >= start_date) & (et_date <= end_date) & rth_mask(data["timestamp_et"])].copy()
    data.sort_values("timestamp_et", inplace=True)
    data["session_date"] = data["timestamp_et"].dt.date.astype(str)
    data["group_key"] = data["session_date"] + "|" + data["contract"].astype(str)
    group = data.groupby("group_key", sort=False, observed=True)
    data["bar_index"] = group.cumcount()
    data["year"] = data["timestamp_et"].dt.year
    for h in horizons:
        future_close = group["close"].shift(-h)
        future_ts = group["timestamp_et"].shift(-h)
        exact = (future_ts - data["timestamp_et"]) == pd.Timedelta(minutes=h)
        data[f"exact_{h}m"] = exact.fillna(False)
        data[f"fwd_{h}m"] = np.where(data[f"exact_{h}m"], future_close / data["close"] - 1.0, np.nan)
    return data


def add_forward_extrema(features, horizons=DEFAULT_HORIZONS):
    out = features.reset_index(drop=True).copy()
    n_total = len(out)
    group_indices = out.groupby("group_key", sort=False, observed=True).indices
    for h in horizons:
        future_high = np.full(n_total, np.nan, dtype=float)
        future_low = np.full(n_total, np.nan, dtype=float)
        for idx in group_indices.values():
            pos = np.asarray(idx, dtype=int)
            n = len(pos)
            if n <= h:
                continue
            highs = out.loc[pos, "high"].to_numpy(dtype=float)
            lows = out.loc[pos, "low"].to_numpy(dtype=float)
            high_windows = np.lib.stride_tricks.sliding_window_view(highs[1:], h)
            low_windows = np.lib.stride_tricks.sliding_window_view(lows[1:], h)
            target = pos[: n - h]
            future_high[target] = high_windows.max(axis=1)
            future_low[target] = low_windows.min(axis=1)
        valid = out[f"exact_{h}m"].fillna(False).to_numpy(dtype=bool)
        future_high[~valid] = np.nan
        future_low[~valid] = np.nan
        out[f"future_high_{h}m"] = future_high
        out[f"future_low_{h}m"] = future_low
    return out


def clustered_mean_stats(values, groups):
    frame = pd.DataFrame({"y": values, "g": groups}).dropna()
    if len(frame) < 2 or frame["g"].nunique() < 2:
        return {"clustered_se": np.nan, "t_stat": np.nan, "p_value": np.nan, "ci_low": np.nan, "ci_high": np.nan}
    y = frame["y"].to_numpy(dtype=float)
    x = np.ones((len(frame), 1), dtype=float)
    result = sm.OLS(y, x).fit(cov_type="cluster", cov_kwds={"groups": frame["g"].to_numpy()})
    ci = result.conf_int(alpha=0.05)[0]
    return {"clustered_se": float(result.bse[0]), "t_stat": float(result.tvalues[0]), "p_value": float(result.pvalues[0]), "ci_low": float(ci[0]), "ci_high": float(ci[1])}


def benjamini_hochberg(p_values):
    p = pd.Series(p_values, dtype=float)
    valid = p.notna()
    out = pd.Series(np.nan, index=p.index, dtype=float)
    if not valid.any():
        return out
    pv = p.loc[valid]
    order = np.argsort(pv.to_numpy())
    ranked = pv.to_numpy()[order]
    m = len(ranked)
    adjusted = ranked * m / np.arange(1, m + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    restored = np.empty(m, dtype=float)
    restored[order] = adjusted
    out.loc[pv.index] = restored
    return out
