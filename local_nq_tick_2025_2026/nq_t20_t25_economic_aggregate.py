#!/usr/bin/env python3
"""T20–T25 stage1: fail-closed seven-month private outcomes -> SAFE aggregate only.
No licensed Last, timestamps, trade logs, or daily PnL in published output.
"""
from __future__ import annotations
import argparse,json,math,random,statistics
from pathlib import Path
from collections import Counter
from nq_tick_short_horizon_month import MONTHS
from nq_b03_aggregate import stitch
from nq_b05k_t05_daily_block_bootstrap import moving_block_stats
from nq_t20_t25_fixed_anchor_screen import IDS,CASE,CONTROL,OTHER,MISSING
from nq_t20_t25_economic_month import (
    BASE,MAG,DIRECTIONAL,MODELS,CASE_NAMES,CTRL_NAMES,ROUTERS,
    SCREEN_COUNTS,EXPECTED)

REPS=10000
LENGTHS=(3,5,10)
MIN_GROUP=15
BASE_SEED=20261012

def as_cents(value):
    if not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('not finite money')
    c=round(value*100)
    if abs(c/100-value)>1e-5:
        raise ValueError('not cents')
    return c

def quantile(array,alpha):
    if not array:
        raise ValueError('empty quantile')
    pos=(len(array)-1)*alpha
    a=math.floor(pos);b=math.ceil(pos)
    return array[a]+(array[b]-array[a])*(pos-a)

def bh(p):
    if set(p)!=set(IDS) or len(p)!=6:
        raise ValueError('exact six-member family required')
    if any(not isinstance(v,(int,float)) or not 0<=v<=1
           for v in p.values()):
        raise ValueError('invalid p value')
    keys=sorted(p,key=p.get)
    q={}
    bound=1.
    for i in range(5,-1,-1):
        k=keys[i]
        bound=min(bound,6*p[k]/(i+1))
        q[k]=round(bound,6)
    return q

def comparison_bootstrap(entries,length,seed,reps=REPS,minimum=MIN_GROUP):
    """Entries are PRIVATE (case_sum,case_count,control_sum,control_count) per day.

    Repeated sessions are grouped into noncircular blocks; within-day case/control
    covariation is preserved. Output is only aggregate means/CI/p.
    """
    if len(entries)!=135 or not 2<=length<=135 or reps<100:
        raise ValueError('invalid bootstrap domain')
    if any(len(e)!=4 or any(not math.isfinite(x) for x in e)
           for e in entries):
        raise ValueError('invalid daily observation')
    cs=sum(x[0] for x in entries)
    cn=sum(x[1] for x in entries)
    ds=sum(x[2] for x in entries)
    dn=sum(x[3] for x in entries)
    if cn<minimum or dn<minimum:
        return {'status':'UNDERPOWERED_OR_UNIDENTIFIABLE',
                'N_case_executions':cn,'N_control_executions':dn,
                'effect_mean_case_minus_control':(round(cs/cn-ds/dn,4)
                                                  if cn and dn else None),
                'CI90':None,'p_unilateral_centered':None,
                'bootstrap_n':0}
    observed=cs/cn-ds/dn
    rng=random.Random(seed)
    n=len(entries)
    valid=[]
    for _ in range(reps):
        acc=[0.,0,0.,0]
        remain=n
        while remain:
            idx=rng.randrange(n-length+1)
            take=min(length,remain)
            for row in entries[idx:idx+take]:
                for i in range(4):
                    acc[i]+=row[i]
            remain-=take
        if acc[1] and acc[3]:
            valid.append(acc[0]/acc[1]-acc[2]/acc[3])
    coverage=len(valid)/reps
    if coverage<.90:
        return {'status':'BOOTSTRAP_GROUP_COVERAGE_INSUFFICIENT',
                'N_case_executions':cn,'N_control_executions':dn,
                'effect_mean_case_minus_control':round(observed,4),
                'CI90':None,'p_unilateral_centered':None,
                'bootstrap_n':len(valid),'bootstrap_fraction_with_two_groups':round(coverage,5)}
    valid.sort()
    low,high=quantile(valid,.05),quantile(valid,.95)
    p=(1+sum(z-observed>=observed for z in valid))/(len(valid)+1)
    return {'status':'IN_SAMPLE_EXPLORATORY_ONLY',
            'N_case_executions':cn,'N_control_executions':dn,
            'effect_mean_case_minus_control':round(observed,4),
            'CI90':[round(low,4),round(high,4)],
            'bootstrap_se':round(statistics.stdev(valid),4),
            'p_unilateral_centered':round(p,6),
            'bootstrap_n':len(valid),
            'bootstrap_fraction_with_two_groups':round(coverage,5),
            'seed':seed,'L':length,'p_is_confirmatory':False}

