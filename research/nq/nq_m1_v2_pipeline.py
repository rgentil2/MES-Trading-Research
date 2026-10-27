#!/usr/bin/env python3
"""NQ M1 V2 fail-closed integration contracts + one-account shadow portfolio router.

This is NOT a claim that legacy cohort-specific G0/D0/D1/D2 have been re-run,
nor that a portfolio has real broker fills. No market archive is read here.
"""
from __future__ import annotations
from collections import defaultdict, Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
import random
from typing import Any

IST_YEARS = (2020, 2021, 2022)
SEALED_YEARS = (2025, 2026)
REFERENCE_ACCOUNT = {
    "max_open_positions": 1,
    "max_entries_per_day": 2,
    "daily_closed_pnl_pause_usd": -600.,
    "max_initial_stop_risk_usd": 300.,
    "max_allowed_reference_drawdown_usd": 2000.,
}
# These are legacy research engines with frozen, cohort-specific semantics.
# They may contribute code after an explicit V2 adapter and parity tests;
# direct invocation on V2 strategy dictionaries is NOT safe.
LEGACY_VALIDATORS = {
    "G0": {
        "sources": ["local_nq_tick_2025_2026/nq_t05_t147_g0_preflight.py",
                    "local_nq_tick_2025_2026/nq_t209_t228_structural_d0.py"],
        "status": "ADAPTER_REQUIRED_COHORT_SPECIFIC"},
    "D0": {
        "sources": ["local_nq_tick_2025_2026/nq_t133_t168_combined_D0_batch.py",
                    "local_nq_tick_2025_2026/nq_t209_t228_structural_d0.py"],
        "status": "ADAPTER_REQUIRED_COHORT_SPECIFIC"},
    "D1": {
        "sources": ["local_nq_tick_2025_2026/nq_t133_t168_d1_engine.py",
                    "local_nq_tick_2025_2026/nq_t133_t168_economic_d1_batch.py"],
        "status": "ADAPTER_REQUIRED_COHORT_SPECIFIC"},
    "D2": {
        "sources": ["local_nq_tick_2025_2026/nq_t133_t168_shadow_d2_portfolios.py",
                    "local_nq_tick_2025_2026/nq_nine_d2_t05_t224_shadow.py"],
        "status": "ADAPTER_REQUIRED_COHORT_SPECIFIC"},
}
FORMAL_GATE_STATES = {"PENDING_ADAPTER", "FAILED", "PASSED_VERIFIED"}


def adapter_state() -> dict:
    """No implicit PASS from legacy name-matching."""
    return {k: {"state": "PENDING_ADAPTER", "legacy_sources": v["sources"],
                "reason": v["status"]} for k, v in LEGACY_VALIDATORS.items()}


def validate_candidate_envelope(record: dict) -> None:
    """G0 technical contract only; distinct from legacy formal G0."""
    from research.nq.nq_m1_v2_generator import STRATEGY_SCHEMA, fingerprint
    if (record.get("schema") != STRATEGY_SCHEMA
            or record.get("market_data_years_permitted_for_discovery") != list(IST_YEARS)
            or record.get("signal_clock") != "America/New_York"
            or record.get("bars_are_end_labeled") is not True
            or record.get("signal_uses_completed_bars_only") is not True
            or record.get("exit", {}).get("flat_at_et") != "11:29"
            or not isinstance(record.get("exit", {}).get("stop_loss_required"), dict)
            or record.get("entry_order", {}).get("kind") not in {"MARKET", "LIMIT", "STOP"}):
        raise ValueError("INVALID_V2_G0_TECHNICAL_ENVELOPE")
    observed = record.get("lineage", {}).get("fingerprint_sha256")
    if observed and observed != fingerprint(record):
        raise ValueError("CANDIDATE_FINGERPRINT_MISMATCH")


def stage_contract(stage: str, years: tuple[int, ...], frozen_manifest: str | None) -> dict:
    planned = {"IST": IST_YEARS, "ISV1": (2023,), "ISV2": (2024,)}
    if stage not in planned or tuple(years) != planned[stage]:
        raise PermissionError("Stage/years prohibited; 2025-2026 remain sealed")
    if stage != "IST" and (not frozen_manifest or len(frozen_manifest) != 64
                           or any(c not in "0123456789abcdef" for c in frozen_manifest)):
        raise PermissionError("ISV1/ISV2 require valid immutable SHA256 frozen manifest")
    return {"stage": stage, "years_permitted": list(years),
            "frozen_manifest": frozen_manifest,
            "H2025_H2026": "SEALED"}


def portfolio_candidates(ids: list[str], count: int, seed: int = 20261027,
                         min_size: int = 2, max_size: int = 8) -> list[dict]:
    """Structural basket definitions; no outcome-based portfolio optimization."""
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate strategy IDs")
    if min_size < 2 or max_size < min_size or count < 1:
        raise ValueError("Invalid portfolio search dimensions")
    if len(ids) < min_size:
        raise ValueError("Insufficient distinct strategies")
    rng = random.Random(seed)
    unique = set()
    res = []
    max_possible = sum(math.comb(len(ids), k) for k in range(min_size, min(max_size, len(ids)) + 1))
    if count > max_possible:
        raise ValueError("More requested baskets than possible")
    trials = 0
    while len(res) < count:
        trials += 1
        if trials > count * 1000:
            raise RuntimeError("Could not create nonduplicate basket count")
        k = rng.randint(min_size, min(max_size, len(ids)))
        members = tuple(sorted(rng.sample(ids, k)))
        if members in unique:
            continue
        unique.add(members)
        res.append({"portfolio_id": f"NQ-V2-PORT-{seed}-{len(res)+1:05d}",
                    "members": list(members), "priority": list(members),
                    "priority_rule": "LEXICOGRAPHIC_FROZEN_ID",
                    "status": "STRUCTURAL_NOT_BACKTESTED"})
    return res


