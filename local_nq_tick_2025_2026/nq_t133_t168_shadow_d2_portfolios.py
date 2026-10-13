#!/usr/bin/env python3
"""Post-D1 SHADOW D2 six *one-position* portfolio exercises, never real D2.

Only previously licensed DEV Last. D1 original SAFE aggregates must reconcile
per-ID daily model outcomes before any portfolios are published. No daily
trades, raw ticks, or individual-session outcomes may leave the runner.
"""
from __future__ import annotations
import argparse,json,math
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path

from qc_tick_day import file_for
from qc_tick_to_minutes import source_events
from nq_tick_short_horizon import dev_day
from nq_tick_short_horizon_month import MONTHS,month_days
from nq_b05h01_trade_expansion_month import frozen_t05
from nq_t133_t168_combined_D0_batch import (
    OLD_IDS,NEW_IDS,IDS,SOURCE,READY,load_new,old_registry)
from nq_t133_t168_d1_engine import day_sim
from nq_t133_t168_economic_d1_batch import gate

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'research/nq/NQ_T133_T168_SHADOW_D2_PORTFOLIO_PREREG_2026_10_12.json'
LABELS=('CASE','CONTROL','OTHER','NOT_EVALUABLE')
SIM='MODELLED_EXECUTION_UNVERIFIED'
PORT_IDS=('ALL36_ID_PRIORITY','ALL36_CALENDAR_ROTATION',
 'DIVERSE27_CALENDAR_ROTATION','POSITIVE10_ID_PRIORITY_POSTHOC',
 'POSITIVE5_N15_ID_PRIORITY_POSTHOC','T147_ONLY_POSTHOC')

def load_policy(path=POLICY):
    obj=json.loads(path.read_text())
    frozen=gate()
    cases=obj['cases']
    if (obj.get('exercise_name')!='NQ-T133-T168-SHADOW-D2-PORTFOLIO-EXERCISE'
        or obj.get('source_d1_action')!=38326216082
        or obj.get('source_d0_action')!=38325498797
        or obj.get('source_d1_safe_artifact_id')!=11781138134
        or obj.get('governance')!='D1_NO_APPROVED_CANDIDATES_FORMAL_D2_REMAINS_EMPTY'
        or obj.get('all36')!=list(IDS)
        or obj.get('d0_diverse27')!=frozen['D0_diverse_ids']
        or obj.get('source_dev_months')!=list(MONTHS)
        or (obj.get('expected_source'),obj.get('expected_ready'))!=(SOURCE,READY)
        or [c['id'] for c in cases]!=list(PORT_IDS)
        or len(cases[0]['pool'])!=36
        or len(cases[1]['pool'])!=36
        or len(cases[2]['pool'])!=27
        or [len(c['pool']) for c in cases[3:]]!=[10,5,1]
        or cases[-1]['pool']!=['T147']
        or set(cases[3]['pool'])!={'T133','T134','T135','T137','T138','T139','T143','T144','T145','T147'}
        or set(cases[4]['pool'])!={'T133','T135','T137','T145','T147'}
        or any(set(x['pool'])-set(IDS) for x in cases)
        or any(x['priority'] not in ('LOWEST_ID_FIRST','ROTATE_DATE_ORDINAL_MOD_POOL_LENGTH') for x in cases)
        or (obj.get('account_start_usd'),obj.get('reference_daily_loss_usd'),
            obj.get('reference_trailing_closed_equity_dd_usd'),
            obj.get('reference_profit_goal_usd'),obj.get('reference_model_dd_alert_usd'))
           !=(50000,500,2000,3000,1500)
        or obj.get('broker_fills_verified') is not False
        or obj.get('do_not_open_holdouts') is not True
        or obj.get('one_daily_entry_max') is not True
        or obj.get('selection_is_only_based_on_frozen_membership_calendar_and_at_anchor_case') is not True
        or obj.get('never_fall_through_to_second_choice_after_selected_trade_rejected_or_horizon_missing') is not True
        or obj.get('one_account_one_open_trade_at_a_time') is not True):
        raise ValueError('SHADOW_D2_FROZEN_PORTFOLIO_PREREG_VIOLATED')
    return obj

