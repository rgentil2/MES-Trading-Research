#!/usr/bin/env python3
"""Full original 36 members economic D1, 7 DEV months, conservative Last PROXY.

NO broker fills! Prereg (before future PnL), 27-diverse gate & old20 frozen
parity are enforced before reading any market source. All day/trade-level
information remains private in ONE GH runner; only SAFE aggregates uploaded.
"""
from __future__ import annotations
import argparse,json,random,math
from collections import Counter,defaultdict
from pathlib import Path
from datetime import date

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05
from nq_t133_t168_combined_D0_batch import (
    OLD_IDS,NEW_IDS,IDS,SOURCE,READY,load_new,old_registry)
from nq_t133_t168_d1_engine import day_sim
from nq_t153_t168_executable_d0_features import CASE,CONTROL,OTHER,MISSING,LABELS

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/'research/nq/NQ_T133_T168_36_MEMBER_D0_FROZEN_COUNTS_2026_10_12.json'
PREREG=ROOT/'research/nq/NQ_T133_T168_36_MEMBER_ECONOMIC_D1_PREREG_2026_10_12.md'
B=10000
FAMILY_SIZE=36

def gate(path=FROZEN):
    if not PREREG.is_file():raise ValueError('ECONOMIC_D1_PREREG_MISSING')
    x=json.loads(path.read_text())
    if (x.get('cohort_id')!='NQ-C133-168'
        or x.get('frozen_after_complete_action')!=38325498797
        or x.get('seed_source_action')!=38324292967
        or x.get('seed_20_masks_identical') is not True
        or x.get('family_size')!=36
        or x.get('all_ids')!=list(IDS)
        or (x.get('source'),x.get('eligible'))!=(SOURCE,READY)
        or x.get('D0_testable_count')!=29
        or x.get('D0_diverse_count')!=27
        or x.get('D1_20_gate') is not True
        or len(x.get('D0_testable_ids',[]))!=29
        or len(x.get('D0_diverse_ids',[]))!=27
        or x.get('D1_executed') is not False
        or x.get('future_outcomes_read') is not False
        or x.get('holdouts_opened') is not False
        or set(x.get('case_control_other_missing',{}))!=set(IDS)
        or any(set(x['case_control_other_missing'][k])!=set(LABELS)
             or sum(x['case_control_other_missing'][k].values())!=READY for k in IDS)):
        raise ValueError('FROZEN_36_D0_GATE_NOT_PASSED_OR_TAMPERED')
    return x

def mean(v):return sum(v)/len(v) if v else None

def quantile(s,q):
    if not s:return None
    i=(len(s)-1)*q;lo=int(i);hi=min(lo+1,len(s)-1);w=i-lo
    return s[lo]*(1-w)+s[hi]*w

def boot_mean(y,id_,L):
    if len(y)!=READY:raise ValueError('BOOTSTRAP_MUST_INCLUDE_135_SESSIONS')
    if L not in (3,5,10):raise ValueError('INVALID_BLOCK_LENGTH')
    m=sum(y)/len(y)
    bsum=[sum(y[i:i+L]) for i in range(len(y)-L+1)]
    rnd=random.Random(127900+int(id_[1:])*31+L*112)
    n=len(y);b=[];nb=(n+L-1)//L
    for _ in range(B):
        val=sum(bsum[rnd.randrange(len(bsum))] for j in range(nb))
        extra=nb*L-n
        if extra:
            i=rnd.randrange(len(bsum))
            # deterministic random partial block at end, no circular wrapping
            val-=sum(y[i:i+extra])
        b.append(val/n)
    b.sort()
    lo,hi=quantile(b,.05),quantile(b,.95)
    # H0 distribution is the centered resampling distribution; unilateral >0.
    p=(sum(x-m>=m for x in b)+1)/(B+1)
    return {'ci90':[lo,hi],'p_exploratory':p,'L':L,'B':B}

def bh_family(ps):
    if len(ps)!=FAMILY_SIZE or any(not 0<=p<=1 for p in ps):
        raise ValueError('ALL_36_ORIGINAL_REQUIRED_FOR_BH')
    order=sorted(range(FAMILY_SIZE),key=lambda i:ps[i])
    q=[None]*FAMILY_SIZE
    running=1.
    for rank in range(FAMILY_SIZE,0,-1):
        j=order[rank-1]
        running=min(running,ps[j]*FAMILY_SIZE/rank)
        q[j]=running
    return q

