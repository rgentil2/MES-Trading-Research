from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.research_utils import benjamini_hochberg, prepare_rth_features

H017_REF = 60
H017_Q = 0.10
H017_START = 10 * 60 + 1
ENTRY_CUTOFF = 11 * 60 + 30
H017_ACTIVE_MINUTES = 30

VOLUME_REF = 60
VOLUME_Q = 0.80
ER5_MIN = 0.70

MES_POINT_VALUE = 5.0
COMMISSION_RT = 1.88
SLIPPAGE_RT = 2.50
COST_RT = COMMISSION_RT + SLIPPAGE_RT


def enrich_features(raw: pd.DataFrame) -> pd.DataFrame:
    d = prepare_rth_features(
        raw,
        "2020-01-01",
        "2025-12-31",
        horizons=[15, 30],
    ).reset_index(drop=True)

    g = d.groupby("group_key", sort=False, observed=True)

    d["entry_open"] = g["open"].shift(-1)
    d["entry_ts"] = g["timestamp_et"].shift(-1)
    d["entry_exact_1m"] = (
        (d["entry_ts"] - d["timestamp_et"]) == pd.Timedelta(minutes=1)
    ).fillna(False)

    for h in (15, 30):
        d[f"exit_close_{h}"] = g["close"].shift(-h)
        d[f"exit_ts_{h}"] = g["timestamp_et"].shift(-h)
        d[f"exit_exact_{h}m"] = (
            (d[f"exit_ts_{h}"] - d["timestamp_et"])
            == pd.Timedelta(minutes=h)
        ).fillna(False)

    prev_close = g["close"].shift(1)
    prev_ts = g["timestamp_et"].shift(1)
    exact1 = (d["timestamp_et"] - prev_ts) == pd.Timedelta(minutes=1)
    d["r1"] = np.where(exact1, np.log(d["close"] / prev_close), np.nan)

    lag_ts30 = g["timestamp_et"].shift(30)
    exact_hist30 = (
        (d["timestamp_et"] - lag_ts30) == pd.Timedelta(minutes=30)
    ).fillna(False)
    rv30 = (
        d.groupby("group_key", sort=False, observed=True)["r1"]
        .rolling(30, min_periods=30)
        .apply(lambda x: float(np.sqrt(np.square(x).sum()) * 10000.0), raw=True)
        .reset_index(level=0, drop=True)
    )
    d["rv30"] = np.where(exact_hist30, rv30, np.nan)

    lag_close5 = g["close"].shift(5)
    lag_ts5 = g["timestamp_et"].shift(5)
    exact_hist5 = (
        (d["timestamp_et"] - lag_ts5) == pd.Timedelta(minutes=5)
    ).fillna(False)
    d["r5"] = np.where(exact_hist5, np.log(d["close"] / lag_close5), np.nan)

    d["v5"] = (
        d.groupby("group_key", sort=False, observed=True)["volume"]
        .rolling(5, min_periods=5)
        .sum()
        .reset_index(level=0, drop=True)
    )
    d["v5"] = np.where(exact_hist5, d["v5"], np.nan)

    path5 = (
        d.groupby("group_key", sort=False, observed=True)["r1"]
        .rolling(5, min_periods=5)
        .apply(lambda x: float(np.abs(x).sum()), raw=True)
        .reset_index(level=0, drop=True)
    )
    d["er5"] = np.where(
        exact_hist5 & (path5 > 0),
        np.abs(d["r5"]) / path5,
        np.nan,
    )

    d["minute"] = d["timestamp_et"].dt.hour * 60 + d["timestamp_et"].dt.minute

    d.sort_values(["minute", "timestamp_et"], inplace=True)
    by_minute = d.groupby("minute", sort=False, observed=True)

    d["h017_threshold"] = by_minute["rv30"].transform(
        lambda s: s.shift(1).rolling(
            H017_REF,
            min_periods=H017_REF,
        ).quantile(H017_Q)
    )
    d["v5_threshold"] = by_minute["v5"].transform(
        lambda s: s.shift(1).rolling(
            VOLUME_REF,
            min_periods=VOLUME_REF,
        ).quantile(VOLUME_Q)
    )

    d.sort_values("timestamp_et", inplace=True)
    return d.reset_index(drop=True)


