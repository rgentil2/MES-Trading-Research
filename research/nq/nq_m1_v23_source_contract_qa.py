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
