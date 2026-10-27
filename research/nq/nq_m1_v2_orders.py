#!/usr/bin/env python3
"""V2 S0.2: synthetic-tested intraday M1 order/exit model; NEVER broker fills.

Unlike V2 S0.1, supports MARKET/LIMIT/STOP, pending expiry, Chandelier
initial SL, a narrow causal-level target, break-even and ATR trailing. Trade
touches in OHLC M1 cannot resolve intraminute path or limit-order queue; all
such results are a conservative research PROXY, not approved execution.
Only IST 2020-22 date labels; reads NO ZIP/files/market data itself.
"""
from __future__ import annotations
import math
from datetime import date
import numpy as np

from research.nq import nq_m1_v2_m1_engine as base
from research.nq.nq_m1_v2_generator import fingerprint
from research.nq.nq_m1_v2_pipeline import REFERENCE_ACCOUNT, validate_candidate_envelope

TICK = base.TICK
POINT_USD = base.POINT_USD
LAST_IDX = base.LAST_BAR_INDEX
SLIP = base.SLIP_TICKS_SIDE * TICK
FEE = base.COMMISSION_RT_USD
STATUS = "SYNTHETIC_ORDER_MODEL_ONLY_OHLC_PROXY_NOT_BROKER_FILLS"


def _tick(price: float, direction: str) -> float:
    if not math.isfinite(price) or price <= 0:
        raise ValueError("Invalid order price")
    q = price / TICK
    return (math.floor(q+1e-10) if direction == "DOWN" else math.ceil(q-1e-10))*TICK


def validate_supported(s: dict) -> None:
    validate_candidate_envelope(s)
    e = s["entry_order"]
    if e["kind"] not in {"MARKET", "LIMIT", "STOP"}:
        raise base.UnsupportedV2Feature("Unsupported entry order")
    if type(e["expiry_bars"]) is not int or not (1 <= e["expiry_bars"] <= 30):
        raise base.UnsupportedV2Feature("Pending expiry must be 1..30 bars")
    if type(e["offset_ticks"]) is not int or not (0 <= e["offset_ticks"] <= 32):
        raise base.UnsupportedV2Feature("Offset ticks 0..32 only")
    if e["kind"] == "MARKET" and e["offset_ticks"] != 0:
        raise base.UnsupportedV2Feature("Market orders cannot have offset")
    x = s["exit"]
    if x["stop_loss_required"]["kind"] not in {"FIXED_POINTS", "ATR", "STRUCTURE", "CHANDELIER"}:
        raise base.UnsupportedV2Feature("Unsupported initial stop")
    if x["profit_target"]["kind"] not in {"NONE", "R_MULTIPLE", "FIXED_POINTS", "ATR", "CAUSAL_LEVEL"}:
        raise base.UnsupportedV2Feature("Unsupported profit target")
    if x["profit_target"]["kind"] == "CAUSAL_LEVEL" and x["profit_target"]["reference"] != "VWAP":
        raise base.UnsupportedV2Feature("Previous-session/pivot level needs separate causal history")
    if x["trailing"] is not None:
        t = x["trailing"]
        if not (0.25 <= t["start_r"] <= 4 and 0.25 <= t["distance_atr"] <= 5
                and 2 <= t["atr_period"] <= 120):
            raise base.UnsupportedV2Feature("Unsupported trailing parameters")
    if x["break_even"] is not None:
        b = x["break_even"]
        if not (0.5 <= b["start_r"] <= 3 and 0 <= b["plus_ticks"] <= 4):
            raise base.UnsupportedV2Feature("Unsupported break-even parameters")
    d = x["exit_after_bars"]
    if d is not None and (type(d) is not int or not (1 <= d <= 119)):
        raise base.UnsupportedV2Feature("Invalid duration")
    for tree in (s["long"], s["short"]):
        for node in base._leaves(tree):
            b = node["indicator"]
            if b["name"] not in base.SUPPORTED_INDICATORS:
                raise base.UnsupportedV2Feature("Indicator not yet implemented: " + b["name"])
            if b["name"] == "VWAP" and b["parameters"].get("anchor") != "session":
                raise base.UnsupportedV2Feature("Unsupported VWAP anchor")
            if node["op"] not in {"RISING", "FALLING", "ABOVE_LAG", "BELOW_LAG", "CROSSES_OWN_LAG"}:
                raise base.UnsupportedV2Feature("Unsupported predicate")
            if type(node["lag_completed_bars"]) is not int or not 1 <= node["lag_completed_bars"] <= 20:
                raise base.UnsupportedV2Feature("Invalid causal lag")


