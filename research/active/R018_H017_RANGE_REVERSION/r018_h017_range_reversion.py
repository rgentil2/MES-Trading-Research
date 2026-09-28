from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import clustered_mean_stats, prepare_rth_features

REF = 60
RV_Q = 0.10
H017_START = 10 * 60 + 1
ENTRY_CUTOFF = 11 * 60 + 30
ACTIVE_MINUTES = 30

EDGE_LOW = 0.10
EDGE_HIGH = 0.90
HORIZON = 15

MES_POINT_VALUE = 5.0
COST_RT = 4.38


def enrich(raw: pd.DataFrame) -> pd.DataFrame:
    d = prepare_rth_features(
        raw,
        "2020-01-01",
        "2025-12-31",
        horizons=[15],
    ).reset_index(drop=True)
    g = d.groupby("group_key", sort=False, observed=True)

    prev_close = g["close"].shift(1)
    prev_ts = g["timestamp_et"].shift(1)
    exact1 = (d["timestamp_et"] - prev_ts) == pd.Timedelta(minutes=1)
    d["r1"] = np.where(exact1, np.log(d["close"] / prev_close), np.nan)

    lag30 = g["timestamp_et"].shift(30)
    exact30 = ((d["timestamp_et"] - lag30) == pd.Timedelta(minutes=30)).fillna(False)
    rv30 = (
        d.groupby("group_key", sort=False, observed=True)["r1"]
        .rolling(30, min_periods=30)
        .apply(lambda x: float(np.sqrt(np.square(x).sum()) * 10000.0), raw=True)
        .reset_index(level=0, drop=True)
    )
    d["rv30"] = np.where(exact30, rv30, np.nan)

    lag14 = g["timestamp_et"].shift(14)
    exact15range = ((d["timestamp_et"] - lag14) == pd.Timedelta(minutes=14)).fillna(False)
    hi15 = (
        d.groupby("group_key", sort=False, observed=True)["high"]
        .rolling(15, min_periods=15).max().reset_index(level=0, drop=True)
    )
    lo15 = (
        d.groupby("group_key", sort=False, observed=True)["low"]
        .rolling(15, min_periods=15).min().reset_index(level=0, drop=True)
    )
    d["range_high15"] = np.where(exact15range, hi15, np.nan)
    d["range_low15"] = np.where(exact15range, lo15, np.nan)
    width = d["range_high15"] - d["range_low15"]
    d["range_position"] = np.where(
        width > 0,
        (d["close"] - d["range_low15"]) / width,
        np.nan,
    )

    d["entry_open"] = g["open"].shift(-1)
    d["entry_ts"] = g["timestamp_et"].shift(-1)
    d["entry_exact"] = (
        (d["entry_ts"] - d["timestamp_et"]) == pd.Timedelta(minutes=1)
    ).fillna(False)

    d["exit_close"] = g["close"].shift(-HORIZON)
    d["exit_ts"] = g["timestamp_et"].shift(-HORIZON)
    d["exit_exact"] = (
        (d["exit_ts"] - d["timestamp_et"]) == pd.Timedelta(minutes=HORIZON)
    ).fillna(False)

    d["minute"] = d["timestamp_et"].dt.hour * 60 + d["timestamp_et"].dt.minute
    d.sort_values(["minute", "timestamp_et"], inplace=True)
    d["rv_threshold"] = d.groupby(
        "minute", sort=False, observed=True
    )["rv30"].transform(
        lambda s: s.shift(1).rolling(
            REF,
            min_periods=REF,
        ).quantile(RV_Q)
    )
    d.sort_values("timestamp_et", inplace=True)
    return d.reset_index(drop=True)


def build_regimes(d: pd.DataFrame) -> pd.DataFrame:
    eligible = (
        (d["minute"] >= H017_START)
        & (d["minute"] <= ENTRY_CUTOFF)
        & d["rv30"].notna()
        & d["rv_threshold"].notna()
        & (d["rv30"] <= d["rv_threshold"])
    )
    c = d[eligible].copy()
    c.sort_values(["group_key", "timestamp_et"], inplace=True)
    e = c.groupby("group_key", sort=False, observed=True).head(1).copy()
    return e[["group_key", "timestamp_et"]].rename(
        columns={"timestamp_et": "h017_time"}
    )


