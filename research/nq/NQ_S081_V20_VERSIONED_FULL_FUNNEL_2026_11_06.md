# NQ S0.81 — V20: Embudo versionado de 1.320 condiciones hasta robustez, portafolio y OOS
**Fecha:** 2026-11-06  
**Estado:** Implementación fuente C# y QA sintético 2/2 SUCCESS, NO validación NinjaTrader.  
**Referencia de la validación futura única:** serie `NQ DEC2026` visible en NinjaTrader 8 con datos M1 2020–2022 según confirmación del usuario.

## Objetivo ya implementado

Conectar el genoma canónico `EXCANv19` (120 fórmulas técnicas, 1.320 señales) al **embudo de investigación que existía en V13–V16**. Se ha preservado la compatibilidad con las anteriores 132/396 condiciones sin reetiquetar estrategias; el antiguo runner V16 y los tipos V11/V18 siguen presentes. **Sin auditorías adicionales de contratos/rollovers**, sin compilaciones NinjaTrader parciales, sin añadir datos externos al conjunto de entrenamiento.

El nuevo `NQNativeResearchRunnerV20.Run` combina:

1. Insumo exclusivo **2020–2022** (`NQDataPartitionV16.Development2020_2022`), manifiesto y cobertura mínima mensual explícita.
2. Generación evolutiva V12 con **todos los 1.320 predicados V19**, cache V14, simulador de mercado conservador M1 V12 y score exploratorio V9. Diario opcional V17 de reanudación por identidad SHA256 de dataset, reglas y genética.
3. Auditoría sobre ranking de candidatos únicos: reglas G0 V7/V13, frecuencia, PF, resultado neto, DD, costos 1,5× y bootstrap. **Cada superviviente mantiene su genoma `EXCANv19` original**, no se lo reinterpreta como V11.
4. Selección diversificada **3–5 estrategias** con V13; conciliación de cada trade con cada fill; **riesgo de cuenta conjunto minuto a minuto V15**, drawdown bajo orden adverso y exposición simultánea.
5. **`NQNativeWalkForwardV20`**: copia controlada de la metodología V15 de cuatro ventanas móviles train-12 meses/validación-seis meses, con genomas EXCANv19 y señales V19. Cada nuevo genoma de un fold se crea solo usando datos anteriores a ese fold; por construcción no puede acceder a 2023–26.
6. Cuando **y solo cuando** los gates anteriores permiten un portafolio, crea `NQFrozenCandidateV16` con canonicalizador **V19** y la `NQNativeFrozenCampaignV16` versionada, usando `NQNativeV20OosEvaluator`. El SHA del congelado incluye los IDs, genomas, fuente de desarrollo, fecha de corte y etiqueta del evaluador V19. Luego **una sola** validación 2023–24; solo si pasa se habilita **una sola** validación 2025–octubre 2026, corte excluyente **2026-11-01**.
7. `NQNativeHeldoutSignalsV20` es una **caché LRU acotada** por bytes de señales V19 de barras RTH completas en los periodos OOS; no contiene GA, ajustes de parámetros ni score V9 de entrenamiento. Las ejecuciones externas/finales usan el **mismo** simulador de fills V12, con costes y stops conservadores.

## Código

Nuevos archivos:
- `research/nq/ninjatrader/NQNativeWalkForwardV20.cs`
- `research/nq/ninjatrader/NQNativeHeldoutSignalsV20.cs`
- `research/nq/ninjatrader/NQNativeV20OosEvaluator.cs`
- `research/nq/ninjatrader/NQNativeResearchRunnerV20.cs`
- `research/nq/ninjatrader/tests/NQNativeV20DevelopmentWalkForwardTest.cs`
- `research/nq/ninjatrader/tests/NQNativeV20FrozenOosTest.cs`
- `.github/workflows/nq-v20-versioned-portfolio-qa.yml`

Extensiones compatibles y no destructivas:
- `NQNativeExpandedResearchV19.cs`: expone lector de señales V19 al WF versionado.
- `NQNativeHistoricalEvaluatorV12.cs`: `EvaluateHeldoutCustom` aplica el mismo V12 `EvaluateCore` para genomas congelados V19, sin puntuación V9 OOS.
- `NQNativeFrozenCampaignV16.cs`: overload de candidatos y evaluador OOS con canonicalizador/firma versionados; el comportamiento anterior y tests V16 permanecen válidos.

