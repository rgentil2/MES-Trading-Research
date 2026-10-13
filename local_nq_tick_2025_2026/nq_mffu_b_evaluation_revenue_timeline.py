#!/usr/bin/env python3
"""One-pass private 7m DEV route-B revenue timeline; export month aggregates only."""
from __future__ import annotations
import argparse,json
from decimal import Decimal
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_top2_mffu_eod_float_replay import STAGE,aggregate,portfolio_metrics

B="B_T05_T186_T215"
PASS_INDEX=35
def money(x):return Decimal(str(x)).quantize(Decimal("0.01"))

def stage_monthly(rows, n):
    if not 0<n<len(rows):raise ValueError("BAD_PASS_INDEX")
    groups={m:{"month":m,"eval_net":Decimal("0"),"eval_trades":0,
               "eval_trade_days":0,"funded_net":Decimal("0"),
               "funded_trades":0,"funded_trade_days":0} for m in MONTHS}
    for i,row in enumerate(rows):
        mon=row["day"][:7]
        if mon not in groups:raise AssertionError("OUTSIDE_DEV")
        ts=row["fee_router"][B]
        phase="eval" if i<n else "funded"
        z=groups[mon]
        z[phase+"_net"]+=sum((money(x["net_mffu"]) for x in ts),Decimal("0"))
        z[phase+"_trades"]+=len(ts)
        z[phase+"_trade_days"]+=int(bool(ts))
    out=[];e=f=Decimal("0")
    for month in MONTHS:
        z=groups[month];e+=z["eval_net"];f+=z["funded_net"]
        out.append({"month":month,"eval_net_usd":float(z["eval_net"]),
                    "eval_cumulative_usd":float(e),
                    "eval_trades":z["eval_trades"],"eval_trade_days":z["eval_trade_days"],
                    "funded_net_usd":float(z["funded_net"]),
                    "funded_cumulative_usd":float(f),
                    "funded_trades":z["funded_trades"],"funded_trade_days":z["funded_trade_days"],
                    "research_no_reset_cumulative_usd":float(e+f)})
    return out

def analyze(months):
    z=aggregate(months)  # strict original parity of 140/135 and 172 MFFU trades
    r=z["results"][B]
    stage=r["replay_mffu_fee_router"]
    evalz=stage["evaluation"]
    fundedz=stage["post_eval_funded_fresh_zero"]
    if (evalz["first_eval_target_and_consistency_session_index"]!=PASS_INDEX
        or evalz["trades_processed_before_stop"]!=40
        or evalz["trading_days_processed"]!=27
        or money(evalz["current_balance_if_no_bound_failure"])!=money("3152.61")
        or fundedz is None
        or fundedz["trades_processed_before_stop"]!=132
        or fundedz["trading_days_processed"]!=81
        or money(fundedz["current_balance_if_no_bound_failure"])!=money("4899.74")):
        raise AssertionError("ORIGINAL_EVAL_FUNDED_35TH_SESSION_PARITY_FAILED")
    rows=[]
    for mon in MONTHS:
        x=months[mon]
        if x["stage"]!=STAGE or x["ready"]!=len(x["days"]):
            raise AssertionError("INVALID_PRIVATE_DEV_MONTH")
        rows.extend(x["days"])
    if len(rows)!=135 or [r["day"] for r in rows]!=sorted(r["day"] for r in rows):
        raise AssertionError("135_DEV_DAYS_REQUIRED")
    ev=portfolio_metrics(rows[:PASS_INDEX],B,"fee_router")
    fu=portfolio_metrics(rows[PASS_INDEX:],B,"fee_router")
    full=r["mffu_fee_aware_daily_stop_rerouter"]
    timeline=stage_monthly(rows,PASS_INDEX)
    if (ev["N"]!=40 or fu["N"]!=132
        or money(ev["net_mffu"])!=money("3152.61")
        or money(fu["net_mffu"])!=money("4899.74")
        or money(full["DD_closed_eod"])!=money("1152.12")
        or money(full["DD_last_adverse_upper_bound"])!=money("1711.80")
        or money(timeline[-1]["research_no_reset_cumulative_usd"])!=money("8052.35")
        or sum(m["eval_trade_days"] for m in timeline)!=27
        or sum(m["funded_trade_days"] for m in timeline)!=81):
        raise AssertionError("STAGE_PARTITION_OR_MONTHLY_RECONCILIATION_FAILED")
    return {
      "stage":"MFFU_B_50K_EVAL_ONLY_DD_AND_MONTHLY_TIMELINE_DEV_LAST",
      "months":list(MONTHS),"sessions_source":140,"sessions_ready":135,
      "evaluation_cutoff_ready_session":PASS_INDEX,
      "evaluation_cutoff_calendar_month_et":rows[PASS_INDEX-1]["day"][:7],
      "eval_trade_days":27,"eval_trades":40,"eval_net_usd":3152.61,
      "eval_closed_eod_max_dd_usd":ev["DD_closed_eod"],
      "eval_last_adverse_max_dd_bound_usd":ev["DD_last_adverse_upper_bound"],
      "eval_worst_intraday_vs_day_open_usd":ev["worst_intraday_vs_day_open"],
      "eval_min_room_above_firm_floor_usd":evalz["min_open_equity_distance_from_floor_bound_usd"],
      "funded_trades":132,"funded_net_usd":4899.74,
      "funded_closed_eod_max_dd_usd":fu["DD_closed_eod"],
      "funded_last_adverse_max_dd_bound_usd":fu["DD_last_adverse_upper_bound"],
      "research_full_without_reset_net_usd":full["net_mffu"],
      "research_full_without_reset_closed_eod_max_dd_usd":full["DD_closed_eod"],
      "research_full_without_reset_last_adverse_max_dd_bound_usd":full["DD_last_adverse_upper_bound"],
      "monthly":timeline,
      "holdouts_opened":False,"licensed_trade_rows_exported":False,
      "broker_fills_verified":False,"real_funding_revenue":False,
    }

