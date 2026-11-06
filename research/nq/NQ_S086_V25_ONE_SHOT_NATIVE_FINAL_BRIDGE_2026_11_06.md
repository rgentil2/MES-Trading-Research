# NQ S0.86 — V25: Puente y campaña FINAL única de validación nativa en NinjaTrader 8

**Fecha:** 2026-11-06. **Estado real:** puente de código e infraestructura offline V25 **IMPLEMENTADOS Y CI VERDE**; **campaña real final en NinjaTrader 8 PENDIENTE**. No confundir ambas cosas.

## Objetivo fijo de V25 (no renumerar)

**V25 = Integración y validación FINAL en NinjaTrader 8 con NQ DEC2026, una única campaña supervisada.** V23 = generador completo, informes finales, consolidación; V24 = escalamiento a 100.700 backtests económicos M1 de 36 meses SINTÉTICOS. [Contrato obligatorio](NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md).

Las 120 fórmulas/1.320 condiciones y los 20 genes EXCANv19 **no se optimizan dentro de V25**. La única función de V25 es verificar con NT8 real **el mismo portafolio previamente aprobado**, sus barras, señales, órdenes y operaciones, P&L, costes, DD, riesgo diario y conjunto. Sin negociar reglas para que «pase» una estrategia. El usuario no quiere auditorías adicionales de contratos/rollovers ni pruebas intermedias de NinjaTrader.

## Implementación realizada

1. **`NQNativeV25FrozenImporter.cs`** carga SOLO un expediente real V23 que haya pasado el portafolio de 3–5 estrategias, verificando `campaign.lock`, `artifacts.sha256`, `run_summary.txt`, `portfolio_decision.tsv`, la configuración y los genes de `definitive_parameters.tsv`. Los informes actuales conocidos de V23 quedan **rechazados** (`PORTFOLIO_RISK_OR_DIVERSITY_REJECT`). No se crean ganadores ficticios. El `handoff.tsv` fija IDs, 20 genes, hash del paquete y checksum de sus filas. `NQNativeV25FrozenSignalCore.cs` recalcula señales V19 con timestamp comienzo de minuto ET, stops y TP del V12.
2. **`research/nq/ninjatrader/nt8/NQ_V25_FrozenAnalyzer.cs`** prepara el **único adaptador nativo** para la validación final. Desarmado por defecto; solo acepta `IsInStrategyAnalyzer`, estado histórico, barras LAST de 1 minuto, instrumento NQ DEC2026, identidad V19 y archivo `--prepare` original. Verifica SHA de toda la entrega y de las etapas previas antes de colocar órdenes históricas; exporta barras ET 08:00–11:29, entradas, salidas, precios, resultados nativos. Activa `IncludeTradeHistoryInBacktest` y `IncludeCommission`. Su uso fuera de Strategy Analyzer o en datos reales de cuenta viva está bloqueado.
3. **`NQNativeV25NativeBarsReader.cs`** obliga a igualar **cada M1 timestamp, OHLC y volumen** con la fuente de investigación, 120 minutos RTH exactos y cobertura mensual; evita atribuir a la estrategia divergencias debidas a otra serie.
4. **`NQNativeV25ParityAudit.cs`** compara operación a operación el V12 conservador con la ejecución histórica nativa, incluyendo conteo, dirección, contratos, horarios, precios en ticks, P&L bajo costes V12 ($4,68 RT por contrato), DD cerrado y tolerancias. Diferencias → RECHAZO/reportes, sin recalibrar sobre holdouts. Los métodos `SetStopLoss/SetProfitTarget` nativos **no replican mágicamente** el algoritmo V12 stop-first en barras M1 ambiguas; justamente se cuantifica esa diferencia.
5. **`NQNativeV25OneShotValidation.cs` + `NQNativeV25StageAuthorization.cs`** establecen una sola **campaña** con tres puertas de **evaluación histórica**, no tres optimizaciones: DEV 2020–22; solo si su prueba NT8 pasa, EXTERNAL 2023–24; solo si pasa, FINAL 2025–octubre 2026 (corte exclusivo 2026-11-01). Token SHA de reporte/snapshot y freeze impide avance accidental; el script nativo también comprueba los tokens antes de cualquier orden histórico en los periodos futuros. Se reaudita por estrategia PF≥1,25, frecuencia por mes, neto, DD y riesgo flotante combinado $2k / pérdida intradía $1k, con los parámetros originales.
6. **`tools/nq-v25-native/NQNativeV25OneShot.csproj` + `NQNativeV25Console.cs`** enlazan el árbol consolidado V23/V24 y exponen `--prepare`, `--audit-dev`, `--audit-external`, `--audit-final`, `--version`. Cada etapa documenta aprobaciones/rechazos y no reescribe reportes ya consumidos. [Manual de operación final](../../tools/nq-v25-native/README.md).