def build_h017_regimes(d: pd.DataFrame) -> pd.DataFrame:
    eligible = (
        (d["minute"] >= H017_START)
        & (d["minute"] <= ENTRY_CUTOFF)
        & d["rv30"].notna()
        & d["h017_threshold"].notna()
        & (d["rv30"] <= d["h017_threshold"])
    )
    c = d[eligible].copy()
    c.sort_values(["group_key", "timestamp_et"], inplace=True)
    e = c.groupby("group_key", sort=False, observed=True).head(1).copy()
    return e[["group_key", "session_date", "timestamp_et"]].rename(
        columns={"timestamp_et": "h017_time"}
    )


def executable_trades(events: pd.DataFrame, horizon: int, strategy: str) -> pd.DataFrame:
    e = events[
        events["entry_exact_1m"].fillna(False)
        & events[f"exit_exact_{horizon}m"].fillna(False)
        & events["entry_open"].notna()
        & events[f"exit_close_{horizon}"].notna()
    ].copy()

    e["strategy"] = strategy
    e["horizon_min"] = horizon
    e["entry_price"] = e["entry_open"].astype(float)
    e["exit_price"] = e[f"exit_close_{horizon}"].astype(float)
    e["gross_pnl_usd"] = (
        e["direction"]
        * (e["exit_price"] - e["entry_price"])
        * MES_POINT_VALUE
    )
    e["net_pnl_usd"] = e["gross_pnl_usd"] - COST_RT

    keep = [
        "strategy", "timestamp_et", "entry_ts", f"exit_ts_{horizon}",
        "session_date", "year", "contract", "group_key", "direction",
        "horizon_min", "entry_price", "exit_price", "gross_pnl_usd", "net_pnl_usd",
    ]
    return e[keep].rename(columns={f"exit_ts_{horizon}": "exit_ts"}).sort_values("timestamp_et").reset_index(drop=True)


def build_orb_signals(d: pd.DataFrame) -> pd.DataFrame:
    opening = d[d["bar_index"] < 15].copy()
    stats = opening.groupby("group_key", sort=False, observed=True).agg(
        or_high=("high", "max"), or_low=("low", "min"), count=("timestamp_et", "size"),
        first_ts=("timestamp_et", "min"), last_ts=("timestamp_et", "max"),
    ).reset_index()
    stats["valid"] = (
        (stats["count"] == 15)
        & ((stats["first_ts"].dt.hour * 60 + stats["first_ts"].dt.minute) == 571)
        & ((stats["last_ts"].dt.hour * 60 + stats["last_ts"].dt.minute) == 585)
        & ((stats["last_ts"] - stats["first_ts"]) == pd.Timedelta(minutes=14))
    )
    x = d.merge(stats[["group_key","or_high","or_low","valid"]], on="group_key", how="left", validate="many_to_one")
    outside = (x["close"] > x["or_high"]) | (x["close"] < x["or_low"])
    c = x[x["valid"].fillna(False) & (x["bar_index"] >= 15) & (x["minute"] <= ENTRY_CUTOFF) & outside].copy()
    c.sort_values(["group_key","timestamp_et"], inplace=True)
    e = c.groupby("group_key", sort=False, observed=True).head(1).copy()
    e["direction"] = np.where(e["close"] > e["or_high"], 1, -1)
    return executable_trades(e, 30, "S1_ORB")


def add_previous_levels(d: pd.DataFrame) -> pd.DataFrame:
    sessions = d.groupby("group_key", sort=False, observed=True).agg(
        contract=("contract","first"), session_first=("timestamp_et","min"),
        high=("high","max"), low=("low","min"),
    ).sort_values("session_first").reset_index()
    sessions["prev_contract"] = sessions["contract"].shift(1)
    sessions["pdh"] = sessions["high"].shift(1)
    sessions["pdl"] = sessions["low"].shift(1)
    same = sessions["contract"] == sessions["prev_contract"]
    sessions.loc[~same, ["pdh","pdl"]] = np.nan
    return d.merge(sessions[["group_key","pdh","pdl"]], on="group_key", how="left", validate="many_to_one")


