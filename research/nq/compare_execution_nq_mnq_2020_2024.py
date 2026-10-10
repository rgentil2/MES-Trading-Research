#!/usr/bin/env python3
"""DEVELOPMENT ONLY: rescale FROZEN filled 1-MNQ price-proxy trades to 1 NQ.

This does not recompute any price signal or assert actual NQ fills or prop-firm viability.
The inputs are private trade ledgers. Do not upload either input to public GitHub.
2025/2026 are not read.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
R = ROOT / 'results'
FILES = (R / 'NQ_H69_FROZEN_BASELINE_TRADES_PRIVATE.csv', R / 'NQ_H73_H78_COMBINED_STRATEGY_TRADES_PRIVATE.csv')
COST_MNQ = 1.88 + 2.0  # 2 ticks adverse per side at MNQ 0.50 USD/tick
COST_NQ = 5.74 + 20.0  # 2 ticks adverse per side at NQ 5 USD/tick
RESULTS = []
for file in FILES:
    df = pd.read_csv(file)
    assert set(df['year']).issubset({2020, 2021, 2022, 2023, 2024}), 'sealed year attempted'
    for hyp, a in df.groupby('hypothesis', sort=True):
        a = a.sort_values(['session', 'signal_idx'], kind='stable')
        assert not a['session'].duplicated().any(), 'more than 1 trade per session'
        assert (a['model_type'].isin(['strategy', 'baseline'])).all()
        mnq = a['pnl_bracket'].to_numpy(dtype=float)
        # From historical brackets: pnl_MNQ = signed gross points*2 - 3.88
        gross_points_usd_mnq = mnq + COST_MNQ
        nq = gross_points_usd_mnq * 10 - COST_NQ
        cum = np.r_[0.0, nq.cumsum()]
        dd = (np.maximum.accumulate(cum) - cum).max()
        assert np.isfinite(nq).all()
        assert (a.risk_points.to_numpy()>0).all()
        df_year = a[['year']].copy();df_year['nq']=nq
        annual = df_year.groupby('year')['nq'].sum().to_dict()
        total = float(np.sum(nq))
        end = 50000 + total
        cagr = float((end/50000)**(1/5)-1) if end > 0 else None
        profit = float(nq[nq > 0].sum())
        loss = float(-nq[nq < 0].sum())
        results = {
            'strategy':hyp,'trades':int(len(a)),
            'mnq_proxy_net_total_usd':round(float(mnq.sum()),2),
            'nq_rescaled_net_total_usd':round(total,2),
            'nq_rescaled_mean_net_usd':round(float(nq.mean()),2),
            'nq_rescaled_profit_factor':round(profit/loss,3) if loss else None,
            'nq_rescaled_closed_drawdown_usd':round(float(dd),2),
            'nq_nominal_50k_five_year_equivalent_cagr_pct':round(100*cagr,3) if cagr is not None else None,
            'nq_net_total_1_5x_trading_cost_usd':round(total-0.5*COST_NQ*len(a),2),
            'nq_positive_years':sum(v>0 for v in annual.values()),
            'nq_annual_net_usd':{str(k):round(float(v),2) for k,v in annual.items()},
            'nq_min_trade_net_usd':round(float(nq.min()),2),
            'stop_distance_points_median':round(float(a.risk_points.median()),2),
            'one_nq_stop_gross_risk_median_usd':round(float(a.risk_points.median()*20),2),
            'one_nq_stop_gross_risk_max_usd':round(float(a.risk_points.max()*20),2),
            'breaks_2000_closed_drawdown':bool(dd>2000),
            'achieves_15_pct_nominal_cagr': bool(cagr is not None and cagr > 0.15),
        }
        RESULTS.append(results)

RESULTS.sort(key=lambda z: 69 if z['strategy']=='NQ-H69' else int(z['strategy'].split('H')[-1]))
report = {
    'report_id':'NQ_VS_MNQ_SAME_FROZEN_TRADES_2020_2024',
    'date':'2026-10-10',
    'market_years':[2020,2021,2022,2023,2024],
    'data_status':'REUSED_DEVELOPMENT_ONLY_NOT_INDEPENDENT',
    'price_source':'NQ Minute Last 2020-2024, not actual order fills',
    'parent_strategies':['NQ-H69','NQ-H73','NQ-H74','NQ-H75','NQ-H76','NQ-H77','NQ-H78'],
    'cost_model':{'MNQ_1_contract_usd_round_trip':COST_MNQ,'NQ_1_contract_usd_round_trip':COST_NQ,'nq_20_usd_per_point':True,'mnq_2_usd_per_point':True,'fee_source':'Inherited study NinjaTrader Free assumptions, NOT a verified MFFU trading account rate'},
    'conversion':'PnL_1NQ = (pnl_MNQ+3.88)*10 - 25.74, provided 1MNQ and 1NQ share the exact same theoretical entry/exit NQ price path and bracket stop/target points',
    'account_reference_usd':50000,'illustrative_loss_cushion_usd':2000,'years_for_illustrative_CAGR':5,
    'funding_pass':False,'floating_equity_trailing_validated':False,'benchmark_data_checked':False,'voo_qqqm_beaten':None,
    'risks':['No NQ orderbook/tick fill proof','Minute OHLCV stop-first policy does not reconstruct intra-minute order','No firm-specific live pricing or fee validation','Closed drawdown alone is optimistic vs intraday mark-to-market trailing','All strategies fail illustrative 2k closed-DD cushion at 1 NQ','Prior selection on 2020-2024 precludes independent hypothesis evidence'],
    'results':RESULTS
}
(R/'NQ_vs_MNQ_transfer_2020_2024_AGGREGATE.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
lines=['# NQ vs MNQ — mismo backtest congelado, coste por instrumento y riesgo de fondeo','',
'**2026-10-10.** Diagnóstico de transferencia de tamaño/instrumento sobre **operaciones ya simuladas** de H69 y H73–H78. No crea ni valida nuevas hipótesis, no altera los SHA/familias congeladas ni abre 2025 o 2026.','',
'## Metodología y costes', '',
'- Fuente: operaciones exploratorias del ZIP PRIVADO 2020–2024 de cada familia. El NQ se calcula a partir de idénticos puntos de entrada, salida y stops; **no** es ejecución real ni validación de ticks o de un broker.',
'- Modelo previo 1 MNQ = **US$3,88** por round-trip (comisión US$1,88 más slippage US$2). Modelo escenario 1 NQ = **US$25,74** (comisión US$5,74 más slippage US$20). Valores de NinjaTrader Free supuestos, NO costes fondeados verificados.',
'- USD por punto: MNQ **US$2**, NQ **US$20**. 0 puntos de stop en NQ = US$800 antes de costes. Transformación determinista de cada operación: `PnL_NQ = (PnL_MNQ + 3.88) * 10 - 25.74`. El orden de operaciones es idéntico.',
'- CAGR **equivalente** calculado `((50000+P&L_total)/50000)^(1/5)-1`, sin aportaciones, retiros ni capital real del usuario; no debe confundirse con rentabilidad del fondeo de bolsillo.',
'- DD es **máximo drawdown realizado a cierres de operación**. No verifica la regla de pérdida por equity flotante de una firma de fondeo; si DD cerrado ya sobrepasa el colchón, es suficiente para rechazar compatibilidad en este escenario.','',
'## Resultado: mismo sistema pero 1 contrato NQ','',
'| Sistema | Trades 2020-24 | 1 MNQ neto | 1 NQ neto | CAGR nominal 50k NQ | PF NQ | DD cerrado 1 NQ | Pasa 15% | DD <= US$2k |',
'|---|---:|---:|---:|---:|---:|---:|---|---|']
for d in RESULTS:
    lines.append(f"| {d['strategy']} | {d['trades']} | ${d['mnq_proxy_net_total_usd']:,.2f} | ${d['nq_rescaled_net_total_usd']:,.2f} | {d['nq_nominal_50k_five_year_equivalent_cagr_pct']:.2f}% | {d['nq_rescaled_profit_factor']:.3f} | ${d['nq_rescaled_closed_drawdown_usd']:,.2f} | {'YES' if d['achieves_15_pct_nominal_cagr'] else 'NO'} | {'NO' if d['breaks_2000_closed_drawdown'] else 'UNTESTED'} |")
lines += ['','## Qué cambió al aumentar el contrato','',
'- H69, comparador más rentable: **US$30,466.12** en cinco años, **9.98% CAGR equivalente** con capital nominal de USD 50k, y **US$8,214.22 de drawdown cerrado**. En 2020 su resultado sería negativo; 2022 aporta más de la mitad del P&L.',
'- H77 (alta eficiencia por trade): **US$25,681.40**, **8.64% CAGR equivalente**, PF1.695, DD cerrado **US$5,414.42**. Su diagnóstico individual conserva N=140 y dependencia de 2022.',
'- H74 (cinco años positivos en MNQ): **US$18,302.32**, **6.44% CAGR equivalente**, DD cerrado **US$4,179.80**. Es el mejor DD cerrado de las siete simulaciones, pero aun excede el supuesto límite 2k.',
'- Los stops de 1 NQ requieren alrededor de **US$575–620 de riesgo bruto mediano por operación** dependiendo de la estrategia. Puede ser demasiado frente a un colchón de solo USD 2k y al drawdown flotante.',
'- El 15% durante cinco años, normalizando a USD 50k sin flujos, requiere ganar unos **US$50,568** netos acumulados. Ninguna de estas siete simulaciones alcanza ese nivel, y no se dispone aquí del retorno total comparable de VOO y QQQM.',
'- Escalar NQ mejora el rendimiento nominal pero empeora proporcionalmente la pérdida; **no demuestra mayor ventaja predictiva**. El tamaño por contrato debe derivarse del stop calculado en puntos y del riesgo máximo por operación, no de una rentabilidad objetivo.',
'',
'## Regla prospectiva recomendada para H79–H150 (NO cambia lo congelado)', '',
'- **Priorizar NQ como instrumento de investigación y simulación de ejecución** para las nuevas estrategias conjuntas. Mantener MNQ como instrumento de ajuste fino del tamaño y comparación operativa cuando 1 NQ exceda el límite de riesgo del escenario; el dato es NQ minuto, pero fills/costes reales de NQ y MNQ requieren verificación.',
'- Congelar por hipótesis conjunto **un router causal, SL, TP, tiempo, límites de riesgo, costes y priorización de entrada** antes de calcular outcomes. Medir P&L, CAGR, drawdown flotante, drawdown cerrado, riesgo por operación, coste 1.5× y benchmark VOO/QQQM del mismo horizonte.',
'- Mantener H69, H74, H77 y resto de señales en banco exploratorio **sin elevar ninguna a válida ni rescatarla con optimización posterior**; toda modificación será hipótesis nueva, familia Holm nueva.',
'- En escenario ilustrativo USD 50k y colchón 2k, definir antes del test un máximo de dólares arriesgados por operación y evitar 1 NQ si el stop técnico requiere más. Un tamaño menor en MNQ no permite fabricar 15% de retorno a igual alfa/riesgo.',
'- Costes de la firma de fondeo, trailing, payout y drawdown flotante deben revalidarse antes de afirmar cumplimiento. **2025/2026 siguen sellados**.',
'',
'## Auditoría','',
'- Script reproducible: `research/nq/compare_execution_nq_mnq_2020_2024.py` (requiere archivos individuales privados que NO se suben a GitHub público).',
'- Agregado no sensible: `results/nq_h73_h78/NQ_vs_MNQ_TRANSFER_2020_2024_AGGREGATE.json`.',
'- Los resultados originales de H69/H73–H78 mantienen sus verdicts de familia y umbrales; análisis **descriptivo**, no test inferencial independiente.','']
(R/'NQ_vs_MNQ_TRANSFER_2020_2024.md').write_text('\n'.join(lines),encoding='utf-8')
print('saved',len(RESULTS),'rows')
for d in RESULTS:print(d['strategy'], d['nq_rescaled_net_total_usd'],d['nq_rescaled_closed_drawdown_usd'],d['nq_nominal_50k_five_year_equivalent_cagr_pct'])