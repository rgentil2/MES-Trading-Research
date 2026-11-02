# S0.49 — V3 NinjaTrader: huella semántica y fitness que penaliza redundancia interna

**Fecha:** 2026-11-02. **Estado:** código creado, helper C# puro compilado y ejecutado en .NET 8, tests reales PASSED. Los scripts V3 NinjaScript **todavía no han sido compilados en NinjaTrader 8 Windows** ni se han realizado nuevos backtests sobre IST. V1 y V2 sin modificaciones.

## Causa raíz observada en S0.48

La primera optimización estructural V2 conservó 20 resultados negativos; el menos negativo fue `4/2/18/7/6/2/18/9/30/1/0/0/1/20/32/2`, net **−US$8.286,32**, PF0,69, DD cerrado US$8.731,76, 357 trades. Combinó `((A OR B) AND C) AND D` con **A=C=(WMA slope,18)**. Absorción booleana: `((A OR B) AND A) AND D == A AND D`. Por tanto 4 hojas **declaradas** pero solo 2 condiciones booleanas efectivas. Este bug es de *exploración genética*, NO evidencia de un fill incorrecto de NinjaTrader.

## Implementación S0.49

1. [`NQNativeBooleanCanonicalV3.cs`](ninjatrader/NQNativeBooleanCanonicalV3.cs) — helper C# sin dependencias externas. Para 1–4 hojas activas, se define identidad de hoja `(SignalType, Period)`, calcula 2^N asignaciones de verdad (N≤4), elimina variables semánticamente innecesarias y construye una cadena canónica independiente de orden/permutación equivalente. Produce `BooleanKey`, `EffectiveLeaves`, `IsRedundant` y `Fingerprint` SHA256 abreviado. En identidad de **backtest** añade **calentamiento intrasesión requerido** y `Reverse, SL, TP, MaxDailyEntries`: reglas booleanas iguales NO implican necesariamente trades iguales si sus hojas redundantes aumentan el warmup. La identidad no cubre instrumentos/datos/costes (estos se mantienen fijos en esta campaña).
2. [`NQNativeGeneticLabV3.cs`](ninjatrader/NQNativeGeneticLabV3.cs) — Strategy separada (V1/V2 permanecen) que replica la lógica de órdenes V2 1..4 slots/16 genes y calcula la huella en `State.DataLoaded` por iteración. Expone `CanonicalReady`, `IsStructurallyRedundant`, `EffectiveConditionCount`, `CanonicalRuntimeFingerprint`. **No suprime órdenes en backtest**: así puede compararse V3 con V2 en un mismo genotipo y no cambia la estadística de un backtest individual.
3. [`NQNativeStructureFitnessV3.cs`](ninjatrader/NQNativeStructureFitnessV3.cs) — Optimization Fitness personalizado, **obligatorio en la primera búsqueda V3**: `Optimize on = NQNativeStructureFitnessV3` (NO Max. net profit). Pone `Value=-1e12` a candidatos con redundancia booleana o **cero trades** y `Value=net` a candidatos con hojas efectivas; es una **métrica exploratoria**, NO reemplaza filtros G0 (PF ≥1,25, DD ≤2k, frecuencia, etc.).

**Límite crítico:** la optimización Genetic nativa **todavía ejecuta los backtests** de genotipos redundantes y todavía puede repetir genotipos booleanamente equivalentes por permutación o genes de slots inactivos. El fitness solamente penaliza la puntuación de cada *estructura internamente redundante* y evita que un genotipo sin operaciones gane por obtener 0 frente a negativos. **No es un optimizador de 10.000 identidades únicas, no hace memoización entre generaciones.** Para deduplicar antes de ejecutar, se necesitará un Custom Optimizer NinjaScript basado en el contrato oficial `OnOptimize/OptimizationParameters/RunIteration`, verificando que su generación, semilla, set y ciclo de vida estén correctamente aislados; no se implementó aquí.

La equivalencia semántica considera las hojas como variables independientes, salvo que coincidan exactamente indicador y parámetros. No infiere correlaciones o alias entre indicadores diferentes. Esto evita reducir reglas distintas sin una demostración válida.

### Evidencia verificable ya obtenida

