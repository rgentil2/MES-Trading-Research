from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import benjamini_hochberg, clustered_mean_stats, prepare_rth_features, rth_mask

REF = 60
H028_Q = 0.80
H030_Q = 0.20
H032_Q = 0.70
H032_EFFICIENCY_MIN = 0.60
ENTRY_CUTOFF = 11 * 60 + 30


def parse_raw(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.copy()
    d["timestamp_et"] = pd.to_datetime(d["timestamp_et"], utc=True).dt.tz_convert("America/New_York")
    d.sort_values("timestamp_et", inplace=True)
    return d.reset_index(drop=True)


def build_session_table(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rth = raw[rth_mask(raw["timestamp_et"])].copy()
    rth["session_date"] = rth["timestamp_et"].dt.date.astype(str)
    rth["group_key"] = rth["session_date"] + "|" + rth["contract"].astype(str)
    rth["minute"] = rth["timestamp_et"].dt.hour * 60 + rth["timestamp_et"].dt.minute
    rth["year"] = rth["timestamp_et"].dt.year

    sess = (
        rth.groupby("group_key", sort=False, observed=True)
        .agg(
            session_date=("session_date", "first"),
            year=("year", "first"),
            contract=("contract", "first"),
            first_rth_ts=("timestamp_et", "min"),
            last_rth_ts=("timestamp_et", "max"),
            rth_count=("timestamp_et", "size"),
        )
        .sort_values("first_rth_ts")
        .reset_index()
    )

    sess = sess[
        (sess["year"] >= 2020)
        & (sess["year"] <= 2025)
        & (sess["rth_count"] == 390)
        & ((sess["first_rth_ts"].dt.hour * 60 + sess["first_rth_ts"].dt.minute) == 571)
        & ((sess["last_rth_ts"].dt.hour * 60 + sess["last_rth_ts"].dt.minute) == 960)
    ].copy()

    # Previous valid RTH session, same contract only.
    sess["prev_contract"] = sess["contract"].shift(1)
    sess["prev_rth_close_ts"] = sess["last_rth_ts"].shift(1)
    same = sess["contract"] == sess["prev_contract"]
    sess.loc[~same, "prev_rth_close_ts"] = pd.NaT

    return sess.reset_index(drop=True), rth


def overnight_features(raw: pd.DataFrame, sessions: pd.DataFrame, rth: pd.DataFrame) -> pd.DataFrame:
    by_contract = {
        c: g.sort_values("timestamp_et").reset_index(drop=True)
        for c, g in raw.groupby("contract", sort=False, observed=True)
    }

    rth_by_group = {
        k: g.sort_values("timestamp_et").reset_index(drop=True)
        for k, g in rth.groupby("group_key", sort=False, observed=True)
    }

    rows = []
    for row in sessions.itertuples(index=False):
        if pd.isna(row.prev_rth_close_ts):
            continue

        cg = by_contract.get(row.contract)
        rg = rth_by_group.get(row.group_key)
        if cg is None or rg is None or len(rg) < 31:
            continue

        left = int(cg["timestamp_et"].searchsorted(row.prev_rth_close_ts, side="right"))
        right = int(cg["timestamp_et"].searchsorted(row.first_rth_ts, side="left"))
        on = cg.iloc[left:right].copy()
        if on.empty:
            continue

        minute = on["timestamp_et"].dt.hour * 60 + on["timestamp_et"].dt.minute
        on = on[(minute >= 18 * 60 + 1) | (minute <= 9 * 60 + 30)].copy()
        if on.empty:
            continue

        first_minute = int(on["timestamp_et"].iloc[0].hour * 60 + on["timestamp_et"].iloc[0].minute)
        last_minute = int(on["timestamp_et"].iloc[-1].hour * 60 + on["timestamp_et"].iloc[-1].minute)
        if first_minute != 1081 or last_minute != 570:
            continue

        on_open = float(on["open"].iloc[0])
        on_close = float(on["close"].iloc[-1])
        on_high = float(on["high"].max())
        on_low = float(on["low"].min())
        if on_open <= 0 or on_close <= 0 or on_high <= on_low:
            continue

        ts_diff = on["timestamp_et"].diff()
        prev_close = on["close"].shift(1)
        exact = ts_diff == pd.Timedelta(minutes=1)
        exact_rets = np.log(on.loc[exact, "close"].to_numpy(float) / prev_close.loc[exact].to_numpy(float))
        first_bar_ret = float(np.log(on["close"].iloc[0] / on_open))
        path_abs = abs(first_bar_ret) + float(np.abs(exact_rets).sum())

        on_return = float(np.log(on_close / on_open))
        on_eff = abs(on_return) / path_abs if path_abs > 0 else np.nan

        first30 = rg.iloc[:30]
        mins = first30["timestamp_et"].dt.hour * 60 + first30["timestamp_et"].dt.minute
        if len(first30) != 30 or int(mins.iloc[0]) != 571 or int(mins.iloc[-1]) != 600:
            continue

        rth_open = float(first30["open"].iloc[0])
        close_1000 = float(first30["close"].iloc[-1])
        opening_return_bps = float(np.log(close_1000 / rth_open) * 10000.0)
        opening_range_bps = float((first30["high"].max() - first30["low"].min()) / rth_open * 10000.0)

        firstbar = rg.iloc[0]
        open_location = float((rth_open - on_low) / (on_high - on_low))

        rows.append({
            "group_key": row.group_key,
            "session_date": row.session_date,
            "year": int(row.year),
            "contract": row.contract,
            "first_rth_ts": row.first_rth_ts,
            "on_open": on_open,
            "on_close": on_close,
            "on_high": on_high,
            "on_low": on_low,
            "on_return": on_return,
            "on_return_bps": on_return * 10000.0,
            "on_range_bps": (on_high - on_low) / on_close * 10000.0,
            "on_efficiency": on_eff,
            "on_bars": int(len(on)),
            "rth_open": rth_open,
            "close_1000": close_1000,
            "opening_return_bps": opening_return_bps,
            "opening_range_bps": opening_range_bps,
            "open_location": open_location,
            "firstbar_timestamp": firstbar["timestamp_et"],
            "firstbar_fwd30": firstbar.get("fwd_30m", np.nan),
            "firstbar_exact30": bool(firstbar.get("exact_30m", False)),
        })

    s = pd.DataFrame(rows).sort_values("first_rth_ts").reset_index(drop=True)

    valid = s["on_return"].notna() & s["on_range_bps"].notna() & s["opening_range_bps"].notna()
    idx = s.index[valid]
    v = s.loc[idx].copy()

    s["on_abs_return_q80"] = np.nan
    s["on_abs_return_q70"] = np.nan
    s["on_range_q20"] = np.nan
    s["opening_range_baseline"] = np.nan

    s.loc[idx, "on_abs_return_q80"] = (
        v["on_return"].abs().shift(1).rolling(REF, min_periods=REF).quantile(H028_Q)
    )
    s.loc[idx, "on_abs_return_q70"] = (
        v["on_return"].abs().shift(1).rolling(REF, min_periods=REF).quantile(H032_Q)
    )
    s.loc[idx, "on_range_q20"] = (
        v["on_range_bps"].shift(1).rolling(REF, min_periods=REF).quantile(H030_Q)
    )
    s.loc[idx, "opening_range_baseline"] = (
        v["opening_range_bps"].shift(1).rolling(REF, min_periods=REF).mean()
    )

    return s


def primary_row(hypothesis, events, metric, min_n, min_mean):
    y = events[metric]
    stats = clustered_mean_stats(y, events["session_date"])
    yearly = (
        events.groupby("year", observed=True)[metric]
        .mean()
        .reset_index(name="mean_effect")
    )
    return {
        "hypothesis": hypothesis,
        "n": int(len(events)),
        "sessions": int(events["session_date"].nunique()),
        "mean_effect": float(y.mean()) if len(y) else np.nan,
        "median_effect": float(y.median()) if len(y) else np.nan,
        **stats,
        "positive_rate": float((y > 0).mean()) if len(y) else np.nan,
        "years_positive": int((yearly["mean_effect"] > 0).sum()),
        "years_observed": int(yearly["year"].nunique()),
        "min_n_gate": min_n,
        "min_mean_gate": min_mean,
    }, yearly


def h028(s):
    e = s[
        s["on_abs_return_q80"].notna()
        & (s["on_return"].abs() >= s["on_abs_return_q80"])
        & (s["on_return"] != 0)
    ].copy()
    e["reversion_30m_bps"] = -np.sign(e["on_return"]) * e["opening_return_bps"]
    row, yearly = primary_row("H028", e, "reversion_30m_bps", 200, 1.0)
    return e, row, yearly


def h030(s):
    e = s[
        s["on_range_q20"].notna()
        & s["opening_range_baseline"].notna()
        & (s["opening_range_baseline"] > 0)
        & (s["on_range_bps"] <= s["on_range_q20"])
    ].copy()
    e["opening_expansion_pct"] = (
        e["opening_range_bps"] / e["opening_range_baseline"] - 1.0
    ) * 100.0
    row, yearly = primary_row("H030", e, "opening_expansion_pct", 200, 10.0)
    return e, row, yearly


def h031(s):
    e = s[
        ((s["open_location"] >= 0.80) | (s["open_location"] <= 0.20))
        & s["firstbar_exact30"]
        & s["firstbar_fwd30"].notna()
    ].copy()
    e["expected_direction"] = np.where(e["open_location"] >= 0.80, -1, 1)
    e["reversion_30m_bps"] = e["expected_direction"] * e["firstbar_fwd30"] * 10000.0
    row, yearly = primary_row("H031", e, "reversion_30m_bps", 400, 1.0)
    return e, row, yearly


def h032(s):
    e = s[
        s["on_abs_return_q70"].notna()
        & (s["on_return"].abs() >= s["on_abs_return_q70"])
        & (s["on_efficiency"] >= H032_EFFICIENCY_MIN)
        & (s["on_return"] != 0)
    ].copy()
    e["continuation_30m_bps"] = np.sign(e["on_return"]) * e["opening_return_bps"]
    row, yearly = primary_row("H032", e, "continuation_30m_bps", 150, 1.0)
    return e, row, yearly


def h029(raw, sessions):
    rthf = prepare_rth_features(raw, "2020-01-01", "2025-12-31", horizons=[30])
    levels = sessions[["group_key", "on_high", "on_low"]].dropna()
    x = rthf.merge(levels, on="group_key", how="inner", validate="many_to_one")
    minute = x["timestamp_et"].dt.hour * 60 + x["timestamp_et"].dt.minute
    eligible = (minute >= 571) & (minute <= ENTRY_CUTOFF)
    outside = (x["close"] > x["on_high"]) | (x["close"] < x["on_low"])
    c = x[eligible & outside].copy()
    c.sort_values(["group_key", "timestamp_et"], inplace=True)
    e = c.groupby("group_key", sort=False, observed=True).head(1).copy()
    e = e[e["exact_30m"].fillna(False) & e["fwd_30m"].notna()].copy()
    e["direction"] = np.where(e["close"] > e["on_high"], 1, -1)
    e["continuation_30m_bps"] = e["direction"] * e["fwd_30m"] * 10000.0
    row, yearly = primary_row("H029", e, "continuation_30m_bps", 500, 1.0)
    return e, row, yearly


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet")
    p.add_argument("--output-dir", default="results/B02")
    a = p.parse_args()

    raw = parse_raw(pd.read_parquet(a.input))
    sessions_base, rth = build_session_table(raw)

    # Need forward outcome on the first RTH bar for H031.
    rthf = prepare_rth_features(raw, "2020-01-01", "2025-12-31", horizons=[30])
    first_fwd = (
        rthf.sort_values("timestamp_et")
        .groupby("group_key", sort=False, observed=True)
        .head(1)[["group_key", "fwd_30m", "exact_30m"]]
        .rename(columns={"fwd_30m": "firstbar_fwd30", "exact_30m": "firstbar_exact30"})
    )

    s = overnight_features(raw, sessions_base, rth)
    # Replace the placeholder first-bar fields with exact feature-engine values.
    s = s.drop(columns=["firstbar_fwd30", "firstbar_exact30"]).merge(
        first_fwd, on="group_key", how="left", validate="one_to_one"
    )

    e28, r28, y28 = h028(s)
    e29, r29, y29 = h029(raw, s)
    e30, r30, y30 = h030(s)
    e31, r31, y31 = h031(s)
    e32, r32, y32 = h032(s)

    summary = pd.DataFrame([r28, r29, r30, r31, r32])
    summary["q_value_bh"] = benjamini_hochberg(summary["p_value"])
    summary["passes_individual_gate"] = (
        (summary["n"] >= summary["min_n_gate"])
        & (summary["mean_effect"] >= summary["min_mean_gate"])
        & (summary["ci_low"] > 0)
        & (summary["years_observed"] == 6)
        & (summary["years_positive"] >= 4)
    )
    summary["passes_block_gate"] = (
        summary["passes_individual_gate"]
        & (summary["q_value_bh"] < 0.05)
    )

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    s.to_parquet(out / "overnight_sessions.parquet", index=False)

    for h, e, y in [
        ("H028", e28, y28),
        ("H029", e29, y29),
        ("H030", e30, y30),
        ("H031", e31, y31),
        ("H032", e32, y32),
    ]:
        e.to_parquet(out / f"{h}_events.parquet", index=False)
        y.to_csv(out / f"{h}_yearly.csv", index=False)

    summary.to_csv(out / "B02_SUMMARY.csv", index=False)

    lines = [
        "# B02 Overnight & Opening Structure — Results",
        "",
        "| Hypothesis | N | Mean effect | p | q(BH) | Positive years | Individual | Block |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| {r['hypothesis']} | {int(r['n'])} | {r['mean_effect']:.3f} | "
            f"{r['p_value']:.6g} | {r['q_value_bh']:.6g} | "
            f"{int(r['years_positive'])}/{int(r['years_observed'])} | "
            f"{bool(r['passes_individual_gate'])} | {bool(r['passes_block_gate'])} |"
        )
    lines += ["", "2026 was not used."]
    (out / "B02_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