def month_stage(root,month,out,old,new):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_BEFORE_IO')
    if out.exists():raise ValueError('PRIVATE_MONTH_NO_OVERWRITE')
    qc=Counter();nsource=0;daily=[];counts={k:Counter() for k in IDS}
    for day in sorted(month_days(root,month)):
        dd=dev_day(day);nsource+=1
        e=list(source_events(file_for(root,dd,'Last')))
        status,_,_=frozen_t05(e,day)
        qc[status]+=1
        if status!='READY':continue
        result=day_sim(e,day,old,new)
        if set(result)!=set(IDS):raise AssertionError('D1_36_ENTIRE_FAMILY_REQUIRED')
        for k,v in result.items():
            counts[k][v['group']]+=1
        daily.append({'date':day,'proxies':result})
    if sum(qc.values())!=nsource or qc['READY']!=len(daily):
        raise AssertionError('MONTH_DAY_QC_MISMATCH')
    x={'stage':'PRIVATE_ALL36_MODELLED_D1_UNVERIFIED',
      'month':month,'source':nsource,'eligible':len(daily),
      'counts':{k:{g:counts[k][g] for g in LABELS} for k in IDS},
      'daily':daily,'new_history':False,'sealed_opened':False,
      'broker_fills_verified':False,'individual_modelled_trades_public':False,
      'new_5s_signals':False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(x,separators=(',',':'))+'\n')
    return {'month':month,'source':nsource,'eligible':len(daily),'private_only':True}

def drawdown(series):
    equity=peak=dd=0.
    for x in series:
        equity+=x;peak=max(peak,equity);dd=min(dd,equity-peak)
    return -dd

