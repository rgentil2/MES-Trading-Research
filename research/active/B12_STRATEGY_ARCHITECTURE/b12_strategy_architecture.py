from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import benjamini_hochberg, clustered_mean_stats, rth_mask
from research.active.R063_FINAL_REGIME_ENGINE.regime_engine_v1 import build_dynamic_outputs

MES_POINT_VALUE = 5.0
COMMISSION_RT = 1.88
SLIPPAGE_RT = 2.50
COST_RT = COMMISSION_RT + SLIPPAGE_RT

ENTRY_CUTOFF_MINUTE = 11 * 60 + 30
PULLBACK_MAX_BARS = 10
PRIMARY_HORIZON = 30
HORIZONS = (15, 30, 60)


def parse_raw(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.copy()
    d["timestamp_et"] = pd.to_datetime(
        d["timestamp_et"], utc=True
    ).dt.tz_convert("America/New_York")
    d.sort_values("timestamp_et", inplace=True)
    return d.reset_index(drop=True)


def prepare_rth(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    d = raw[rth_mask(raw["timestamp_et"])].copy()
    d["session_date"] = d["timestamp_et"].dt.date.astype(str)
    d["group_key"] = d["session_date"] + "|" + d["contract"].astype(str)
    d["year"] = d["timestamp_et"].dt.year
    d["minute"] = d["timestamp_et"].dt.hour * 60 + d["timestamp_et"].dt.minute
    d = d[(d["year"] >= 2020) & (d["year"] <= 2025)].copy()

    groups = {}
    keep = []
    for key, g in d.groupby("group_key", sort=False, observed=True):
        g = g.sort_values("timestamp_et").reset_index(drop=True)
        if len(g) != 390:
            continue
        if int(g["minute"].iloc[0]) != 571 or int(g["minute"].iloc[-1]) != 960:
            continue
        g["bar_pos"] = np.arange(len(g), dtype=int)
        groups[key] = g
        keep.append(g)

    return pd.concat(keep, ignore_index=True), groups


def build_block_map(raw: pd.DataFrame, groups: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dyn = build_dynamic_outputs(raw).copy()
    dyn = dyn[dyn["block_id"].between(0, 6)].copy()  # last usable block ends 11:15

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
        rows.append({
            "group_key": r.group_key,
            "session_date": r.session_date,
            "year": int(r.year),
            "contract": r.contract,
            "block_id": int(r.block_id),
            "block_end_ts": r.block_end_ts,
            "block_high": float(b["high"].max()),
            "block_low": float(b["low"].min()),
            "block_range_points": float(b["high"].max() - b["low"].min()),
            "raw_state": r.state,
            "engine_state": r.engine_state,
            "engine_stage": r.engine_stage,
            "h017_time": r.h017_time,
        })

    blocks = pd.DataFrame(rows).sort_values(
        ["group_key", "block_id"]
    ).reset_index(drop=True)

    blocks["prev_engine_state"] = (
        blocks.groupby("group_key", sort=False, observed=True)["engine_state"].shift(1)
    )
    return blocks


def h017_active(ts: pd.Timestamp, event_ts) -> bool:
    if pd.isna(event_ts):
        return False
    return bool(
        ts >= event_ts
        and ts <= event_ts + pd.Timedelta(minutes=30)
    )


def latest_engine_state(
    blocks_session: pd.DataFrame,
    ts: pd.Timestamp,
    h017_time,
) -> str | float:
    if h017_active(ts, h017_time):
        return "LOW"
    done = blocks_session[blocks_session["block_end_ts"] <= ts]
    if done.empty:
        return np.nan
    return done.iloc[-1]["engine_state"]


def first_breakout(
    g: pd.DataFrame,
    block_row,
) -> dict | None:
    block_end = block_row.block_end_ts
    next_block_end = block_end + pd.Timedelta(minutes=15)

    window = g[
        (g["timestamp_et"] > block_end)
        & (g["timestamp_et"] < next_block_end)
        & (g["minute"] <= ENTRY_CUTOFF_MINUTE)
    ].copy()

    for _, bar in window.iterrows():
        if h017_active(bar["timestamp_et"], block_row.h017_time):
            continue
        direction = 0
        ref_level = np.nan
        if float(bar["close"]) > float(block_row.block_high):
            direction = 1
            ref_level = float(block_row.block_high)
        elif float(bar["close"]) < float(block_row.block_low):
            direction = -1
            ref_level = float(block_row.block_low)

        if direction == 0:
            continue

        pos = int(bar["bar_pos"])
        if pos + 1 >= len(g):
            return None

        next_bar = g.iloc[pos + 1]
        if (
            next_bar["contract"] != bar["contract"]
            or next_bar["session_date"] != bar["session_date"]
            or next_bar["timestamp_et"] - bar["timestamp_et"] != pd.Timedelta(minutes=1)
        ):
            return None

        # With end-of-bar timestamps, next bar Open occurs at the signal timestamp boundary.
        if int(bar["minute"]) > ENTRY_CUTOFF_MINUTE:
            return None

        return {
            "breakout_signal_ts": bar["timestamp_et"],
            "breakout_signal_pos": pos,
            "breakout_signal_close": float(bar["close"]),
            "direction": direction,
            "reference_level": ref_level,
            "breakout_distance_points": float(
                direction * (float(bar["close"]) - ref_level)
            ),
        }
    return None


def trade_from_signal(
    g: pd.DataFrame,
    signal_pos: int,
    direction: int,
) -> dict | None:
    if signal_pos + 1 >= len(g):
        return None

    entry_bar = g.iloc[signal_pos + 1]
    signal_bar = g.iloc[signal_pos]

    if entry_bar["timestamp_et"] - signal_bar["timestamp_et"] != pd.Timedelta(minutes=1):
        return None

    entry_price = float(entry_bar["open"])
    if entry_price <= 0:
        return None

    out = {
        "entry_bar_ts": entry_bar["timestamp_et"],
        "entry_clock_et": signal_bar["timestamp_et"],
        "entry_price": entry_price,
    }

    for h in HORIZONS:
        exit_pos = signal_pos + h
        if exit_pos >= len(g):
            return None
        exit_bar = g.iloc[exit_pos]
        if exit_bar["timestamp_et"] - signal_bar["timestamp_et"] != pd.Timedelta(minutes=h):
            return None
        exit_price = float(exit_bar["close"])
        gross = direction * (exit_price - entry_price) * MES_POINT_VALUE
        out[f"exit_ts_{h}"] = exit_bar["timestamp_et"]
        out[f"exit_price_{h}"] = exit_price
        out[f"gross_pnl_{h}"] = gross
        out[f"net_pnl_{h}"] = gross - COST_RT

    # MFE / MAE during the first 30 minutes after entry.
    path = g.iloc[signal_pos + 1 : signal_pos + 31]
    if len(path) != 30:
        return None
    if direction == 1:
        mfe_points = float(path["high"].max() - entry_price)
        mae_points = float(entry_price - path["low"].min())
    else:
        mfe_points = float(entry_price - path["low"].min())
        mae_points = float(path["high"].max() - entry_price)

    out["mfe30_points"] = mfe_points
    out["mae30_points"] = mae_points
    out["mfe30_usd"] = mfe_points * MES_POINT_VALUE
    out["mae30_usd"] = mae_points * MES_POINT_VALUE
    return out


def direct_candidates(
    blocks: pd.DataFrame,
    groups: dict[str, pd.DataFrame],
    transition_only: bool = False,
) -> pd.DataFrame:
    rows = []

    eligible = blocks[blocks["engine_state"] == "HIGH"].copy()
    if transition_only:
        eligible = eligible[eligible["prev_engine_state"] == "NORMAL"].copy()

    block_by_session = {
        k: g.sort_values("block_id")
        for k, g in blocks.groupby("group_key", sort=False, observed=True)
    }

    for key, bs in eligible.groupby("group_key", sort=False, observed=True):
        g = groups.get(key)
        if g is None:
            continue

        session_trades = []
        for b in bs.itertuples(index=False):
            # H017 override at block close would already make engine_state LOW.
            br = first_breakout(g, b)
            if br is None:
                continue

            # If H017 starts at breakout, no trade.
            if h017_active(br["breakout_signal_ts"], b.h017_time):
                continue

            tr = trade_from_signal(
                g,
                br["breakout_signal_pos"],
                br["direction"],
            )
            if tr is None:
                continue

            rec = {
                "group_key": key,
                "session_date": b.session_date,
                "year": int(b.year),
                "contract": b.contract,
                "block_id": int(b.block_id),
                "block_end_ts": b.block_end_ts,
                "block_high": float(b.block_high),
                "block_low": float(b.block_low),
                "block_range_points": float(b.block_range_points),
                "prev_engine_state": b.prev_engine_state,
                "engine_state": b.engine_state,
                "h017_time": b.h017_time,
                **br,
                **tr,
            }
            rec["side"] = "LONG" if rec["direction"] == 1 else "SHORT"
            session_trades.append(rec)

        if session_trades:
            rows.append(
                min(session_trades, key=lambda x: x["breakout_signal_ts"])
            )

    return pd.DataFrame(rows).sort_values("breakout_signal_ts").reset_index(drop=True)


def pullback_candidates(
    blocks: pd.DataFrame,
    groups: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    block_by_session = {
        k: g.sort_values("block_id").reset_index(drop=True)
        for k, g in blocks.groupby("group_key", sort=False, observed=True)
    }

    for key, bs in blocks[blocks["engine_state"] == "HIGH"].groupby(
        "group_key", sort=False, observed=True
    ):
        g = groups.get(key)
        all_blocks = block_by_session.get(key)
        if g is None or all_blocks is None:
            continue

        session_trades = []

        for b in bs.itertuples(index=False):
            br = first_breakout(g, b)
            if br is None:
                continue

            start = br["breakout_signal_pos"] + 1
            stop = min(start + PULLBACK_MAX_BARS, len(g))
            invalid = False

            for pos in range(start, stop):
                bar = g.iloc[pos]
                if int(bar["minute"]) > ENTRY_CUTOFF_MINUTE:
                    break

                # A new block state or H017 can invalidate the HIGH architecture.
                current_state = latest_engine_state(
                    all_blocks,
                    bar["timestamp_et"],
                    b.h017_time,
                )
                if current_state != "HIGH":
                    invalid = True
                    break

                if br["direction"] == 1:
                    if float(bar["close"]) < float(b.block_low):
                        invalid = True
                        break
                    retest = (
                        float(bar["low"]) <= float(br["reference_level"])
                        and float(bar["close"]) >= float(br["reference_level"])
                    )
                else:
                    if float(bar["close"]) > float(b.block_high):
                        invalid = True
                        break
                    retest = (
                        float(bar["high"]) >= float(br["reference_level"])
                        and float(bar["close"]) <= float(br["reference_level"])
                    )

                if not retest:
                    continue

                tr = trade_from_signal(g, pos, br["direction"])
                if tr is None:
                    invalid = True
                    break

                rec = {
                    "group_key": key,
                    "session_date": b.session_date,
                    "year": int(b.year),
                    "contract": b.contract,
                    "block_id": int(b.block_id),
                    "block_end_ts": b.block_end_ts,
                    "block_high": float(b.block_high),
                    "block_low": float(b.block_low),
                    "block_range_points": float(b.block_range_points),
                    "engine_state": b.engine_state,
                    "h017_time": b.h017_time,
                    **br,
                    "pullback_signal_ts": bar["timestamp_et"],
                    "pullback_signal_pos": pos,
                    "pullback_delay_bars": int(pos - br["breakout_signal_pos"]),
                    **tr,
                }
                rec["side"] = "LONG" if rec["direction"] == 1 else "SHORT"
                session_trades.append(rec)
                break

            if invalid:
                continue

        if session_trades:
            rows.append(
                min(session_trades, key=lambda x: x["entry_clock_et"])
            )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("entry_clock_et").reset_index(drop=True)


def profit_factor(pnl: pd.Series) -> float:
    wins = float(pnl[pnl > 0].sum())
    losses = float(-pnl[pnl < 0].sum())
    if losses == 0:
        return np.inf if wins > 0 else np.nan
    return wins / losses


def max_drawdown(pnl: pd.Series) -> float:
    eq = pnl.cumsum()
    peak = eq.cummax().clip(lower=0)
    return float((peak - eq).max()) if len(eq) else np.nan


def horizon_metrics(h: str, trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        pnl_col = f"net_pnl_{horizon}"
        gross_col = f"gross_pnl_{horizon}"
        pnl = trades[pnl_col] if len(trades) else pd.Series(dtype=float)
        rows.append({
            "hypothesis": h,
            "horizon_minutes": horizon,
            "trades": int(len(trades)),
            "gross_pnl_usd": float(trades[gross_col].sum()) if len(trades) else 0.0,
            "net_pnl_usd": float(pnl.sum()) if len(trades) else 0.0,
            "gross_expectancy_usd": float(trades[gross_col].mean()) if len(trades) else np.nan,
            "net_expectancy_usd": float(pnl.mean()) if len(trades) else np.nan,
            "profit_factor": profit_factor(pnl),
            "win_rate": float((pnl > 0).mean()) if len(trades) else np.nan,
            "max_drawdown_usd": max_drawdown(pnl),
        })
    return pd.DataFrame(rows)


def primary_summary(h: str, trades: pd.DataFrame, min_n: int) -> tuple[dict, pd.DataFrame]:
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

    row = {
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
    }
    return row, yearly


def descriptive_breakdowns(h: str, trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    side = (
        trades.groupby("side", observed=True)
        .agg(
            trades=(f"net_pnl_{PRIMARY_HORIZON}", "size"),
            expectancy_usd=(f"net_pnl_{PRIMARY_HORIZON}", "mean"),
            net_pnl_usd=(f"net_pnl_{PRIMARY_HORIZON}", "sum"),
            win_rate=(f"net_pnl_{PRIMARY_HORIZON}", lambda x: float((x > 0).mean())),
        )
        .reset_index()
    )
    side["hypothesis"] = h

    x = trades.copy()
    time_col = "entry_clock_et"
    x["entry_hour"] = x[time_col].dt.strftime("%H:%M")
    timing = (
        x.groupby("entry_hour", observed=True)
        .agg(
            trades=(f"net_pnl_{PRIMARY_HORIZON}", "size"),
            expectancy_usd=(f"net_pnl_{PRIMARY_HORIZON}", "mean"),
        )
        .reset_index()
    )
    timing["hypothesis"] = h
    return side, timing


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet",
    )
    p.add_argument("--output-dir", default="results/B12")
    a = p.parse_args()

    raw = parse_raw(pd.read_parquet(a.input))
    _, groups = prepare_rth(raw)
    blocks = build_block_map(raw, groups)

    t74 = direct_candidates(blocks, groups, transition_only=False)
    t75 = pullback_candidates(blocks, groups)
    t76 = direct_candidates(blocks, groups, transition_only=True)

    architectures = [
        ("H074", t74, 200),
        ("H075", t75, 120),
        ("H076", t76, 120),
    ]

    rows = []
    yearly_parts = []
    horizon_parts = []
    side_parts = []
    timing_parts = []

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for h, trades, min_n in architectures:
        if trades.empty:
            # Keep schema failure explicit rather than silently inventing stats.
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

        side, timing = descriptive_breakdowns(h, trades)
        side_parts.append(side)
        timing_parts.append(timing)

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

    summary.to_csv(out / "B12_SUMMARY.csv", index=False)
    if yearly_parts:
        pd.concat(yearly_parts, ignore_index=True).to_csv(out / "yearly.csv", index=False)
    if horizon_parts:
        pd.concat(horizon_parts, ignore_index=True).to_csv(out / "horizon_metrics.csv", index=False)
    if side_parts:
        pd.concat(side_parts, ignore_index=True).to_csv(out / "side_breakdown.csv", index=False)
    if timing_parts:
        pd.concat(timing_parts, ignore_index=True).to_csv(out / "entry_time_breakdown.csv", index=False)

    blocks.to_parquet(out / "dynamic_blocks.parquet", index=False)

    print(summary.to_string(index=False))
    if horizon_parts:
        print("\nHorizon metrics")
        print(pd.concat(horizon_parts, ignore_index=True).to_string(index=False))
    if side_parts:
        print("\nSide breakdown")
        print(pd.concat(side_parts, ignore_index=True).to_string(index=False))


if __name__ == "__main__":
    main()
