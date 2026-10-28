"""S0.19 50K MFFU plan-specific evaluation parameters (configuration only).

2026-09-24 official plan matrix:
https://help.myfundedfutures.com/en/articles/11802636-traders-evaluation-simplified
Builder details:
https://help.myfundedfutures.com/en/articles/14290805-builder-plan-50k-a-comprehensive-guide

Never silently infer the user's purchased plan. These profiles do NOT claim
that an execution engine honors the broker's real-time mark/fill or all terms.
No historical prices, orders, or PnL are accessed or produced.
"""
from __future__ import annotations
from dataclasses import dataclass

SOURCE_DATE="2026-09-24"
SOURCE_URL="https://help.myfundedfutures.com/en/articles/11802636-traders-evaluation-simplified"
STATUS="OFFICIAL_EVALUATION_PARAMETERS_UNCONFIRMED_ACCOUNT_NO_REAL_EXECUTION"


@dataclass(frozen=True)
class EvaluationPlan:
    name:str
    starting_balance_usd:int
    profit_target_usd:int
    max_loss_limit_eod_usd:int
    daily_soft_pause_usd:int|None
    max_minis:int
    min_trading_days:int
    consistency_fraction:float|None
    drawdown_type:str="EOD_TRAILING"


PLANS={
    "BUILDER_50K_DEFAULT":EvaluationPlan(
        "BUILDER_50K_DEFAULT",50000,3000,2000,1000,4,1,None),
    "BUILDER_50K_ADDON_1500":EvaluationPlan(
        "BUILDER_50K_ADDON_1500",50000,3000,1500,1000,4,1,None),
    "RAPID_INTRADAY_50K":EvaluationPlan(
        "RAPID_INTRADAY_50K",50000,3000,2000,None,5,2,.50),
    "RAPID_EOD_50K":EvaluationPlan(
        "RAPID_EOD_50K",50000,3000,2000,None,3,4,.30),
    "PRO_50K_DEFAULT":EvaluationPlan(
        "PRO_50K_DEFAULT",50000,3000,2000,None,3,2,.50),
}


def require_specific_plan(name:str|None,stage:str="EVALUATION")->EvaluationPlan:
    if stage!="EVALUATION":
        raise PermissionError("Funded/live stage has different balances/payout rules")
    if type(name) is not str or name not in PLANS:
        raise PermissionError("Exact purchased MFFU 50K plan must be verified")
    return PLANS[name]


def technical_preflight(name:str|None,contracts:int,stage:str="EVALUATION")->dict:
    plan=require_specific_plan(name,stage)
    if type(contracts) is not int or not 1<=contracts<=plan.max_minis:
        raise ValueError("NQ contract count violates selected official plan")
    # This is a CONFIG check only, not a release to the financial backtester.
    return {"status":STATUS, "source_url":SOURCE_URL,"source_date":SOURCE_DATE,
        "name":plan.name,"contracts":contracts,
        "evaluation_target_usd":plan.profit_target_usd,
        "eod_maximum_loss_usd":plan.max_loss_limit_eod_usd,
        "daily_soft_pause_usd":plan.daily_soft_pause_usd,
        "consistency_limit":plan.consistency_fraction,
        "funded_rules_validated":False,
        "intraday_floating_engine_certified":False,
        "market_data_opened":False,"economic_execution_authorized":False}
