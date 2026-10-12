#!/usr/bin/env python3
"""B05F: stream ALREADY ARCHIVED DEV NQ Last, objective QC and causal print bars.

NO P&L, no strategy signals, no quotes-as-fills. No new data acquisition.
Outputs ONLY safe seven-month QC aggregates, not days/ticks/trades/prices.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

from qc_tick_day import utc_bounds,file_for
from qc_tick_to_minutes import source_events,Bar,consolidate_bars,CONTRACT_RE
from nq_tick_short_horizon import dev_day,N_BARS,OR_START,OR_END,STEP_100NS
from nq_tick_short_horizon_month import MONTHS,month_days

LENGTHS=(233,377,4181,10946)
CUTOFFS={'09:30':1080,'10:00':1440,'11:10':2280}
WINDOW_START,WINDOW_END=1200,2280
WINDOW_BARS=WINDOW_END-WINDOW_START
TOTAL_SOURCE=140
TOTAL_ELIGIBLE=135
STATES=('READY','SKIP_MISSING_OPENING_RANGE','SKIP_TINY_OPENING_RANGE')
FIELDS=('last_events','last_contracts','same_timestamp','same_timestamp_price_changes',
        'gaps_ge_60s','missing_5s_0800_1200','missing_5s_0940_1110',
        'missing_1m_0800_1200','five_s_0940_1110_fully_populated',
        'max_gap_100ns')

def check(cond,what):
    if not cond:raise ValueError('B05F_SOURCE_QC_REJECT: '+what)

def audit_stream(events,day):
    d=dev_day(day) # Always before consuming events, even generators.
    lo,hi=utc_bounds(d)
    bins5=[None]*N_BARS
    bins1=[None]*240
    totals=Counter()
    prev=None;prev_px=None
    # Reading source is streaming, no list of prints, no price exported.
    for ts,px,qty in events:
        check(type(ts) is int and lo<=ts<hi,'out of ET session')
        check(type(px) is int and px>0,'invalid price/tick')
        check(type(qty) is int and qty>0,'invalid Last contract quantity')
        check(prev is None or ts>=prev,'Last timestamps decreasing')
        if prev is not None:
            if ts==prev:
                totals['same_timestamp']+=1
                if px!=prev_px:totals['same_timestamp_price_changes']+=1
            else:
                gap=ts-prev
                totals['max_gap_100ns']=max(totals['max_gap_100ns'],gap)
                if gap>=600_000_000:totals['gaps_ge_60s']+=1
        i=(ts-lo)//STEP_100NS
        j=i//12
        check(0<=i<N_BARS and 0<=j<240,'bin range invalid')
        for arr,k in ((bins5,i),(bins1,j)):
            if arr[k] is None:arr[k]=Bar.start(px,qty,ts)
            else:arr[k].add(px,qty,ts)
        totals['last_events']+=1
        totals['last_contracts']+=qty
        prev=ts;prev_px=px
    check(totals['last_events']>0,'no Last events')
    # Exact OHLCV & print count consistency across independent groupings.
    grouped=consolidate_bars({i:b for i,b in enumerate(bins5) if b is not None},slot=12)
    for i in range(240):
        check(grouped.get(i)==bins1[i],'5s to 1m OHLCV conservation')
    check(sum(b.events for b in bins5 if b is not None)==totals['last_events'],
          '5s event count conservation')
    check(sum(b.qty for b in bins1 if b is not None)==totals['last_contracts'],
          '1m traded contracts conservation')
    counts=[b.events if b is not None else 0 for b in bins5]
    totals['missing_5s_0800_1200']=sum(v==0 for v in counts)
    totals['missing_5s_0940_1110']=sum(v==0 for v in counts[WINDOW_START:WINDOW_END])
    totals['missing_1m_0800_1200']=sum(b is None for b in bins1)
    totals['five_s_0940_1110_fully_populated']=int(
        totals['missing_5s_0940_1110']==0)
    if any(v==0 for v in counts[OR_START:OR_END]):
        state='SKIP_MISSING_OPENING_RANGE'
    else:
        opening=bins5[OR_START:OR_END]
        width=max(b.high for b in opening)-min(b.low for b in opening)
        state='READY' if width>=4 else 'SKIP_TINY_OPENING_RANGE'
    prefix=[0]
    for n in counts:prefix.append(prefix[-1]+n)
    readiness={str(length):{
        'ready_window_5s_decisions':sum(
            prefix[i+1]>=2*length for i in range(WINDOW_START,WINDOW_END)),
        'ready_at_0930':int(prefix[CUTOFFS['09:30']]>=2*length),
        'ready_at_1000':int(prefix[CUTOFFS['10:00']]>=2*length),
        'ready_at_1110':int(prefix[CUTOFFS['11:10']]>=2*length),
        'completed_bars_by_1110':prefix[CUTOFFS['11:10']]//length,
    } for length in LENGTHS}
    return {'state':state,'counters':dict(totals),
            'readiness':readiness,
            'window_decisions':WINDOW_BARS,
            'bars_5s_per_day':N_BARS,
            'holdouts_opened':False,
            'profits_computed':False}

def scan_day(root,day):
    d=dev_day(day) # Before file_for access and generator consumption.
    path=file_for(root,d,'Last')
    m=CONTRACT_RE.fullmatch(path.name)
    check(m is not None and m.group(2)==str(d.year) and
          m.group(3)==d.strftime('%Y%m%d'),'wrong quarter contract or date')
    return audit_stream(source_events(path),day)

def month_summary(month,days):
    check(month in MONTHS,'forbidden month')
    check(bool(days),'empty month')
    check(all(x['state'] in STATES and
           x['holdouts_opened'] is False and
           x['profits_computed'] is False for x in days),
          'invalid source day or holdout flag')
    merged=Counter()
    states=Counter(x['state'] for x in days)
    readiness={str(n):Counter() for n in LENGTHS}
    for d in days:
        merged.update({k:v for k,v in d['counters'].items()
                       if k!='max_gap_100ns'})
        merged['max_gap_100ns']=max(merged['max_gap_100ns'],
                                  d['counters'].get('max_gap_100ns',0))
        for n,values in d['readiness'].items():
            readiness[n].update(values)
    eligible=states['READY']
    return {'month':month,'status':'B05F_EXISTING_LAST_ONLY_QC',
            'source_days':len(days),'eligible_days':eligible,
            'excluded_days':len(days)-eligible,
            'skip_counts':{k:states[k] for k in STATES if k!='READY'},
            'qc_counters':{k:merged[k] for k in FIELDS},
            'context_availability':{n:dict(v) for n,v in readiness.items()},
            'total_5s_candidate_decisions':len(days)*WINDOW_BARS,
            'eligible_5s_candidate_decisions':eligible*WINDOW_BARS,
            'holdouts_opened':False,'trade_results_computed':False,
            'day_level_private_data_exported':False,
            'data_were_existing_private_Last_releases':True}

def run_month(root,month):
    if month not in MONTHS:raise ValueError('B05F_SEALED_MONTH_REJECTED')
    days=sorted(month_days(root,month))
    return month_summary(month,[scan_day(root,day) for day in days])

def aggregate(months):
    check(set(months)==set(MONTHS) and len(months)==7,
          'exactly 7 DEV months needed')
    for m in MONTHS:
        x=months[m]
        check(x['month']==m and x['status']=='B05F_EXISTING_LAST_ONLY_QC'
              and x['holdouts_opened'] is False
              and x['trade_results_computed'] is False
              and x['day_level_private_data_exported'] is False
              and x['data_were_existing_private_Last_releases'] is True,
              'malformed or unsafe month '+m)
        check(x['source_days']==x['eligible_days']+x['excluded_days'],
              'unreconciled month '+m)
        check(x['total_5s_candidate_decisions']==x['source_days']*WINDOW_BARS,
              'window count mismatch '+m)
    source=sum(months[m]['source_days'] for m in MONTHS)
    eligible=sum(months[m]['eligible_days'] for m in MONTHS)
    check((source,eligible)==(TOTAL_SOURCE,TOTAL_ELIGIBLE),
          'frozen 140 source /135 ready Last sample changed')
    skips=Counter()
    grand=Counter()
    avail={str(n):Counter() for n in LENGTHS}
    for m in MONTHS:
        x=months[m]
        skips.update(x['skip_counts'])
        for k,v in x['qc_counters'].items():
            if k=='max_gap_100ns':grand[k]=max(grand[k],v)
            else:grand[k]+=v
        for length,c in x['context_availability'].items():
            avail[length].update(c)
    check(sum(skips.values())==5,'five expected exclusion flags')
    check(grand['last_events']>0 and grand['last_contracts']>=grand['last_events'],
          'invalid print/qty conservation')
    check(grand['missing_5s_0940_1110']<=source*WINDOW_BARS,
          'missing 5s window count invalid')
    for length in LENGTHS:
        x=avail[str(length)]
        check(0<=x['ready_window_5s_decisions']<=source*WINDOW_BARS,
              'context readiness counter overflow '+str(length))
        for label in ('ready_at_0930','ready_at_1000','ready_at_1110'):
            check(0<=x[label]<=source,'anchor overflow '+label)
    return {
      'status':'B05F_COMPLETE_EXISTING_LAST_DATA_QC_NO_ALPHA',
      'source_months':list(MONTHS),'source_days':source,
      'eligible_days':eligible,'excluded_days':source-eligible,
      'source_excluded_reason_counts':dict(skips),
      'monthly':[months[m] for m in MONTHS],
      'grand_counters':dict(grand),
      'context_availability':{n:dict(x) for n,x in avail.items()},
      'window_5s_candidate_decisions':source*WINDOW_BARS,
      'context_lengths_last_prints':list(LENGTHS),
      'volume_qty_is_not_print_count':True,
      'quoted_endpoints_T05_do_not_change_baseline':True,
      'frozen_T05_trades_UNMODIFIED':115,
      'frozen_T05_stress_net_usd_REFERENCE_NOT_COMPUTED':5102.5,
      'frozen_T05_stress_plus10_pf_REFERENCE_NOT_COMPUTED':1.23717,
      'independent_NQ_minute_source_comparison_done':False,
      'broker_fills_verified':False,'new_history_acquired':False,
      'holdouts_opened':False,'trading_outcomes_computed':False,
      'raw_ticks_or_trade_level_published':False}

def report(r):
    out=['# NQ-B05F — Calidad objetiva de los ticks Last históricos YA almacenados',
      '',
      '**No se adquirió historial adicional. Sin backtest de rentabilidad,',
      'sin modificación de T05, sin OOS, sin certificación de fills.**',
      '',
      f"Universo DEV: **{r['source_days']} días fuente**, "
      f"**{r['eligible_days']} elegibles**, {r['excluded_days']} excluidos "
      'por reglas existentes antes de esta auditoría.',
      '',
      '| Mes | Días fuente | Elegibles | OR vacía | OR pequeña | Prints Last | 5s vacías 09:40–11:10 |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for m in r['monthly']:
        c=m['qc_counters'];sk=m['skip_counts']
        out.append(f"| {m['month']} | {m['source_days']} | {m['eligible_days']} | "
                   f"{sk.get('SKIP_MISSING_OPENING_RANGE',0)} | "
                   f"{sk.get('SKIP_TINY_OPENING_RANGE',0)} | "
                   f"{c['last_events']} | {c['missing_5s_0940_1110']} |")
    out+=['',
      '## Dos barras de N prints terminadas ANTES de la decisión (08:00 ET reset)',
      '',
      'Un tick-bar de 377 tiene 377 PRINTS Last, no 377 ticks de precio ni 377 contratos.',
      'Por cada día se evalúan 1080 cierres de 5s 09:40–11:10 ET; no se usan outcomes.',
      '',
      '| Longitud N prints | Decisiones de 5s con 2 barras completadas | Cobertura % | Días listos 09:30 | Días listos 10:00 | Días listos 11:10 |',
      '|---:|---:|---:|---:|---:|---:|']
    total=r['window_5s_candidate_decisions']
    for length in LENGTHS:
        c=r['context_availability'][str(length)]
        v=c['ready_window_5s_decisions']
        out.append(f"| {length} | {v} / {total} | {round(100*v/total,2)} | "
                   f"{c['ready_at_0930']} | {c['ready_at_1000']} | "
                   f"{c['ready_at_1110']} |")
    t=r['grand_counters']
    out+=['','## Integridad y límites','',
      f"- Total prints Last: **{t['last_events']}**, contratos qty: **{t['last_contracts']}**; ambos son magnitudes distintas.",
      f"- Timestamps Last repetidos: {t['same_timestamp']} (con precios distintos {t['same_timestamp_price_changes']}); empates NO prueban corrupción, pero prohíben inferir orden de exchange.",
      f"- Intervalos sin transacciones >=60s: {t['gaps_ge_60s']}. 5s vacías durante 09:40–11:10: {t['missing_5s_0940_1110']}; son huecos sin prints observados, NO prueba automática de ticks faltantes.",
      '- Validación de conservación OHLCV exacta entre 5s y 1m para el Last observado; **NO** comparación externa minuto NQ/MNQ del programa H.',
      '- Las 2 T05 sin BBO previo fresco permanecen en sus 115 fills sintéticos: un quote stale no invalida Last.',
      '- No autoriza simular True Delta, L2, agresor comprador/vendedor ni fills broker.',
      '- T05 histórico de comparación **no reejecutado**: 115 trades +$5.102,50 estrés, PF estrés+$10/RT 1,23717 FAIL. No indica que limpiar mejore rentabilidad.',
      '- Meses mayo–junio/julio–septiembre 2026 y old-H sealed siguen cerrados.',
      '',
      '## Decisión',
      '',
      'Usar exclusivamente ventanas/contextos causalmente completos, sin imputar ticks ni excluir operaciones por P&L; formular la siguiente hipótesis Last observable por mecanismo y con presupuesto de pruebas explícito, en otro bloque PRERREGISTRADO, sin declarar estrategia aprobada.']
    return '\n'.join(out)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path)
    p.add_argument('--month')
    p.add_argument('--inputs',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    if a.month is not None:
        if a.root is None or a.inputs is not None:raise SystemExit('Month requires root')
        result=run_month(a.root,a.month)
        label='B05F_MONTH_QC_SAFE='
    else:
        if a.inputs is None or a.root is not None or a.report is None:
            raise SystemExit('Aggregate requires inputs and report')
        rows={}
        for file in a.inputs.rglob('nq_b05f_*.json'):
            v=json.loads(file.read_text(encoding='utf8'))
            if v['month'] in rows:raise ValueError('Duplicate monthly QC')
            rows[v['month']]=v
        result=aggregate(rows)
        label='B05F_AGGREGATE_QC_SAFE='
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    if a.report is not None:a.report.write_text(report(result),encoding='utf8')
    print(label+json.dumps({'status':result['status'],
      'month':result.get('month'),'source_days':result['source_days'],
      'eligible_days':result['eligible_days'],
      'holdouts_opened':result['holdouts_opened']}))
