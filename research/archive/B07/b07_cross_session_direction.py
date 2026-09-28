from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import (
    benjamini_hochberg,
    clustered_mean_stats,
    rth_mask,
)

REF = 60
MAG_Q = 0.60


def parse_raw(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.copy()
    d["timestamp_et"] = pd.to_datetime(
        d["timestamp_et"], utc=True
    ).dt.tz_convert("America/New_York")
    d.sort_values("timestamp_et", inplace=True)
    return d.reset_index(drop=True)


def rolling_prior_quantile(
    frame: pd.DataFrame,
    value_col: str,
    eligible_mask: pd.Series,
    out_col: str,
    q: float,
) -> pd.DataFrame:
    frame[out_col] = np.nan
    idx = frame.index[eligible_mask & frame[value_col].notna()]
    vals = frame.loc[idx, value_col].abs()
    thresholds = (
        vals.shift(1)
        .rolling(REF, min_periods=REF)
        .quantile(q)
    )
    frame.loc[idx, out_col] = thresholds
    return frame


def build_sessions(raw: pd.DataFrame) -> pd.DataFrame:
    rth = raw[rth_mask(raw["timestamp_et"])].copy()
    rth["session_date"] = (
        rth["timestamp_et"].dt.date.astype(str)
    )
    rth["group_key"] = (
        rth["session_date"]
        + "|"
        + rth["contract"].astype(str)
    )
    rth["year"] = rth["timestamp_et"].dt.year

    rows = []
    rth_groups = {}

    for key, g in rth.groupby(
        "group_key", sort=False, observed=True
    ):
        g = g.sort_values("timestamp_et").reset_index(drop=True)
        if len(g) != 390:
            continue
        minute = (
            g["timestamp_et"].dt.hour * 60
            + g["timestamp_et"].dt.minute
        )
        if int(minute.iloc[0]) != 571 or int(minute.iloc[-1]) != 960:
            continue

        year = int(g["year"].iloc[0])
        if year < 2020 or year > 2025:
            continue

        rth_open = float(g["open"].iloc[0])
        rth_close = float(g["close"].iloc[-1])
        close_1000 = float(g["close"].iloc[29])

        if rth_open <= 0 or rth_close <= 0 or close_1000 <= 0:
            continue

        rows.append({
            "group_key": key,
            "session_date": g["session_date"].iloc[0],
            "year": year,
            "contract": g["contract"].iloc[0],
            "first_rth_ts": g["timestamp_et"].iloc[0],
            "last_rth_ts": g["timestamp_et"].iloc[-1],
            "rth_open": rth_open,
            "rth_close": rth_close,
            "day_return": float(
                np.log(rth_close / rth_open)
            ),
            "opening_return_bps": float(
                np.log(close_1000 / rth_open)
                * 10000.0
            ),
        })
        rth_groups[key] = g

    s = (
        pd.DataFrame(rows)
        .sort_values("first_rth_ts")
        .reset_index(drop=True)
    )

    s["prev_contract"] = s["contract"].shift(1)
    s["prev_rth_close"] = s["rth_close"].shift(1)
    s["prev_day_return"] = s["day_return"].shift(1)
    s["prev_last_rth_ts"] = s["last_rth_ts"].shift(1)

    same = s["contract"] == s["prev_contract"]
    for col in [
        "prev_rth_close",
        "prev_day_return",
        "prev_last_rth_ts",
    ]:
        s.loc[~same, col] = np.nan

    # Previous-day threshold must exclude current and previous day.
    s["prev_day_abs_q60"] = (
        s["day_return"]
        .abs()
        .shift(2)
        .rolling(REF, min_periods=REF)
        .quantile(MAG_Q)
    )

    return s


def add_overnight_and_gap(
    raw: pd.DataFrame,
    sessions: pd.DataFrame,
) -> pd.DataFrame:
    s = sessions.copy()
    by_contract = {
        contract: g.sort_values(
            "timestamp_et"
        ).reset_index(drop=True)
        for contract, g in raw.groupby(
            "contract", sort=False, observed=True
        )
    }

    s["overnight_return"] = np.nan
    s["gap_return"] = np.nan
    s["overnight_bars"] = np.nan

    for i, row in s.iterrows():
        if (
            pd.isna(row["prev_last_rth_ts"])
            or pd.isna(row["prev_rth_close"])
        ):
            continue

        cg = by_contract.get(row["contract"])
        if cg is None:
            continue

        prev_close_ts = row["prev_last_rth_ts"]
        current_rth_ts = row["first_rth_ts"]

        left = int(
            cg["timestamp_et"].searchsorted(
                prev_close_ts,
                side="right",
            )
        )
        right = int(
            cg["timestamp_et"].searchsorted(
                current_rth_ts,
                side="left",
            )
        )
        on = cg.iloc[left:right].copy()
        if on.empty:
            continue

        minute = (
            on["timestamp_et"].dt.hour * 60
            + on["timestamp_et"].dt.minute
        )
        on = on[
            (minute >= 1081)
            | (minute <= 570)
        ].copy()
        if on.empty:
            continue

        first_min = (
            on["timestamp_et"].iloc[0].hour * 60
            + on["timestamp_et"].iloc[0].minute
        )
        last_min = (
            on["timestamp_et"].iloc[-1].hour * 60
            + on["timestamp_et"].iloc[-1].minute
        )
        if first_min != 1081 or last_min != 570:
            continue

        on_open = float(on["open"].iloc[0])
        on_close = float(on["close"].iloc[-1])
        if on_open <= 0 or on_close <= 0:
            continue

        current_open = float(row["rth_open"])
        prev_close = float(row["prev_rth_close"])
        if current_open <= 0 or prev_close <= 0:
            continue

        s.loc[i, "overnight_return"] = float(
            np.log(on_close / on_open)
        )
        s.loc[i, "gap_return"] = float(
            np.log(current_open / prev_close)
        )
        s.loc[i, "overnight_bars"] = int(len(on))

    eligible_on = s["overnight_return"].notna()
    eligible_gap = s["gap_return"].notna()

    s = rolling_prior_quantile(
        s,
        "overnight_return",
        eligible_on,
        "overnight_abs_q60",
        MAG_Q,
    )
    s = rolling_prior_quantile(
        s,
        "gap_return",
        eligible_gap,
        "gap_abs_q60",
        MAG_Q,
    )
    return s


def summarize(
    hypothesis: str,
    events: pd.DataFrame,
    metric: str,
    min_n: int,
):
    y = events[metric]
    stats = clustered_mean_stats(
        y,
        events["session_date"],
    )
    yearly = (
        events.groupby("year", observed=True)[metric]
        .mean()
        .reset_index(name="mean_effect")
    )
    side = (
        events.groupby(
            "signal_side",
            observed=True,
        )
        .agg(
            n=(metric, "size"),
            mean_effect=(metric, "mean"),
            positive_rate=(
                metric,
                lambda z: float((z > 0).mean()),
            ),
        )
        .reset_index()
    )
    row = {
        "hypothesis": hypothesis,
        "n": int(len(events)),
        "sessions": int(
            events["session_date"].nunique()
        ),
        "mean_effect": (
            float(y.mean())
            if len(y)
            else np.nan
        ),
        "median_effect": (
            float(y.median())
            if len(y)
            else np.nan
        ),
        "continuation_rate": (
            float((y > 0).mean())
            if len(y)
            else np.nan
        ),
        **stats,
        "years_positive": int(
            (yearly["mean_effect"] > 0).sum()
        ),
        "years_observed": int(
            yearly["year"].nunique()
        ),
        "min_n_gate": min_n,
    }
    return row, yearly, side


def meaningful(
    value: pd.Series,
    threshold: pd.Series,
) -> pd.Series:
    return (
        value.notna()
        & threshold.notna()
        & (value != 0)
        & (value.abs() >= threshold)
    )


def h049(s):
    a = meaningful(
        s["prev_day_return"],
        s["prev_day_abs_q60"],
    )
    b = meaningful(
        s["overnight_return"],
        s["overnight_abs_q60"],
    )
    aligned = (
        np.sign(s["prev_day_return"])
        == np.sign(s["overnight_return"])
    )
    e = s[a & b & aligned].copy()
    e["signal_side"] = np.where(
        e["prev_day_return"] > 0,
        "BULL",
        "BEAR",
    )
    e["effect"] = (
        np.sign(e["prev_day_return"])
        * e["opening_return_bps"]
    )
    return e, *summarize(
        "H049", e, "effect", 150
    )


def h050(s):
    a = meaningful(
        s["overnight_return"],
        s["overnight_abs_q60"],
    )
    b = meaningful(
        s["gap_return"],
        s["gap_abs_q60"],
    )
    aligned = (
        np.sign(s["overnight_return"])
        == np.sign(s["gap_return"])
    )
    e = s[a & b & aligned].copy()
    e["signal_side"] = np.where(
        e["overnight_return"] > 0,
        "BULL",
        "BEAR",
    )
    e["effect"] = (
        np.sign(e["overnight_return"])
        * e["opening_return_bps"]
    )
    return e, *summarize(
        "H050", e, "effect", 150
    )


def h051(s):
    a = meaningful(
        s["prev_day_return"],
        s["prev_day_abs_q60"],
    )
    b = meaningful(
        s["gap_return"],
        s["gap_abs_q60"],
    )
    aligned = (
        np.sign(s["prev_day_return"])
        == np.sign(s["gap_return"])
    )
    e = s[a & b & aligned].copy()
    e["signal_side"] = np.where(
        e["prev_day_return"] > 0,
        "BULL",
        "BEAR",
    )
    e["effect"] = (
        np.sign(e["prev_day_return"])
        * e["opening_return_bps"]
    )
    return e, *summarize(
        "H051", e, "effect", 150
    )


def h052(s):
    a = meaningful(
        s["prev_day_return"],
        s["prev_day_abs_q60"],
    )
    b = meaningful(
        s["overnight_return"],
        s["overnight_abs_q60"],
    )
    c = meaningful(
        s["gap_return"],
        s["gap_abs_q60"],
    )
    sign_prev = np.sign(s["prev_day_return"])
    aligned = (
        (sign_prev == np.sign(s["overnight_return"]))
        & (sign_prev == np.sign(s["gap_return"]))
    )
    e = s[a & b & c & aligned].copy()
    e["signal_side"] = np.where(
        e["prev_day_return"] > 0,
        "BULL",
        "BEAR",
    )
    e["effect"] = (
        np.sign(e["prev_day_return"])
        * e["opening_return_bps"]
    )
    return e, *summarize(
        "H052", e, "effect", 75
    )


def h053(s):
    a = meaningful(
        s["prev_day_return"],
        s["prev_day_abs_q60"],
    )
    b = meaningful(
        s["overnight_return"],
        s["overnight_abs_q60"],
    )
    conflict = (
        np.sign(s["prev_day_return"])
        == -np.sign(s["overnight_return"])
    )
    e = s[a & b & conflict].copy()
    e["signal_side"] = np.where(
        e["overnight_return"] > 0,
        "BULL",
        "BEAR",
    )
    e["effect"] = (
        np.sign(e["overnight_return"])
        * e["opening_return_bps"]
    )
    return e, *summarize(
        "H053", e, "effect", 150
    )


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
        default="results/B07",
    )
    a = p.parse_args()

    raw = parse_raw(
        pd.read_parquet(a.input)
    )
    s = build_sessions(raw)
    s = add_overnight_and_gap(raw, s)

    results = []
    event_parts = []
    yearly_parts = []
    side_parts = []

    for h, fn in [
        ("H049", h049),
        ("H050", h050),
        ("H051", h051),
        ("H052", h052),
        ("H053", h053),
    ]:
        e, row, yearly, side = fn(s)
        results.append(row)
        event_parts.append((h, e))
        yearly["hypothesis"] = h
        side["hypothesis"] = h
        yearly_parts.append(yearly)
        side_parts.append(side)

    summary = pd.DataFrame(results)
    summary["q_value_bh"] = benjamini_hochberg(
        summary["p_value"]
    )
    summary["passes_individual_gate"] = (
        (summary["n"] >= summary["min_n_gate"])
        & (summary["sessions"] >= summary["min_n_gate"])
        & (summary["mean_effect"] >= 1.0)
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

    s.to_parquet(
        out / "session_features.parquet",
        index=False,
    )
    for h, e in event_parts:
        e.to_parquet(
            out / f"{h}_events.parquet",
            index=False,
        )
    pd.concat(
        yearly_parts,
        ignore_index=True,
    ).to_csv(
        out / "yearly.csv",
        index=False,
    )
    pd.concat(
        side_parts,
        ignore_index=True,
    ).to_csv(
        out / "side_breakdown.csv",
        index=False,
    )
    summary.to_csv(
        out / "B07_SUMMARY.csv",
        index=False,
    )

    print(summary.to_string(index=False))
    print("\nSide breakdown")
    print(
        pd.concat(
            side_parts,
            ignore_index=True,
        ).to_string(index=False)
    )


if __name__ == "__main__":
    main()
