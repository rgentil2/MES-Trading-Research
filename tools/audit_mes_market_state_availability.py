#!/usr/bin/env python3
"""MES-MS1 availability audit A1.

Descriptive only. No forward returns, trade labels, P&L or strategy outcomes.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_pipeline import build_continuous, contract_info, read_contract
from src.mes_market_state_v1 import causal_inputs, classify

OUT = ROOT / "results/market_state"
RAW = ROOT / "data/raw"


def source_files(include_mar25: bool) -> list[Path]:
    files = []
    for p in RAW.glob("MES ??-??.Last.txt"):
        year, month, _ = contract_info(p)
        if 2020 <= year <= 2024 or (include_mar25 and year == 2025 and month == 3):
            files.append(p)
    files = sorted(files, key=lambda p: contract_info(p)[:2])
    expected = {(y, m) for y in range(2020, 2025) for m in (3, 6, 9, 12)}
    actual_dev = {contract_info(p)[:2] for p in files if contract_info(p)[0] <= 2024}
    if actual_dev != expected:
        raise ValueError("missing 2020-2024 quarterly source files")
    if include_mar25 and not any(contract_info(p)[:2] == (2025, 3) for p in files):
        raise ValueError("MAR25 source required for late-2024 audit")
    return files


def raw_contract_frame(path: Path) -> pd.DataFrame:
    _, _, contract = contract_info(path)
    df = read_contract(path, tick_size=.25)
    df["timestamp_utc"] = df["timestamp"].dt.tz_localize("UTC")
    df["timestamp_et"] = df["timestamp_utc"].dt.tz_convert("America/New_York")
    # The MAR25 file is only a source container. Remove all non-2024/earlier
    # observations before any daily summaries are formed.
    df = df[df["timestamp_et"].dt.year.between(2020, 2024)].copy()
    df["contract"] = contract
    df["day"] = df["timestamp_et"].dt.date
    df["minute"] = df["timestamp_et"].dt.hour * 60 + df["timestamp_et"].dt.minute
    return df


def rth_table(df: pd.DataFrame) -> pd.DataFrame:
    rth = df[(df["minute"] > 570) & (df["minute"] <= 960)].copy()
    rows = []
    for day, g in rth.groupby("day", sort=True):
        rows.append(
            dict(
                day=str(day),
                bars=int(len(g)),
                first_minute=int(g["minute"].iloc[0]),
                last_minute=int(g["minute"].iloc[-1]),
                full=bool(
                    len(g) == 390
                    and g["minute"].iloc[0] == 571
                    and g["minute"].iloc[-1] == 960
                ),
            )
        )
    return pd.DataFrame(rows)


def md(report: dict) -> str:
    lines = [
        "# MES-MS1 Availability Audit A1",
        "",
        "Auditoría exclusivamente descriptiva. No se calcularon retornos futuros, P&L ni resultados de estrategia.",
        "",
        "## Hallazgos principales",
        "",
        f"- R0 por calentamiento de contrato en V1: **{report['v1_contract_warmup_rows']}**.",
        f"- De esos, con >=14 RTH completas ya observables en el archivo crudo del mismo contrato: **{report['warmup_recoverable_from_preroll']}**.",
        f"- R0 por RTH anterior incompleta en V1: **{report['v1_previous_rth_rows']}**.",
        f"- Casos donde el RTH del mismo contrato sí estaba completo en el archivo crudo: **{report['previous_rth_raw_full_same_contract']}**.",
        f"- Filas ET-2024 añadidas al continuo al permitir MAR25 sólo como contenedor de 2024: **{report['late_2024_added_minute_rows']:,}**.",
        f"- Fechas ET-2024 añadidas: **{report['late_2024_added_dates']}**.",
        f"- Último timestamp ET de V1: **{report['v1_last_et']}**.",
        f"- Último timestamp ET con MAR25 filtrado a 2024: **{report['extended_last_et']}**.",
        "",
        "## Historia pre-roll por contrato",
        "",
        "| Contrato | Primera fecha activa | RTH completas crudas previas |",
        "|---|---|---:|",
    ]
    for r in report["contract_preroll"]:
        lines.append(
            f"| {r['contract']} | {r['first_active_date']} | {r['raw_full_rth_before_activation']} |"
        )
    lines += [
        "",
        "## Interpretación",
        "",
        "Esta auditoría no cambia V1. Sólo determina si parte de R0 se produjo porque la serie continua descartó solapamientos del contrato entrante aunque esas barras ya existían y eran observables.",
        "",
        "Si los conteos recuperables son materiales, el siguiente paso es congelar una V2 que mantenga la selección de contrato activo del continuo, pero permita usar historia cruda causal del mismo contrato para ATR/trend al momento del rollover. CUSUM, cuantiles e histéresis no se ajustan por estos resultados.",
        "",
        "MES 2026 permaneció completamente cerrado.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    dev = source_files(False)
    ext = source_files(True)

    v1_cont, _, _ = build_continuous(dev, "UTC", .25)
    ext_cont, _, _ = build_continuous(ext, "UTC", .25)

    v1_cont = v1_cont[v1_cont.timestamp_et.dt.year.between(2020, 2024)].copy()
    ext_cont = ext_cont[ext_cont.timestamp_et.dt.year.between(2020, 2024)].copy()

    if v1_cont.empty or ext_cont.empty:
        raise ValueError("empty in-scope data")
    if (ext_cont.timestamp_et.dt.year > 2024).any():
        raise ValueError("2025 leaked into audit")
    if ext_cont.contract.str.endswith("-26").any():
        raise ValueError("2026 contract opened")

    features = classify(causal_inputs(v1_cont))

    baseline_path = OUT / "MES_MS1_REPORT.json"
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text())
        if len(features) != baseline["weekday_rows"]:
            raise ValueError("V1 baseline row count drifted")

    raw_daily: dict[str, pd.DataFrame] = {}
    for p in ext:
        _, _, contract = contract_info(p)
        raw_daily[contract] = rth_table(raw_contract_frame(p))

    first_active = (
        ext_cont.assign(day=ext_cont.timestamp_et.dt.date)
        .groupby("contract", sort=False)["day"]
        .min()
        .to_dict()
    )

    preroll = []
    for contract, first_day in first_active.items():
        t = raw_daily.get(contract, pd.DataFrame())
        if t.empty:
            full_before = 0
        else:
            full_before = int(
                ((t["full"]) & (pd.to_datetime(t["day"]).dt.date < first_day)).sum()
            )
        preroll.append(
            dict(
                contract=contract,
                first_active_date=str(first_day),
                raw_full_rth_before_activation=full_before,
            )
        )

    warm = features[
        (features.regime == "R0")
        & (features.r0_reason == "UNKNOWN_CONTRACT_WARMUP")
    ].copy()
    warm_rows = []
    for r in warm.itertuples():
        t = raw_daily.get(r.contract, pd.DataFrame())
        day = pd.Timestamp(r.date).date()
        prior_full = (
            int(((t["full"]) & (pd.to_datetime(t["day"]).dt.date < day)).sum())
            if not t.empty
            else 0
        )
        warm_rows.append(
            dict(
                date=r.date,
                contract=r.contract,
                raw_full_rth_before_date=prior_full,
                recoverable_from_preroll=bool(prior_full >= 14),
            )
        )
    warm_df = pd.DataFrame(warm_rows)

    prev = features[
        (features.regime == "R0")
        & (features.r0_reason == "UNKNOWN_PREVIOUS_RTH")
    ].copy()
    prev_rows = []
    for r in prev.itertuples():
        t = raw_daily.get(r.contract, pd.DataFrame())
        match = t[t["day"] == r.previous_rth_date] if not t.empty and r.previous_rth_date else pd.DataFrame()
        if match.empty:
            category = "RAW_NONE_SAME_CONTRACT"
            bars = 0
            full = False
        else:
            bars = int(match.iloc[-1]["bars"])
            full = bool(match.iloc[-1]["full"])
            category = "RAW_FULL_SAME_CONTRACT" if full else "RAW_PARTIAL_SAME_CONTRACT"
        prev_rows.append(
            dict(
                date=r.date,
                contract=r.contract,
                previous_rth_date=r.previous_rth_date,
                raw_same_contract_bars=bars,
                raw_same_contract_full=full,
                category=category,
            )
        )
    prev_df = pd.DataFrame(prev_rows)

    v1_last = v1_cont.timestamp_et.max()
    added = ext_cont[ext_cont.timestamp_et > v1_last].copy()
    added_dates = sorted({str(x) for x in added.timestamp_et.dt.date})

    report = dict(
        authority="DESCRIPTIVE_DATA_AVAILABILITY_ONLY",
        forward_returns_computed=False,
        pnl_computed=False,
        strategy_outcomes_computed=False,
        calendar_2025_features_computed=False,
        calendar_2026_opened=False,
        v1_contract_warmup_rows=int(len(warm)),
        warmup_recoverable_from_preroll=int(
            warm_df["recoverable_from_preroll"].sum() if not warm_df.empty else 0
        ),
        v1_previous_rth_rows=int(len(prev)),
        previous_rth_raw_full_same_contract=int(
            (prev_df["category"] == "RAW_FULL_SAME_CONTRACT").sum() if not prev_df.empty else 0
        ),
        previous_rth_raw_partial_same_contract=int(
            (prev_df["category"] == "RAW_PARTIAL_SAME_CONTRACT").sum() if not prev_df.empty else 0
        ),
        previous_rth_raw_none_same_contract=int(
            (prev_df["category"] == "RAW_NONE_SAME_CONTRACT").sum() if not prev_df.empty else 0
        ),
        v1_minute_rows=int(len(v1_cont)),
        extended_minute_rows=int(len(ext_cont)),
        late_2024_added_minute_rows=int(len(added)),
        late_2024_added_dates=int(len(added_dates)),
        late_2024_added_date_list=added_dates,
        v1_last_et=str(v1_last),
        extended_last_et=str(ext_cont.timestamp_et.max()),
        contract_preroll=preroll,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "MES_MS1_AVAILABILITY_AUDIT.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (OUT / "MES_MS1_AVAILABILITY_AUDIT.md").write_text(md(report))
    warm_df.to_csv(OUT / "MES_MS1_WARMUP_AUDIT.csv", index=False)
    prev_df.to_csv(OUT / "MES_MS1_PREVIOUS_RTH_AUDIT.csv", index=False)

    print(md(report))


if __name__ == "__main__":
    main()
