#!/usr/bin/env python3
"""USER AUTHORIZED D2 SHADOW: five fixed single-position routers, 36 strategies.

THIS IS NOT D2 OFFICIAL, NO REAL FILLS. Reconstruct 36 modelled D1
outcomes, reconcile exact N/PNL with existing SAFE D1 artifact; route by
causal trigger only, never result. No new market data/OOS.
"""
from __future__ import annotations
import argparse, json, random
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05
from nq_t133_t168_combined_D0_batch import IDS,load_new,old_registry
from nq_t133_t168_d1_engine import day_sim
from nq_t133_t168_economic_d1_batch import gate,drawdown
from nq_t153_t168_executable_d0_features import LABELS,CASE

EXPECTED_D1_ACTION=38326216082
N_SESSIONS,N_SOURCE=135,140
CAPITAL_USD=50000.0
ROUTERS={
  'R0_ALL36_ID':tuple(IDS),
  'R1_POSITIVE5_ID':('T133','T135','T137','T145','T147'),
  'R2_POSITIVE5_REVERSAL_FIRST':('T145','T147','T133','T135','T137'),
  'R3_REVERSAL2_ID':('T145','T147'),
  'R4_T147_ONLY':('T147',),
}
N_BOOT=10000

def select_causal(day,priority):
    """Never choose based on future net, stop/target or eventual rejection."""
    if set(day)!=set(IDS):raise AssertionError('DAY_HAS_NOT_ALL36')
    candidates=[k for k in priority if day[k]['group']==CASE]
    return candidates[0] if candidates else None,len(candidates)

def month_stage(root,month,old,new):
    if month not in MONTHS:raise ValueError('SEALED_MONTH_NO_IO')
    cnt={k:Counter() for k in IDS}
    trade_count=Counter();gross=defaultdict(float);source=eligible=0
    days=[]
    for day in sorted(month_days(root,month)):
        d=dev_day(day);source+=1
        events=list(source_events(file_for(root,d,'Last')))
        qc,_,_=frozen_t05(events,day)
        if qc!='READY':continue
        results=day_sim(events,day,old,new)
        if set(results)!=set(IDS):raise AssertionError('NOT_COMPLETE_36')
        for k,x in results.items():
            if x['group'] not in LABELS:raise AssertionError('BAD_MASK')
            cnt[k][x['group']]+=1
            if x['status']=='MODELLED_EXECUTION_UNVERIFIED':
                trade_count[k]+=1;gross[k]+=x['net_usd']
        dd={'date':day,'portfolio_candidates':{}}
        for router,priority in ROUTERS.items():
            pick,conflict=select_causal(results,priority)
            z=results[pick] if pick else None
            status=z['status'] if z else 'NO_SIGNAL'
            dd['portfolio_candidates'][router]={
              'chosen_id':pick, 'n_CASE_in_router':conflict,
              'status':status,
              'net':z['net_usd'] if status=='MODELLED_EXECUTION_UNVERIFIED' else 0.,
              'stress15':z['stress_1_5x_usd'] if status=='MODELLED_EXECUTION_UNVERIFIED' else 0.,
              'stress10':z['stress_plus_10_rt_usd'] if status=='MODELLED_EXECUTION_UNVERIFIED' else 0.,
              'instrument':z.get('instrument') if z else None,
              'nominal_risk':z.get('risk_nominal_usd') if z else None,
              'exit_reason':z.get('exit_reason') if z else None}
        days.append(dd);eligible+=1
    if any(sum(cnt[k].values())!=eligible for k in IDS):
        raise AssertionError('MISSING_DAILY_LABEL')
    return {'stage':'D2_SHADOW_PRIVATE_ONLY','month':month,'source':source,
      'eligible':eligible,'private_days':days,
      'D1_N_by_strategy':{k:trade_count[k] for k in IDS},
      'D1_net_by_strategy':{k:gross[k] for k in IDS},
      'D0_labels_by_strategy':{k:{z:cnt[k][z] for z in LABELS} for k in IDS},
      'broker_fills_verified':False,'holdouts_opened':False,
      'new_data':False,'export_private_daily_data':False}