def priority(c,day):
    # Rotate by calendar information ONLY; no outcomes or marks used.
    ordered=c['pool'][:]
    if c['priority']=='LOWEST_ID_FIRST':
        return sorted(ordered,key=lambda x:int(x[1:]))
    if c['priority']=='ROTATE_DATE_ORDINAL_MOD_POOL_LENGTH':
        k=date.fromisoformat(day).toordinal()%len(ordered)
        return ordered[k:]+ordered[:k]
    raise ValueError('UNKNOWN_PREREGISTERED_PRIORITY')

def decide(c,day,outcomes):
    """Lock the FIRST CASE at the anchor; never skip losses or later rejected fills."""
    eligible=set(k for k,z in outcomes.items() if z['group']=='CASE')
    for k in priority(c,day):
        if k in eligible:
            return k
    return None

def dd_metrics(profits,initial,loss_limit,trail_limit,alert_dd,goal):
    equity=float(initial);high=equity
    max_dd=0.;hit_trail=hit_alert=hit_goal=False
    risk_days=0;worst=0.
    high_gain=0.
    for v in profits:
        equity+=v;high=max(high,equity)
        dd=high-equity;max_dd=max(max_dd,dd)
        if dd>trail_limit:hit_trail=True
        if dd>alert_dd:hit_alert=True
        if equity-initial>=goal:hit_goal=True
        if v < -loss_limit:risk_days+=1
        worst=min(worst,v)
        high_gain=max(high_gain,equity-initial)
    return {'ending_equity_usd':round(equity,2),
      'max_closed_equity_dd_usd':round(max_dd,2),
      'closed_equity_dd_gt_2000_ever':hit_trail,
      'dd_gt_1500_ever':hit_alert,
      'reference_goal_3000_reached_ever':hit_goal,
      'worst_model_daily_usd':round(worst,2),
      'model_daily_loss_below_minus500_count':risk_days,
      'max_cumulative_model_gain_usd':round(high_gain,2)}