## Pruebas y evidencia de CI

**[Run 42274607818](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42274607818) — 2/2 SUCCESS**.

**`development-walkforward`**
- `NQ_V20_DEV_WF_PASS geneticUnique=22 robustAudited=10 robustPass=5 result=PORTFOLIO_RISK_OR_DIVERSITY_REJECT folds=4 foldedGenomes=88 version=EXCANv19 noFutureLeakage=TRUE`.
- 36 meses **sintéticos** 2020–2022, 8 días completos por mes, puntuación V12 real sobre esa fuente sintética y V13 robustez. Cinco candidatos pasaron G0 individual pero el portfolio **fue rechazado** (no falseada rentabilidad); no se fabricó ningún congelado.
- Cuatro folds cronológicos; cambiando solo la segunda mitad de 2022 no se cambian los genomas ni los scores de entrenamiento de ningún fold. La inyección de partición 2023–24 fue rechazada por el runner, y cobertura insuficiente mensual provoca rechazo antes de usar el GA.

**`frozen-versioned-oos`**
- `NQ_V20_FROZEN_OOS_PASS canonical=EXCANv19 frozen=3 directCachedMatches=4056 oosScore=NONE combinedChronology=TRUE sourceCacheBuilds=2 oneShotExternal=TRUE finalLockedOnFail=TRUE freezeDigestBound=TRUE passingSyntheticExternalAndFinal=TRUE`.
- 4.056 comparaciones de señales 2023–24 (cálculo completo por prefijo frente a caché LRU); misma evaluación económica V12 con y sin caché para V19; clasificador V11 original rechaza genes 396+ en lugar de reinterpretarlos.
- El caso OOS **plano** (sin señales) rechaza tres candidatos congelados **sintéticamente aprobados** en la fixture y **mantiene 2025–26 bloqueado**.
- Un segundo caso con tendencia positiva perfectamente controlada demuestra que la rama de **2023–24 aceptado → 2025–oct 2026 habilitado** funciona con los **mismos tres genomas EXCANv19** y una única evaluación por segmento. Repetir externo/final es prohibido, y la fecha límite 2026-11-01 bloquea cualquier futuro. **La prueba de selección DEV aprobada es un stub intencional**, no una estrategia exitosa de mercado.
- Se conservan los tests V16 de compatibilidad. CI no requiere datos de usuario ni NinjaTrader.

## Qué NO se ha demostrado

- No se han evaluado estrategias V19/V20 con el histórico real de `NQ DEC2026`. **Ningún PF/neto/DD histórico real, rentabilidad o viabilidad de fondeo está probado.**
- La prueba masiva de 109.464 genomas V19 anterior usó una **función sintética de fitness**. Todavía no hay evidencia de que 100.000+ **backtests económicos completos** se hayan ejecutado eficazmente con los 36 meses reales de M1. El journal conserva scores y permite repetición, pero el rendimiento histórico real queda para el siguiente bloque.
- El walk-forward anidado de V20 prueba la **estabilidad del generador** por fold (un ganador congelado por ventana), **no** que el portafolio de 3–5 seleccionado sobre toda DEV tenga validación verdaderamente independiente dentro de DEV; la medida externa 2023–24 permanece sellada hasta congelar.
- La biblioteca tiene **120 fórmulas OHLCV programadas**, no 120 señales estadísticamente independientes ni 120 cálculos exactamente equivalentes a las versiones comerciales de NT8. Proxies de flujo no reconstruyen bid/ask/tick.
- La protección de reuso OOS V16 depende de una **instancia en memoria** y de la disciplina de campaña; no es una garantía criptográfica de que alguien no cree otra campaña. No presentar bloqueo lógico como antimanipulación infalible.
- No existe aún un AddOn nativo terminado ni una paridad con Strategy Analyzer o fills de NinjaTrader. Eso seguirá reservado a la **única migración/validación final** acordada.

## Siguiente prioridad P0: V21

**Búsqueda masiva económica verificable**: medir CPU/memoria/caché para decenas/miles de backtests completos y progresar hacia 100k, preservar resultados en disco (incluidos operaciones y razones de exclusión para shortlist), ranking estructurado y reanudación real de varias ejecuciones. Luego rematar empaquetado reproducible y reportes finales antes de integrar en NinjaTrader; sin reabrir auditoría de contratos ni compilar F5 de forma parcial.