def bci(y,seed):
    if len(y)!=N_SESSIONS:raise AssertionError('UNCONDITIONED_SESSION_COUNT')
    n=len(y);L=5;rnd=random.Random(831100+seed)
    starts=n-L+1;means=[]
    for _ in range(N_BOOT):
        x=[]
        while len(x)<n:
            start=rnd.randrange(starts)
            x.extend(y[start:start+L])
        means.append(sum(x[:n])/n)
    means.sort()
    return [means[int(.05*(N_BOOT-1))],means[int(.95*(N_BOOT-1))]]

def aggregate(monthly,original_d1,frozen):
    if set(monthly)!=set(MONTHS):raise AssertionError('SEVEN_MONTHS_REQUIRED')
    if (original_d1.get('stage')!='T133_T168_D1_ECONOMIC_PROXIES_FULL36_DEV_UNVERIFIED'
       or original_d1.get('family_size')!=36
       or (original_d1.get('source'),original_d1.get('eligible'))!=(140,135)
       or set(original_d1.get('results',{}))!=set(IDS)
       or original_d1.get('broker_fills_verified') is not False):
        raise ValueError('ORIGINAL_D1_SAFE_AGGREGATES_REQUIRED')
    totals={k:Counter() for k in IDS};n=Counter();profit=defaultdict(float)
    days=[];source=ready=0
    for m in MONTHS:
        z=monthly[m]
        if (z['stage']!='D2_SHADOW_PRIVATE_ONLY' or z['month']!=m
            or z['eligible']!=len(z['private_days'])
            or any(z[x] is not False for x in ('broker_fills_verified','holdouts_opened','new_data','export_private_daily_data'))
            or set(z['D0_labels_by_strategy'])!=set(IDS)):
            raise AssertionError('UNSAFE_OR_INVALID_MONTH')
        source+=z['source'];ready+=z['eligible'];days.extend(z['private_days'])
        for k in IDS:
            totals[k].update(z['D0_labels_by_strategy'][k])
            n[k]+=z['D1_N_by_strategy'][k]
            profit[k]+=z['D1_net_by_strategy'][k]
    if (source,ready,len(days))!=(N_SOURCE,N_SESSIONS,N_SESSIONS):
        raise AssertionError('FULL_DEV_COVERAGE_140_135')
    if [x['date'] for x in days]!=sorted(x['date'] for x in days):
        raise AssertionError('CHRONOLOGY_INVALID')
    # A strict independent replay of all 36 D1 source models.
    for k in IDS:
        if totals[k]!=frozen['case_control_other_missing'][k]:
            raise AssertionError('D0_MASK_CHANGED_'+k)
        historic=original_d1['results'][k]
        if n[k]!=historic['N_proxy_trades'] or abs(profit[k]-historic['net_total_usd'])>.01:
            raise AssertionError('D1_FULL36_REPLAY_MISMATCH_'+k+
                                 f' n={n[k]}/{historic["N_proxy_trades"]} pnl={profit[k]}/{historic["net_total_usd"]}')
    models={}
    for i,(name,priority) in enumerate(ROUTERS.items()):
        day=[z['portfolio_candidates'][name] for z in days]
        if len(day)!=N_SESSIONS:raise AssertionError('NOT_135_PORTFOLIO_DAYS')
        net=[r['net'] for r in day]
        trade=[(z,r) for z,r in zip(days,day)
               if r['status']=='MODELLED_EXECUTION_UNVERIFIED']
        wins=sum(r['net'] for _,r in trade if r['net']>0)
        losses=sum(r['net'] for _,r in trade if r['net']<0)
        pf=(wins/-losses if losses<0 else None)
        segQ4=sum(r['net'] for z,r in zip(days,day) if z['date']<='2025-12-31')
        seg2026=sum(r['net'] for z,r in zip(days,day) if z['date']>='2026-01-01')
        months=defaultdict(float);week=set();byid=Counter();byinst=Counter()
        bystatus=Counter();byexit=Counter();risks=[];maxover=0.
        for z,r in zip(days,day):
            bystatus[r['status']]+=1
            if r['status']=='MODELLED_EXECUTION_UNVERIFIED':
                months[z['date'][:7]]+=r['net']
                week.add(date.fromisoformat(z['date']).isocalendar()[:2])
                byid[r['chosen_id']]+=1;byinst[r['instrument']]+=1
                byexit[r['exit_reason']]+=1
                risks.append(r['nominal_risk'])
                if r['nominal_risk'] is None or r['nominal_risk']>250.000001:
                    raise AssertionError('ACCOUNT_RISK_CAP_VIOLATED')
                maxover=max(maxover,max(0.,-r['net']-r['nominal_risk']))
            else:
                if r['net']!=0:raise AssertionError('GHOST_TRADE_PNL')
        month={m:round(months.get(m,0.),2) for m in MONTHS}
        pos=[v for v in month.values() if v>0]
        concentration=max(pos)/sum(pos) if pos else None
        ntr=len(trade);pnl=sum(net);dd=drawdown(net)
        stress15=sum(r['stress15'] for r in day)
        stress10=sum(r['stress10'] for r in day)
        criteria={'N_trades_ge_15':ntr>=15,
         'net_positive':pnl>0,
         'expectancy_positive':pnl>0 and ntr>0,
         'PF_ge_1_25':pf is not None and pf>=1.25,
         'stress_1_5x_positive':stress15>0,
         'stress_plus_10_RT_positive':stress10>0,
         'Q4_2025_positive':segQ4>0,
         'Jan_Apr_2026_positive':seg2026>0,
         'DD_le_1500':dd<=1500,
         'monthly_concentration_lt_40pct':concentration is not None and concentration<.4}
        models[name]={'portfolio_priority_ids':list(priority),
          'posthoc_selected_from_D1':name!='R0_ALL36_ID',
          'N_sessions':N_SESSIONS,
          'N_days_any_CASE':sum(r['n_CASE_in_router']>=1 for r in day),
          'N_days_collision_2plus_CASE':sum(r['n_CASE_in_router']>=2 for r in day),
          'N_trade_proxies':ntr,'N_active_weeks':len(week),
          'case_status_counts':dict(bystatus),'proxy_trades_by_id':dict(byid),
          'proxy_trades_by_instrument':dict(byinst),
          'proxy_exits_by_reason':dict(byexit),
          'net_model_usd':round(pnl,2),
          'net_stress_1_5x_usd':round(stress15,2),
          'net_stress_plus_10_RT_usd':round(stress10,2),
          'model_ROI_of_50000_pct':round(pnl/CAPITAL_USD*100,4),
          'PF_model':None if pf is None else round(pf,4),
          'DD_model_usd':round(dd,2),
          'DD_of_50000_pct':round(dd/CAPITAL_USD*100,4),
          'expectancy_per_trade_model_usd':None if not ntr else round(pnl/ntr,2),
          'win_rate_model':None if not ntr else round(sum(r['net']>0 for _,r in trade)/ntr,4),
          'worst_day_model_usd':round(min(net),2),
          'max_loss_above_initial_nominal_stop_risk_usd':round(maxover,2),
          'max_initial_nominal_risk_usd':round(max(risks),2) if risks else None,
          'Q4_2025_net_usd':round(segQ4,2),'Jan_Apr_2026_net_usd':round(seg2026,2),
          'net_by_dev_month_usd':month,
          'month_profit_concentration':None if concentration is None else round(concentration,4),
          'bootstrap_daily_mean_CI90_L5_usd':bci(net,i),
          'economic_gates':criteria,
          'N_economic_gates_passed':sum(criteria.values()),
          'pass_all_economic_gates_EXPLORATORY_ONLY':all(criteria.values())}
    return {'stage':'D2_SHADOW_EXERCISE_ONLY_NO_OFFICIAL_PROMOTION',
      'source_D1_action':EXPECTED_D1_ACTION,
      'source_D0_action':38325498797,
      'source':source,'eligible':ready,
      'original_36_D1_N_and_USD_reconciled':True,
      'original_36_D0_MASKS_reconciled':True,
      'policy_count':len(ROUTERS),'portfolio_models':models,
      'account_usd':CAPITAL_USD,'one_position_per_day':True,
      'D1_pass_ids':[],'D2_official_pass_ids':[],
      'no_official_D2_promotion':True,'broker_fills_verified':False,
      'posthoc_selection_contamination':True,
      'true_independent_OOS':False,'holdouts_opened':False,'new_data':False}