def validate(months):
    if set(months)!=set(MONTHS):
        raise ValueError('all seven DEV months needed')
    source=eligible=0
    records=[]
    cases={k:Counter() for k in IDS}
    magnitudes={CASE:{'n':0,'sum_ticks':0},
                CONTROL:{'n':0,'sum_ticks':0}}
    for month in MONTHS:
        z=months[month]
        safe=z['safe']
        if (safe['month']!=month
            or safe['status']!='T20_T25_STAGE1_DEV_PRIVATE_OUTCOMES'
            or set(safe['models'])!=set(MODELS)
            or set(safe['category_counts'])!=set(IDS)
            or safe['source']!=len(z['private_daily'])
            or safe['source']!=safe['eligible']+safe['not_eligible']
            or any(safe[k] is not False for k in
                   ('holdouts_opened','new_history_acquired',
                    'five_second_new_signals','broker_fill_verified',
                    'daily_or_trade_rows_public'))):
            raise ValueError('untrusted or incomplete monthly stage1 result')
        source+=safe['source'];eligible+=safe['eligible']
        for key in IDS:
            kinds=safe['category_counts'][key]
            if set(kinds)!={CASE,CONTROL,OTHER,MISSING} or sum(kinds.values())!=safe['eligible']:
                raise ValueError('missing category/invalid stage0 counts')
            cases[key].update(kinds)
        for kind in (CASE,CONTROL):
            zz=safe['magnitude'][kind]
            if zz['n']<0 or zz['sum_ticks']<0:
                raise ValueError('invalid magnitude')
            magnitudes[kind]['n']+=zz['n']
            magnitudes[kind]['sum_ticks']+=zz['sum_ticks']
        if (safe['models'][BASE]['trades'],safe['models'][BASE]['net_usd'])!=EXPECTED[month]:
            raise AssertionError('changed frozen T05 month')
        for day in z['private_daily']:
            if day['day'][:7]!=month:
                raise ValueError('private month mismatch')
            if not day['eligible']:
                if set(day)!={'day','eligible'}:
                    raise ValueError('excluded day leaked label or outcome')
                continue
            if set(day['labels'])!=set(IDS) or set(day['models'])!=set(MODELS):
                raise ValueError('missing private label/model')
            for name in MODELS:
                row=day['models'][name]
                if (row['trades'] not in (0,1,2) or
                    row['extra_cents']!=row['stress_cents']-1000*row['trades']):
                    raise AssertionError('invalid daily trades/cost parity')
            records.append(day)
    if (source,eligible,len(records))!=(140,135,135):
        raise ValueError('140/135 parity failed')
    if [z['day'] for z in records]!=sorted(z['day'] for z in records):
        raise ValueError('private daily timeline unsorted')
    for k in IDS:
        if (cases[k][CASE],cases[k][CONTROL])!=SCREEN_COUNTS[k]:
            raise AssertionError('stage0 case/control changed')
        if cases[k][MISSING]:
            raise AssertionError('stage0 all 135 anchors required')
    if magnitudes[CASE]['n']!=cases[MAG][CASE] or magnitudes[CONTROL]['n']!=cases[MAG][CONTROL]:
        raise AssertionError('T23 future magnitude not fully covered')
    return records, cases, magnitudes, source, eligible

