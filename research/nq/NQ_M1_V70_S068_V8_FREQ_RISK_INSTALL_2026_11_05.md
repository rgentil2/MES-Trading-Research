# NQ V8 — diagnóstico M1 de frecuencia + DD de equity al cierre de barras (S0.68)

**Código NinjaScript:** [NQNativeGeneticLabV8Audit.cs](ninjatrader/NQNativeGeneticLabV8Audit.cs)

## Objetivo

Añade registros de frecuencia y equity sin modificar ni sustituir V5, G0 V6 o G0 V7. `NQNativeGeneticLabV8Audit : NQNativeGeneticLabV5` utiliza la implementación original `base.OnBarUpdate()` **una sola vez por barra**; el observador realiza un recuento independiente de señales después de la ejecución. No abre ni cierra operaciones adicionales. La compatibilidad nativa aún debe comprobarse por F5 de NT8 y comparando las 20 ejecuciones anteriores.

* **Frecuencia:** en cada año 2020/2021/2022 cuenta barras M1, barras dentro de 09:35–11:27, barras tras calentamiento, barras con señal de dirección bruta, ausencia de dirección, señales con posición abierta, bloqueo por máximo diario, ATR inválido, presupuesto stop>$300, veto pérdida cerrada diaria, y **submissions previstas** (diagnóstico). V8 imprime además cada mes de 2022 con `rawDirectional`, `predictedSubmissions`, `actualCompletedTrades`.
* **Equity cronológica M1:** por cada **cierre de barra M1** del backtest calculamos equity de una sola estrategia en US$ como `AllTrades.TradesPerformance.Currency.CumProfit + Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0])`. Seguimiento de peak-to-trough de equity, DD anual desde pico del año, DD diario de cierres y menor equity respecto al saldo cerrado de comienzo de sesión. **No hay acceso a la cronología dentro de la barra; gaps, orden/filled intra-bar, comisiones pendientes, Bid/Ask y reglas de drawdown trailing de MFFU no están medidos.** Los valores son un diagnóstico M1 bar-close, no certificación de cuenta.
* **Importante:** el conteo rawDirectional observa señales *independientemente* de una posición abierta y otros filtros. El **orden de gates del contador de rechazos** es un análisis paralelo, no el número de entradas que hubiera generado realmente la estrategia sin esos filtros. El observador evalúa indicadores en más barras que V5; verificar paridad de resultados es obligatorio.

## Instalación NT8 (sin Python ni descargar ticks)

1. Conserva los archivos ya instalados `NQNativeGeneticLabV5.cs`, `NQNativeExitCanonicalV5.cs`, `NQNativeATRExitMathV5.cs`, y módulos G0 V6/V7 tal como están. **No reemplazar V5 ni G0V7**.
2. Descargar el código [Raw de NQNativeGeneticLabV8Audit.cs](https://raw.githubusercontent.com/rgentil2/MES-Trading-Research/main/research/nq/ninjatrader/NQNativeGeneticLabV8Audit.cs) en `Documentos\NinjaTrader 8\bin\Custom\Strategies\NQNativeGeneticLabV8Audit.cs`. No copiar código de test ni de CI a NinjaTrader.
3. Abrir NinjaTrader `New → NinjaScript Editor` y presionar **F5**. Si aparecen errores, conservar screenshot de primera línea con archivo/columna; los tests .NET de GitHub no sustituyen esta prueba nativa.
4. `New → Strategy Analyzer`, `Backtest type=Optimization`. **Strategy = `NQNativeGeneticLabV8Audit`**, `Optimizer = NQNativeUniqueOptimizerV5`, `Optimize on = NQNativeG0RiskFitnessV7`. El optimizador V5 usa `Strategies[0] is NQNativeGeneticLabV5` y el fitness G0V7 hace un `as NQNativeGeneticLabV5`, así que la clase auditora V8 hereda los 20 genes/canonical de V5. Confirmar que ambos aceptan la estrategia V8 en la versión local. No tocar el código del optimizador.
5. **Copiar exactamente los rangos/genes de la prueba V5/G0V7**: `UniqueCandidates=20`, `Seed=20261102`, `MaxAttempts=2000`, periodos y combinadores originales. `NQ DEC26` con historial continuo verificado, `Last`, M1, `CME US Index Futures RTH`, `2020-01-01` a `2022-12-31`, `Break at EOD`, comisiones activadas (misma plantilla), `Slippage=2`, fill Standard. Evitar 2023–2026.
6. Guarda copia nueva `NQ_V8_AUDIT_FREQ_EQUITY_20_2020_2022` sin sobrescribir V5/V6/V7. Ejecutar **20**, no más por ahora.
7. `New → NinjaScript Output → Output 1`. Busca `NQ_V5 BEGIN`, `NQ_V5 PRE_RUN`, `NQ_V5 END`, `NQ_V8_BEGIN`, `NQ_V8_FREQ`, `NQ_V8_MONTH`, `NQ_V8_RISK`, `NQ_V8_END`, `NQ_G0_V7`. Envía texto del output y captura Summary de los 20 resultados.

## Resultado exigido para certificar V8

- **Paridad estricta** de 20 fingerprints, neto, PF, DD cerrado, 20 cantidades de operaciones con el V5/G0V7 anterior. Si cambia, **V8 NO está validado**; investigar interferencia de evaluaciones adicionales de indicadores o registro al terminar.
- `NQ_V5 END executed=20 generatedUnique=20 failure=0` o diagnóstico claro de por qué no se reproduce.
- `NQ_V8_FREQ` en cada año; `NQ_V8_MONTH` para 12 meses de 2022; `NQ_V8_RISK` con DD bar-close finito y sin invalid.
- Reconciliar `predictedSubmissions` vs `actualCompletedTrades`, permitiendo diferencias legítimas por órdenes rechazadas/sin fill o cierre fuera del rango, pero no ignorarlas. Donde difieran, **no concluir** razones de pérdida de frecuencia como comprobadas.
- Aun con paridad, `maxDailyBarCloseDD` **no sustituye** el control de pérdida intraminuto, ni trailing DD/excursiones de MFFU.

## Documentación de API

NinjaTrader especifica `Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0])` para analizar PnL no realizado de una estrategia usando precio de backtest: https://static.ninjatrader.com/support/helpGuides/nt8/position_getunrealizedprofitloss.htm

**Estado de código:** CI .NET contra simulador NT8 permite comprobar sintaxis/comportamientos *del observador* y su no envío de órdenes; la verdadera compilación y paridad de V8 en NinjaTrader Windows están pendientes.