def report(s):
    a=['# NQ T133–T168 — D2 SHADOW: carteras con UNA sola posición por sesión, 50K',
       '', '**Ejercicio explícitamente solicitado por el usuario. D1 OFICIAL 0/36 PASS.** '
       'Se prueban enrutadores mutuamente excluyentes, no suma de 36 PnL simultáneos.',
       f"**Auditoría:** 140 fuente / {s['eligible']} READY, todas las 36 máscaras D0 y "
       "36 N/PnL originales D1 reconciliados contra sus artifacts congelados, sin diferencias.",
       'Una posición NQ/MNQ/día; costos/Last stop-first del motor D1; '
       'capital 50.000 USD y riesgo nominal stop <=250 USD. '
       'Las cinco políticas fueron congeladas ANTES de computar esta D2.',
       'R1–R4 usan selección retrospectiva de positivos D1: POST-HOC, '
       'NO VALIDACIÓN. Q4-2025/Ene–Abr2026 DEV ya reexaminada, NO OOS. '
       'No fills broker. Rentabilidad NO ANUALIZADA.',
       '', '| Router | Trades | CASE días | Colisiones días | Neto USD PROXY | Estrés1,5× | Estrés +$10 RT | PF | DD USD | ROI simple 50k | Q4 | Ene–Abr | Gates económicos /10 |',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for k,v in s['portfolio_models'].items():
        fmt=lambda x:'N/D' if x is None else f'{x:+,.2f}'
        a.append(f"| {k} | {v['N_trade_proxies']} | {v['N_days_any_CASE']} | "
        f"{v['N_days_collision_2plus_CASE']} | {fmt(v['net_model_usd'])} | "
        f"{fmt(v['net_stress_1_5x_usd'])} | "
        f"{fmt(v['net_stress_plus_10_RT_usd'])} | "
        f"{fmt(v['PF_model'])} | {fmt(v['DD_model_usd'])} | "
        f"{fmt(v['model_ROI_of_50000_pct'])}% | "
        f"{fmt(v['Q4_2025_net_usd'])} | {fmt(v['Jan_Apr_2026_net_usd'])} | "
        f"{v['N_economic_gates_passed']}/10 |")
    a+=['','## Decisión', '',
        '**El ejercicio D2 SHADOW NO cambia el embudo D1 ni promociona ningún modelo al D2 OFICIAL.** '
        'Si un router sale positivo, se considera simulación exploratoria posterior a selección '
        'en la misma DEV y no prueba confirmatoria. No abrir cuentas ni OOS sellados.',
        'Las salidas incluyen tasas por mes, IC90 bootstrap L5 descriptivo, '
        'selección de instrumentos, pérdidas por gaps y conteo de conflictos en summary.json SAFE.',
        'ROI calculado exclusivamente como PnL de 135 sesiones sobre capital 50K, sin anualizar.',
        'El requisito deseable de una operación semanal no equivale a mínimo formal.',
        '']
    return '\n'.join(a)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path)
    p.add_argument('--month');p.add_argument('--inputs',type=Path)
    p.add_argument('--original-d1',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path)
    args=p.parse_args();frozen=gate();old=old_registry();new=load_new()
    if args.month:
        if args.month not in MONTHS:raise SystemExit('SEALED_MONTH_BEFORE_IO')
        z=month_stage(args.root,args.month,old,new)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(z,separators=(',',':'))+'\n')
        print('D2_SHADOW_PRIVATE_MONTH='+json.dumps(
            {'month':args.month,'source':z['source'],'eligible':z['eligible']}))
    else:
        if not args.inputs or not args.original_d1 or not args.report:
            raise ValueError('AGGREGATE_NEEDS_ORIGINAL_SAFE_D1_AND_ALL_SEVEN_MONTHS')
        ms={m:json.loads((args.inputs/f'd2shadow_{m}.json').read_text())
              for m in MONTHS}
        orig=json.loads(args.original_d1.read_text())
        z=aggregate(ms,orig,frozen)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
        args.report.write_text(report(z)+'\n')
        print('NQ_D2_SHADOW_SAFE_FINAL='+json.dumps({
         'source':z['source'],'eligible':z['eligible'],
         'original_36_D1_N_and_USD_reconciled':True,
         'portfolios':{k:{key:v[key] for key in ('N_trade_proxies','net_model_usd','PF_model','DD_model_usd',
           'net_stress_1_5x_usd','net_stress_plus_10_RT_usd',
           'Q4_2025_net_usd','Jan_Apr_2026_net_usd','N_economic_gates_passed')}
             for k,v in z['portfolio_models'].items()},
         'D2_official':[]},sort_keys=True))
