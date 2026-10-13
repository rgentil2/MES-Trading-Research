#!/usr/bin/env python3
"""Read ONLY D2 SHADOW six-portfolio SAFE aggregate; print reproducible audit.
Never touches Last, one-day trades, or any holdout.
"""
import argparse,json
from pathlib import Path
PORTS=['ALL36_ID_PRIORITY','ALL36_CALENDAR_ROTATION','DIVERSE27_CALENDAR_ROTATION',
'POSITIVE10_ID_PRIORITY_POSTHOC','POSITIVE5_N15_ID_PRIORITY_POSTHOC','T147_ONLY_POSTHOC']
def audit(x):
    if (x.get('stage')!='SHADOW_D2_POSTHOC_PORTFOLIOS_NO_FORMAL_PROMOTION'
        or x.get('source_d1_action')!=38326216082
        or x.get('cohort')!='NQ-C133-168'
        or (x.get('N_source_sessions'),x.get('N_ready_sessions'))!=(140,135)
        or x.get('full_family_size')!=36
        or x.get('D1_pass_formal')!=0
        or x.get('D2_formal_assessments')!=0
        or x.get('broker_fills_verified') is not False
        or x.get('licensed_data_exported') is not False
        or x.get('OOS_confirmed') is not False
        or x.get('new_data_acquired') is not False
        or x.get('D1_reproduction_check',{}).get('n_original_members_reconciled')!=36
        or x.get('D1_reproduction_check',{}).get('N_trades_net_and_both_stresses_reconciled_exactly') is not True
        or [z['id'] for z in x.get('scenarios',[])]!=PORTS):
        raise ValueError('SHADOW_D2_SAFE_AGGREGATE_DID_NOT_PASS_AUDIT')
    out=[]
    for z in x['scenarios']:
        one=z['closed_equity_base'];s15=z['closed_equity_stress_1_5x'];s10=z['closed_equity_stress_plus10']
        if (z['n_sessions']!=135
            or z['selected_CASE_at_anchor_days'] < z['proxy_trades_in_one_account']
            or z['proxy_trades_in_one_account']!=sum(z['monthly_trade_count'].values())
            or abs(z['model_net_usd']-sum(z['monthly_net_usd'].values()))>.05
            or abs(z['model_net_usd']-(z['q4_2025_net_usd']+z['jan_apr_2026_net_usd']))>.05
            or abs(one['ending_equity_usd']-(50000+z['model_net_usd']))>.05
            or abs(z['sample_return_pct_on_50k_not_annual']-z['model_net_usd']/50000*100)>.001
            or z['model_is_fill_verified'] is not False):
            raise ValueError('SIX_PORTFOLIO_RECONCILIATION_FAILED_'+z['id'])
        out.append({
          'id':z['id'],'pool':z['pool_size'],
          'n_proxy_trades':z['proxy_trades_in_one_account'],
          'weeks_active':z['n_active_weeks'],
          'trades_per_month':z['trades_per_calendar_month'],
          'n_selected_case_days':z['selected_CASE_at_anchor_days'],
          'no_model_fill_selected':z['days_with_anchor_selection_but_no_modelled_trade'],
          'net_base_usd':z['model_net_usd'],'PF':z['model_PF'],
          'win_rate':z['model_win_rate'],
          'net_stress_1_5x':z['model_net_stress_1_5x_usd'],
          'net_stress_plus10rt':z['model_net_stress_plus10_usd'],
          'model_dd_closed_usd':one['max_closed_equity_dd_usd'],
          'stress_1_5x_dd_closed_usd':s15['max_closed_equity_dd_usd'],
          'stress_plus10_dd_closed_usd':s10['max_closed_equity_dd_usd'],
          'closed_trailing_2000_breach':one['closed_equity_dd_gt_2000_ever'],
          'daily_loss500_breach_days':one['model_daily_loss_below_minus500_count'],
          'worst_daily_model_usd':one['worst_model_daily_usd'],
          'goal3000_reached_ever':one['reference_goal_3000_reached_ever'],
          'Q4_2025_net':z['q4_2025_net_usd'],
          'Jan_Apr_2026_net':z['jan_apr_2026_net_usd'],
          'monthly_net':z['monthly_net_usd'],
          'monthly_trade_count':z['monthly_trade_count'],
          'roi_seven_months_pct':z['sample_return_pct_on_50k_not_annual'],
          'contribution':z['strategy_contribution_usd'],
          'n_multi_case_days':z['n_days_multiple_CASE_in_full36'],
          'n_opposing_modelled_sides_days_lower_bound':z['n_days_opposite_side_modelled_case_in_full36_lower_bound'],
          'selection_posthoc_biased':'POSTHOC' in z['id'],
          'qualifies_for_real_funding':False})
    return {'status':'SHADOW_D2_SAFE_AUDITED','n':len(out),
      'source_action':38335007318,'formal_D2_candidates':0,
      'all36_D1_reconciled':True,'portfolios':out}
