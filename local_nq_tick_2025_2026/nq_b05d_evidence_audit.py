#!/usr/bin/env python3
"""NQ B05D -- audit existing T10/B03/B05C aggregate artifacts, NO market ticks.

Evidence-based feasibility of order-flow identification, shared-capacity and
Last-only execution. Never treats quote matches as fills, never opens holdouts.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

MONTHS=('2025-10','2025-11','2025-12','2026-01','2026-02','2026-03','2026-04')
STRESS='stress_1p5_fee_2ticks_each_side'
STRESS_EXTRA='stress_plus_10_usd_rt_FIXED_PATH_ONLY'
FAMILY_HISTORY={'T09':'FAIL_INCREMENTAL_COST_STRESS',
                'T11':'FAIL_ATTRIBUTED_NET_AND_DD',
                'T12':'FAIL_ATTRIBUTED_NET_AND_CAPACITY',
                'T13':'FAIL_ATTRIBUTED_NET_AND_CAPACITY'}
DOCS={
  'ninjatrader_tick_replay':
     'https://ninjatrader.com/support/helpGuides/nt8/developing_for__tick_replay.htm',
  'ninjatrader_market_replay':
     'https://ninjatrader.com/support/helpguides/nt8/playback.htm',
  'cme_mdp_trade_summary':
     'https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457418925/MDP%2B3.0%2B-%2BTrade%2BSummary',
  'ninjatrader_historical_bidask':
     'https://ninjatrader.com/support/helpguides/nt8/using_historical_bid_ask_serie.htm'
}

def verify(condition,why):
    if not condition:raise ValueError('B05D evidence invariant FAILED: '+why)

def audit(t10,b03,t13):
    for label,d in [('T10',t10),('B03',b03),('B05C',t13)]:
        verify(d['holdouts_opened'] is False,label+' opened holdouts')
        verify((d['source_days'],d['eligible_days'])==(140,135),label+' coverage')
        verify(tuple(d['source_months'])==MONTHS,label+' months')
    verify(t10['status']=='NQ_T10_T05_EXECUTION_QC_NOT_TRADING_APPROVED','T10 status')
    verify(t10['quote_max_age_ms']==250,'T10 quote age')
    verify(t10['prior_quote_rule']=='BID_ASK_T_STRICTLY_LESS_THAN_LAST_MODEL_ENDPOINT_T',
           'quote causal gate')
    verify(t10['source_source_NQ_Last_Bid_Ask_private_checked'] is True,'T10 source')
    verify(t10['broker_fills_or_ETF_comparison_done'] is False,'T10 fake live fills')
    verify(t10['independent_minute_parity_done'] is False,'T10 wide minute parity claim')
    verify(b03['status']=='B03_DEV_FROZEN_PATH_RISK_SENSITIVITY_NOT_FILL_BACKTEST','B03 status')
    verify(b03['quote_based_execution_not_inferred'] is True,'B03 fill warning')
    verify(b03['reference_firm_loss_limit_actual_verified'] is False,'B03 funding terms')
    verify(t13['status']=='B05C_T13_COMPLETE_ADAPTIVE_DEV_NOT_OOS','B05C status')
    verify(t13['actual_fills_verified'] is False,'B05C actual fills claimed')
    verify(t13['router_gate']['decision']=='B05C_T13_FAIL_DO_NOT_PROMOTE','B05C trade result')
    coverage={}
    for sc,old_net in [('baseline',6220.0),(STRESS,5102.5)]:
        z=t10['scenarios'][sc]
        verify(z['frozen_T05_last_simulated_trades']==115,'T10 trade parity '+sc)
        verify(z['frozen_T05_last_simulated_net_usd_NOT_EXECUTABLE']==old_net,
               'T10 net parity '+sc)
        verify(z['both_endpoints_valid_n']==113,'T10 quote coverage '+sc)
        verify(z['actual_exchange_sequence_or_broker_fill_verified'] is False,
               'T10 misclassified fills')
        verify(sum(m['trades'] for m in z['per_month'])==115,
               'T10 monthly trade count '+sc)
        verify(sum(m['quote_pairs_valid'] for m in z['per_month'])==113,
               'T10 monthly quote valid '+sc)
        verify(tuple(m['month'] for m in z['per_month'])==MONTHS,
               'T10 monthly chronology '+sc)
        entry=z['entry_quote_categories'];exit=z['exit_quote_categories']
        verify(entry['VALID_STRICT_PRIOR_BBO']==113 and
               entry['STALE_GT_250MS']==2 and
               entry['MISSING']==0 and entry['LOCKED_OR_CROSSED']==0,
               'T10 entry classifications')
        verify(exit['VALID_STRICT_PRIOR_BBO']==114 and
               exit['STALE_GT_250MS']==1 and
               exit['MISSING']==0 and exit['LOCKED_OR_CROSSED']==0,
               'T10 exit classifications')
        feb=next(x for x in z['per_month'] if x['month']=='2026-02')
        verify(feb['quote_pairs_valid']==11 and feb['trades']==13,
               'T10 FEB exception count')
        coverage[sc]={
            'total_model_trades':115,'matched_two_endpoints':113,
            'matched_pct':round(100*113/115,2),
            'unmatched_trade_count':2,'unmatched_month':'2026-02',
            'entry_valid_n':113,'entry_stale_n':2,
            'exit_valid_n':114,'exit_stale_n':1,
            'entry_model_outside_prior_bbo_n':
                z['entry_last_fill_outside_prior_bbo_n'],
            'exit_model_outside_prior_bbo_n':
                z['exit_last_fill_outside_prior_bbo_n'],
            'entry_model_outside_valid_prior_bbo_pct':
                round(100*z['entry_last_fill_outside_prior_bbo_n']/113,2),
            'exit_model_outside_valid_prior_bbo_pct':
                round(100*z['exit_last_fill_outside_prior_bbo_n']/114,2),
            'quote_pair_is_executable_fill':False
        }
    ref={}
    for sc,net,dd in [('baseline',6220.0,1725.0),(STRESS,5102.5,1797.5)]:
        x=b03['scenarios'][sc]
        verify(x['frozen_T05_trades']==115 and x['frozen_T05_net_usd_UNMODIFIED']==net,
               'B03 model unchanged '+sc)
        verify(x['DD_at_zero_extra_ticks_chronologically']==dd,
               'B03 corrected Last DD '+sc)
        for ticks in ('0','1','2','4'):
            r=x['surcharge_alternatives'][ticks]
            verify(r['trades']==115 and r['trades_or_stop_paths_recomputed'] is False,
                   'B03 zero reroute guarantee')
        ref[sc]={'trades':115,'net_usd':net,'chronological_last_envelope_dd_usd':dd}
    z=b03['scenarios'][STRESS]['surcharge_alternatives']['1']
    verify(z['adjusted_net_usd_FROZEN_PATH_ONLY']==3952.5 and
           z['pf_FROZEN_PATH_ONLY']==1.23717 and
           z['last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH']==1887.5,
           'B03 stress extra 10 RT parity')
    ref['stress_plus_10usd_per_trade_FIXED_PATH']={
        'net_usd':3952.5,'profit_factor':1.23717,
        'last_envelope_dd_usd':1887.5,
        'below_illustrative_pf_1p25':True,
        'actual_broker_drawdown_verified':False
    }
    gates=t13['router_gate']
    stress=t13['model_outputs']['T05_PLUS_T13_ROUTER'][STRESS]
    old=t13['model_outputs']['T05_377'][STRESS]
    verify(old['trades']==115 and old['net_usd']==5102.5,'B05C T05 frozen')
    verify(stress['trades']==210 and stress['net_usd']==-1810.0,
           'B05C shared router counts')
    verify(gates['router_t05_trades']==91 and gates['router_t13_trades']==119 and
           gates['router_t13_attributed_net_stress_usd']==-6572.5,
           'B05C owner allocation')
    verify(gates['delta_stress_usd']==-6912.5 and
           gates['delta_stress_extra10_usd']==-7862.5,'B05C negative increment')
    verify(gates['required_gates']['T05_retains_at_least_104_of_115_original_trades']
           is False,'B05C explicit capacity gate')
    displacement=115-gates['router_t05_trades']
    verify(displacement==24,'B05C displacement')
    return {
       'status':'B05D_AUDITED_DECISION_NO_NEW_TRADE_HYPOTHESIS_TESTED',
       'source_reports':{
           't10_run':38177582699,'b03_run':38179855851,'b05c_run':38183250984},
       'source_months':list(MONTHS),'source_days':140,'eligible_days':135,
       'holdouts_opened':False,'new_alpha_models_tested':0,
       'licensed_tick_or_trade_level_exported':False,
       'quote_coverage':coverage,
       't05_last_only_economic_headroom':ref,
       'portfolio_capacity_counterexample':{
         'router_trades':210,'router_t05_trades':91,
         'router_t13_trades':119,'t05_standalone_trades':115,
         't05_displaced':displacement,
         't05_displaced_pct':round(100*displacement/115,2),
         't13_stress_attribution_usd':-6572.5,
         'router_stress_increment_vs_t05_usd':-6912.5,
         'fixed_equal_bar_t05_priority_prevents_earlier_occupancy':False,
         'retains_104_t05_gate_passed':False},
       'market_data_capabilities':{
         'last_trade_price_and_quantity':'OBSERVABLE',
         'historical_asof_prior_L1_bid_ask':'OBSERVABLE_WITH_250MS_98P26_PERCENT_PAIR_COVERAGE',
         'true_CME_aggressor_side_tag_5797':'NOT_IN_CURRENT_NINJATRADER_TXT',
         'cross_stream_total_event_sequence_or_matching_sequence_id':'NOT_PROVEN',
         'level2_order_depth_and_queue_position':'NOT_IN_CURRENT_EXPORT',
         'true_bid_ask_volume_flow':'NOT_IN_CURRENT_EXPORT',
         'full_trade_barrier_execution_and_broker_fills':'NOT_IDENTIFIED',
         'signed_delta_and_passive_absorption':'NOT_IDENTIFIABLE_FROM_CURRENT_EXPORT',
         'market_replay_L1_L2_sequenced_file':'NOT_ACQUIRED_OR_AUDITED'},
       'prior_adaptive_secondary_families':FAMILY_HISTORY,
       'gates':{
         '100pct_strict_prior_quote_coverage':False,
         'quoted_endpoint_is_confirmed_fill':False,
         'stress_plus10_pf_at_least_1p25':False,
         'shared_router_preserved_104_T05_trades':False,
         'candidate_T13_incremental_net_positive':False,
         'actual_funding_rules_verified':False,
         'T_holdouts_opened':False},
       'decisions':[
         'BLOCK_ORDER_FLOW_ALPHA_FROM_EXISTING_EXPORTS',
         'BLOCK_LIVE_OR_FUNDING_USE_OF_T05',
         'PAUSE_ADAPTIVE_T14_WITHOUT_NEW_INFORMATION',
         'REQUIRE_NEW_SEQUENCED_SOURCE_OR_DIFFERENT_TESTABLE_NON_FLOW_MECHANISM'],
       'external_spec_sources':DOCS,
       'new_market_data_source_opened':False
    }

def report(x):
    c=x['quote_coverage']['baseline'];s=x['quote_coverage'][STRESS]
    f=x['t05_last_only_economic_headroom']['stress_plus_10usd_per_trade_FIXED_PATH']
    r=x['portfolio_capacity_counterexample']
    lines=[
      '# NQ-B05D — Diagnóstico de datos y ejecutabilidad antes de otra familia T14',
      '',
      '**SIN NUEVO BACKTEST**, basado en artefactos T10, B03 y B05C inalterados,',
      '**SIN APERTURA OOS**: desarrollo Oct2025–Abr2026, 140 días fuente, 135 elegibles.',
      '',
      '## 1. Bid/Ask y Last: lo identificable (NO fills del broker)',
      '',
      f"- T05 {c['matched_two_endpoints']}/{c['total_model_trades']} trades con Bid+Ask strictly-prior y frescos <=250ms (**{c['matched_pct']}%**). Excepciones {c['unmatched_trade_count']}, ambas febrero 2026.",
      f"- Entrada: {c['entry_stale_n']} endpoints STALE; salida: {c['exit_stale_n']} STALE (pueden coincidir en trades).",
      f"- Last synthetic fill fuera de BBO previo válido: base entrada {c['entry_model_outside_prior_bbo_n']}/113 = {c['entry_model_outside_valid_prior_bbo_pct']}%, salida {c['exit_model_outside_prior_bbo_n']}/114 = {c['exit_model_outside_valid_prior_bbo_pct']}%.",
      f"- En estrés: entrada {s['entry_model_outside_prior_bbo_n']}/113 = {s['entry_model_outside_valid_prior_bbo_pct']}%; salida {s['exit_model_outside_prior_bbo_n']}/114 = {s['exit_model_outside_valid_prior_bbo_pct']}%.",
      '- NO extrapolar estos porcentajes a probabilidad de fills: precios teóricos Last incluyen slippage supuesto y fuentes pueden tener relojes/secuencias diferentes.',
      '',
      '## 2. ¿Se puede estudiar order flow verdadero?',
      '',
      '| Variable | Dictamen |',
      '|---|---|',
      '| Last precio y qty | Sí, de prints históricos exportados |',
      '| Cotización bid/ask anterior al endpoint | Parcial, 113/115 con máximo 250ms |',
      '| Orden TOTAL Last/Bid/Ask a timestamp idéntico | NO probado, tres archivos sin secuencia común |',
      '| Agresor comprador/vendedor de CME (tag 5797) | NO incluido en estos TXT |',
      '| Profundidad L2, colas y size real disponible | NO incluido |',
      '| Delta agresor real, absorción pasiva | NO identificable de forma verificable |',
      '| Fill broker/estrategia exit path al sustituir BBO | NO validado |',
      '',
      '## 3. Riesgo, capital compartido y fricción',
      '',
      f"- T05 estrés 115 trades +USD 5102.50, DD Last USD 1797.50. **+$10 RT** congelado: net USD {f['net_usd']}, PF **{f['profit_factor']} <1.25**, DD Last USD {f['last_envelope_dd_usd']}. NO es ejecución dinámica re-backtesteada.",
      f"- T05 sola 115 trades vs router T05+T13 {r['router_trades']} trades (T05 {r['router_t05_trades']}, T13 {r['router_t13_trades']}), **{r['t05_displaced']} T05 desplazados = {r['t05_displaced_pct']}%**, T13 aportó USD {r['t13_stress_attribution_usd']} estrés. Prioridad de T05 si empatan misma barra NO preserva T05 futura.",
      '- 2 operaciones/día, riesgo compartido y orden cronológico deben mantenerse en toda comparación incremental; no sumar profits standalone ni usar futuro.',
      '- Referencia DD USD2000 no comprobada en una firma. Cuenta nominal 50K no equivale a pérdida admisible ni retorno invertido.',
      '',
      '## 4. Decisión',
      '',
    ]
    lines.extend('- **'+decision+'**' for decision in x['decisions'])
    lines+=['',
      'No abrir mayo–junio 2026 o julio–septiembre 2026 para rescatar un sistema; no llamar OOS a los siete meses ya reutilizados.',
      'No T14 automático: evaluar compra/licencia de fuente unificada Market Replay L1/L2 o CME con AggressorSide/seq solo si objetivo de mecanismo lo justifica. Es una posibilidad de auditoría, NO garantía de alpha.',
      'Antes de nuevo alpha, especificar secuenciación de proveedor, contratos/rollover, diferencia Last/L1/L2, costo de adquisición, límites de uso/reproducción, simulación dinámica de TP/SL bajo quotes y presupuesto de familias.',
      '',
      '## Documentación técnica (no fuente de retornos)','']
    lines.extend('- '+label+': '+url for label,url in x['external_spec_sources'].items())
    return '\n'.join(lines)+'\n'

def self_test(t10,b03,t13):
    value=audit(t10,b03,t13)
    assert value['quote_coverage']['baseline']['matched_pct']==98.26
    assert value['portfolio_capacity_counterexample']['t05_displaced']==24
    a=json.loads(json.dumps(t10));a['scenarios']['baseline']['both_endpoints_valid_n']=115
    try:audit(a,b03,t13)
    except ValueError:pass
    else:raise AssertionError('Quote invariant intentionally broken not detected')
    b=json.loads(json.dumps(b03));b['holdouts_opened']=True
    try:audit(t10,b,t13)
    except ValueError:pass
    else:raise AssertionError('Sealed boundary intentionally broken not detected')
    c=json.loads(json.dumps(t13));c['router_gate']['router_t05_trades']=104
    try:audit(t10,b03,c)
    except ValueError:pass
    else:raise AssertionError('Displacement invariant intentionally broken not detected')
    return 'PASS_3_SYNTHETIC_FAIL_CLOSED_MUTATIONS'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--t10',required=True,type=Path)
    p.add_argument('--b03',required=True,type=Path)
    p.add_argument('--b05c',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    t10=json.loads(a.t10.read_text(encoding='utf8'))
    b03=json.loads(a.b03.read_text(encoding='utf8'))
    b05c=json.loads(a.b05c.read_text(encoding='utf8'))
    tests=self_test(t10,b03,b05c)
    x=audit(t10,b03,b05c)
    x['self_tests']=tests
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf8')
    a.report.write_text(report(x),encoding='utf8')
    print('NQ_B05D_SAFE_DECISION='+json.dumps({
        'status':x['status'],'quote_coverage_pct':x['quote_coverage']['baseline']['matched_pct'],
        'T05_retained':x['portfolio_capacity_counterexample']['router_t05_trades'],
        'T05_displaced':x['portfolio_capacity_counterexample']['t05_displaced'],
        'extra_10_pf':f'{f:.5f}' if (f:=x['t05_last_only_economic_headroom']['stress_plus_10usd_per_trade_FIXED_PATH']['profit_factor']) else None,
        'tests':tests,'decisions':x['decisions'],'holdouts_opened':False},sort_keys=True))
