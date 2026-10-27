#!/usr/bin/env python3
"""NQ M1 V2 limited executable OHLC prototype (S0 SYNTHETIC ONLY).

Supports a specifically listed indicator subset and MARKET entry with
FIXED_POINTS/ATR/STRUCTURE initial SL, NONE/R_MULTIPLE/FIXED_POINTS/ATR TP,
optional bar timeout. Anything else FAILS CLOSED (including trailing/BE,
LIMIT/STOP entries and the remaining registered indicators). No data loading,
no real fills, no G0-D2 pass and no risk of reading 2025/2026 here.
"""
from __future__ import annotations
import math
import numpy as np
from research.nq.nq_m1_v2_generator import fingerprint
from research.nq.nq_m1_v2_pipeline import REFERENCE_ACCOUNT, validate_candidate_envelope
from research.nq.nq_m1_v2_indicators_ext import EXTENDED, calc as extended_calc

SUPPORTED_INDICATORS = frozenset((
    "SMA", "EMA", "WMA", "RMA", "ROC", "Momentum",
    "ATR", "NATR", "True Range", "VWAP", "Relative Volume",
    "Z-Score", "Standard Deviation", "Variance",
    "Volume Z-Score", "Donchian", "OBV", "Bollinger Bandwidth"
)) | EXTENDED
SAMPLE_STATUS = "SYNTHETIC_ONLY_NO_REFERENCE_PARITY_OR_MARKET_BACKTEST"
TICK = .25
POINT_USD = 20.
LAST_BAR_INDEX = 118
COMMISSION_RT_USD = 4.68
SLIP_TICKS_SIDE = 2


class UnsupportedV2Feature(ValueError):
    pass


def _round_up_to_tick(points: float) -> float:
    if points <= 0 or not math.isfinite(points):
        raise ValueError("Invalid stop distance")
    return max(TICK, math.ceil(points / TICK - 1e-12) * TICK)


def _round_down_to_tick(points: float) -> float:
    if points <= 0 or not math.isfinite(points):
        raise ValueError("Invalid target distance")
    return max(TICK, math.floor(points / TICK + 1e-12) * TICK)


def _true_range(bars: np.ndarray) -> np.ndarray:
    h, l, c = bars[:, 1], bars[:, 2], bars[:, 3]
    close_prev = np.concatenate(([c[0]], c[:-1]))
    return np.maximum.reduce((h-l, abs(h-close_prev), abs(l-close_prev)))


def _wilder(values: np.ndarray, period: int):
    if len(values) < period:
        return None
    smoothed = float(np.mean(values[:period]))
    for x in values[period:]:
        smoothed += (float(x) - smoothed) / period
    return smoothed


def indicator_value(bars: np.ndarray, i: int, block: dict) -> float | None:
    """Scalar from bars <= i; returns None if warmup unavailable.
    Each formula is a documented initial convention, not certified parity.
    """
    if bars.ndim != 2 or bars.shape[1] != 5:
        raise ValueError("Expected M1 OHLCV array")
    if i < 0:
        return None
    if i >= len(bars):
        raise ValueError("Future bar not available")
    name, params = block["name"], block["parameters"]
    if name not in SUPPORTED_INDICATORS:
        raise UnsupportedV2Feature(f"Not implemented indicator: {name}")
    if name in EXTENDED:
        return extended_calc(bars, i, block)
    if not np.isfinite(bars[:i+1]).all():
        raise ValueError("Invalid OHLCV")
    g = bars[:i+1]
    c, h, l, v = (g[:, 3], g[:, 1], g[:, 2], g[:, 4])
    n = int(params.get("period", 0))
    if n < 0:
        raise ValueError("Invalid period")
    if name == "VWAP":
        if params.get("anchor") != "session":
            raise UnsupportedV2Feature("Only session-anchored VWAP supported")
        total_v = float(v.sum())
        return float(np.dot((h+l+c)/3., v)/total_v) if total_v > 0 else None
    if name == "True Range":
        return float(_true_range(g)[-1])
    if name == "OBV":
        # TA-Lib OBV is initialized at volume of first available bar.
        return float(v[0] + np.dot(np.sign(np.diff(c)), v[1:])) if len(c) > 1 else float(v[0])
    if n < 1:
        raise ValueError("Indicator period required")
    if name in {"Relative Volume", "Volume Z-Score"}:
        if len(g) <= n:
            return None
        prev = v[-n-1:-1]
        if name == "Relative Volume":
            denom = float(np.median(prev))
            return float(v[-1] / denom) if denom > 0 else None
        std = float(np.std(prev))
        return float((v[-1] - np.mean(prev)) / std) if std > 0 else 0.
    if name == "ROC" or name == "Momentum":
        if len(c) <= n:
            return None
        if name == "Momentum":
            return float(c[-1] - c[-n-1])
        return float(100 * (c[-1] / c[-n-1] - 1)) if c[-n-1] != 0 else None
    if len(c) < n:
        return None
    values = c[-n:]
    if name == "SMA":
        return float(np.mean(values))
    if name == "WMA":
        weights = np.arange(1, n+1, dtype=float)
        return float(np.dot(values, weights)/weights.sum())
    if name == "EMA":
        # Seed SMA of first n closes, then standard alpha 2/(n+1).
        smoothed = float(np.mean(c[:n]))
        for price in c[n:]:
            smoothed += 2./(n+1) * (float(price)-smoothed)
        return smoothed
    if name == "RMA":
        return _wilder(c, n)
    if name == "ATR":
        # TA-Lib/Wilder convention: first true range requires PREVIOUS close.
        # Exclude TR[0]; ATR(period=n) first exists at end-label index n.
        return _wilder(_true_range(g)[1:], n)
    if name == "NATR":
        a = _wilder(_true_range(g)[1:], n)
        return float(100 * a / c[-1]) if a is not None and c[-1] > 0 else None
    if name == "Z-Score":
        std = float(np.std(values))
        return float((c[-1] - np.mean(values))/std) if std > 0 else 0.
    if name == "Standard Deviation":
        return float(np.std(values))
    if name == "Variance":
        return float(np.var(values))
    if name == "Donchian":
        if len(c) <= n:
            return None
        return float(np.max(h[-n-1:-1]))  # upper channel excludes present bar
    if name == "Bollinger Bandwidth":
        multiple = float(params["std_multiplier"])
        mean = float(np.mean(values))
        return float(2*multiple*np.std(values)/abs(mean)) if mean != 0 else None
    raise UnsupportedV2Feature(f"Formula unavailable: {name}")


