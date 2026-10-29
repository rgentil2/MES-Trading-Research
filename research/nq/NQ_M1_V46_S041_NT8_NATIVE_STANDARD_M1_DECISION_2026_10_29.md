# S0.41 — NinjaTrader 8 como único motor, con ejecución histórica Standard M1

**Decisión explícita, 29-oct-2026:** a partir de esta etapa, **la generación, señales, backtests y evaluación económica de nuevas estrategias se realizan directamente en NinjaTrader 8 mediante NinjaScript/C#**. Para descubrir estrategias aceptamos temporalmente la simulación de fills **Standard (Fastest)** de NinjaTrader 8 sobre **NQ Last M1**. **No** se requiere Python ni históricos tick ni equiparar el motor de NinjaTrader con el antiguo *stop-first* Python. El repositorio Python es solo **archivo de investigación anterior**, nunca fuente de señales/fill para esta campaña nativa.

## Configuración inicial nativa

| Elemento | Decisión S0.41 |
|---|---|
| Plataforma | NinjaTrader Desktop 8 / NinjaScript C# / Strategy Analyzer |
| Mercado | NQ, 1 contrato total de evaluación |
| Fuente | Histórico M1, Last, por contrato trimestral correcto |
| Procesamiento histórico de órdenes | **Standard**, algoritmo OHLC virtual interno de NinjaTrader |
| `Fill limit orders on touch` | **False** |
| `Slippage` | **2 ticks** por fill donde NinjaTrader lo aplique (acotado por el rango de barra según documentación) |
| `Include commission` | **True**, mediante plantilla de comisión NQ aplicada en la plataforma; verificar valor efectivo |
| Zona horaria plataforma | **Eastern Time (America/New_York)**, con DST |
| Trading Hours | Equivalente CME U.S. Index Futures RTH, 09:30–16:00 Eastern |
| Primera señal permitida | 09:35 ET, barra terminada |
| Última señal | 11:27 ET, para entrada histórica en siguiente barra |
| Cierre intradía | `ExitLong/ExitShort` en 11:28 close → próximo fill histórico, aproximado a apertura de barra 11:29 |
| Datos IST de descubrimiento | 2020–2022 únicamente |
| Fuera de muestra | 2023 ISV1 y 2024 ISV2 siguen **sin abrir** |
| Reservados/sellados | 2025–2026 siguen sin utilizarse |
| Rollover | Preservar política **jueves 8 días antes del tercer viernes trimestral**; no asumir que el Merge Policy o continuous del NT8 coincide automáticamente |
| Stop, límite diario y frecuencia | Provisionales para laboratorio; **NO** equivalen a reglas oficiales del plan MFFU 50K |
| ¿Cuenta real, broker fill o evaluación financiada? | **NO autorizados** |

**Razón:** NinjaTrader documenta que *Standard* divide una barra histórica en tres tramos virtuales utilizando su proximidad OHLC. Eso **no** reconstruye cada trade tick ni garantiza precio de ejecución real; lo aceptamos ahora como nuestro único modelo exploratorio y registramos las limitaciones, sin añadir un simulador Python ni su comparación como requisito previo. La validación posterior del **portafolio compartido** se hará también *dentro de NinjaTrader 8*, con las mismas opciones de datos y algoritmo **Standard**, más riesgo y robustez; ya no se exigirá paridad de fills con Python.

Fuentes oficiales:
- https://static.ninjatrader.com/support/helpGuides/nt8/understanding_historical_fill_.htm
- https://static.ninjatrader.com/support/helpGuides/nt8/orderfillresolution.htm
- https://static.ninjatrader.com/support/helpGuides/nt8/isfilllimitontouch.htm
- https://static.ninjatrader.com/support/helpGuides/nt8/includecommission.htm
- https://support.ninjatrader.com/s/article/How-Can-I-Import-Historical-Data?language=en_US
- https://static.ninjatrader.com/support/helpGuides/nt8/optimize_a_strategy.htm

## Código disponible

1. [`NQNativeM1DataAuditV1.cs`](ninjatrader/NQNativeM1DataAuditV1.cs) — **Strategy sin órdenes**: verifica NQ/1min, escala de ticks, coherencia OHLC, continuidad de barras RTH y sesiones completas de 390 minutos. Rechaza años fuera de IST. Los contadores se imprimen en **NinjaScript Output**; una sesión parcial se etiqueta REVIEW, no se modifica ni rellena.
2. [`NQNativeGeneticLabV1.cs`](ninjatrader/NQNativeGeneticLabV1.cs) — primera Strategy nativa experimental: 10 primitivas de señales, dos tipos A/B con períodos, AND/OR, reversión y SL/TP. Se puede probar con *Default* o *Genetic Optimizer* una vez compilado en Windows. S0.41 fija Standard, touch=false, comisión incluida, 2 ticks slippage y desactiva entradas en estado **Realtime** (solo procesamiento histórico).
3. [`NQNativeResearchFitnessV1.cs`](ninjatrader/NQNativeResearchFitnessV1.cs) — Optimization Fitness C# inicial; umbrales **150 trades, PF 1.25 y DD cerrado $2.000**. S0.41 corrigió propiedad NT8 oficial `Currency.Drawdown` (distinta capitalización de algunas versiones antiguas). Aún no incluye drawdown flotante de una cuenta fondeada.