def aggregate(months):
    records,cases,magnitude,source,eligible=validate(months)
    models={};daily={}
    for name in MODELS:
        entries=[months[m]['safe']['models'][name] for m in MONTHS]
        n=sum(z['trades'] for z in entries)
        positive=sum(as_cents(z['positive_usd']) for z in entries)
        negative=sum(as_cents(z['negative_usd']) for z in entries)
        net=sum(as_cents(z['net_usd']) for z in entries)
        epositive=sum(as_cents(z['extra_positive_usd']) for z in entries)
        enegative=sum(as_cents(z['extra_negative_usd']) for z in entries)
        enet=sum(as_cents(z['net_extra10_usd']) for z in entries)
        if (net!=positive-negative or enet!=epositive-enegative
            or enet!=net-1000*n
            or n!=sum(d['models'][name]['trades'] for d in records)
            or net!=sum(d['models'][name]['stress_cents'] for d in records)):
            raise AssertionError('model/account balance or 10RT parity changed')
        stitch_rows=[{
            'frozen_path_adjusted_net_usd':z['net_usd'],
            'gross_positive_net_usd':z['positive_usd'],
            'gross_negative_net_usd':z['negative_usd'],
            'trades':z['trades'],
            'last_envelope_segment':z['last_envelope_segment']}
            for z in entries]
        dd=stitch(stitch_rows)['last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH']
        daily[name]={
            'stress':[d['models'][name]['stress_cents']/100 for d in records],
            'extra':[d['models'][name]['extra_cents']/100 for d in records]}
        models[name]={
            'N_trades':n,'N_trade_days':sum(d['models'][name]['trades']>0 for d in records),
            'stress_net_usd':net/100,'stress_pf':round(positive/negative,5) if negative else None,
            'stress_dd_last_usd':dd,
            'extra10_net_usd':enet/100,'extra10_pf':round(epositive/enegative,5) if enegative else None,
            'net_stress_by_month':[z['net_usd'] for z in entries],
            'trades_by_month':[z['trades'] for z in entries],
            'active_months_with_5trades':sum(z['trades']>=5 for z in entries)}
    baseline=models[BASE]
    if (baseline['N_trades'],baseline['stress_net_usd'],
        baseline['extra10_net_usd'],baseline['stress_dd_last_usd'])!=(115,5102.5,3952.5,1797.5):
        raise AssertionError('T05 frozen global benchmark parity')
    out={};p_values={}
    for k in IDS:
        stage={'N_case_days':cases[k][CASE],
               'N_control_days':cases[k][CONTROL],
               'N_other_days':cases[k][OTHER],
               'N_independent_events':None,
               'IC90_by_block_length':{},
               'p_is_postselection_descriptive':True,
               'Holm_confirmatory':None,'five_year_stability':None}
        if k==MAG:
            avg_case=(magnitude[CASE]['sum_ticks']/magnitude[CASE]['n']
                      if magnitude[CASE]['n'] else None)
            avg_ctrl=(magnitude[CONTROL]['sum_ticks']/magnitude[CONTROL]['n']
                      if magnitude[CONTROL]['n'] else None)
            stage['unit']='future_15m_high_low_price_ticks'
            stage['mean_case_ticks']=round(avg_case,4) if avg_case is not None else None
            stage['mean_control_ticks']=round(avg_ctrl,4) if avg_ctrl is not None else None
            ent=[(float(0),0,float(x['future_range_T23_ticks'] or 0),
                  int(x['labels'][k]==CONTROL)) if x['labels'][k]==CONTROL else
                 (float(x['future_range_T23_ticks'] or 0),int(x['labels'][k]==CASE),
                  0.,0) for x in records]
            # The primary T23 contrast is control mean MINUS case mean.
            ent=[(r[2],r[3],r[0],r[1]) for r in ent]
            stage['N_trades']=None
            stage['standalone_trade_PF']=None
            stage['economic_profit']=None
            stage['router_delta']=None
        else:
            cs,ct,ro=CASE_NAMES[k],CTRL_NAMES[k],ROUTERS[k]
            c_mod,t_mod,r_mod=models[cs],models[ct],models[ro]
            ent=[]
            for day in records:
                state=day['labels'][k]
                c=day['models'][cs]
                t=day['models'][ct]
                ent.append((
                    c['extra_cents']/100 if state==CASE else 0.,
                    c['trades'] if state==CASE else 0,
                    t['extra_cents']/100 if state==CONTROL else 0.,
                    t['trades'] if state==CONTROL else 0))
            deltas=[round(a-b,2) for a,b in zip(daily[ro]['extra'],daily[BASE]['extra'])]
            delta=round(sum(deltas),2)
            if abs(delta-(r_mod['extra10_net_usd']-baseline['extra10_net_usd']))>.011:
                raise AssertionError('router paired extra10 delta parity')
            stage.update({
                'unit':'net_usd_per_executed_trade_case_minus_control',
                'case':c_mod,'control':t_mod,
                'N_trades':c_mod['N_trades'],
                'router':r_mod,
                'router_extra10_increment_usd':delta,
                'router_extra10_increment_monthly':[
                    round(x-y,2) for x,y in zip(r_mod['net_stress_by_month'],
                                                baseline['net_stress_by_month'])],
                'router_bootstrap_daily_extra10':{
                    str(L):moving_block_stats(deltas,L,seed=BASE_SEED+100*L+
                          int(k[1:3])+1000,reps=REPS) for L in LENGTHS}})
        stage['bootstrap']={
            str(L):comparison_bootstrap(ent,L,
                      seed=BASE_SEED+100*L+int(k[1:3]))
            for L in LENGTHS}
        z=stage['bootstrap']['5']
        if z['p_unilateral_centered'] is None:
            p_values[k]=1.
            stage['gate']='INSUFFICIENT_CASE_CONTROL_FOR_INFERENCE'
        else:
            p_values[k]=z['p_unilateral_centered']
            stage['gate']='EVALUATED_EXPLORATORY_NOT_CONFIRMED'
        if k!=MAG and stage['N_trades']==0:
            stage['gate']='NO_CASE_TRADES'
        out[k]=stage
    q=bh(p_values)
    for k in IDS:
        out[k]['BH_q_six_family_IN_SAMPLE_ONLY']=q[k]
        out[k]['BH_p_or_sentinel']=p_values[k]
        out[k]['economic_gate_passed']=False # No N >150, Holm, OOS, broker evidence.
    return {'status':'T20_T25_STAGE1_ECONOMIC_AND_PREDICTIVE_EXPLORATORY_ONLY',
        'source_days':source,'eligible_sessions':eligible,'anchor_days':135,
        'T05_benchmark':baseline,
        'hypotheses':out,
        'BH_family_size':6,'BH_descriptive_only':True,
        'OOS_validated':False,'broker_fills_verified':False,
        'Holm_confirmatory':None,'N_independent':None,
        'new_history_acquired':False,'holdouts_opened':False,
        'no_new_5second_signals':True,
        'daily_outcome_vectors_exported':False}