def build_previous_level_signals(d: pd.DataFrame) -> pd.DataFrame:
    x = add_previous_levels(d)
    eligible = (x["minute"] >= 571) & (x["minute"] <= ENTRY_CUTOFF) & x["pdh"].notna() & x["pdl"].notna()
    outside = (x["close"] > x["pdh"]) | (x["close"] < x["pdl"])
    c = x[eligible & outside].copy()
    c.sort_values(["group_key","timestamp_et"], inplace=True)
    e = c.groupby("group_key", sort=False, observed=True).head(1).copy()
    e["direction"] = np.where(e["close"] > e["pdh"], 1, -1)
    return executable_trades(e, 30, "S2_PREV_LEVEL")


def build_volume_impulse_signals(d: pd.DataFrame) -> pd.DataFrame:
    eligible = (
        (d["minute"] >= 576) & (d["minute"] <= ENTRY_CUTOFF)
        & d["r5"].notna() & d["er5"].notna() & d["v5_threshold"].notna()
    )
    signal = (d["v5"] >= d["v5_threshold"]) & (d["er5"] >= ER5_MIN) & (d["r5"] != 0)
    c = d[eligible & signal].copy()
    c.sort_values(["group_key","timestamp_et"], inplace=True)
    e = c.groupby("group_key", sort=False, observed=True).head(1).copy()
    e["direction"] = np.sign(e["r5"]).astype(int)
    return executable_trades(e, 15, "S3_VOLUME_IMPULSE")


def mark_h017(trades: pd.DataFrame, regimes: pd.DataFrame) -> pd.DataFrame:
    e = trades.merge(regimes[["group_key","h017_time"]], on="group_key", how="left", validate="many_to_one")
    e["inside_h017"] = (
        e["h017_time"].notna()
        & (e["timestamp_et"] >= e["h017_time"])
        & (e["timestamp_et"] <= e["h017_time"] + pd.Timedelta(minutes=H017_ACTIVE_MINUTES))
    )
    return e


