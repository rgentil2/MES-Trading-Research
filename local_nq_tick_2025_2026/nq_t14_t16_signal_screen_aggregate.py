#!/usr/bin/env python3
"""Seven-month immutable T14-T16 opportunity screen; no backtest nor inference."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_t14_t16_signal_feasibility import IDS

def reconcile(rows):
    if set(rows)!=set(MONTHS):raise ValueError('Must include exactly seven DEV months')
    total_source=total_eligible=0
    counts=Counter()
    pairs=Counter()
    months=[]
    for m in MONTHS:
        r=rows[m]
        if (r['month']!=m or
            r['status']!='T14_T16_FROZEN_SIGNAL_SCREEN_ONLY_NO_RETURNS' or
            set(r['hypotheses'])!=set(IDS) or
            r['holdouts_opened'] is not False or
            r['new_data_acquired'] is not False or
            r['new_5second_signals'] is not False or
            r['returns_or_fills_computed'] is not False or
            r['tick_or_trade_rows_exported'] is not False or
            r['source_days']!=r['eligible_days']+r['excluded_days']):
            raise ValueError('Nonreconciling or unsafe inputs')
        total_source+=r['source_days'];total_eligible+=r['eligible_days']
        brief={'month':m,'source_days':r['source_days'],
           'eligible_sessions':r['eligible_days']}
        for k in IDS:
            h=r['hypotheses'][k]
            if (h['candidate_signal_days']!=h['candidate_signals']
                or h['candidate_signals']>r['eligible_days'] or
                h['executed_trades'] is not None or
                h['net_pnl'] is not None or h['IC90'] is not None or
                h['q_BH'] is not None or h['economically_validated'] is not False):
                raise ValueError('No outcomes or fake N allowed in stage 0')
            counts[k]+=h['candidate_signals']
            brief[k]=h['candidate_signals']
        pairs.update(r['pairwise_candidate_days'])
        months.append(brief)
    if (total_source,total_eligible)!=(140,135):
        raise AssertionError('FROZEN 140 source /135 eligible parity failed')
    for k,v in pairs.items():
        a,b=k.split('__')
        if v>min(counts[a],counts[b]):raise AssertionError('Invalid pairwise overlap')
    return {'status':'T14_T16_STAGE0_SEVEN_MONTHS_COMPLETE_NOT_ALPHA',
      'N_source_days':total_source,'N_eligible_sessions':total_eligible,
      'N_active_sessions_by_question':dict(counts),
      'N_trade_signals_by_question':dict(counts),
      'N_executed_trades_by_question':{k:None for k in IDS},
      'pairwise_same_session_signals':dict(pairs),
      'monthly':months,'N_effective_independent':None,
      'IC90':None,'p_values':None,'q_BH_family':None,'Holm':None,
      'economic_PnL':None,'profitable_or_statistically_significant':None,
      'all_six_questions_economically_evaluated':False,
      'new_history_acquired':False,'holdouts_opened':False,
      'new_5second_signals':False,
      'decision':'FEASIBILITY_ONLY_PREREG_ECONOMIC_DESIGN_REQUIRED'}
def report(z):
    ln=['# T14–T16: tres hipótesis NUEVAS por prints NQ — solo pantalla de viabilidad',
      '',
      '**La métrica N de esta tabla es DÍAS CON SEÑAL, no trades ejecutados.**',
      'Se usaron únicamente los siete meses DEV ya almacenados 2025-oct..2026-abr.',
      'Los resultados NO incluyen TP/SL, costes, fills, P&L, intervalos IC90 o q BH;',
      'todas estas celdas son N/D y ninguna hipótesis puede declararse rentable.',
      '',
      '| Hipótesis | Pregunta resumida | N sesiones con señal | N trades | IC90 | q BH | ¿Cumple como estrategia? |',
      '|---|---|---:|---|---|---|---|']
    q={IDS[0]:'¿La persistencia direccional suave continúa?',
       IDS[1]:'¿Aceptar precios redondos anticipa continuación?',
       IDS[2]:'¿Contratos por print altos sin desplazamiento anticipan giro?'}
    for id in IDS:
        ln.append(f"| {id} | {q[id]} | {z['N_active_sessions_by_question'][id]} | N/D | N/D | N/D | **PENDIENTE de evaluación económica** |")
    ln+=['','## Cantidad por mes y control de cobertura','','| Mes | Días fuente | Elegibles | T14 | T15 | T16 |',
         '|---|---:|---:|---:|---:|---:|']
    for m in z['monthly']:
        ln.append(f"| {m['month']} | {m['source_days']} | {m['eligible_sessions']} | "+' | '.join(str(m[k]) for k in IDS)+" |")
    ln+=['',f"Total **{z['N_source_days']} fuente / {z['N_eligible_sessions']} sesiones elegibles**.",
      'Solapamientos entre días con señal: '+(str(z['pairwise_same_session_signals']) or '{}')+'.',
      '',
      '## Implicaciones estrictas',
      '',
      '- No filtrar señales usando el P&L de T05 ni cambiar umbrales por estos conteos.',
      '- Aunque N señal sea alto, nunca equivale a N de trades, ni a N estadísticamente independientes.',
      '- Para estudiar P&L se debe congelar primero la ejecución/riesgo de las tres preguntas,',
      '  evaluarlas todas como familia con los mismos costes, y calcular incremental',
      '  en UNA cuenta si se decide incorporar T05 congelada.',
      '- T17–T19 están registrados como preguntas, **aún NO probados**.',
      '- Sin 5s para señales nuevas, sin adquirir más historia, sin abrir OOS.',
      '']
    return '\n'.join(ln)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    months={}
    for f in a.inputs.rglob('t14_t16_*.json'):
        row=json.loads(f.read_text('utf8'))
        if row['month'] in months:raise ValueError('Duplicate month in screen')
        months[row['month']]=row
    z=reconcile(months)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n')
    a.report.write_text(report(z)+'\n')
    print('T14_T16_SCREEN_RESULT_SAFE='+json.dumps({
        'status':z['status'],'source':z['N_source_days'],
        'eligible':z['N_eligible_sessions'],
        'signal_days':z['N_active_sessions_by_question'],
        'pnl':False,'oos':False},sort_keys=True))
