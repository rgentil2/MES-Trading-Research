# S0.54 — V4 NinjaTrader: generador aleatorio de identidades únicas ANTES del backtest

**2026-11-02.** Usuario confirmó que guardó la plantilla de Strategy Analyzer `NQ_V3_FITNESS_2020_2022`. V1/V2/V3 continúan instaladas. Este desarrollo V4 está diseñado para el objetivo de búsqueda **100 % dentro de NinjaTrader**, pero el adaptador de Optimizer aún **NO se ha compilado ni ejecutado en Windows NinjaTrader real**. No afirmar que las 10k estrategias únicas ya están probadas.

## Código entregado (solo dos archivos nuevos)

1. `research/nq/ninjatrader/NQNativeUniqueSearchV4.cs`: motor C# puro con Random sembrado, 16 genes, rangos `Min/Max/Increment`, identidad booleana V3 `NQNativeBooleanCanonicalV3.Analyze`, rechazo de reglas con hojas internamente redundantes, HashSet de `RuntimeKey` para detectar duplicados, conteos completos: `Attempted/GeneratedUnique/RedundantSkipped/DuplicateSkipped/InvalidSkipped`. La firma respeta warmup/Reverse/SL/TP/maxDaily para evitar declarar igual una ejecución que no lo es. Sin mercado, sin Python.
2. `research/nq/ninjatrader/NQNativeUniqueOptimizerV4.cs`: Optimizer NinjaScript propio `OnOptimize()`, genera candidatos desde el motor V4, los verifica y fija parámetros, SOLO ENTONCES llama `RunIteration()`; imprime una línea de diagnóstico `NQ_V4 PRE_RUN candidate=... uniqueId=...` antes de cada evaluación y `NQ_V4 END executed=... generatedUnique=... attempted=... structuralRedundantSkipped=... equivalentFingerprintSkipped=... invalidSkipped=... exhausted=...`. **Este primer V4 es exploración Random con deduplicación, NO un Genetic con crossover/mutación**. La fase evolutiva seguirá cuando NT8 certifique asignación de genes/ciclo de iteración.

**Precaución crucial — API del Optimizer:** La documentación oficial confirma `OnOptimize`, `Strategies[0].OptimizationParameters`, `NumberOfIterations` y `RunIteration`, PERO no documenta exhaustivamente los nombres de las propiedades de `Parameter`. Por eso V4 usa reflexión de lectura/escritura **estrictamente validada** de `Name/Min/Max/Increment/Value` (también algunos alias), identifica las 16 propiedades de V3 por nombre o etiqueta y hace readback antes de cada backtest. Si la versión NinjaTrader no expone estos campos, imprime `NQ_V4 STOP binding validation: ... members=[...]` y ejecuta **CERO backtests**; es correcto fallar de forma segura, sin asignar valores dudosos. No modificar ni reemplazar archivos internos de NT8. La interfaz exacta solo puede resolverse compilando y ejecutando el pequeño smoke real en Windows.

## Pruebas independientes de CI (no certifican plataforma NT8)

`nq-native-v4-s054-seeded-unique-shim-source-qa.yml`:
- Compila y ejecuta el **C# de producción**, V3 canonicalizer + V4 generator, con .NET 8. 20.216 aserciones, busca 1.000 identidades distintas, mantiene un orden reproducible con seed=20261102, valida A=C/absorción, genes inactivos no crean falsas identidades y rangos exactos. En la muestra CI obtuvo **1.000 candidatos únicos en 1.280 intentos** (224 equivalentes/56 redundantes), que son genotipos calculados **sin backtests**.
- Compila el código del adaptador V4 real frente a un **SIMULADOR DE API NinjaTrader** marcado explícitamente `SHIM`; prueba tres escenarios: un caso equivalente se evalúa **una sola vez**; muestra con 20 estructuras permite 20 llamadas únicas a `RunIteration`; parámetro `Value` de solo lectura da cero llamadas y STOP. El shimming **no garantiza** compilación del adaptador contra los assemblies de NinjaTrader Windows.
- Contrato estático confirma que deduplicación precede a `RunIteration` y V3 sigue `State.Historical` exclusivamente.
- No incluye datos históricos ni ejecuta pruebas IST/ISV.

## Instalación en NinjaTrader Windows, solo después de integrar cambios