def perf(trades: pd.DataFrame) -> dict:
    t = trades.sort_values("timestamp_et").copy()
    pnl = t["net_pnl_usd"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else np.inf
    equity = pnl.cumsum()
    running_max = equity.cummax()
    dd = running_max - equity
    return {
        "trades": int(len(t)),
        "net_pnl_usd": float(pnl.sum()) if len(t) else 0.0,
        "expectancy_usd": float(pnl.mean()) if len(t) else np.nan,
        "profit_factor": float(pf),
        "win_rate": float((pnl > 0).mean()) if len(t) else np.nan,
        "avg_win_usd": float(wins.mean()) if len(wins) else np.nan,
        "avg_loss_usd": float(losses.mean()) if len(losses) else np.nan,
        "max_drawdown_usd": float(dd.max()) if len(dd) else 0.0,
    }


def filter_delta_stats(trades: pd.DataFrame) -> dict:
    frame = trades[["net_pnl_usd","inside_h017","session_date"]].dropna().copy()
    if len(frame) < 4 or frame["inside_h017"].nunique() < 2 or frame["session_date"].nunique() < 2:
        return {"filter_delta_usd":np.nan,"clustered_se":np.nan,"t_stat":np.nan,"p_value":np.nan,"ci_low":np.nan,"ci_high":np.nan}
    y = frame["net_pnl_usd"].to_numpy(float)
    inside = frame["inside_h017"].astype(int).to_numpy(float)
    x = sm.add_constant(inside)
    result = sm.OLS(y, x).fit(cov_type="cluster", cov_kwds={"groups":frame["session_date"].to_numpy()})
    b = float(result.params[1]); ci = result.conf_int(alpha=0.05)[1]
    return {
        "filter_delta_usd": -b,
        "clustered_se": float(result.bse[1]),
        "t_stat": float(-result.tvalues[1]),
        "p_value": float(result.pvalues[1]),
        "ci_low": float(-ci[1]),
        "ci_high": float(-ci[0]),
    }


def evaluate_strategy(trades: pd.DataFrame, hypothesis: str):
    all_perf = perf(trades)
    inside = trades[trades["inside_h017"]].copy()
    filtered = trades[~trades["inside_h017"]].copy()
    inside_perf = perf(inside)
    filt_perf = perf(filtered)
    stats = filter_delta_stats(trades)

    row = {
        "hypothesis":hypothesis,
        "strategy":trades["strategy"].iloc[0] if len(trades) else "",
        "total_trades":all_perf["trades"],
        "inside_trades":inside_perf["trades"],
        "filtered_trades":filt_perf["trades"],
        "baseline_net_pnl_usd":all_perf["net_pnl_usd"],
        "baseline_expectancy_usd":all_perf["expectancy_usd"],
        "baseline_pf":all_perf["profit_factor"],
        "baseline_max_dd_usd":all_perf["max_drawdown_usd"],
        "inside_expectancy_usd":inside_perf["expectancy_usd"],
        "inside_pf":inside_perf["profit_factor"],
        "filtered_net_pnl_usd":filt_perf["net_pnl_usd"],
        "filtered_expectancy_usd":filt_perf["expectancy_usd"],
        "filtered_pf":filt_perf["profit_factor"],
        "filtered_max_dd_usd":filt_perf["max_drawdown_usd"],
        "expectancy_improvement_usd":filt_perf["expectancy_usd"]-all_perf["expectancy_usd"],
        "pf_improvement":filt_perf["profit_factor"]-all_perf["profit_factor"],
        **stats,
    }
    yearly = trades.assign(version=np.where(trades["inside_h017"],"INSIDE_H017","FILTERED")).groupby(
        ["year","version"], observed=True
    ).agg(trades=("net_pnl_usd","size"),net_pnl_usd=("net_pnl_usd","sum"),expectancy_usd=("net_pnl_usd","mean")).reset_index()
    yearly["hypothesis"] = hypothesis
    return row, yearly


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir",default="results/R017")
    a=p.parse_args()

    raw=pd.read_parquet(a.input)
    d=enrich_features(raw)
    regimes=build_h017_regimes(d)

    strategies=[
        ("H024",mark_h017(build_orb_signals(d),regimes)),
        ("H025",mark_h017(build_previous_level_signals(d),regimes)),
        ("H026",mark_h017(build_volume_impulse_signals(d),regimes)),
    ]

    rows=[]; yearly_parts=[]
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)

    for hypothesis,trades in strategies:
        row,yearly=evaluate_strategy(trades,hypothesis)
        rows.append(row); yearly_parts.append(yearly)
        trades.to_parquet(out/f"{hypothesis}_trades.parquet",index=False)

    summary=pd.DataFrame(rows)
    summary["q_value_bh"]=benjamini_hochberg(summary["p_value"])
    summary["passes_filter_gate"]=(
        (summary["inside_trades"]>=30)
        & (summary["filtered_trades"]>=150)
        & (summary["filter_delta_usd"]>=3.00)
        & (summary["ci_low"]>0)
        & (summary["q_value_bh"]<0.05)
        & (summary["filtered_expectancy_usd"]>0)
        & (summary["expectancy_improvement_usd"]>=0.50)
        & (summary["filtered_pf"]>=1.10)
        & (summary["pf_improvement"]>=0.05)
        & (summary["filtered_max_dd_usd"]<=summary["baseline_max_dd_usd"])
    )

    summary.to_csv(out/"R017_SUMMARY.csv",index=False)
    pd.concat(yearly_parts,ignore_index=True).to_csv(out/"yearly_breakdown.csv",index=False)
    regimes.to_parquet(out/"h017_regimes.parquet",index=False)

    lines=[
        "# R017 — H017 Filter Results","",
        f"Costs: commission $${COMMISSION_RT:.2f} + slippage $${SLIPPAGE_RT:.2f} = $${COST_RT:.2f}/trade.","",
        "| Hypothesis | Strategy | All | H017 | Filtered | Base Exp | Filt Exp | Base PF | Filt PF | Delta outside-inside | q | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _,r in summary.iterrows():
        lines.append(
            f"| {r['hypothesis']} | {r['strategy']} | {int(r['total_trades'])} | {int(r['inside_trades'])} | "
            f"{int(r['filtered_trades'])} | $${r['baseline_expectancy_usd']:.2f} | $${r['filtered_expectancy_usd']:.2f} | "
            f"{r['baseline_pf']:.2f} | {r['filtered_pf']:.2f} | $${r['filter_delta_usd']:.2f} | "
            f"{r['q_value_bh']:.4g} | {'PASS' if r['passes_filter_gate'] else 'FAIL'} |"
        )
    lines += ["","2026 was not used."]
    (out/"R017_SUMMARY.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(summary.to_string(index=False))


if __name__=="__main__":
    main()
