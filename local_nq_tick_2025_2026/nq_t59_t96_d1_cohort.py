#!/usr/bin/env python3
"""NQ 38-member T59...T96 D1 batch, preregistered BEFORE future outcomes.

Observational SAME-DEV, NOT trading. Full family BH38; no fill or PNL.
Must have verified T59...T96 38-member D0 31 diverse ≥20 before ANY I/O.
"""
from __future__ import annotations
import argparse,json
from bisect import bisect_left
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05,et_edge
from nq_b05h_atomic_print_bars import completed_bars_by_print_count
from nq_t61_t96_d0_cohort import IDS,NEW_IDS,load_registry,SOURCE,READY
from nq_t61_t96_d0_features import classify_day,summary,CASE,CONTROL,OTHER,MISSING
from nq_t59_t60_d0_premarket import classify as classify_old
from nq_t20_t25_d1_atomic_markout import (
    range_at_900,first_post_horizon_atomic_vwap,bootstrap_delta)

EXPECTED_PATH=Path(__file__).resolve().parents[1]/'research/nq/NQ_T59_T96_COHORT_D0_COUNTS_FROZEN_2026_10_12.json'
PRE_PATH=Path(__file__).resolve().parents[1]/'research/nq/NQ_T59_T96_COHORT_38_D1_PREREG_2026_10_12.md'
CLASSES=(CASE,CONTROL,OTHER,MISSING)
N_FAMILY=38

def d0_gate(path=EXPECTED_PATH):
    if not PRE_PATH.is_file():raise ValueError('D1_PREREG_MISSING')
    a=json.loads(path.read_text())
    cnt=a['case_control_other_missing']
    if (a.get('source')!=SOURCE or a.get('eligible')!=READY
        or a.get('anchors')!=READY or a.get('source_action_run')!=38313046875
        or a.get('source_artifact_id')!=11775368631
        or a.get('cohort_id')!='NQ-C59-NEXT'
        or a.get('D0_diverse_count',0)<20
        or a.get('D0_testable_count',0)<20
        or a.get('D1_executed') is not False or a.get('outcomes_read') is not False
        or a.get('holdouts_opened') is not False
        or a.get('D1_threshold_satisfied') is not True
        or a.get('all_ids')!=list(IDS)
        or set(cnt)!=set(IDS)
        or any(sum(cnt[k].values())!=READY or set(cnt[k])!=set(CLASSES) for k in IDS)
        or (cnt['T59'][CASE],cnt['T59'][CONTROL])!=(45,42)
        or (cnt['T60'][CASE],cnt['T60'][CONTROL])!=(71,6)):
        raise ValueError('D0_COHORT_GATE38_NOT_VERIFIED')
    return a

def bh38(ps):
    if len(ps)!=N_FAMILY or any(not 0<=v<=1 for v in ps):
        raise ValueError('COMPLETE_38_BH_REQUIRED')
    order=sorted(range(N_FAMILY),key=lambda k:ps[k])
    q=[None]*N_FAMILY
    m=1.
    for rank in range(N_FAMILY,0,-1):
        i=order[rank-1]
        m=min(m,ps[i]*N_FAMILY/rank)
        q[i]=m
    return q

def one_day(events,day,reg):
    dev_day(day)
    old=classify_old(events,day)
    new=classify_day(events,day,reg)
    groups={'T59':old['T59_PM_BODY_OPPOSITION'],
            'T60':old['T60_PM_VWAP_OPEN_DISLOCATION'],**new}
    if set(groups)!=set(IDS):raise AssertionError('38_NOT_PRESENT')
    bars=completed_bars_by_print_count(events,day,(377,))[377]
    lo,hi=et_edge(day,10,0),et_edge(day,10,15)
    ix=next((i for i,b in enumerate(bars) if lo<=b.end_timestamp<hi),None)
    if ix is None or ix<4:raise AssertionError('FROZEN_ANCHOR_PARITY_FAIL')
    E,D=bars[ix],bars[ix-1]
    vE=Q(E.price_times_qty_ticks,E.total_qty)
    vD=Q(D.price_times_qty_ticks,D.total_qty)
    side=(vE>vD)-(vE<vD)
    times=[z[0] for z in events]
    vfuture=first_post_horizon_atomic_vwap(events,times,E.end_timestamp+300*10_000_000)
    premkt_clock=et_edge(day,9,45)
    o1=summary(events[bisect_left(times,et_edge(day,9,30)):bisect_left(times,premkt_clock)])
    if o1 is None:raise AssertionError('PREREG_OPEN_15_MISSING')
    o1side=(o1['end']>o1['open'])-(o1['end']<o1['open'])
    vfuture_early=first_post_horizon_atomic_vwap(events,times,premkt_clock+300*10_000_000)
    range_early=range_at_900(events,times,premkt_clock)
    vals={}
    for id_ in IDS:
        label=groups[id_]
        if label not in CLASSES:raise ValueError('BAD_CATEGORY')
        if label not in (CASE,CONTROL):
            value=None;local_side=0
        elif id_=='T59':
            local_side=o1side
            value=float(local_side*(vfuture_early-o1['end'])) if local_side else None
        elif id_=='T60':
            local_side=0;value=float(range_early)
        else:
            local_side=side
            value=float(local_side*(vfuture-vE)) if local_side else None
        vals[id_]={'group':label,'side':local_side,'value':value}
    return vals

