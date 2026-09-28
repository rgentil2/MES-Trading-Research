from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from research.archive.B05.b05_volatility_regime_forecast import (
    add_overnight_ranges,
    add_states_and_predictions,
    build_base_sessions,
    parse_raw,
)
from research.archive.B11.b11_extended_regime_persistence import build_blocks
from research.archive.R017.r017_h017_filter import (
    build_h017_regimes,
    enrich_features,
)

REF = 60

PREOPEN_MULTIPLIER = {
    "LOW": 0.704,
    "NORMAL": 0.950,
    "HIGH": 1.419,
}
OPEN15_MULTIPLIER = {
    "LOW": 0.693,
    "NORMAL": 0.954,
    "HIGH": 1.438,
}
DYNAMIC_MULTIPLIER = {
    15: {"LOW": 0.6448, "NORMAL": 1.0000, "HIGH": 1.5423},
    60: {"LOW": 0.6592, "NORMAL": 1.0000, "HIGH": 1.5234},
    120: {"LOW": 0.6626, "NORMAL": 1.0000, "HIGH": 1.5311},
    180: {"LOW": 0.6951, "NORMAL": 1.0000, "HIGH": 1.4899},
    240: {"LOW": 0.7455, "NORMAL": 1.0000, "HIGH": 1.4399},
}
H017_NEXT30_MULTIPLIER = 0.611


def classify_numeric(v, q20, q80):
    if pd.isna(v) or pd.isna(q20) or pd.isna(q80):
        return np.nan
    if v <= q20:
        return -1
    if v >= q80:
        return 1
    return 0


def label_numeric(v):
    if pd.isna(v):
        return np.nan
    return "LOW" if v < 0 else ("HIGH" if v > 0 else "NORMAL")


def five_day_context(sessions: pd.DataFrame) -> pd.DataFrame:
    s = sessions.copy().sort_values("first_ts").reset_index(drop=True)

    same5 = pd.Series(True, index=s.index)
    range_cols = []
    for lag in range(1, 6):
        ccol = f"contract_lag{lag}"
        rcol = f"range_lag{lag}"
        s[ccol] = s["contract"].shift(lag)
        s[rcol] = s["full_rth_range_bps"].shift(lag)
        same5 &= s["contract"].eq(s[ccol])
        range_cols.append(rcol)

    s["avg_range5"] = np.where(
        same5,
        s[range_cols].mean(axis=1),
        np.nan,
    )

    idx = s.index[s["avg_range5"].notna()]
    vals = s.loc[idx, "avg_range5"]
    s["avg_range5_q20"] = np.nan
    s["avg_range5_q80"] = np.nan
    s.loc[idx, "avg_range5_q20"] = (
        vals.shift(1).rolling(REF, min_periods=REF).quantile(0.20)
    )
    s.loc[idx, "avg_range5_q80"] = (
        vals.shift(1).rolling(REF, min_periods=REF).quantile(0.80)
    )

    s["five_day_state"] = [
        classify_numeric(v, q20, q80)
        for v, q20, q80 in zip(
            s["avg_range5"],
            s["avg_range5_q20"],
            s["avg_range5_q80"],
        )
    ]
    s["five_day_state_label"] = s["five_day_state"].apply(label_numeric)
    return s


def support_label(prediction, five_state):
    if pd.isna(prediction) or pd.isna(five_state):
        return "NEUTRAL"
    if prediction == "HIGH" and five_state == 1:
        return "ALIGNED"
    if prediction == "LOW" and five_state == -1:
        return "ALIGNED"
    if prediction == "HIGH" and five_state == -1:
        return "CONFLICT"
    if prediction == "LOW" and five_state == 1:
        return "CONFLICT"
    return "NEUTRAL"


def build_session_outputs(raw: pd.DataFrame) -> pd.DataFrame:
    parsed = parse_raw(raw)
    sessions, _, _ = build_base_sessions(parsed)
    sessions = add_overnight_ranges(parsed, sessions)
    sessions = add_states_and_predictions(sessions)
    sessions = five_day_context(sessions)

    sessions["preopen_support"] = [
        support_label(pred, st)
        for pred, st in zip(
            sessions["preopen_prediction"],
            sessions["five_day_state"],
        )
    ]
    sessions["open15_support"] = [
        support_label(pred, st)
        for pred, st in zip(
            sessions["update_prediction"],
            sessions["five_day_state"],
        )
    ]
    sessions["preopen_expected_multiplier"] = sessions[
        "preopen_prediction"
    ].map(PREOPEN_MULTIPLIER)
    sessions["open15_expected_multiplier"] = sessions[
        "update_prediction"
    ].map(OPEN15_MULTIPLIER)
    sessions["directional_prediction"] = False
    return sessions


