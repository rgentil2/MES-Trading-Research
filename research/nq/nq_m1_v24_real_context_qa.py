#!/usr/bin/env python3
"""NQ IST real-source *technical* indicator/context QA, no strategies or PnL.

This verifies that the already integrated OHLC indicator reader consumes
prior RTH sessions of the SAME explicitly selected contract, and never reads
a future current-session bar. Selected moments are deterministic and include
every quarter roll boundary. No entries, trades, positions, fills or strategy
outcomes are evaluated; report exports only aggregate counts.
"""
from __future__ import annotations
import json
from pathlib import Path
from math import isclose
import numpy as np

from research.nq.nq_m1_chrono_discovery import load_years
from research.nq.nq_m1_v22_contract_provenance import metadata_for_sessions, prior_same_contract
from research.nq.nq_m1_v21_warmup_context import indicator_at
from research.nq.nq_m1_v2_orders import _causal_reader, _validate_context
from research.nq.nq_m1_v22_quality_gate import audit as quality_audit

IST = (2020, 2021, 2022)
INDICATORS = (
    {"name": "SMA", "parameters": {"period": 390, "source": "close"}},
    {"name": "ATR", "parameters": {"period": 14}},
    {"name": "Z-Score", "parameters": {"period": 40}},
    {"name": "VWAP", "parameters": {"anchor": "session"}},
    {"name": "OBV", "parameters": {}},
)
BAR_ENDPOINTS = (10, 118, 389)
LOCAL = frozenset(("VWAP", "OBV"))


def _equal(a: float | None, b: float | None) -> bool:
    return a is None and b is None or (
        a is not None and b is not None and
        np.isfinite(a) and np.isfinite(b) and
        isclose(a, b, rel_tol=1e-9, abs_tol=1e-7)
    )


def check_selected_sessions(dates: list[str], bars: np.ndarray) -> dict:
    """Runs purely structural/numerical QA; returns no market price or trade."""
    if len(dates) != len(bars) or len(dates) < 3:
        raise ValueError("Expected ordered IST complete RTH sessions")
    meta = metadata_for_sessions(dates, bars)
    rolls = [i for i in range(1, len(meta))
             if meta[i].contract_id != meta[i-1].contract_id]
    selections = sorted(set([0, len(dates)//2, len(dates)-1] + rolls))
    positions = {d:i for i,d in enumerate(dates)}
    compared = checked_causal = missing_warmups = 0
    for idx in selections:
        session = dates[idx]
        ctx = prior_same_contract(dates, bars, idx)
        history = _validate_context(session, ctx)
        previous = [(meta[positions[d]], bars[positions[d]])
                    for d in ctx["prior_session_dates"]]
        reader = _causal_reader(history)
        if idx in rolls and len(history) != 0:
            raise AssertionError("Cross-roll warmup contamination")
        for decision in BAR_ENDPOINTS:
            for spec in INDICATORS:
                from_context = indicator_at(meta[idx], bars[idx], decision,
                                            spec, previous)
                from_runner = reader(bars[idx], decision, spec)
                if not _equal(from_context, from_runner):
                    raise AssertionError(
                        f"Context/runner indicator mismatch: {idx}, {decision}, {spec['name']}"
                    )
                compared += 1
                if from_runner is None:
                    missing_warmups += 1
                if decision < 389:
                    future_altered = bars[idx].copy()
                    future_altered[decision+1:, 3] += 50.0
                    observed = reader(future_altered, decision, spec)
                    if not _equal(from_runner, observed):
                        raise AssertionError("Future OHLC bar influenced indicator")
                    checked_causal += 1
    return {
        "status": "NQ_IST_REAL_CONTEXT_INDICATORS_TECHNICAL_ONLY",
        "source_sessions": len(dates),
        "selected_contexts": len(selections),
        "roll_boundaries": len(rolls),
        "indicator_context_comparisons": compared,
        "future_bar_mutation_checks": checked_causal,
        "unavailable_indicators_recorded_not_imputed": missing_warmups,
        "years_opened": list(IST),
        "contract_roll_policy_modified": False,
        "market_prices_exported": False,
        "signals_or_trades_evaluated": False,
        "pnl_or_fills_evaluated": False,
        "holdouts": "SEALED",
        "releases_all_13_quality_gates": False,
    }


def audit_archive(zip_path: Path) -> dict:
    # Fail closed before any market/archive file is loaded.
    gate = quality_audit()
    if gate["ready_for_economic_execution"] or gate["asset"] != "NQ":
        raise PermissionError("Technical QA must not silently enable economic execution")
    dates, bars, source = load_years(zip_path, IST)
    if source["years_opened"] != list(IST) or source["holdout_2025_opened"] or source["holdout_2026_opened"]:
        raise PermissionError("Sealed stage touched")
    return check_selected_sessions(dates, bars)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit_archive(args.zip)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