def month_stage(root,month,out,reg,expected):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_BEFORE_IO')
    if out.exists():raise ValueError('PRIVATE_DAILY_ROWS_CANNOT_OVERWRITE')
    qc=Counter();totals={k:Counter() for k in IDS};daily=[];nsource=0
    for day in sorted(month_days(root,month)):
        date=dev_day(day);nsource+=1
        e=list(source_events(file_for(root,date,'Last')))
        status,_,_=frozen_t05(e,day)
        qc[status]+=1
        if status!='READY':continue
        outcome=one_day(e,day,reg)
        daily.append(outcome)
        for k,x in outcome.items():totals[k][x['group']]+=1
    if sum(qc.values())!=nsource or len(daily)!=qc['READY']:
        raise AssertionError('MISSING_ANY_READY_DAY')
    if any(sum(totals[k].values())!=qc['READY'] for k in IDS):
        raise AssertionError('FAMILY_MEMBER_DROPPED')
    out.parent.mkdir(parents=True,exist_ok=True)
    payload={'stage':'T59_T96_D1_PRIVATE_38_FULL_NO_TRADES',
      'month':month,'source':nsource,'eligible':qc['READY'],
      'counts':{k:{g:totals[k][g] for g in CLASSES} for k in IDS},
      'daily':daily,'trades_simulated':0,'PnL':None,'PF':None,'DD':None,
      'broker_fills_verified':False,'individual_outcomes_public':False,
      'holdouts_opened':False,'new_history_acquired':False,
      'new_five_second_signals':False}
    out.write_text(json.dumps(payload,separators=(',',':'))+'\n')
    return {'month':month,'source':nsource,'eligible':qc['READY'],
            'private_vectors_only':True,'N_trades':0,'PnL':None}

def aggregate(months,reg,expected):
    if set(months)!=set(MONTHS):raise ValueError('REQUIRES_EXACTLY_SEVEN_MONTHS')
    total={k:Counter() for k in IDS};rows=[];src=ready=0
    per_month=[]
    for m in MONTHS:
        x=months[m]
        if (x['stage']!='T59_T96_D1_PRIVATE_38_FULL_NO_TRADES'
            or x['month']!=m or set(x['counts'])!=set(IDS)
            or x['trades_simulated']!=0 or x['PnL'] is not None
            or x['PF'] is not None or x['DD'] is not None
            or any(x[k] is not False for k in ('broker_fills_verified',
               'individual_outcomes_public','holdouts_opened','new_history_acquired',
               'new_five_second_signals'))
            or x['eligible']!=len(x['daily'])):
            raise ValueError('INVALID_PRIVATE_D1_SOURCE')
        src+=x['source'];ready+=x['eligible']
        rows.extend(x['daily'])
        for k in IDS:
            if set(x['counts'][k])!=set(CLASSES) or sum(x['counts'][k].values())!=x['eligible']:
                raise AssertionError('BAD_MONTH_LABELS')
            total[k].update(x['counts'][k])
        per_month.append({'month':m,'source':x['source'],'eligible':x['eligible'],
          'N_case_control':{k:[x['counts'][k][CASE],x['counts'][k][CONTROL]] for k in IDS}})
    if (src,ready,len(rows))!=(SOURCE,READY,READY):
        raise AssertionError('BASELINE_140_135_CHANGED')
    for k in IDS:
        if any(total[k][g]!=expected['case_control_other_missing'][k][g] for g in CLASSES):
            raise AssertionError('CANNOT_CHANGE_D0_CASE_CONTROL_AFTER_READING_RETURNS')
    results={};ps=[]
    for k in IDS:
        sample={g:[r[k]['value'] for r in rows if r[k]['group']==g and r[k]['value'] is not None]
                for g in (CASE,CONTROL)}
        means={g:sum(sample[g])/len(sample[g]) if sample[g] else None
               for g in (CASE,CONTROL)}
        delta=means[CASE]-means[CONTROL] if all(means[g] is not None for g in (CASE,CONTROL)) else None
        boot={str(L):bootstrap_delta(rows,k,L) for L in (3,5,10)}
        p=boot['5']['p_exploratory']
        ps.append(p if p is not None else 1.)
        results[k]={'N_case':total[k][CASE],'N_control':total[k][CONTROL],
          'N_case_observed':len(sample[CASE]),'N_control_observed':len(sample[CONTROL]),
          'mean_case':means[CASE],'mean_control':means[CONTROL],
          'delta_ticks':delta,'CI90_L3_L5_L10':boot,
          'p_L5_exploratory':p,'p1_sentinel_for_BH':p is None,
          'endpoint':'NQ_RANGE15M_EARLY_CONTEXT_ONLY' if k=='T60' else
                     'NQ_VWAP_SIGNED_MARKOUT_300S_NO_FILL',
          'N_trades':0,'PnL':None,'PF':None,'DD':None,
          'DeltaRouter':None,'Holm':None}
    q=bh38(ps)
    for i,k in enumerate(IDS):
        x=results[k];ci=x['CI90_L3_L5_L10']['5']['ci90']
        x['q_BH38_exploratory']=None if x['p1_sentinel_for_BH'] else q[i]
        if ci is None:x['D1']='NOT_ESTIMABLE'
        elif x['delta_ticks']<=0:x['D1']='NOT_SUPPORTED_DESCRIPTIVE'
        elif ci[0]<=0 or q[i]>.10:x['D1']='INCONCLUSIVE'
        else:x['D1']='PREDICTIVE_SHORTLIST_CONTEXT_ONLY' if k=='T60' else 'PREDICTIVE_SHORTLIST_NO_FILL'
    return {'stage':'NQ_T59_T96_D1_ALL38_COMPLETE_EXPLORATORY',
      'prereg_id':reg['prereg_id'],'D0_action':expected['source_action_run'],
      'family_size':38,'source_sessions':src,'eligible_sessions':ready,
      'results':results,'months':per_month,
      'shortlist_predictive_ids':[k for k,x in results.items() if x['D1'].startswith('PREDICTIVE_SHORTLIST')],
      'context_ids':[k for k,x in results.items() if x['D1']=='PREDICTIVE_SHORTLIST_CONTEXT_ONLY'],
      'economic_screen_pass_ids':[],
      'N_trades':0,'PnL':None,'PF':None,'DD':None,'DeltaRouter':None,
      'Holm_confirmatory':None,'broker_fills_verified':False,
      'holdouts_opened':False,'new_history_acquired':False,
      'individual_outcomes_public':False,
      'adaptive_DEV_not_confirmatory':True}

