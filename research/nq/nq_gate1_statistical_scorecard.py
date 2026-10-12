#!/usr/bin/env python3
"""Auditable statistical Gate 1 scoreboard from EXISTING PUBLIC SAFE reports.

No raw ticks, prices, trades or OOS reads. No inference from P&L aggregates.
H67-H78: prospective exploratory screen (N>150, signed positive net effect,
2sided IC90 >0, 1sided BH q<=0.10 over full six-member family,
>=3/5 favorable years), Holm descriptive family alpha only.
T tick program: NOT statistically assessed; N may reflect correlated trades
within 135 sessions, and CI90/q/year metrics are NOT PRESENT in safe summaries.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from typing import Any

H_QUESTIONS={
"NQ-H67":"¿Combinar gap H09 o consenso H55+H56 suma ventaja neta?",
"NQ-H68":"¿Admitir H09 o H55 sin H56 mejora la estrategia conjunta?",
"NQ-H69":"¿Admitir H09 o H56 como alternativa mejora la estrategia conjunta?",
"NQ-H70":"¿Agregar H29 de respaldo a H67 aporta rentabilidad incremental?",
"NQ-H71":"¿Incorporar ruptura H54 posterior mejora el router base?",
"NQ-H72":"¿Enrutar gap/ruptura/consenso por régimen previo mejora la expectativa?",
"NQ-H73":"¿Volatilidad previa alta→H09 y baja→H56 mejora el router H69?",
"NQ-H74":"¿Volatilidad previa baja→H09 y alta→H56 mejora H69?",
"NQ-H75":"¿Premercado contraído→H09 y expandido→H56 mejora H69?",
"NQ-H76":"¿Premercado expandido→H09 y contraído→H56 mejora H69?",
"NQ-H77":"¿Alineación gap/premarket→H09 y oposición→H56 mejora H69?",
"NQ-H78":"¿Oposición gap/premarket→H09 y alineación→H56 mejora H69?",
}
T_HISTORY=[
 ("T02/T04","¿Reversión de ruptura fallida resiste coste y riesgo?",190,6860.0,1.24356,3385.0,"NO CUMPLE GATE OPERATIVO","NQ_PROJECT_MASTER.md"),
 ("T05-377","¿Filtrado por barras 377 mejora la reversión T02?",115,5102.5,1.31826,1797.5,"PARCIAL, SIN APROBACIÓN","local_nq_tick_2025_2026/NQ_B05G_LAST_TIMESTAMP_SENSITIVITY_RESULTS_2026_10_11.md"),
 ("T05-233+377","¿Doble confirmación mejora sin destruir frecuencia?",59,4657.5,None,None,"NO CUMPLE FRECUENCIA","NQ_PROJECT_MASTER.md"),
 ("T09","¿Breakout revertido antes de 60s mejora la cartera?",None,-2087.5,None,None,"NO CUMPLE INCREMENTO","local_nq_tick_2025_2026/NQ_T09_FAST_TRAP_SEVEN_MONTH_RESULTS_2026_10_11.md"),
 ("T11","¿Aceptación VWAP+actividad aporta segundo alfa?",85,-382.5,0.97183,3960.0,"NO CUMPLE GATE OPERATIVO","local_nq_tick_2025_2026/NQ_B05_T11_VWAP_ROUTER_RESULTS_2026_10_11.md"),
 ("T12","¿Compresión y actividad predicen escape rentable?",268,-2440.0,0.94494,6052.5,"NO CUMPLE GATE OPERATIVO","local_nq_tick_2025_2026/NQ_B05B_T12_COMPRESSION_RELEASE_RESULTS_2026_10_11.md"),
 ("T13","¿Shock de qty seguido de reversión monetiza el flujo Last?",133,-5562.5,0.75447,6320.0,"NO CUMPLE GATE OPERATIVO","local_nq_tick_2025_2026/NQ_B05C_T13_SHOCK_RESULTS_2026_10_11.md"),
 ("B05H-01","¿Expansión acelerada 233+4181/10946 continúa?",None,None,None,None,"NO EVALUABLE (4 SESIONES AMBIGUAS)","local_nq_tick_2025_2026/NQ_B05H01_RESULTS_AND_DIAGNOSTIC_2026_10_11.md"),
 ("B05H-02","¿Giro de VWAP 377 en rango revierte al valor?",75,-1427.5,0.82431,1597.5,"NO CUMPLE GATE OPERATIVO","local_nq_tick_2025_2026/NQ_B05H02_VWAP_REVERSION_RESULTS_2026_10_11.md"),
]
def bh_adjust(pvals:dict[str,float])->dict[str,float]:
    if not pvals:raise ValueError("empty preregistered family")
    if any(not isinstance(p,(int,float)) or not math.isfinite(p) or p<0 or p>1
           for p in pvals.values()):raise ValueError("invalid primary one-sided p")
    ordered=sorted(pvals,key=lambda k:pvals[k])
    out={}
    running=1.0
    m=len(ordered)
    for i in range(m-1,-1,-1):
        k=ordered[i]
        running=min(running,pvals[k]*m/(i+1))
        out[k]=max(0.,min(1.,running))
    return out

def holm_family(pvals:dict[str,float],alpha:float)->dict[str,bool]:
    """Family-level descriptive Holm step-down; NOT independent confirmation."""
    if alpha<=0 or alpha>=1:raise ValueError("bad family alpha")
    ordered=sorted(pvals,key=lambda k:pvals[k])
    passed=True; out={}
    for rank,k in enumerate(ordered):
        passed=passed and (pvals[k]<=alpha/(len(ordered)-rank))
        out[k]=passed
    return out

def family_rows(raw:dict[str,Any],family:dict[str,Any],idx:int)->list[dict]:
    ids=[f"NQ-H{i}" for i in range(67 if idx==6 else 73,
                               73 if idx==6 else 79)]
    if (raw.get('stage')!='DEVELOPMENT_EXPLORATORY' or
        family.get('stage')!='DEVELOPMENT_EXPLORATORY' or
        set(raw.get('hypotheses',{}))!=set(ids) or
        set(family.get('family_metrics',{}))!=set(ids) or
        raw.get('holdout_2025_loaded') is not False or
        raw.get('holdout_2026_loaded') is not False or
        family.get('holdout_2025_loaded') is not False or
        family.get('holdout_2026_loaded') is not False):
        raise ValueError("fail closed: incomplete or contaminated frozen 6-member family")
    p1={k:raw['hypotheses'][k]['p_one_sided'] for k in ids}
    p2={k:family['family_metrics'][k]['p_value_two_sided'] for k in ids}
    q=bh_adjust(p1)
    alpha=.05/(idx*(idx+1))
    holm=holm_family(p2,alpha)
    out=[]
    for k in ids:
        x=raw['hypotheses'][k]
        n=x['n']; net=x['net_usd']
        ci=x.get('ci90',x.get('ci90_mean_trade_usd'))
        sourceq=x['bh_q6']
        if (abs(q[k]-sourceq)>0.00002 or len(ci)!=2 or n<1
            or x['positive_years'] != sum(x['by_year'][str(y)]['net_usd']>0 for y in range(2020,2025))
            or sum(x['by_year'][str(y)]['n'] for y in range(2020,2025))!=n
            or x['strategy_authorized'] is not False
            or x['same_window_benchmarks_available'] is not False
            or x['economic_gate']!='ECONOMIC_DATA_PENDING'
            or not math.isfinite(net) or not math.isfinite(ci[0])
            or not math.isfinite(ci[1])):
            raise ValueError("frozen data/q/year mismatch "+k)
        gates={
            'N_gt_150':n>150,
            'net_signed_mean_positive':net>0 and x['mean_net_mnq_usd']>0,
            'two_sided_IC90_lower_gt_zero':ci[0]>0,
            'BH_q_le_0_10':q[k]<=.10,
            'positive_years_ge_3_of_5':x['positive_years']>=3,
            'prereg_family_full_six_members':True,
        }
        rowsource=x.get('gate1_exploratory_screen',x.get('gate1',{}))
        mapping={'N_gt_150':"N_gt150",
                 'net_signed_mean_positive':"net_mean_positive" if idx==6 else "mean_positive",
                 'two_sided_IC90_lower_gt_zero':"ci90_lower_above_zero" if idx==6 else "ci90_lower_positive",
                 'BH_q_le_0_10':"bh_q_le_010" if idx==6 else "BH_q_at_most_010",
                 'positive_years_ge_3_of_5':"positive_years_3_of_5" if idx==6 else "years_positive_at_least3"}
        for field,fieldsrc in mapping.items():
            if gates[field]!=rowsource[fieldsrc]:
                raise AssertionError(f"Recorded Gate1 conflict {k} {field}")
        if x['mean_net_mnq_usd']*n/net<0:raise ValueError("direction disagreement")
        gate_pass=all(gates.values())
        out.append({
            'id':k,'program':'H_2020_2024_1MIN_MNQ_PROXY',
            'family_number':idx,'family_alpha_Holm':alpha,
            'question':H_QUESTIONS[k],
            'n_executed_trades':n,'n_independent_eligible_events_proven':None,
            'mean_net_usd':x['mean_net_mnq_usd'],
            'net_usd':net,'PF':x['pf'],
            'IC90_lower_usd':ci[0],'IC90_upper_usd':ci[1],
            'p_one_sided':p1[k],'q_BH_six':q[k],
            'p_two_sided':p2[k],
            'Holm_descriptive_family_pass':holm[k],
            'positive_years':x['positive_years'],
            'closed_DD_usd':x['closed_dd_usd'],
            'CAGR_nominal_50k_pct':round(x['equivalent_50k_cagr_full_dev_2020_2024']*100,4),
            'gates':gates,'gate1_exploratory_pass':gate_pass,
            'gate1_result':('PROMISING_EXPLORATORY_ONLY' if gate_pass else
                 'INSUFFICIENT_EVIDENCE_N' if n<=150 else 'NOT_SUPPORTED_EXPLORATORY'),
            'incremental_vs_parent':(
                 raw['hypotheses'][k].get('incremental_total_vs_h69_usd')
                 if idx==7 else None),
            'economic_gate':'NOT_EVALUATED_ETF_AND_FUNDED_RISK',
            'out_of_sample_verified':False,'broker_fills_verified':False,
            'question_source':("research/nq/NQ_H73_H78_PREREG_2026_10_10.md" if idx==7
                       else "research/nq/NQ_DEDUCTIVE_ENSEMBLE_POLICY_2026_10_10.md"),
            'original_record_decision':x['decision']})
    return out

def evaluation(root:Path):
    rows=[]
    for a,b,index in [
         ('results/nq_h67_h72/NQ_H67_H72_REPORT_2020_2024.json',
          'results/development/nq_h67_h72_family.json',6),
         ('results/nq_h73_h78/NQ_H73_H78_REPORT_2020_2024.json',
          'results/development/nq_h73_h78_family.json',7)]:
        x=json.loads((root/a).read_text('utf8'))
        y=json.loads((root/b).read_text('utf8'))
        rows.extend(family_rows(x,y,index))
    if len(rows)!=12:raise AssertionError('12 historical strategies required')
    pending=[{
       'id':k,'question':q,'program':'T_TICK_DEV_SEVEN_MONTHS',
       'n_executed_trades':n,'net_usd_stress':net,
       'PF_stress':pf,'Last_DD_stress_usd':dd,
       'IC90_net_usd':None,'q_BH':None,'Holm_family_pass':None,
       'positive_years_3of5':None,
       'N_gt150_independent_events':None,
       'gate1_exploratory_pass':None,
       'statistical_status':'NOT_EVALUABLE_YET_NO_PREREGISTERED_T_FAMILY_INFERENCE',
       'economic_status':status,'source':source,'no_5second_new_signals':True
       } for k,q,n,net,pf,dd,status,source in T_HISTORY]
    return {'status':'GATE1_STATISTICAL_HISTORICAL_REAUDIT_COMPLETED_NO_NEW_INFERENCE',
      'gate_policy':'research/es/ES_STAGE_GATES_EXPLORATORY_AMENDMENT_2026_10_09.md',
      'confirmation_policy':'research/RESEARCH_CONTROLS_POLICY.md',
      'old_frozen_gates_modified':False,'new_trading_results_computed':False,
      'new_data_downloaded':False,'holdout_read':False,
      'H67_H78_historical_screen':rows,
      'T_recent_missing_statistical_evidence':pending,
      'historical_gate1_n_pass':sum(x['gate1_exploratory_pass'] for x in rows)}

def report(z):
    s=['# NQ — Evaluación estadística acumulativa y completa por hipótesis',
      '',
      '**Auditoría de evidencia EXISTENTE, no nuevo backtest.** Se reconstruyen q de BH por familia',
      'con los seis p unilaterales registrados; IC90 bilateral, N y años desde los reportes',
      'H67–H78 2020–2024. Holm familiar desde p bilaterales es DIAGNÓSTICO DESCRIPTIVO',
      'sin reemplazar el control oficial ni la validación independiente OOS.',
      'El histórico H usa **MNQ 1 contrato PROXY de OHLC NQ de 1 minuto**; no NQ tick Last.',
      '',
      '## Históricos H67–H78: Gate 1 exploratorio íntegro',
      '',
      '| Hipótesis | Pregunta falsable | N trades | Media USD | IC90 (USD/trade) | q BH (familia de 6) | Años + /5 | PF | DD cerrado USD | Holm familiar* | ¿Gate 1? |',
      '|---|---|---:|---:|---|---:|---:|---:|---:|---|---|']
    for r in z['H67_H78_historical_screen']:
        s.append(f"| {r['id']} | {r['question']} | {r['n_executed_trades']} | "
           f"{r['mean_net_usd']:.2f} | [{r['IC90_lower_usd']:.2f}, {r['IC90_upper_usd']:.2f}] | "
           f"{r['q_BH_six']:.4f} | {r['positive_years']}/5 | {r['PF']:.3f} | "
           f"{r['closed_DD_usd']:.2f} | {'Pasa' if r['Holm_descriptive_family_pass'] else 'No pasa'} | "
           f"**{'PASS exploratorio únicamente' if r['gate1_exploratory_pass'] else 'NO CUMPLE'}** |")
    s+=['','* Holm se muestra con la asignación familiar histórica αₖ =0,05/[k(k+1)]',
        '(k=6 o k=7), bajo p bilaterales almacenados y corrección step-down.',
        'No equivale a prueba OOS confirmatoria ni a replicación independiente.',
        '**N de eventos independientes:** los informes registran N de trades/sesiones',
        'máximo 1 MNQ/día; se conserva la diferencia conceptual y no se inventa',
        'N efectivo de clusters. Para esta pantalla se informa el N histórico preregistrado.',
        '',
        f"**Históricos Gate 1 PASS: {z['historical_gate1_n_pass']}/12.**",
        '',
        '## Programa T reciente: ESTADÍSTICAS NO CALCULADAS (no confundir con cero)',
        '',
        '| Hipótesis | Pregunta | N trades | Neto estrés USD | PF estrés | DD Last USD | IC90 | q BH | Holm | 3/5 años | Dictamen operativo | Gate 1 estadístico |',
        '|---|---|---:|---:|---:|---:|---|---|---|---|---|---|']
    for r in z['T_recent_missing_statistical_evidence']:
        def fmt(x):
            return 'N/D' if x is None else str(x)
        s.append(f"| {r['id']} | {r['question']} | {fmt(r['n_executed_trades'])} | "
            f"{fmt(r['net_usd_stress'])} | {fmt(r['PF_stress'])} | "
            f"{fmt(r['Last_DD_stress_usd'])} | **N/D** | **N/D** | **N/D** | **N/D** | "
            f"{r['economic_status']} | **NO EVALUABLE** |")
    s+=['','**N/D ≠ cero, ni aprobado ni evidencia de significancia.** Las 135 sesiones',
       'DEV Tick Last están reutilizadas; no existe la serie 2020–24 de ticks de',
       'estas T ni un registro estadístico de toda la familia con efectos/p unilaterales',
       'y IC90 causal por días/semanas. N trades no equivale a N independientes:',
       'dos entradas/día pueden estar correlacionadas. No calcular q desde P&L agregado.',
       'Las cuatro sesiones H01 no resueltas bloquean sus métricas completas.',
       '',
       '## Criterios que seguirán las próximas hipótesis (en el chat y en GitHub)',
       '',
       '1. Prerregistrar ID, pregunta, dirección, familia y todos los miembros, unidad',
       '   de inferencia día/semana; condiciones de falsación y datos sellados.',
       '2. Publicar N de eventos elegibles y N de trades distintos, IC90 bilateral',
       '   de efecto NETO con dependencia temporal, p unilateral, q BH familiar,',
       '   Holm confirmatorio separado, 3/5 años cuando corresponda, y el PASS/FAIL',
       '   de CADA condición. Costes, estrés, PF, DD, estabilidad mensual e incremento',
       '   de router son gates operativos ADICIONALES, no sustitutos estadísticos.',
       '3. T que no posea cinco años, resultados de efecto por sesión o familia',
       '   congelada conserva N/D y decisión **INSUFICIENTE/NO EVALUABLE**:',
       '   no aprobar T05 por su PF ni llamar exitoso un GitHub Actions SUCCESS.',
       '4. **No 5s en señales T nuevas**; las T antiguas con esa unidad quedan como',
       '   evidencia histórica sin reescritura. Sin adquirir historia nueva ni abrir OOS.',
       '']
    return '\n'.join(s)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--out-json',type=Path,required=True)
    p.add_argument('--out-md',type=Path,required=True)
    a=p.parse_args()
    z=evaluation(a.root)
    a.out_json.parent.mkdir(parents=True,exist_ok=True)
    a.out_json.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    a.out_md.write_text(report(z),encoding='utf8')
    print('NQ_GATE1_SAFE_AUDIT='+json.dumps({
       'historical_hypotheses':len(z['H67_H78_historical_screen']),
       'historical_gate1_pass':z['historical_gate1_n_pass'],
       'T_missing_advanced_stats':len(z['T_recent_missing_statistical_evidence']),
       'holms_all_descriptive':sum(r['Holm_descriptive_family_pass'] for r in z['H67_H78_historical_screen']),
       'data_new':False,'oos_read':False},sort_keys=True))