def _entry_limit_or_trigger(close: float, side: int, kind: str, offset_ticks: int) -> float | None:
    if kind == "MARKET":
        return None
    if kind == "STOP":
        raw = close + side * TICK * offset_ticks
        return _tick(raw, "UP" if side == 1 else "DOWN")
    raw = close - side * TICK * offset_ticks
    return _tick(raw, "DOWN" if side == 1 else "UP")


def _pending_fill(bars: np.ndarray, idx: int, side: int, kind: str,
                  requested: float | None) -> float | None:
    """Entry fill model; limit entry never goes beyond limit price.
    Stop may gap through adversely and adds entry slippage.
    """
    opening, hi, lo = map(float, bars[idx, :3])
    if kind == "MARKET":
        return opening + side * SLIP
    if requested is None:
        raise ValueError("Missing trigger price")
    if kind == "LIMIT":
        touched = (lo <= requested) if side == 1 else (hi >= requested)
        return requested if touched else None
    if kind == "STOP":
        touched = (hi >= requested) if side == 1 else (lo <= requested)
        if not touched:
            return None
        raw = max(opening, requested) if side == 1 else min(opening, requested)
        return raw + side * SLIP
    raise base.UnsupportedV2Feature("Unknown entry type")


def _risk(bars: np.ndarray, decision: int, side: int, entry: float, sl: dict) -> float | None:
    if sl["kind"] != "CHANDELIER":
        return base._risk_distance(bars, decision, side, entry, sl)
    n = int(sl["period"])
    if n < 3 or n > 120 or decision+1 < n:
        return None
    atr = base.indicator_value(bars, decision, {"name": "ATR", "parameters": {"period": n}})
    if atr is None:
        return None
    context = bars[decision+1-n:decision+1]
    extreme = float(np.max(context[:, 1])) if side == 1 else float(np.min(context[:, 2]))
    stop_level = extreme - side*float(sl["atr_multiple"])*atr
    distance = side*(entry-stop_level)
    if distance <= 0:
        return None
    return base._round_up_to_tick(distance)


def _tp_distance(bars: np.ndarray, decision: int, side: int,
                 entry: float, risk: float, target: dict) -> float | None:
    if target["kind"] == "NONE":
        return None
    if target["kind"] != "CAUSAL_LEVEL":
        return base._target_distance(bars, decision, risk, target)
    vw = base.indicator_value(bars, decision, {"name": "VWAP",
                                             "parameters": {"anchor": "session"}})
    if vw is None:
        return None
    distance = side*(vw-entry)
    if distance < TICK:
        return None
    return base._round_down_to_tick(distance)


def _tighten_stop(bars: np.ndarray, previous_bar: int, side: int,
                  entry: float, risk: float, old_stop: float, exit_policy: dict):
    """Move a protective stop ONLY from data of an already completed bar."""
    favorable = (float(bars[previous_bar, 1]) if side == 1
                 else float(bars[previous_bar, 2]))
    gain = side*(favorable-entry)
    proposed = old_stop
    be = exit_policy["break_even"]
    if be is not None and gain >= float(be["start_r"])*risk:
        level = entry+side*float(be["plus_ticks"])*TICK
        proposed = max(proposed, level) if side == 1 else min(proposed, level)
    trail = exit_policy["trailing"]
    if trail is not None and gain >= float(trail["start_r"])*risk:
        atr = base.indicator_value(bars, previous_bar, {"name": "ATR",
                    "parameters": {"period": int(trail["atr_period"])}})
        if atr is not None:
            level = favorable - side*float(trail["distance_atr"])*atr
            proposed = max(proposed, level) if side == 1 else min(proposed, level)
    # Grid conservative: floor protective sell stops, ceil protective buy stops.
    return _tick(proposed, "DOWN" if side == 1 else "UP")