def report(z):
    lines=['# NQ T20–T25 | Primera medición ECONÓMICA y PREDICTIVA de seis preguntas',
           '',
           '**SOLO DEV EXPLORATORIO, NO VALIDA FONDEO NI FILLS.**',
           '[Action y prerregistro](../research/nq/NQ_T20_T25_CONTROLLED_ECONOMIC_PREDICTIVE_PREREG_2026_10_12.md).',
           '',
           '| Hipótesis | N caso/control días | N trade caso/control | Neto caso estrés +10 USD | PF caso estrés +10 | DD Last estrés | Dif. caso-control USD/trade (CI90 L5) | q BH seis descriptiva | Δrouter+$10 vs T05 USD | Estado |',
           '|---|---:|---:|---:|---:|---:|---|---:|---:|---|']
    for k in IDS:
        r=z['hypotheses'][k]
        b=r['bootstrap']['5']
        if k==MAG:
            lines.append(f"| {k} | {r['N_case_days']}/{r['N_control_days']} | N/A magnitud | N/D | N/D | N/D | "
                f"control−caso={b['effect_mean_case_minus_control']}, IC={b['CI90']} (ticks rango +15m) | "
                f"{r['BH_q_six_family_IN_SAMPLE_ONLY']} | N/D | {r['gate']} |")
        else:
            c,t=r['case'],r['control']
            lines.append(f"| {k} | {r['N_case_days']}/{r['N_control_days']} | "
                f"{c['N_trades']}/{t['N_trades']} | {c['extra10_net_usd']} | "
                f"{c['extra10_pf']} | {c['stress_dd_last_usd']} | "
                f"{b['effect_mean_case_minus_control']} / {b['CI90']} | "
                f"{r['BH_q_six_family_IN_SAMPLE_ONLY']} | "
                f"{r['router_extra10_increment_usd']} | {r['gate']} |")
    lines+=['','N=135 días elegibles; seis endpoints predeclarados, la comparación case/control',
            'es por operación neta +$10 en DIRECCIONALES; T23 solo magnitud, no P&L.',
            'CI90 de dependencia=bootstrap móvil no circular 10.000 L5; L3/10 sensibilidad',
            'en summary.json; p/q EXPLORATORIOS tras selección adaptativa DEV, Holm/OOS N/D.',
            'N<15 casos/control ejecutados => IC90/p N/D y p=1 sentinela de BH, NO prueba favorable.',
            'Router=UNA cuenta, T05 congelado, 1 NQ, max2 trades/día, stop fechado -$600;',
            'extra +$10 RT es fijo contable, no nuevo fill ni ajuste stop.',
            'Ambigüedad Last intratimestamp/fondeo/ejecución broker NO demostrados.',
            'Sin nuevos datos, 5s nuevas señales, lectura holdout, ni exportación privada.',
            '']
    return '\n'.join(lines)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--private',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    months={m:json.loads((args.private/f't20_t25_{m}.json').read_text())
            for m in MONTHS}
    result=aggregate(months)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    args.report.write_text(report(result)+'\n')
    print('NQ_T20_T25_STAGE1_SAFE_SUMMARY='+json.dumps({
        'source':result['source_days'],'eligible':result['eligible_sessions'],
        'results':{k:{'N_case_trade':(result['hypotheses'][k]['N_trades']),
            'outcome_status':result['hypotheses'][k]['gate']}
            for k in IDS},'OOS':False,'broker':False},sort_keys=True))
