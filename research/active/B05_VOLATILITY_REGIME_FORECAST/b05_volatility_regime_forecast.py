from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.research_utils import clustered_mean_stats, prepare_rth_features, rth_mask

REF = 60
LOW_Q = 0.20
HIGH_Q = 0.80
H017_Q = 0.10
H017_START = 10 * 60 + 1
ENTRY_CUTOFF = 11 * 60 + 30


def state_from_thresholds(value, q20, q80):
    if pd.isna(value) or pd.isna(q20) or pd.isna(q80):
        return np.nan
    if value <= q20:
        return -1
    if value >= q80:
        return 1
    return 0


def label_state(x):
    if pd.isna(x):
        return np.nan
    return "LOW" if x < 0 else ("HIGH" if x > 0 else "NORMAL")


def parse_raw(raw):
    d = raw.copy()
    d["timestamp_et"] = pd.to_datetime(
        d["timestamp_et"], utc=True
    ).dt.tz_convert("America/New_York")
    d.sort_values("timestamp_et", inplace=True)
    return d.reset_index(drop=True)


def build_base_sessions(raw):
    rth = raw[rth_mask(raw["timestamp_et"])].copy()
    rth["session_date"] = rth["timestamp_et"].dt.date.astype(str)
    rth["group_key"] = (
        rth["session_date"] + "|" + rth["contract"].astype(str)
    )
    rth["year"] = rth["timestamp_et"].dt.year

    rows = []
    by_group = {}

    for key, g in rth.groupby(
        "group_key", sort=False, observed=True
    ):
        g = g.sort_values("timestamp_et").reset_index(drop=True)
        if len(g) != 390:
            continue
        mins = (
            g["timestamp_et"].dt.hour * 60
            + g["timestamp_et"].dt.minute
        )
        if int(mins.iloc[0]) != 571 or int(mins.iloc[-1]) != 960:
            continue

        prev_range_bps = (
            (float(g["high"].max()) - float(g["low"].min()))
            / float(g["close"].iloc[-1])
            * 10000.0
        )

        first15 = g.iloc[:15]
        first30 = g.iloc[:30]
        next30 = g.iloc[15:45]

        opening15_bps = (
            (float(first15["high"].max()) - float(first15["low"].min()))
            / float(first15["open"].iloc[0])
            * 10000.0
        )
        opening30_bps = (
            (float(first30["high"].max()) - float(first30["low"].min()))
            / float(first30["open"].iloc[0])
            * 10000.0
        )
        future30_bps = (
            (float(next30["high"].max()) - float(next30["low"].min()))
            / float(first15["close"].iloc[-1])
            * 10000.0
        )

        rows.append({
            "group_key": key,
            "session_date": g["session_date"].iloc[0],
            "year": int(g["year"].iloc[0]),
            "contract": g["contract"].iloc[0],
            "first_ts": g["timestamp_et"].iloc[0],
            "full_rth_range_bps": prev_range_bps,
            "first15_range_bps": opening15_bps,
            "opening30_range_bps": opening30_bps,
            "future30_after_0945_bps": future30_bps,
        })
        by_group[key] = g

    s = pd.DataFrame(rows).sort_values(
        "first_ts"
    ).reset_index(drop=True)

    s["prev_contract"] = s["contract"].shift(1)
    s["prev_day_range_bps"] = s["full_rth_range_bps"].shift(1)
    same = s["contract"] == s["prev_contract"]
    s.loc[~same, "prev_day_range_bps"] = np.nan

    # Prior-day state thresholds must exclude both current and previous day.
    s["prev_day_q20"] = (
        s["full_rth_range_bps"]
        .shift(2)
        .rolling(REF, min_periods=REF)
        .quantile(LOW_Q)
    )
    s["prev_day_q80"] = (
        s["full_rth_range_bps"]
        .shift(2)
        .rolling(REF, min_periods=REF)
        .quantile(HIGH_Q)
    )

    # Current first15 and targets compare only to completed prior sessions.
    s["first15_q20"] = (
        s["first15_range_bps"]
        .shift(1)
        .rolling(REF, min_periods=REF)
        .quantile(LOW_Q)
    )
    s["first15_q80"] = (
        s["first15_range_bps"]
        .shift(1)
        .rolling(REF, min_periods=REF)
        .quantile(HIGH_Q)
    )

    for col, prefix in [
        ("opening30_range_bps", "opening30"),
        ("future30_after_0945_bps", "future30"),
    ]:
        s[f"{prefix}_q20"] = (
            s[col]
            .shift(1)
            .rolling(REF, min_periods=REF)
            .quantile(LOW_Q)
        )
        s[f"{prefix}_q80"] = (
            s[col]
            .shift(1)
            .rolling(REF, min_periods=REF)
            .quantile(HIGH_Q)
        )
        s[f"{prefix}_baseline"] = (
            s[col]
            .shift(1)
            .rolling(REF, min_periods=REF)
            .mean()
        )

    return s, rth, by_group


