from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.archive.R001.r001_vwap_analysis import clustered_mean_stats, prepare_features

PRIMARY_THRESHOLD = 2.0
PRIMARY_HORIZON = 15


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
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


def add_regime_features(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy()
    group = data.groupby("group_key", sort=False, observed=True)

    prev_close = group["close"].shift(1)
    prev_ts = group["timestamp_et"].shift(1)
    exact_1m = (data["timestamp_et"] - prev_ts) == pd.Timedelta(minutes=1)
    data["logret_1m"] = np.where(
        exact_1m,
        np.log(data["close"] / prev_close),
        np.nan,
    )

    lag_vwap_30 = group["vwap"].shift(30)
    lag_ts_30 = group["timestamp_et"].shift(30)
    exact_history_30m = (data["timestamp_et"] - lag_ts_30) == pd.Timedelta(minutes=30)
    data["exact_history_30m"] = exact_history_30m.fillna(False)
    data["vwap_slope_30m_bps"] = np.where(
        data["exact_history_30m"],
        (data["vwap"] / lag_vwap_30 - 1.0) * 10000.0,
        np.nan,
    )

    rv = (
        data.groupby("group_key", sort=False, observed=True)["logret_1m"]
        .rolling(window=30, min_periods=30)
        .apply(lambda x: float(np.sqrt(np.square(x).sum()) * 10000.0), raw=True)
        .reset_index(level=0, drop=True)
    )
    data["rv30_bps"] = np.where(data["exact_history_30m"], rv, np.nan)
    return data


def build_r002_events(features: pd.DataFrame) -> pd.DataFrame:
    lower = (features["z_vwap"] <= -PRIMARY_THRESHOLD) & (
        features["prev_z"] > -PRIMARY_THRESHOLD
    )
    upper = (features["z_vwap"] >= PRIMARY_THRESHOLD) & (
        features["prev_z"] < PRIMARY_THRESHOLD
    )

    frames = []
    for band, direction, mask in [
        ("LOWER", -1, lower),
        ("UPPER", 1, upper),
    ]:
        ev = features.loc[
            mask,
            [
                "timestamp_et",
                "session_date",
                "group_key",
                "year",
                "time_segment",
                "contract",
                "close",
                "vwap",
                "z_vwap",
                "vwap_slope_30m_bps",
                "rv30_bps",
                "exact_history_30m",
                "exact_15m",
                "fwd_15m",
            ],
        ].copy()
        ev["band"] = band
        ev["excursion_direction"] = direction
        frames.append(ev)

    events = pd.concat(frames, ignore_index=True)
    events = events[
        events["exact_history_30m"]
        & events["exact_15m"]
        & events["vwap_slope_30m_bps"].notna()
        & events["rv30_bps"].notna()
        & events["fwd_15m"].notna()
    ].copy()

    slope_sign = np.sign(events["vwap_slope_30m_bps"].to_numpy(dtype=float))
    excursion = events["excursion_direction"].to_numpy(dtype=float)
    events["alignment"] = np.where(
        slope_sign == 0,
        "FLAT",
        np.where(slope_sign == excursion, "WITH_TREND", "COUNTER_TREND"),
    )

    events["continuation_15m_bps"] = (
        events["excursion_direction"] * events["fwd_15m"] * 10000.0
    )
    return events


def fit_volatility_thresholds(events: pd.DataFrame) -> tuple[float, float]:
    q1, q2 = events["rv30_bps"].quantile([1.0 / 3.0, 2.0 / 3.0]).tolist()
    if not np.isfinite(q1) or not np.isfinite(q2) or q1 >= q2:
        raise ValueError("Could not estimate distinct volatility tercile thresholds")
    return float(q1), float(q2)


def assign_volatility_regime(
    events: pd.DataFrame, q1: float, q2: float
) -> pd.DataFrame:
    out = events.copy()
    out["vol_regime"] = pd.cut(
        out["rv30_bps"],
        bins=[-np.inf, q1, q2, np.inf],
        labels=["LOW", "MID", "HIGH"],
        include_lowest=True,
        right=True,
    ).astype(str)
    return out


def summarize_cells(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    usable = events[events["alignment"].isin(["WITH_TREND", "COUNTER_TREND"])].copy()

    for (alignment, vol_regime), g in usable.groupby(
        ["alignment", "vol_regime"], observed=True
    ):
        y = g["continuation_15m_bps"]
        stats = clustered_mean_stats(y, g["session_date"])
        rows.append(
            {
                "alignment": alignment,
                "vol_regime": vol_regime,
                "n": int(len(g)),
                "sessions": int(g["session_date"].nunique()),
                "mean_continuation_bps": float(y.mean()),
                "median_continuation_bps": float(y.median()),
                "std_continuation_bps": float(y.std(ddof=1)),
                "continuation_rate": float((y > 0).mean()),
                "mean_abs_vwap_slope_30m_bps": float(
                    g["vwap_slope_30m_bps"].abs().mean()
                ),
                "mean_rv30_bps": float(g["rv30_bps"].mean()),
                **stats,
            }
        )

    return pd.DataFrame(rows).sort_values(["alignment", "vol_regime"]).reset_index(
        drop=True
    )


def summarize_years(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    usable = events[events["alignment"].isin(["WITH_TREND", "COUNTER_TREND"])].copy()
    for (alignment, vol_regime, year), g in usable.groupby(
        ["alignment", "vol_regime", "year"], observed=True
    ):
        y = g["continuation_15m_bps"]
        rows.append(
            {
                "alignment": alignment,
                "vol_regime": vol_regime,
                "year": int(year),
                "n": int(len(g)),
                "sessions": int(g["session_date"].nunique()),
                "mean_continuation_bps": float(y.mean()),
                "continuation_rate": float((y > 0).mean()),
            }
        )
    return pd.DataFrame(rows)


def primary_hypotheses(
    cells: pd.DataFrame, yearly: pd.DataFrame
) -> pd.DataFrame:
    specs = [
        {
            "hypothesis": "H003",
            "alignment": "WITH_TREND",
            "vol_regime": "HIGH",
            "expected_sign": 1,
            "description": "Trend-aligned high-volatility continuation",
        },
        {
            "hypothesis": "H004",
            "alignment": "COUNTER_TREND",
            "vol_regime": "LOW",
            "expected_sign": -1,
            "description": "Counter-trend low-volatility reversion",
        },
    ]

    rows = []
    for spec in specs:
        match = cells[
            (cells["alignment"] == spec["alignment"])
            & (cells["vol_regime"] == spec["vol_regime"])
        ]
        if len(match) != 1:
            raise ValueError(f"Primary cell missing or duplicated: {spec}")
        r = match.iloc[0]

        yg = yearly[
            (yearly["alignment"] == spec["alignment"])
            & (yearly["vol_regime"] == spec["vol_regime"])
        ]
        sign = spec["expected_sign"]
        years_on_side = int(
            (np.sign(yg["mean_continuation_bps"].to_numpy(dtype=float)) == sign).sum()
        )
        years_observed = int(yg["year"].nunique())

        rows.append(
            {
                **spec,
                "n": int(r["n"]),
                "sessions": int(r["sessions"]),
                "mean_continuation_bps": float(r["mean_continuation_bps"]),
                "clustered_se": float(r["clustered_se"]),
                "t_stat": float(r["t_stat"]),
                "p_value": float(r["p_value"]),
                "ci_low": float(r["ci_low"]),
                "ci_high": float(r["ci_high"]),
                "years_on_hypothesized_side": years_on_side,
                "years_observed": years_observed,
            }
        )

    out = pd.DataFrame(rows)
    out["q_value"] = benjamini_hochberg(out["p_value"])

    def gate(row: pd.Series) -> bool:
        sign = int(row["expected_sign"])
        ci_ok = row["ci_low"] > 0 if sign > 0 else row["ci_high"] < 0
        effect_ok = (
            row["mean_continuation_bps"] >= 1.0
            if sign > 0
            else row["mean_continuation_bps"] <= -1.0
        )
        return bool(
            row["n"] >= 500
            and row["sessions"] >= 250
            and row["q_value"] < 0.05
            and ci_ok
            and effect_ok
            and row["years_observed"] == 5
            and row["years_on_hypothesized_side"] >= 4
        )

    out["passes_development_gate"] = out.apply(gate, axis=1)
    return out


def write_summary(
    primary: pd.DataFrame,
    thresholds: dict,
    events: pd.DataFrame,
    output: Path,
) -> None:
    lines = [
        "# R002 VWAP regime study — development 2020–2024",
        "",
        "R002 tests whether ±2σ VWAP excursions behave differently by 30-minute VWAP trend alignment and trailing 30-minute realized volatility.",
        "",
        "Positive continuation score means movement farther away from VWAP. Negative means reversion.",
        "",
        "## Frozen volatility thresholds",
        "",
        f"- LOW / MID cutoff: {thresholds['rv30_q33_bps']:.3f} bps",
        f"- MID / HIGH cutoff: {thresholds['rv30_q67_bps']:.3f} bps",
        "",
        "## Primary hypotheses",
        "",
        "| Hypothesis | Regime | N | Sessions | Mean (bps) | p | q | 95% CI | Years on side | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in primary.iterrows():
        regime = f"{r['alignment']} + {r['vol_regime']}"
        lines.append(
            f"| {r['hypothesis']} | {regime} | {int(r['n'])} | {int(r['sessions'])} | "
            f"{r['mean_continuation_bps']:.3f} | {r['p_value']:.4f} | {r['q_value']:.4f} | "
            f"[{r['ci_low']:.3f}, {r['ci_high']:.3f}] | "
            f"{int(r['years_on_hypothesized_side'])}/{int(r['years_observed'])} | "
            f"{'PASS' if r['passes_development_gate'] else 'FAIL'} |"
        )

    lines += [
        "",
        f"Eligible R002 events: {len(events):,}",
        "",
        "2025 and 2026 are not used in this development output.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet"
    )
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--output-dir", default="results/R002/development_2020_2024")
    args = parser.parse_args()

    raw = pd.read_parquet(args.input)
    features = prepare_features(raw, args.start, args.end)
    features = add_regime_features(features)
    events = build_r002_events(features)

    q1, q2 = fit_volatility_thresholds(events)
    events = assign_volatility_regime(events, q1, q2)

    cells = summarize_cells(events)
    yearly = summarize_years(events)
    primary = primary_hypotheses(cells, yearly)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    thresholds = {
        "development_start": args.start,
        "development_end": args.end,
        "event_threshold_sigma": PRIMARY_THRESHOLD,
        "forward_horizon_minutes": PRIMARY_HORIZON,
        "trend_lookback_minutes": 30,
        "volatility_lookback_minutes": 30,
        "rv30_q33_bps": q1,
        "rv30_q67_bps": q2,
    }

    events.to_parquet(out / "events.parquet", index=False, compression="zstd")
    cells.to_csv(out / "regime_cells.csv", index=False)
    yearly.to_csv(out / "yearly_stability.csv", index=False)
    primary.to_csv(out / "primary_hypotheses.csv", index=False)
    (out / "regime_thresholds.json").write_text(
        json.dumps(thresholds, indent=2), encoding="utf-8"
    )
    write_summary(primary, thresholds, events, out / "SUMMARY.md")

    print(primary.to_string(index=False))
    print(json.dumps(thresholds, indent=2))
    print(f"Eligible events: {len(events):,}")


if __name__ == "__main__":
    main()
