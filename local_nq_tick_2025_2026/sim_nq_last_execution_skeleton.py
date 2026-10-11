#!/usr/bin/env python3
"""Conservative hypothetical single-NQ trade-fill engine, SYNTHETIC TESTS ONLY.

No strategy signals included. Never use Bid/Ask at same timestamp for fills.
Last prints do NOT prove live executability. Parameters are required, NOT tuned
or inferred from source QC. No 2026-Jul-Sep data may enter this module.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,time,timezone
from itertools import groupby
from zoneinfo import ZoneInfo
import math
from qc_tick_day import check_day

TICKS_PER_POINT=4
NQ_USD_PER_TICK=5.0
ONE_MS=10000

@dataclass(frozen=True)
class FillPolicy:
    """Explicit inputs: never infer live costs from Last/Bid/Ask export."""
    latency_ms:int
    entry_slippage_ticks:int
    exit_slippage_ticks:int
    stop_ticks:int
    take_profit_ticks:int
    max_holding_seconds:int
    commission_round_trip_usd:float
    contracts:int=1
    def __post_init__(self):
        if self.latency_ms<1 or self.entry_slippage_ticks<0 or self.exit_slippage_ticks<0:
            raise ValueError("Require positive latency, nonnegative adverse slippage")
        if self.stop_ticks<1 or self.take_profit_ticks<1:
            raise ValueError("Stop and TP must be positive ticks")
        if not 1<=self.max_holding_seconds<=3600:
            raise ValueError("Holding time must be 1..3600 seconds")
        if self.contracts!=1:
            raise ValueError("Only 1 NQ supported at this stage; no sizing optimization")
        if not math.isfinite(self.commission_round_trip_usd) or self.commission_round_trip_usd<0:
            raise ValueError("Explicit finite nonnegative NQ RT fees required")

@dataclass(frozen=True)
class Signal:
    day_et:str
    timestamp_100ns:int
    side:int  # +1 buy/long, -1 sell/short
    def __post_init__(self):
        d=check_day(self.day_et)
        if self.side not in (1,-1):raise ValueError("invalid side")
        ny=ZoneInfo("America/New_York")
        def edge(h,m):
            x=datetime.combine(d,time(h,m),tzinfo=ny).astimezone(timezone.utc)
            return int(x.timestamp())*10000000
        if not edge(9,30)<=self.timestamp_100ns<edge(11,30):
            raise ValueError("Signal must occur 09:30-11:30 ET")

def _cutoff(day):
    d=check_day(day)
    end=datetime.combine(d,time(11,30),tzinfo=ZoneInfo("America/New_York"))
    return int(end.astimezone(timezone.utc).timestamp())*10000000

def simulate_single_trade(events,signal:Signal,policy:FillPolicy):
    """Receive ordered (ts_100ns, price_ticks, qty) Last prints.

    At entry, choose worst price within first eligible shared timestamp. At exit,
    when both barriers appear within one timestamp, stop takes precedence.
    Same entry-timestamp barrier touch is AMBIGUOUS -> fail-closed, no P&L.
    Unresolved end of data is NOT marked as a profit/loss.
    """
    check_day(signal.day_et)  # before touching events
    cutoff=_cutoff(signal.day_et)
    eligibility=signal.timestamp_100ns + policy.latency_ms*ONE_MS
    last_t=None
    entry=None
    stop=target=None
    n_groups=0
    for ts,g in groupby(events,key=lambda e:e[0]):
        if last_t is not None and ts<last_t:
            raise ValueError("Last events not time ordered")
        last_t=ts;n_groups+=1
        ticks=[]
        for t,px,qty in g:
            if t!=ts or not isinstance(px,int) or px<=0 or not isinstance(qty,int) or qty<=0:
                raise ValueError("Invalid Last event")
            ticks.append(px)
        if ts<=signal.timestamp_100ns:
            continue
        if entry is None:
            if ts<eligibility:
                continue
            if ts>=cutoff:
                return {"status":"NO_ENTRY_BEFORE_SESSION_CUTOFF","trading_outcomes_valid":False}
            # The first eligible timestamp may contain many prices without
            # exchange sequence; worst available within that timestamp.
            ref=max(ticks) if signal.side==1 else min(ticks)
            price=ref+signal.side*policy.entry_slippage_ticks
            if price<=0:raise ValueError("entry price invalid")
            entry=(ts,price)
            stop=price-signal.side*policy.stop_ticks
            target=price+signal.side*policy.take_profit_ticks
            # Any same-timestamp stop touch is unresolved, cannot assume
            # the entry was safely earlier than it.
            if any(signal.side*(p-stop)<=0 for p in ticks):
                return {"status":"ENTRY_TIMESTAMP_BARRIER_AMBIGUOUS","trading_outcomes_valid":False}
            continue
        # TS strict later than entry required; groups of Last prints are unordered.
        if ts==entry[0]:continue
        triggered_stop=[px for px in ticks if signal.side*(px-stop)<=0]
        triggered_target=any(signal.side*(px-target)>=0 for px in ticks)
        if triggered_stop:
            reason="STOP"
            # Gap past stop is filled at the worse observed print, never at
            # a favorable stopped-out price.
            exit_reference=(min(triggered_stop) if signal.side==1 else max(triggered_stop))
        elif triggered_target:
            reason="TAKE_PROFIT"
            # Market exit capped to TP; never collect a favorable price beyond TP.
            exit_reference=target
        elif ts>=entry[0]+policy.max_holding_seconds*10000000 or ts>=cutoff:
            reason="TIMEOUT_OR_SESSION"
            exit_reference=(min(ticks) if signal.side==1 else max(ticks))
        else:
            continue
        exit_price=exit_reference - signal.side*policy.exit_slippage_ticks
        gross_ticks=signal.side*(exit_price-entry[1])
        return {
            "status":"SYNTHETIC_FILL_MODEL_ONLY",
            "exit_reason":reason,
            "entry_timestamp":entry[0],"exit_timestamp":ts,
            "entry_price_ticks":entry[1],"exit_price_ticks":exit_price,
            "gross_ticks":gross_ticks,
            "gross_usd":round(gross_ticks*NQ_USD_PER_TICK*policy.contracts,2),
            "estimated_net_usd":round(gross_ticks*NQ_USD_PER_TICK*policy.contracts-policy.commission_round_trip_usd,2),
            "assumed_latency_ms":policy.latency_ms,
            "assumed_adverse_slippage_total_ticks":policy.entry_slippage_ticks+policy.exit_slippage_ticks,
            "trading_outcomes_valid":False,  # no actual market fills or signal validation
            "warning":"Hypothetical Last-print path. Tick prints cannot confirm fill, spread, queue or broker stop execution"
        }
    return {"status":"UNRESOLVED_END_OF_LAST_DATA" if entry else "NO_ENTRY_EVENT",
            "trading_outcomes_valid":False}
