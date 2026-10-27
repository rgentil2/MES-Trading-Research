#!/usr/bin/env python3
"""NQ funded evaluation account risk arithmetic: synthetic policy test ONLY.

PRELIMINARY profile: MFFU Builder 50K evaluation, NOT a declaration of
the user's actual plan or a cleared economic run. Source (2026-10):
https://help.myfundedfutures.com/en/articles/14290805-builder-plan-50k-a-comprehensive-guide
https://help.myfundedfutures.com/en/articles/8348565-end-of-day-eod-drawdown-explained

EOD trailing floor only updates after day close; hard breach is checked using
intraday floating equity as conservative policy, soft pause at -$1000 from
start-day balance. Extra internal closed-pnl pause -$600 remains separate
from official DLL and is not represented by this equity-only module.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class AccountProfile:
    plan: str = "BUILDER_EVAL_50K_REFERENCE_ONLY"
    initial_balance: float = 50000.
    max_eod_loss: float = 2000.
    soft_daily_loss: float = 1000.
    profit_target: float = 3000.
    eod_floor_lock_above_start: float = 100.
    contracts: int = 1
    instrument: str = "NQ"
    verified_user_plan: bool = False

    def check(self):
        if (self.plan!="BUILDER_EVAL_50K_REFERENCE_ONLY" or
                self.initial_balance!=50000. or self.max_eod_loss!=2000. or
                self.soft_daily_loss!=1000. or self.profit_target!=3000. or
                self.eod_floor_lock_above_start!=100. or
                self.contracts!=1 or self.instrument!="NQ" or self.verified_user_plan):
            raise ValueError("Only unverified Builder 50K NQ research scenario permitted")


def synthetic_account_path(days:list[dict], profile:AccountProfile|None=None)->dict:
    """Test relative account PnL snapshots, NOT historical strategy outcomes.

    Each day contains date and path = [{equity,closed_balance},...], with
    opening/closing equity equal to closed balance for this no-overnight test.
    The profile is NOT an execution-ready official account certification.
    """
    p=profile or AccountProfile()
    p.check()
    high_eod=p.initial_balance
    hard_floor=p.initial_balance-p.max_eod_loss
    prev_end=p.initial_balance
    records=[]
    stopped=False
    prior_day=None
    for day in days:
        dt=day["date"]
        if prior_day is not None and dt<=prior_day:
            raise ValueError("Day order and unique calendar dates required")
        prior_day=dt
        from datetime import date
        try:
            parsed=date.fromisoformat(dt)
        except (ValueError,TypeError):
            raise ValueError("Use ISO dates") from None
        if parsed.year not in (2020,2021,2022):
            raise PermissionError("Only synthetic IST 2020-22 dates")
        points=day["path"]
        if not points:
            raise ValueError("Intraday equity checkpoints required")
        opened=points[0]
        if (opened["equity"]!=prev_end or
                opened["closed_balance"]!=prev_end):
            raise ValueError("No overnight exposures or account balance discontinuity")
        soft_floor=prev_end-p.soft_daily_loss
        soft_paused=False
        hard_breached=False
        for point in points:
            equity=float(point["equity"])
            balance=float(point["closed_balance"])
            if not isfinite(equity) or not isfinite(balance):
                raise ValueError("Finite marked equity and closed balance required")
            if equity<=hard_floor:
                hard_breached=True
            if equity<=soft_floor:
                soft_paused=True
        last=points[-1]
        if float(last["equity"])!=float(last["closed_balance"]):
            raise ValueError("Close-of-day flat is mandatory")
        prev_end=float(last["closed_balance"])
        if not hard_breached:
            # Trailing advances on new EOD balance peaks, never intraday peaks.
            high_eod=max(high_eod,prev_end)
            next_floor=min(p.initial_balance+p.eod_floor_lock_above_start,
                           high_eod-p.max_eod_loss)
            hard_floor=max(hard_floor,next_floor)
        records.append({"date":dt,"eod_closed_balance":prev_end,
                        "hard_floor_after_close":hard_floor,
                        "soft_pause_touched":soft_paused,
                        "hard_breach_touched":hard_breached,
                        "end_day_profit_target_reached":prev_end>=p.initial_balance+p.profit_target})
        if hard_breached:
            stopped=True
            break
    return {"status":"SYNTHETIC_UNVERIFIED_PLAN_NO_MARKET_DATA",
            "model":"BUILDER_50K_EOD_TRAILING_RESEARCH_REFERENCE",
            "date_rows":records,
            "hard_breach":stopped,
            "official_daily_loss_usd":p.soft_daily_loss,
            "internal_closed_pnl_pause_usd":-600.,
            "no_mnq":True,
            "plan_identity_confirmed":False,
            "holdouts":"SEALED"}