**Importante:** esta versión V1 NO equivale a las 132 rutas nativas implementadas ni a un generador de 10.000 genotipos únicos. Los 10 indicadores son el conjunto piloto inicial; la gramática y las fórmulas C# deben extenderse. La optimización genética integrada varía parámetros y tipos expuestos pero **no garantiza 10.000 estrategias diferentes** ni evoluciona árboles arbitrarios de 1–8 condiciones. El portafolio compartido necesita un ejecutor NinjaScript independiente del Basket Test.

## Paso a paso en NinjaTrader 8

1. En Control Center → Tools → Settings → General seleccionar **Eastern Time / New York** y reiniciar NinjaTrader. Esta selección altera las etiquetas horarias; **configurar por separado Trading Hours RTH**.
2. Verificar histórico importado como `NQ ##-YY.Last.txt` (contratos individuales) o fuente ya instalada; en caso de importación desde TXT, **NinjaTrader (timestamps end-of-bar)**, **Last**, y zona horaria correspondiente al archivo. NinjaTrader convierte los datos importados al horario de la PC/plataforma. Verificar que la política de rollover en el gráfico/análisis corresponde a la congelada; no suponer que un símbolo continuo es equivalente.
3. En **NinjaScript Editor**, crear una estrategia y pegar `NQNativeM1DataAuditV1.cs` con el mismo nombre de clase/namespace. **Compile**. Abrir Strategy Analyzer → Backtest → NQ 1 Minute, Last, horario RTH, 2020–2022. Ejecutar el auditor. Revisar **NinjaScript Output**, sesiones completas, parciales y anomalías; el auditor no coloca operaciones.
4. Compilar la Strategy `NQNativeGeneticLabV1.cs` y (opcional) la `Optimization Fitness NQNativeResearchFitnessV1.cs` desde el editor. **No existe confirmación de que se hayan compilado en la instalación de Windows**: los errores reales deben corregirse allí, no ocultarse.
5. Strategy Analyzer → Backtest inicial, NQ M1, rango **2020-01-01 a 2022-12-30**, Standard fill, `Fill limit orders on touch=false`, slippage 2, **Include commission=true** y plantilla NQ (revisar coste exacto). Verificar que realmente produce operaciones, horas correctas, cero overnight y resultados con costes. **No ejecutar sobre 2023–26** todavía.
6. Para exploración de genotipos, cambiar Backtest type a **Optimization** y usar primero **Default** con un rango pequeño y luego **Genetic**, variando `AType/BType, APeriod/BPeriod, CombineMode, ReverseSignals, StopTicks/TargetTicks`. Usar *Optimization Fitness* solo si compila, y guardar parámetros de los mejores resultados sin declararlos finalistas. No variar `MaxDailyEntrySubmissions` durante la primera prueba: fijar 2.
7. Tras validación de compilación y configuración, ampliar catálogo a las **132 rutas**, gramática de múltiples condiciones y optimizador nativo con control de genotipos únicos, y después filtros G0/D0/D1/D2, ISV1/ISV2, cartera compartida y backtest final nativo.

## Qué se puede verificar desde GitHub y qué NO

Esta rama incluye una prueba **estática de contrato C#** para confirmar propiedades de NinjaScript, guardas históricas, comisiones, parámetros y ausencia de lectura externa de señales. **No compila NinjaScript contra los assemblies NinjaTrader 8** ni ejecuta Strategy Analyzer (no se dispone de NT8 Windows conectado). La compilación y la primera ejecución histórica en NinjaTrader requieren la instalación del usuario.

**Criterio de resultado:** No decir «10.000 estrategias ya corridas» ni «NinjaTrader backtest aprobado» por pasar el CI de GitHub. Los 13 gates del motor Python anterior permanecen como historial 0/13, y ahora se deberá construir una **matriz nueva específica NT8** con evidencia real de cada etapa. Mantener la regla de una cuenta compartida, máximo 1 NQ, y confirmación posterior del perfil comprado MFFU.