def _exit_trade(bars: np.ndarray, decision: int, fill_idx: int, side: int,
                entry: float, risk: float, target_distance: float | None,
                kind: str, exit_policy: dict) -> dict:
    sl = _tick(entry-side*risk, "DOWN" if side == 1 else "UP")
    tp = (None if target_distance is None else
          _tick(entry+side*target_distance, "UP" if side == 1 else "DOWN"))
    expiry = exit_policy["exit_after_bars"]
    end = min(LAST_IDX, fill_idx+int(expiry)-1) if expiry is not None else LAST_IDX
    updates = 0
    for j in range(fill_idx, end+1):
        # On the entry bar a pending order's pre-fill high/low MUST NEVER
        # tighten a stop. Even on MARKET, modifications take effect next bar.
        if j > fill_idx and (kind == "MARKET" or j-1 > fill_idx):
            new_sl = _tighten_stop(bars, j-1, side, entry, risk, sl, exit_policy)
            if new_sl != sl:
                updates += 1
                sl = new_sl
        opening, high, low, close = map(float, bars[j, :4])
        hit_sl = (low <= sl) if side == 1 else (high >= sl)
        hit_tp = (tp is not None and ((high >= tp) if side == 1 else (low <= tp)))
        if hit_sl:
            exit_raw = min(opening, sl) if side == 1 else max(opening, sl)
            reason = "SL_FIRST_OR_GAP"
        elif hit_tp and not (kind != "MARKET" and j == fill_idx):
            # For pending orders the TP may have printed BEFORE entry within
            # the same M1 bar. Suppress same-bar TP to avoid favorable bias.
            exit_raw, reason = tp, "TP"
        elif j == end:
            exit_raw = close
            reason = "TIME_1129" if j == LAST_IDX else "TIMEOUT_BARS"
        else:
            continue
        exit_px = exit_raw-side*SLIP
        net = round(side*(exit_px-entry)*POINT_USD-FEE, 2)
        return {"exit_idx": j, "exit_price": round(exit_px, 5),
                "exit_reason": reason, "net_usd": net,
                "stop_updates": updates, "final_stop_price": sl,
                "target_price": tp}
    raise AssertionError("Mandatory time close not reached")


