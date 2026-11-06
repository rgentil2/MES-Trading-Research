# NQ S0.82 — V21: Memoización de fórmulas + evaluación económica auditable y reanudable
Fecha: **2026-11-06** | Estado: **GitHub Actions 3/3 SUCCESS**, investigación C# con OHLCV M1 sintético.

## Decisión vinculante del usuario
- Plataforma final: **NQ DEC2026** (el usuario ya ve M1 2020–2022 directamente en NinjaTrader 8).
- Completar el generador, robustez y portafolios en C# primero; **una sola integración y validación final NT8**.
- No gastar el camino crítico en auditar contratos/rollovers, exportaciones nuevas, F5, ni backtests intermedios solicitados al usuario.

## Qué queda implementado con código

1. **`NQNativeFeatureMemoV21.cs`**: cache LRU de **valores numéricos por familia/periodo**, reutilizados por las **11 reglas direccionales** de cada fórmula. Tiene presupuesto acotado en bytes, expulsión de tablas LRU, contadores de hits/construcciones/expulsiones. Los tipos heredados **0..395** delegan íntegros en la caché V14; los nuevos **396..1319** se resuelven con la **misma función compartida V19 `ResolveRule`** y nunca con fórmulas aproximadas. Se conserva la compresión RTH original y se calcula el ATR sobre el source original para mantener equivalencia de costos/stops. Se preservan las fórmulas de 120 familias, sin añadir indicadores nominales.

2. **`NQNativeSignalCacheV14.cs`**, nueva sobrecarga `EvaluateExpandedWithSignalProvider`: evaluación conservadora V12 con su cronología original y el proveedor de señales indexado a la fuente sin reescribir cálculos de fills, comisiones, slip ni flatten. Las llamadas antiguas mantienen su comportamiento.

3. **`NQNativeEconomicLedgerV21.cs`**: diario durable **una fila por genoma único**, con identificador canónico EXCANv19, sus 20 genes, score V9, P&L neto de la simulación, recuento de operaciones, PF, DD cerrado y contadores de stops, targets, flat por tiempo y ambigüedad SL/TP. Identificador SHA256 de la fuente y versión/configuración/seed de GA, más SHA256 por registro; las filas corruptas, duplicadas, con otros genes o diferente origen/parámetros **se rechazan**. La cantidad de generaciones puede ampliarse conservando la semilla; el GA reproduce determinísticamente el orden, usando scores guardados, **sin recalcular backtests**.

4. **`NQNativeBulkEconomicV21.cs`**: motor de evaluación económica GA de los **1.320 tipos**, ahora con memoización opcional y diario de resultados completo. Emite ranking TSV reproducible y **recibos detallados de cada entrada/salida** para los mejores N (máximo 1.000) con fechas ET, direcciones, precios, contratos, comisiones, P&L, MAE y MFE; verifica que estos finalistas coincidan con el ledger. El resto de candidatos conserva estadísticas compactas para evitar un archivo gigante de operaciones. Fallas fatales de escritura/datos se propagan tras el GA en lugar de disfrazarlas de score de mala calidad.

5. **`NQNativeResearchRunnerV21.cs`**: integra realmente el GA económico reanudable V21 → auditoría G0 y costos 1,5×/bootstrap V13 → selección de 3–5 estrategias y riesgo cronológico de cuenta V15 → `NQNativeWalkForwardV20` 2020–2022 → campaña congelada de V16 con EXCANv19, validación externa 2023–2024 y final 2025–oct2026 estrictamente sellados. El flujo rechaza la falta de candidatos; no inventa estrategias rentables. Su test ejecuta el entrenamiento/filtros y también ejercita el walk-forward por separado porque el portafolio sintético fue rechazado.

## Evidencias exactas de CI

**[GitHub Actions workflow 42277531275](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42277531275) — 3/3 jobs SUCCESS** (también [42276835664](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42276835664), 2/2 PASS antes de añadir el test del embudo).