def build_dynamic_outputs(raw: pd.DataFrame) -> pd.DataFrame:
    blocks = build_blocks(raw)
    d = blocks[blocks["block_id"].isin(range(0, 8))].copy()
    d = d[d["state"].notna()].copy()
    d["stage"] = "DYNAMIC"
    d["directional_prediction"] = False

    for horizon, mapping in DYNAMIC_MULTIPLIER.items():
        d[f"expected_multiplier_{horizon}m"] = d["state"].map(mapping)

    features = enrich_features(raw)
    h017 = build_h017_regimes(features)
    d = d.merge(
        h017[["group_key", "h017_time"]],
        on="group_key",
        how="left",
        validate="many_to_one",
    )
    d["h017_active_at_block_close"] = (
        d["h017_time"].notna()
        & (d["block_end_ts"] >= d["h017_time"])
        & (
            d["block_end_ts"]
            <= d["h017_time"] + pd.Timedelta(minutes=30)
        )
    )
    d["engine_state"] = d["state"]
    d.loc[d["h017_active_at_block_close"], "engine_state"] = "LOW"
    d["engine_stage"] = np.where(
        d["h017_active_at_block_close"],
        "H017_OVERRIDE",
        "DYNAMIC",
    )
    return d


def calibration_table(sessions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for stage, pred_col, actual_col, ratio_col in [
        (
            "PREOPEN",
            "preopen_prediction",
            "opening30_actual",
            "opening30_ratio",
        ),
        (
            "OPEN15",
            "update_prediction",
            "future30_actual",
            "future30_ratio",
        ),
    ]:
        for cls in ["LOW", "NORMAL", "HIGH"]:
            x = sessions[
                (sessions[pred_col] == cls)
                & sessions[ratio_col].notna()
            ].copy()
            rows.append({
                "stage": stage,
                "regime": cls,
                "n": int(len(x)),
                "mean_ratio": float(x[ratio_col].mean()) if len(x) else np.nan,
                "precision": (
                    float((x[actual_col] == cls).mean())
                    if len(x)
                    else np.nan
                ),
                "frozen_multiplier": (
                    PREOPEN_MULTIPLIER[cls]
                    if stage == "PREOPEN"
                    else OPEN15_MULTIPLIER[cls]
                ),
            })
    return pd.DataFrame(rows)


def lookup_table() -> pd.DataFrame:
    rows = []
    for horizon, mapping in DYNAMIC_MULTIPLIER.items():
        for state, value in mapping.items():
            rows.append({
                "stage": "DYNAMIC",
                "horizon_minutes": horizon,
                "regime": state,
                "expected_multiplier": value,
            })
    rows.append({
        "stage": "H017_OVERRIDE",
        "horizon_minutes": 30,
        "regime": "LOW",
        "expected_multiplier": H017_NEXT30_MULTIPLIER,
    })
    return pd.DataFrame(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default="data/processed/MES_CONTINUOUS_1M_2020_2026.parquet",
    )
    p.add_argument("--output-dir", default="results/R063")
    a = p.parse_args()

    raw = pd.read_parquet(a.input)

    sessions = build_session_outputs(raw)
    dynamic = build_dynamic_outputs(raw)
    calibration = calibration_table(sessions)
    lookup = lookup_table()

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    sessions.to_parquet(out / "session_outputs.parquet", index=False)
    dynamic.to_parquet(out / "dynamic_outputs.parquet", index=False)
    calibration.to_csv(out / "development_calibration.csv", index=False)
    lookup.to_csv(out / "frozen_multiplier_lookup.csv", index=False)

    h017_n = int(dynamic["h017_time"].dropna().groupby(dynamic.loc[dynamic["h017_time"].notna(), "group_key"]).first().shape[0])

    lines = [
        "# R063 Final Regime Engine v1 — Development Audit",
        "",
        "This audit executes only 2020–2025 development data.",
        "It does not constitute independent validation.",
        "",
        "## Frozen stage calibration",
        "",
        calibration.to_csv(index=False),
        "",
        "## Dynamic lookup",
        "",
        lookup.to_csv(index=False),
        "",
        f"H017 sessions represented in dynamic map: {h017_n}",
        "",
        "Directional prediction: disabled by design.",
        "",
        "2026 was not used.",
    ]
    (out / "R063_DEV_AUDIT.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(calibration.to_string(index=False))
    print("\nFrozen multiplier lookup")
    print(lookup.to_string(index=False))
    print(f"\nH017 sessions: {h017_n}")


if __name__ == "__main__":
    main()