def aggregate(months,old,new,frozen):
    if set(months)!=set(MONTHS):raise ValueError('NEED_ALL_SEVEN_DEV_MONTHS')
    raw=[];src=ready=0;totals={k:Counter() for k in IDS};coverage=[]
    for m in MONTHS:
        z=months[m]
        if (z.get('stage')!='PRIVATE_ALL36_MODELLED_D1_UNVERIFIED'
            or z.get('month')!=m
            or z.get('eligible')!=len(z['daily'])
            or set(z.get('counts',{}))!=set(IDS)
            or any(z[k] is not False for k in ('new_history','sealed_opened',
             'broker_fills_verified','individual_modelled_trades_public',
             'new_5s_signals'))):
            raise ValueError('UNSAFE_OR_INCOMPLETE_PRIVATE_RUN')
        src+=z['source'];ready+=z['eligible']
        for k in IDS:
            if set(z['counts'][k])!=set(LABELS) or sum(z['counts'][k].values())!=z['eligible']:
                raise AssertionError('MISSING_MEMBER_LABEL')
            totals[k].update(z['counts'][k])
        raw.extend(z['daily'])
        coverage.append({'month':m,'source':z['source'],'eligible':z['eligible']})
    if (src,ready,len(raw))!=(SOURCE,READY,READY):
        raise AssertionError('FINAL_140_135_PARITY_FAIL')
    for k in IDS:
        if any(totals[k][g]!=frozen['case_control_other_missing'][k][g] for g in LABELS):
            raise AssertionError('FROZEN_D0_MASK_CHANGED_AFTER_ECONOMIC_OUTCOME_READ: '+k)
    if [r['date'] for r in raw]!=sorted(r['date'] for r in raw):
        raise AssertionError('CHRONOLOGICAL_ORDER_WRONG')
    members={z['id']:z for z in old['members']+new['members']}
    results={};ps=[]
    for k in IDS:
        dayvals=[];tradevals=[];stressvals=[];plusvals=[];permonth=defaultdict(list)
        rejections=Counter();instruments=Counter();reasons=Counter()
        weeks=set();cases=totals[k][CASE]
        for record in raw:
            z=record['proxies'][k]
            if z['group'] not in LABELS:raise AssertionError('D0_GROUP_BAD')
            state=z['status'];rejections[state]+=1
            if state=='MODELLED_EXECUTION_UNVERIFIED':
                v=z['net_usd'];tradevals.append(v)
                stressvals.append(z['stress_1_5x_usd'])
                plusvals.append(z['stress_plus_10_rt_usd'])
                instruments[z['instrument']]+=1
                reasons[z['exit_reason']]+=1
                iso=date.fromisoformat(record['date']).isocalendar()
                weeks.add((iso.year,iso.week))
            elif state=='NO_CAUSAL_TRIGGER':
                v=0.
            else:
                v=0.
            dayvals.append(v);permonth[record['date'][:7]].append(v)
        n=len(tradevals)
        if n>=15:
            boot={str(L):boot_mean(dayvals,k,L) for L in (3,5,10)}
            primary=boot['5'];p=primary['p_exploratory']
        else:
            boot={str(L):{'ci90':None,'p_exploratory':None,'L':L,'B':B}
                  for L in (3,5,10)}
            p=None
        ps.append(p if p is not None else 1.)
        wins=sum(x for x in tradevals if x>0)
        losses=sum(x for x in tradevals if x<0)
        pf=wins/-losses if losses<0 else None
        season=sum(dayvals[:53]),sum(dayvals[53:])
        nmonth={m:len(permonth.get(m,[])) for m in MONTHS}
        month_net={m:sum(permonth.get(m,[])) for m in MONTHS}
        positive_months=[v for v in month_net.values() if v>0]
        largest_month_pos=max(positive_months)/sum(positive_months) if positive_months else None
        results[k]={'block':members[k]['block'],'question':members[k]['question'],
          'N_case_D0':cases,'N_control_D0':totals[k][CONTROL],
          'N_proxy_trades':n,'N_active_weeks_proxy':len(weeks),
          'N_sessions':READY,'instruments':dict(instruments),
          'proxy_exit_reasons':dict(reasons),
          'statuses':dict(rejections),
          'win_rate':sum(v>0 for v in tradevals)/n if n else None,
          'net_total_usd':sum(tradevals),'net_expectancy_per_proxy_trade_usd':mean(tradevals),
          'net_daily_usd':mean(dayvals),
          'net_stress_1_5x_total_usd':sum(stressvals),
          'net_stress_plus_10_rt_usd':sum(plusvals),
          'PF_proxy':pf,'maxDD_proxy_usd':drawdown(dayvals),
          'diagnostic_oct_dec_2025_net':season[0],
          'internal_jan_apr_2026_net':season[1],
          'monthly_net_usd':month_net,
          'month_positive_concentration':largest_month_pos,
          'CI90_L3_L5_L10':boot,'p_exploratory':p,
          'q_BH36':None,'Holm_confirmatory':None,
          'broker_fills_verified':False,'D2':'BLOCKED_UNVERIFIED_EXECUTION'}
    q=bh_family(ps)
    for i,k in enumerate(IDS):
        z=results[k];n=z['N_proxy_trades'];ci=z['CI90_L3_L5_L10']['5']['ci90']
        z['q_BH36']=None if z['p_exploratory'] is None else q[i]
        if n<15 or ci is None:
            z['D1']='NOT_ESTIMABLE_LOW_PROXY_FREQUENCY'
        elif z['net_expectancy_per_proxy_trade_usd']<=0 or z['net_total_usd']<=0:
            z['D1']='NOT_SUPPORTED_NET'
        elif (ci[0]<=0 or q[i]>.10 or z['PF_proxy'] is None or
              z['PF_proxy']<1.25 or z['net_stress_1_5x_total_usd']<=0 or
              z['net_stress_plus_10_rt_usd']<=0 or
              z['diagnostic_oct_dec_2025_net']<=0 or
              z['internal_jan_apr_2026_net']<=0 or
              z['maxDD_proxy_usd']>1500 or
              z['month_positive_concentration'] is None or
              z['month_positive_concentration']>=.40):
            z['D1']='INCONCLUSIVE_OR_GATE_FAIL'
        else:
            z['D1']='PASS_EXPLORATORY_MODELLED_ONLY_NO_BROKER_FILL'
    return {'stage':'T133_T168_D1_ECONOMIC_PROXIES_FULL36_DEV_UNVERIFIED',
      'prereg':'NQ_T133_T168_36_MEMBER_ECONOMIC_D1_PREREG_2026_10_12.md',
      'D0_action':frozen['frozen_after_complete_action'],
      'source':src,'eligible':ready,'family_size':FAMILY_SIZE,
      'model':'MARKET_PROXY_WORST_NEXT_ATOMIC_LAST_PLUS_2_TICKS_PER_SIDE',
      'cost_NQ_rt_usd_assumed':4,'cost_MNQ_rt_usd_assumed':1.5,
      'results':results,'months':coverage,
      'D1_exploratory_pass_ids':[k for k in IDS if
          results[k]['D1'].startswith('PASS_EXPLORATORY')],
      'economic_confirmatory_pass_ids':[],
      'broker_fills_verified':False,'not_OOS_confirmed':True,
      'last_only':True,'holdouts_opened':False,'new_data':False,
      'individual_modelled_trades_public':False,
      'Holm_confirmatory':None,'DeltaRouter':None}

