#!/usr/bin/env python3
"""NQ M1 time-staged discovery. All H-2025/26 data are sealed.

S0 --mode catalog reads no prices. S1 --mode evaluate --stage IST opens only
the whitelisted private archive members from 2020-2022. ISV1/ISV2 need a
separately frozen IST-selection JSON; --mode evaluate never auto-advances.
Historical NQ M1 OHLC execution remains a proxy, NOT broker fills.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from research.nq.nq_h05_h07_level_volume_screen import roll_contract

CONFIG_PATH = Path(__file__).with_name("NQ_M1_CHRONO_DISCOVERY_CONFIG_2026_10_27.json")
STAGES = {"IST": (2020, 2021, 2022), "ISV1": (2023,), "ISV2": (2024,)}
NAME_RE = re.compile(r"^NQ_(03|06|09|12)-(20|21|22|23|24|25)_20(20|21|22|23|24)_Minute_Last\.txt$")
TICK = 0.25
EXIT_BAR_END_MIN = 11 * 60 + 29  # ET minute bar label, not opening timestamp
FIRST_BAR_END_MIN = 9 * 60 + 31
LAST_BAR_INDEX = EXIT_BAR_END_MIN - FIRST_BAR_END_MIN  # 118; 11:29 close
RTH_END_MIN = 16 * 60
FAMILIES = ("BREAKOUT", "REVERSAL", "CONTINUATION", "VWAP_PULLBACK", "VOL_EXPANSION")


def read_config(path: Path = CONFIG_PATH) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("holdout_years_blocked") != [2025, 2026]:
        raise RuntimeError("Sealed H holdout policy changed")
    if cfg.get("stages") != {k: list(v) for k, v in STAGES.items()}:
        raise RuntimeError("Unexpected year stage definition")
    if cfg.get("signal_entry_window_et") != ["09:30", "11:29"] or cfg.get("all_positions_flat_et") != "11:29":
        raise RuntimeError("Trading window changed")
    p = cfg["search"]
    if (tuple(p["families"]) != FAMILIES or p["expected_candidates"] != 120
            or p["variants"] != [0, 1, 2] or p["lookbacks"] != [10, 20]
            or p["stop_models"] != ["ATR", "STRUCTURE"] or p["target_r"] != [None, 2.0]):
        raise RuntimeError("Search family was modified after preregistration")
    e = cfg["execution"]
    if (e["contract"] != "NQ" or e["contract_count"] != 1
            or e["point_value_usd"] != 20 or e["tick_size"] != TICK
            or e["max_open_positions"] != 1 or e["max_filled_entries_per_day"] != 2):
        raise RuntimeError("Execution policy modified")
    return cfg


def catalog(cfg: dict) -> list[dict]:
    s = cfg["search"]
    records = []
    for family, variant, lookback, stop, target in itertools.product(
        s["families"], s["variants"], s["lookbacks"], s["stop_models"], s["target_r"]
    ):
        records.append({
            "id": f"NQ-M1-C{len(records) + 1:04d}",
            "family": family,
            "variant": variant,
            "lookback": lookback,
            "stop_model": stop,
            "target_r": target,
        })
    if len(records) != 120 or len({r["id"] for r in records}) != 120:
        raise RuntimeError("Catalog count/ID integrity failed")
    counts = {name: sum(row["family"] == name for row in records) for name in FAMILIES}
    if set(counts.values()) != {24}:
        raise RuntimeError("Unbalanced research budget")
    return records


def manifest_sha(rows: list[dict]) -> str:
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def stage_years(stage: str) -> tuple[int, ...]:
    if stage not in STAGES:
        raise ValueError(f"Stage {stage!r} is not allowed; 2025/2026 stay sealed")
    return STAGES[stage]


def permitted_market_member(name: str, years: tuple[int, ...]) -> bool:
    """Whitelist full archived path + filename BEFORE any z.open is allowed."""
    if any(y not in {2020, 2021, 2022, 2023, 2024} for y in years):
        raise ValueError("Prohibited years")
    if "/development_2020_2024/" not in name or ".." in Path(name).parts:
        return False
    match = NAME_RE.fullmatch(name.rsplit("/", 1)[-1])
    return bool(match and int(match.group(3)) + 2000 in years)


def load_years(zip_path: Path, years: tuple[int, ...]) -> tuple[list[str], np.ndarray, dict]:
    """Load ONLY allowed NQ minute archive members; never read sealed H 2025/2026."""
    if not years or any(y not in {2020, 2021, 2022, 2023, 2024} for y in years):
        raise ValueError("Stage years not allowed")
    parts = []
    with zipfile.ZipFile(zip_path) as archive:
        members = sorted(x for x in archive.namelist() if permitted_market_member(x, years))
        if len(members) != 5 * len(years):
            raise ValueError(f"Expected {5 * len(years)} named NQ DEV member files, found {len(members)}")
        for name in members:
            m = NAME_RE.fullmatch(name.rsplit("/", 1)[-1])
            assert m is not None
            contract = f"NQ_{m.group(1)}-{m.group(2)}"
            year = 2000 + int(m.group(3))
            with archive.open(name) as stream:
                frame = pd.read_csv(
                    stream, sep=";", header=None,
                    names=["utc", "open", "high", "low", "close", "volume"],
                    dtype={"utc": "string"},
                )
            times = pd.to_datetime(frame["utc"], format="%Y%m%d %H%M%S", utc=True)
            if not bool((times.dt.year == year).all()):
                raise ValueError("Archive calendar year mismatch")
            et = times.dt.tz_convert("America/New_York")
            minute = et.dt.hour * 60 + et.dt.minute
            is_rth = minute.between(FIRST_BAR_END_MIN, RTH_END_MIN)
            if not bool(is_rth.any()):
                continue
            sub = frame.loc[is_rth, ["open", "high", "low", "close", "volume"]].copy()
            sub["session"] = et.loc[is_rth].dt.strftime("%Y-%m-%d").values
            sub["minute"] = minute.loc[is_rth].to_numpy()
            sub = sub[sub.session.str.slice(0, 4).astype(int).isin(years)]
            eligible = {d for d in sub["session"].unique() if roll_contract(date.fromisoformat(d)) == contract}
            sub = sub[sub.session.isin(eligible)]
            if not sub.empty:
                parts.append(sub)
    if not parts:
        raise ValueError("No RTH NQ minute data in explicitly permitted years")
    all_rows = pd.concat(parts, ignore_index=True)
    dates = []
    arrays = []
    excluded = 0
    for day, g in all_rows.groupby("session", sort=True):
        g = g.sort_values("minute")
        valid = (len(g) == 390 and np.array_equal(g.minute.to_numpy(), np.arange(571, 961)))
        if not valid:
            excluded += 1
            continue
        bars = g[["open", "high", "low", "close", "volume"]].to_numpy(float)
        if not np.isfinite(bars).all() or (bars[:, 4] < 0).any():
            raise ValueError("Invalid OHLCV content")
        if int(day[:4]) not in years:
            raise ValueError("Out-of-range day")
        dates.append(day)
        arrays.append(bars)
    if not arrays:
        raise ValueError("No complete RTH days in allowed stage")
    return dates, np.stack(arrays), {
        "years_opened": list(years),
        "members_opened": len(members),
        "complete_rth_sessions": len(dates),
        "partial_sessions_excluded": excluded,
        "holdout_2025_opened": False,
        "holdout_2026_opened": False,
    }


def signal(g: np.ndarray, i: int, rule: dict) -> int:
    """Long +1 / short -1 / no signal 0; uses bars through i inclusive only."""
    lb = rule["lookback"]
    if i < lb or i < 2:
        return 0
    prev = g[i-lb:i]
    o, high, low, close, vol = g[i]
    pclose = g[i-1, 3]
    vmed = max(1., float(np.median(prev[:, 4])))
    variant = rule["variant"]
    family = rule["family"]
    if family == "BREAKOUT":
        factor = [1., 1.2, 1.5][variant]
        if vol < factor * vmed:
            return 0
        if close > prev[:, 1].max() + TICK:
            return 1
        if close < prev[:, 2].min() - TICK:
            return -1
    elif family == "REVERSAL":
        factor = [1., 1.15, 1.3][variant]
        if vol < factor * vmed:
            return 0
        if high >= prev[:, 1].max() + TICK and close < prev[:, 1].max():
            return -1
        if low <= prev[:, 2].min() - TICK and close > prev[:, 2].min():
            return 1
    elif family == "CONTINUATION":
        # Current move and longer horizon must agree, beyond an ex-ante threshold.
        change = close - g[i-lb, 3]
        recent = close - pclose
        threshold = [0., .25, .5][variant] * max(TICK, float(np.median(prev[:, 1]-prev[:, 2])))
        if change > threshold and recent > TICK and vol >= vmed:
            return 1
        if change < -threshold and recent < -TICK and vol >= vmed:
            return -1
    elif family == "VWAP_PULLBACK":
        # VWAP is cumulative from RTH open through the fully completed current minute.
        v = g[:i+1, 4]
        if v.sum() <= 0:
            return 0
        mid = (g[:i+1, 1] + g[:i+1, 2] + g[:i+1, 3]) / 3
        vw = float(np.dot(mid, v) / v.sum())
        gap = [0., 1., 2.][variant] * TICK
        trend = close - g[i-lb, 3]
        if trend > 0 and pclose <= vw and close >= vw + gap:
            return 1
        if trend < 0 and pclose >= vw and close <= vw - gap:
            return -1
    elif family == "VOL_EXPANSION":
        factor = [1.25, 1.5, 1.75][variant]
        width = high - low
        if width < factor * max(TICK, float(np.median(prev[:, 1]-prev[:, 2]))):
            return 0
        if width < TICK:
            return 0
        if (close - low) / width >= .75:
            return 1
        if (high - close) / width >= .75:
            return -1
    else:
        raise ValueError("Unknown signal family")
    return 0


def ceil_tick(points: float) -> float:
    if not math.isfinite(points) or points < 0:
        raise ValueError("Invalid risk distance")
    return max(TICK, math.ceil(points / TICK - 1e-9) * TICK)


def stop_distance(g: np.ndarray, i: int, side: int, entry: float, rule: dict) -> float:
    lb = rule["lookback"]
    seg = g[i-lb+1:i+1]
    if rule["stop_model"] == "ATR":
        # Historical true range based only on completed bars through i.
        prevclose = g[i-lb:i, 3]
        tr = np.maximum.reduce([
            seg[:, 1] - seg[:, 2],
            np.abs(seg[:, 1] - prevclose),
            np.abs(seg[:, 2] - prevclose),
        ])
        return ceil_tick(1.25 * float(np.mean(tr)))
    if rule["stop_model"] == "STRUCTURE":
        pivot = float(seg[:, 2].min()) if side == 1 else float(seg[:, 1].max())
        return ceil_tick(max(TICK, side * (entry-pivot) + TICK))
    raise ValueError("Unknown stop calculation")


def one_trade(g: np.ndarray, i: int, side: int, rule: dict, cfg: dict):
    """M1 OHLC proxy: entry at next bar open, stop-first when target and SL overlap."""
    ex = cfg["execution"]
    slip = TICK * ex["slippage_ticks_each_side"]
    raw_entry = float(g[i+1, 0])
    entry = raw_entry + side * slip
    risk = stop_distance(g, i, side, entry, rule)
    if risk * ex["point_value_usd"] > ex["max_initial_stop_risk_usd"]:
        return None, "RISK_INELIGIBLE_NQ"
    sl = entry - side * risk
    tp = entry + side * risk * rule["target_r"] if rule["target_r"] is not None else None
    for j in range(i+1, LAST_BAR_INDEX+1):
        opening, hi, lo, cl = map(float, g[j, :4])
        hit_sl = (lo <= sl) if side == 1 else (hi >= sl)
        hit_tp = tp is not None and ((hi >= tp) if side == 1 else (lo <= tp))
        if hit_sl:
            exit_raw = min(opening, sl) if side == 1 else max(opening, sl)
            reason = "SL"  # conservative first-hit precedence
        elif hit_tp:
            exit_raw = tp
            reason = "TP"
        elif j == LAST_BAR_INDEX:
            exit_raw = cl
            reason = "TIME_1129"
        else:
            continue
        exit_filled = exit_raw - side * slip
        pnl = side * (exit_filled - entry) * ex["point_value_usd"] - ex["round_trip_commission_usd"]
        return {
            "net": round(float(pnl), 2),
            "side": side,
            "decision_idx": i,
            "exit_idx": j,
            "exit_reason": reason,
            "risk_usd": round(risk * ex["point_value_usd"], 2),
        }, None
    raise RuntimeError("11:29 exit not reached")


def run_day(g: np.ndarray, rule: dict, cfg: dict) -> tuple[list[dict], dict]:
    if g.shape != (390, 5):
        raise ValueError("A complete RTH NQ day must have exactly 390 1m bars")
    ex = cfg["execution"]
    results = []
    counts = {"signals": 0, "rejected_risk": 0}
    day_closed_pnl = 0.
    i = max(20, rule["lookback"])
    while i < LAST_BAR_INDEX and len(results) < ex["max_filled_entries_per_day"]:
        if day_closed_pnl <= ex["closed_pnl_daily_pause_usd"]:
            break
        side = signal(g, i, rule)
        if not side:
            i += 1
            continue
        counts["signals"] += 1
        trade, error = one_trade(g, i, side, rule, cfg)
        if error:
            counts["rejected_risk"] += 1
            i += 1
            continue
        results.append(trade)
        day_closed_pnl += trade["net"]
        i = trade["exit_idx"] + 1  # never overlap active positions
    return results, counts


def summarize(rows: list[dict], all_days: list[str]) -> dict:
    net = [x["net"] for x in rows]
    positives = sum(z for z in net if z > 0)
    losses = -sum(z for z in net if z < 0)
    curve = [0.]
    for z in net:
        curve.append(curve[-1] + z)
    peak = 0.
    dd = 0.
    for z in curve:
        peak = max(peak, z)
        dd = max(dd, peak-z)
    years = sorted({d[:4] for d in all_days})
    byyear = {year: round(sum(x["net"] for x in rows if x["session"][:4] == year), 2) for year in years}
    pf = round(positives / losses, 4) if losses > 0 else None
    return {
        "trades": len(rows),
        "net_usd": round(sum(net), 2),
        "pf": pf,
        "closed_trade_dd_usd": round(dd, 2),
        "net_per_trade": round(sum(net) / len(rows), 2) if rows else None,
        "positive_years": sum(z > 0 for z in byyear.values()),
        "by_year": byyear,
        "notes": "M1 OHLC stop-first proxy; not intrabar tick reconstruction or brokerage fills",
    }


def freeze_selection(path: Path, rows: list[dict]) -> list[dict]:
    """Explicit frozen IST selection required for all later stages."""
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = [z["id"] for z in rows]
    selected = data.get("selected_ids")
    if (data.get("stage") != "IST_FROZEN" or data.get("catalog_sha256") != manifest_sha(rows)
            or not isinstance(selected, list) or not selected or len(set(selected)) != len(selected)
            or any(cid not in ids for cid in selected)):
        raise RuntimeError("Invalid frozen IST selection, later periods cannot be opened")
    selected_set = set(selected)
    return [r for r in rows if r["id"] in selected_set]


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--mode", required=True, choices=["catalog", "evaluate"])
    cli.add_argument("--stage", choices=list(STAGES))
    cli.add_argument("--zip", type=Path)
    cli.add_argument("--freeze", type=Path)
    cli.add_argument("--ack-isv2", action="store_true")
    cli.add_argument("--config", type=Path, default=CONFIG_PATH)
    cli.add_argument("--out", type=Path)
    args = cli.parse_args()
    cfg = read_config(args.config)
    rules = catalog(cfg)
    hashval = manifest_sha(rules)
    if args.mode == "catalog":
        print(json.dumps({
            "stage": "S0_NO_MARKET_DATA", "count": len(rules), "catalog_sha256": hashval,
            "by_family": {f: 24 for f in FAMILIES},
            "candidate_grid": rules, "H2025_H2026": "SEALED",
        }, indent=2))
        return
    if args.stage is None or args.zip is None or args.out is None:
        cli.error("--mode evaluate needs --stage, --zip and --out")
    years = stage_years(args.stage)
    if args.stage != "IST":
        if args.freeze is None:
            cli.error("ISV requires a separate frozen IST selection file")
        rules = freeze_selection(args.freeze, rules)
        if args.stage == "ISV2" and not args.ack_isv2:
            cli.error("Explicit --ack-isv2 required for 2024 stage")
    # All stage-year and strategy rules verified BEFORE any archive member is read.
    dates, bars, source = load_years(args.zip, years)
    reports = []
    for rule in rules:
        completed = []
        counts = {"signals": 0, "rejected_risk": 0}
        for day, g in zip(dates, bars):
            trades, stats = run_day(g, rule, cfg)
            for trade in trades:
                completed.append({"session": day, **trade})
            for key in counts:
                counts[key] += stats[key]
        report = summarize(completed, dates)
        reports.append({**rule, **counts, **report})
    reports.sort(key=lambda z: z["id"])
    envelope = {
        "study": cfg["id"], "stage": args.stage, "source": source,
        "catalog_sha256": hashval, "strategies_evaluated": len(rules),
        "H2025_H2026": "SEALED",
        "evaluation_status": "REUSED_H_DEVELOPMENT_EXPLORATORY_ONLY",
        "results": reports,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(envelope, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "stage": args.stage, "days": len(dates), "evaluated": len(rules),
        "total_fills_across_alternative_models": sum(x["trades"] for x in reports),
        "positive_net": sum(x["net_usd"] > 0 for x in reports),
        "all_years": list(years), "report_path": str(args.out),
        "H2025_H2026": "SEALED",
    }, indent=2))


if __name__ == "__main__":
    main()
