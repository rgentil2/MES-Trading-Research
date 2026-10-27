#!/usr/bin/env python3
"""NQ-only V2.1 causal multi-session RTH warmup, TECHNICAL CONTRACT ONLY.

Every prior session must be a complete, strictly earlier IST RTH session from
the SAME explicit futures contract_id. Rolling windows may then carry history
without accidentally stitching unadjusted contract-roll gaps. Session-anchored
VWAP and OBV explicitly restart at the target session. No orders or market
archive are read here; full IST backtesting remains pending.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import numpy as np
from research.nq import nq_m1_v2_m1_engine as engine

IST_YEARS = frozenset((2020,2021,2022))
SESSION_BARS = 390
SUPPORTED_CONTEXT_MODE = "SAME_CONTRACT_PRIOR_COMPLETED_RTH_ONLY"
SESSION_LOCAL_INDICATORS = frozenset(("VWAP","OBV"))


@dataclass(frozen=True)
class SessionMeta:
    session_date: str
    contract_id: str
    symbol: str = "NQ"


def _check_date(d: str) -> date:
    try:
        val=date.fromisoformat(d)
    except (ValueError,TypeError):
        raise ValueError("Malformed NQ session date") from None
    if val.year not in IST_YEARS:
        raise PermissionError("V2.1 warmup forbids ISV and 2025/2026 holdouts")
    return val


def _check_complete_session(meta: SessionMeta, bars: np.ndarray):
    _check_date(meta.session_date)
    if meta.symbol!="NQ" or not meta.contract_id or not meta.contract_id.startswith("NQ"):
        raise ValueError("Required explicit NQ futures contract identifier")
    if (not isinstance(bars,np.ndarray) or bars.shape!=(SESSION_BARS,5)
            or not np.isfinite(bars).all() or (bars[:,4]<0).any()
            or (bars[:,1]<bars[:,2]).any()):
        raise ValueError("Only complete valid NQ RTH sessions can be warmup sources")


def history_for_session(target: SessionMeta, current: np.ndarray,
                        previous: list[tuple[SessionMeta,np.ndarray]],
                        max_prior_sessions: int=2) -> np.ndarray:
    """Return only <=2 prior SAME-contract sessions; never mix roll boundaries.

    Target current OHLCV is validated for shape but is NEVER joined to returned
    history. Caller explicitly supplies the *current elapsed prefix* at query.
    """
    _check_complete_session(target,current)
    if type(max_prior_sessions) is not int or not 0<=max_prior_sessions<=5:
        raise ValueError("Previous RTH session budget outside 0..5")
    used,prior_date=[],None
    target_date=_check_date(target.session_date)
    for m,bars in previous:
        _check_complete_session(m,bars)
        d=_check_date(m.session_date)
        if d>=target_date:
            raise PermissionError("Current/future session cannot be used for warmup")
        if prior_date is not None and d<=prior_date:
            raise ValueError("Previous sessions must be strictly sorted and unique")
        prior_date=d
        if m.contract_id!=target.contract_id:
            raise ValueError("Unadjusted contract roll: explicit same-contract data required")
        used.append(bars)
    selected=used[-max_prior_sessions:] if max_prior_sessions else []
    return np.vstack(selected) if selected else np.empty((0,5),dtype=float)


def indicator_at(target: SessionMeta, current: np.ndarray, bar_end_index: int,
                 indicator: dict, previous: list[tuple[SessionMeta,np.ndarray]]) -> float | None:
    """Indicator as of completed current bar; positive earlier RTH history only.

    ATR/RSI/etc reflect prior completed session bars of SAME contract,
    including the RTH overnight gap in next-session true range by explicit
    convention. VWAP and OBV restart at the current session boundary.
    """
    hist=history_for_session(target,current,previous)
    if type(bar_end_index) is not int or not 0<=bar_end_index<SESSION_BARS:
        raise ValueError("Current complete end-labeled bar index is required")
    current_prefix=current[:bar_end_index+1]
    if indicator["name"] in SESSION_LOCAL_INDICATORS:
        return engine.indicator_value(current_prefix,len(current_prefix)-1,indicator)
    joined=np.vstack([hist,current_prefix]) if len(hist) else current_prefix
    return engine.indicator_value(joined,len(joined)-1,indicator)
