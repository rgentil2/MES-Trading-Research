#!/usr/bin/env python3
"""MONTHLY-ONLY 7-point descriptive statistics for already-processed NQ T evidence.

NO raw ticks, no new trading signals, no daily/weekly p-values, no family q-BH.
Bilateral 90% t interval of MONTHLY mean with df=6 is descriptive only.
Exact one-sided monthly sign p requires independent exchangeable month signs,
an unverified assumption; neither p nor CI is confirmatory after selection.
"""
import argparse,json,math,statistics
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS

T_CRIT_90_DF6=1.943180280515303
T05="T05_377"
H02="H02_PRINT_VWAP_MEAN_REVERSION"
ROUTER="T05_PRIORITY_H02_SHARED_ROUTER"
SC="stress_1p5_fee_2ticks_each_side"

def cents(x):
    if type(x) not in (int,float) or not math.isfinite(x):
        raise ValueError("nonfinite money")
    y=round(x*100)
    if abs(x-y/100)>1e-7:
        raise ValueError("not rounded to cents")
    return y
def usd(x):
    return round(x/100,2)

def exact_sign_p(n_positive,n_total):
    if not (isinstance(n_total,int) and n_total>=1 and
            isinstance(n_positive,int) and 0<=n_positive<=n_total):
        raise ValueError("invalid month sign count")
    return sum(math.comb(n_total,k) for k in range(n_positive,n_total+1))/2**n_total

def month_diagnostic(values):
    """Seven independently described periods; not seven independent proofs."""
    if len(values)!=7:
        raise ValueError("need all seven preselected months")
    nums=[cents(v) for v in values]
    n=7
    m=statistics.mean(nums)/100
    sd=statistics.stdev(nums)/100
    se=sd/math.sqrt(n)
    half=T_CRIT_90_DF6*se
    total=sum(nums)
    leave=[total-v for v in nums]
    npos=sum(v>0 for v in nums)
    return {
       "unit":"USD_PER_CALENDAR_MONTH",
       "n_months":n,
       "n_positive_months":npos,
       "n_zero_months":sum(v==0 for v in nums),
       "total_usd":usd(total),
       "mean_monthly_usd":round(m,4),
       "std_monthly_usd":round(sd,4),
       "standard_error_monthly_usd":round(se,4),
       "ci90_mean_monthly_usd":[round(m-half,4),round(m+half,4)],
       "ci90_method":"STUDENT_T_DF6_ASSUMES_APPROX_INDEPENDENT_MONTHS_DESCRIPTIVE_ONLY",
       "exact_one_sided_monthly_sign_p":exact_sign_p(npos,n),
       "p_is_confirmatory":False,
       "q_BH":None,
       "Holm":None,
       "leave_one_month_out_total_range_usd":[usd(min(leave)),usd(max(leave))],
       "leave_one_month_out_signs_positive":sum(a>0 for a in leave),
       "stability_descriptive_positive_5of7":npos>=5,
       "gate1_statistical_pass":None,
       "inference_status":"SEVEN_MONTHS_DESCRIPTIVE_ONLY_NOT_INDEPENDENT_VALIDATION"}

def run(src):
    if (src.get("status")!="B05H02_FINISHED_DEV_ONLY_NOT_OOS" or
        src.get("decision")!="B05H02_REJECT_DO_NOT_PROMOTE" or
        src.get("source_months")!=list(MONTHS) or
        (src.get("source_days"),src.get("eligible_days"))!=(140,135) or
        src.get("holdouts_opened") is not False or
        src.get("new_history_acquired") is not False or
        src.get("H02_uses_5s_signals") is not False or
        src.get("funded_strategy_approved") is not False or
        src.get("broker_fills_verified") is not False):
        raise ValueError("source must be untouched, seven DEV months, no OOS")
    models=src["models"]
    if set(models)!={T05,H02,ROUTER}:
        raise ValueError("all three models required")
    frozen={T05:(115,510250),H02:(75,-142750),ROUTER:(166,219500)}
    month_counts=[]
    sequences={}
    for model in (T05,H02,ROUTER):
        r=models[model][SC]
        n_trades,net=frozen[model]
        if r['trades']!=n_trades or cents(r['net_usd'])!=net:
            raise ValueError("frozen standalone/router result mutated")
        entries=r["monthly"]
        if len(entries)!=7 or any(v["month"]!=MONTHS[i] for i,v in enumerate(entries)):
            raise ValueError("monthly chronology or coverage wrong")
        months=[v["net_usd"] for v in entries]
        if cents(sum(months))!=net:raise AssertionError("all seven month nets differ")
        if sum(v["trades"] for v in entries)!=n_trades:
            raise AssertionError("monthly trades do not reconcile")
        sequences[model]=months
        month_counts.append({"model":model,"n_trades":n_trades,
                             "monthly_positive":sum(x>0 for x in months)})
    paired=[usd(cents(a)-cents(b)) for a,b in
            zip(sequences[ROUTER],sequences[T05])]
    if cents(sum(paired))!=-290750:
        raise AssertionError("paired router delta does not reconcile")
    extra=src['diagnostics']
    if (extra['T05_retained_router']!=106 or
        extra['H02_executed_router']!=60 or
        cents(extra['H02_stress_net_router'])!=-253000 or
        cents(extra['router_minus_T05_extra10_usd'])!=-341750):
        raise AssertionError("fixed attribution mismatch")
    stats={x:month_diagnostic(sequences[x]) for x in (T05,H02,ROUTER)}
    stats["ROUTER_MINUS_T05_PAIRED"]=month_diagnostic(paired)
    return {"status":"NQ_T_7_MONTH_DESCRIPTIVE_DIAGNOSTIC_COMPLETE",
      "statistical_gate1_promotion":False,
      "note":"IC90 USD/MONTH and exact sign p from just 7 preobserved monthly totals; neither is confirmatory",
      "source_days":140,"eligible_sessions":135,"calendar_months":list(MONTHS),
      "n_daily_independent_events":None,"effective_sample_size":None,
      "N_trades_source":{x:frozen[x][0] for x in frozen},
      "stats":stats,"source_month_trades":month_counts,
      "original_operational_decisions_unchanged":True,
      "holms_or_bh_computed":False,"new_market_data_read":False,
      "raw_tick_history_read":False,"holdouts_opened":False,
      "source_kind":"EXISTING_PUBLIC_MONTHLY_SAFE_SUMMARY_ONLY"}