def portfolio_stats(c,records,prereg):
    initial=prereg['account_start_usd'];n=len(records)
    if n!=READY:raise ValueError('135 complete days required')
    all_y=[];stress_y=[];extra_y=[];monthly=defaultdict(float)
    monthly_n=Counter();reasons=Counter();instruments=Counter()
    id_n=Counter();id_pnl=defaultdict(float);groups=Counter()
    active_weeks=set();num_singles=0;num_multi=0;num_opposite=0
    locked_candidates=0;proxy_trades=0;win=0;gain=loss=0.
    for x in records:
        d=x['date'];outcomes=x['proxies']
        candidates=[k for k,z in outcomes.items() if z['group']=='CASE']
        if len(candidates)==1:num_singles+=1
        if len(candidates)>1:num_multi+=1
        modeled_sides={z['direction'] for z in outcomes.values()
                       if z.get('status')==SIM and 'direction' in z}
        if len(modeled_sides)>1:num_opposite+=1
        winner=decide(c,d,outcomes)
        if winner is None:
            v=s15=s10=0.
            groups['NO_CANDIDATE']+=1
        else:
            locked_candidates+=1
            selected=outcomes[winner]
            groups[selected['status']]+=1
            if selected['status']==SIM:
                v=selected['net_usd']
                s15=selected['stress_1_5x_usd']
                s10=selected['stress_plus_10_rt_usd']
                id_n[winner]+=1;id_pnl[winner]+=v
                instruments[selected['instrument']]+=1
                proxy_trades+=1
                if v>0:win+=1;gain+=v
                if v<0:loss+=v
                iso=date.fromisoformat(d).isocalendar()
                active_weeks.add((iso.year,iso.week))
                monthly_n[d[:7]]+=1
                if selected['risk_nominal_usd']>250+1e-9:
                    raise AssertionError('FROZEN_NOMINAL_RISK_CAP_VIOLATED')
            else:
                # Do NOT 'fallback' to another CASE: would select with future outcomes.
                v=s15=s10=0.
        all_y.append(v);stress_y.append(s15);extra_y.append(s10)
        monthly[d[:7]]+=v
    if locked_candidates!=sum(v for k,v in groups.items() if k!='NO_CANDIDATE'):
        raise AssertionError('PORTFOLIO_LOCK_AND_STATUS_MISMATCH')
    all_net=sum(all_y);stress_net=sum(stress_y);extra_net=sum(extra_y)
    if abs(all_net-sum(id_pnl.values()))>1e-7:
        raise AssertionError('ONE_ACCOUNT_PNL_NOT_SUM_OF_SELECTED_TRADES')
    base_dd=dd_metrics(all_y,initial,prereg['reference_daily_loss_usd'],
      prereg['reference_trailing_closed_equity_dd_usd'],
      prereg['reference_model_dd_alert_usd'],prereg['reference_profit_goal_usd'])
    stress_dd=dd_metrics(stress_y,initial,prereg['reference_daily_loss_usd'],
      prereg['reference_trailing_closed_equity_dd_usd'],
      prereg['reference_model_dd_alert_usd'],prereg['reference_profit_goal_usd'])
    extra_dd=dd_metrics(extra_y,initial,prereg['reference_daily_loss_usd'],
      prereg['reference_trailing_closed_equity_dd_usd'],
      prereg['reference_model_dd_alert_usd'],prereg['reference_profit_goal_usd'])
    monthly_n={m:monthly_n.get(m,0) for m in MONTHS}
    monthly={m:round(monthly.get(m,0.),2) for m in MONTHS}
    if sum(monthly_n.values())!=proxy_trades:raise AssertionError('MONTHLY_TRADE_COUNT_INCONSISTENT')
    q4=sum(monthly[m] for m in MONTHS[:3]);h1=sum(monthly[m] for m in MONTHS[3:])
    return {'id':c['id'],'selection_source':c['selection_source'],
       'priority':c['priority'],'pool_size':len(c['pool']),
       'n_sessions':n,'n_days_with_any_case_across_full36':sum(any(z['group']=='CASE' for z in x['proxies'].values()) for x in records),
       'n_days_single_CASE_in_full36':num_singles,
       'n_days_multiple_CASE_in_full36':num_multi,
       'n_days_opposite_side_modelled_case_in_full36_lower_bound':num_opposite,
       'selected_CASE_at_anchor_days':locked_candidates,
       'proxy_trades_in_one_account':proxy_trades,
       'days_with_anchor_selection_but_no_modelled_trade':locked_candidates-proxy_trades,
       'skipped_after_priority_lock_by_status':dict(groups),
       'n_active_weeks':len(active_weeks),
       'trades_per_calendar_month':round(proxy_trades/len(MONTHS),3),
       'monthly_trade_count':monthly_n,
       'monthly_net_usd':monthly,
       'q4_2025_net_usd':round(q4,2),
       'jan_apr_2026_net_usd':round(h1,2),
       'model_net_usd':round(all_net,2),
       'model_net_stress_1_5x_usd':round(stress_net,2),
       'model_net_stress_plus10_usd':round(extra_net,2),
       'model_net_per_trade_usd':round(all_net/proxy_trades,2) if proxy_trades else None,
       'model_PF':round(gain/-loss,4) if loss<0 else None,
       'model_win_rate':round(win/proxy_trades,4) if proxy_trades else None,
       'model_gross_positive_usd':round(gain,2),
       'model_gross_negative_usd':round(loss,2),
       'instruments':dict(instruments),
       'strategy_trade_counts':dict(id_n),
       'strategy_contribution_usd':{k:round(v,2) for k,v in id_pnl.items()},
       'closed_equity_base':base_dd,
       'closed_equity_stress_1_5x':stress_dd,
       'closed_equity_stress_plus10':extra_dd,
       'sample_return_pct_on_50k_not_annual':round(100*all_net/initial,4),
       'model_is_fill_verified':False,
       'cumulative_model_not_tradeable_cash_account':True,
       'OOS_independent':False}

