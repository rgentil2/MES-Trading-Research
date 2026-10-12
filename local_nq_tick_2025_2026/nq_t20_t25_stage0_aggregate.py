#!/usr/bin/env python3
"""T20–T25 safe aggregate. Only case/control frequencies, NO alpha."""
import argparse,json
from pathlib import Path
from collections import Counter
from nq_tick_short_horizon_month import MONTHS
from nq_t20_t25_fixed_anchor_screen import IDS,LABELS,CASE,CONTROL

STATUS='T20_T25_FROZEN_STAGE0_CASE_CONTROL_NO_OUTCOMES'


def aggregate(docs):
    if set(docs)!=set(MONTHS):
        raise ValueError('all seven fixed DEV months required, no others')
    source=eligible=anchor=0
    counts={k:Counter() for k in IDS}
    sides={k:Counter() for k in IDS}
    overlaps=Counter()
    per_month=[]
    for month in MONTHS:
        v=docs[month]
        if (v['status']!=STATUS or v['month']!=month
            or set(v['by_question'])!=set(IDS)
            or set(v['side_counts_case_or_control'])!=set(IDS)
            or v['source_days']!=v['eligible_days']+v['excluded_days']
            or v['anchor_days']>v['eligible_days']
            or any(v[k] is not False for k in
                ('holdouts_opened','new_history_acquired','five_second_new_signals',
                 'outcomes_computed','individual_events_exported'))
            or any(v[k] is not None for k in
                ('N_trades','net_usd','CI90','p','q_BH','PF','DD'))):
            raise ValueError('unsafe month, missing hypothesis, or invented alpha')
        source+=v['source_days']
        eligible+=v['eligible_days']
        anchor+=v['anchor_days']
        row={'month':month,'source':v['source_days'],'eligible':v['eligible_days'],
             'anchor':v['anchor_days']}
        for k in IDS:
            item=v['by_question'][k]
            if set(item)!=set(LABELS) or any(
                    type(item[s]) is not int or item[s]<0 for s in LABELS):
                raise ValueError('bad case/control categories')
            if sum(item.values())!=v['eligible_days']:
                raise ValueError('case/control categories not exhaustive')
            if item[CASE]+item[CONTROL]+item['OTHER']>v['anchor_days']:
                raise ValueError('more classified observations than anchors')
            counts[k].update(item)
            sides[k].update(v['side_counts_case_or_control'][k])
            row[k]={'case':item[CASE],'control':item[CONTROL],
                    'missing':item['NOT_EVALUABLE']}
        overlaps.update(v['case_case_overlap_days'])
        per_month.append(row)
    if (source,eligible)!=(140,135):
        raise AssertionError('prior 140/135 DEV parity failed')
    for pair,n in overlaps.items():
        a,b=pair.split('__')
        if a not in IDS or b not in IDS or n>min(counts[a][CASE],counts[b][CASE]):
            raise AssertionError('bad case overlap')
    return {'status':'STAGE0_COMPLETE_NO_ALPHA_INFERENCE',
        'source_days':source,'eligible_sessions':eligible,'anchor_days':anchor,
        'by_question':{k:dict(counts[k]) for k in IDS},
        'side_counts_case_or_control':{k:dict(sides[k]) for k in IDS},
        'case_case_overlap_days':dict(overlaps),
        'per_month':per_month,
        'control_identifiable':{k:counts[k][CASE]>0 and counts[k][CONTROL]>0
                                for k in IDS},
        'N_independent':None,'N_trades':None,'net_usd':None,'CI90':None,
        'p':None,'q_BH':None,'Holm':None,'PF':None,'DD':None,
        'holdouts_opened':False,'new_history_acquired':False,
        'new_five_second_signals':False,'PnL_computed':False}


def report(a):
    names={
      IDS[0]:'¿Valor negociado cerca del extremo de barra frente al centro?',
      IDS[1]:'¿Rechazo de extremo previo frente a aceptación?',
      IDS[2]:'¿Tamaño/print con avance frente a tamaño estable?',
      IDS[3]:'¿Desaceleración y rango futuro frente a duración estable?',
      IDS[4]:'¿Alternancia de direcciones VWAP frente a alineación?',
      IDS[5]:'¿Discrepancia 233/4181 frente a alineación?'}
    out=['# NQ T20–T25 | Primera medición de seis preguntas con control',
      '',
      '**SOLO ETAPA 0: N = sesiones clasificadas en caso/control; NO N trades,',
      'NO retornos, IC90, q, PF, DD o evidencia de alfa.**',
      '',
      '| ID | Pregunta | N caso | N control | Otro | N/D | ¿Control identificable? | ¿Alpha validada? |',
      '|---|---|---:|---:|---:|---:|---|---|']
    for k in IDS:
        z=a['by_question'][k]
        out.append(f"| {k} | {names[k]} | {z.get('CASE',0)} | "
            f"{z.get('CONTROL',0)} | {z.get('OTHER',0)} | "
            f"{z.get('NOT_EVALUABLE',0)} | "
            f"{'Sí' if a['control_identifiable'][k] else 'NO'} | **NO** |")
    out+=['','| Mes | Fuente | Elegibles | Ancla | '
          +' | '.join('T'+k[1:3]+' caso/control' for k in IDS)+' |',
          '|---|---:|---:|---:|'+ '|'.join(['---:']*len(IDS))+'|']
    for z in a['per_month']:
        out.append(f"| {z['month']} | {z['source']} | {z['eligible']} | {z['anchor']} | "
                   +' | '.join(f"{z[k]['case']}/{z[k]['control']}" for k in IDS)+' |')
    out+=['',f"Universo {a['source_days']} sesiones fuente / {a['eligible_sessions']} "
          f"elegibles / {a['anchor_days']} con ancla 10:00–10:15 ET.",
          'Casos simultáneos por día: '+str(a['case_case_overlap_days']),
          'Orientaciones de caso o control (no fills): '+str(a['side_counts_case_or_control']),
          '',
          'Preregistro congelado antes de cualquier outcome, sin selección por P&L.',
          'No añadir una estrategia a T05 ni medir retorno hasta fijar endpoint,',
          'simulador y presupuesto de seis pruebas en prerregistro económico separado.',
          'Sin nueva historia, holdouts sellados, ni barras 5s de señales nuevas.',
          '']
    return '\n'.join(out)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    x=p.parse_args()
    docs={}
    for fn in x.inputs.rglob('t20_t25_*.json'):
        z=json.loads(fn.read_text())
        if z['month'] in docs:raise ValueError('duplicate month')
        docs[z['month']]=z
    final=aggregate(docs)
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(final,sort_keys=True,indent=2)+'\n')
    x.report.write_text(report(final)+'\n')
    print('NQ_T20_T25_STAGE0_FINAL='+json.dumps({
        'source':final['source_days'],'eligible':final['eligible_sessions'],
        'anchor':final['anchor_days'],
        'cases_controls':{k:(final['by_question'][k]['CASE'],
                             final['by_question'][k]['CONTROL']) for k in IDS},
        'no_alpha':True},sort_keys=True))
