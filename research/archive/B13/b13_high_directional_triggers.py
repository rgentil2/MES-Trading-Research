from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import benjamini_hochberg, clustered_mean_stats
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_dynamic_outputs
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

BODY_RATIO_MIN = 0.60
CLV_UPPER = 0.80
CLV_LOWER = 0.20
VWAP_Q = 0.60
VWAP_REF = 60
WICK_MIN = 0.50


def block_features(raw: pd.DataFrame, groups: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dyn = build_dynamic_outputs(raw).copy()
    dyn = dyn[
        dyn["block_id"].between(0, 6)
        & (dyn["engine_state"] == "HIGH")
    ].copy()

    rows = []
    for r in dyn.itertuples(index=False):
        g = groups.get(r.group_key)
        if g is None:
            continue

        start = int(r.block_id) * 15
        end = start + 15
        b = g.iloc[start:end]
        if len(b) != 15:
            continue

        op = float(b["open"].iloc[0])
        cl = float(b["close"].iloc[-1])
        hi = float(b["high"].max())
        lo = float(b["low"].min())
        rng = hi - lo
        if op <= 0 or cl <= 0 or rng <= 0:
            continue

        body_ratio = abs(cl - op) / rng
        clv = (cl - lo) / rng
        upper_wick = (hi - max(op, cl)) / rng
        lower_wick = (min(op, cl) - lo) / rng

        # Cumulative RTH VWAP through this completed block.
        cum = g.iloc[:end]
        tp = (
            cum["high"].to_numpy(float)
            + cum["low"].to_numpy(float)
            + cum["close"].to_numpy(float)
        ) / 3.0
        vol = cum["volume"].to_numpy(float)
        total_vol = float(vol.sum())
        if total_vol <= 0:
            continue
        vwap = float(np.sum(tp * vol) / total_vol)
        if vwap <= 0:
            continue

        disp_bps = float(np.log(cl / vwap) * 10000.0)

        rows.append({
            "group_key": r.group_key,
            "session_date": r.session_date,
            "year": int(r.year),
            "contract": r.contract,
            "block_id": int(r.block_id),
            "block_end_ts": r.block_end_ts,
            "signal_pos": end - 1,
            "block_open": op,
            "block_close": cl,
            "block_high": hi,
            "block_low": lo,
            "block_range_points": rng,
            "body_ratio": body_ratio,
            "clv": clv,
            "upper_wick_ratio": upper_wick,
            "lower_wick_ratio": lower_wick,
            "block_return": float(np.log(cl / op)),
            "cum_vwap": vwap,
            "vwap_displacement_bps": disp_bps,
            "h017_time": r.h017_time,
        })

    x = pd.DataFrame(rows).sort_values(
        ["block_id", "block_end_ts"]
    ).reset_index(drop=True)

    x["abs_vwap_disp_q60"] = (
        x.groupby("block_id", sort=False, observed=True)["vwap_displacement_bps"]
        .transform(
            lambda s: s.abs().shift(1).rolling(
                VWAP_REF, min_periods=VWAP_REF
            ).quantile(VWAP_Q)
        )
    )
    return x.sort_values(["group_key", "block_id"]).reset_index(drop=True)


def execute_first_per_session(
    features: pd.DataFrame,
    groups: dict[str, pd.DataFrame],
    hypothesis: str,
) -> pd.DataFrame:
    rows = []

    for key, f in features.groupby(
        "group_key", sort=False, observed=True
    ):
        g = groups.get(key)
        if g is None:
            continue

        candidates = []
        for r in f.sort_values("block_id").itertuples(index=False):
            direction = 0

            if hypothesis == "H077":
                bullish = (
                    r.block_close > r.block_open
                    and r.body_ratio >= BODY_RATIO_MIN
                    and r.clv >= CLV_UPPER
                )
                bearish = (
                    r.block_close < r.block_open
                    and r.body_ratio >= BODY_RATIO_MIN
                    and r.clv <= CLV_LOWER
                )
                if bullish:
                    direction = 1
                elif bearish:
                    direction = -1

            elif hypothesis == "H078":
                meaningful = (
                    pd.notna(r.abs_vwap_disp_q60)
                    and abs(r.vwap_displacement_bps)
                    >= r.abs_vwap_disp_q60
                )
                aligned = (
                    np.sign(r.block_return)
                    == np.sign(r.vwap_displacement_bps)
                    and r.block_return != 0
                    and r.vwap_displacement_bps != 0
                )
                if meaningful and aligned:
                    direction = 1 if r.vwap_displacement_bps > 0 else -1

            elif hypothesis == "H079":
                upper = (
                    r.upper_wick_ratio >= WICK_MIN
                    and r.block_close < r.block_open
                )
                lower = (
                    r.lower_wick_ratio >= WICK_MIN
                    and r.block_close > r.block_open
                )
                if upper:
                    direction = -1
                elif lower:
                    direction = 1
            else:
                raise ValueError(hypothesis)

            if direction == 0:
                continue

            signal_pos = int(r.signal_pos)
            signal_bar = g.iloc[signal_pos]

            # End-of-bar timestamp is the actual next-bar entry clock boundary.
            signal_minute = (
                signal_bar["timestamp_et"].hour * 60
                + signal_bar["timestamp_et"].minute
            )
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
            candidates.append(rec)

        if candidates:
            rows.append(
                min(candidates, key=lambda z: z["entry_clock_et"])
            )

    if not rows:
        return pd.DataFrame()
    return (
        pd.DataFrame(rows)
        .sort_values("entry_clock_et")
        .reset_index(drop=True)
    )


def horizon_metrics(h: str, trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        pnl = trades[f"net_pnl_{horizon}"]
        gross = trades[f"gross_pnl_{horizon}"]
        rows.append({
            "hypothesis": h,
            "horizon_minutes": horizon,
            "trades": int(len(trades)),
            "gross_pnl_usd": float(gross.sum()),
            "net_pnl_usd": float(pnl.sum()),
            "gross_expectancy_usd": float(gross.mean()),
            "net_expectancy_usd": float(pnl.mean()),
            "profit_factor": profit_factor(pnl),
            "win_rate": float((pnl > 0).mean()),
            "max_drawdown_usd": max_drawdown(pnl),
        })
    return pd.DataFrame(rows)


def primary_summary(
    h: str,
    trades: pd.DataFrame,
    min_n: int,
) -> tuple[dict, pd.DataFrame]:
    pnl = trades[f"net_pnl_{PRIMARY_HORIZON}"]
    stats = clustered_mean_stats(pnl, trades["session_date"])

    yearly = (
        trades.groupby("year", observed=True)
        .agg(
            trades=(f"net_pnl_{PRIMARY_HORIZON}", "size"),
            net_pnl_usd=(f"net_pnl_{PRIMARY_HORIZON}", "sum"),
            expectancy_usd=(f"net_pnl_{PRIMARY_HORIZON}", "mean"),
        )
        .reset_index()
    )

    return {
        "hypothesis": h,
        "trades": int(len(trades)),
        "sessions": int(trades["session_date"].nunique()),
        "net_pnl_usd": float(pnl.sum()),
        "expectancy_usd": float(pnl.mean()),
        "profit_factor": profit_factor(pnl),
        "win_rate": float((pnl > 0).mean()),
        "max_drawdown_usd": max_drawdown(pnl),
        "avg_mfe30_usd": float(trades["mfe30_usd"].mean()),
        "avg_mae30_usd": float(trades["mae30_usd"].mean()),
        "years_positive": int((yearly["expectancy_usd"] > 0).sum()),
        "years_observed": int(yearly["year"].nunique()),
        "min_n_gate": min_n,
        **stats,
    }, yearly


def side_breakdown(h, trades):
    x = (
        trades.groupby("side", observed=True)
        .agg(
            trades=(f"net_pnl_{PRIMARY_HORIZON}", "size"),
            expectancy_usd=(f"net_pnl_{PRIMARY_HORIZON}", "mean"),
            net_pnl_usd=(f"net_pnl_{PRIMARY_HORIZON}", "sum"),
            win_rate=(
                f"net_pnl_{PRIMARY_HORIZON}",
                lambda s: float((s > 0).mean()),
            ),
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
    p.add_argument("--output-dir", default="results/B13")
    a = p.parse_args()

    raw = parse_raw(pd.read_parquet(a.input))
    _, groups = prepare_rth(raw)
    feats = block_features(raw, groups)

    t77 = execute_first_per_session(feats, groups, "H077")
    t78 = execute_first_per_session(feats, groups, "H078")
    t79 = execute_first_per_session(feats, groups, "H079")

    architectures = [
        ("H077", t77, 150),
        ("H078", t78, 150),
        ("H079", t79, 100),
    ]

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    yearly_parts = []
    horizon_parts = []
    side_parts = []

    for h, trades, min_n in architectures:
        if trades.empty:
            rows.append({
                "hypothesis": h,
                "trades": 0,
                "sessions": 0,
                "net_pnl_usd": 0.0,
                "expectancy_usd": np.nan,
                "profit_factor": np.nan,
                "win_rate": np.nan,
                "max_drawdown_usd": np.nan,
                "avg_mfe30_usd": np.nan,
                "avg_mae30_usd": np.nan,
                "years_positive": 0,
                "years_observed": 0,
                "min_n_gate": min_n,
                "mean": np.nan,
                "clustered_se": np.nan,
                "t_stat": np.nan,
                "p_value": np.nan,
                "ci_low": np.nan,
                "ci_high": np.nan,
            })
            continue

        row, yearly = primary_summary(h, trades, min_n)
        rows.append(row)
        yearly["hypothesis"] = h
        yearly_parts.append(yearly)
        horizon_parts.append(horizon_metrics(h, trades))
        side_parts.append(side_breakdown(h, trades))
        trades.to_parquet(out / f"{h}_trades.parquet", index=False)

    summary = pd.DataFrame(rows)
    summary["q_value_bh"] = benjamini_hochberg(summary["p_value"])
    summary["passes_architecture_gate"] = (
        (summary["trades"] >= summary["min_n_gate"])
        & (summary["sessions"] >= summary["min_n_gate"])
        & (summary["expectancy_usd"] >= 1.0)
        & (summary["ci_low"] > 0)
        & (summary["p_value"] < 0.05)
        & (summary["q_value_bh"] < 0.05)
        & (summary["profit_factor"] >= 1.15)
        & (summary["net_pnl_usd"] > 0)
        & (summary["years_observed"] == 6)
        & (summary["years_positive"] >= 4)
    )

    summary.to_csv(out / "B13_SUMMARY.csv", index=False)
    feats.to_parquet(out / "high_block_features.parquet", index=False)

    if yearly_parts:
        pd.concat(yearly_parts, ignore_index=True).to_csv(
            out / "yearly.csv", index=False
        )
    if horizon_parts:
        pd.concat(horizon_parts, ignore_index=True).to_csv(
            out / "horizon_metrics.csv", index=False
        )
    if side_parts:
        pd.concat(side_parts, ignore_index=True).to_csv(
            out / "side_breakdown.csv", index=False
        )

    print(summary.to_string(index=False))
    if horizon_parts:
        print("\nHorizon metrics")
        print(pd.concat(horizon_parts, ignore_index=True).to_string(index=False))
    if side_parts:
        print("\nSide breakdown")
        print(pd.concat(side_parts, ignore_index=True).to_string(index=False))


if __name__ == "__main__":
    main()
