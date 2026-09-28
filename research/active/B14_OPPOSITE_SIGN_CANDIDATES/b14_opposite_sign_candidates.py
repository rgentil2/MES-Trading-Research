from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import benjamini_hochberg, clustered_mean_stats
from research.archive.B12.b12_strategy_architecture import (
    COST_RT,
    HORIZONS,
    PRIMARY_HORIZON,
    max_drawdown,
    parse_raw,
    prepare_rth,
    profit_factor,
    trade_from_signal,
)
from research.archive.B13.b13_high_directional_triggers import (
    WICK_MIN,
    block_features,
)

STRESS_COST_RT = COST_RT * 1.5


def build_exact_inverse_trades(
    feats: pd.DataFrame,
    groups: dict[str, pd.DataFrame],
    hypothesis: str,
) -> pd.DataFrame:
    rows = []

    for key, f in feats.groupby("group_key", sort=False, observed=True):
        g = groups.get(key)
        if g is None:
            continue

        candidates = []

        for r in f.sort_values("block_id").itertuples(index=False):
            direction = 0

            if hypothesis == "H080":
                meaningful = (
                    pd.notna(r.abs_vwap_disp_q60)
                    and abs(r.vwap_displacement_bps) >= r.abs_vwap_disp_q60
                )
                aligned = (
                    r.block_return != 0
                    and r.vwap_displacement_bps != 0
                    and np.sign(r.block_return) == np.sign(r.vwap_displacement_bps)
                )
                if meaningful and aligned:
                    direction = -1 if r.vwap_displacement_bps > 0 else 1

            elif hypothesis == "H081":
                upper = (
                    r.upper_wick_ratio >= WICK_MIN
                    and r.block_close < r.block_open
                )
                lower = (
                    r.lower_wick_ratio >= WICK_MIN
                    and r.block_close > r.block_open
                )
                if upper:
                    direction = 1
                elif lower:
                    direction = -1
            else:
                raise ValueError(hypothesis)

            if direction == 0:
                continue

            signal_pos = int(r.signal_pos)
            signal_bar = g.iloc[signal_pos]
            signal_minute = signal_bar["timestamp_et"].hour * 60 + signal_bar["timestamp_et"].minute
            if signal_minute > 690:
                continue

            tr = trade_from_signal(g, signal_pos, direction)
            if tr is None:
                continue

            rec = {
                **r._asdict(),
                "direction": direction,
                "side": "LONG" if direction == 1 else "SHORT",
                **tr,
            }
            for h in HORIZONS:
                rec[f"stress_net_pnl_{h}"] = rec[f"gross_pnl_{h}"] - STRESS_COST_RT

            candidates.append(rec)

        if candidates:
            rows.append(min(candidates, key=lambda z: z["entry_clock_et"]))

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("entry_clock_et").reset_index(drop=True)


