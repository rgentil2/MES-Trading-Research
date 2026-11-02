# S0.45 — NQNativeGeneticLabV2: instalación y primer backtest de la gramática estructural

**Fecha 2026-11-02 · Estado: archivo fuente C# nuevo; todavía NO compilado ni ejecutado en NinjaTrader Windows.** La V1 real compilada del usuario y su primer backtest/Genetic siguen intactos. Esta versión **no necesita Python, PowerShell, ticks, ni bibliotecas externas**; emplea exclusivamente NT8 Strategy Analyzer Standard M1, NQ Last.

## Qué cambia realmente respecto a V1

- [`NQNativeGeneticLabV2.cs`](ninjatrader/NQNativeGeneticLabV2.cs): 1–4 condiciones activas A/B/C/D, cada una elige tipo 0–9 y período 2–117. Los operadores `CombineAB`, `CombineBC`, `CombineCD` son genes independientes, `0=AND, 1=OR`.
- Evaluación **de izquierda a derecha**: `(((A opAB B) opBC C) opCD D)`; si `ConditionCount` es 1/2/3, no se evalúan las ramas desactivadas. Las señales bullish y bearish se combinan de igual forma; si ambas verdaderas o ambas falsas, se abstiene; `ReverseSignals` opcional.
- 16 propiedades NinjaScript optimizables en lugar de 9; la colección **continúa siendo solamente 10 primitivas** (SMA/EMA/WMA/RSI/CCI y comparaciones/cruces simples), NO los 132 indicadores ni árboles arbitrarios con 1–8 condiciones por sentido. El optimizador Genetic puede re-evaluar combinaciones funcionalmente idénticas, todavía sin deduplicación.
- SL/TP **ticks solo como placeholder del primer smoke** de estructura, para comparar V2 contra V1; el usuario priorizó **salidas adaptativas ATR** más adelante. No se incluyó ATR en esta entrega por indicación expresa. No promover rentabilidad de esos stops como solución final.
- Invariantes preservados: historical-only, max 2 entradas al día, una unidad NQ por entrada, 09:35–11:27 señales, flatten solicitado al cierre de la barra 11:28 para próximo fill ~11:29, IST2020–22, NQ M1 Last, Standard, limit-touch=false, slippage2, include commission con plantilla efectiva NT8, pausa cerrada -$600 y límite aproximado de riesgo inicial $300 provisionales.

## Paso 1 — Instalar SIN reemplazar V1

1. Descargar **Raw** de `NQNativeGeneticLabV2.cs` y comprobar extensión `.cs`.
2. Cerrar NinjaTrader. Copiar archivo a **Documentos\\NinjaTrader 8\\bin\\Custom\\Strategies\\NQNativeGeneticLabV2.cs** (la carpeta de NinjaTrader puede estar bajo OneDrive Documentos dependiendo de instalación). **No eliminar ni editar** `NQNativeGeneticLabV1.cs`, `NQNativeM1DataAuditV1.cs` ni `NQNativeResearchFitnessV1.cs`.
3. Abrir NinjaTrader 8 → **New → NinjaScript Editor** → **F5 (Compile)**. Resolver cualquier error real reportado; GitHub no puede compilar contra las librerías instaladas de NinjaTrader. Si no aparece en Strategy Analyzer, cerrar/reabrir Analyzer y confirmar compilación.

## Paso 2 — Prueba de equivalencia de V2 contra V1 (OBLIGATORIA antes de explorar)

**Control histórico:** el usuario ya ejecutó V1 2020–22 con el genotipo base `AType0 / APeriod12 / BType7 / BPeriod14 / AND0 / Reverse0 / Stop20 / Target32 / MaxDaily2`, obteniendo **1546 trades, -US$43.554,96, PF0,64, DD cerrado -US$44.380,44**, comisión US$5,76 RT. No usar el ganador genético para este control (fue elegido in-sample).

En **Strategy Analyzer → Backtest** escoger `NQNativeGeneticLabV2`; establecer:

| Parámetro | Valor para prueba idéntica V1 |
|---|---:|
| Condition count (1..4) | **2** |
| A type / A period | **0 / 12** |
| B type / B period | **7 / 14** |
| C type / C period | 4 / 18 (inactivos) |
| D type / D period | 6 / 20 (inactivos) |
| AB (AND=0 OR=1) | **0** |
| BC / CD | 0 / 0 (inactivos) |
| Reverse | 0 |
| Stop ticks | **20** |
| Target ticks | **32** |
| Max daily entries | 2 |