[Workflow #41520367760 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/41520367760): **el archivo C# exacto de producción `NQNativeBooleanCanonicalV3.cs` se compiló y ejecutó con .NET 8**, sumando **1.034 aserciones** sobre el caso real A=C, absorción, AND/OR conmutativos, hojas inactivas, warmup diferente, identidad de riesgo/Reverse, cuatro hojas esenciales, genes inválidos, estabilidad SHA. Además pasó un contrato estático de Strategy y OptimizationFitness; **NO se compilaron las dos clases NT8 contra assemblies NinjaTrader** (ausentes en el runner).

## Instalación NinjaTrader 8 (sin Python ni PowerShell)

1. Descargar los TRES `.cs` desde esta carpeta GitHub; conservar V1/V2 actuales.
2. Copiar `NQNativeBooleanCanonicalV3.cs` y `NQNativeGeneticLabV3.cs` a **`Documentos\\NinjaTrader 8\\bin\\Custom\\Strategies`**.
3. Copiar `NQNativeStructureFitnessV3.cs` a **`Documentos\\NinjaTrader 8\\bin\\Custom\\OptimizationFitnesses`**.
4. Abrir NinjaTrader 8 → `New → NinjaScript Editor` → F5 **Compile**. Si no compila, enviar screenshot con archivo/línea/error y no ejecutar la optimización.
5. **Primera paridad V2/V3:** Strategy Analyzer → `Backtest` → `NQNativeGeneticLabV3`; usar mismo NQ Last M1/merge/IST2020–22, Standard, slippage2, misma plantilla de comisiones NT8. Fijar `ConditionCount=2`, AType=0/APeriod=12, BType=7/BPeriod=14, CType=4/CPeriod=18, DType=6/DPeriod=20, CombineAB=0, CombineBC=0, CombineCD=0, Reverse=0, Stop20, Target32, MaxDaily2. **Debería reproducir métricas agregadas V2:** 1546 trades, net -US$43.554,96, PF0,64, DD cerrado -US$44.380,44. No declararlo probado hasta screenshot V3 en NT8; si difiere, detenerse.
6. **Prueba de la redundancia real:** Backtest V3 con `4/2/18/7/6/2/18/9/30/1/0/0/1/20/32/2` de S0.48. Debe coincidir con el backtest individual V2 (si las opciones son iguales): la huella *no* altera órdenes. El fitness V3 lo penalizará **solo al ejecutar Optimization**. El código no imprime un ID en resultados estándar; para comprobar visualmente la penalización seleccionar el fitness y observar puntuación `-1e12`. El valor de PnL seguirá siendo el neto histórico real.
7. **Genetic smoke V3 solo después de paridad V2/V3:** `Backtest type=Optimization`, `Strategy=NQNativeGeneticLabV3`, `Optimize on=NQNativeStructureFitnessV3` (**nunca Max net profit**), `Optimizer=Genetic`, `Keep best=20`, `Generation size=20`, `Generations=5`, crossover=80%, mutation=20%, otros por defecto. Reusar exactamente los mismos 16 rangos S0.48: count1..4 step1; A/B/C/D type0..9 step1; A/B/C/D period6..30 step6; AB/BC/CD0..1 step1; Reverse0..1 step1; Stop20/20/1; Target32/32/1; max2/2/1. No abrir 2023+.
8. Guardar captura de Optimization Results con parámetros visibles y fitness. Cuando un genotipo es **redundante internamente**, su fitness tiene que ser `-1e12`, por diseño; valores 0 por no-trades también `-1e12`. No asumir que las 20 filas son distintas ni que se evitó ejecutar sus backtests.

## Próxima fase después de instalar y validar

Crear **Custom Optimizer** que evite llamar `RunIteration()` para huellas ya vistas, con semilla y set aislados por ejecución; exigir 10K candidatos *efectivos* antes de finalización. También ampliar 132 indicadores y probar nuevas salidas dinámicas por ATR, como pidió el usuario, en una versión separada de este estudio de identidad. Posteriormente integrar G0/D0/D1/D2 y riesgo flotante MFFU 50K compartido. **2023–2026 permanecen sin leer** y no hay finalistas.