- `NQ_V21_FEATURE_MEMO_PASS comparisons=33264 familyPeriodTables=254 featureHits=34474 evictions=251 peakPayloadBytes=33984 originalSignalMisses=2796 economicTradeParity=TRUE`. Diferencial completo con la caché anterior, 84 familias nuevas, 11 reglas, periodos 6/12/24, 12 sesiones sintéticas, con límite intencional de **tres tablas de valores numéricos** para demostrar expulsión y recomputación correctas. `peakPayloadBytes` es el valor impreso de bytes usados tras el test, **no** una medición del pico completo de memoria del proceso; el presupuesto de tablas está acotado.

- `NQ_V21_BULK_ECONOMIC_PASS uniqueCompleteV12Backtests=82 directParity=82 resumeFresh=0 resumeReused=82 extensionFresh=26 extensionReused=82 allCandidatesWithNetPFDD=108 finalistsWithDetailedFills=5 memoFirstMs=257 v14FirstMs=771 memoFeatureBuilds=85 sourceAndConfigGuard=TRUE corruptionGuard=TRUE`. Son **82 ejecuciones auténticas del simulador V12 M1 y cálculo económico V9 sobre 14 sesiones OHLCV sintéticas**, comparadas candidato por candidato, **no** una función oráculo artificial de puntuación. Segundo run: 0 nuevas; extensión 4ª generación: +26 nuevos =108 y posterior replay 0 nuevos. Cinco finalistas tienen recibo detallado de operaciones. Una sola comparación temporizada en CI: **257 vs 771 ms**, factor ~3, **no estimación general de 100k backtests reales ni extrapolación de velocidad**.

- `NQ_V21_FULL_FUNNEL_PASS geneticUnique=22 robustAudited=10 robustPass=5 result=PORTFOLIO_RISK_OR_DIVERSITY_REJECT folds=4 foldedGenomes=88 version=EXCANv19 noFutureLeakage=TRUE`. Sobre serie sintética **2020–2022** de 36 meses, el nuevo ledger se alimentó del evaluador económico; en una repetición no hubo nuevos backtests del GA, se ejecutaron 10 auditorías G0 y 5 candidatos pasaron individualmente pero **el portafolio fue rechazado**. Las cuatro ventanas train12/validate6 (88 genomas de entrenamiento) se probaron como componente separado, sin fugas de datos futuros. Datos de 2023+ explícitamente rechazados por el runner de desarrollo.

## Qué falta; NO hacer afirmaciones falsas
- **NO** se han procesado 100.000+ backtests con el M1 real 2020–2022 de NQ DEC2026. Hasta aquí la evidencia económica nueva es de 82 completos sobre **14 días sintéticos** y de 22 genomas en un fixture sintético de 36 meses. Las pruebas históricas anteriores de 109.464 candidatos usan **fitness sintético**, no fills económicos.
- El benchmark 257 ms vs 771 ms se limita a ese mismo test y hardware CI. Costos de 36 meses reales y 100k candidatos **requieren perfilado / escalado adicional**. El máximo de memoria cubre payload de tablas, no toda la memoria del proceso.
- El motor M1 V12 sigue siendo una **aproximación conservadora** con SL primero cuando SL/TP se cruzan en la misma vela, y parámetros de costos supuestos. No reproduce aún llenados propietarios de Strategy Analyzer ni orden intraminuto desconocido.
- No hay PF/DD ni ventaja de mercado real validada; no hay portafolio aprobado para fondeo MFFU, ni NinjaTrader nativo compilado. Los 120 cálculos de fórmulas no implican 120 indicadores estadísticamente independientes.

## Siguiente bloque recomendado
**V22**: completar perfilado del simulador económico en escenarios M1 2020–2022 de longitud equivalente (no solo 14 días), observar throughput/costes de 10k/100k evaluaciones reales sin usar datos externos/holdouts en búsqueda; optimizar donde el profiler lo demuestre; enriquecer ranking/archivo de rechazos y portafolios congelados; prepararse para un paquete único final de validación NinjaTrader una vez terminado el sistema. No se necesita ninguna intervención en NT8 ahora.
