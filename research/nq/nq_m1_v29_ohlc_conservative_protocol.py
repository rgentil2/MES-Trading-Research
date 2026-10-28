#!/usr/bin/env python3
"""S0.24 NQ M1-only conservative OHLC execution protocol -- independent fixture.

This is a deterministic, ONE-BAR synthetic reference, NOT a whole backtester
and NOT an exchange/broker fill oracle. This code reads no market files and
does not release the locked 13-gate economic pipeline.

When OHLC order within a minute is unknown: stop beats target on ambiguity;
adverse stop gaps fill at open + adverse slip; favorable target gap improvement
is discarded; pending limit exact touch does not prove queue fill, so require
a full tick trade-through, except marketable-at-open orders. The assumption
still cannot guarantee fill or true slippage. Pending same-bar TP forbidden.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

TICK=.25
POINT_USD=20.
DEFAULT_SLIP_TICKS_SIDE=2
COMMISSION_RT_USD=4.68
STATUS="S0_24_NQ_M1_OHLC_BOUNDS_EXPERIMENTAL_NO_BROKER_PARITY"
ACCEPTED_SOURCES=("NQ_M1_IST_2020_2022_ONLY",)

@dataclass(frozen=True)
class Bar:
    open:float
    high:float
    low:float
    close:float

def _grid(x:float)->bool:
    return abs(x/TICK-round(x/TICK))<1e-7

def _bar(b:Bar):
    if (not isinstance(b,Bar) or
        any(type(x) not in (int,float) or not math.isfinite(x) or x<=0
            for x in (b.open,b.high,b.low,b.close)) or
        b.low>b.high or b.high<max(b.open,b.close) or b.low>min(b.open,b.close) or
        not all(_grid(x) for x in (b.open,b.high,b.low,b.close))):
        raise ValueError("M1 requires finite positive price OHLC on NQ .25 grid")

def _side(side:int):
    if type(side) is not int or side not in (1,-1):
        raise ValueError("side must be 1 or -1")

def _price(x:float):
    if type(x) not in (int,float) or not math.isfinite(x) or x<=0 or not _grid(x):
        raise ValueError("NQ order levels must be positive on .25 tick grid")

def _slippage(n:int):
    if type(n) is not int or n<0:
        raise ValueError("Slippage must be a nonnegative integer tick count")
    return n*TICK

def entry(b:Bar,side:int,kind:str,requested:float|None=None,
          slippage_ticks:int=DEFAULT_SLIP_TICKS_SIDE)->dict:
    """Evaluate ONE next-minute OHLC bar, not submit historical orders."""
    _bar(b);_side(side);s=_slippage(slippage_ticks)
    if kind not in ("MARKET","STOP","LIMIT"):
        raise ValueError("Unsupported order kind")
    if kind=="MARKET":
        if requested is not None:raise ValueError("Market order cannot have level")
        px=b.open+side*s
        return {"status":STATUS,"filled_proxy":True,
                "fill_price":px,"reason":"NEXT_OPEN_WITH_ADVERSE_SLIPPAGE",
                "intraminute_path_known":False}
    _price(requested)
    if kind=="STOP":
        touched=(b.high>=requested if side==1 else b.low<=requested)
        if not touched:return {"status":STATUS,"filled_proxy":False,"fill_price":None,
                               "reason":"STOP_NOT_REACHED","intraminute_path_known":False}
        raw=max(b.open,requested) if side==1 else min(b.open,requested)
        px=raw+side*s
        return {"status":STATUS,"filled_proxy":True,"fill_price":px,
                "reason":"STOP_ADVERSE_GAP_OR_TRIGGER_SLIPPAGE",
                "intraminute_path_known":False}
    # A LIMIT hit at its exact level is NOT evidence that an order in an
    # exchange queue would fill. Use one tick trade-through. This is still
    # only a conservative assumption, not observed order-book queue position.
    at_open=(b.open<=requested if side==1 else b.open>=requested)
    beyond=(b.low<=requested-TICK if side==1 else b.high>=requested+TICK)
    if not (at_open or beyond):
        return {"status":STATUS,"filled_proxy":False,"fill_price":None,
                "reason":"LIMIT_TOUCH_ONLY_OR_NOT_CROSSED",
                "intraminute_path_known":False}
    return {"status":STATUS,"filled_proxy":True,"fill_price":requested,
            "reason":"LIMIT_MARKETABLE_OPEN_OR_TRADE_THROUGH_ONE_TICK",
            "intraminute_path_known":False}

def exit_bar(b:Bar,side:int,stop:float,target:float|None=None,
             pending_entry_same_bar:bool=False,
             forced_time_exit:bool=False,
             slippage_ticks:int=DEFAULT_SLIP_TICKS_SIDE)->dict:
    """Protective barriers on ONE bar after a modeled entry already exists.

    For pending entries, current bar OHLC might predate entry. A stop touch
    is conservatively charged anyway, but a favorable TP on that bar is
    suppressed (even if stop is not hit). Requiring stop-first is an adverse
    *scenario*, not proof of the historical price path.
    """
    _bar(b);_side(side);_price(stop)
    if target is not None:_price(target)
    s=_slippage(slippage_ticks)
    stop_hit=b.low<=stop if side==1 else b.high>=stop
    target_hit=target is not None and (b.high>=target if side==1 else b.low<=target)
    if stop_hit:
        raw=min(b.open,stop) if side==1 else max(b.open,stop)
        return {"status":STATUS,"exited_proxy":True,"exit_price":raw-side*s,
                "reason":"SL_STOP_FIRST_AMBIGUOUS" if target_hit else "SL_OR_ADVERSE_GAP",
                "ambiguous_bar":bool(target_hit),
                "target_suppressed":bool(target_hit)}
    if target_hit and not pending_entry_same_bar:
        # Do not book improvement above the limit target on favorable gaps.
        return {"status":STATUS,"exited_proxy":True,"exit_price":target,
                "reason":"TP_NO_GAP_IMPROVEMENT",
                "ambiguous_bar":False,"target_suppressed":False}
    if forced_time_exit:
        return {"status":STATUS,"exited_proxy":True,"exit_price":b.close-side*s,
                "reason":"FORCED_CLOSE_WITH_ADVERSE_SLIPPAGE",
                "ambiguous_bar":False,
                "target_suppressed":bool(target_hit)}
    return {"status":STATUS,"exited_proxy":False,"exit_price":None,
            "reason":"SAME_BAR_PENDING_TP_SUPPRESSED" if target_hit
                    else "NO_EXIT_BARRIER",
            "ambiguous_bar":False,
            "target_suppressed":bool(target_hit)}

def contract()->dict:
    """Machine-readable declaration, independent of any broker model."""
    return {"schema":"NQ_S024_M1_ONLY_OHLC_CONSERVATIVE_DRAFT_V1",
            "asset":"NQ","contracts":1,"timeframe":"M1",
            "data_source":"NQ_M1_IST_2020_2022_ONLY",
            "tick_size_points":TICK,"dollars_per_point":POINT_USD,
            "default_slippage_ticks_per_side":DEFAULT_SLIP_TICKS_SIDE,
            "provisional_roundtrip_commission_usd":COMMISSION_RT_USD,
            "pending_limit_exact_touch_counts_as_fill":False,
            "pending_limit_tradethrough_required_ticks":1,
            "same_bar_stop_first":True,"pending_entry_same_bar_target_allowed":False,
            "adverse_stop_gap_fill_at_open":True,
            "target_favorable_gap_improvement_allowed":False,
            "M1_backtest_authorized":False,"tick_certification_claimed":False,
            "quality_gate_passed_verified":0,
            "ISV1_2023":"SEALED","ISV2_2024":"SEALED",
            "2025_2026":"SEALED","frozen_roll_policy_modified":False,
            "use":"DESIGN_AND_SYNTHETIC_REFERENCE_ONLY"}
