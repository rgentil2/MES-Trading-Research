from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import benjamini_hochberg, clustered_mean_stats
from research.archive.B05.b05_volatility_regime_forecast import (
    add_overnight_ranges,
    add_states_and_predictions,
    build_base_sessions,
    parse_raw,
)
from research.archive.R017.r017_h017_filter import (
    build_h017_regimes,
    build_orb_signals,
    build_previous_level_signals,
    build_volume_impulse_signals,
    enrich_features,
    perf,
)

UPDATE_MINUTE = 9 * 60 + 45
H017_ACTIVE_MINUTES = 30


def build_regime_map(raw: pd.DataFrame, strategy_features: pd.DataFrame):
    parsed = parse_raw(raw)
    sessions, _, _ = build_base_sessions(parsed)
    sessions = add_overnight_ranges(parsed, sessions)
    sessions = add_states_and_predictions(sessions)

    regime = sessions[
        [
            "group_key",
            "preopen_prediction",
            "update_prediction",
        ]
    ].copy()

    h017 = build_h017_regimes(strategy_features)
    regime = regime.merge(
        h017[["group_key", "h017_time"]],
        on="group_key",
        how="left",
        validate="one_to_one",
    )
    return regime


def attach_dynamic_regime(trades: pd.DataFrame, regime: pd.DataFrame):
    e = trades.merge(
        regime,
        on="group_key",
        how="left",
        validate="many_to_one",
    )
    minute = (
        e["timestamp_et"].dt.hour * 60
        + e["timestamp_et"].dt.minute
    )
    e["regime"] = np.where(
        minute >= UPDATE_MINUTE,
        e["update_prediction"],
        e["preopen_prediction"],
    )

    h017_override = (
        e["h017_time"].notna()
        & (e["timestamp_et"] >= e["h017_time"])
        & (
            e["timestamp_et"]
            <= e["h017_time"]
            + pd.Timedelta(minutes=H017_ACTIVE_MINUTES)
        )
    )
    e.loc[h017_override, "regime"] = "LOW"
    return e[e["regime"].notna()].copy()


