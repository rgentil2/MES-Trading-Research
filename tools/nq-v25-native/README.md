# V25 — Integración y validación FINAL con NinjaTrader 8 (objetivo fijo)

**Versión:** S0.86 V25. **No renumerar ni cambiar el alcance.** V23 es el generador único, informes y portafolios; V24 son los **100.700 backtests económicos de 36 meses SINTÉTICOS**; **V25 es SOLO el puente y la ÚNICA campaña de validación final en NinjaTrader 8 con `NQ DEC2026`**. [Contrato de versiones](../../research/nq/NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md).

## Estado REAL, 6 de noviembre de 2026

- **Código del puente y su evaluador offline de diferencias:** implementados en esta rama de trabajo. QA de GitHub verifica fórmulas, ET, precios, retornos, SHA y bloqueos de OOS sobre **fuentes sintéticas y fixtures**.
- **NO se ha ejecutado NinjaTrader 8 real** desde GitHub. El archivo `nt8/NQ_V25_FrozenAnalyzer.cs` se compila solamente contra un pequeño **sustituto de API en CI**, **NO contra la DLL real de NinjaTrader 8**. La compilación y la paridad auténticas quedan reservadas para la fase final supervisada.
- **NO existe aún portafolio de 3–5 estrategias descubierto, aprobado y congelado con datos reales** en el proyecto. Los runs de V23 conocidos terminaron con `PORTFOLIO_RISK_OR_DIVERSITY_REJECT`. **V25 falla cerrada**: `--prepare` rechaza un expediente sin aprobación real. No inventar estrategias, no reemplazar genes ni abrir 2023–2026 para optimización.
- **No solicitar acciones de NinjaTrader ahora.** El usuario eligió terminar el código, preparar la integración y efectuar **una única validación final** cuando haya portafolio aprobado y datos disponibles.

## Dos aplicaciones diferentes, sin duplicar la generación

1. **Herramienta offline de una sola campaña final:** `tools/nq-v25-native/NQNativeV25OneShot.csproj` (referencia el generador V23/V24 ya consolidado), con acceso a los informes de V23, validación SHA de 3–5 identidades EXCANv19, 20 genes, datos M1, reporte de discrepancias y puertas temporales.
2. **Strategy Analyzer NT8 — solo histórico:** `research/nq/ninjatrader/nt8/NQ_V25_FrozenAnalyzer.cs`. Es el adaptador nativo para ejecutar exactamente una estrategia congelada, con la matemática de señales V19 y exits V12, completar entradas/SL/TP en el propio simulador NT8, guardar precios y fechas de sus ejecuciones y una exportación de sus barras M1. No genera ni optimiza nuevas estrategias, **no se habilita en charts/lives**, y está **desarmado por defecto**.

### Archivos matemáticos C# puros que deben acompañar la estrategia en NinjaTrader

Los archivos fuente que necesitará el editor NinjaScript **para la validación final**, y solo entonces:

```text
research/nq/ninjatrader/NQNativeConditionsV11.cs
research/nq/ninjatrader/NQNativeConditionCatalogV18.cs
research/nq/ninjatrader/NQFeatureMathV19.cs
research/nq/ninjatrader/NQTrendFeaturesV19.cs
research/nq/ninjatrader/NQMomentumFeaturesV19.cs
research/nq/ninjatrader/NQVolatilityFeaturesV19.cs
research/nq/ninjatrader/NQVolumeActionFeaturesV19.cs
research/nq/ninjatrader/NQNativeConditionCatalogV19.cs
research/nq/ninjatrader/NQNativeBooleanCanonicalV11.cs
research/nq/ninjatrader/NQNativeExitCanonicalV11.cs
research/nq/ninjatrader/NQNativeExitCanonicalV19.cs
research/nq/ninjatrader/NQNativeATRExitMathV5.cs
research/nq/ninjatrader/NQNativeV25FrozenSignalCore.cs
research/nq/ninjatrader/nt8/NQ_V25_FrozenAnalyzer.cs
```

**No importa los otros 42 módulos de investigación .NET8 en NinjaScript**: V23/V24 trabajan fuera de NinjaTrader y pueden utilizar APIs .NET que difieren de la versión interna de NT8. Solo el adaptador y sus dependencias mínimas se probarán con DLL nativas durante la **única validación final**.

