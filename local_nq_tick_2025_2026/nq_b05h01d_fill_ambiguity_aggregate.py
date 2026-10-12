#!/usr/bin/env python3
"""Seven-month existing-source B05H01D fail-closed diagnostics, never trading alpha."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_b05h01d_fill_ambiguity_month import NEW,ROUTER

def aggregate(rows):
    if set(rows)!=set(MONTHS):raise ValueError('exact seven DEV months required')
    total_source=total_eligible=0
    defects=Counter()
    summary=[]
    for month in MONTHS:
        x=rows[month]
        if (x['month']!=month or x['status']!='B05H01D_DIAGNOSTIC_ONLY_NO_PNL'
            or x['holdouts_opened'] is not False
            or x['new_market_history_acquired'] is not False
            or x['trading_results_calculated_or_published'] is not False
            or x['five_second_bars_used_in_new_signals'] is not False
            or x['source_days']!=x['eligible_days']+x['excluded_days']):
            raise ValueError('QC security or coverage mismatch')
        total_source+=x['source_days'];total_eligible+=x['eligible_days']
        defects.update(x['hard_fail_details'])
        summary.append({'month':month,'source_days':x['source_days'],
                        'eligible_days':x['eligible_days'],
                        'h01_opportunities':x['h01_candidate_opportunities'],
                        'route_scenario_hard_fails':x['hard_fail_routes_by_scenario']})
    if (total_source,total_eligible)!=(140,135):
        raise AssertionError('Frozen DEV 140/135 changed')
    blocked=any(x['route_scenario_hard_fails'] for x in summary)
    # Document detection; under all circumstances old H01 remains not funded.
    return {'status':'B05H01D_FULL_SEVEN_MONTH_EXECUTION_DIAGNOSTIC',
            'decision':'B05H01_DO_NOT_PROMOTE_AMBIGUOUS_EXECUTION'
                if blocked else 'B05H01_STILL_NOT_VALIDATED_NO_7MONTH_PNL',
            'source_days':total_source,'eligible_days':total_eligible,
            'months':summary,'hard_failure_totals_by_owner_scenario_status':dict(defects),
            'h01_opportunities_total':sum(x['h01_opportunities'] for x in summary),
            'new_alpha_hypotheses':0,'new_history_acquired':False,
            'holdouts_opened':False,'broker_fills_verified':False,
            'trading_returns_recovered_or_published':False,
            'B05H01_original_results_preserved_as_failed':True}
def report(x):
    lines=['# B05H01D — causa de bloqueos, SIN declarar P&L','',
      'Solo NQ Last histórico YA disponible. **B05H-01 ORIGINAL sigue FAILED**.',
      '**Este diagnóstico no modifica parámetros, ni omite operaciones, ni estima rentabilidad.**','',
      '| Mes | Días fuente | Días elegibles | Señales H01 | Bloqueos primera ejecución por ruta/escenario |',
      '|---|---:|---:|---:|---|']
    for r in x['months']:
        labels=', '.join(f"{k}={v}" for k,v in
                 sorted(r['route_scenario_hard_fails'].items())) or '0'
        lines.append(f"| {r['month']} | {r['source_days']} | {r['eligible_days']} | {r['h01_opportunities']} | {labels} |")
    lines+=['','## Fallos agregados por propietario/escenario/causa','']
    for k,v in sorted(x['hard_failure_totals_by_owner_scenario_status'].items()):
        lines.append(f"- {k}: **{v}** sesiones/primer fallo")
    lines+=['',f"**Decisión: {x['decision']}**.",'',
      'NO hay medición válida de rentabilidad para siete meses bajo el protocolo original.',
      'No cambiar el orden de prints, excluir trades por outcome, ni recuperar cifras mensuales',
      'como demostración de ventaja. El H01 pudo agotar los dos slots diarios y',
      'desplazar T05 incluso en meses no bloqueados.',
      'Los resultados B05F/B05G y T05 quedan históricos, no aprobados para fondeo.',
      'Siguiente estudio debe prerregistrar una unidad económica realmente independiente',
      'con señal Last por número de transacciones, nunca 5 segundos, y un esquema',
      'causal de entrada de acuerdo con la información observable sin nueva data.',
      '']
    return '\n'.join(lines)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    months={}
    for f in a.inputs.rglob('nq_b05h01d_*.json'):
        v=json.loads(f.read_text(encoding='utf8'))
        if v['month'] in months:raise ValueError('duplicate month')
        months[v['month']]=v
    x=aggregate(months)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n',encoding='utf8')
    a.report.write_text(report(x),encoding='utf8')
    print('B05H01D_SAFE_FINAL='+json.dumps(x,sort_keys=True))