def _leaves(expr: dict):
    if expr["op"] in {"AND", "OR"}:
        yield from _leaves(expr["left"])
        yield from _leaves(expr["right"])
    else:
        yield expr


def check_supported(strategy: dict) -> None:
    """Fail before simulating a single fill; never silently ignore components."""
    validate_candidate_envelope(strategy)
    if strategy["entry_order"]["kind"] != "MARKET":
        raise UnsupportedV2Feature("LIMIT/STOP orders pending accurate fill engine")
    ext = strategy["exit"]
    if ext["trailing"] is not None or ext["break_even"] is not None:
        raise UnsupportedV2Feature("Trailing and break-even not implemented yet")
    if ext["stop_loss_required"]["kind"] not in {"FIXED_POINTS", "ATR", "STRUCTURE"}:
        raise UnsupportedV2Feature("SL model not implemented")
    if ext["profit_target"]["kind"] not in {"NONE", "R_MULTIPLE", "FIXED_POINTS", "ATR"}:
        raise UnsupportedV2Feature("TP model not implemented")
    for tree in (strategy["long"], strategy["short"]):
        for node in _leaves(tree):
            if node["indicator"]["name"] not in SUPPORTED_INDICATORS:
                raise UnsupportedV2Feature(f"Indicator {node['indicator']['name']} not implemented")
            if node["indicator"]["name"] == "VWAP" and node["indicator"]["parameters"].get("anchor") != "session":
                raise UnsupportedV2Feature("Prior-day VWAP not computable from one RTH day")
            if node["op"] not in {"RISING", "FALLING", "ABOVE_LAG", "BELOW_LAG", "CROSSES_OWN_LAG"}:
                raise UnsupportedV2Feature("Predicate unknown")
            if node["lag_completed_bars"] < 1:
                raise UnsupportedV2Feature("Lookahead lag")
    if ext["stop_loss_required"]["kind"] == "ATR" and not 2 <= ext["stop_loss_required"]["period"] <= 240:
        raise UnsupportedV2Feature("ATR period outside research range")


def eval_expr(bars: np.ndarray, i: int, expr: dict) -> bool:
    op = expr["op"]
    if op == "AND":
        return eval_expr(bars, i, expr["left"]) and eval_expr(bars, i, expr["right"])
    if op == "OR":
        return eval_expr(bars, i, expr["left"]) or eval_expr(bars, i, expr["right"])
    lag = expr["lag_completed_bars"]
    block = expr["indicator"]
    cur = indicator_value(bars, i, block)
    prior = indicator_value(bars, i-lag, block)  # honor the preregistered lag for EVERY predicate
    if cur is None or prior is None:
        return False
    if op in ("RISING", "ABOVE_LAG"):
        return cur > prior
    if op in ("FALLING", "BELOW_LAG"):
        return cur < prior
    if op == "CROSSES_OWN_LAG":
        one_back = indicator_value(bars, i-1, block)
        earlier = indicator_value(bars, i-lag-1, block)
        return one_back is not None and earlier is not None and cur > prior and one_back <= earlier
    raise ValueError(f"Unknown expression operator {op}")


