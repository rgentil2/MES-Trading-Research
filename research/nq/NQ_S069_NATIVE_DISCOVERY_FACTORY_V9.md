# NQ S0.69 — Primer módulo de fábrica de estrategias nativa (V9)

**Estado:** implementación inicial de selección exploratoria, NO equivalente completo a StrategyQuant X, NO listo para trading real.

## Motivo: no más auditorías manuales para cada candidato

V8 ya entregó los diagnósticos de los 20 candidatos de V5 con seed `20261102`. Resultado de auditoría interna de los logs de NinjaTrader:

| Observación (20 candidatos; suma no es un portafolio) | 2020 | 2021 | 2022 |
|---|---:|---:|---:|
| Trades de los 20 modelos | 6565 | 6529 | 3305 |
| Signals raw | 341706 | 341061 | 341668 |
| Bloqueos por `TryCompute` salida ATR | 124505 | 134562 | 223245 |
| Trades de los 15 modelos con bloqueos ATR en 2022 | 3986 | 3960 | 725 |
| Trades de 5 modelos sin bloqueos ATR en 2022 | 2579 | 2569 | 2580 |

20/20 candidatos rechazados por `LOW_PROFIT_FACTOR`; 19/20 por DD cerrado > $2k y estrés DD > $2k; 15/20 no alcanzaron 5 trades/mes; 16/20 PnL negativo; 2/20 menos de 150 operaciones. **Ninguno aprobado**. Nota: las cifras agregadas de 20 estrategias son repeticiones de backtests, no una curva combinada.

Se ha identificado el cuello de botella: `NQNativeATRExitMathV5.TryCompute` devuelve `false` si `rawStop > 55` ticks (o target ATR >240 / parámetros inválidos), y con ATR altos en 2022 más entradas quedan bloqueadas. El observador V8 agrupa esas causas bajo `blockedATR`: NO se puede atribuir el 100% de esos bloqueos al stop sin la desagregación subcausa, aunque el límite de stop es una explicación comprobable en código. **Nunca simplemente quitar el límite de 55 ticks o subir el presupuesto por trade**: en NQ $5/tick, 55 ticks cuestan $275 sin fees y slippage; la restricción de riesgo es deliberada.

## Qué se agregó

* `ninjatrader/NQNativeDiscoveryScoreV9.cs`: cálculo puro C# con validación del neto de cada operación contra la performance de NinjaTrader; evaluación cronológica de equity desde G0V7, penalización continua de profit factor, neto, drawdown por estrés M1, frecuencia de los 36 meses y resultados por año. Todas las métricas se calculan solo sobre 2020–2022; el score NO es una puerta de aceptación.
* `ninjatrader/NQNativeDiscoveryFitnessV9.cs`: **Optimization Fitness** que retorna el score continuo por candidato. Evita la situación actual en la que todas las estrategias reciben exactamente `-1e12` por fallar las reglas duras G0V7. Admite tanto la estrategia base V5 como V8 derivada y no toca órdenes. Imprime `NQ_DISCOVERY_V9 SCORE`.
* `tests/s069_v9` y `.github/workflows/nq-s069-v9-tests.yml`: tests puros y comprobación de que el adaptador no usa métodos de ejecución. **Las pruebas CI no sustituyen F5 en NinjaTrader**.

**No se modificaron** V5, V8, G0V6 ni G0V7. Los filtros de fondeo siguen siendo obligatorios antes de validar finalistas.

## Primera ejecución de descubrimiento en NinjaTrader 8

1. Conservar todos los archivos existentes. Instalar **solo dos** archivos nuevos en `Documentos\\NinjaTrader 8\\bin\\Custom\\`:
   - `NQNativeDiscoveryScoreV9.cs` dentro de `Strategies`;
   - `NQNativeDiscoveryFitnessV9.cs` dentro de `Optimization Fitnesses` (también puede colocarse en una carpeta NinjaScript Custom compilable si el namespace es correcto).