def validate_d1_parity(records,original):
    old=original
    if (old.get('stage')!='T133_T168_D1_ECONOMIC_PROXIES_FULL36_DEV_UNVERIFIED'
        or (old.get('family_size'),old.get('source'),old.get('eligible'))!=(36,140,135)
        or set(old.get('results',{}))!=set(IDS)
        or old.get('D1_exploratory_pass_ids')!=[]
        or old.get('broker_fills_verified') is not False
        or old.get('holdouts_opened') is not False):
        raise ValueError('WRONG_D1_ORIGINAL_SAFE_REFERENCE')
    if len(records)!=READY:raise ValueError('BAD_SHADOW_SESSION_COUNT')
    per={k:{'N':0,'net':0.,'s15':0.,'s10':0.,'groups':Counter()} for k in IDS}
    for day in records:
        for k in IDS:
            z=day['proxies'][k]
            per[k]['groups'][z['group']]+=1
            if z['status']==SIM:
                per[k]['N']+=1
                per[k]['net']+=z['net_usd']
                per[k]['s15']+=z['stress_1_5x_usd']
                per[k]['s10']+=z['stress_plus_10_rt_usd']
    for k in IDS:
        src=old['results'][k];p=per[k]
        if (p['N']!=src['N_proxy_trades']
            or abs(p['net']-src['net_total_usd'])>1e-5
            or abs(p['s15']-src['net_stress_1_5x_total_usd'])>1e-5
            or abs(p['s10']-src['net_stress_plus_10_rt_usd'])>1e-5
            or p['groups']['CASE']!=src['N_case_D0']
            or p['groups']['CONTROL']!=src['N_control_D0']):
            raise AssertionError('D1_EXACT_AGGREGATE_PARITY_FAIL_'+k)
    return {'n_original_members_reconciled':36,
      'N_trades_net_and_both_stresses_reconciled_exactly':True,
      'all_original_case_control_masks_reconciled':True}

def run(root,original,prereg):
    if not root.is_dir():raise ValueError('DEV_ROOT_NOT_FOUND')
    old,new=old_registry(),load_new()
    qc=Counter();source=0;records=[]
    for month in MONTHS:
        # The existing month_days reader intentionally fails closed on mixed
        # contract/month folders. Preserve this separation for all 7 DEV files.
        month_root=root/month
        for day in sorted(month_days(month_root,month)):
            d=dev_day(day)
            source+=1
            events=list(source_events(file_for(month_root,d,'Last')))
            status,_,_=frozen_t05(events,day)
            qc[status]+=1
            if status!='READY':continue
            out=day_sim(events,day,old,new)
            if set(out)!=set(IDS):raise AssertionError('FULL_36_REQUIRED')
            records.append({'date':day,'proxies':out})
    if (source,len(records),qc['READY'])!=(SOURCE,READY,READY):
        raise AssertionError('INVALID_SEVEN_MONTH_DEV_QC')
    records.sort(key=lambda x:x['date'])
    parity=validate_d1_parity(records,original)
    scenarios=[portfolio_stats(c,records,prereg) for c in prereg['cases']]
    return {'stage':'SHADOW_D2_POSTHOC_PORTFOLIOS_NO_FORMAL_PROMOTION',
      'source_d1_action':38326216082,'N_source_sessions':source,
      'N_ready_sessions':len(records),'D1_pass_formal':0,
      'D2_formal_assessments':0,'shadow_portfolios':len(scenarios),
      'D1_reproduction_check':parity,
      'cohort':'NQ-C133-168','full_family_size':36,
      'broker_fills_verified':False,'OOS_confirmed':False,
      'licensed_data_exported':False,'new_data_acquired':False,
      'regime_periods_previously_explored':True,
      'account_initial_usd':prereg['account_start_usd'],
      'notes':'SHADOW D2 only, 1 trade per portfolio/day, all 7 DEV months reused, trade selection never uses daily PnL; posthoc positive pools heavily biased',
      'scenarios':scenarios}