def report(r):
    lines=["# NQ T — Análisis estadístico adaptado a la muestra REAL de 7 meses (diagnóstico)",
    "",
    "**Fuente:** solo resumen seguro congelado B05H02 (140 días fuente/135 sesiones elegibles).",
    "No se descargaron ticks ni se abrió 2026-05..09 reservado. N_trades no equivale a sesiones independientes.",
    "**ADVERTENCIA:** se dispone aquí solo de SIETE observaciones mensuales, NO 135 P&L diarios.",
    "Un IC90 de media mensual t(d.f.=6) NO es un IC90 robusto por día/trade; el test de signo",
    "supone meses independientes, supuesto imposible de comprobar bien con 7 meses.",
    "Son diagnósticos EXPLORATORIOS sobre estrategias YA SELECCIONADAS; q BH/Holm = N/D.",
    "",
    "| Modelo | N trades | Meses positivos/7 | Total neto estrés USD | Media USD/mes | IC90 media mensual USD/mes | p signo mensual* | Rango LOMO total USD | ¿Cumple estadísticamente? |",
    "|---|---:|---:|---:|---:|---|---:|---|---|"]
    for k,label in ((T05,"T05-377"),(H02,"H02-377"),(ROUTER,"Router T05+H02"),
                    ("ROUTER_MINUS_T05_PAIRED","Incremento router−T05")):
        a=r['stats'][k];n=r['N_trades_source'].get(k,"N/A: delta emparejado")
        low,hi=a['ci90_mean_monthly_usd']
        lom=a['leave_one_month_out_total_range_usd']
        lines.append(f"| {label} | {n} | {a['n_positive_months']}/7 | "
          f"{a['total_usd']:.2f} | {a['mean_monthly_usd']:.2f} | "
          f"[{low:.2f}, {hi:.2f}] | {a['exact_one_sided_monthly_sign_p']:.4f} | "
          f"[{lom[0]:.2f}, {lom[1]:.2f}] | **NO EVALUABLE formalmente** |")
    lines+=["",
      "*p de signo es binomial exacto (7 meses, signos equiprobables independientes bajo nula),",
      "no BH q y **no prueba significancia válida tras búsqueda adaptativa**.",
      "Un p=0.0625 para 6/7 meses positivos no acredita edge; el mínimo p no-cero",
      "de 7 signos todos positivos es 0.0078125 antes de corrección.",
      "",
      "## Ajuste a 135 sesiones — próximos cálculos válidos sin nuevos datos",
      "",
      "1. Usar P&L DAILY de las 135 sesiones DEV **incluyendo días sin trade**;",
      "   n_sessions, n_active_days, n_trades, unidad efectiva y mismo calendario.",
      "2. IC90 de bloques móviles de 5 sesiones, 10,000 bootstrap; sensibilidad",
      "   a bloques 3 y 10 antes de evaluar outcomes; métricas para incremento",
      "   diario P&L(router)−P&L(T05) EMPAREJADO, no comparar estrategias separadas.",
      "3. Ver siete meses y siete leave-one-month-out sin seleccionar el mejor,",
      "   p/q BH solo sobre una familia preregistrada COMPLETA, Holm separado.",
      "4. Si falta vector diario o family p-values, campo = **N/D**, NO PASS.",
      "5. Histórico de cinco años H y confirmación independiente OOS sin cambiar.",
      "6. Operativamente H02 sigue rechazado (−$2907.50 incremento con estrés),",
      "   T05 solo exploratorio (PF extra $10 RT <1.25); ninguna cuenta financiada aprobada.",
      "",
      "Documentación vinculante: [política NQ de siete meses](research/nq/NQ_TICK_SEVEN_MONTH_STATISTICAL_POLICY_2026_10_11.md)."]
    return '\n'.join(lines)+'\n'

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    r=run(json.loads(a.source.read_text("utf8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding="utf8")
    a.report.write_text(report(r),encoding="utf8")
    print("NQ_T_7_MONTH_SAMPLE_STATS="+json.dumps({"status":r["status"],
      "source_days":r["source_days"],"eligible_sessions":r["eligible_sessions"],
      "signs":{k:r["stats"][k]["n_positive_months"] for k in r["stats"]},
      "range":{k:r["stats"][k]["ci90_mean_monthly_usd"] for k in r["stats"]},
      "gates_unchanged":True,"no_new_data":True},sort_keys=True))