## Condiciones de seguridad operativa

- Instrumento de destino: **NQ DEC2026**, LAST, **1 minuto**. El usuario confirmó que visualiza datos M1 de 2020–2022 en su NinjaTrader, pero eso **no demuestra por sí solo** paridad de barras, costes o fills.
- Solo **Strategy Analyzer / Backtest histórico**, nunca panel Strategies, Chart Trader, cuenta simulada en tiempo real ni cuenta real. `ArmHistoricalValidation=false` por defecto, y el código exige `IsInStrategyAnalyzer`, `State.Historical`, `ConfirmEndStampedET`, identidad/handoff congelados y prueba SHA de la etapa anterior cuando corresponde.
- El reloj del script asume zona horaria **New York / Eastern** y barras de NinjaTrader con sello al **final** del minuto; convierte a timestamp del **inicio** restando 1 minuto. Solo analiza y exporta de 08:00 a 11:29 ET. Los datos iniciales V23 deben ser las **mismas barras completadas** (no otro proveedor, feed, plantilla de sesiones o trading-hours). La herramienta compara **cada OHLCV y timestamp** antes de valorar resultados.
- Usar `Use Local Data Only` al preparar el Strategy Analyzer si corresponde para evitar descargar automáticamente barras de otro proveedor. Es una preferencia documentada por NinjaTrader, no un requisito de revisar contratos/rollovers.
- `IncludeTradeHistoryInBacktest=true` (en `State.Configure`) para que `SystemPerformance.AllTrades` tenga registros históricos; `IncludeCommission=true` y `Slippage=2`. El reporte nativo **recalcula por separado el P&L bajo el supuesto V12 de USD 4,68 por ida y vuelta**, de modo que no confunde comisiones reales de broker con las asumidas.
- Las órdenes `SetStopLoss`, `SetProfitTarget` y `EnterLong/EnterShort` **solo simulan órdenes históricas en el Strategy Analyzer**, con 1 contrato. Sus precios pueden **diferir** de V12 (stop primero si SL y TP se cruzan dentro de la misma vela, salto adverso y dos ticks de slippage). Las diferencias se **reportan y pueden causar rechazo**, no se ocultan ni se ajustan parámetros usando holdout.
- Riesgo de investigación: **$2.000 de DD conjunto**, menos de **$1.000** de pérdida intradiaria y riesgo simultáneo, ≥150 trades/36mo, ≥5/mes, neto positivo, PF≥1,25 y 3–5 estrategias diversificadas. El cálculo M1 de posiciones flotantes es una aproximación, no certificación de las reglas MFFU ni autorización de operar.

## Campaña final única y escalonada (solo cuando exista freeze real V23)

No se inicia ni se recomienda esta campaña hasta disponer de un expediente V23 **realmente aprobado y congelado**. Debe usarse la misma carpeta de campaña y la **misma SHA del freeze** en las tres particiones.

**Preparación y bloqueo** — después de la investigación real 2020–22:

```powershell
dotnet build tools/nq-v25-native/NQNativeV25OneShot.csproj -c Release

dotnet run --project tools/nq-v25-native/NQNativeV25OneShot.csproj -- --prepare "V23_APROBADO" "V25_HANToff.tsv"
```

`--prepare` verifica `artifacts.sha256`, `campaign.lock`, `run_summary.txt`, `portfolio_decision.tsv`, `settings_snapshot.tsv` y los **20 genes canónicos por estrategia**. Si V23 no aprobó **3–5 sistemas**, se detiene. La salida `V25_HANToff.tsv` fija `V25LockSHA256`, identificación de 3–5 candidatos, sus genes y el SHA de sus informes.

**Etapa 1 — desarrollo DEV 2020–2022:** configurar el Strategy Analyzer con solo el periodo DEV y la misma fuente M1. Para cada candidato, colocar `CandidateId`, `FrozenHandoffFile` (ruta absoluta), `FrozenV25LockSHA256`, `FrozenCanonicalBase64`, `FrozenGenes20` exactamente del handoff, `HistoricalScope=DEV`, `ArmHistoricalValidation=true` solo bajo Strategy Analyzer y `ConfirmEndStampedET=true`. Exportar `V25_<candidate>_DEV_bars.tsv` y `V25_<candidate>_DEV_native_trades.tsv` en la misma carpeta de reportes. Ejecutar **una vez**:

```powershell
dotnet run --project tools/nq-v25-native/NQNativeV25OneShot.csproj -- --audit-dev "V23_APROBADO" "M1_DEV_ORIGINAL_UTC.txt" "V25_NT8_REPORTS" "V25_CAMPANA"
```

Si falla cualquier comparación de barras/trade/costos/riesgo → `V25_DEV_audit.tsv` con rechazo; **ni EXTERNAL ni FINAL autorizados**. Si pasa, crea `V25_DEV_PASSED.sha256` encadenado al freeze.

**Etapa 2 — EXTERNAL 2023–2024:** únicamente después de DEV aprobado. Para cada candidato, `HistoricalScope=EXTERNAL`, `StageGateDirectory=V25_CAMPANA`, `PreviousGateSHA256=hash completo de V25_DEV_PASSED.sha256`; misma fuente/instrumento y genes, y solo el periodo histórico autorizado. El propio NinjaScript se niega a trabajar si el SHA/report anterior cambió. Después:

```powershell
dotnet run --project tools/nq-v25-native/NQNativeV25OneShot.csproj -- --audit-external "V23_APROBADO" "V25_NT8_REPORTS" "V25_CAMPANA"
```

Si pasa, crea `V25_EXTERNAL_PASSED.sha256`. Si no, FINAL continúa cerrado. **No se permite reentrenar ni repetir EXTERNAL para ajustar parámetros**.

**Etapa 3 — FINAL 2025–octubre 2026:** solo con DEV y EXTERNAL aprobados. Configurar `HistoricalScope=FINAL`, `PreviousGateSHA256=hash de V25_EXTERNAL_PASSED.sha256` y `StageGateDirectory` idéntico, final exclusivo **2026-11-01**. Solo entonces se pueden emitir las barras/fills de la última partición. Comparación final:

```powershell
dotnet run --project tools/nq-v25-native/NQNativeV25OneShot.csproj -- --audit-final "V23_APROBADO" "V25_NT8_REPORTS" "V25_CAMPANA"
```

El expediente V25 contiene por candidato señal/canon, fills de NT8, comparación barra por barra, diferencias en timestamps/ticks/net, PF y DD cerrados, cronología M1 de riesgo conjunto y permisos SHA de cada etapa. **Un rechazo es un resultado válido.** El resultado favorable es *provisional* hasta revisión humana del comportamiento en NT8, no certificación de fondeo.

## Lo que prueban las pruebas automatizadas (NO el mercado)

Las suites en CI abarcan, con datos fabricados: paridad de **120 familias** y 630.000 observaciones de señal V19, hora M1 end→start, aceptación y rechazo de recibos de ejecución, importar 3/5 genomas sintéticos completos, rechazar expedientes sin portafolio congelado, 164.430 barras sintéticas con coincidencia total, bloqueo de 2023+ si DEV falla, y tokens SHA de aprobación encadenados con detección de modificaciones.

El archivo NinjaScript se compila contra un **stub de API NinjaTrader mínimo** para detectar errores sintácticos ordinarios y verificar su desarme/guardas; **NO se ha compilado contra NinjaTrader 8 real ni ejecutado Strategy Analyzer**. Su API real/compatibilidad y cualquier diferencia de comportamiento se resolverán **solo durante la única validación final de V25**. No prometer que terminará con un portafolio rentable.

**Fuente oficial NT8**: [Backtest en Strategy Analyzer](https://ninjatrader.com/support/helpGuides/nt8/backtest_a_strategy.htm), [IncludeTradeHistoryInBacktest](https://static.ninjatrader.com/support/helpGuides/nt8/includetradehistoryinbacktest.htm), [Managed Approach](https://static.ninjatrader.com/support/helpGuides/nt8/managed_approach.htm) y [IsInStrategyAnalyzer](https://static.ninjatrader.com/support/helpGuides/nt8/isinstrategyanalyer.htm).