def report(z):
    f=lambda v:'N/D' if v is None else f'{v:+.3f}'
    s=['# NQ C59–C96 — D1 COMPLETO 38 hipótesis (NO trading)',
       '',f"Fuente {z['source_sessions']} / DEV READY {z['eligible_sessions']} sesiones.",
       'T59 VWAP firmado a +300s desde 09:45; T60 RANGO15min desde 09:45;',
       'T61–T96 VWAP firmado a +300s desde fin de E 377 bar, lado E−D;',
       '**q BH38 EXPLORATORIA** de TODOS los 38, incluidos 2 insuficientes D0.',
       'IC90 L5 bootstrap 10k con sensibilidad L3 y L10; no Holm/OOS.',
       '', '| ID | N caso/control | Efecto Δ ticks | IC90 L5 ticks | p/q BH38 | D1 |',
       '|---|---:|---:|---|---|---|']
    for k,x in z['results'].items():
        ci=x['CI90_L3_L5_L10']['5']['ci90']
        cis='['+f(ci[0])+', '+f(ci[1])+']' if ci else 'N/D'
        s.append(f"| {k} | {x['N_case']}/{x['N_control']} | "
          f"{f(x['delta_ticks'])} | {cis} | "
          f"{f(x['p_L5_exploratory'])}/{f(x['q_BH38_exploratory'])} | {x['D1']} |")
    s+=['',
      f"**D1 filtros de signo+IC90+q_BH38 aprobados (exploratorios): {len(z['shortlist_predictive_ids'])}**. "
       'Todas las shortlist siguen sin fills reales ni economía neta.',
      '**Etapa D2 NO desbloqueada:** no trades, USD, PF, DD, costos, DeltaRouter verificables, '
      'ni Holm confirmatorio. Markouts son aproximaciones físicas y T60 rango no direccional.',
      'N trades=0, neto/PF/DD/ROI/OOS/beneficio fondeo=N/D. '
      'No promover sin plan de ejecución independiente.','']
    return '\n'.join(s)

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--root',type=Path)
    a.add_argument('--month')
    a.add_argument('--inputs',type=Path)
    a.add_argument('--out',type=Path,required=True)
    a.add_argument('--report',type=Path)
    q=a.parse_args()
    expected=d0_gate()
    reg=load_registry()
    if q.month:
        if q.month not in MONTHS:raise SystemExit('SEALED_MONTH_BEFORE_IO')
        result=month_stage(q.root,q.month,q.out,reg,expected)
        print('NQ_T59_T96_D1_PRIVATE_MONTH='+json.dumps(result,sort_keys=True))
    else:
        if not q.inputs or not q.report:raise ValueError('aggregate requires months and report')
        ms={m:json.loads((q.inputs/f't59_t96_d1_{m}.json').read_text())
            for m in MONTHS}
        result=aggregate(ms,reg,expected)
        q.out.parent.mkdir(parents=True,exist_ok=True)
        q.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        q.report.write_text(report(result)+'\n')
        print('NQ_T59_T96_D1_FINAL='+json.dumps({
          'source':result['source_sessions'],'eligible':result['eligible_sessions'],
          'family':38,'D1_statuses':dict(Counter(x['D1'] for x in result['results'].values())),
          'predictive_shortlist':result['shortlist_predictive_ids'],
          'economic_pass_ids':[], 'future_private':True,'N_trades':0},sort_keys=True))