## Evidencia automatizada concreta (solo pruebas de C# y datos fabricados)

**[Workflow GitHub Actions 42307994460 — SUCCESS 3/3](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42307994460)**:

- **Código puro + consola:** `dotnet build` V23+V24+V25 exitoso, sin NinjaTrader instalado.
- **Paridad de señales:** `NQ_V25_SIGNAL_PARITY_PASS families=120 checked=630000 emitted=176173 EOD_M1_to_ET_start=TRUE`. Compara 120 familias con matemáticas V19 sin adelantar barras.
- **Paridad y rechazo de fills:** `NQ_V25_NATIVE_FILL_COMPARISON_PASS exactAccepted=2 changedPriceRejected=TRUE missingTradeRejected=TRUE`. Son recibos **fabricados para probar el comparador**, NO ejecuciones NT8 reales.
- **Integridad de freeze y barras:** `NQ_V25_FROZEN_HANDOFF_PASS approvedFixture3And5=TRUE rejectedDevFailClosed=TRUE alteredGeneSHARejected=TRUE strictNativeBars=164430 sourceBarMismatchRejected=TRUE noOosReadAfterDevReject=TRUE nativeReceiptLockBinding=TRUE stageShaAuthorizations=TRUE tamperChainGuard=TRUE`. Los expedientes «aprobados» son *fixtures construidas*, no salidas de rentabilidad.
- **Compilación con API simulada, NO DLL NT8:** `NQ_V25_NT8_API_STUB_PASS syntaxCompiledWithSurrogate=TRUE defaultDisabled=TRUE noLiveChartActivation=TRUE finalWithoutExternalDenied=TRUE changedGeneHandoffRejected=TRUE modifiedHandoffSHARejected=TRUE note=NOT_A_REAL_NINJATRADER_DLL_COMPILATION`. El stub reproduce únicamente la parte del API necesaria para detectar errores comunes de C# y verificar protecciones; **no puede certificar la compatibilidad real de NinjaScript con NinjaTrader instalado**.

## Qué falta para poder declarar V25 TERMINADA

- Un portafolio real de **3–5 estrategias congeladas** por V23, después de superar desarrollo 2020–2022, G0, correlación, Monte Carlo, WF y riesgo conjunto. **Hoy NO existe** en los resultados reales disponibles; el último fixture de GA V23 se rechazó. La capacidad V24 de 100.700 backtests sintéticos no constituye portafolio de mercado ni permite saltearse esa puerta.
- Compilar de verdad el adaptador en **NinjaTrader 8 del usuario**, con solo los módulos matemáticos puros indicados en el README, **una sola vez cuando corresponda**. Los 42 módulos de V23/V24 son investigación .NET externa; no deben meterse indiscriminadamente en NinjaScript.
- Ejecutar la **campaña histórica final supervisada** en `NQ DEC2026`: mismos M1 de la investigación, comparar barras, entradas, stops/targets, fees, 3–5 estrategias y DD de cuenta, sin volver a entrenar con 2023–26. No es correcto afirmar que haya aprobado ni que sean compatibles los fills hasta que se ejecute.
- Si falta un portafolio aprobado, V25 se mantiene bloqueada. El software está preparado para informar el rechazo sin introducir «estrategias ganadoras» artificiales. Tampoco se declara cuenta fondeada aprobada ni se habilita trading automático real.

## Decisión de estado

**V25: integración de código preparada / offline QA aprobada / VALIDACIÓN NATIVA Y RENTABILIDAD REAL NO PROBADAS.** Conservar su objetivo fijo y el PR en revisión hasta la campaña de NinjaTrader. Nada de promesas de resultados en segundo plano ni pruebas nativas intermedias.
