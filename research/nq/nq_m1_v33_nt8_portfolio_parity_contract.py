#!/usr/bin/env python3
"""S0.28: deterministic, STRICT comparison contract for a FUTURE NinjaTrader 8
portfolio Strategy Analyzer backtest vs Python M1 shared-account execution.

CURRENT SCOPE: artificial CSV and manifest QA ONLY. NO winning portfolio exists.
This validator NEVER runs NinjaTrader, reads IST archives, selects a strategy,
authorizes a holdout, releases a funded account or certifies broker fill parity.

Future genuine comparisons require separate approved release and *frozen*
winner/engine/source/NinjaScript identifiers. NT8 Standard fill simulation and
Python's stop-first conservative OHLC policy are NOT equivalent algorithms:
compare and flag disagreements, never change rules to force a pass.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, date, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse
import csv
import hashlib
import json
import math
import re

from research.nq.nq_h05_h07_level_volume_screen import roll_contract
from research.nq.nq_m1_v22_quality_gate import audit

STATUS="S0_28_SYNTHETIC_NT8_PORTFOLIO_PARITY_CONTRACT_NO_WINNER_NO_IST"
SCHEMA="NQ_NT8_PYTHON_FROZEN_PORTFOLIO_PARITY_V1"
ROOT="NQ_M1_2020_2022_IST"
SOURCE_SHA256="a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8"
HEADERS=(
    "session","portfolio_sequence","strategy_id","contract","side",
    "quantity","signal_time_utc","entry_time_utc","exit_time_utc",
    "entry_price","exit_price","commission_usd","net_usd","exit_reason"
)
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
STRATEGY_RE=re.compile(r"^NQ26_[0-9a-f]{16}$")
TIME_FMT="%Y-%m-%dT%H:%M:%SZ"
NY=ZoneInfo("America/New_York")
TICK=.25
POINT_USD=20.
# This is a synthetic protocol setting, NOT the official account risk limits.
MAX_MISMATCH_SAMPLES=20
EXPECTED_SETTINGS={
    "platform":"NinjaTrader 8 Strategy Analyzer",
    "instrument":"NQ",
    "primary_interval":"1 Minute",
    "primary_price_type":"Last",
    "order_fill_resolution":"Standard",
    "fill_limit_orders_on_touch":False,
    "calculate":"OnBarClose",
    "trading_hours":"CME US Index Futures RTH equivalent 09:30-16:00 NY",
    "session_timezone":"America/New_York",
    "session_bar_labels":"END_OF_MINUTE",
    "signal_window":["09:35","11:28"],
    "forced_flat_time":"11:29",
    "positions_shared":True,
    "max_aggregate_nq_contracts":1,
    "no_overnight":True,
    "no_strategy_optimization_during_parity":True,
    "multi_strategy_joint_scheduler":True,
    "account_rules_exact_profile_confirmed":False,
}
COMPARE_FIELDS=("strategy_id","contract","side","quantity",
                "signal_time_utc","entry_time_utc","exit_time_utc",
                "entry_price","exit_price","commission_usd","net_usd",
                "exit_reason")
FIELD_GROUP={
    "strategy_id":"SIGNAL_OR_PORTFOLIO_SCHEDULER",
    "side":"SIGNAL_OR_PORTFOLIO_SCHEDULER",
    "signal_time_utc":"SIGNAL_CLOCK",
    "contract":"DATA_ROLLOVER",
    "quantity":"SHARED_ACCOUNT_SIZING",
    "entry_time_utc":"ENTRY_FILL_TIMING",
    "entry_price":"ENTRY_FILL_PRICE",
    "exit_time_utc":"EXIT_FILL_TIMING",
    "exit_price":"EXIT_FILL_PRICE",
    "commission_usd":"COSTS",
    "net_usd":"PNL_ARITHMETIC_OR_COSTS",
    "exit_reason":"EXIT_LOGIC",
}

def _sha(text):
    return hashlib.sha256(text.encode("utf8")).hexdigest()

def _sha_valid(value):
    return type(value) is str and bool(SHA_RE.fullmatch(value))

def _f(x,field):
    try: v=float(x)
    except (ValueError,TypeError):raise ValueError("Invalid "+field) from None
    if not math.isfinite(v):raise ValueError("Nonfinite "+field)
    return v

def _utc(s):
    if type(s) is not str:
        raise ValueError("Timestamp not ISO UTC")
    try: parsed=datetime.strptime(s,TIME_FMT).replace(tzinfo=timezone.utc)
    except (ValueError,TypeError):raise ValueError("Timestamp requires YYYY-MM-DDTHH:MM:SSZ") from None
    if parsed.strftime(TIME_FMT)!=s:raise ValueError("Noncanonical UTC time")
    return parsed

def _from_source_file(file):
    with Path(file).open("r",newline="",encoding="utf8-sig") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=list(HEADERS):
            raise ValueError("Require identical canonical CSV headers, no vendor positional guess")
        result=list(reader)
    if len(result)>100000:
        raise ValueError("Trade list size exceeds parser budget")
    if any(None in r or None in r.values() for r in result):
        raise ValueError("CSV missing value or unexpected columns")
    return result

def _strict_ist_only():
    g=audit()
    if (g["checks_total"]!=13 or g["passed_verified"]!=0
        or g["decision"]!="EXECUTION_BLOCKED" or g["ready_for_economic_execution"]):
        raise PermissionError("S0.28 synthetic checker cannot execute under changed 13-gate state")

def validate_manifest(m,side):
    _strict_ist_only()
    if not isinstance(m,dict):
        raise ValueError("Manifest must be a JSON object")
    necessary={"schema","evidence_mode","engine","stage","source_zip_sha256",
               "portfolio_sha256","strategy_ast_bundle_sha256","engine_code_sha256",
               "ninjatrader_ninjascript_sha256","shared_portfolio_scheduler_sha256",
               "settings","portfolio_frozen","isv1_2023_opened","isv2_2024_opened",
               "sealed_2025_2026_opened","historical_backtest_authorized"}
    if set(m)!=necessary:
        raise ValueError("Manifest missing or unknown keys")
    if (m["schema"]!=SCHEMA or m["engine"]!=side or
        m["evidence_mode"]!="ARTIFICIAL_PARITY_FIXTURE_ONLY" or
        m["stage"]!=ROOT or m["source_zip_sha256"]!=SOURCE_SHA256 or
        m["portfolio_frozen"] is not False or
        m["historical_backtest_authorized"] is not False or
        m["isv1_2023_opened"] is not False or
        m["isv2_2024_opened"] is not False or
        m["sealed_2025_2026_opened"] is not False):
        raise PermissionError("No winner, real backtest or reserved year can be asserted in S0.28")
    for key in ("portfolio_sha256","strategy_ast_bundle_sha256",
                "engine_code_sha256","ninjatrader_ninjascript_sha256",
                "shared_portfolio_scheduler_sha256"):
        if not _sha_valid(m[key]):
            raise ValueError("Invalid SHA fingerprint "+key)
    if m["settings"]!=EXPECTED_SETTINGS:
        raise ValueError("Nonidentical NT8 frozen settings or account assumptions")
    return m

def _manifest_pair(a,b):
    validate_manifest(a,"PYTHON")
    validate_manifest(b,"NINJATRADER_8")
    for key in ("schema","stage","source_zip_sha256","portfolio_sha256",
                "strategy_ast_bundle_sha256",
                "shared_portfolio_scheduler_sha256","settings"):
        if a[key]!=b[key]:
            raise ValueError("Paired manifests differ in "+key)
    # Engine binary and NinjaScript SHA are each independently pinned in both.
    if a["engine_code_sha256"]!=b["engine_code_sha256"]:
        raise ValueError("Python engine SHA not equal across manifests")
    if a["ninjatrader_ninjascript_sha256"]!=b["ninjatrader_ninjascript_sha256"]:
        raise ValueError("NinjaScript SHA not equal across manifests")

def _parse(rows):
    records={}
    for n,r in enumerate(rows,1):
        if set(r)!=set(HEADERS):raise ValueError("Unrecognized columns")
        session=r["session"]
        try:
            d=date.fromisoformat(session)
        except (TypeError,ValueError):raise ValueError("Bad session date") from None
        if (type(session) is not str or d.isoformat()!=session
            or d.year not in (2020,2021,2022)):
            raise PermissionError("2023+ dates cannot be processed in IST synthetic parity")
        k=r["portfolio_sequence"]
        try: seq=int(k)
        except (ValueError,TypeError):raise ValueError("Bad portfolio sequence") from None
        if str(seq)!=k or seq<=0:raise ValueError("Sequence must be positive integer")
        key=(session,seq)
        if key in records:raise ValueError("Duplicate shared portfolio sequence")
        if not STRATEGY_RE.fullmatch(r["strategy_id"]):
            raise ValueError("Require exact frozen strategy ID pattern")
        if r["contract"]!=roll_contract(d):
            raise ValueError("Contract inconsistent with frozen quarterly roll map")
        if r["side"] not in ("LONG","SHORT") or r["quantity"]!="1":
            raise ValueError("One NQ only, LONG or SHORT; no simultaneous holdings")
        for field in ("entry_price","exit_price","commission_usd","net_usd"):
            r[field]=_f(r[field],field)
        if (r["entry_price"]<=0 or r["exit_price"]<=0 or r["commission_usd"]<0 or
            any(abs(r[f]/TICK-round(r[f]/TICK))>1e-8 for f in ("entry_price","exit_price"))):
            raise ValueError("NQ tick grid, positive prices and nonnegative commission required")
        signal=_utc(r["signal_time_utc"]);entry=_utc(r["entry_time_utc"]);exit_=_utc(r["exit_time_utc"])
        if not signal<entry<=exit_:
            raise ValueError("Noncausal entry/exit times")
        local_sig=signal.astimezone(NY)
        local_entry=entry.astimezone(NY)
        local_exit=exit_.astimezone(NY)
        if any(t.date()!=d for t in (local_sig,local_entry,local_exit)):
            raise ValueError("Local session date differs from UTC/NQ NY clock")
        if (not time(9,35)<=local_sig.time()<=time(11,28)
            or not time(9,36)<=local_entry.time()<=time(11,29)
            or not time(9,36)<=local_exit.time()<=time(11,29)):
            raise ValueError("Clock outside 09:35 signal to 11:29 flat")
        side=1 if r["side"]=="LONG" else -1
        net=side*(r["exit_price"]-r["entry_price"])*POINT_USD-r["commission_usd"]
        if abs(net-r["net_usd"])>.011:
            raise ValueError("Net PnL arithmetic inconsistent with one NQ and commission")
        if not r["exit_reason"] or len(r["exit_reason"])>80:
            raise ValueError("Exit reason required")
        records[key]=r
    for day in set(d for d,_ in records):
        found=[(seq,records[(d,seq)]) for d,seq in records if d==day]
        found.sort()
        if [s for s,_ in found]!=list(range(1,len(found)+1)):
            raise ValueError("Daily portfolio sequence gaps")
        if len(found)>2:
            raise ValueError("More than 2 NQ entries in one day")
        for (a,x),(b,y) in zip(found,found[1:]):
            if _utc(y["entry_time_utc"])<=_utc(x["exit_time_utc"]):
                raise ValueError("Portfolio overlap or same-minute reentry")
    return records

def _summary(trades):
    net=[r["net_usd"] for r in trades.values()]
    profit=sum(z for z in net if z>0)
    loss=-sum(z for z in net if z<0)
    bal=peak=drawdown=0.
    for key in sorted(trades):
        bal+=trades[key]["net_usd"]
        peak=max(peak,bal)
        drawdown=max(drawdown,peak-bal)
    return {"trades":len(net),"net_usd":round(sum(net),2),
            "gross_profit":round(profit,2),"gross_loss":round(loss,2),
            "pf":round(profit/loss,6) if loss>0 else None,
            "closed_trade_max_drawdown_usd":round(drawdown,2)}
def compare(py_rows,nt_rows,py_manifest,nt_manifest):
    """Compare only two separately supplied *artificial* engine CSV exports."""
    _manifest_pair(py_manifest,nt_manifest)
    py=_parse(py_rows);nt=_parse(nt_rows)
    keys=sorted(set(py)|set(nt))
    mismatches=Counter();examples=[]
    missing_py=missing_nt=0
    for key in keys:
        if key not in py:
            missing_py+=1;mismatches["MISSING_IN_PYTHON"]+=1
            if len(examples)<MAX_MISMATCH_SAMPLES:
                examples.append({"key":list(key),"type":"MISSING_IN_PYTHON"})
            continue
        if key not in nt:
            missing_nt+=1;mismatches["MISSING_IN_NINJATRADER"]+=1
            if len(examples)<MAX_MISMATCH_SAMPLES:
                examples.append({"key":list(key),"type":"MISSING_IN_NINJATRADER"})
            continue
        for col in COMPARE_FIELDS:
            a,b=py[key][col],nt[key][col]
            equal=(abs(a-b)<.011 if col in ("net_usd","commission_usd")
                   else abs(a-b)<1e-9 if col in ("entry_price","exit_price")
                   else a==b)
            if not equal:
                category=FIELD_GROUP[col]
                mismatches[category]+=1
                if len(examples)<MAX_MISMATCH_SAMPLES:
                    examples.append({"key":list(key),"field":col,
                                     "category":category,"python":a,"ninjatrader":b})
    # No evidence can be derived from matching two empty trade files.
    pass_synthetic=not mismatches and len(py)>0 and len(nt)>0
    return {
        "schema":"NQ_M1_NT8_PYTHON_PARITY_COMPARISON_SYNTHETIC_ONLY_V1",
        "status":STATUS,
        "verdict":("PASS_SYNTHETIC_FORMAT_AND_VALUES_ONLY" if pass_synthetic else
                   "INCONCLUSIVE_NO_TRADES" if not py and not nt else
                   "FAIL_DIFFERENCES_REQUIRE_INVESTIGATION"),
        "python":_summary(py),"ninjatrader":_summary(nt),
        "shared_trade_keys":len(set(py)&set(nt)),
        "missing_in_python":missing_py,"missing_in_ninjatrader":missing_nt,
        "mismatch_categories":dict(sorted(mismatches.items())),
        "mismatch_examples_at_most_20":examples,
        "real_ninjatrader_strategy_analyzer_run_verified":False,
        "real_winner_portfolio_exists":False,
        "real_IST_historical_backtest_executed":False,
        "formal_funnel_or_parity_approval":False,
        "holdouts":"2023_2024_2025_2026_UNOPENED",
        "note":"A matching synthetic CSV pair does NOT guarantee same historical fills, broker parity, risk limits or funding readiness."
    }

def _read_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf8"))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--python-csv",type=Path,required=True)
    p.add_argument("--ninjatrader-csv",type=Path,required=True)
    p.add_argument("--python-manifest",type=Path,required=True)
    p.add_argument("--ninjatrader-manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=compare(_from_source_file(args.python_csv),
                   _from_source_file(args.ninjatrader_csv),
                   _read_manifest(args.python_manifest),
                   _read_manifest(args.ninjatrader_manifest))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({k:report[k] for k in
        ("verdict","shared_trade_keys","mismatch_categories","real_winner_portfolio_exists")},
        sort_keys=True))

if __name__=="__main__":
    main()
