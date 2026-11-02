# S0.58 — V5 nativo NinjaTrader 8: ATR exits + 20 genes + deduplicación previa a backtest

**Fecha:** 2026-11-02. **Estado:** seis nuevos archivos C# en GitHub. Tests reales de C# puro + simulador de API NinjaTrader aprobados en CI. **NO COMPILADO AÚN EN NINJATRADER WINDOWS / NO BACKTEST V5 HECHO**; se requiere F5 y pruebas en Strategy Analyzer del usuario. V3/V4 no se modifican. `V5` no es un Genetic evolutivo, es `Random(seed)` con deduplicación semántica + salidas ATR.

## Archivos a instalar — seis, no sustituir V3/V4

Descargar desde GitHub como **Raw** o copiar el contenido exactamente, no descargar la página HTML.

| Nuevo archivo | Ruta de destino dentro de Documentos\\NinjaTrader 8\\bin\\Custom |
|---|---|
| `NQNativeATRExitMathV5.cs` | `Strategies` |
| `NQNativeExitCanonicalV5.cs` | `Strategies` |
| `NQNativeUniqueSearchV5.cs` | `Strategies` |
| `NQNativeGeneticLabV5.cs` | `Strategies` |
| `NQNativeUniqueOptimizerV5.cs` | `Optimizers` |
| `NQNativeStructureFitnessV5.cs` | `OptimizationFitnesses` |

La dependencia `NQNativeBooleanCanonicalV3.cs` **debe conservarse** en `Strategies`; no instalar duplicados del mismo código. Cerrar NinjaTrader para copiar los archivos, abrir `New → NinjaScript Editor`, pulsar **F5** y revisar `NinjaScript Output / Error list`. **Si hay error de compilación:** no ejecutar; enviar captura con archivo, línea y mensaje. No borrar las versiones anteriores.

## Contrato de señales/horario/instrumento

- Misma base de señales V3: 1..4 condiciones de 10 primitivas, AND/OR asociativo izquierda, opción Reverse.
- **Histórico exclusivamente** `State.Historical`, NQ M1 Last, años 2020–22; no opera real ni SIM, no abre periodos ISV/OOS de 2023 en adelante.
- Entradas 09:35–11:27 ET; salir con envío a 11:28, posible llenado en barra siguiente (aprox. 11:29); `Calculate.OnBarClose`.
- Standard (Fastest), `IsFillLimitOnTouch=false`, comisión marcada **NinjaTrader Brokerage** (no basta marcar casilla: escoger plantilla) y slippage2. 1 NQ por entrada, cap2/day.
- Motor de órdenes nativo `SetStopLoss/SetProfitTarget`; V5 ajusta distancia ATR calculada con `ATR(ATRPeriod)[0]` de la barra de señal YA COMPLETADA, antes de colocar `EnterLong/EnterShort` (que llena en la barra histórica siguiente).
- `intendedStopTicks` = ceil(ATR / TickSize × multiplier) con stop bruto permitido [1,55] ticks; **se descarta señal si stop excede 55 ticks** para respetar el control de riesgo de investigación; TP ATR bruto permitido [1,240] ticks. Se evita recortar silenciosamente los valores (cambiaría la estrategia y favorecería selección sesgada).
- La protección es previa al fill. **Es una barrera aproximada de riesgo**, NO el trailing drawdown oficial MyFundedFutures ni estrés intrabar; slippage/gaps reales aún pueden superarla.

## V5 4 modalidades de salidas

- `ExitMode=0`: SL fijo `StopTicks` y TP fijo `TargetTicks` (0 = sin objetivo). **Debe reproducir V3 exactamente** a igualdad de los 16 genes, histórico y costes.
- `ExitMode=1`: SL ATR dinámico fijado por barra de entrada, TP fijo `TargetTicks>0`.
- `ExitMode=2`: SL ATR y TP ATR, ambos fijados con la ATR de la señal.
- `ExitMode=3`: SL ATR y **sin objetivo de beneficio**; cierre obligatorio horario. Aún NO es trailing stop; no incluye salida por señal inversa.
- `ATRPeriod=7..28`, `ATRStopX10=10..30` (=1,0–3,0×), `ATRTargetX10=10..50` (=1,0–5,0×). P.ej. 15 = 1,5× ATR, 25 = 2,5×.
- Se hace warmup intra-sesión conservador `max(requiredSignals,ATRPeriod+4)` en modos ATR; en modo0 no se aumenta.
- La huella `NQEX5_...` incorpora solo los genes de salida que afectan a cada modo, además de la expresión boolean canónica y el warmup. Genes de salida inactivos NO generan falsos nuevos candidatos.

## Prueba REAL A — calibración obligatoria V3/V5 (`ExitMode=0`)

No empezar con optimización: primero **Backtest** de una sola combinación conocida:

`Strategy = NQNativeGeneticLabV5`, NQ M1 Last, 2020-01-01 a 2022-12-31, mismas sesiones/roll/fees/slippage/historical fill que V3. Cargar valores:
- `ConditionCount=2`
- `AType=0, APeriod=12`, `BType=7, BPeriod=14`.
- `CType=4,CPeriod=18`, `DType=6,DPeriod=20` (inactivos).
- `CombineAB=0,CombineBC=0,CombineCD=0`, `ReverseSignals=0`.
- `StopTicks=20,TargetTicks=32,MaxDailyEntrySubmissions=2`.
- `ExitMode=0,ATRPeriod=14,ATRStopX10=15,ATRTargetX10=25`.
- **Control V3 real**: 1546 trades, **net −$43.554,96**, PF 0,64, máximo drawdown de operaciones cerradas −$44.380,44, comisiones $8.904,96. El criterio fundamental es **igualdad exacta** en trades/net/comisiones/drawdown con la misma configuración (sin ajustar el modelo para obtener esta igualdad).

En NinjaScript Output: `NQ_V5_EXIT_RUNTIME ready=True redundant=False ... id=NQEX5_...`.

Si 1546 o neto no coincide, **NO** pasar a ATR: revisar exactamente parámetros, commissions, trading hours, session timezone, merge, fill. Cargar V3 y V5 en backtests separados en idéntico rango para comparar si es necesario.

## Prueba REAL B — tres salidas ATR aisladas

Una vez superada A, repetir backtest sin tocar las condiciones ni el dataset:
- modo1 (`ATRPeriod14,StopX10=15,TargetTicks32`);
- modo2 (`ATRPeriod14,StopX10=15,TargetX10=25`);
- modo3 (`ATRPeriod14,StopX10=15`, sin target).

Cada modo debe imprimir una huella `NQEX5_` diferente. **No se espera igualdad de PnL con V3**, ni rentabilidad positiva; es validación funcional de órdenes, cantidad de entradas, tiempos de salida y riesgo. Revisar `Trades` para posiciones simultáneas, stops inválidos, cierres a 11:28, salidas dentro de horario y SL máximo provisional. Si los 3 dan 0 trades, puede ser ATR/risk gate demasiado estricto y no implica motor correcto.

## Prueba REAL C — deduplicación de 20 genes, 20 únicos

`Backtest type=Optimization`, `Strategy=NQNativeGeneticLabV5`, `Optimize on=NQNativeStructureFitnessV5`, `Optimizer=NQNativeUniqueOptimizerV5`, `UniqueCandidates=20`, `Seed=20261102`, `MaxAttempts=2000`, `Keep best=20`.

Mantener con rango todos los 20 genes si Analyzer los muestra; si algún `STOP binding validation`, no ejecutar, enviar log. Configuración de smoke:
- Count1..4 inc1
- AType0..9 inc1, APeriod6..30 inc6; BType0..9 inc1, BPeriod6..30 inc6;
- C2/18 y D9/30 fijos;
- AB=1, BC=0, CD=0, Reverse=1, Daily=2;
- StopTicks=20, TargetTicks=32 (controles heredados);
- ExitMode0..3 inc1, ATRPeriod14, ATRStopX10=15, ATRTargetX10=25 (primero explora modos, luego parámetros).

Resultado buscado: `NQ_V5 BEGIN ... selectedParams=20`, **20 PRE_RUN con firmas distintas**, `NQ_V5 END executed=20 generatedUnique=20 failure=0 exhausted=False`, V5 runtime ids en conjunto idénticos a 20 PRE_RUN. Si `STOP` o menos de 20, detener, revisar logs. No abrir 2023–26. No aceptar un candidato por performance positiva hasta G0 formal con DD, PF, ntrades, costes, múltiples particiones.

## Qué está validado FUERA de NinjaTrader

[CI .NET8 QA S0.58](https://github.com/rgentil2/MES-Trading-Research/actions/workflows/nq-native-v5-s058-atr-csharp-qa.yml) compila/ejecuta en C# real código de producción de V3 Boolean, V5 exits math/identity/generator: **24.046 aserciones**, 1.000 identidades de salida/estructura en 1.057 intentos (39 redundant, 18 equivalentes), reproducciones semilla, exactitud modo0 key/warmup, ATR5 / 0,25 => stop30 target50, redondeo ceil, NaN/Inf/cap, colapso de genes inactivos. El Optimizer V5 compila contra un **mock NT8** y supera tres pruebas de escritura y fail-closed del API. Estos tests no incluyen la clase Strategy compilada contra NinjaTrader ni PnL histórico; solo un NinjaTrader Windows real puede confirmar ese punto.

## Limitaciones y próximos hitos

V5 mantiene solo 10 señales primitivas (no 132). No implementa trailing ATR ni evolución genética real. Los stops ATR se fijan en la entrada, no se desplazan cada barra. El fitness V5 solo evalúa neto después de descartar genotipos redundantes y sin operaciones; aún no incorpora PF/DD/criterios de G0. No hay backtests V5 certificados, 10k búsquedas, holdouts 2023+ ni portafolio validado. Ningún resultado de V4 perdedor constituye una estrategia de trading utilizable.