def report(z):
    s=["# Cartera B T05 + T186 + T215 — MFFU 50K línea de tiempo hipotética",
       "",
       "Desarrollo único Last oct2025–abr2026; no OOS ni fills del broker.",
       "Evaluación: primera aprobación simulada en 35ª sesión elegible, mes ET "+
       z["evaluation_cutoff_calendar_month_et"]+", 40 trades, US$ 3.152,61.",
       "",
       "**Drawdown SOLO fase evaluación:** cerrado EOD **US$ "+
       f'{z["eval_closed_eod_max_dd_usd"]:,.2f}'+"**, cota Last adversa **US$ "+
       f'{z["eval_last_adverse_max_dd_bound_usd"]:,.2f}'+"**.",
       "Distancia mínima al piso móvil MFFU durante evaluación, NO es DD: US$ "+
       f'{z["eval_min_room_above_firm_floor_usd"]:,.2f}'+".",
       "",
       "| Mes (ET) | Eval: P&L mes | Eval: saldo acumulado | Ops eval | Funded: P&L mes | Funded: saldo acumulado | Ops funded | Histórico sin reset |",
       "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for x in z["monthly"]:
        s.append("| "+x["month"]+" | "+
            f'US$ {x["eval_net_usd"]:,.2f} | US$ {x["eval_cumulative_usd"]:,.2f} | {x["eval_trades"]} | '+
            f'US$ {x["funded_net_usd"]:,.2f} | US$ {x["funded_cumulative_usd"]:,.2f} | '+
            f'{x["funded_trades"]} | US$ {x["research_no_reset_cumulative_usd"]:,.2f} |')
    s.extend(["",
       "Funded comienza de US$ 0 tras aprobar evaluación, nunca de US$ 3152,61; "
       "los beneficios de la evaluación NO son retirables.",
       "",
       f'Drawdown fundado EOD US$ {z["funded_closed_eod_max_dd_usd"]:,.2f}; '+
       f'cota adversa Last US$ {z["funded_last_adverse_max_dd_bound_usd"]:,.2f}.',
       "El histórico completo sin reset NO corresponde a una única cuenta fondeada: "
       f'US$ {z["research_full_without_reset_net_usd"]:,.2f}, '+
       f'DD cerrado US$ {z["research_full_without_reset_closed_eod_max_dd_usd"]:,.2f}, '+
       f'cota Last adversa US$ {z["research_full_without_reset_last_adverse_max_dd_bound_usd"]:,.2f}.',
       "",
       "Cotas basadas solo en grupos atómicos Last, no fills reales, bid/ask o "
       "ejecución garantizada; sensibilidad a noticia/gaps pendiente.",
       "No se abrió holdout ni se exportaron precios, trades diarios o timestamps privados."])
    return "\n".join(s)+"\n"

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--inputs",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    x={m:json.loads((a.inputs/f"mffu_top2_{m}.json").read_text()) for m in MONTHS}
    z=analyze(x)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+"\n")
    a.report.write_text(report(z))
    print("MFFU_B_SAFE_EVAL_RISK="+json.dumps({
      "eval_closed_dd":z["eval_closed_eod_max_dd_usd"],
      "eval_last_bound_dd":z["eval_last_adverse_max_dd_bound_usd"],
      "eval_cutoff_month":z["evaluation_cutoff_calendar_month_et"],
      "funded_closed_dd":z["funded_closed_eod_max_dd_usd"],
      "holdouts_opened":False,
    },sort_keys=True))