def build_trades(d: pd.DataFrame, regimes: pd.DataFrame) -> pd.DataFrame:
    x = d.merge(regimes, on="group_key", how="inner", validate="many_to_one")
    active_end = x["h017_time"] + pd.Timedelta(minutes=ACTIVE_MINUTES)
    x["active_end"] = active_end

    eligible = (
        (x["timestamp_et"] >= x["h017_time"])
        & (x["timestamp_et"] <= x["active_end"])
        & (x["minute"] <= ENTRY_CUTOFF)
        & x["range_position"].notna()
        & x["entry_exact"].fillna(False)
        & x["exit_exact"].fillna(False)
        & x["entry_open"].notna()
        & x["exit_close"].notna()
    )

    edge = (
        (x["range_position"] >= EDGE_HIGH)
        | (x["range_position"] <= EDGE_LOW)
    )

    c = x[eligible & edge].copy()
    c.sort_values(["group_key", "timestamp_et"], inplace=True)
    e = c.groupby("group_key", sort=False, observed=True).head(1).copy()

    e["edge"] = np.where(
        e["range_position"] >= EDGE_HIGH,
        "UPPER_EDGE",
        "LOWER_EDGE",
    )
    e["direction"] = np.where(e["edge"] == "UPPER_EDGE", -1, 1)
    e["entry_price"] = e["entry_open"].astype(float)
    e["exit_price"] = e["exit_close"].astype(float)
    e["gross_pnl_usd"] = (
        e["direction"]
        * (e["exit_price"] - e["entry_price"])
        * MES_POINT_VALUE
    )
    e["net_pnl_usd"] = e["gross_pnl_usd"] - COST_RT

    keep = [
        "timestamp_et", "entry_ts", "exit_ts", "session_date", "year",
        "contract", "group_key", "h017_time", "edge", "direction",
        "range_position", "range_high15", "range_low15", "entry_price",
        "exit_price", "gross_pnl_usd", "net_pnl_usd",
    ]
    return e[keep].sort_values("timestamp_et").reset_index(drop=True)


def performance(trades: pd.DataFrame) -> dict:
    t = trades.sort_values("timestamp_et")
    pnl = t["net_pnl_usd"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gp = float(wins.sum())
    gl = float(-losses.sum())
    pf = gp / gl if gl > 0 else np.inf
    equity = pnl.cumsum()
    dd = equity.cummax() - equity

    stats = clustered_mean_stats(pnl, t["session_date"])

    yearly = (
        t.groupby("year", observed=True)
        .agg(
            trades=("net_pnl_usd", "size"),
            net_pnl_usd=("net_pnl_usd", "sum"),
            expectancy_usd=("net_pnl_usd", "mean"),
        )
        .reset_index()
    )

    return {
        "trades": int(len(t)),
        "sessions": int(t["session_date"].nunique()),
        "net_pnl_usd": float(pnl.sum()),
        "expectancy_usd": float(pnl.mean()),
        "profit_factor": float(pf),
        "win_rate": float((pnl > 0).mean()),
        "avg_win_usd": float(wins.mean()) if len(wins) else np.nan,
        "avg_loss_usd": float(losses.mean()) if len(losses) else np.nan,
        "max_drawdown_usd": float(dd.max()) if len(dd) else 0.0,
        **stats,
        "years_positive": int((yearly["expectancy_usd"] > 0).sum()),
        "years_observed": int(yearly["year"].nunique()),
    }, yearly


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet",
    )
    p.add_argument("--output-dir", default="results/R018")
    a = p.parse_args()

    raw = pd.read_parquet(a.input)
    d = enrich(raw)
    regimes = build_regimes(d)
    trades = build_trades(d, regimes)

    perf, yearly = performance(trades)
    summary = pd.DataFrame([{"hypothesis": "H027", **perf}])
    summary["passes_candidate_gate"] = (
        (summary["trades"] >= 200)
        & (summary["sessions"] >= 200)
        & (summary["expectancy_usd"] >= 1.0)
        & (summary["ci_low"] > 0)
        & (summary["p_value"] < 0.05)
        & (summary["profit_factor"] >= 1.15)
        & (summary["years_observed"] == 6)
        & (summary["years_positive"] >= 4)
        & (summary["net_pnl_usd"] > 0)
    )

    side = (
        trades.groupby("edge", observed=True)
        .agg(
            trades=("net_pnl_usd", "size"),
            net_pnl_usd=("net_pnl_usd", "sum"),
            expectancy_usd=("net_pnl_usd", "mean"),
            win_rate=("net_pnl_usd", lambda s: float((s > 0).mean())),
        )
        .reset_index()
    )

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    trades.to_parquet(out / "trades.parquet", index=False)
    regimes.to_parquet(out / "h017_regimes.parquet", index=False)
    summary.to_csv(out / "R018_SUMMARY.csv", index=False)
    yearly.to_csv(out / "yearly.csv", index=False)
    side.to_csv(out / "side_breakdown.csv", index=False)

    print(summary.to_string(index=False))
    print(yearly.to_string(index=False))
    print(side.to_string(index=False))


if __name__ == "__main__":
    main()
