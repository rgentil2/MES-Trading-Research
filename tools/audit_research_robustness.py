#!/usr/bin/env python3
"""Retrospective 2020-2024 diagnostics; never promotes or retunes a candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
START, END = date(2020, 1, 1), date(2025, 1, 1)
CALENDAR_DAYS = (END - START).days
YEARS = list(range(2020, 2025))
SEED, DRAWS, BLOCK_DAYS = 20261002, 10_000, 20


def day_offset(day):
    d = date.fromisoformat(day)
    if not START <= d < END:
        raise ValueError("diagnostic accepts 2020-2024 only")
    return (d - START).days


def fit_components(rows):
    rows = sorted(rows, key=lambda r: r["date"])
    dates = [r["date"] for r in rows]
    for ds in dates:
        day_offset(ds)
    if len(set(dates)) != len(dates):
        raise ValueError("regression rows must contain one observation per day")
    if len(rows) < 3:
        return None
    x = np.asarray([r["x"] for r in rows], float)
    y = np.asarray([r["y"] for r in rows], float)
    X = np.column_stack([np.ones(len(x)), x])
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("nonfinite regression input")
    if np.linalg.matrix_rank(X) < 2:
        return None
    bread = np.linalg.inv(X.T @ X)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ beta
    return rows, X, y, bread, beta, resid


def regression_inference(beta, cov, n):
    se2 = float(cov[1, 1])
    if not math.isfinite(se2) or se2 <= 0:
        return {"slope": float(beta[1]), "standard_error": None,
                "ci95": None, "p_two_sided": None, "estimable": False}
    se = math.sqrt(se2)
    critical = float(stats.t.ppf(0.975, n - 2))
    return {"slope": float(beta[1]), "standard_error": se,
            "ci95": [float(beta[1] - critical * se), float(beta[1] + critical * se)],
            "p_two_sided": float(2 * stats.t.sf(abs(beta[1] / se), n - 2)),
            "estimable": True}


def regression_audit(rows, lag_days=20):
    c = fit_components(rows)
    if c is None:
        return {"n_days": len(rows), "estimable": False, "methods": {}}
    rows, X, y, bread, beta, resid = c
    n = len(rows)
    ols_cov = float(resid @ resid) / (n - 2) * bread
    leverage = np.sum((X @ bread) * X, axis=1)
    methods = {"OLS": regression_inference(beta, ols_cov, n)}
    if np.any(1 - leverage <= 1e-12):
        methods["HC3"] = {"estimable": False, "reason": "unit leverage"}
    else:
        scores = X * (resid / (1 - leverage))[:, None]
        methods["HC3"] = regression_inference(beta, bread @ (scores.T @ scores) @ bread, n)

    # Calendar distances matter: two trades months apart are not one-day neighbors.
    grid = np.zeros((CALENDAR_DAYS, 2))
    offsets = [day_offset(r["date"]) for r in rows]
    grid[offsets] = X * resid[:, None]
    meat = grid.T @ grid
    for lag in range(1, lag_days + 1):
        cross = grid[lag:].T @ grid[:-lag]
        meat += (1 - lag / (lag_days + 1)) * (cross + cross.T)
    hac_cov = n / (n - 2) * bread @ meat @ bread
    methods["CALENDAR_HAC20"] = regression_inference(beta, hac_cov, n)
    return {"n_days": n, "estimable": True, "intercept": float(beta[0]),
            "slope": float(beta[1]), "methods": methods,
            "max_leverage": float(np.max(leverage)), "lag_calendar_days": lag_days}



def validated_events(events, instrument):
    if instrument not in {"MES", "ES"}:
        raise ValueError("explicit MES/ES execution instrument required")
    for e in events:
        day_offset(e["date"])
        if e.get("instrument") != instrument or not str(e.get("contract", "")).startswith(instrument + " "):
            raise ValueError("execution instrument/contract mismatch")
        for k in ("gross_pnl_usd", "cost_round_trip_usd"):
            if isinstance(e.get(k), bool) or not isinstance(e.get(k), (float, int)) or not math.isfinite(e[k]):
                raise ValueError("explicit finite gross P&L and instrument-specific costs required")
        if e["cost_round_trip_usd"] < 0:
            raise ValueError("negative cost")
    return np.asarray([e["gross_pnl_usd"] - e["cost_round_trip_usd"] for e in events], float)


def summary(events, instrument, cost_multiplier=1.0):
    net = validated_events(events, instrument)
    costs = np.asarray([e["cost_round_trip_usd"] for e in events], float)
    net -= (cost_multiplier - 1) * costs
    gains, losses = net[net > 0].sum(), -net[net < 0].sum()
    return {"trades": len(events), "active_days": len({e["date"] for e in events}),
            "net_expectancy_usd": float(net.mean()) if len(net) else None,
            "net_pnl_usd": float(net.sum()), "profit_factor": float(gains / losses) if losses > 0 else None,
            "no_losing_trades": bool(len(net) and losses == 0),
            "positive_trade_fraction": float((net > 0).mean()) if len(net) else None}


def ci_from_se(mean, se, degrees):
    if degrees < 1 or not math.isfinite(se) or se <= 0:
        return {"estimable": False, "mean": mean, "se": None, "ci95": None, "p_two_sided": None}
    critical = float(stats.t.ppf(.975, degrees))
    return {"estimable": True, "mean": mean, "se": se, "degrees_of_freedom": degrees,
            "ci95": [mean - critical * se, mean + critical * se],
            "p_two_sided": float(2 * stats.t.sf(abs(mean / se), degrees))}


def mean_inference(events, instrument, lag_days=20):
    net = validated_events(events, instrument)
    n, days = len(net), len({e["date"] for e in events})
    if n < 3 or days < 3:
        return {"estimable": False, "reason": "fewer than 3 trades/session clusters"}
    mean = float(net.mean())
    residuals = net - mean
    grid = np.zeros(CALENDAR_DAYS)
    for e, residual in zip(events, residuals):
        grid[day_offset(e["date"])] += residual
    # Intercept-only cluster sandwich with cluster finite-sample correction.
    cluster_var = days / (days - 1) * float(grid @ grid) / n**2
    hc3_var = float(np.sum((residuals / (1 - 1 / n))**2)) / n**2
    meat = float(grid @ grid)
    for lag in range(1, lag_days + 1):
        meat += 2 * (1 - lag / (lag_days + 1)) * float(grid[lag:] @ grid[:-lag])
    hac_var = n / (n - 1) * meat / n**2
    return {"estimable": True, "SESSION_CLUSTER_T": ci_from_se(mean, math.sqrt(max(cluster_var, 0)), days - 1),
            "HC3_EVENT_DIAGNOSTIC": ci_from_se(mean, math.sqrt(max(hc3_var, 0)), n - 1),
            "CALENDAR_HAC20_T_APPROX": ci_from_se(mean, math.sqrt(max(hac_var, 0)), days - 1),
            "note": "HC3 alone does not address within-session dependence. Calendar-HAC t inference is approximate; bootstrap is also reported.",
            "lag_calendar_days": lag_days}


def calendar_bootstrap(events, instrument, draws=DRAWS, block_days=BLOCK_DAYS, seed=SEED):
    net = validated_events(events, instrument)
    if draws < 1 or not 1 <= block_days <= CALENDAR_DAYS:
        raise ValueError("invalid bootstrap settings")
    sums, counts = np.zeros(CALENDAR_DAYS), np.zeros(CALENDAR_DAYS)
    for e, value in zip(events, net):
        index = day_offset(e["date"])
        sums[index] += value
        counts[index] += 1
    # Sufficient statistics preserve event weighting and all inactive calendar days.
    sums = np.r_[0.0, np.cumsum(sums)]
    counts = np.r_[0.0, np.cumsum(counts)]
    rng = np.random.default_rng(seed)
    blocks = math.ceil(CALENDAR_DAYS / block_days)
    means = []
    for _ in range(draws):
        starts = rng.integers(0, CALENDAR_DAYS - block_days + 1, size=blocks)
        lengths = np.full(blocks, block_days)
        lengths[-1] = CALENDAR_DAYS - (blocks - 1) * block_days
        ends = starts + lengths
        n = float((counts[ends] - counts[starts]).sum())
        if n:
            means.append(float((sums[ends] - sums[starts]).sum() / n))
    return {"resamples": draws, "valid_resamples": len(means), "seed": seed,
            "block_calendar_days": block_days,
            "ci95_net_expectancy_usd": np.quantile(means, [.025, .975]).tolist()
            if len(means) >= .95 * draws else None,
            "sampling": "moving calendar blocks; all trades of a selected day retained; event-weighted mean"}


def audit_events(events, instrument, draws=DRAWS):
    net = validated_events(events, instrument)
    day_totals = {}
    for e, value in zip(events, net):
        day_totals[e["date"]] = day_totals.get(e["date"], 0) + float(value)
    best = sorted(day_totals, key=lambda day: (-day_totals[day], day))
    removals = {}
    for number in (1, 2):
        omitted = best[:number]
        kept = [e for e in events if e["date"] not in omitted]
        removals[f"remove_best_{number}_days"] = {"omitted_days": omitted, "remaining": summary(kept, instrument)}
    positive = sum(max(v, 0) for v in day_totals.values())
    return {"authority": "DIAGNOSTIC_ONLY_NO_PROMOTION", "instrument": instrument,
            "strategy_authorized": False, "baseline": summary(events, instrument),
            "stress_1_5x_costs": summary(events, instrument, 1.5),
            "inference": mean_inference(events, instrument),
            "calendar_bootstrap": calendar_bootstrap(events, instrument, draws=draws),
            "best_two_share_of_positive_day_gains": sum(max(day_totals[d], 0) for d in best[:2]) / positive if positive else None,
            **removals,
            "leave_one_day_out": {d: summary([e for e in events if e["date"] != d], instrument) for d in sorted(day_totals)},
            "annual": {str(y): summary([e for e in events if int(e["date"][:4]) == y], instrument) for y in YEARS},
            "leave_one_year_out": {str(y): summary([e for e in events if int(e["date"][:4]) != y], instrument) for y in YEARS}}


def development_mes_files(raw_dir):
    from src.data_pipeline import contract_info
    files = sorted(raw_dir.glob('MES ??-??.Last.txt'), key=lambda p: contract_info(p)[:2])
    files = [p for p in files if contract_info(p)[0] in YEARS]
    if len(files) != 20:
        raise ValueError("require all 20 MES quarterly development files; never substitute holdout contracts")
    return files


def mes_b14_diagnostic(raw_dir):
    from src.data_pipeline import build_continuous
    from research.archive.B12.b12_strategy_architecture import COST_RT, parse_raw, prepare_rth
    from research.archive.B13.b13_high_directional_triggers import block_features
    from research.archive.B14.b14_opposite_sign_candidates import build_exact_inverse_trades
    if not math.isclose(COST_RT, 4.38):
        raise ValueError("frozen MES cost changed")
    files = development_mes_files(raw_dir)
    raw, manifest, _ = build_continuous(files, 'UTC', .25)
    raw = parse_raw(raw)
    # DEC24 may contain later timestamps; exclude before any feature/outcome construction.
    raw = raw[raw['timestamp_et'].dt.year.isin(YEARS)].copy()
    if not len(raw) or not set(raw['timestamp_et'].dt.year).issubset(YEARS):
        raise ValueError("diagnostic calendar isolation failed")
    _, groups = prepare_rth(raw)
    feats = block_features(raw, groups)
    candidates = {}
    for hypothesis in ('H080', 'H081'):
        trades = build_exact_inverse_trades(feats, groups, hypothesis)
        events = [{'date':str(r.session_date), 'instrument':'MES', 'contract':str(r.contract),
                   'gross_pnl_usd':float(r.gross_pnl_30), 'cost_round_trip_usd':4.38}
                  for r in trades.itertuples(index=False)]
        candidates[hypothesis] = audit_events(events, 'MES')
    return {"stage":"DEVELOPMENT_RETROSPECTIVE_DIAGNOSTIC", "loaded_years":YEARS,
            "loaded_contract_files":[p.name for p in files],
            "source_file_sha256":{r.file:r.sha256 for r in manifest.itertuples(index=False)},
            "holdout_2025_loaded":False, "holdout_2026_loaded":False,
            "source_scope":"Subset 2020-2024 of archived B14; not a reproduction of its 2020-2025 primary gate.",
            "cost_round_trip_usd":4.38, "original_statuses_changed":False, "strategy_authorized":False,
            "MES":candidates,
            "ES":{"status":"NOT_RUN_NO_DIRECTIONAL_OUTCOMES_AVAILABLE",
                  "reason":"ES-B01 remains planned; same diagnostics are available once ES data and operational definitions pass their gates. No Last-only delta or MES-to-ES transfer is assumed."}}


def render_md(report):
    lines = ['# MES / ES Robustness Audit', '', report['source_scope'], '',
             'Diagnostic only. Original B14 statuses and frozen R063 are preserved. No promotion or retuning.',
             'MES cost: $4.38 RT. Outcome years: 2020-2024 only. No 2025/2026 outcome construction.', '',
             '| MES candidate | Trades | Net USD/trade | Without best day | Without best two days | 1.5x costs |',
             '|---|---:|---:|---:|---:|---:|']
    def fmt(value):
        return f'{value:.2f}' if value is not None else 'N/A'
    for name, audit in report['MES'].items():
        lines.append(f"| {name} | {audit['baseline']['trades']} | {fmt(audit['baseline']['net_expectancy_usd'])} | {fmt(audit['remove_best_1_days']['remaining']['net_expectancy_usd'])} | {fmt(audit['remove_best_2_days']['remaining']['net_expectancy_usd'])} | {fmt(audit['stress_1_5x_costs']['net_expectancy_usd'])} |")
    lines += ['', 'JSON includes session-cluster t inference, HC3 diagnostic, calendar-HAC20, 10,000 calendar-block bootstrap samples, leave-one-day/year-out and yearly results.',
              '', 'ES: NOT RUN. ES-B01 has no executed directional outcome table; no ES robustness claim is made.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-dir', type=Path, default=Path('data/raw'))
    args = parser.parse_args()
    report = mes_b14_diagnostic(args.raw_dir)
    out = Path('results/research_controls')
    out.mkdir(parents=True, exist_ok=True)
    (out/'ROBUSTNESS_AUDIT.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    (out/'ROBUSTNESS_AUDIT.md').write_text(render_md(report))
    print(render_md(report))


if __name__ == '__main__':
    main()
