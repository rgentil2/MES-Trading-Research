#!/usr/bin/env python3
"""NQ B03 aggregate 7 DEV frozen T05 Last-path surcharge/DD diagnostic only."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from nq_tick_short_horizon_month import MONTHS
from nq_t04_execution import SCENARIOS
from nq_b03_execution_headroom import SURCHARGE_TICKS_PER_SIDE,surcharge_usd,EXPECTED

HISTORICAL_T08_DD={'baseline':1750.0,
                   'stress_1p5_fee_2ticks_each_side':1825.0}
REFERENCE_DD_USD=2000.0 # Historical illustrative, not actual firm rules

def stitch(rows):
    """Correct chronological month-ordered high-water, as T08 aggregation intended."""
    net=0.;hwm=0.;dd=0.;close_hwm=0.;close_dd=0.
    gross_pos=0.;gross_neg=0.;trades=0
    for row in rows:
        seg=row['last_envelope_segment']
        if abs(seg['equity']-row['frozen_path_adjusted_net_usd'])>.011:
            raise ValueError('Monthly equity not reconciled')
        if seg['low']>seg['high'] or seg['closed_low']>seg['closed_high']:
            raise ValueError('Impossible Last envelope')
        dd=max(dd,seg['max_dd'],hwm-(net+seg['low']))
        close_dd=max(close_dd,seg['closed_dd'],close_hwm-(net+seg['closed_low']))
        hwm=max(hwm,net+seg['high'])
        close_hwm=max(close_hwm,net+seg['closed_high'])
        net=round(net+row['frozen_path_adjusted_net_usd'],2)
        trades+=row['trades']
        gross_pos+=row['gross_positive_net_usd']
        gross_neg+=row['gross_negative_net_usd']
    return {'trades':trades,'adjusted_net_usd_FROZEN_PATH_ONLY':round(net,2),
        'pf_FROZEN_PATH_ONLY':round(gross_pos/gross_neg,5) if gross_neg else None,
        'last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH':round(dd,2),
        'closed_trade_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH':round(close_dd,2),
        'illustrative_dd_headroom_vs_2000_usd':round(REFERENCE_DD_USD-dd,2),
        'illustrative_dd_below_2000':dd<REFERENCE_DD_USD,
        'actual_broker_drawdown_verified':False}

def aggregate(months):
    if sorted(months)!=sorted(MONTHS):
        raise ValueError('Require seven and ONLY seven registered DEV months')
    if any(months[m]['month']!=m or
           months[m]['status']!='B03_FROZEN_PATH_ACCOUNTING_ONLY' or
           months[m]['holdouts_opened'] is not False or
           months[m]['chronological_ET_days'] is not True or
           months[m]['month_days_dates_unique'] is not True or
           months[m]['no_trade_or_price_level_exported'] is not True or
           months[m]['actual_fills_verified'] is not False
           for m in MONTHS):
        raise ValueError('Invalid B03 DEV source/QC')
    result={}
    for sc in SCENARIOS:
        exp_n,exp_net=EXPECTED[sc]
        original_n=sum(months[m]['scenarios'][sc]['frozen_trades'] for m in MONTHS)
        original_net=round(sum(months[m]['scenarios'][sc]['frozen_last_net_usd'] for m in MONTHS),2)
        orig_bad=sum(months[m]['scenarios'][sc]['original_ambiguities'] for m in MONTHS)
        if original_n!=exp_n or original_net!=exp_net or orig_bad:
            raise AssertionError('Original frozen 115 T05 trade/PnL parity failed')
        d={}
        for ticks in SURCHARGE_TICKS_PER_SIDE:
            rows=[months[m]['scenarios'][sc]['surcharges'][str(ticks)] for m in MONTHS]
            row=stitch(rows)
            predicted=round(exp_net-surcharge_usd(ticks)*original_n,2)
            if row['trades']!=exp_n or abs(row['adjusted_net_usd_FROZEN_PATH_ONLY']-predicted)>.01:
                raise AssertionError('Frozen-path cost delta mismatch')
            row['additional_ticks_each_side']=ticks
            row['additional_usd_per_round_trip']=surcharge_usd(ticks)
            row['stress_pf_ge_1p25_illustrative']=(row['pf_FROZEN_PATH_ONLY']>=1.25
                if sc!='baseline' else None)
            row['trades_or_stop_paths_recomputed']=False
            d[str(ticks)]=row
        out={
            'frozen_T05_trades':original_n,
            'frozen_T05_net_usd_UNMODIFIED':original_net,
            'surcharge_alternatives':d,
            'T08_historical_Last_DD':HISTORICAL_T08_DD[sc],
            'DD_at_zero_extra_ticks_chronologically':d['0']['last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH'],
            'DD_difference_from_T08_due_to_clock_or_engine':round(
                d['0']['last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH']-HISTORICAL_T08_DD[sc],2)
        }
        result[sc]=out
    return {
      'status':'B03_DEV_FROZEN_PATH_RISK_SENSITIVITY_NOT_FILL_BACKTEST',
      'source_months':list(MONTHS),
      'source_days':sum(months[m]['source_days'] for m in MONTHS),
      'eligible_days':sum(months[m]['eligible_days'] for m in MONTHS),
      'selected_contract_family':'NQ',
      'reference_firm_loss_limit_actual_verified':False,
      'quote_based_execution_not_inferred':True,
      'holdouts_opened':False,
      'surcharges_fixed_before_results_ticks_each_side':list(SURCHARGE_TICKS_PER_SIDE),
      'scenarios':result,
    }

def report(x):
    lines=['# NQ-B03 — fragilidad de ejecución en T05-377: recargos sobre ruta Last congelada',
    '',
    '**Solo análisis contrafactual, no fills de broker ni nuevo backtest de TP/SL.**',
    'Los recargos NO cambian las decisiones de entrada/salida, daily stop o TP/SL. '
    'Los límites de fondeo ($2000) son ilustrativos, no verificados.',
    'Meses ET y días procesados cronológicamente. '
    'Mayo–septiembre no abiertos para resultados.',
    '',
    '| Escenario T04 | Extra ticks/lado | Cargo extra RT USD | Trades congelados | Neto ajustado USD (no ejecutable) | PF de esa ruta | DD Last-envelope USD | Margen a $2000 ilustrativo |',
    '|---|---:|---:|---:|---:|---:|---:|---:|']
    for sc,row in x['scenarios'].items():
        for ticks,z in row['surcharge_alternatives'].items():
            lines.append(f"| {sc} | {ticks} | {z['additional_usd_per_round_trip']} | {z['trades']} | "
             f"{z['adjusted_net_usd_FROZEN_PATH_ONLY']} | {z['pf_FROZEN_PATH_ONLY']} | "
             f"{z['last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH']} | "
             f"{z['illustrative_dd_headroom_vs_2000_usd']} |")
    lines+=['','## Comprobación T08 sin recargos','']
    for sc,row in x['scenarios'].items():
        lines.append(f"- {sc}: T08 DD anterior = {row['T08_historical_Last_DD']} USD; "
          f"DD B03 cronológico con extra 0 = {row['DD_at_zero_extra_ticks_chronologically']} USD; "
          f"diferencia = {row['DD_difference_from_T08_due_to_clock_or_engine']} USD.")
    lines+=['','## Alcance y decisión','',
      '- Recargo adicional de 1 tick por lado = USD10 por operación de 1 NQ; '
      '2 = USD20, 4 = USD40. No son precios de compra/venta observados.',
      '- Cualquier cambio del DD con 0 recargo es una advertencia de orden de días '
      'o auditabilidad T08, NO una mejora de la estrategia.',
      '- No se infiere ni manipula Bid/Ask como fill; T10 solo registró 113/115 BBO '
      'frescos. La fuente Minute↔Tick coincidió para un único día B02.',
      '- Descartado promover T05 a fondeo por este reporte: aún faltan '
      'precio ejecutable, fee de firma, trailing real, secuencia, OOS.',
      '- Próximo paso: NQ-B04 robustez por semana/mes/trimestre y NQ-B05 nueva '
      'estrategia NQ independiente y aportación incremental al router.',
      '']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    r={}
    for file in a.inputs.rglob('nq_b03_*.json'):
        value=json.loads(file.read_text(encoding='utf8'))
        if value['month'] in r:raise ValueError('Duplicate DEV monthly result')
        r[value['month']]=value
    result=aggregate(r)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    a.report.write_text(report(result),encoding='utf8')
    print('NQ_B03_AGGREGATE='+json.dumps({
        'source_days':result['source_days'],'eligible_days':result['eligible_days'],
        'scenarios':{sc:{t:{
          'net':z['adjusted_net_usd_FROZEN_PATH_ONLY'],
          'pf':z['pf_FROZEN_PATH_ONLY'],
          'dd':z['last_envelope_max_dd_usd_CHRONOLOGICAL_FROZEN_PATH']}
          for t,z in row['surcharge_alternatives'].items()}
          for sc,row in result['scenarios'].items()}},sort_keys=True))
