from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

THRESHOLDS = [1.5, 1.75, 2.0, 2.25, 2.5]
HORIZONS = [5, 10, 15, 30]


def rth_mask(ts_et: pd.Series) -> pd.Series:
    # NinjaTrader exports minute bars with END-OF-BAR timestamps.
    # 09:31 ET contains trades from 09:30:00-09:30:59; 16:00 contains
    # trades from 15:59:00-15:59:59.
    minute = ts_et.dt.hour * 60 + ts_et.dt.minute
    return (minute > 9 * 60 + 30) & (minute <= 16 * 60)


def prepare_features(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    data = df.copy()
    data["timestamp_et"] = pd.to_datetime(data["timestamp_et"], utc=True).dt.tz_convert(
        "America/New_York"
    )
    start_date = pd.Timestamp(start).date()
    end_date = pd.Timestamp(end).date()
    et_date = data["timestamp_et"].dt.date
    data = data.loc[(et_date >= start_date) & (et_date <= end_date) & rth_mask(data["timestamp_et"])].copy()
    data.sort_values("timestamp_et", inplace=True)

    data["session_date"] = data["timestamp_et"].dt.date.astype(str)
    data["group_key"] = data["session_date"] + "|" + data["contract"].astype(str)
    group = data.groupby("group_key", sort=False, observed=True)
    data["bar_index"] = group.cumcount()

    typical = (data["high"] + data["low"] + data["close"]) / 3.0
    pv = typical * data["volume"]
    p2v = typical.pow(2) * data["volume"]
    cum_v = group["volume"].cumsum()
    cum_pv = pv.groupby(data["group_key"], sort=False).cumsum()
    cum_p2v = p2v.groupby(data["group_key"], sort=False).cumsum()

    data["vwap"] = cum_pv / cum_v
    variance = (cum_p2v / cum_v) - data["vwap"].pow(2)
    variance = variance.clip(lower=0)
    data["vwap_sd"] = np.sqrt(variance)
    data["z_vwap"] = np.where(
        data["vwap_sd"] > 0,
        (data["close"] - data["vwap"]) / data["vwap_sd"],
        np.nan,
    )
    data["prev_z"] = group["z_vwap"].shift(1)

    minute = data["timestamp_et"].dt.hour * 60 + data["timestamp_et"].dt.minute
    data["time_segment"] = pd.cut(
        minute,
        bins=[9 * 60 + 30, 10 * 60, 12 * 60, 14 * 60, 16 * 60],
        labels=["09:30-10:00", "10:00-12:00", "12:00-14:00", "14:00-16:00"],
        right=True,
        include_lowest=False,
    ).astype(str)
    data["year"] = data["timestamp_et"].dt.year

    for h in HORIZONS:
        future_close = group["close"].shift(-h)
        future_ts = group["timestamp_et"].shift(-h)
        exact_horizon = (future_ts - data["timestamp_et"]) == pd.Timedelta(minutes=h)
        data[f"exact_{h}m"] = exact_horizon.fillna(False)
        data[f"fwd_{h}m"] = np.where(
            data[f"exact_{h}m"],
            future_close / data["close"] - 1.0,
            np.nan,
        )

    return data


def build_events(features: pd.DataFrame) -> pd.DataFrame:
    event_frames = []
    for threshold in THRESHOLDS:
        lower = (features["z_vwap"] <= -threshold) & (features["prev_z"] > -threshold)
        upper = (features["z_vwap"] >= threshold) & (features["prev_z"] < threshold)

        for side, mask, label in [
            (1, lower, "LOWER"),
            (-1, upper, "UPPER"),
        ]:
            ev = features.loc[
                mask,
                [
                    "timestamp_et",
                    "session_date",
                    "group_key",
                    "bar_index",
                    "year",
                    "time_segment",
                    "contract",
                    "close",
                    "high",
                    "low",
                    "z_vwap",
                    *[f"fwd_{h}m" for h in HORIZONS],
                    *[f"future_high_{h}m" for h in HORIZONS],
                    *[f"future_low_{h}m" for h in HORIZONS],
                ],
            ].copy()
            ev["threshold"] = threshold
            ev["side"] = side
            ev["band"] = label
            for h in HORIZONS:
                ev[f"directional_{h}m"] = side * ev[f"fwd_{h}m"]
            event_frames.append(ev)

    return pd.concat(event_frames, ignore_index=True)


def add_forward_extrema(features: pd.DataFrame) -> pd.DataFrame:
    out = features.reset_index(drop=True).copy()
    n_total = len(out)
    group_indices = out.groupby("group_key", sort=False, observed=True).indices

    for h in HORIZONS:
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
        valid_window = out[f"exact_{h}m"].fillna(False).to_numpy(dtype=bool)
        future_high[~valid_window] = np.nan
        future_low[~valid_window] = np.nan
        out[f"future_high_{h}m"] = future_high
        out[f"future_low_{h}m"] = future_low
    return out


def add_excursions(events: pd.DataFrame) -> pd.DataFrame:
    out = events.copy()
    for h in HORIZONS:
        high = out[f"future_high_{h}m"]
        low = out[f"future_low_{h}m"]
        entry = out["close"]
        long_side = out["side"] == 1
        out[f"mfe_{h}m"] = np.where(
            long_side, high / entry - 1.0, 1.0 - low / entry
        )
        out[f"mae_{h}m"] = np.where(
            long_side, low / entry - 1.0, 1.0 - high / entry
        )
    return out


def clustered_mean_stats(values: pd.Series, groups: pd.Series) -> dict:
    frame = pd.DataFrame({"y": values, "g": groups}).dropna()
    n = len(frame)
    clusters = frame["g"].nunique()
    if n < 2 or clusters < 2:
        return {
            "clustered_se": np.nan,
            "t_stat": np.nan,
            "p_value": np.nan,
            "ci_low": np.nan,
            "ci_high": np.nan,
        }
    y = frame["y"].to_numpy(dtype=float)
    x = np.ones((n, 1), dtype=float)
    result = sm.OLS(y, x).fit(cov_type="cluster", cov_kwds={"groups": frame["g"].to_numpy()})
    ci = result.conf_int(alpha=0.05)[0]
    return {
        "clustered_se": float(result.bse[0]),
        "t_stat": float(result.tvalues[0]),
        "p_value": float(result.pvalues[0]),
        "ci_low": float(ci[0]),
        "ci_high": float(ci[1]),
    }


def summarize(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold in THRESHOLDS:
        for band in ["LOWER", "UPPER"]:
            subset = events[(events["threshold"] == threshold) & (events["band"] == band)]
            for h in HORIZONS:
                col = f"directional_{h}m"
                valid = subset.dropna(subset=[col])
                y_bps = valid[col] * 10000.0
                robust = clustered_mean_stats(y_bps, valid["session_date"])
                std = float(y_bps.std(ddof=1)) if len(y_bps) > 1 else np.nan
                rows.append(
                    {
                        "threshold": threshold,
                        "band": band,
                        "horizon_min": h,
                        "n": int(len(valid)),
                        "sessions": int(valid["session_date"].nunique()),
                        "mean_directional_bps": float(y_bps.mean()) if len(y_bps) else np.nan,
                        "median_directional_bps": float(y_bps.median()) if len(y_bps) else np.nan,
                        "std_directional_bps": std,
                        "win_rate": float((y_bps > 0).mean()) if len(y_bps) else np.nan,
                        "effect_size_d": float(y_bps.mean() / std) if len(y_bps) > 1 and std > 0 else np.nan,
                        "mean_mfe_bps": float((valid[f"mfe_{h}m"] * 10000).mean()) if len(valid) else np.nan,
                        "mean_mae_bps": float((valid[f"mae_{h}m"] * 10000).mean()) if len(valid) else np.nan,
                        **robust,
                    }
                )
    return pd.DataFrame(rows)


def segment_summary(events: pd.DataFrame) -> pd.DataFrame:
    base = events[(events["threshold"] == 2.0)].dropna(subset=["directional_15m"]).copy()
    rows = []
    for dimension in ["year", "time_segment"]:
        for (band, value), g in base.groupby(["band", dimension], observed=True):
            y = g["directional_15m"] * 10000.0
            robust = clustered_mean_stats(y, g["session_date"])
            rows.append(
                {
                    "dimension": dimension,
                    "value": str(value),
                    "band": band,
                    "n": len(g),
                    "sessions": g["session_date"].nunique(),
                    "mean_directional_bps": y.mean(),
                    "win_rate": (y > 0).mean(),
                    **robust,
                }
            )
    return pd.DataFrame(rows)


def write_markdown(summary: pd.DataFrame, segmented: pd.DataFrame, output: Path, label: str) -> None:
    core = summary[(summary["threshold"] == 2.0) & (summary["horizon_min"] == 15)].copy()
    lines = [
        f"# R001 VWAP — {label}",
        "",
        "Primary hypotheses use first crossings of ±2.0 cumulative volume-weighted VWAP standard deviations and 15-minute forward returns.",
        "Positive directional return means reversion in the hypothesized direction (long below VWAP, short above VWAP).",
        "Inference uses session-clustered standard errors.",
        "",
        "## Core ±2σ / 15-minute result",
        "",
        "| Band | N | Sessions | Mean directional (bps) | Win rate | t-stat | p-value | 95% CI (bps) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in core.iterrows():
        lines.append(
            f"| {r['band']} | {int(r['n'])} | {int(r['sessions'])} | {r['mean_directional_bps']:.3f} | "
            f"{r['win_rate']:.3%} | {r['t_stat']:.3f} | {r['p_value']:.4f} | "
            f"[{r['ci_low']:.3f}, {r['ci_high']:.3f}] |"
        )
    lines += [
        "",
        "## Interpretation rule",
        "",
        "This file is descriptive research output, not a trading rule. No stop loss, target, sizing rule, or execution filter is introduced at R001.",
        "",
        "Sensitivity and segmentation tables are stored in CSV outputs for review before any validation-period data are opened.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--label", default="development_2020_2024")
    parser.add_argument("--output-dir", default="results/R001/development_2020_2024")
    args = parser.parse_args()

    df = pd.read_parquet(args.input)
    features = prepare_features(df, args.start, args.end)
    features = add_forward_extrema(features)
    events = build_events(features)
    events = add_excursions(events)
    summary = summarize(events)
    segmented = segment_summary(events)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    events.to_parquet(out / "events.parquet", index=False, compression="zstd")
    summary.to_csv(out / "sensitivity_summary.csv", index=False)
    segmented.to_csv(out / "segmentation_2sigma_15m.csv", index=False)
    write_markdown(summary, segmented, out / "SUMMARY.md", args.label)

    print(summary[(summary["threshold"] == 2.0) & (summary["horizon_min"] == 15)].to_string(index=False))
    print(f"Feature rows: {len(features):,}")
    print(f"Event rows: {len(events):,}")


if __name__ == "__main__":
    main()