def _risk_distance(bars: np.ndarray, i: int, side: int, entry: float, stop: dict):
    typ = stop["kind"]
    if typ == "FIXED_POINTS":
        return _round_up_to_tick(float(stop["points"]))
    if typ == "ATR":
        val = indicator_value(bars, i, {"name": "ATR", "parameters": {"period": int(stop["period"])}})
        return _round_up_to_tick(val * float(stop["multiple"])) if val is not None else None
    if typ == "STRUCTURE":
        lookback = int(stop["lookback"])
        if i+1 < lookback:
            return None
        seg = bars[i+1-lookback:i+1]
        level = float(np.min(seg[:, 2])) if side == 1 else float(np.max(seg[:, 1]))
        return _round_up_to_tick(max(TICK, side*(entry-level)+TICK*stop["buffer_ticks"]))
    raise UnsupportedV2Feature("Unknown stop model")


def _target_distance(bars: np.ndarray, i: int, risk: float, target: dict):
    typ = target["kind"]
    if typ == "NONE":
        return None
    if typ == "R_MULTIPLE":
        return _round_down_to_tick(risk*float(target["risk_multiple"]))
    if typ == "FIXED_POINTS":
        return _round_down_to_tick(float(target["points"]))
    if typ == "ATR":
        atr = indicator_value(bars, i, {"name": "ATR", "parameters": {"period": int(target["period"])}})
        return _round_down_to_tick(atr*float(target["multiple"])) if atr is not None else None
    raise UnsupportedV2Feature("Target type not supported")


def simulate_day(bars: np.ndarray, strategy: dict, day: str,
                 policy: dict | None = None) -> dict:
    """One strategy, one day, causal M1 OHLC proxy, no broker-fill guarantee."""
    check_supported(strategy)
    if (bars.shape != (390, 5) or not np.isfinite(bars).all() or
            (bars[:, 4] < 0).any() or (bars[:, 1] < bars[:, 2]).any()):
        raise ValueError("Invalid complete RTH OHLCV day")
    if not (len(day) == 10 and day[:4] in {"2020", "2021", "2022"}):
        raise PermissionError("Only IST complete days may be used for this prototype")
    p = dict(REFERENCE_ACCOUNT if policy is None else policy)
    slip = SLIP_TICKS_SIDE*TICK
    trades = []
    rejected = {"risk": 0, "indicator_warmup": 0, "ambiguous_side": 0}
    closed = 0.
    i = 20
    while i < LAST_BAR_INDEX and len(trades) < p["max_entries_per_day"]:
        if closed <= p["daily_closed_pnl_pause_usd"]:
            break
        long = eval_expr(bars, i, strategy["long"])
        short = eval_expr(bars, i, strategy["short"])
        if not long and not short:
            i += 1
            continue
        if long and short:
            rejected["ambiguous_side"] += 1
            i += 1
            continue
        side = 1 if long else -1
        entry_index = i+1
        entry = float(bars[entry_index, 0]) + side*slip
        risk = _risk_distance(bars, i, side, entry, strategy["exit"]["stop_loss_required"])
        if risk is None:
            rejected["indicator_warmup"] += 1
            i += 1
            continue
        adverse_initial_risk = risk*POINT_USD + 2*slip*POINT_USD + COMMISSION_RT_USD
        if adverse_initial_risk > p["max_initial_stop_risk_usd"]:
            rejected["risk"] += 1
            i += 1
            continue
        target = _target_distance(bars, i, risk, strategy["exit"]["profit_target"])
        if target is None and strategy["exit"]["profit_target"]["kind"] != "NONE":
            rejected["indicator_warmup"] += 1
            i += 1
            continue
        stop_price = entry-side*risk
        target_price = (entry+side*target) if target is not None else None
        duration = strategy["exit"]["exit_after_bars"]
        last_index = min(LAST_BAR_INDEX, entry_index + int(duration) - 1) if duration else LAST_BAR_INDEX
        for j in range(entry_index, last_index+1):
            opn, high, low, close = map(float, bars[j, :4])
            hit_sl = low <= stop_price if side == 1 else high >= stop_price
            hit_tp = (target_price is not None and
                      (high >= target_price if side == 1 else low <= target_price))
            if hit_sl:
                exit_raw = min(opn, stop_price) if side == 1 else max(opn, stop_price)
                reason = "SL_STOP_FIRST"
            elif hit_tp:
                exit_raw = target_price
                reason = "TP"
            elif j == last_index:
                exit_raw = close
                reason = "TIME"
            else:
                continue
            exit_price = exit_raw-side*slip
            net = round(side*(exit_price-entry)*POINT_USD-COMMISSION_RT_USD, 2)
            trades.append({"date": day, "strategy_id": strategy.get("id", fingerprint(strategy)[:12]),
                           "signal_idx": i, "entry_idx": entry_index, "exit_idx": j,
                           "initial_risk_usd": round(adverse_initial_risk, 2),
                           "net_usd": net, "side": side, "exit_reason": reason})
            closed += net
            i = j+1  # never overlap
            break
        else:
            raise AssertionError("Forced EOD timeout is mandatory")
    return {"status": SAMPLE_STATUS, "day": day, "trades": trades,
            "rejected": rejected, "session_close_idx": LAST_BAR_INDEX,
            "H2025_H2026": "SEALED"}
