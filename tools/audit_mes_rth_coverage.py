#!/usr/bin/env python3
"""MES-MS1 RTH coverage audit A2. Descriptive only."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_pipeline import build_continuous, contract_info
from src.mes_market_state_v1 import causal_inputs, classify

RAW = ROOT / "data/raw"
OUT = ROOT / "results/market_state"
THRESHOLDS = [390, 385, 380, 370, 350]


def dev_files():
    files = sorted(
        [p for p in RAW.glob("MES ??-??.Last.txt") if 2020 <= contract_info(p)[0] <= 2024],
        key=lambda p: contract_info(p)[:2],
    )
    if len(files) != 20:
        raise ValueError("expected twenty 2020-2024 contracts")
    return files


def daily_rth(bars: pd.DataFrame) -> pd.DataFrame:
    b = bars.copy()
    b["day"] = b.timestamp_et.dt.date
    b["minute"] = b.timestamp_et.dt.hour * 60 + b.timestamp_et.dt.minute
    rth = b[(b.minute > 570) & (b.minute <= 960)]
    rows = []
    for (day, contract), g in rth.groupby(["day", "contract"], sort=True):
        rows.append(
            dict(
                day=str(day),
                year=int(pd.Timestamp(day).year),
                contract=contract,
                bars=int(len(g)),
                first_minute=int(g.minute.iloc[0]),
                last_minute=int(g.minute.iloc[-1]),
                has_0931=bool((g.minute == 571).any()),
                has_1600=bool((g.minute == 960).any()),
            )
        )
    d = pd.DataFrame(rows)
    if d.empty:
        raise ValueError("no RTH days")
    return d


def bucket(n: int) -> str:
    if n >= 390:
        return "390"
    if n >= 385:
        return "385-389"
    if n >= 380:
        return "380-384"
    if n >= 370:
        return "370-379"
    if n >= 350:
        return "350-369"
    if n >= 300:
        return "300-349"
    return "<300"


def main():
    cont, _, _ = build_continuous(dev_files(), "UTC", .25)
    cont = cont[cont.timestamp_et.dt.year.between(2020, 2024)].copy()
    features = classify(causal_inputs(cont))
    daily = daily_rth(cont)

    failures = features[
        (features.regime == "R0")
        & (features.r0_reason == "UNKNOWN_PREVIOUS_RTH")
    ].copy()

    detail = []
    key = {(r.day, r.contract): r for r in daily.itertuples()}
    for r in failures.itertuples():
        k = (r.previous_rth_date, r.contract)
        d = key.get(k)
        if d is None:
            detail.append(
                dict(
                    blocked_date=r.date,
                    previous_rth_date=r.previous_rth_date,
                    contract=r.contract,
                    bars=0,
                    has_0931=False,
                    has_1600=False,
                    bucket="<300",
                    same_contract_record_found=False,
                )
            )
        else:
            detail.append(
                dict(
                    blocked_date=r.date,
                    previous_rth_date=r.previous_rth_date,
                    contract=r.contract,
                    bars=int(d.bars),
                    has_0931=bool(d.has_0931),
                    has_1600=bool(d.has_1600),
                    bucket=bucket(int(d.bars)),
                    same_contract_record_found=True,
                )
            )
    detail = pd.DataFrame(detail)

    overall = {}
    for t in THRESHOLDS:
        overall[str(t)] = dict(
            days=int((daily.bars >= t).sum()),
            pct=float((daily.bars >= t).mean()),
            days_with_both_endpoints=int(
                ((daily.bars >= t) & daily.has_0931 & daily.has_1600).sum()
            ),
        )

    fail_thresholds = {}
    for t in THRESHOLDS:
        fail_thresholds[str(t)] = dict(
            cases=int((detail.bars >= t).sum()),
            pct=float((detail.bars >= t).mean()) if len(detail) else 0.0,
            cases_with_both_endpoints=int(
                ((detail.bars >= t) & detail.has_0931 & detail.has_1600).sum()
            ),
        )

    annual = {}
    for y in range(2020, 2025):
        yd = daily[daily.year == y]
        annual[str(y)] = {
            str(t): int((yd.bars >= t).sum()) for t in THRESHOLDS
        }
        annual[str(y)]["rth_days_observed"] = int(len(yd))

    report = dict(
        authority="DESCRIPTIVE_RTH_COVERAGE_ONLY",
        forward_returns_computed=False,
        pnl_computed=False,
        strategy_outcomes_computed=False,
        calendar_2025_opened=False,
        calendar_2026_opened=False,
        rth_days_observed=int(len(daily)),
        blocked_rows=int(len(detail)),
        blocked_bar_buckets=detail.bucket.value_counts().sort_index().to_dict(),
        blocked_has_0931=int(detail.has_0931.sum()),
        blocked_has_1600=int(detail.has_1600.sum()),
        blocked_has_both_endpoints=int((detail.has_0931 & detail.has_1600).sum()),
        overall_thresholds=overall,
        blocked_thresholds=fail_thresholds,
        annual_thresholds=annual,
    )

    lines = [
        "# MES-MS1 RTH Coverage Audit A2",
        "",
        "Sin retornos futuros, P&L ni selección de estrategia.",
        "",
        f"RTH observadas: **{report['rth_days_observed']}**.",
        f"Filas V1 bloqueadas por RTH anterior incompleta: **{report['blocked_rows']}**.",
        "",
        "## Distribución de las 169 sesiones bloqueantes",
        "",
        "| Barras observadas | Casos |",
        "|---|---:|",
    ]
    for k, v in report["blocked_bar_buckets"].items():
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        f"Con 09:31 presente: **{report['blocked_has_0931']}**.",
        f"Con 16:00 presente: **{report['blocked_has_1600']}**.",
        f"Con ambos extremos presentes: **{report['blocked_has_both_endpoints']}**.",
        "",
        "## Sensibilidad puramente descriptiva",
        "",
        "| Mínimo de barras | Casos bloqueantes que alcanzarían el mínimo | Con ambos extremos |",
        "|---:|---:|---:|",
    ]
    for t in THRESHOLDS:
        a = report["blocked_thresholds"][str(t)]
        lines.append(
            f"| {t} | {a['cases']} | {a['cases_with_both_endpoints']} |"
        )
    lines += [
        "",
        "No se elige ningún umbral aquí. El objetivo es saber si exigir 390/390 está confundiendo ausencia de trades en algunos minutos con pérdida real de sesión.",
        "",
        "MES 2026 permaneció cerrado.",
        "",
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "MES_MS1_RTH_COVERAGE_AUDIT.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (OUT / "MES_MS1_RTH_COVERAGE_AUDIT.md").write_text("\n".join(lines))
    detail.to_csv(OUT / "MES_MS1_RTH_COVERAGE_BLOCKED.csv", index=False)
    daily.to_csv(OUT / "MES_MS1_RTH_COVERAGE_DAILY.csv", index=False)

    print("\n".join(lines))


if __name__ == "__main__":
    main()