def simulate_shadow_router(trades: list[dict], priority: list[str],
                           policy: dict | None = None) -> dict:
    """Replay precomputed *model* trades on one shadow account. No price reads.

    Inputs include YYYY-MM-DD, integer signal_idx/entry_idx/exit_idx,
    strategy_id, initial_risk_usd and net_usd. Deduplicates simultaneous
    proposals deterministically. Precomputed per-strategy fills must NOT be
    described as broker fills, true intrabar drawdown, or fully proven PnL:
    each trade is a model outcome with its own unstated execution assumptions.
    """
    p = dict(REFERENCE_ACCOUNT if policy is None else policy)
    if (p["max_open_positions"] != 1 or p["max_entries_per_day"] < 1
            or p["max_initial_stop_risk_usd"] <= 0
            or p["daily_closed_pnl_pause_usd"] >= 0):
        raise ValueError("Invalid one-account policy")
    if not priority or len(set(priority)) != len(priority):
        raise ValueError("Priority must have distinct strategy IDs")
    rank = {sid: i for i, sid in enumerate(priority)}
    for t in trades:
        if set(t) < {"date", "strategy_id", "signal_idx", "entry_idx", "exit_idx",
                     "initial_risk_usd", "net_usd"}:
            raise ValueError("Trade is missing a required field")
        if t["strategy_id"] not in rank:
            raise ValueError("Unknown strategy not in frozen portfolio")
        day = t["date"]
        if not isinstance(day, str) or len(day) != 10 or int(day[:4]) not in IST_YEARS:
            raise PermissionError("Shadow router only accepts explicit IST 2020-22 dates")
        if not (isinstance(t["signal_idx"], int) and
                isinstance(t["entry_idx"], int) and isinstance(t["exit_idx"], int)
                and 0 <= t["signal_idx"] < t["entry_idx"] <= t["exit_idx"] <= 118):
            raise ValueError("Invalid closed-bar causal indices/window")
        if (not math.isfinite(float(t["initial_risk_usd"])) or
                t["initial_risk_usd"] <= 0 or not math.isfinite(float(t["net_usd"]))):
            raise ValueError("Invalid model trade")
    ordered = sorted(trades, key=lambda t: (t["date"], t["signal_idx"],
                                           rank[t["strategy_id"]], t["strategy_id"]))
    # If any trade is rejected by risk/priority, never pretend it can be
    # substituted by another signal at the exact timestamp after its outcome.
    accepted = []
    rejected = Counter()
    for day, items in itertools.groupby(ordered, key=lambda t: t["date"]):
        opened_through = -1
        closed_pnl = 0.0
        entries = 0
        same_signal_times = set()
        for t in items:
            i = t["signal_idx"]
            if i in same_signal_times:
                rejected["SAME_TIMESTAMP_LOWER_PRIORITY"] += 1
                continue
            # Reserve the timestamp ONLY after a candidate is EX-ANTE
            # executable. If higher-priority NQ exceeds the risk cap, a
            # lower-priority NQ can still be considered using only risk
            # known before entry (never trade outcome or future PnL).
            # A strategy may evaluate at the exact bar that just closed
            # the prior position; its new entry is at the NEXT bar only.
            if i < opened_through:
                rejected["OVERLAPPING_POSITION"] += 1
                continue
            if entries >= p["max_entries_per_day"]:
                rejected["ENTRY_DAILY_LIMIT"] += 1
                continue
            if closed_pnl <= p["daily_closed_pnl_pause_usd"]:
                rejected["CLOSED_DAILY_PAUSE"] += 1
                continue
            if t["initial_risk_usd"] > p["max_initial_stop_risk_usd"]:
                rejected["RISK_CAP"] += 1
                continue
            same_signal_times.add(i)
            accepted.append(t)
            entries += 1
            closed_pnl += float(t["net_usd"])
            opened_through = t["exit_idx"]
    net = sum(float(t["net_usd"]) for t in accepted)
    return {"status": "IST_SHADOW_PRECOMPUTED_MODEL_NOT_BROKER_EXECUTION",
            "source": "EXTERNALLY_PRECOMPUTED_TRADES_FROM_IST_ONLY",
            "entries": len(accepted), "rejected": dict(rejected),
            "net_usd": round(net, 2),
            "accepted": accepted,
            "H2025_H2026": "SEALED"}


def exploratory_trade_metrics(net_usd: list[float]) -> dict[str, Any]:
    """Exploratory descriptive stats only; does NOT run D1/D2 formal gates."""
    if any(not math.isfinite(float(x)) for x in net_usd):
        raise ValueError("Nonfinite PnL")
    gross_win = sum(x for x in net_usd if x > 0)
    gross_loss = -sum(x for x in net_usd if x < 0)
    equity = peak = drawdown = 0.0
    for x in net_usd:
        equity += float(x)
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return {"n": len(net_usd), "net": round(sum(net_usd), 2),
            "expectancy": sum(net_usd) / len(net_usd) if net_usd else None,
            "profit_factor": gross_win / gross_loss if gross_loss > 0 else None,
            "closed_trade_drawdown": round(drawdown, 2),
            "gate": "EXPLORATORY_NOT_D1_D2_NOT_FLOATING_MLL"}


if __name__ == "__main__":
    print(json.dumps({"status": "V2_ADAPTER_CONTRACT_ONLY_NO_PRICES",
                      "gate_adapters": adapter_state(),
                      "H2025_H2026": "SEALED"}, sort_keys=True))
