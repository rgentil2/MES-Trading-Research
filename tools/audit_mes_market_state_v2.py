#!/usr/bin/env python3
"""First frozen descriptive run of MES Market State V2.

No forward returns, trade labels, P&L or strategy outcomes are calculated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_pipeline import build_continuous, contract_info
from src.mes_market_state_v2 import (
    VERSION,
    STATES,
    causal_inputs,
    classify,
    diagnose,
    configuration,
)

LOCK = ROOT / "research/market_state/MES_MS2_FREEZE.json"
FROZEN_FILES = [
    "src/mes_market_state_v2.py",
    "tests/test_mes_market_state_v2.py",
    "tools/audit_mes_market_state_v2.py",
    "research/market_state/MES_MS2_PROTOCOL.md",
]


def digest(path: Path) -> str:
    data = path.read_bytes()
    header = b"blob " + str(len(data)).encode("ascii") + bytes([0])
    return hashlib.sha1(header + data).hexdigest()


def preflight() -> dict:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock["version"] != VERSION:
        raise ValueError("V2 freeze version mismatch")
    if lock["authority"] != "DESCRIPTIVE_FEATURE_MAP_ONLY":
        raise ValueError("V2 freeze authority mismatch")
    if lock["outcomes_permitted"]:
        raise ValueError("V2 freeze unexpectedly permits outcomes")
    if lock["config"] != configuration():
        raise ValueError("V2 freeze configuration mismatch")
    actual = {p: digest(ROOT / p) for p in FROZEN_FILES}
    if actual != lock["fingerprints"]:
        raise ValueError("V2 frozen file fingerprint mismatch")
    return lock


def source_files(raw_dir: Path) -> list[Path]:
    files = []
    for p in raw_dir.glob("MES ??-??.Last.txt"):
        year, month, _ = contract_info(p)
        if 2020 <= year <= 2024 or (year == 2025 and month == 3):
            files.append(p)
    files = sorted(files, key=lambda p: contract_info(p)[:2])

    expected = {(y, m) for y in range(2020, 2025) for m in (3, 6, 9, 12)}
    actual = {contract_info(p)[:2] for p in files if contract_info(p)[0] <= 2024}
    if actual != expected:
        raise ValueError("require all twenty 2020-2024 MES contracts")
    if not any(contract_info(p)[:2] == (2025, 3) for p in files):
        raise ValueError("MAR25 source required solely to complete ET-calendar 2024")
    if len(files) != 21:
        raise ValueError("unexpected source-file scope")
    return files


def state_summary(features: pd.DataFrame, episodes: pd.DataFrame) -> dict:
    out = {}
    for state in STATES:
        e = episodes[episodes.regime == state]
        out[state] = {
            "sessions": int((features.regime == state).sum()),
            "episodes": int(len(e)),
            "median_episode_sessions": (
                float(e.sessions.median()) if len(e) else None
            ),
            "max_episode_sessions": int(e.sessions.max()) if len(e) else None,
        }
    return out


def annual_summary(features: pd.DataFrame) -> dict:
    out = {}
    for year in range(2020, 2025):
        y = features[features.date.str.startswith(str(year))]
        out[str(year)] = {
            "sessions": int(len(y)),
            "classified": int((y.regime != "R0").sum()),
            "r0": int((y.regime == "R0").sum()),
            "ready_inputs": int((y.input_status == "READY").sum()),
        }
    return out


def markdown(report: dict) -> str:
    cmp = report["comparison_v1"]
    lines = [
        "# MES Market State V2 — primera auditoría descriptiva",
        "",
        "Corrección de calendario/cobertura congelada antes de esta ejecución. "
        "Sin retornos futuros, P&L ni selección de estrategia.",
        "",
        "## Cobertura",
        "",
        f"- Sesiones CME Equity 2020–2024: **{report['session_rows']}**.",
        f"- Sesiones R1–R4 V2: **{report['classified_rows']}** "
        f"({100 * report['classified_share']:.1f}%).",
        f"- Sesiones R0 V2: **{report['r0_rows']}** "
        f"({100 * report['r0_share']:.1f}%).",
        f"- V1 tenía R1–R4: **{cmp['v1_classified_rows']}** de "
        f"**{cmp['v1_weekday_rows']}** ({100 * cmp['v1_classified_share']:.1f}%).",
        f"- Cambio absoluto de sesiones clasificadas: "
        f"**{cmp['classified_row_change']:+d}**.",
        "",
        "| Estado | Sesiones | Episodios | Mediana episodio |",
        "|---|---:|---:|---:|",
    ]
    for s in STATES:
        a = report["states"][s]
        lines.append(
            f"| {s} | {a['sessions']} | {a['episodes']} | "
            f"{a['median_episode_sessions']} |"
        )

    lines += [
        "",
        "## Motivos de R0",
        "",
        "| Motivo | V2 | V1 | Cambio |",
        "|---|---:|---:|---:|",
    ]
    reasons = sorted(
        set(report["r0_reasons"]) | set(cmp["v1_r0_reasons"])
    )
    for reason in reasons:
        v2 = int(report["r0_reasons"].get(reason, 0))
        v1 = int(cmp["v1_r0_reasons"].get(reason, 0))
        lines.append(f"| {reason} | {v2} | {v1} | {v2-v1:+d} |")

    lines += [
        "",
        "## Cobertura anual",
        "",
        "| Año | Sesiones | R1–R4 | R0 | Inputs READY |",
        "|---|---:|---:|---:|---:|",
    ]
    for year, a in report["annual"].items():
        lines.append(
            f"| {year} | {a['sessions']} | {a['classified']} | "
            f"{a['r0']} | {a['ready_inputs']} |"
        )

    lines += [
        "",
        "## Límites",
        "",
        "- V2 corrige disponibilidad/calendario; no demuestra que los estados sean rentables.",
        "- MAR25 se utilizó únicamente como contenedor para timestamps ET de 2024.",
        "- No existe ninguna fila de características de 2025 ni 2026.",
        "- No se calcularon forward returns, entradas, stops, targets, comisiones ni P&L.",
        "- MES 2026 continúa reservado para la estrategia final completamente congelada.",
        "",
        "Siguiente paso científico: registrar una familia acotada de pruebas de "
        "heterogeneidad por estado/tiempo antes de calcular outcomes.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw")
    p.add_argument("--preflight", action="store_true")
    args = p.parse_args()

    lock = preflight()
    if args.preflight:
        print("PASS: MES-MS2 freeze fingerprints and configuration match")
        return

    files = source_files(args.raw_dir)
    raw, manifest, rolls = build_continuous(files, "UTC", 0.25)

    # Critical boundary: MAR25 may contain 2025, but those rows are removed
    # before the state engine receives any data.
    raw = raw[raw.timestamp_et.dt.year.between(2020, 2024)].copy()
    if raw.empty:
        raise ValueError("no in-scope ET-calendar 2020-2024 rows")
    if (raw.timestamp_et.dt.year >= 2025).any():
        raise ValueError("2025 leaked past source filter")
    if raw.contract.str.endswith("-26").any():
        raise ValueError("2026 contract opened")

    inputs = causal_inputs(raw)
    features = classify(inputs)
    matrix, probabilities, episodes = diagnose(features)

    if features.empty:
        raise ValueError("empty feature map")
    if features.date.max() >= "2025-01-01":
        raise ValueError("2025 feature row created")
    if features.contract.str.endswith("-26").any():
        raise ValueError("2026 contract reached features")

    for r in features.itertuples():
        if r.source_max_et and pd.Timestamp(r.source_max_et) > pd.Timestamp(r.asof_et):
            raise ValueError("future bar reached pre-open feature")
        if r.previous_rth_date and r.previous_rth_date >= r.date:
            raise ValueError("same/future RTH used as previous RTH")

    v1 = json.loads(
        (ROOT / "results/market_state/MES_MS1_REPORT.json").read_text(encoding="utf-8")
    )
    v1_classified = sum(
        int(v1["states"][s]["weekday_rows"]) for s in ["R1", "R2", "R3", "R4"]
    )
    classified = int((features.regime != "R0").sum())

    report = {
        "version": VERSION,
        "authority": "DESCRIPTIVE_ONLY_NO_STRATEGY_PROMOTION",
        "source_scope": "20 MES 2020-2024 contracts + MAR25 source filtered to ET<=2024",
        "source_files": manifest.to_dict("records"),
        "source_rollovers": rolls.to_dict("records"),
        "minute_rows_after_scope_filter": int(len(raw)),
        "session_rows": int(len(features)),
        "classified_rows": classified,
        "classified_share": float(classified / len(features)),
        "r0_rows": int((features.regime == "R0").sum()),
        "r0_share": float((features.regime == "R0").mean()),
        "ready_input_rows": int((features.input_status == "READY").sum()),
        "states": state_summary(features, episodes),
        "r0_reasons": (
            features.loc[features.regime == "R0", "r0_reason"]
            .value_counts()
            .to_dict()
        ),
        "annual": annual_summary(features),
        "change_alerts": int(features.change_alert.sum()),
        "transition_counts": matrix.to_dict(orient="index"),
        "transition_proportions": json.loads(probabilities.to_json(orient="index")),
        "comparison_v1": {
            "v1_weekday_rows": int(v1["weekday_rows"]),
            "v1_classified_rows": int(v1_classified),
            "v1_classified_share": float(v1_classified / v1["weekday_rows"]),
            "v1_r0_rows": int(v1["states"]["R0"]["weekday_rows"]),
            "v1_r0_reasons": v1["r0_reasons"],
            "classified_row_change": int(classified - v1_classified),
        },
        "freeze": lock,
        "config": configuration(),
        "pandas_market_calendars_version": configuration()["calendar_package_version"],
        "strategy_authorized": False,
        "forward_returns_computed": False,
        "pnl_computed": False,
        "calendar_2025_features_computed": False,
        "calendar_2026_opened": False,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }

    out = ROOT / "results/market_state"
    out.mkdir(parents=True, exist_ok=True)
    features.to_csv(out / "MES_MS2_CAUSAL_FEATURES.csv", index=False)
    episodes.to_csv(out / "MES_MS2_EPISODES.csv", index=False)
    matrix.to_csv(out / "MES_MS2_TRANSITION_COUNTS.csv", index_label="from_state")
    probabilities.to_csv(
        out / "MES_MS2_TRANSITION_PROPORTIONS.csv", index_label="from_state"
    )
    (out / "MES_MS2_REPORT.json").write_text(
        json.dumps(report, indent=2, default=str, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    text = markdown(report)
    (out / "MES_MS2_REPORT.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
