"""NQ technical-only source-contract validation. No PnL or strategy selection."""
from __future__ import annotations
from datetime import date
import zipfile
from pathlib import Path
from collections import Counter
from research.nq.nq_m1_chrono_discovery import NAME_RE, permitted_market_member
from research.nq.nq_h05_h07_level_volume_screen import roll_contract

IST=(2020,2021,2022)
STATUS="NQ_IST_SOURCE_FILENAME_ONLY_TECHNICAL_QA"

def validate_member(member:str, day:str)->dict:
    if not permitted_market_member(member,IST):
        raise PermissionError("Only NQ 2020-22 permitted Minute_Last members")
    m=NAME_RE.fullmatch(member.rsplit("/",1)[-1])
    if m is None:
        raise ValueError("Unexpected archive member")
    d=date.fromisoformat(day)
    if d.year not in IST or d.year!=2000+int(m.group(3)):
        raise PermissionError("Only IST source day/year")
    actual_contract="NQ_"+m.group(1)+"-"+m.group(2)
    planned_contract=roll_contract(d)
    return {"date":day,"source_contract":actual_contract,
            "expected_contract":planned_contract,
            "selected":actual_contract==planned_contract,
            "is_nq":True}

def inspect_archive_manifest(path:Path)->dict:
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        selected=sorted(n for n in names if permitted_market_member(n,IST))
    if len(selected)!=15 or len(set(selected))!=15:
        raise ValueError("Unexpected IST NQ source member count")
    contracts=Counter()
    for name in selected:
        m=NAME_RE.fullmatch(name.rsplit("/",1)[-1])
        if m is None:
            raise ValueError("Unrecognized NQ member")
        contracts["NQ_"+m.group(1)+"-"+m.group(2)]+=1
    return {"status":STATUS,"allowed_years":list(IST),
            "source_members":len(selected),"contract_member_counts":dict(sorted(contracts.items())),
            "holdouts":"SEALED","market_member_contents_opened":False,
            "pnl_or_trades_calculated":False}


def audit_actual_session_sources(path:Path)->dict:
    """Trace accepted IST sessions to concrete archive file names, timestamps only."""
    import numpy as np
    import pandas as pd
    from research.nq.nq_m1_chrono_discovery import load_years
    from research.nq.nq_m1_v22_contract_provenance import metadata_for_sessions, prior_same_contract
    found={}
    partial=0
    with zipfile.ZipFile(path) as archive:
        names=sorted(n for n in archive.namelist()
                     if permitted_market_member(n,IST))
        if len(names)!=15:
            raise ValueError("Expected 15 IST source files")
        for name in names:
            with archive.open(name) as stream:
                ts=pd.read_csv(stream,sep=";",header=None,usecols=[0],
                               names=["utc"],dtype={"utc":"string"})["utc"]
            utc=pd.to_datetime(ts,format="%Y%m%d %H%M%S",utc=True)
            local=utc.dt.tz_convert("America/New_York")
            mins=local.dt.hour*60+local.dt.minute
            keep=mins.between(571,960)
            d=local[keep].dt.strftime("%Y-%m-%d")
            t=pd.DataFrame({"day":d.to_numpy(),"minute":mins[keep].to_numpy()})
            for day,rows in t.groupby("day"):
                meta=validate_member(name,day)
                if not meta["selected"]:
                    continue
                minutes=np.sort(rows["minute"].to_numpy())
                if not np.array_equal(minutes,np.arange(571,961)):
                    partial+=1
                    continue
                if day in found:
                    raise ValueError("Ambiguous double-source NQ RTH session")
                found[day]=meta["source_contract"]
    dates,bars,source=load_years(path,IST)
    if set(dates)!=set(found):
        raise ValueError("CSV file origin dates do not match existing OHLC loader")
    metadata=metadata_for_sessions(dates,bars)
    for m in metadata:
        if m.contract_id!=found[m.session_date]:
            raise ValueError("Contract identifier inconsistent with concrete source file")
    rollover_indexes=[i for i in range(1,len(metadata))
        if metadata[i].contract_id!=metadata[i-1].contract_id]
    tested=0
    for i in sorted(set([0,len(dates)//2,len(dates)-1]+rollover_indexes)):
        ctx=prior_same_contract(dates,bars,i)
        if i in rollover_indexes and len(ctx["prior_bars"])!=0:
            raise ValueError("History crosses unadjusted NQ expiry")
        tested+=1
    if source["years_opened"]!=list(IST) or source["holdout_2025_opened"] or source["holdout_2026_opened"]:
        raise PermissionError("Loader accessed prohibited years")
    return {"status":"NQ_IST_ACTUAL_MEMBER_PROVENANCE_QA_NO_PNL",
        "accepted_sessions":len(found),"loader_sessions":len(dates),
        "partial_member_sessions":partial,
        "roll_boundaries":len(rollover_indexes),"real_warmup_contexts_checked":tested,
        "source_contracts":len(set(found.values())),
        "years_opened":list(IST),"holdouts":"SEALED",
        "file_origin_contract_verified":True,
        "independent_exchange_roll_verified":False,
        "economic_backtests":0,"strategy_signals_evaluated":0,
        "price_data_exported":False,"pnl_exported":False}