2. Abrir NinjaScript Editor, compilar con F5. Los nombres deben aparecer en Strategy Analyzer.
3. Ejecutar **primero** con `Strategy=NQNativeGeneticLabV5`, `Optimizer=NQNativeUniqueOptimizerV5`, `Optimize on=NQNativeDiscoveryFitnessV9`, `UniqueCandidates=100`, `Seed=20261102`, `MaxAttempts=10000`, `Keep best # results=50`. **No usar V8 observador para toda la búsqueda**: el coste de logs es innecesario. RTH M1 Last NQ continuo, 2020-01-01 a 2022-12-31, comisiones reales y slippage 2. Nunca fechas 2023+ en esta fase.
4. Reabrir rangos en `01 Generation`; evitar `Min=Max` en todos los genes. Ejemplo de rango exploratorio: ConditionCount 1..4; A/B tipos 0..9, periodos 6..30 increment3; C/D tipos 0..9, periodos 6..30 inc3; AB/BC/CD/reverse 0..1; ExitMode 0..3; ATRPeriod 7..28 inc7; ATRStopX10 10..30 inc5; ATRTargetX10 10..50 inc5; StopTicks=20, TargetTicks=32 y MaxDailyEntrySubmissions=2 inicialmente constantes. Estos rangos son de exploración, no parámetros optimizados validados.
5. Confirmar `NQ_V5 END executed=100 generatedUnique=100`, líneas `NQ_DISCOVERY_V9 SCORE ...` con valores **variados**, y ranking en Strategy Analyzer. **Aunque todos sean negativos, se ordenan en vez de descartarse sin información.**
6. Subir a lotes de 500+ candidatos después de verificar F5, IDs únicos y costes. Se pueden estudiar las principales estructuras sin relajar los límites del riesgo.
7. **G0 estricto separado:** reproducir los mejores genes encontrados en backtest con `NQNativeG0RiskFitnessV7`, sin hacer validación final sobre el mismo conjunto de 2020–22. Los aceptados deben pasar filtros adicionales out-of-sample y correlaciones, usando fechas reservadas solamente tras congelar las hipótesis y criterios.

Para evolución de parámetros existe también el optimizador nativo `Genetic` de NinjaTrader. Con esta nueva fitness continua sí puede discriminar candidatos, pero Genetic no garantiza deduplicación estructural; usar primero el optimizador V5 para descubrir estructuras únicas. **NQNativeUniqueOptimizerV5 aún es muestreo aleatorio sin cruces/mutaciones**, NO un GA equivalente a SQX.

## Arquitectura objetivo — por implementar, en este orden

1. **Catálogo de señales:** pasar de 10 tipos de señal a 100+ reglas efectivas / 132 indicadores seleccionados, con parámetros acotados, cálculos en caché, pruebas de equivalencia y canonicalización de árboles (no presentar variaciones de una misma regla como 100 indicadores).
2. **Motor de búsqueda:** generación estructural y evolutiva con selección, cruce y mutación, deduplicación **antes** del backtest, semillas reproducibles y reanudación; generación y ranking separados de aprobación. Evitar que Optimizer saque un solo candidato por rangos fijos.
3. **Robustez integrada:** ranking de IS, re-test OOS congelado, stress comisiones/slippage, variaciones de parámetros, Monte Carlo de trades (sin falsear cronología intraminuto), walk-forward y comparaciones interanuales. M1 no permite inferir ticks que no existen.
4. **Construcción de portafolios:** correlación de equity/operaciones y exposición simultánea, sizing conjunto con reglas de $2k trailing y pausa de $1k; no sumar de manera ingenua 20 backtests.
5. **Validación final:** comparar backtests idénticos de los candidatos ganadores en NinjaTrader con fechas y contratos correctamente roll-over; solo después SIM con registro cronológico real.

**Condición de cierre:** un sistema nativo de investigación de escala StrategyQuant es un programa por módulos, no una única optimización ni un solo NinjaScript. S0.69 construye y prueba el ranking continuo que faltaba, pero **aún NO** incorpora 132 indicadores, búsqueda evolutiva ni portafolios.
