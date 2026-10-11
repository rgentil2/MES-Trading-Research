# NQ T10 — Auditoría real de cotizaciones Bid/Ask estrictamente anteriores a T05-377

**Fecha:** 11 de octubre de 2026. **Decisión:** `T05_377_PRIOR_BBO_COVERAGE_98P26_PERCENT_NOT_EXECUTION_VALIDATED`. 
**Estado del estudio:** investigación exploratoria de control de calidad; NO representa fills reales, una nueva prueba de alpha ni una aprobación de fondeo.

## Ejecución reproducible y procedencia

- Prerregistro previo: `NQ_T10_T05_377_BBO_EXECUTION_QC_PREREG_2026_10_11.md`.
- Código: `nq_t10_t05_bbo_endpoints.py`, `nq_t10_aggregate.py`; pruebas sintéticas `test_nq_t10_t05_bbo_endpoints.py` **PASS**.
- Workflows: [T10 todos los meses DEV (run 38177036580)](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177036580), seis meses SUCCESS y diciembre con ERROR DE ORDENACIÓN DE LISTA en agregación (no falla de datos / estrategia); [recuperación únicamente diciembre + consolidación de los siete meses (run 38177472643)](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177472643) SUCCESS. Se corrigió el orden cronológico por fechas ET a través del rollover, sin tocar las operaciones, costos, períodos, P&L o señales. El segundo workflow publica el artifact `t10-complete-seven-month-qc-results` con JSON y Markdown agregados.
- Datos privados comprobados por SHA256 en `rgentil2/NQ-Ticks-Dev-2026`; NQ Last/Bid/Ask de octubre 2025–abril 2026, 140 fechas fuente, 135 sesiones elegibles. Ningún dato de resultados mayo–junio de 2026; julio–septiembre sigue sellado; antiguos holdouts 2025/2026 del programa de minutos nunca se abrieron.
- **Regresión exacta** con T05/T04 anterior, sin alterar una sola decisión: 115 operaciones, **+USD 6.220 base** y **+USD 5.102,50 con estrés**, bajo *costes de simulador no verificados*.

## Resultado principal: cobertura de cotizaciones estrictamente anteriores a los fills simulados

| Mes DEV | Trades T05-377 simulados | Entrada y salida con BBO estrictamente anterior válido, <=250ms | Cobertura |
|---|---:|---:|---:|
| Octubre 2025 | 15 | 15 | 100 % |
| Noviembre 2025 | 8 | 8 | 100 % |
| Diciembre 2025 | 22 | 22 | 100 % |
| Enero 2026 | 19 | 19 | 100 % |
| Febrero 2026 | 13 | **11** | **84,62 %** |
| Marzo 2026 | 21 | 21 | 100 % |
| Abril 2026 | 17 | 17 | 100 % |
| **Total** | **115** | **113** | **98,26 %** |

Desglose exacto de los 115 endpoints **escenario base**:
- Entrada: **113 válidas, 2 anticuadas más de 250ms**, 0 ausentes y 0 Bid/Ask bloqueado/cruzado.
- Salida: **114 válidas, 1 anticuada más de 250ms**, 0 ausentes y 0 bloqueado/cruzado.
- Dos trades de febrero no tienen un par con ambas cotizaciones elegibles; una de las excepciones afecta entrada y otra puede afectar también salida. **No inferir que son tres trades distintos**; las categorías son por endpoint.

El umbral de 250ms proviene del QC previo, no de maximizar retornos T05. Sólo se permite una cotización `quote_timestamp < last_model_endpoint_timestamp`. Quotes que coinciden exactamente en la misma marca de tiempo quedan excluidas.

## Advertencia monetaria fundamental

En las 113 operaciones pareadas se observó una **diferencia contable de +USD290 BASE** o **+USD1.235 STRESS** al sustituir hipotéticamente solo los precios de los dos endpoints por la cara Bid/Ask correspondiente; NO son incrementos de rendimiento ni re-backtests operables. Los stops, TP, secuencias intratrade, decisiones de nuevos trades, slippage, cola y noticias **no fueron recalculados**. Más aún, sólo se incluyen 113 operaciones pareadas y las otras dos no deben imputarse favorablemente.

- El precio de entrada del modelo Last se situaba **fuera** del BBO estrictamente anterior en **46 de 113 entradas con quote válida (base)**.
- El precio de salida Last modelado se situaba **fuera** del BBO estrictamente anterior en **75 de 114 salidas con quote válida (base)**.
- Con el modelo de estrés, las cifras son **56/113** en entradas y **79/114** en salidas. Los precios del modelo incluyen slippage adverso, de modo que estas diferencias no demuestran que la fuente esté corrupta; sí indican que el BBO previo NO puede sustituirse mecánicamente como si fuese fill garantizado.
- Los spreads medianos por mes fueron aproximadamente **2–3 ticks** tanto en entradas como salidas. La diferencia entre Last y BBO puede responder a latencia de exportación, sequenciación distinta por archivo, cambios del mercado y slippage supuesto.

**Por tanto: 98,26 % es cobertura técnica, NO 98,26 % de probabilidad de ejecución, de operaciones ganadoras, ni tasa de llenado de la firma de fondeo.** La pantalla ingenieril de cobertura plena (100 %) queda **NO SUPERADA**, sin descartar T05 de la biblioteca de investigación.

## Criterios / próximos trabajos para NQ-only multi-strategy portfolio

1. **Conciliación independiente de fuente:** cotejar una sesión DEV NQ, contrato exacto, de la fuente original 1 minuto que permanece en ZIP privado contra los Tick Last originales. Prueba sintética 34/34 ya aprobada; falta el match real por OHLCV minuto, timestamps ET/DST y rollover. No subir el ZIP privado ni mezclar meses sellados.
2. **Calidad de secuencia/fills:** un as-of Bid/Ask con dos archivos exportados separados no tiene orden real de eventos compartiendo timestamp. La sustitución contable T10 no basta. Preparar un modelo de ejecución con datos de orden fiable o estrés de fill más adverso, reconstruyendo toda la ruta SL/TP en vez de reemplazar endpoints congelados. No estimar P&L nuevo a partir de +USD290/+USD1.235.
3. **Robustez de T05:** frecuencia mínima por mes, riesgo flotante, límites actuales del programa fondeado, spreads, costes de NQ/MNQ y ejecución en plataforma. Solo si pasan gates, aplicar una sola validación interna mayo–junio y holdout julio–septiembre después de congelamiento.
4. **Nueva estrategia independiente** para la futura cartera NQ: T09 rápida reversión de apertura **falló** incremento neto con capital compartido, de modo que la familia siguiente debe medir un mecanismo diferente y evaluar su valor incremental vs T05 **con el mismo router**. Ejemplo para formular/prerregistrar: aceptación direccional de VWAP o recuperación de desequilibrio con ventanas causales de Last; no usar delta agresor ficticio inferido de Last ni explorar arbitrariamente Fibonacci.
5. **Benchmark económico:** superar `max(15 %, CAGR VOO-TR, CAGR QQQM-TR)` con fechas y capital/riesgo consistentes; cuenta nominal 50K no equivale a retorno personal de fondeo. Ningún resultado de estos siete meses acredita rentabilidad anual futura.

**Estado:** T05-377 = `RISK_SCREEN_CONDITIONAL`, `EXECUTION_QUALITY_INCOMPLETE`, `OOS_UNOPENED`. T09 = `PORTFOLIO_INCREMENTAL_FAIL`. **No comprar aún evaluación ni declarar cartera aprobada.**