1. Con NinjaTrader **cerrado**, descargar **Raw** los nuevos `NQNativeUniqueSearchV4.cs` y `NQNativeUniqueOptimizerV4.cs` desde GitHub.
2. Copiar **`NQNativeUniqueSearchV4.cs`** a `Documentos\\NinjaTrader 8\\bin\\Custom\\Strategies`, junto al helper anterior `NQNativeBooleanCanonicalV3.cs`. **No sustituir V3**.
3. Copiar **`NQNativeUniqueOptimizerV4.cs`** a `Documentos\\NinjaTrader 8\\bin\\Custom\\Optimizers` (si carpeta no existe, comprobar `Optimizers` dentro de NinjaScript Editor y crear archivo/script en categoría correcta; la categoría es soportada oficialmente).
4. Abrir NinjaTrader → `New → NinjaScript Editor` → `F5 Compile`. Si aparece error, capturar archivo, línea y mensaje. El compilador incluye todos los archivos personalizados.
5. En Control Center abrir `New → NinjaScript Output` para leer `NQ_V4` y `NQ_V3_CANONICAL_RUNTIME`. Confirmar ausencia de errores de compilación.

### Prueba REAL A — compatibilidad de parámetros antes de la búsqueda

En Strategy Analyzer `Optimization`, `Strategy = NQNativeGeneticLabV3`, **`Optimize on = NQNativeStructureFitnessV3`**, `Optimizer = NQNativeUniqueOptimizerV4`, y propiedades V4: `UniqueCandidates=3`, `Seed=20261102`, `MaxAttempts=100`. Usar siempre NQ Last M1 2020–22, merge original, plantilla RTH, Include Commission + **NinjaTrader Brokerage** seleccionada, Standard (Fastest), 2 ticks de slippage, limit-touch desactivado, máximo 1 NQ.

Reusar los parámetros de la **plantilla V3 guardada**, con sólo Count variable 2..4 step1 y los demás 15 congelados A2/18 B7/6 C2/18 D9/30, AB1 BC0 CD0 Reverse1 SL20 TP32 Daily2. Es deliberadamente un espacio en que:
- Count=2, `A OR B` -> no redundante → **1 llamada a RunIteration como máximo**.
- Count=3, `(A OR B) AND A` -> rechazada ANTES de RunIteration.
- Count=4, `((A OR B) AND A) AND D` -> rechazada ANTES de RunIteration.

Resultado esperado si el ABI de Parameter permite asignación:
- `END executed=1 generatedUnique=1 structuralRedundantSkipped > 0 exhausted=True`.
- La tabla de resultados debería contener **solo una evaluación**, no tres, y su genotipo count2 debería mostrar el neto conocido de aproximadamente -US$46.390,72 con costes correctos.
- Es normal que el contador `NumberOfIterations` haya sido anunciado como 3 pero la búsqueda termine con solo una evaluación por agotamiento de identidades válidas. Si el motor NT8 exige una cantidad fija y se bloquea, detenerse: ajustar la forma de anunciar/progreso, nunca forzar backtests redundantes.
- Si aparece `NQ_V4 STOP binding validation` o `STOP iteration`, capturar la línea entera. **No** hacer búsqueda de 20 o 10.000, no asumir backtests ejecutados.

### Prueba REAL B — 20 candidatos únicos (solo tras A)

Ampliar solo algunos rangos: `Count 1..4`, `AType 0..9`, `APeriod 6..30×6`, `BType 0..9`, `BPeriod 6..30×6`, mantener C/D y demás fijos (y SL20 TP32 fijo sólo para smoke). Fijar V4 `UniqueCandidates=20`, `MaxAttempts=2000`, `Seed=20261102`, Keep best results=20. Confirmar:
- `NQ_V4 END executed=20`;
- huellas `NQ_V4 PRE_RUN` **20 distintas**;
- ningún `NQ_V4 PRE_RUN` con reglas booleanas redundantes; y
- cada `NQ_V4 PRE_RUN uniqueId=...` debe coincidir con el `NQ_V3_CANONICAL_RUNTIME id=...` correspondiente de instancia histórica. Si las huellas no coinciden, la interfaz de asignación está alterando los genes y hay que **bloquear** la búsqueda.
- No inferir PnL positivo ni cumplimiento G0 de 20 genotipos.

## Qué aún NO está resuelto

- En este V4, explorar Random con dedup **no es todavía un algoritmo genético evolutivo**; se programarán crossover/mutación una vez la interfaz real de parámetros quede verificada.
- 1.000 identidades en CI fueron **generadas** sin backtest. Ninguna búsqueda de 1.000/10.000 todavía se ha ejecutado en NT8. La cantidad total de estrategias realmente evaluadas dependerá de la configuración, opciones y acceso histórico de usuario.
- Tampoco están las 132 rutas de indicadores, salidas ATR dinámicas (solicitud explícita del usuario), PF/DD/formal G0–D2, OOS 2023/24, datos 2025/26 ni portfolio de riesgo compartido MFFU.
- Se mantienen los límites 09:35–11:27 ET y cierre solicitado fin de 11:28, sin operar cuenta real.
