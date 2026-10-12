#!/usr/bin/env python3
"""T17-T19 batch: only feasibility counts, seven preexisting NQ DEV months."""
import argparse,json
from pathlib import Path
from collections import Counter
from nq_tick_short_horizon_month import MONTHS
from nq_t17_t19_signal_feasibility import IDS

def aggregate(docs):
    if set(docs)!=set(MONTHS):raise ValueError('all seven DEV months required')
    src=elig=0
    counts=Counter();over=Counter();months=[]
    for m in MONTHS:
        v=docs[m]
        if (v['month']!=m or v['status']!='T17_T19_MECHANISM_SCREEN_ONLY_NO_RETURNS'
          or set(v['hypotheses'])!=set(IDS)
          or v['source_days']!=v['eligible_days']+v['excluded_days']
          or v['oos_read'] is not False or v['new_history_acquired'] is not False
          or v['five_second_new_signals'] is not False or v['PnL_calculated'] is not False):
            raise ValueError('unsafe or inconsistent month')
        src+=v['source_days'];elig+=v['eligible_days']
        x={'month':m,'source':v['source_days'],'eligible':v['eligible_days']}
        for k in IDS:
            a=v['hypotheses'][k]
            if (not 0<=a['signal_days']<=v['eligible_days'] or
                any(a[q] is not None for q in ('economic_trades','net_usd','IC90','q_BH'))
                or a['validated'] is not False):
                raise ValueError('false inference/trades in signal screen')
            counts[k]+=a['signal_days']
            x[k]=a['signal_days']
        over.update(v['overlap_days'])
        months.append(x)
    if (src,elig)!=(140,135):raise AssertionError('Frozen 140/135 parity')
    for pair,n in over.items():
        a,b=pair.split('__')
        if n>min(counts[a],counts[b]):raise AssertionError('overlap > candidates')
    return {'status':'T17_T19_STAGE0_COMPLETE_NO_ECONOMIC_ALPHA',
        'source_days':src,'eligible_sessions':elig,
        'signal_days_by_question':dict(counts),'per_month':months,
        'pairwise_signal_day_overlap':dict(over),
        'n_executed_trades':None,'IC90':None,'q_BH':None,'PF':None,
        'inference_status':'NO_ECONOMIC_RESULTS',
        'holdouts_opened':False,'new_history_acquired':False,
        'no_new_5second_signals':True}
def report(x):
    names={IDS[0]:'¿Ráfaga de transacciones sin expansión contemporánea anuncia volatilidad?',
      IDS[1]:'¿Dirección de subasta 08:00–09:30 persiste postapertura?',
      IDS[2]:'¿Trayectoria ineficiente anticipa aumento de amplitud?'}
    out=['# NQ T17–T19 — tres preguntas NUEVAS, viabilidad en siete meses',
      '',
      '**N representa DÍAS con evento, NO operaciones ejecutadas.** Sin P&L,',
      'IC90, q BH, SL/TP ni prueba estadística de rentabilidad en esta fase.',
      '',
      '| Hipótesis | Pregunta | N días con señal | ¿Direccional? | N trades | IC90 | q BH | ¿Cumple como estrategia? |',
      '|---|---|---:|---|---|---|---|---|']
    for k in IDS:
        out.append(f"| {k} | {names[k]} | {x['signal_days_by_question'][k]} | "
           f"{'Sí (pregunta)' if k==IDS[1] else 'No, magnitud futura'} | N/D | N/D | N/D | **NO EVALUADA** |")
    out+=['','| Mes | Fuente | Elegibles | T17 | T18 | T19 |',
          '|---|---:|---:|---:|---:|---:|']
    for z in x['per_month']:
        out.append(f"| {z['month']} | {z['source']} | {z['eligible']} | "
          +' | '.join(str(z[k]) for k in IDS)+" |")
    out+=['',
      f"Total fuente {x['source_days']} / elegibles {x['eligible_sessions']}.",
      f"Solapamiento de días: {x['pairwise_signal_day_overlap']}.",
      '',
      'T17/T19 son hipótesis de MAGNITUD/volatilidad; no son estrategias long/short',
      'ni pueden sumarse como entradas al portafolio. Cualquier uso monetario exige',
      'convertir una predicción de magnitud en regla económica antes de mirar outcomes.',
      'El usuario pidió AMPLIAR preguntas, no optimizar T05. Se mantiene T05 congelada.',
      'Sin descargar historia nueva, ni abrir holdouts, ni usar velas de 5s para señales.',
      '']
    return '\n'.join(out)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    d={}
    for f in a.inputs.rglob('t17_t19_*.json'):
        x=json.loads(f.read_text())
        if x['month'] in d:raise ValueError('duplicate')
        d[x['month']]=x
    z=aggregate(d)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
    a.report.write_text(report(z)+'\n')
    print('T17_T19_SAFE_FINAL='+json.dumps({
      'source':z['source_days'],'eligible':z['eligible_sessions'],
      'signal_days':z['signal_days_by_question'],
      'PnL_computed':False,'holdouts_opened':False},sort_keys=True))
