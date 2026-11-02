# S0.64 — G0 Filtro económico nativo de V5 (instalación y validación)

**Estado 2026-11-02:** código listo en rama S0.64, 25 pruebas del motor puro + 5 pruebas del adaptador mediante SHIM NinjaTrader + validaciones estáticas aprobadas en [Actions #41549165268](https://github.com/rgentil2/MES-Trading-Research/actions/runs/41549165268). **Pendiente prueba real en NinjaTrader Windows F5 / evaluación nativa G0.** NO modifica V5 ni V4; no aporta nuevos tipos de indicadores ni algoritmo genético.

## Propósito

La anterior función `NQNativeStructureFitnessV5` solo ordena por beneficio neto sin verificar todos los límites. `NQNativeG0FitnessV6` asigna un puntaje de **-1e12** a cada candidato que NO cumpla simultáneamente:

| Gate básico G0 | Criterio sobre NQ M1 2020–2022 |
|---|---|
| Expresión válida | `CanonicalReady`, sin redundancia, `EffectiveConditionCount>=1` |
| Beneficio neto histórico | **mayor que 0 USD** con mismas comisiones |
| PF de operaciones cerradas | **>=1,25** |
| Tamaño de muestra | **>=150 operaciones** |
| Frecuencia por mes | **>=5 entradas en CADA uno de los 36 meses calendario** 2020-01 a 2022-12; meses vacíos cuentan 0 |
| Máximo drawdown **CERRADO** | **<=2.000 USD**, recomputado desde equity acumulada de operaciones cerradas (máximo histórico anterior empieza en 0) |
| Fiabilidad de costes | suma de PnL `Trade.ProfitCurrency` debe coincidir con `TradesPerformance.NetProfit` dentro de $0,03; si no, **REJECT** y revisar diferencias |

Orden de causas: datos inválidos/no históricos o PnL de comercio no conciliado → número de operaciones → frecuencia mensual → neto negativo → PF insuficiente → DD cerrado >2k → `PASS_PROVISIONAL_CLOSED_EQUITY`.

**Importante:** El filtro de fitness actúa **DESPUÉS** de `RunIteration`. El optimizador V5 todavía ahorra backtests estructuralmente repetidos, pero no puede saber el PF/DD del candidato sin simularlo. Cuando ningún candidato cumpla G0, NinjaTrader podría seguir mostrando 20 filas, todas con valor de fitness `-1e12`. Eso NO significa que estén aprobadas; mirar `NQ_G0 REJECT`.

**G0 NO certifica riesgo real de la cuenta My Funded Futures**: aún faltan drawdown flotante/intrabar, pérdidas diarias y trailing drawdown según reglas vigentes, costes de mercado real, segmentación IS/ISV/OOS, 132 indicadores, verdadera mutación/cruce y portfolio. No abrir años reservados 2023–2026.

## Archivos de instalación (solo dos, V5 ya instalado)

| Archivo nuevo | Destino bajo `Documentos\\NinjaTrader 8\\bin\\Custom` |
|---|---|
| `research/nq/ninjatrader/NQNativeG0RulesV6.cs` | `Strategies` |
| `research/nq/ninjatrader/NQNativeG0FitnessV6.cs` | `OptimizationFitnesses` |

Descarga cada archivo desde GitHub con **Raw** (no el HTML). Cierra NT8, copia ambos, abre **New → NinjaScript Editor → F5**. Si hay errores, no ejecutes y envía primera línea/archivo y captura de mensajes.

## Smoke real controlado con la plantilla que acabamos de guardar

1. Abre Strategy Analyzer y carga plantilla **`NQ_V5_UNIQUE20_2020_2022`**.
2. **Guarda una copia de la plantilla** como `NQ_V5_G0_20_2020_2022` **ANTES** de cambios: no sobrescribir la primera.
3. Conservar `Backtest type=Optimization`, **Strategy=NQNativeGeneticLabV5**, **Optimizer=NQNativeUniqueOptimizerV5**, **Unique candidates target=20**, `seed=20261102`, `Max attempts=2000`, `Keep best=20` y los **mismos 20 rangos y el mismo NQ Last M1 2020–22** del S0.63, Standard (Fastest), slippage2, comisión marcada con plantilla NinjaTrader Brokerage.
4. **Cambiar SOLO** `Optimize on` de `NQNativeStructureFitnessV5` a **`NQNativeG0FitnessV6`**.
5. Abrir **New → NinjaScript Output**, pestaña Output 1. Ejecutar Run una sola vez.
6. Verificar `NQ_V5 BEGIN ... target=20 selectedParams=20` y `END executed=20 generatedUnique=20 failure=0`, comparar las mismas 20 firmas de la anterior búsqueda con la misma semilla. Deben aparecer 20 mensajes `NQ_G0 REJECT reason=...` o de `PASS`. Se esperan **0 candidatos aprobados** dados los resultados S0.63 (PF<1,25 para los cuatro únicos con PnL>0).
7. **Parar y reportar si aparece** `PNL_MISMATCH_NATIVE_VS_TRADE_HISTORY`, `EXCEPTION`, resultado positivo sin filtro, diferencias de 20 genes, o F5 error. No corregir comisiones arbitrariamente para que pase. Enviar screenshot de Optimization + texto `NQ_G0` y `NQ_V5 END`.

## Auditoría correcta del puntaje

- **PASS provisional:** Value=neto USD positivo, solo si net, PF, 150 trades, 36 meses con cinco y DD cerrado <=2k pasan.
- **REJECT:** Value=-1e12. Una fila que aparezca en Optimization Results no equivale a una estrategia aceptada.
- Sin trades o fuera de IST 2020–22: **REJECT**.
- Regla de `PNL_MISMATCH`: necesita diagnóstico de base comisiones reales vs trade p/l; no silenciarla sin evidencia.

El motor G0 puro se validó de forma independiente con casos elegibles, PF bajo, drawdown excedido, 179 operaciones faltando un mes, <150 trades, PnL con 1 USD de diferencia, datos 2023 y fechas fuera de orden. La clase Fitness también se compiló contra un SHIM simulado de la API NT8, **no** contra tu instalación Windows.

**Referencia oficial:** NinjaTrader `OnCalculatePerformanceValue`, `SystemPerformance.AllTrades`, `Trade.ProfitCurrency`, `Trade.Entry.Time`. Todas las reglas operan sobre operaciones históricas cerradas.