def report(res):
    p=res['portfolios']
    a=['# D2 experimentada — resumen auditado de seis carteras, 50k capital ficticio',
       '',
       'D2 SHADOW autorizada para ejercicio pese a D1=0 pass. **No equivale a fondeo ni fill broker**. '
       '[Action D2 38335007318](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38335007318) '
       'y artifact 11785105339. **Reproducción EXACTA de los 36 D1 en N/neto/costos ambos estrés**; '
       'no se abrieron holdouts ni se adquirieron datos.',
       '',
       '| Cartera | N trades | Trades/mes | Neto US$ | PF | DD cerrado US$ | Estrés 1,5× US$ | +US$10 RT US$ | Q4-2025 US$ | Ene–Abr26 US$ | DD>2k | 3k meta |',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|']
    for z in p:
        f=lambda k: 'N/D' if z[k] is None else f"{z[k]:,.2f}"
        a.append(f"| {z['id']} | {z['n_proxy_trades']} | "
          f"{z['trades_per_month']:.2f} | {f('net_base_usd')} | {f('PF')} | "
          f"{f('model_dd_closed_usd')} | {f('net_stress_1_5x')} | "
          f"{f('net_stress_plus10rt')} | {f('Q4_2025_net')} | "
          f"{f('Jan_Apr_2026_net')} | "
          f"{'Sí' if z['closed_trailing_2000_breach'] else 'No'} | "
          f"{'Sí' if z['goal3000_reached_ever'] else 'No'} |")
    a+=['','**Interpretación:** Cada cartera es una ejecución MUTUAMENTE EXCLUYENTE de máximo 1 operación al día y por cuenta. '
      'No se suman resultados de estrategias que habrían operado simultáneamente. '
      'Las carteras POSTHOC usan ganancias observadas EN EL MISMO DEV para elegir las estrategias: '
      'sus resultados son in-sample severamente sesgados. '
      'Riesgo de US$2k de trailing DD calculado SOLO sobre equity de cierre, '
      'no reglas reales de intradía ni garantía de fills.',
      'La meta de US$3k y límites de US$500/día y US$2000 DD son ilustrativos, '
      'no pertenecen a una firma de fondeo identificada. ROI es muestra de 7 meses, no anualizada. '
      'D1 formal cero y D2 formal cero aunque algún escenario SHADOW sea positivo.','']
    return '\n'.join(a)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    args=p.parse_args()
    r=audit(json.loads(args.input.read_text()))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    args.report.write_text(report(r)+'\n')
    print('NQ_SHADOW_D2_DETAIL_SAFE='+json.dumps(
      [{k:z[k] for k in ('id','n_proxy_trades','trades_per_month','net_base_usd','PF','model_dd_closed_usd','net_stress_1_5x','net_stress_plus10rt','Q4_2025_net','Jan_Apr_2026_net','closed_trailing_2000_breach','daily_loss500_breach_days','goal3000_reached_ever','weeks_active','roi_seven_months_pct','no_model_fill_selected')} for z in r['portfolios']],sort_keys=True))
