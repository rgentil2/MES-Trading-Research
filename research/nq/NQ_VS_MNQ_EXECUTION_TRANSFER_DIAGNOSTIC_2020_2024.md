# NQ vs MNQ — mismo backtest congelado, coste por instrumento y riesgo de fondeo

**2026-10-10.** Diagnóstico de transferencia de tamaño/instrumento sobre **operaciones ya simuladas** de H69 y H73–H78. No crea ni valida nuevas hipótesis, no altera los SHA/familias congeladas ni abre 2025 o 2026.

## Metodología y costes

- Fuente: operaciones exploratorias del ZIP PRIVADO 2020–2024 de cada familia. El NQ se calcula a partir de idénticos puntos de entrada, salida y stops; **no** es ejecución real ni validación de ticks o de un broker.
- Modelo previo 1 MNQ = **US$3,88** por round-trip (comisión US$1,88 más slippage US$2). Modelo escenario 1 NQ = **US$25,74** (comisión US$5,74 más slippage US$20). Valores de NinjaTrader Free supuestos, NO costes fondeados verificados.
- USD por punto: MNQ **US$2**, NQ **US$20**. 0 puntos de stop en NQ = US$800 antes de costes. Transformación determinista de cada operación: `PnL_NQ = (PnL_MNQ + 3.88) * 10 - 25.74`. El orden de operaciones es idéntico.
- CAGR **equivalente** calculado `((50000+P&L_total)/50000)^(1/5)-1`, sin aportaciones, retiros ni capital real del usuario; no debe confundirse con rentabilidad del fondeo de bolsillo.
- DD es **máximo drawdown realizado a cierres de operación**. No verifica la regla de pérdida por equity flotante de una firma de fondeo; si DD cerrado ya sobrepasa el colchón, es suficiente para rechazar compatibilidad en este escenario.

## Resultado: mismo sistema pero 1 contrato NQ

| Sistema | Trades 2020-24 | 1 MNQ neto | 1 NQ neto | CAGR nominal 50k NQ | PF NQ | DD cerrado 1 NQ | Pasa 15% | DD <= US$2k |
|---|---:|---:|---:|---:|---:|---:|---|---|
| NQ-H69 | 262 | $2,704.44 | $30,466.12 | 9.98% | 1.385 | $8,214.22 | NO | NO |
| NQ-H73 | 139 | $1,140.18 | $13,217.14 | 4.80% | 1.298 | $7,362.20 | NO | NO |
| NQ-H74 | 132 | $1,657.84 | $18,302.32 | 6.44% | 1.494 | $4,179.80 | NO | NO |
| NQ-H75 | 165 | $1,197.30 | $14,127.90 | 5.10% | 1.271 | $6,245.34 | NO | NO |
| NQ-H76 | 92 | $1,091.04 | $12,111.92 | 4.43% | 1.473 | $4,767.76 | NO | NO |
| NQ-H77 | 140 | $2,385.30 | $25,681.40 | 8.64% | 1.695 | $5,414.42 | NO | NO |
| NQ-H78 | 129 | $427.98 | $5,964.54 | 2.28% | 1.136 | $6,660.36 | NO | NO |

## Qué cambió al aumentar el contrato

- H69, comparador más rentable: **US$30,466.12** en cinco años, **9.98% CAGR equivalente** con capital nominal de USD 50k, y **US$8,214.22 de drawdown cerrado**. En 2020 su resultado sería negativo; 2022 aporta más de la mitad del P&L.
- H77 (alta eficiencia por trade): **US$25,681.40**, **8.64% CAGR equivalente**, PF1.695, DD cerrado **US$5,414.42**. Su diagnóstico individual conserva N=140 y dependencia de 2022.
- H74 (cinco años positivos en MNQ): **US$18,302.32**, **6.44% CAGR equivalente**, DD cerrado **US$4,179.80**. Es el mejor DD cerrado de las siete simulaciones, pero aun excede el supuesto límite 2k.
- Los stops de 1 NQ requieren alrededor de **US$575–620 de riesgo bruto mediano por operación** dependiendo de la estrategia. Puede ser demasiado frente a un colchón de solo USD 2k y al drawdown flotante.
- El 15% durante cinco años, normalizando a USD 50k sin flujos, requiere ganar unos **US$50,568** netos acumulados. Ninguna de estas siete simulaciones alcanza ese nivel, y no se dispone aquí del retorno total comparable de VOO y QQQM.
- Escalar NQ mejora el rendimiento nominal pero empeora proporcionalmente la pérdida; **no demuestra mayor ventaja predictiva**. El tamaño por contrato debe derivarse del stop calculado en puntos y del riesgo máximo por operación, no de una rentabilidad objetivo.

## Regla prospectiva recomendada para H79–H150 (NO cambia lo congelado)

- **Priorizar NQ como instrumento de investigación y simulación de ejecución** para las nuevas estrategias conjuntas. Mantener MNQ como instrumento de ajuste fino del tamaño y comparación operativa cuando 1 NQ exceda el límite de riesgo del escenario; el dato es NQ minuto, pero fills/costes reales de NQ y MNQ requieren verificación.
- Congelar por hipótesis conjunto **un router causal, SL, TP, tiempo, límites de riesgo, costes y priorización de entrada** antes de calcular outcomes. Medir P&L, CAGR, drawdown flotante, drawdown cerrado, riesgo por operación, coste 1.5× y benchmark VOO/QQQM del mismo horizonte.
- Mantener H69, H74, H77 y resto de señales en banco exploratorio **sin elevar ninguna a válida ni rescatarla con optimización posterior**; toda modificación será hipótesis nueva, familia Holm nueva.
- En escenario ilustrativo USD 50k y colchón 2k, definir antes del test un máximo de dólares arriesgados por operación y evitar 1 NQ si el stop técnico requiere más. Un tamaño menor en MNQ no permite fabricar 15% de retorno a igual alfa/riesgo.
- Costes de la firma de fondeo, trailing, payout y drawdown flotante deben revalidarse antes de afirmar cumplimiento. **2025/2026 siguen sellados**.

## Auditoría

- Script reproducible: `research/nq/compare_execution_nq_mnq_2020_2024.py` (requiere archivos individuales privados que NO se suben a GitHub público).
- Agregado no sensible: `results/nq_h73_h78/NQ_vs_MNQ_TRANSFER_2020_2024_AGGREGATE.json`.
- Los resultados originales de H69/H73–H78 mantienen sus verdicts de familia y umbrales; análisis **descriptivo**, no test inferencial independiente.