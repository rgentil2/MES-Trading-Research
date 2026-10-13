#!/usr/bin/env python3
"""Compare H09/H56/H69/H74/H77 as alternative single-MNQ-proxy policies.

Existing public aggregate frozen reports only. No new H market files; NO
cross-calendar H+T equity and no duplicate parent/router stacking.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
H=("H09","H56","H69","H74","H77")
BASE=ROOT/"results/nq_h67_h72/NQ_H67_H72_REPORT_2020_2024.json"
ROUTER=ROOT/"results/nq_h73_h78/NQ_H73_H78_REPORT_2020_2024.json"
FROZEN={
 "H09":(173,2074.26,763.56),
 "H56":(100,749.50,365.52),
 "H69":(262,2704.44,890.64),
 "H74":(132,1657.84,444.10),
 "H77":(140,2385.30,584.54),
}

def evaluate(base=BASE,router=ROUTER):
    b=json.loads(Path(base).read_text())
    r=json.loads(Path(router).read_text())
    for j in (b,r):
        if (j["holdout_2025_loaded"] is not False
            or j["holdout_2026_loaded"] is not False
            or list(j["loaded_years"])!=[2020,2021,2022,2023,2024]):
            raise ValueError("H_HOLDOUT_OR_CALENDAR_SEAL_BROKEN")
    report={}
    source={
        "H09":b["comparators"]["NQ-H09"],
        "H56":b["comparators"]["NQ-H56"],
        "H69":r["baseline_H69"],
        "H74":r["hypotheses"]["NQ-H74"],
        "H77":r["hypotheses"]["NQ-H77"],
    }
    for k in H:
        z=source[k]
        n,net,dd=FROZEN[k]
        if (z["n"]!=n or abs(z["net_usd"]-net)>.01
            or abs(z["closed_dd_usd"]-dd)>.01):
            raise AssertionError("H_SAME_MNQ_PROXY_PARENT_PARITY_"+k)
        report[k]={
            "N":n,"net_mnq_proxy_usd":net,"DD_closed_usd":dd,
            "net_per_trade_usd":round(net/n,3),
            "net_DD_closed":round(net/dd,4),
            "PF":z.get("pf"),"cost_1p5_usd":
                z.get("cost_1_5x_total_net_usd",z.get("stress_1_5x_costs_net_usd")),
            "positive_years":z.get("positive_years"),
            "q_BH_prior_family":z.get("bh_q6"),
            "base_2020_2024_all_reused_DEV":True,
            "contract":"1_MNQ_PROXY_ON_NQ_1MIN_OHLC"
        }
    pareto=[]
    for k in H:
        v=report[k]
        dominated_by=[
            other for other,z in report.items() if other!=k and
             z["net_mnq_proxy_usd"]>=v["net_mnq_proxy_usd"] and
             z["DD_closed_usd"]<=v["DD_closed_usd"] and
             (z["net_mnq_proxy_usd"]>v["net_mnq_proxy_usd"] or
              z["DD_closed_usd"]<v["DD_closed_usd"])
        ]
        report[k]["dominated_by"]=dominated_by
        report[k]["Pareto"]=not dominated_by
        if not dominated_by:pareto.append(k)
    return {
        "stage":"ALL13_H_FIVE_ALTERNATIVES_SAME_MNQ_PROXY_REUSE_ONLY",
        "H_five":report,"Pareto_H_options":pareto,
        "best_historical_net_DD":"H77",
        "confirmed_H_strategy":None,
        "duplicate_H_router_parent_stacks_prohibited":True,
        "H_T_total_net":None,
        "H_T_combined_DD":None,
        "H_OOS_2025_2026_opened":False,
        "risk_floating_and_broker_fills_verified":False,
    }

def report(z):
    lines=[
        "# Rama H de las 13 — cinco decisiones alternativas comparables en MNQ proxy",
        "",
        "Solo resultados públicos congelados H 2020–24. Se conservan los cinco IDs.",
        "**NO cinco operaciones aditivas**: H69/H74/H77 ya rutean H09 y H56.",
        "",
        "| H | N | Neto MNQ proxy USD | DD cerrado USD | Neto/DD | USD/trade | PF | Estado Pareto |",
        "|---|---:|---:|---:|---:|---:|---:|---|"
    ]
    for name,v in z["H_five"].items():
        lines.append(f"| {name} | {v['N']} | {v['net_mnq_proxy_usd']:,.2f} | "
                     f"{v['DD_closed_usd']:,.2f} | {v['net_DD_closed']:.4f} | "
                     f"{v['net_per_trade_usd']:.2f} | {v['PF'] if v['PF'] is not None else 'N/D'} | "
                     f"{'NO DOMINADA' if v['Pareto'] else 'DOMINADA por '+','.join(v['dominated_by'])} |")
    lines.extend([
        "",
        "**H77 lidera Neto/DD HISTÓRICO** entre las opciones compatibles, pero N140",
        "y un 75,2% de su neto procede de 2022. H74 N132 y q0,1149. H69 N262 y",
        "qBH0,1152; ninguno pasa toda la validación estadística/OOS.",
        "H09 de esta tabla es su **comparador 1MNQ**, no el H09 standalone",
        "1NQ de un bracket diferente. No mezclar los dos importes.",
        "Sin Bid/Ask MNQ negociable ni equity flotante; ninguna recomendación",
        "de fondeo o mejor portafolio H+T queda demostrada. H 2025/26 sellado.",
        ""
    ])
    return "\n".join(lines)+"\n"

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    z=evaluate()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+"\n")
    a.report.write_text(report(z))
    print("NQ_ALL13_H5_SAFE="+json.dumps({
        "IDs":list(z["H_five"]),"Pareto":z["Pareto_H_options"],
        "best_historical_net_DD":z["best_historical_net_DD"],
        "confirmed_strategy":None,"holdouts_opened":False},sort_keys=True))