def report(r):
    def fm(x):
        return 'N/D' if x is None else f'{x:,.2f}'
    lines=['# NQ T133–T168 — D2 SIMULADA / SHADOW (NO PROMOCIÓN FORMAL)',
      '',
      '**Usuario autorizó un ejercicio D2 aun con 0/36 aprobadas D1**. '
      'Las seis carteras comparten el mismo DEV explorado; una posición '
      'proxy por sesión y por cartera. Las 6 NO se operan simultáneamente.',
      '',
      f"Action original D1 **{r['source_d1_action']}**; "
      f"verificación reproduce EXACTAMENTE 36 miembros, CASE/CONTROL/N/neto "
      "y ambos estrés. **140 sesiones fuente/135 READY**. Sin abrir OOS, "
      "nuevos ticks, nuevas temporalidades ni broker fills.",
      '',
      'Valores NOMINALES para una cuenta SIMULADA de **US$50.000**; '
      'DD únicamente sobre equity CERRADA, no trailing intradía de fondeo. '
      'Tarifas/slippage supuestos del mismo motor D1; '
      'los pools POSTHOC están etiquetados como sesgados.',
      '',
      '| Cartera congelada | Miembros | Trades proxy | Media mes | '
      'Neto US$ | PF | DD cerrado US$ | Neto estrés1,5× | '
      'Neto +$10RT | ROI simple período | Q4/2025 | Ene–Abr/2026 | '
      '¿DD cerrado>2000? |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for z in r['scenarios']:
        dd=z['closed_equity_base']
        lines.append(f"| {z['id']} | {z['pool_size']} | "
          f"{z['proxy_trades_in_one_account']} | {z['trades_per_calendar_month']:.2f} | "
          f"{fm(z['model_net_usd'])} | {fm(z['model_PF'])} | "
          f"{fm(dd['max_closed_equity_dd_usd'])} | "
          f"{fm(z['model_net_stress_1_5x_usd'])} | "
          f"{fm(z['model_net_stress_plus10_usd'])} | "
          f"{z['sample_return_pct_on_50k_not_annual']:.2f}% | "
          f"{fm(z['q4_2025_net_usd'])} | {fm(z['jan_apr_2026_net_usd'])} | "
          f"{'SÍ' if dd['closed_equity_dd_gt_2000_ever'] else 'NO'} |")
    lines+=['', '## Interpretación y límites',
      '',
      '- **Selección de operaciones:** primera señal causal CASE de cada '
      'cartera según orden fijo o rotación por ordinal de fecha. '
      'No se elige la ganadora después de ver futuro; si rechazada '
      'por riesgo, se pierde oportunidad y NO se hace fallback.',
      '- Los pools «POSITIVE10», «POSITIVE5» y «T147_ONLY» son '
      '**hindsight de la MISMA DEV**: nunca interpretar resultado '
      'superior como ventaja replicable en datos independientes.',
      '- Márgenes, regla de pérdida intradía, trailing máximo en '
      'equity abierta, requisitos concretos de prop firm, fill ejecutable '
      'y liquidez no verificados. Alertas DD cerrado US$1500/2000 y '
      'meta US$3000 son ilustrativas; NO prueban pasar una evaluación.',
      '- ROI = neto del modelo / US$50.000 en estos siete meses, '
      '**NO** retorno anual comparable a ETF ni trading real.',
      '- El estado formal **D1=0 aprobadas, D2=0 habilitadas** y '
      'holdouts mayo–septiembre sellados permanecen INALTERADOS.',
      '',
      '**Detalle técnico agregado por cartera**: artifact JSON con '
      'frecuencia semanal y mensual, contribuciones, drawdowns bajo '
      '2 estrés, estados sin trades, alertas y equity cerrada.',
      '']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--original-summary',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    if not a.original_summary.exists():raise ValueError('D1_SAFE_ORIGINAL_REQUIRED')
    pre=load_policy()
    original=json.loads(a.original_summary.read_text())
    result=run(a.root,original,pre)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    a.report.write_text(report(result)+'\n')
    print('NQ_SHADOW_D2_SAFE_FINAL='+json.dumps({
      'source':result['N_source_sessions'],'eligible':result['N_ready_sessions'],
      'D1_parity':result['D1_reproduction_check'],
      'D2_formal_assessments':0,
      'scenarios':[{k:x[k] for k in ('id','proxy_trades_in_one_account',
                  'model_net_usd','model_PF','sample_return_pct_on_50k_not_annual')}
                 for x in result['scenarios']]},sort_keys=True))
