# NQ S0.84 — V23: Generador completo, resultados finales y consolidación reproducible

**Fecha:** 2026-11-06  
**Contrato de alcance fijo:** [NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md](NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md). La definición de V23 **no volverá a cambiar**: un ejecutor configurable que genere/guarde candidatos, aplique filtros, rankee, seleccione o rechace portafolios y exporte operaciones, P&L, DD, resultados anuales, motivos de descarte y 20 parámetros de cada estrategia congelada, consolidando las versiones anteriores en una compilación reproducible. **V24** = escala económica M1 de 36 meses/100k; **V25** = validación única NT8.

## Implementación terminada en código

- **Una ejecución** con `NQNativeCompleteGeneratorV23.Run`: fuente limitada a DEV 2020–2022 + configuración `NQGeneratorSettingsV23`; invoca directamente el **mismo** `NQNativeResearchRunnerV22` y este V21 GA/ledger → V13 G0/robustez → V15 riesgo/portafolio → V20 walk-forward → V22 auditoría integral → V16 freeze EXCANv19. No modifica fórmulas, reglas, fitness, fills o criterios, ni introduce una segunda búsqueda.
- **Hook de auditoría retrocompatible** (opcional) en el runner V22 permite capturar cada decisión individual G0: cantidad, PF, P&L, costos 1,5×, Monte Carlo bootstrap P95 DD, motivos individuales y todas las operaciones de candidatos auditados. El ranking se cruza por canónico V19 con **todos los genomas** del ledger V21; fuera del límite de auditoría se marca explícitamente `BEYOND_CANDIDATE_AUDIT_LIMIT`, no se inventan operaciones ni se califica artificialmente.
- **16 artefactos** archivados por ejecución: `economics_ledger.tsv`, `candidates_full.tsv`, `rejected_candidates.tsv`, `robustness_audits.tsv`, `annual_development.tsv`, `monthly_development.tsv`, `audited_trades.tsv`, `ranking_top.tsv`, `finalist_trades.tsv`, `portfolio_decision.tsv`, `walkforward.tsv`, `definitive_parameters.tsv`, `settings_snapshot.tsv`, `campaign.lock`, `run_summary.txt`, `artifacts.sha256`. Si no hay portafolio aprobado, el informe explica la causa y no publica estrategias definitivas falsas.
- **Congelación reproducible**: SHA256 de configuración completa, manifiesto del dataset + SHA adicional del contenido **real de cada barra OHLCV y timestamp**; lock previo a la búsqueda rechaza origen/configuración alterados. Diario económico V21 guarda resultados y hash por fila, el replay genético no reevalúa scores conocidos. Salidas ordenadas de forma determinista, con manifest de hash por archivo; no se guardan contadores de backtests «frescos vs reutilizados» en el paquete estable porque cambiarían su hash al reanudar (sí se notifican en memoria/CLI). `--verify` detecta alteraciones posteriores.
- **Consolidador autónomo .NET8**: `tools/nq-v23-research/NQResearchV23.csproj` **42 módulos C# listados explícitamente de V11–V23**, sin dependencia del runtime NinjaTrader ni paquetes externos. `NQNativeV23Console.cs` admite `--write-example`, `--run` y `--verify`, usando el adaptador V16 UTC-LAST M1 de solo DEV. [Manual](../../tools/nq-v23-research/README.md).
- **Contrato financiero de configuración**: no se pueden relajar por accidente los costos estresados 1,5×, DD bootstrap 2.000, 3 años positivos en DEV, DD cuenta 2.000, sesión y exposición adversa 1.000, correlación 0,45, concentración 40%, 3–5 componentes ni corte final 2026-11-01.

## Pruebas CI reales y exactas

**[Github Actions 42289323087 — SUCCESS 3/3 jobs](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42289323087)**:
1. **Compilación/CLI**: `dotnet build` del proyecto completo pasa sin NinjaTrader; `--version` y `--write-example` se ejecutan y producen configuración.
2. **Campaña y reportes auditables**: `NQ_V23_COMPLETE_GENERATOR_PASS version=V23_FIXED_SCOPE scored=22 audited=10 individualPass=5 portfolio=REJECTED allCandidateRankRows=22 monthlyMetricsRows=360 annualMetricsRows=30 artifacts=16 newBacktestsOnResume=0 outputByteExactReplay=TRUE changedConfigGuard=TRUE changedBarsGuard=TRUE checksumTamperGuard=TRUE frozenParamFixture3And5=TRUE fixedRiskContract=TRUE externalFinalUnopened=TRUE`.
   - M1 2020–22 **sintético** de 36 meses, 8 sesiones/mes; 22 genomas evaluados con V12 económico/V9, 10 revisados individualmente, 5 pasan G0, pero portafolio queda correctamente **RECHAZADO** por riesgo/diversificación, sin abrir holdouts ni inventar ganadores. Se crean 22 filas de ranking, 22 descartes, **30 métricas anuales** y **360 mensuales** para los 10 auditados, recibos detallados y 16 archivos.
   - Segunda ejecución idéntica: **0 nuevas evaluaciones económicas** y paquete SHA256 **idéntico bit a bit**. Cambio de parámetros, cambio de OHLCV con SHA de origen declarado idéntico, o alteración de un informe: bloqueo o verificación fallida. Restaura informes con el mismo hash reusando los 22 scores.
   - **Fixture de exportación positiva de parámetros**: 3 y 5 genomas EXCANv19 fabricados a propósito producen exactamente 60/100 filas de 20 parámetros; esta prueba valida serialización, **no** certifica ninguna estrategia ganadora.
