#!/usr/bin/env python3
"""NQ 1-contract shared-account EVENT REPLAY QA (only artificial events).

Simulates deterministic chronological intents, marked equity and exits to
test portfolio invariants; DOES NOT execute NQ OHLC/tick historical data or
choose promising strategies. All prices are synthetic NQ tick-grid.
A delayed or absent STOP fill must be disclosed, never invented.

Caveats: simplified reference Builder evaluation 50K trailing model, neither
confirmation of user's MFFU plan nor real exchange order-book dynamics.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from math import isfinite

STATUS = "SYNTHETIC_NQ_SHARED_ACCOUNT_EVENT_G0_QA_NOT_BACKTEST"
TICK = .25
DOLLARS_PER_POINT = 20.
BASELINE_RT_COST = 24.68  # 4.68 commission + 2 adverse ticks / side
INITIAL = 50_000.
MAX_INITIAL_RISK = 300.
MAX_ENTRIES = 2
DAILY_CLOSED_PAUSE = -600.
SOFT_DAILY_EQUITY_LOSS = 1_000.
EOD_TRAIL = 2_000.
EOD_FLOOR_LOCK = 50_100.
CUTOFF_END_BAR = 118
PHASE = {"ENTRY": 0, "MARK": 1, "EXIT": 2}


def _grid(price):
    return (type(price) in (int, float)
            and isfinite(price) and price > 0
            and abs(price / TICK - round(price / TICK)) < 1e-7)


def _validate_event(e:dict, priority:dict):
    if not isinstance(e,dict):
        raise ValueError("Event must be a dict")
    day=e.get("date")
    try:
        d=date.fromisoformat(day)
    except (TypeError,ValueError):
        raise ValueError("Invalid ISO date") from None
    if d.year not in (2020,2021,2022):
        raise PermissionError("IST 2020-22 only; holdouts sealed")
    if e.get("instrument")!="NQ" or e.get("contracts")!=1:
        raise PermissionError("Only single NQ model positions")
    i=e.get("idx")
    if type(i) is not int or not 0<=i<=CUTOFF_END_BAR:
        raise ValueError("Invalid local RTH end-bar index")
    kind=e.get("kind")
    if kind not in PHASE or not _grid(e.get("price")):
        raise ValueError("Unknown event or off-grid price")
    if kind=="ENTRY":
        if (e.get("strategy_id") not in priority
                or type(e.get("signal_idx")) is not int
                or not 0<=e["signal_idx"]<i
                or e.get("side") not in (-1,1)
                or not _grid(e.get("stop"))):
            raise ValueError("Noncausal, malformed or unknown NQ order intent")
        if (e["side"]==1 and e["stop"]>=e["price"]
                or e["side"]==-1 and e["stop"]<=e["price"]):
            raise ValueError("Stop must protect on adverse side")
    else:
        if kind=="EXIT" and not _grid(e.get("price")):
            raise ValueError("Exit price is invalid")
    return day


def _entry_risk(e):
    distance=e["side"]*(e["price"]-e["stop"])
    return distance*DOLLARS_PER_POINT+BASELINE_RT_COST


def replay(events:list[dict], priority:list[str])->dict:
    if not priority or len(set(priority))!=len(priority):
        raise ValueError("Frozen distinct priority required")
    if not isinstance(events,list):
        raise ValueError("Ordered events list required")
    rank={name:i for i,name in enumerate(priority)}
    dates=[_validate_event(e,rank) for e in events]
    if any(b<a for a,b in zip(dates,dates[1:])):
        raise ValueError("Events must be sorted by actual calendar date")
    # Stable same-minute phases; ENTRY intents compete using frozen priority,
    # not later marks/exits, and cannot be replaced using known future PnL.
    by_day={}
    for e in events:
        by_day.setdefault(e["date"],[]).append(e)
    balance=INITIAL
    floor=INITIAL-EOD_TRAIL
    peak_eod=INITIAL
    all_trades=[]
    records=[]
    rejections=Counter()
    ever_hard=False
    for day,daily in by_day.items():
        if ever_hard:
            raise PermissionError("No events permitted after funded hard breach")
        daily=sorted(daily,key=lambda e:(e["idx"],PHASE[e["kind"]],
                     rank.get(e.get("strategy_id"),9999)))
        open_trade=None
        opened_balance=balance
        day_entries=0
        daily_closed=0.
        soft_paused=False
        hard_breach=False
        peak_unrealized=None
        last_bar=-1
        same_entry_minutes=set()
        entry_order_details=[]
        for event in daily:
            bar=event["idx"]
            if bar<last_bar:
                raise ValueError("Cannot rewind bar clock")
            last_bar=bar
            kind=event["kind"]
            if kind=="ENTRY":
                if bar in same_entry_minutes:
                    rejections["SAME_MINUTE_LOWER_PRIORITY"]+=1
                    continue
                if hard_breach:
                    rejections["HARD_BREACH_BLOCK"]+=1
                    continue
                if soft_paused:
                    rejections["SOFT_EQUITY_PAUSE"]+=1
                    continue
                if daily_closed<=DAILY_CLOSED_PAUSE:
                    rejections["INTERNAL_CLOSED_PNL_PAUSE"]+=1
                    continue
                if open_trade is not None:
                    rejections["SHARED_POSITION_BUSY"]+=1
                    continue
                if day_entries>=MAX_ENTRIES:
                    rejections["MAX_ENTRIES_PER_DAY"]+=1
                    continue
                risk=_entry_risk(event)
                if risk<=0 or risk>MAX_INITIAL_RISK:
                    rejections["NQ_INITIAL_RISK_CAP"]+=1
                    continue
                same_entry_minutes.add(bar)
                open_trade={"strategy_id":event["strategy_id"],
                            "entry_idx":bar,"entry_price":float(event["price"]),
                            "stop_price":float(event["stop"]), "side":event["side"],
                            "risk_usd":round(risk,2),
                            "mark_count":0,
                            "min_floating_equity":balance-BASELINE_RT_COST,
                            "stop_crossed_unreconciled":False}
                day_entries+=1
                entry_order_details.append({"strategy_id":event["strategy_id"],
                                            "idx":bar,"risk_usd":round(risk,2)})
            elif kind=="MARK":
                if open_trade is None:
                    raise ValueError("Cannot mark equity without an open position")
                gross=(event["price"]-open_trade["entry_price"])*DOLLARS_PER_POINT*open_trade["side"]
                marked=balance+gross-BASELINE_RT_COST
                open_trade["mark_count"]+=1
                open_trade["min_floating_equity"]=min(open_trade["min_floating_equity"],marked)
                if marked<=opened_balance-SOFT_DAILY_EQUITY_LOSS:
                    soft_paused=True
                if marked<=floor:
                    hard_breach=True
                # A trade can cross a synthetic stop and still be open when
                # using Last marks (gap, queue or missing execution evidence).
                # Reject such an event sequence as an unresolved execution.
                if ((open_trade["side"]==1 and event["price"]<=open_trade["stop_price"])
                        or (open_trade["side"]==-1 and event["price"]>=open_trade["stop_price"])):
                    open_trade["stop_crossed_unreconciled"]=True
            else:
                if open_trade is None or bar<=open_trade["entry_idx"]:
                    raise ValueError("Exit needs an earlier actual entry")
                if (event.get("strategy_id") is not None
                        and event["strategy_id"]!=open_trade["strategy_id"]):
                    raise ValueError("Exit belongs to different strategy")
                pnl=(event["price"]-open_trade["entry_price"])*DOLLARS_PER_POINT*open_trade["side"]-BASELINE_RT_COST
                balance+=pnl
                daily_closed+=pnl
                if balance<=opened_balance-SOFT_DAILY_EQUITY_LOSS:
                    soft_paused=True
                if balance<=floor:
                    hard_breach=True
                all_trades.append({
                    **open_trade,"exit_idx":bar,"exit_price":float(event["price"]),
                    "synthetic_net_usd":round(pnl,2),
                    "date":day, "stop_crossed_unreconciled":open_trade["stop_crossed_unreconciled"]})
                if open_trade["stop_crossed_unreconciled"]:
                    raise ValueError("STOP_CROSSED_WITHOUT_ATOMIC_FILL_RECONCILIATION")
                open_trade=None
        if open_trade is not None:
            raise ValueError("No overnight NQ position; missing synthetic EXIT")
        if not hard_breach:
            peak_eod=max(peak_eod,balance)
            floor=max(floor,min(EOD_FLOOR_LOCK,peak_eod-EOD_TRAIL))
        records.append({"date":day,"entries":day_entries,"closed_pnl_usd":round(daily_closed,2),
                        "eod_balance":round(balance,2),
                        "hard_floor_after_close":round(floor,2),
                        "soft_pause_triggered":soft_paused,
                        "hard_breach_triggered":hard_breach,
                        "accepted_entry_intents":entry_order_details})
        if hard_breach:
            ever_hard=True
    return {"status":STATUS, "asset":"NQ","contracts":1,
            "trades":all_trades,"days":records,"rejections":dict(rejections),
            "hard_breach":ever_hard,"ending_balance":round(balance,2),
            "official_account_plan_verified":False,
            "actual_trades_backtested":False,
            "real_tick_fill_parity_certified":False,
            "holdouts":"SEALED"}