def simulate_day(bars: np.ndarray, strategy: dict, session: str,
                 policy: dict | None = None) -> dict:
    """Fail-closed IST-only one-strategy proxy; no market data opened here."""
    validate_supported(strategy)
    try:
        d = date.fromisoformat(session)
    except (ValueError, TypeError):
        raise ValueError("Require exact YYYY-MM-DD ISO session") from None
    if d.year not in (2020, 2021, 2022):
        raise PermissionError("V2 generator/backtester restricted to IST 2020-22")
    if (not isinstance(bars, np.ndarray) or bars.shape != (390, 5)
            or not np.isfinite(bars).all() or (bars[:, 4] < 0).any()
            or (bars[:, 1] < bars[:, 2]).any()
            or (bars[:, 1] < bars[:, [0,3]].max(axis=1)).any()
            or (bars[:, 2] > bars[:, [0,3]].min(axis=1)).any()
            or (np.abs(bars[:, :4] / TICK - np.round(bars[:, :4] / TICK)) > 1e-7).any()):
        raise ValueError("Malformed RTH 390 x OHLCV bars")
    p = dict(REFERENCE_ACCOUNT if policy is None else policy)
    if (p["max_open_positions"] != 1 or p["max_entries_per_day"] < 1
            or p["max_initial_stop_risk_usd"] <= 0 or
            p["daily_closed_pnl_pause_usd"] >= 0):
        raise ValueError("Invalid one-account policy")
    trades, rejected = [], {"expired_pending": 0, "risk_ineligible": 0,
                            "ambiguous_side": 0, "missing_stop_context": 0,
                            "invalid_or_unavailable_target": 0}
    signal_diagnostics = {"decision_bars_checked": 0, "raw_long_at_decision": 0,
                          "raw_short_at_decision": 0, "both_sides_at_decision": 0,
                          "nq_risk_reject_feasible_as_1mnq": 0,
                          "nq_risk_reject_not_feasible_as_1mnq": 0}
    i = 20
    daily_net = 0.
    while i < LAST_IDX and len(trades) < p["max_entries_per_day"]:
        if daily_net <= p["daily_closed_pnl_pause_usd"]:
            break
        lon = base.eval_expr(bars, i, strategy["long"])
        sho = base.eval_expr(bars, i, strategy["short"])
        signal_diagnostics["decision_bars_checked"] += 1
        signal_diagnostics["raw_long_at_decision"] += int(lon)
        signal_diagnostics["raw_short_at_decision"] += int(sho)
        signal_diagnostics["both_sides_at_decision"] += int(lon and sho)
        if not lon and not sho:
            i += 1
            continue
        if lon and sho:
            rejected["ambiguous_side"] += 1
            i += 1
            continue
        side = 1 if lon else -1
        kind = strategy["entry_order"]["kind"]
        exp = int(strategy["entry_order"]["expiry_bars"])
        requested = _entry_limit_or_trigger(float(bars[i,3]), side, kind,
                                             strategy["entry_order"]["offset_ticks"])
        last_pending_bar = min(LAST_IDX, i+(1 if kind == "MARKET" else exp))
        fill_idx, entry = None, None
        for j in range(i+1, last_pending_bar+1):
            candidate = _pending_fill(bars, j, side, kind, requested)
            if candidate is not None:
                fill_idx, entry = j, candidate
                break
        if fill_idx is None:
            rejected["expired_pending"] += 1
            i = last_pending_bar
            continue
        risk = _risk(bars, i, side, entry, strategy["exit"]["stop_loss_required"])
        if risk is None:
            rejected["missing_stop_context"] += 1
            i = fill_idx
            continue
        # NQ price + realistic cost approximation, both entry/exit slippage
        # built into model fills, no broker guarantees on gaps.
        exit_slip_usd = SLIP*POINT_USD
        initial_adverse = risk*POINT_USD+exit_slip_usd+FEE
        if initial_adverse > p["max_initial_stop_risk_usd"]:
            rejected["risk_ineligible"] += 1
            # Diagnostic ONLY: one MNQ at the SAME stop distance. Reference
            # MNQ $2/point and $1.90 RT fee; exit 2 ticks adverse. Does not
            # create MNQ orders, performance, sizing or trade eligibility.
            projected_mnq_risk = risk*2.0 + SLIP*2.0 + 1.90
            bucket = ("nq_risk_reject_feasible_as_1mnq" if
                      projected_mnq_risk <= p["max_initial_stop_risk_usd"]
                      else "nq_risk_reject_not_feasible_as_1mnq")
            signal_diagnostics[bucket] += 1
            i = fill_idx
            continue
        tp = _tp_distance(bars, i, side, entry, risk,
                          strategy["exit"]["profit_target"])
        if strategy["exit"]["profit_target"]["kind"] != "NONE" and tp is None:
            rejected["invalid_or_unavailable_target"] += 1
            i = fill_idx
            continue
        executed = _exit_trade(bars, i, fill_idx, side, entry, risk, tp,
                               kind, strategy["exit"])
        trade = {"date": session, "strategy_id": strategy.get("id", fingerprint(strategy)[:16]),
                 "signal_idx": i, "entry_idx": fill_idx,
                 "entry_order_kind": kind, "requested_price": requested,
                 "entry_price": round(entry, 5), "initial_risk_usd": round(initial_adverse, 2),
                 "side": side, **executed}
        trades.append(trade)
        daily_net += executed["net_usd"]
        # Re-evaluate only using bar already closed. Any next entry is no
        # earlier than the subsequent minute.
        i = executed["exit_idx"]
    return {"status": STATUS, "session": session, "trades": trades,
            "rejected": rejected, "filled": len(trades),
            "closed_pnl": round(daily_net, 2), "signal_diagnostics": signal_diagnostics,
            "holdouts": "SEALED"}