Mantener **exactamente el mismo merge NQ** confirmado por usuario, Last/Minute/1, horario Eastern DST, plantilla de sesión RTH, 2020-01-01 a 2022-12-31, Include Commission (misma NinjaTrader Brokerage), `Standard (Fastest)`, `Fill limit orders on touch = False`, `Slippage=2`, Break at EOD activado, 1 contrato, histórico-only. Ejecutar **Run** y comprobar **1546 órdenes, neto -US$43.554,96, PF0,64 y sin variación en tiempos**. Una diferencia relevante bloquea la expansión y exige comparar Trades CSV V1/V2 antes de avanzar; no se puede afirmar equivalencia hasta esa prueba real.

## Paso 3 — Probar la estructura 1, 3 y 4 sin optimizar

Una vez la comparación a dos condiciones pase:
- `ConditionCount=1`: usa **solo A** (B/C/D y los operadores no afectan).
- `ConditionCount=3`: usa A/B/C, por ejemplo `CType=4 CPeriod=18 CombineBC=1` (OR) con AB=0.
- `ConditionCount=4`: además incorpora D, por ejemplo `DType=6 DPeriod=20 CombineCD=1`.

Ejecutar Backtest por cada estructura, observar cambios de operaciones y comprobar: ninguna entrada en 2023+, jamás posición al cierre RTH, no más de 2 entradas por sesión, coherencia de operaciones y comisión. **No buscar rentabilidad cambiando a mano reglas sobre 2020–22**; esta es una prueba de programación.

## Paso 4 — Primera optimización técnica V2 pequeña

Solo después de los tres backtests estructurales, elegir `Backtest type = Optimization`, `Optimizer = Genetic`, `Optimize on = Max. net profit` **como diagnóstico**, `Keep best # results = 20`. **Generation size=20, Generations=5**, crossover 80%, mutation 20%, otros valores genéticos por defecto. Esto son ~100 evaluaciones **nominales**, NO 100 genotipos únicos. Respetar 2020–22.

Usar estos rangos en **Min / Max / Increment** (primera versión limitada y reproducible, sin optimizar todavía stops/targets):

| Gen | Min | Max | Increment |
|---|---:|---:|---:|
| ConditionCount | 1 | 4 | 1 |
| AType | 0 | 9 | 1 |
| APeriod | 6 | 30 | 6 |
| BType | 0 | 9 | 1 |
| BPeriod | 6 | 30 | 6 |
| CType | 0 | 9 | 1 |
| CPeriod | 6 | 30 | 6 |
| DType | 0 | 9 | 1 |
| DPeriod | 6 | 30 | 6 |
| CombineAB | 0 | 1 | 1 |
| CombineBC | 0 | 1 | 1 |
| CombineCD | 0 | 1 | 1 |
| ReverseSignals | 0 | 1 | 1 |
| StopTicks | **20** | **20** | 1 |
| TargetTicks | **32** | **32** | 1 |
| MaxDailyEntrySubmissions | **2** | **2** | 1 |

**Razón de dejar SL/TP fijos solo esta vez:** comparar la diversidad de estructuras sin confundir efectos de salidas, mientras se decide una gramática de salidas dinámicas ATR en una **entrega futura separada**.

## Evidencias que debemos revisar tras V2

- Captura de F5 compilación limpia.
- Backtest 2-slot con parámetros de V1, capturas Summary y Trades para verificar igualdad real; si difiere, no interpretar el resto.
- Backtests con 1, 3 y 4 hojas y cambios de frecuencia.
- Tabla completa Optimization Results V2 con valores de 16 genes por candidato y CSV de Trades de los mejores; la optimización es en-sample y **NO valida estrategias**.
- Mantener 2023 ISV1, 2024 ISV2 y 2025–26 sellados. No hay 132 nativos, CustomOptimizer 10K, DD flotante MFFU, cartera ni entrada real habilitados.

**Importante:** El workflow GitHub `nq-native-v2-s045-structural-4slot-source-qa.yml` valida propiedades de fuente, **NO compila ni ejecuta NT8**, por lo que la instalación en tu Windows es la siguiente prueba esencial.