def strategy_stats(trades: pd.DataFrame, hypothesis: str):
    baseline = perf(trades)
    high = trades[trades["regime"] == "HIGH"].copy()
    high_perf = perf(high)

    if len(high):
        stats = clustered_mean_stats(
            high["net_pnl_usd"],
            high["session_date"],
        )
        yearly = (
            high.groupby("year", observed=True)
            .agg(
                trades=("net_pnl_usd", "size"),
                net_pnl_usd=("net_pnl_usd", "sum"),
                expectancy_usd=("net_pnl_usd", "mean"),
            )
            .reset_index()
        )
        years_positive = int(
            (yearly["expectancy_usd"] > 0).sum()
        )
        years_observed = int(
            yearly["year"].nunique()
        )
    else:
        stats = {
            "mean": np.nan,
            "clustered_se": np.nan,
            "t_stat": np.nan,
            "p_value": np.nan,
            "ci_low": np.nan,
            "ci_high": np.nan,
        }
        yearly = pd.DataFrame(
            columns=[
                "year",
                "trades",
                "net_pnl_usd",
                "expectancy_usd",
            ]
        )
        years_positive = 0
        years_observed = 0

    by_regime = (
        trades.groupby("regime", observed=True)
        .agg(
            trades=("net_pnl_usd", "size"),
            net_pnl_usd=("net_pnl_usd", "sum"),
            expectancy_usd=("net_pnl_usd", "mean"),
            win_rate=(
                "net_pnl_usd",
                lambda s: float((s > 0).mean()),
            ),
        )
        .reset_index()
    )
    by_regime["hypothesis"] = hypothesis

    row = {
        "hypothesis": hypothesis,
        "strategy": (
            trades["strategy"].iloc[0]
            if len(trades)
            else ""
        ),
        "baseline_trades": baseline["trades"],
        "baseline_net_pnl_usd": baseline["net_pnl_usd"],
        "baseline_expectancy_usd": baseline[
            "expectancy_usd"
        ],
        "baseline_pf": baseline["profit_factor"],
        "baseline_max_dd_usd": baseline[
            "max_drawdown_usd"
        ],
        "high_trades": high_perf["trades"],
        "high_net_pnl_usd": high_perf["net_pnl_usd"],
        "high_expectancy_usd": high_perf[
            "expectancy_usd"
        ],
        "high_pf": high_perf["profit_factor"],
        "high_win_rate": high_perf["win_rate"],
        "high_max_dd_usd": high_perf[
            "max_drawdown_usd"
        ],
        "expectancy_improvement_usd": (
            high_perf["expectancy_usd"]
            - baseline["expectancy_usd"]
            if np.isfinite(high_perf["expectancy_usd"])
            and np.isfinite(baseline["expectancy_usd"])
            else np.nan
        ),
        "pf_improvement": (
            high_perf["profit_factor"]
            - baseline["profit_factor"]
            if np.isfinite(high_perf["profit_factor"])
            and np.isfinite(baseline["profit_factor"])
            else np.nan
        ),
        "years_positive": years_positive,
        "years_observed": years_observed,
        **stats,
    }
    return row, yearly, by_regime


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default=(
            "data/processed/"
            "MES_CONTINUOUS_1M_2020_2026.parquet"
        ),
    )
    p.add_argument(
        "--output-dir",
        default="results/B06",
    )
    a = p.parse_args()

    raw = pd.read_parquet(a.input)
    features = enrich_features(raw)
    regime = build_regime_map(raw, features)

    strategies = [
        (
            "H046",
            attach_dynamic_regime(
                build_orb_signals(features),
                regime,
            ),
        ),
        (
            "H047",
            attach_dynamic_regime(
                build_previous_level_signals(features),
                regime,
            ),
        ),
        (
            "H048",
            attach_dynamic_regime(
                build_volume_impulse_signals(features),
                regime,
            ),
        ),
    ]

    rows = []
    yearly_parts = []
    regime_parts = []
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for h, trades in strategies:
        row, yearly, by_regime = strategy_stats(
            trades, h
        )
        rows.append(row)
        yearly["hypothesis"] = h
        yearly_parts.append(yearly)
        regime_parts.append(by_regime)
        trades.to_parquet(
            out / f"{h}_trades.parquet",
            index=False,
        )

    summary = pd.DataFrame(rows)
    summary["q_value_bh"] = benjamini_hochberg(
        summary["p_value"]
    )
    summary["passes_strategy_gate"] = (
        (summary["high_trades"] >= 150)
        & (summary["high_expectancy_usd"] >= 1.0)
        & (summary["ci_low"] > 0)
        & (summary["p_value"] < 0.05)
        & (summary["q_value_bh"] < 0.05)
        & (summary["high_pf"] >= 1.15)
        & (summary["years_observed"] == 6)
        & (summary["years_positive"] >= 4)
        & (summary["high_net_pnl_usd"] > 0)
        & (
            summary["expectancy_improvement_usd"]
            >= 3.0
        )
        & (summary["pf_improvement"] >= 0.10)
    )

    summary.to_csv(
        out / "B06_SUMMARY.csv",
        index=False,
    )
    pd.concat(
        yearly_parts,
        ignore_index=True,
    ).to_csv(
        out / "yearly_high_regime.csv",
        index=False,
    )
    pd.concat(
        regime_parts,
        ignore_index=True,
    ).to_csv(
        out / "regime_breakdown.csv",
        index=False,
    )
    regime.to_parquet(
        out / "regime_map.parquet",
        index=False,
    )

    print(summary.to_string(index=False))
    print("\nBy regime")
    print(
        pd.concat(
            regime_parts,
            ignore_index=True,
        ).to_string(index=False)
    )


if __name__ == "__main__":
    main()