def add_overnight_ranges(raw, sessions):
    by_contract = {
        c: g.sort_values("timestamp_et").reset_index(drop=True)
        for c, g in raw.groupby(
            "contract", sort=False, observed=True
        )
    }

    s = sessions.copy()
    s["prev_rth_close_ts"] = s["first_ts"].shift(1)
    # replace shifted first-ts with actual prior RTH close timestamp
    prior_close_map = {}
    for i in range(1, len(s)):
        if s.loc[i, "contract"] == s.loc[i - 1, "contract"]:
            prev_date = s.loc[i - 1, "session_date"]
            prior_close_map[i] = pd.Timestamp(
                f"{prev_date} 16:00:00",
                tz="America/New_York",
            )
    s["overnight_range_bps"] = np.nan

    for i, row in s.iterrows():
        if i not in prior_close_map:
            continue
        cg = by_contract.get(row["contract"])
        if cg is None:
            continue

        left_ts = prior_close_map[i]
        right_ts = row["first_ts"]
        left = int(
            cg["timestamp_et"].searchsorted(
                left_ts, side="right"
            )
        )
        right = int(
            cg["timestamp_et"].searchsorted(
                right_ts, side="left"
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
            (minute >= 1081) | (minute <= 570)
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

        on_high = float(on["high"].max())
        on_low = float(on["low"].min())
        on_close = float(on["close"].iloc[-1])
        if on_close <= 0:
            continue

        s.loc[i, "overnight_range_bps"] = (
            (on_high - on_low) / on_close * 10000.0
        )

    eligible = s["overnight_range_bps"].notna()
    vals = s.loc[eligible, "overnight_range_bps"]
    s.loc[eligible, "overnight_q20"] = (
        vals.shift(1)
        .rolling(REF, min_periods=REF)
        .quantile(LOW_Q)
    )
    s.loc[eligible, "overnight_q80"] = (
        vals.shift(1)
        .rolling(REF, min_periods=REF)
        .quantile(HIGH_Q)
    )

    return s


def add_states_and_predictions(s):
    x = s.copy()

    x["prev_state"] = [
        state_from_thresholds(v, q20, q80)
        for v, q20, q80 in zip(
            x["prev_day_range_bps"],
            x["prev_day_q20"],
            x["prev_day_q80"],
        )
    ]
    x["overnight_state"] = [
        state_from_thresholds(v, q20, q80)
        for v, q20, q80 in zip(
            x["overnight_range_bps"],
            x["overnight_q20"],
            x["overnight_q80"],
        )
    ]
    x["first15_state"] = [
        state_from_thresholds(v, q20, q80)
        for v, q20, q80 in zip(
            x["first15_range_bps"],
            x["first15_q20"],
            x["first15_q80"],
        )
    ]

    x["opening30_actual_state"] = [
        state_from_thresholds(v, q20, q80)
        for v, q20, q80 in zip(
            x["opening30_range_bps"],
            x["opening30_q20"],
            x["opening30_q80"],
        )
    ]
    x["future30_actual_state"] = [
        state_from_thresholds(v, q20, q80)
        for v, q20, q80 in zip(
            x["future30_after_0945_bps"],
            x["future30_q20"],
            x["future30_q80"],
        )
    ]

    x["preopen_score"] = (
        x["prev_state"] + x["overnight_state"]
    )
    x["update_score"] = (
        x["prev_state"]
        + x["overnight_state"]
        + x["first15_state"]
    )

    x["preopen_prediction"] = x["preopen_score"].apply(
        label_state
    )
    x["update_prediction"] = x["update_score"].apply(
        label_state
    )
    x["opening30_actual"] = x[
        "opening30_actual_state"
    ].apply(label_state)
    x["future30_actual"] = x[
        "future30_actual_state"
    ].apply(label_state)

    x["opening30_ratio"] = (
        x["opening30_range_bps"]
        / x["opening30_baseline"]
    )
    x["future30_ratio"] = (
        x["future30_after_0945_bps"]
        / x["future30_baseline"]
    )

    return x


def evaluate_stage(
    x,
    hypothesis,
    prediction_col,
    actual_col,
    ratio_col,
):
    d = x[
        x[prediction_col].notna()
        & x[actual_col].notna()
        & x[ratio_col].notna()
    ].copy()

    metrics = []
    effects = {}

    for cls in ["LOW", "NORMAL", "HIGH"]:
        c = d[d[prediction_col] == cls].copy()
        if cls == "LOW":
            c["effect"] = (
                1.0 - c[ratio_col]
            ) * 100.0
        elif cls == "HIGH":
            c["effect"] = (
                c[ratio_col] - 1.0
            ) * 100.0
        else:
            c["effect"] = (
                c[ratio_col] - 1.0
            ) * 100.0

        if len(c):
            stats = clustered_mean_stats(
                c["effect"],
                c["session_date"],
            )
            precision = float(
                (c[actual_col] == cls).mean()
            )
            mean_ratio = float(c[ratio_col].mean())
        else:
            stats = {
                "mean": np.nan,
                "clustered_se": np.nan,
                "t_stat": np.nan,
                "p_value": np.nan,
                "ci_low": np.nan,
                "ci_high": np.nan,
            }
            precision = np.nan
            mean_ratio = np.nan

        metrics.append({
            "hypothesis": hypothesis,
            "predicted_class": cls,
            "n": int(len(c)),
            "mean_ratio": mean_ratio,
            "mean_effect_pct": float(
                c["effect"].mean()
            ) if len(c) else np.nan,
            "median_effect_pct": float(
                c["effect"].median()
            ) if len(c) else np.nan,
            "precision": precision,
            **stats,
        })
        effects[cls] = {
            "n": int(len(c)),
            "mean_effect": (
                float(c["effect"].mean())
                if len(c) else np.nan
            ),
            "ci_low": stats["ci_low"],
            "precision": precision,
            "mean_ratio": mean_ratio,
        }

    confusion = pd.crosstab(
        d[prediction_col],
        d[actual_col],
        dropna=False,
    ).reindex(
        index=["LOW", "NORMAL", "HIGH"],
        columns=["LOW", "NORMAL", "HIGH"],
        fill_value=0,
    )

    overall_accuracy = float(
        (d[prediction_col] == d[actual_col]).mean()
    )
    ext = d[
        d[prediction_col].isin(["LOW", "HIGH"])
    ]
    extreme_accuracy = (
        float(
            (
                ext[prediction_col]
                == ext[actual_col]
            ).mean()
        )
        if len(ext)
        else np.nan
    )

    ordered = (
        np.isfinite(effects["LOW"]["mean_ratio"])
        and np.isfinite(effects["NORMAL"]["mean_ratio"])
        and np.isfinite(effects["HIGH"]["mean_ratio"])
        and (
            effects["LOW"]["mean_ratio"]
            < effects["NORMAL"]["mean_ratio"]
            < effects["HIGH"]["mean_ratio"]
        )
    )

    passes = (
        effects["LOW"]["n"] >= 200
        and effects["HIGH"]["n"] >= 200
        and effects["LOW"]["mean_effect"] >= 10.0
        and effects["HIGH"]["mean_effect"] >= 10.0
        and effects["LOW"]["ci_low"] > 0
        and effects["HIGH"]["ci_low"] > 0
        and effects["LOW"]["precision"] >= 0.30
        and effects["HIGH"]["precision"] >= 0.30
        and ordered
    )

    summary = {
        "hypothesis": hypothesis,
        "n_total": int(len(d)),
        "low_n": effects["LOW"]["n"],
        "high_n": effects["HIGH"]["n"],
        "low_effect_pct": effects["LOW"]["mean_effect"],
        "high_effect_pct": effects["HIGH"]["mean_effect"],
        "low_precision": effects["LOW"]["precision"],
        "high_precision": effects["HIGH"]["precision"],
        "low_mean_ratio": effects["LOW"]["mean_ratio"],
        "normal_mean_ratio": effects["NORMAL"]["mean_ratio"],
        "high_mean_ratio": effects["HIGH"]["mean_ratio"],
        "overall_accuracy": overall_accuracy,
        "extreme_accuracy": extreme_accuracy,
        "ordered_ratios": bool(ordered),
        "passes_stage_gate": bool(passes),
    }

    return (
        pd.DataFrame(metrics),
        confusion,
        summary,
    )


def add_h017_features(raw):
    f = prepare_rth_features(
        raw,
        "2020-01-01",
        "2025-12-31",
        horizons=[30],
    ).reset_index(drop=True)
    g = f.groupby(
        "group_key", sort=False, observed=True
    )

    prev_close = g["close"].shift(1)
    prev_ts = g["timestamp_et"].shift(1)
    exact1 = (
        f["timestamp_et"] - prev_ts
    ) == pd.Timedelta(minutes=1)
    f["r1"] = np.where(
        exact1,
        np.log(f["close"] / prev_close),
        np.nan,
    )

    lag30 = g["timestamp_et"].shift(30)
    exact_hist30 = (
        (f["timestamp_et"] - lag30)
        == pd.Timedelta(minutes=30)
    ).fillna(False)

    rv30 = (
        f.groupby(
            "group_key",
            sort=False,
            observed=True,
        )["r1"]
        .rolling(30, min_periods=30)
        .apply(
            lambda z: float(
                np.sqrt(
                    np.square(z).sum()
                ) * 10000.0
            ),
            raw=True,
        )
        .reset_index(level=0, drop=True)
    )
    f["rv30"] = np.where(
        exact_hist30,
        rv30,
        np.nan,
    )

    # exact next-30m high-low range.
    future = np.full(len(f), np.nan)
    for idx in f.groupby(
        "group_key",
        sort=False,
        observed=True,
    ).indices.values():
        pos = np.asarray(idx, dtype=int)
        n = len(pos)
        if n <= 30:
            continue
        highs = f.loc[pos, "high"].to_numpy(float)
        lows = f.loc[pos, "low"].to_numpy(float)
        closes = f.loc[pos, "close"].to_numpy(float)
        hw = np.lib.stride_tricks.sliding_window_view(
            highs[1:], 30
        )
        lw = np.lib.stride_tricks.sliding_window_view(
            lows[1:], 30
        )
        vals = (
            (hw.max(axis=1) - lw.min(axis=1))
            / closes[: n - 30]
            * 10000.0
        )
        future[pos[: n - 30]] = vals

    future[
        ~f["exact_30m"].fillna(False).to_numpy(bool)
    ] = np.nan
    f["future_range30_bps"] = future
    f["minute"] = (
        f["timestamp_et"].dt.hour * 60
        + f["timestamp_et"].dt.minute
    )

    f.sort_values(
        ["minute", "timestamp_et"],
        inplace=True,
    )
    by = f.groupby(
        "minute",
        sort=False,
        observed=True,
    )
    f["h017_threshold"] = by["rv30"].transform(
        lambda s: s.shift(1).rolling(
            REF, min_periods=REF
        ).quantile(H017_Q)
    )
    f["future_range_q20"] = by[
        "future_range30_bps"
    ].transform(
        lambda s: s.shift(1).rolling(
            REF, min_periods=REF
        ).quantile(LOW_Q)
    )
    f["future_range_baseline"] = by[
        "future_range30_bps"
    ].transform(
        lambda s: s.shift(1).rolling(
            REF, min_periods=REF
        ).mean()
    )
    f.sort_values("timestamp_et", inplace=True)
    return f


def evaluate_h045(raw):
    f = add_h017_features(raw)
    eligible = (
        (f["minute"] >= H017_START)
        & (f["minute"] <= ENTRY_CUTOFF)
        & f["rv30"].notna()
        & f["h017_threshold"].notna()
        & (f["rv30"] <= f["h017_threshold"])
        & f["future_range30_bps"].notna()
        & f["future_range_q20"].notna()
        & f["future_range_baseline"].notna()
        & (f["future_range_baseline"] > 0)
    )
    c = f[eligible].copy()
    c.sort_values(
        ["group_key", "timestamp_et"],
        inplace=True,
    )
    e = c.groupby(
        "group_key",
        sort=False,
        observed=True,
    ).head(1).copy()

    e["range_discount_pct"] = (
        1.0
        - e["future_range30_bps"]
        / e["future_range_baseline"]
    ) * 100.0
    e["actual_low"] = (
        e["future_range30_bps"]
        <= e["future_range_q20"]
    )

    stats = clustered_mean_stats(
        e["range_discount_pct"],
        e["session_date"],
    )
    low_precision = float(
        e["actual_low"].mean()
    ) if len(e) else np.nan

    passes = (
        len(e) >= 100
        and e["session_date"].nunique() >= 100
        and float(
            e["range_discount_pct"].mean()
        ) >= 25.0
        and stats["ci_low"] > 0
        and low_precision >= 0.40
    )

    summary = {
        "hypothesis": "H045",
        "n_total": int(len(e)),
        "mean_discount_pct": float(
            e["range_discount_pct"].mean()
        ) if len(e) else np.nan,
        "median_discount_pct": float(
            e["range_discount_pct"].median()
        ) if len(e) else np.nan,
        "low_precision": low_precision,
        **stats,
        "passes_stage_gate": bool(passes),
    }
    return e, summary


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
        default="results/B05",
    )
    a = p.parse_args()

    raw = parse_raw(
        pd.read_parquet(a.input)
    )
    sessions, _, _ = build_base_sessions(raw)
    sessions = add_overnight_ranges(
        raw, sessions
    )
    sessions = add_states_and_predictions(
        sessions
    )

    m43, c43, s43 = evaluate_stage(
        sessions,
        "H043",
        "preopen_prediction",
        "opening30_actual",
        "opening30_ratio",
    )
    m44, c44, s44 = evaluate_stage(
        sessions,
        "H044",
        "update_prediction",
        "future30_actual",
        "future30_ratio",
    )
    e45, s45 = evaluate_h045(raw)

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    sessions.to_parquet(
        out / "regime_session_features.parquet",
        index=False,
    )
    m43.to_csv(
        out / "H043_metrics.csv",
        index=False,
    )
    m44.to_csv(
        out / "H044_metrics.csv",
        index=False,
    )
    c43.to_csv(
        out / "H043_confusion.csv"
    )
    c44.to_csv(
        out / "H044_confusion.csv"
    )
    e45.to_parquet(
        out / "H045_events.parquet",
        index=False,
    )

    summary = pd.DataFrame(
        [s43, s44, s45]
    )
    summary.to_csv(
        out / "B05_SUMMARY.csv",
        index=False,
    )

    lines = [
        "# B05 Staged Volatility-Regime Forecast",
        "",
        "2026 was not used.",
        "",
        summary.to_string(index=False),
    ]
    (out / "B05_SUMMARY.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(summary.to_string(index=False))
    print("\nH043 metrics")
    print(m43.to_string(index=False))
    print("\nH044 metrics")
    print(m44.to_string(index=False))


if __name__ == "__main__":
    main()
