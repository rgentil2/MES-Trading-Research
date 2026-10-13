#!/usr/bin/env python3
"""T05/T147 G0 ONLY: historical parent parity and ambiguity feasibility.

No combined portfolio calculation, no new alpha, no OOS, no public raw events.
This preflight is preregistered in NQ_T05_T147_SHARED_ROUTER_G0_PREFLIGHT_PREREG_2026_10_13.md.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS, month_days
from nq_b05h01_trade_expansion_month import frozen_t05
from nq_t04_execution import simulate_portfolio
from nq_t133_t152_executable_d0_batch import load_registry
from nq_t133_t152_executable_d0_features import classify_day
from nq_t133_t168_d1_engine import (
    prepare_context, stop_and_side, first_future_groups, model_one
)

PREREG = "NQ_T05_T147_SHARED_ROUTER_G0_PREFLIGHT_PREREG_2026_10_13.md"
STRESS = "stress_1p5_fee_2ticks_each_side"
ID = "T147"
MODELLED = "MODELLED_EXECUTION_UNVERIFIED"
SOURCE = 140
READY = 135
T05_N = 115
T05_NET = 5102.50
T147_N = 20
T147_NET = 642.25
SAFE_KEYS = (
    "stage", "source_sessions", "eligible_sessions", "t05_trades",
    "t05_net_stress_usd", "t05_unknown_or_aborted_days",
    "t147_cases", "t147_modelled_trades", "t147_net_base_usd",
    "t147_entry_group_ambiguous", "t147_instruments",
    "t147_not_modelled_statuses", "days_both_signal_families",
    "compatibility_state", "broker_fills_verified", "holdouts_opened",
    "source_is_old_licensed_dev_only", "new_data"
)


def guard_month(month):
    """Strict path gate BEFORE even listing or opening any source file."""
    if month not in MONTHS:
        raise ValueError("SEALED_MONTH_BEFORE_ANY_MARKET_IO")
    return month


def summarize_one_day(events, day, registry):
    """Consume only development in-memory Last for two FROZEN parents."""
    dev_day(day)
    status, bars, t05 = frozen_t05(events, day)
    if status != "READY":
        if status not in ("SKIP_MISSING_OPENING_RANGE", "SKIP_TINY_OPENING_RANGE"):
            raise ValueError("UNKNOWN_FROZEN_T05_QC")
        return {"eligible": False}
    baseline = simulate_portfolio(
        day, events, bars, [(ts_to_5s_index(day, ts), side) for ts, side, _ in t05],
        STRESS
    )
    frozen_label = classify_day(events, day, registry)[ID]
    record = {
        "eligible": True,
        "t05_n": baseline["trades"],
        "t05_net": baseline["net_usd"],
        "t05_unknown": int(baseline["day_aborted_due_to_ambiguity"]),
        "t147_case": int(frozen_label == "CASE"),
        "t147_n": 0,
        "t147_net": 0.0,
        "t147_ambiguous": 0,
        "t147_instrument": None,
        "t147_status": None,
        "both": False,
    }
    if frozen_label != "CASE":
        return record
    record["both"] = bool(t05)
    member = next(m for m in registry["members"] if m["id"] == ID)
    ctx = prepare_context(events, day)
    plan = stop_and_side(member, ctx)
    if plan is None:
        raise AssertionError("D0_CASE_WITHOUT_T147_FROZEN_SIDE_AND_STOP")
    side, stop, target_r, max_minutes = plan
    future, covered = first_future_groups(events, ctx["anchor"], max_minutes)
    model = model_one(
        future, side, stop, target_r, max_minutes, ctx["anchor"], covered
    )
    record["t147_status"] = model["status"]
    if model["status"] == MODELLED:
        record["t147_n"] = 1
        record["t147_net"] = model["net_usd"]
        record["t147_ambiguous"] = int(model["entry_group_ambiguous"])
        record["t147_instrument"] = model["instrument"]
    return record


def ts_to_5s_index(day, ts):
    """Unmodified T05 seconds-bar index; source order/decision unchanged."""
    from nq_tick_short_horizon import STEP_100NS
    from qc_tick_day import utc_bounds
    lo, _ = utc_bounds(dev_day(day))
    delta = ts - lo
    if delta <= 0 or delta % STEP_100NS:
        raise AssertionError("T05_DECISION_NOT_END_OF_5S_BAR")
    return delta // STEP_100NS - 1


def month_stage(root, month, registry):
    guard_month(month)
    rows = []
    source = 0
    for day in sorted(month_days(root, month)):
        d = dev_day(day)
        source += 1
        events = list(source_events(file_for(root, d, "Last")))
        rows.append(summarize_one_day(events, day, registry))
        del events  # no licensed Last values persisted
    cases = [r for r in rows if r["eligible"]]
    instruments = Counter(r["t147_instrument"] for r in cases if r["t147_n"])
    statuses = Counter(r["t147_status"] for r in cases if r["t147_case"] and
                       r["t147_status"] != MODELLED)
    return {
        "month": month,
        "source": source,
        "eligible": len(cases),
        "t05_n": sum(r["t05_n"] for r in cases),
        "t05_net": round(sum(r["t05_net"] for r in cases), 2),
        "t05_unknown": sum(r["t05_unknown"] for r in cases),
        "t147_cases": sum(r["t147_case"] for r in cases),
        "t147_n": sum(r["t147_n"] for r in cases),
        "t147_net": round(sum(r["t147_net"] for r in cases), 2),
        "t147_ambiguous": sum(r["t147_ambiguous"] for r in cases),
        "t147_instruments": dict(instruments),
        "t147_not_modelled": dict(statuses),
        "both": sum(r["both"] for r in cases),
        "licensed_ticks_in_output": False,
        "individual_dates_or_trades_in_output": False
    }


def aggregate(months):
    if set(months) != set(MONTHS):
        raise ValueError("EXACTLY_SEVEN_DEV_MONTHS_REQUIRED")
    keys = ("source", "eligible", "t05_n", "t05_net", "t05_unknown",
            "t147_cases", "t147_n", "t147_net", "t147_ambiguous", "both")
    cnt = Counter()
    ins, statuses = Counter(), Counter()
    for month in MONTHS:
        row = months[month]
        if (row["month"] != month or row["licensed_ticks_in_output"] is not False
                or row["individual_dates_or_trades_in_output"] is not False):
            raise AssertionError("INVALID_MONTH_OR_PRIVATE_OUTPUT_LEAK")
        cnt.update({k: row[k] for k in keys})
        ins.update(row["t147_instruments"])
        statuses.update(row["t147_not_modelled"])
    if (cnt["source"], cnt["eligible"]) != (SOURCE, READY):
        raise AssertionError("SOURCE_COVERAGE_NOT_140_135")
    if cnt["t05_n"] != T05_N or abs(cnt["t05_net"] - T05_NET) > .01:
        raise AssertionError("FROZEN_T05_PARENT_PARITY_FAIL")
    if cnt["t147_n"] != T147_N or abs(cnt["t147_net"] - T147_NET) > .01:
        raise AssertionError("FROZEN_T147_PARENT_PARITY_FAIL")
    # This merely decides if chronological exposure reconstruction is possible.
    state = ("G0_PARENT_PARITY_OK_SHARED_ROUTER_BLOCKED"
             if cnt["t147_ambiguous"] else
             "G0_PARENT_PARITY_OK_EXPOSURE_REPLAY_REQUIRED")
    out = {
        "stage": "T05_T147_G0_SHARED_ROUTER_COMPATIBILITY_ONLY",
        "source_sessions": cnt["source"],
        "eligible_sessions": cnt["eligible"],
        "t05_trades": cnt["t05_n"],
        "t05_net_stress_usd": round(cnt["t05_net"], 2),
        "t05_unknown_or_aborted_days": cnt["t05_unknown"],
        "t147_cases": cnt["t147_cases"],
        "t147_modelled_trades": cnt["t147_n"],
        "t147_net_base_usd": round(cnt["t147_net"], 2),
        "t147_entry_group_ambiguous": cnt["t147_ambiguous"],
        "t147_instruments": dict(ins),
        "t147_not_modelled_statuses": dict(statuses),
        "days_both_signal_families": cnt["both"],
        "compatibility_state": state,
        "broker_fills_verified": False,
        "holdouts_opened": False,
        "source_is_old_licensed_dev_only": True,
        "new_data": False,
    }
    if set(out) != set(SAFE_KEYS):
        raise AssertionError("SAFE_AGGREGATE_SCHEMA_CHANGED")
    return out


def report(s):
    return "\n".join((
        "# NQ T05 + T147 — G0 compatibilidad de padres, no backtest combinado",
        "",
        "**Solo siete meses DEV Last existentes, sin abrir holdouts ni descargar nueva historia.**",
        "",
        f"- Sesiones: {s['source_sessions']} fuente / {s['eligible_sessions']} elegibles.",
        f"- T05 congelada: {s['t05_trades']} operaciones, "
        f"neto estrés US${s['t05_net_stress_usd']:,.2f}.",
        f"- T147 D1 congelada: {s['t147_modelled_trades']} operaciones "
        f"entre {s['t147_cases']} CASE, neto base US${s['t147_net_base_usd']:,.2f}.",
        f"- T147 entradas con exposición ambigua dentro de un mismo timestamp: "
        f"{s['t147_entry_group_ambiguous']}.",
        f"- Instrumentos T147 NQ/MNQ seleccionados por modelo: {s['t147_instruments']}.",
        f"- Días con señales de ambas familias: {s['days_both_signal_families']}.",
        f"- Resultado G0: **{s['compatibility_state']}**.",
        "",
        "No hay beneficio incremental, PF/DD de una cartera ni simulación trailing de fondeo.",
        "La paridad de padres NO garantiza reconstrucción causal de entradas y salidas.",
        "Sin Bid/Ask ejecutable ni fills verificados; sin D1/D2 formal aprobado.",
        "",
    ))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--month")
    p.add_argument("--root", type=Path)
    p.add_argument("--inputs", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    if a.month is not None:
        guard_month(a.month)  # before reading ANY private path
        if a.root is None:
            raise ValueError("ROOT_REQUIRED")
        result = month_stage(a.root, a.month, load_registry())
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(result, sort_keys=True) + "\n")
        print("T05_T147_G0_MONTH_SAFE=" + json.dumps({
            "month": a.month, "source": result["source"],
            "eligible": result["eligible"],
            "t147_cases": result["t147_cases"],
            "t147_ambiguous": result["t147_ambiguous"],
        }, sort_keys=True))
    else:
        if not a.inputs or not a.report:
            raise ValueError("SEVEN_MONTH_INPUTS_AND_REPORT_REQUIRED")
        months = {
            m: json.loads((a.inputs / f"g0_t05_t147_{m}.json").read_text())
            for m in MONTHS
        }
        result = aggregate(months)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        a.report.write_text(report(result) + "\n")
        print("T05_T147_G0_SAFE_FINAL=" + json.dumps(result, sort_keys=True))