def horizon_metrics(hypothesis: str, trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for h in HORIZONS:
        gross = trades[f"gross_pnl_{h}"]
        net = trades[f"net_pnl_{h}"]
        stress = trades[f"stress_net_pnl_{h}"]

        rows.append({
            "hypothesis": hypothesis,
            "horizon_minutes": h,
            "trades": int(len(trades)),
            "gross_expectancy_usd": float(gross.mean()),
            "net_expectancy_usd": float(net.mean()),
            "stress_1_5x_expectancy_usd": float(stress.mean()),
            "net_pnl_usd": float(net.sum()),
            "profit_factor": profit_factor(net),
            "win_rate": float((net > 0).mean()),
            "max_drawdown_usd": max_drawdown(net),
        })
    return pd.DataFrame(rows)


def primary_summary(
    hypothesis: str,
    trades: pd.DataFrame,
    min_n: int,
    min_years_observed: int,
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    pnl = trades[f"net_pnl_{PRIMARY_HORIZON}"]
    stress = trades[f"stress_net_pnl_{PRIMARY_HORIZON}"]
    stats = clustered_mean_stats(pnl, trades["session_date"])

    yearly = (
        trades.groupby("year", observed=True)
        .agg(
            trades=(f"net_pnl_{PRIMARY_HORIZON}", "size"),
            expectancy_usd=(f"net_pnl_{PRIMARY_HORIZON}", "mean"),
            stress_expectancy_usd=(f"stress_net_pnl_{PRIMARY_HORIZON}", "mean"),
            net_pnl_usd=(f"net_pnl_{PRIMARY_HORIZON}", "sum"),
        )
        .reset_index()
    )

    split = trades.assign(
        period=np.where(trades["year"] <= 2022, "2020_2022", "2023_2025")
    ).groupby("period", observed=True).agg(
        trades=(f"net_pnl_{PRIMARY_HORIZON}", "size"),
        expectancy_usd=(f"net_pnl_{PRIMARY_HORIZON}", "mean"),
        stress_expectancy_usd=(f"stress_net_pnl_{PRIMARY_HORIZON}", "mean"),
        net_pnl_usd=(f"net_pnl_{PRIMARY_HORIZON}", "sum"),
    ).reset_index()

    early = split.loc[split["period"] == "2020_2022", "expectancy_usd"]
    late = split.loc[split["period"] == "2023_2025", "expectancy_usd"]

    row = {
        "hypothesis": hypothesis,
        "trades": int(len(trades)),
        "sessions": int(trades["session_date"].nunique()),
        "net_pnl_usd": float(pnl.sum()),
        "expectancy_usd": float(pnl.mean()),
        "stress_1_5x_expectancy_usd": float(stress.mean()),
        "profit_factor": profit_factor(pnl),
        "win_rate": float((pnl > 0).mean()),
        "max_drawdown_usd": max_drawdown(pnl),
        "avg_mfe30_usd": float(trades["mfe30_usd"].mean()),
        "avg_mae30_usd": float(trades["mae30_usd"].mean()),
        "years_positive": int((yearly["expectancy_usd"] > 0).sum()),
        "years_observed": int(yearly["year"].nunique()),
        "min_n_gate": min_n,
        "min_years_observed": min_years_observed,
        "early_expectancy_usd": float(early.iloc[0]) if len(early) else np.nan,
        "late_expectancy_usd": float(late.iloc[0]) if len(late) else np.nan,
        **stats,
    }

    return row, yearly, split


def side_breakdown(h, trades):
    x = (
        trades.groupby("side", observed=True)
        .agg(
            trades=(f"net_pnl_{PRIMARY_HORIZON}", "size"),
            expectancy_usd=(f"net_pnl_{PRIMARY_HORIZON}", "mean"),
            stress_expectancy_usd=(f"stress_net_pnl_{PRIMARY_HORIZON}", "mean"),
            net_pnl_usd=(f"net_pnl_{PRIMARY_HORIZON}", "sum"),
            win_rate=(f"net_pnl_{PRIMARY_HORIZON}", lambda s: float((s > 0).mean())),
        )
        .reset_index()
    )
    x["hypothesis"] = h
    return x


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet",
    )
    p.add_argument("--output-dir", default="results/B14")
    a = p.parse_args()

    raw = parse_raw(pd.read_parquet(a.input))
    _, groups = prepare_rth(raw)
    feats = block_features(raw, groups)

    t80 = build_exact_inverse_trades(feats, groups, "H080")
    t81 = build_exact_inverse_trades(feats, groups, "H081")

    candidates = [
        ("H080", t80, 150, 5),
        ("H081", t81, 100, 6),
    ]

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    yearly_parts = []
    split_parts = []
    horizon_parts = []
    side_parts = []

    for h, trades, min_n, min_years in candidates:
        row, yearly, split = primary_summary(h, trades, min_n, min_years)
        rows.append(row)
        yearly["hypothesis"] = h
        split["hypothesis"] = h
        yearly_parts.append(yearly)
        split_parts.append(split)
        horizon_parts.append(horizon_metrics(h, trades))
        side_parts.append(side_breakdown(h, trades))
        trades.to_parquet(out / f"{h}_trades.parquet", index=False)

    summary = pd.DataFrame(rows)
    summary["q_value_bh"] = benjamini_hochberg(summary["p_value"])
    summary["passes_candidate_gate"] = (
        (summary["trades"] >= summary["min_n_gate"])
        & (summary["sessions"] >= summary["min_n_gate"])
        & (summary["expectancy_usd"] >= 2.0)
        & (summary["ci_low"] > 0)
        & (summary["p_value"] < 0.05)
        & (summary["q_value_bh"] < 0.05)
        & (summary["profit_factor"] >= 1.15)
        & (summary["net_pnl_usd"] > 0)
        & (summary["years_observed"] >= summary["min_years_observed"])
        & (summary["years_positive"] >= 4)
        & (summary["stress_1_5x_expectancy_usd"] > 0)
        & (summary["early_expectancy_usd"] > 0)
        & (summary["late_expectancy_usd"] > 0)
    )

    summary.to_csv(out / "B14_SUMMARY.csv", index=False)
    pd.concat(yearly_parts, ignore_index=True).to_csv(out / "yearly.csv", index=False)
    pd.concat(split_parts, ignore_index=True).to_csv(out / "early_late_split.csv", index=False)
    pd.concat(horizon_parts, ignore_index=True).to_csv(out / "horizon_metrics.csv", index=False)
    pd.concat(side_parts, ignore_index=True).to_csv(out / "side_breakdown.csv", index=False)

    print(summary.to_string(index=False))
    print("\nHorizon metrics")
    print(pd.concat(horizon_parts, ignore_index=True).to_string(index=False))
    print("\nEarly/late")
    print(pd.concat(split_parts, ignore_index=True).to_string(index=False))
    print("\nSide")
    print(pd.concat(side_parts, ignore_index=True).to_string(index=False))


if __name__ == "__main__":
    main()
