#!/usr/bin/env python3
"""NQ M1 V2 structural candidate generation, no market reads or validated performance.

The 132-block registry is DESIGN inventory. This program creates reproducible,
causal-AST *specifications*, NOT 132 already executable indicator implementations.
Economic genetic selection requires external IST-only fitness in a future adapter.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import random
from pathlib import Path

CATALOG_PATH = Path(__file__).with_name("NQ_M1_V2_INDICATOR_CATALOG_2026_10_27.json")
HOLDOUTS = (2025, 2026)
IST = (2020, 2021, 2022)
SEED = 20261027
ENTRY_TYPES = ("MARKET", "LIMIT", "STOP")
SL_TYPES = ("FIXED_POINTS", "ATR", "STRUCTURE", "CHANDELIER")
TP_TYPES = ("NONE", "R_MULTIPLE", "FIXED_POINTS", "ATR", "CAUSAL_LEVEL")
STRATEGY_SCHEMA = "NQ_M1_V2_STRATEGY_AST_1"


def read_registry(path: Path = CATALOG_PATH) -> dict:
    r = json.loads(path.read_text(encoding="utf8"))
    entries = r["entries"]
    if (r.get("schema") != "NQ_M1_V2_INDICATOR_REGISTRY_V1"
            or len(entries) != 132 or r.get("indicator_count") != 120
            or r.get("pattern_count") != 12
            or len(set(e["id"] for e in entries)) != 132
            or len(set(e["name"] for e in entries)) != 132
            or any(e["status"] != "REGISTERED_NOT_YET_CERTIFIED" for e in entries)
            or r["stage_years"] != {"IST": [2020, 2021, 2022], "ISV1": [2023], "ISV2": [2024]}
            or r["prohibited_data"] != ["H2025", "H2026", "T_HOLDOUT"]):
        raise ValueError("V2 registry integrity or sealed-year guarantee broken")
    counts = {}
    for e in entries:
        counts[e["group"]] = counts.get(e["group"], 0) + 1
    if len(counts) != 11 or set(counts.values()) != {12}:
        raise ValueError("Unexpected group distribution")
    return r


def permitted_years_for_generation(years: tuple[int, ...]) -> bool:
    """Fail closed: search/fitness/selection must only see IST."""
    if tuple(years) != IST:
        raise PermissionError("V2 discovery is IST 2020-22 only; ISV/holdouts unavailable to the generator")
    return True


def _num(rng: random.Random, lo: float, hi: float, is_int: bool, name: str):
    if lo > hi:
        raise ValueError("Invalid parameter interval")
    if lo == hi:
        return int(lo) if is_int else float(lo)
    if (is_int and lo >= 1 and hi / lo >= 8 and
            any(s in name for s in ("period", "minutes", "lookback", "sessions_back"))):
        value = math.exp(rng.uniform(math.log(lo), math.log(hi)))
    else:
        value = rng.uniform(lo, hi)
    return max(int(lo), min(int(hi), round(value))) if is_int else round(value, 5)


def sample_parameters(rng: random.Random, parameter_ranges: dict) -> dict:
    values = {}
    for key, r in parameter_ranges.items():
        if isinstance(r, list) and len(r) == 2 and all(type(x) in (int, float) for x in r):
            is_int = all(type(x) is int for x in r)
            values[key] = _num(rng, r[0], r[1], is_int, key)
        elif isinstance(r, list) and r and all(type(x) is str for x in r):
            values[key] = rng.choice(r)
        elif key == "constraint" and r == "fast_period < slow_period":
            continue
        else:
            raise ValueError(f"Unsupported parameter domain: {key}={r!r}")
    if parameter_ranges.get("constraint") == "fast_period < slow_period":
        if values["fast_period"] >= values["slow_period"]:
            lo, hi = parameter_ranges["slow_period"]
            values["slow_period"] = min(hi, max(lo, values["fast_period"] + 1))
            if values["fast_period"] >= values["slow_period"]:
                values["fast_period"] = min(values["slow_period"] - 1, parameter_ranges["fast_period"][1])
        if values["fast_period"] >= values["slow_period"]:
            raise ValueError("MACD-family parameter range lacks a feasible solution")
    return values


def sample_block(rng: random.Random, registry: dict) -> dict:
    # Independently and uniformly samples one of the 132 registered blocks;
    # it is NOT claiming that this block is already computable on market data.
    item = rng.choice(registry["entries"])
    return {"registry_id": item["id"], "name": item["name"],
            "parameters": sample_parameters(rng, item["parameters"])}


def sample_leaf(rng: random.Random, registry: dict) -> dict:
    return {"op": rng.choice(["RISING", "FALLING", "ABOVE_LAG", "BELOW_LAG", "CROSSES_OWN_LAG"]),
            "indicator": sample_block(rng, registry),
            "lag_completed_bars": rng.randint(1, 20)}


def sample_expr(rng: random.Random, registry: dict, max_conditions: int = 8) -> dict:
    if max_conditions < 1:
        raise ValueError("max_conditions must be at least one")
    leaves = [sample_leaf(rng, registry) for _ in range(rng.randint(1, max_conditions))]
    while len(leaves) > 1:
        a = leaves.pop(rng.randrange(len(leaves)))
        b = leaves.pop(rng.randrange(len(leaves)))
        leaves.append({"op": rng.choice(["AND", "OR"]), "left": a, "right": b})
    return leaves[0]


def sample_exit(rng: random.Random) -> dict:
    sl_type = rng.choice(SL_TYPES)
    if sl_type == "FIXED_POINTS":
        stop = {"kind": sl_type, "points": round(rng.uniform(1, 120) * 4) / 4}
    elif sl_type == "ATR":
        stop = {"kind": sl_type, "period": rng.randint(2, 240),
                "multiple": round(rng.uniform(.25, 6), 3)}
    elif sl_type == "STRUCTURE":
        stop = {"kind": sl_type, "lookback": rng.randint(2, 120),
                "buffer_ticks": rng.randint(0, 16)}
    else:
        stop = {"kind": sl_type, "period": rng.randint(3, 120),
                "atr_multiple": round(rng.uniform(.5, 6), 3)}
    tp_type = rng.choice(TP_TYPES)
    if tp_type == "NONE":
        tp = {"kind": "NONE"}
    elif tp_type == "R_MULTIPLE":
        tp = {"kind": tp_type, "risk_multiple": round(rng.uniform(.25, 8), 3)}
    elif tp_type == "FIXED_POINTS":
        tp = {"kind": tp_type, "points": round(rng.uniform(1, 240) * 4) / 4}
    elif tp_type == "ATR":
        tp = {"kind": tp_type, "period": rng.randint(2, 240),
              "multiple": round(rng.uniform(.25, 10), 3)}
    else:
        tp = {"kind": tp_type, "reference": rng.choice(["VWAP", "PREVIOUS_COMPLETED_SESSION_LEVEL", "PIVOT"])}
    trailing = None if rng.randrange(2) == 0 else {
        "start_r": round(rng.uniform(.25, 4), 3),
        "distance_atr": round(rng.uniform(.25, 5), 3),
        "atr_period": rng.randint(2, 120)}
    breakeven = None if rng.randrange(2) == 0 else {
        "start_r": round(rng.uniform(.5, 3), 3), "plus_ticks": rng.randint(0, 4)}
    return {"stop_loss_required": stop, "profit_target": tp,
            "trailing": trailing, "break_even": breakeven,
            "exit_after_bars": rng.choice([None, rng.randint(1, 119)]),
            "flat_at_et": "11:29"}


def sample_strategy(rng: random.Random, registry: dict, max_conditions: int = 8) -> dict:
    typ = rng.choice(ENTRY_TYPES)
    return {
        "schema": STRATEGY_SCHEMA,
        "universe": "NQ_M1",
        "market_data_years_permitted_for_discovery": list(IST),
        "signal_clock": "America/New_York",
        "bars_are_end_labeled": True,
        "signal_uses_completed_bars_only": True,
        "long": sample_expr(rng, registry, max_conditions),
        "short": sample_expr(rng, registry, max_conditions),
        "entry_order": {"kind": typ,
                        "offset_ticks": rng.randint(0, 32) if typ != "MARKET" else 0,
                        "expiry_bars": rng.randint(1, 30) if typ != "MARKET" else 1},
        "exit": sample_exit(rng)
    }


def fingerprint(strategy: dict) -> str:
    stable = {k: v for k, v in strategy.items() if k not in ("id", "lineage")}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def mutate(rng: random.Random, parent: dict, registry: dict) -> dict:
    obj = copy.deepcopy(parent)
    obj.pop("id", None)
    obj.pop("lineage", None)
    branch = rng.choice(["long", "short", "exit", "entry_order"])
    if branch in ("long", "short"):
        obj[branch] = sample_expr(rng, registry)
    elif branch == "exit":
        obj["exit"] = sample_exit(rng)
    else:
        kind = rng.choice(ENTRY_TYPES)
        obj["entry_order"] = {"kind": kind,
                              "offset_ticks": rng.randint(0, 32) if kind != "MARKET" else 0,
                              "expiry_bars": rng.randint(1, 30) if kind != "MARKET" else 1}
    return obj


def crossover(rng: random.Random, first: dict, second: dict) -> dict:
    obj = copy.deepcopy(first)
    obj.pop("id", None)
    obj.pop("lineage", None)
    for key in rng.sample(["long", "short", "entry_order", "exit"], k=rng.randint(1, 3)):
        obj[key] = copy.deepcopy(second[key])
    return obj


def generate_batch(count: int, seed: int = SEED, random_fraction: float = .6,
                   max_conditions: int = 8, parent_pool: list[dict] | None = None,
                   registry: dict | None = None) -> list[dict]:
    """Bounded reproducible batch (not a ceiling on the research programme).
    Without externally supplied IST-scored parents, genetic steps are structural
    recombination, NOT profitability-driven evolution.
    """
    if count <= 0 or count > 100_000:
        raise ValueError("Batch size must be 1..100000; run more batches to continue")
    if not 0 <= random_fraction <= 1:
        raise ValueError("random_fraction must be in [0,1]")
    permitted_years_for_generation(IST)
    registry = read_registry() if registry is None else registry
    rng = random.Random(seed)
    pool = [copy.deepcopy(p) for p in (parent_pool or [])]
    if any(p.get("schema") != STRATEGY_SCHEMA or p.get("market_data_years_permitted_for_discovery") != list(IST) for p in pool):
        raise ValueError("Invalid parent or non-IST provenance")
    out, fingerprints = [], {fingerprint(p) for p in pool}
    trials = 0
    while len(out) < count:
        trials += 1
        if trials > count * 250:
            raise RuntimeError("Unable to build enough distinct strategies under supplied domain")
        if rng.random() < random_fraction or not pool:
            s = sample_strategy(rng, registry, max_conditions)
            source = "RANDOM"
        else:
            if len(pool) > 1 and rng.random() < .7:
                a, b = rng.sample(pool, 2)
                s = crossover(rng, a, b)
                source = "CROSSOVER"
            else:
                s = mutate(rng, rng.choice(pool), registry)
                source = "MUTATION"
        sha = fingerprint(s)
        if sha in fingerprints:
            continue
        fingerprints.add(sha)
        s["id"] = f"NQ-M1-V2-{seed}-{len(out)+1:06d}"
        s["lineage"] = {"method": source, "fingerprint_sha256": sha}
        out.append(s)
        pool.append(s)
    return out


def pareto_front_ist_only(rows: list[dict], stage: str) -> list[str]:
    """Exploratory non-dominated ranking; does not certify any gate.
    Score rows require NET (higher), PF (higher), DD (lower), TRADES (higher).
    Cross-year/holdout scores are prohibited, and multiplicity remains mandatory.
    """
    if stage != "IST":
        raise PermissionError("Only IST outcomes may rank/evolve candidates")
    keys = ("net", "profit_factor", "drawdown", "trades")
    if any(not all(k in r for k in keys) for r in rows):
        raise ValueError("Missing scores")
    if any(not all(math.isfinite(float(r[k])) for k in keys) for r in rows):
        raise ValueError("Infinite/non-finite score")
    maximize = lambda r: (r["net"], r["profit_factor"], -r["drawdown"], r["trades"])
    result = []
    for r in rows:
        v = maximize(r)
        if not any(other["id"] != r["id"] and
                   all(a >= b for a, b in zip(maximize(other), v)) and
                   any(a > b for a, b in zip(maximize(other), v)) for other in rows):
            result.append(r["id"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("registry", "generate"), required=True)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--random-fraction", type=float, default=.6)
    args = parser.parse_args()
    catalog = read_registry()
    if args.mode == "registry":
        print(json.dumps({"state": "REGISTER_ONLY_NO_PRICES",
                          "total": len(catalog["entries"]),
                          "groups": catalog["groups"],
                          "holdouts": "SEALED"}, sort_keys=True))
    else:
        rows = generate_batch(args.count, args.seed, args.random_fraction, registry=catalog)
        print(json.dumps({"state": "STRUCTURAL_CANDIDATES_ONLY_NOT_BACKTESTED",
                          "count": len(rows),
                          "seed": args.seed,
                          "genetic_fitness": "NOT_AVAILABLE_UNTIL_IST_ONLY_EVALUATOR",
                          "holdouts": "SEALED",
                          "strategies": rows}, sort_keys=True))

if __name__ == "__main__":
    main()