3. **Regresión histórica V22**: `NQ_V22_FULL_FUNNEL_PASS geneticUnique=22 robustAudited=10 robustPass=5 result=PORTFOLIO_RISK_OR_DIVERSITY_REJECT folds=4 foldedGenomes=88 version=EXCANv19 noFutureLeakage=TRUE`, garantizando que el hook de V23 no cambió el embudo.

El primer CI de V23 [42288828765](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42288828765) falló porque el workflow temporario no copió módulos C# con una regex; **se corrigió sustituyendo la copia por ProjectReference a la fuente ya compilada**. Las corridas finales tienen 3/3 green.

## Límites y no afirmaciones

- No hay datos reales históricos de NQ DEC2026 en este repo/CI; las 22 evaluaciones económicas y sus métricas son **sintéticas**. No existe todavía cartera rentable descubierta/validada con todas las puertas reales.
- No existe aún el rendimiento real de 100.000+ backtests completos de toda DEV 2020–22: eso es exclusivamente **V24**. La prueba V19 de 109.464 genomas fue de score sintético y **no** se reclasifica.
- Los 4 folds train-only V20 prueban estabilidad del **generador**, no la capacidad predictiva independiente del mismo portafolio ya elegido. Los períodos OOS 2023–24 y 2025–oct2026 siguen cerrados, y solo se abren luego de congelar parámetros según V16.
- El riesgo M1 estrés con extremos altos/bajos sigue siendo proxy, no cumplimiento de reglas MFFU certificado ni paridad exacta NT8.
- **No pedir nuevas comprobaciones de contratos/rollovers ni pruebas F5/Strategy Analyzer intermedias.** La serie final del usuario es **NQ DEC2026** y confirma visualizar datos 2020–22 allí. La única integración/validación nativa está reservada a **V25**.
- El lock es una garantía de continuidad local de un directorio de resultados; no constituye una firma de un tercero ni seguridad frente a un usuario con control total de archivos. La identidad de ejecución incluye rutas locales: replicar byte a byte es demostrable **en la misma ubicación y configuración**; el commit Git de la rama consolidada pincha el árbol de código.

## Consolidación de cambios

V23 contiene el histórico de funciones V11–V22 y nuevo ejecutor en una misma rama basada en la última versión, con un `.csproj` de **módulos explícitos**. El repositorio mantiene PRs apilados históricamente y se presenta una **integración acumulativa única a `main`**, evitando exigir al usuario que fusione una docena de PR independientes para construir la aplicación.

Aun si el PR acumulado queda abierto/revisable, **no** afirmar que el código ya fue fusionado a `main` hasta comprobar el merge. La continuidad de V24 usa el árbol fuente integrado, no reinterpreta V23.

## Siguiente fase: V24 sin cambios de nombre

V24, definido antes de V23 y congelado en el contrato, se enfocará exclusivamente en **escala económica con escenarios de longitud equivalente a 36 meses** y pruebas progresivas hacia 10k–100k backtests V12 completos, medición de CPU/memoria y detección de cuellos reales. El generador y reportes ya corresponden a V23; no se traslada el objetivo.


## Estado de consolidación verificado al cierre de V23

- **Fusionado, no solo propuesto:** [PR acumulado #82](https://github.com/rgentil2/MES-Trading-Research/pull/82), squash merge a `main`, commit **`d1d7bd434e89f28e696e37c9a5eb00c2c97a5a29`**.
- **Matriz del PR completada antes de fusionar: 14/14 workflows SUCCESS** (versiones V10–V23). Los PR históricos apilados #70–#81 quedaron **cerrados como reemplazados** por el árbol acumulado, no fusionados individualmente.
- El ejecutable autónomo `NQResearchV23.csproj` incluye **42 módulos C# enumerados** de la rama principal y permite reconstruir el software sin depender de una cadena de PR.
- El cierre de software de V23 NO significa que exista una estrategia rentable de mercado NQ ni que se haya completado la validación en NinjaTrader. El objetivo fijo de **V24** es escalar el backtest económico largo; **V25** será la única comparación nativa final.
