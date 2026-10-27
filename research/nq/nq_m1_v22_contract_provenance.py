#!/usr/bin/env python3
"""NQ V2.2 explicit RTH contract provenance for causal indicator warmup.

Reuses the EXACT deterministic roll_contract() that the immutable V1 M1 ZIP
reader used when selecting the source member. Does not open any prices.
All dates are IST 2020-22, sorted unique, with explicit NQ expiry labels.
This adapter is a stage-0 contract metadata layer, NOT integration into
the market execution engine or independent validation of roll rules.
"""
from __future__ import annotations
from datetime import date
from collections import Counter
import numpy as np

from research.nq.nq_h05_h07_level_volume_screen import roll_contract
from research.nq.nq_m1_v21_warmup_context import SessionMeta, history_for_session

PERMITTED_YEARS = frozenset((2020, 2021, 2022))
STATUS = "NQ_IST_CONTRACT_METADATA_DERIVED_FROM_EXISTING_READER_ROLL_MAP"


def metadata_for_sessions(dates: list[str], bars: np.ndarray) -> list[SessionMeta]:
    if not isinstance(bars,np.ndarray) or bars.ndim!=3 or bars.shape[1:]!=(390,5):
        raise ValueError("Expected complete [session,390,OHLCV] tensor")
    if not isinstance(dates, list) or len(dates)!=len(bars):
        raise ValueError("Dates and arrays mismatched")
    previous=None
    meta=[]
    for day in dates:
        try:
            d=date.fromisoformat(day)
        except (ValueError,TypeError):
            raise ValueError("Invalid ISO session date") from None
        if d.year not in PERMITTED_YEARS:
            raise PermissionError("No 2023/24 evaluation or sealed 2025/26 permitted")
        if previous is not None and d<=previous:
            raise ValueError("Session dates must be strictly increasing, without duplicates")
        previous=d
        contract=roll_contract(d)
        if not contract.startswith("NQ_") or len(contract)!=8:
            raise RuntimeError("Unexpected contract label from existing canonical roll map")
        meta.append(SessionMeta(session_date=day,contract_id=contract,symbol="NQ"))
    return meta


def prior_same_contract(dates: list[str], bars: np.ndarray,
                        target_index: int, max_prior_sessions: int=2) -> dict:
    meta=metadata_for_sessions(dates,bars)
    if (type(target_index) is not int or
            not 0<=target_index<len(meta)):
        raise ValueError("Invalid target session index")
    active=meta[target_index]
    candidates=[]
    for j in range(max(0,target_index-max_prior_sessions),target_index):
        if meta[j].contract_id!=active.contract_id:
            # Respect roll boundary: only take the suffix of prior sessions
            # having the same concrete contract, never skip a roll gap.
            candidates=[]
        else:
            candidates.append((meta[j],bars[j]))
    historical=history_for_session(active,bars[target_index],candidates,
                                   max_prior_sessions=max_prior_sessions)
    return {
        "status":STATUS, "target":active,
        "source_contract":active.contract_id,
        "prior_session_dates":[m.session_date for m,_ in candidates],
        "prior_bars":historical,
        "contract_boundary_detected":bool(target_index and
            meta[target_index-1].contract_id!=active.contract_id),
        "holdouts":"SEALED"
    }


def audit_roll_coverage(dates: list[str], bars: np.ndarray) -> dict:
    meta=metadata_for_sessions(dates,bars)
    hist=Counter(x.contract_id for x in meta)
    changes=[]
    for prev,cur in zip(meta,meta[1:]):
        if prev.contract_id!=cur.contract_id:
            changes.append({"first_session_new_contract":cur.session_date,
                            "previous_contract":prev.contract_id,
                            "new_contract":cur.contract_id})
    return {
        "status":STATUS, "sessions":len(meta),
        "contracts_present":dict(sorted(hist.items())),
        "changes":changes,
        "risk": "DERIVED_CONTRACT_ID_NOT_INDEPENDENTLY_MATCHED_TO_ACTUAL_TICK_CONTRACT",
        "years_allowed":sorted(PERMITTED_YEARS),
        "holdouts":"SEALED"
    }
