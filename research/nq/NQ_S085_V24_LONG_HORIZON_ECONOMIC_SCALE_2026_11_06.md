# NQ S0.85 — V24: Escalamiento económico de largo horizonte M1

**Fecha:** 2026-11-06.  
**OBJETIVO FIJO DE V24:** rendimiento, memoria y escalamiento de **backtests económicos completos** durante los 36 meses de desarrollo 2020–2022, avanzando de pruebas controladas hacia ≥100.000 candidatos; sin redefinir el entregable V23 (generador/reports) ni adelantarse a V25 (única validación nativa NT8). Contrato: [NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md](NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md).

## Componentes V24 ya implementados

- `NQNativePreparedEconomicV24.cs`: precalcula/prefetch **una sola vez por genoma** hasta cuatro tablas de valores de familias nuevas V19, manteniendo como **cache antiguo V14** las señales heredadas; evalúa con **idéntico simulador V12** de stop primero en vela ambigua, costos, slippage, intrabar proxy, ATR original, score V9 y señal EXCANv19. No cambia los genes ni fórmulas ni reglas G0.
- `NQNativeFeatureMemoV21.cs` expone internamente acceso de solo lectura por contrato a sus tablas numéricas y fuente ordinal, para evitar buscar en LRU durante cada barra. No muta la versión numérica ni el comportamiento legacy V21. Las tablas pueden permanecer referenciadas por un candidato aunque su ID LRU haya sido expulsado; **limite de bytes acota el payload residente en el diccionario, NO memoria total del proceso ni los hasta cuatro arrays pineados**.
- `NQNativeEconomicScaleV24.cs`: función pública para ejecutar una búsqueda GA real, un candidato = simulación económica completa **V12 de todas las barras M1** (no fitness sintético), con scores y net/PF/DD en diario SHA V21, reanudación sin backtest repetido, métricas de velocidad **backtests nuevos/seg**, millones de RTH barras recorridas/seg, tablas cacheadas/evictadas y memoria aproximada del proceso. Los genomas se canonizan en EXCANv19 1.320 condiciones.
- `NQNativeSynthetic36V24.cs`: fixture determinística OHLCV de **todos los días lunes–viernes 2020–2022, 08:00–11:29 ET**. Son 36 meses, **783 sesiones sintéticas y 164.430 barras M1**, de las cuales **93.960** forman el bucle reducido 09:30–11:29 y **92.394** son barras 09:30–11:27 de señal. Los datos son fabricados; no pretenden reproducir precios, calendario real de festivos, rollover ni condiciones de mercado de NQ.
- `tools/nq-v24-scale/NQResearchV24.csproj` (mismo árbol explícito C# de V11–V23 + V24) y `NQNativeV24Console.cs` tienen `--bench-synthetic36` y `--run-development` (este último queda para cuando sea apropiado alimentar los datos reales de desarrollo). Permite asignar topología genética y presupuestos de caché, genera diario económico + ranking + perfil de velocidad/memoria sin modificar reportes de V23.
- Workflows CI: `.github/workflows/nq-v24-economic-scale-qa.yml` valida regresión V21 y paridad económica de 36 meses; `.github/workflows/nq-v24-economic-throughput-1k-qa.yml` encadena 1.120 y 10.500; `.github/workflows/nq-v24-100k-full-economic-qa.yml` intenta 100.700 backtests económicos completos (límite 180 minutos). Todos usan solo **36 meses sintéticos**, con reanudación y artefactos versionados; no autorizan trading.

## Evidencia V24 de paridad y primer rendimiento medido (COMPLETADO)

**[Github Actions workflow 42292796604 — 2/2 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42292796604)**, luego nuevamente [42293052955](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42293052955) al modificar opciones CLI.

Log:
`NQ_V24_LONG_HORIZON_ECON_PASS syntheticFullMonths=36 sessions=783 sourceBars=164430 workingBars=93960 exactV12ParityGenomes=5 exactV12ParityTrades=5275 firstNewBacktests=45 extensionNewBacktests=21 totalFullEconomicBacktests=66 restartNewBacktests=0 firstMs=5430 fullBacktestsPerSecond=8.2860 barsPerSecMillions=0.7786 maxWorkingSetMiB=196.30 shaProtected=TRUE`.

Esto significa:
- **66 evaluaciones económicas COMPLETAS** (45 nuevas + 21 al extender la búsqueda) con el simulador conservador V12, 36 meses **sintéticos**.
- **Cinco genomas y 5.275 operaciones** con coincidencia exacta V21 vs V24: neto, score, tiempos, precio entrada/salida, fees, MAE/MFE, stops/targets y rechazos por reglas de simulador.
- 45 pruebas iniciales tardaron **5,430 segundos** en ese runner CI; tasa puntual **8,286 backtests nuevos/s**. No extrapolar linealmente a 100k: caché fría/caliente, mayor diversidad de combinaciones, memoria, disco y GC cambian la velocidad.
- Pico working-set de ese proceso CI: **196,30 MiB** y reanudación **0 nuevos**; el estimador de caché no equivale al total de memoria real.

## Escalamiento de capacidades en GitHub Actions

El segundo workflow ejecuta, siempre sobre la misma muestra **sintética 36 meses**, una generación real de **1.120 evaluaciones M1 económicas** y luego **10.500** (población 600, 19 generaciones, élites 50). Cada nivel vuelve a arrancar la campaña en el mismo directorio para confirmar que las filas del diario y los rankings se conservan idénticos y que la segunda ejecución hace **0 backtests nuevos**.

### 1.120 simulaciones económicas reales V12, 36 meses sintéticos — CONFIRMADO

**[Github Actions 42293251090, etapa `economic-one-thousand` SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42293251090)**:

- `NQ_V24_SCALE_ECONOMIC source=SYNTHETIC_36_MONTH_WEEKDAYS fullBacktests=1120 journalReused=0 workingBars=93960 seconds=56.065 backtestsPerSecond=19.9766 featurePayloadMiB=337.65 maxWorkingSetMiB=520.00`.
- Misma fuente M1 2020–22 sintética (164.430 barras/783 sesiones). **1.120 backtests V12 económicos completos**; filas fuente/genoma/score P&L PF DD persistidas = **1.121 líneas** incluido el encabezado.
- Segundo run: `fullBacktests=0 journalReused=1120 workingBars=93960 seconds=0.104`, archivo de ranking byte idéntico y diario sin filas añadidas; no se volvieron a simular las entradas/salidas.
- Un único benchmark de runner CI: **19,98 backtests nuevos por segundo**, 56,065 s; **520 MiB** pico aproximado de memoria del proceso y 337,65 MiB de payload numérico residente. No es tasa garantizada, ni prueba NQ real, ni certificación de 100k.

### 10.500 y 100.700 simulaciones — NO declarar éxito sin evidencia final

- **10.500 BACKTESTS ECONÓMICOS V12 COMPLETOS CONFIRMADOS**: `economic-ten-thousand` en [workflow 42293251090](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42293251090), **SUCCESS 2/2 jobs**. `fullBacktests=10500 journalReused=0 workingBars=93960 seconds=215.975 backtestsPerSecond=48.6167 featurePayloadMiB=414.49 maxWorkingSetMiB=712.01`. Diario con **10.501 filas** (incluido encabezado) y resultado real V12 económico net/PF/DD por cada genoma. Replay `fullBacktests=0 journalReused=10500 seconds=0.440` y ranking byte idéntico. Fuente: 36 meses **sintéticos** 2020–22, NO NQ del mercado.
- `hundred-thousand-full-m1-economic` en [workflow 42293746661](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42293746661): **100.700** candidatos únicos esperados, todos deben pasar realmente por el simulador V12 de 36 meses; salida de diario de 100.701 filas y reinicio sin evaluaciones si se completa. Al redactar este informe, el run había **comenzado, sin resultado verificado**. Límite de CI: 180 minutos; exceder tiempo o memoria se debe registrar como insuficiencia de capacidad, no como éxito.

**10.500 verificados y aprobados. Los 100.700 permanecen NO VERIFICADOS en este informe hasta revisar la conclusión del workflow.** Nunca confundir puntuación con oráculo sintético con un backtest económico real. 100.000 backtests de 36 meses **sintéticos** tampoco validan rentabilidad del NQ real.

## Decisiones inmutables y limitaciones

- **V24 solamente escala backtests económicos** y no amplía fórmulas V19, modifica gates de V22 ni renombra fases.
- **V23 ya está fusionado a main** mediante el PR #82, SHA de merge `d1d7bd434e89f28e696e37c9a5eb00c2c97a5a29`. V24 es rama separada para CI de performance.
- **V25** seguirá siendo una única integración final a **NinjaTrader 8, NQ DEC2026**, cuando el software esté terminado. El usuario confirma datos M1 2020–22 visibles allí. No solicitarle exportaciones nuevas, compilar F5, auditar contratos/rollover ni correr pruebas nativas ahora.
- Las cifras CI no son P&L real; la cuenta objetivo MFFU 50K y DD $2k requieren prueba de riesgo/orden intraminuto FINAL. V12 es conservador estimado, no estrategia aprobada o fondeo certificado.

## Próximo criterio para llamar V24 completo

1. **CUMPLIDO EN CI SINTÉTICO:** ≥1.000 y ≥10.000 backtests completos de 36 meses con perfilado temporal/memoria, resultados económicos, persistencia SHA y 0 nuevas evaluaciones en replay. No equivale a NQ real.
2. Si la capacidad es compatible con los límites operativos y del runner, ampliar hacia **≥100.000** backtests completos 36 meses; no aceptar un número de genomas con scores oráculo como evidencia económica.
3. Documentar restricciones y requisitos de hardware / tiempo para el usuario y dejar el paquete de rendimiento integrado sin afectar la definición ni los outputs de V23.