def report(z):
    f=lambda x:'N/D' if x is None else f'{x:+.2f}'
    lines=['# NQ T133–T168 — D1 ECONÓMICA PROXY k36 COMPLETO',
       '',f"Fuente {z['source']} READY {z['eligible']}, mismos 7 DEV.",
       '**FILL SOLO SIMULADO con Last**, peor grupo atómico siguiente +2 ticks '
       'slippage por entrada y salida, stop FIRST ante empate temporal; '
       'NQ fee supuesto $4 RT, MNQ $1,50 RT; dos estrés 1,5x/+10.',
       'IC90 bootstrap 10.000 L5 primario, L3/L10; BH completa 36.',
       'Segmentación 2025-Q4 / 2026-Jan-Apr INTERNA, NO OOS.',
       '', '| ID | Bloque | N trades proxy | Neto USD proxy | PF | DD USD | IC90 diario L5 USD | q BH36 | D1 |',
       '|---|---|---:|---:|---:|---:|---|---:|---|']
    for k,v in z['results'].items():
        ci=v['CI90_L3_L5_L10']['5']['ci90']
        lines.append(f"| {k} | {v['block']} | {v['N_proxy_trades']} | "
          f"{f(v['net_total_usd'])} | {f(v['PF_proxy'])} | "
          f"{f(v['maxDD_proxy_usd'])} | "
          f"{'['+f(ci[0])+','+f(ci[1])+']' if ci else 'N/D'} | "
          f"{f(v['q_BH36'])} | {v['D1']} |")
    lines+=['',f"**PASS exploratorias sobre grupo Last hipotético: "
         f"{len(z['D1_exploratory_pass_ids'])}**; supervivientes "
         'confirmatorias y ejecutables broker: **0**.',
         '**D2 NO se activa automáticamente**: sin spread, prioridades ni '
         'broker fills verificados, Holm confirmatoria/OOS/ROI independiente N/D.',
         'Los retornos y PF son solo de un MODELO de fricción conservadora, '
         'NO evidencia de ganancias del usuario.','']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path);p.add_argument('--month')
    p.add_argument('--inputs',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path);a=p.parse_args()
    frozen=gate();old=old_registry();new=load_new()
    if a.month:
        if a.month not in MONTHS:raise SystemExit('SEALED_MONTH_BEFORE_IO')
        result=month_stage(a.root,a.month,a.out,old,new)
        print('NQ_ECONOMIC_D1_PRIVATE_MONTH='+json.dumps(result,sort_keys=True))
    else:
        if not a.inputs or not a.report:raise ValueError('requires input/report')
        ms={m:json.loads((a.inputs/f't133_t168_d1_{m}.json').read_text())
            for m in MONTHS}
        result=aggregate(ms,old,new,frozen)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        a.report.write_text(report(result)+'\n')
        print('NQ_ECONOMIC_D1_SAFE_FINAL='+json.dumps({
          'source':result['source'],'eligible':result['eligible'],
          'statuses':dict(Counter(v['D1'] for v in result['results'].values())),
          'BH_qmin':min((v['q_BH36'] for v in result['results'].values()
             if v['q_BH36'] is not None),default=None),
          'D1_exploratory_pass_ids':result['D1_exploratory_pass_ids'],
          'economic_confirmatory_pass_ids':[],
          'broker_fills_verified':False},sort_keys=True))
