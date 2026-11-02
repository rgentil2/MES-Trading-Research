# S0.52 — V3 detector probado en NinjaTrader, siguiente prueba determinista de Fitness

**Fecha: 2026-11-02.** El usuario ejecutó ambas pruebas sobre su instalación NinjaTrader8 con NQ Last M1 Standard (Fastest), 2020–2022, merge previamente confirmado, slippage2, `Include commission=true` y misma plantilla `NinjaTrader Brokerage`. Capturas originales conservadas en la conversación, sin copiar fotos ni datos de mercado al GitHub.

## Resultados de pruebas reales

**Control SIN redundancia (ConditionCount2)**:
- AType0/APeriod12 (SMA slope), BType7/BPeriod14 (RSI band), AB=0 AND, Reverse0, Stop20, Target32, MaxDaily2.
- `NQ_V3_CANONICAL_RUNTIME ready=True redundant=False effective=2 id=NQBC3_97A7396DFB465D4F93F4859D bool=BCANv1:00:012,07:014;tt=0001`.
- 1.546 operaciones (825 long,721 short), neto **−US$43.554,96**, PF0,64, max DD cerrado **−US$44.380,44**, comisión **US$8.904,96**. Confirmada restauración de costes tras la anterior corrida errónea sin plantilla.

**Caso CON redundancia real S0.48 (ConditionCount4)**:
- Genes completos 4/2/18/7/6/2/18/9/30/1/0/0/1/20/32/2. `((A OR B) AND A) AND D`, A=C WMA-slope18, B=RSIband6, D=crossover SMA30/EMA60. Algebra: `A AND D`; Reverse1.
- `NQ_V3_CANONICAL_RUNTIME ready=True redundant=True effective=2 id=NQBC3_D081C4AB236E860917A3463E bool=BCANv1:02:018,09:030;tt=0001`.
- 357 operaciones (170 long/187 short), neto **−US$8.286,32**, PF0,69, DD cerrado **−US$8.731,76**, comisión **US$2.056,32**. Resultado igual a su ejecución previa V2 con mismo genotipo/costes.

**Conclusión exactamente soportada:** el detector canónico y el flag de redundancia se calculan de verdad en `State.DataLoaded` dentro de NT8 para un caso sin redundancia y otro con redundancia; V3 preserva los agregados de V2 para las dos configuraciones y los costes ahora coinciden. **Aún NO se ha demostrado que `NQNativeStructureFitnessV3` sea visible ni que penalice en una optimización real**, mucho menos que evite ejecutar backtests duplicados por el Genetic. No promueven G0 ni abren ISV2023+.

## Siguiente prueba óptima: SOLO TRES variantes mediante Default Optimizer

Antes de una búsqueda genética de 100 o 10.000 candidatos, comprobar el contrato del fitness sin estocasticidad. En Strategy Analyzer:

1. `Backtest type = Optimization`, `Strategy = NQNativeGeneticLabV3`, **`Optimize on = NQNativeStructureFitnessV3`** (si no aparece, parar y revisar compilación de clase bajo `OptimizationFitnesses`), **`Optimizer = Default`**, `Keep best # results=3`, `Optimize Data Series = false`.
2. Mantener exactamente NQ Last M1, IST2020–22, Standard, 2 ticks slippage, commission template NinjaTrader Brokerage y RTH como los dos backtests confirmados.
3. **Sólo** `Condition count (1..4)` optimizado: **Min2, Max4, Increment1**, por lo que Default debe procesar tres combinaciones count2, count3, count4. Los otros 15 parámetros se fijan `Min=Max` y `Increment=1` en todos:
   - AType2, APeriod18; BType7, BPeriod6; CType2, CPeriod18; DType9, DPeriod30.
   - CombineAB1 (OR), CombineBC0 (AND), CombineCD0 (AND); Reverse1.
   - StopTicks20, TargetTicks32, MaxDailyEntrySubmissions2.
4. **Predicción de clasificación (no de PnL exacto)**:
   - Count=2: expresión `A OR B`, dos hojas esenciales, `redundant=False`, fitness = NetProfit del backtest (si genera operaciones).
   - Count=3: `(A OR B) AND A == A`, tres hojas declaradas, una efectiva, `redundant=True`, **fitness = -1e12**.
   - Count=4: `((A OR B) AND A) AND D == A AND D`, cuatro declaradas, dos efectivas, `redundant=True`, **fitness = -1e12**. Su **Total net profit** real debería permanecer cerca de **−US$8.286,32** si los costes y series son iguales; la penalización sólo afecta columna **Performance**, NO al neto del backtest.
5. Verificar columna `Parameters`, columna **`Performance`** (según guía oficial es valor del fitness seleccionado) y `Total net profit` por fila. Entregar captura con las tres filas; `NinjaScript Output` opcional para confirmar `ready/redundant/effective`. Si falta el fitness, hay excepción, difiere el count o los redundantes no valen -1e12: **NO** lanzar Genetic, hay que corregir la clase/selección.

Este ensayo fija expresamente 15 de 16 genes para aislar el comportamiento del filtro. **No mide competitividad económica ni corrige duplicación intergenotipo**. El último objetivo requiere un optimizer propio que se salte llamadas `RunIteration` para firmas previamente evaluadas; la biblioteca de 132 rutas y salidas ATR dinámicas siguen pendientes.

Referencias oficiales NinjaTrader: https://static.ninjatrader.com/support/helpGuides/nt8/optimize_a_strategy.htm y https://static.ninjatrader.com/support/helpGuides/nt8/optimization_fitness.htm.
