#!/usr/bin/env python3
"""Synthetic NQ Last-tick first-touch reference for OHLC ambiguity audits ONLY.

Raw Last prints establish which protective barrier was crossed first.
This does NOT model exchange queue priority, limit fills, partial fills,
commission, bid/ask spread, NinjaTrader replay, or official account risk.
No market data or private tick archive is ever opened here.
"""
from __future__ import annotations
from datetime import date
import math

TICK=.25
VALID_YEARS=frozenset((2020,2021,2022))
STATUS="SYNTHETIC_NQ_LAST_FIRST_TOUCH_NOT_BROKER_EXECUTION"


def tick_barrier(ticks:list[tuple[int,float]], side:int, stop:float,
                 target:float|None, entry_timestamp:int, day:str)->dict:
    d=date.fromisoformat(day)
    if d.year not in VALID_YEARS:
        raise PermissionError("No ISV or sealed year price access")
    if side not in (-1,1):
        raise ValueError("Side must be +1 or -1")
    if (not math.isfinite(stop) or stop<=0 or
            target is not None and (not math.isfinite(target) or target<=0)):
        raise ValueError("Barrier prices invalid")
    if stop/TICK!=round(stop/TICK):
        raise ValueError("Stop must be on NQ tick grid")
    if target is not None and target/TICK!=round(target/TICK):
        raise ValueError("Target must be on NQ tick grid")
    seen=None
    after=0
    for timestamp,price in ticks:
        if type(timestamp) is not int or (seen is not None and timestamp<=seen):
            raise ValueError("Atomic Last timestamps must be increasing and unique")
        if not math.isfinite(price) or price<=0:
            raise ValueError("Invalid raw Last print")
        seen=timestamp
        if timestamp<=entry_timestamp:
            continue
        after+=1
        hit_stop=(price<=stop) if side==1 else (price>=stop)
        hit_tp=target is not None and ((price>=target) if side==1 else (price<=target))
        if hit_stop:
            return {"status":STATUS,"result":"STOP",
                    "first_touch_timestamp":timestamp,"first_last_price":price,
                    "ticks_examined_after_entry":after,"economic_result":None}
        if hit_tp:
            return {"status":STATUS,"result":"TARGET",
                    "first_touch_timestamp":timestamp,"first_last_price":price,
                    "ticks_examined_after_entry":after,"economic_result":None}
    return {"status":STATUS,"result":"NO_BARRIER_TOUCHED",
            "first_touch_timestamp":None,"first_last_price":None,
            "ticks_examined_after_entry":after,"economic_result":None}


def ohlc_stop_first(high:float,low:float,side:int,
                    stop:float,target:float|None)->str:
    if side not in (-1,1) or high<low:
        raise ValueError("Invalid NQ model bar")
    sl=(low<=stop) if side==1 else (high>=stop)
    tp=target is not None and ((high>=target) if side==1 else (low<=target))
    if sl:return "STOP"
    if tp:return "TARGET"
    return "NO_BARRIER_TOUCHED"
