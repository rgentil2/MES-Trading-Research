# S0.42 — Primera optimización genética nativa NQ M1 / 1.000 evaluaciones nominales

**Registro 2026-11-01.** El usuario confirmó que **NinjaTrader fusiona correctamente los contratos anteriores** en su instalación. Se acepta mantener las **39 sesiones marcadas REVIEW** para este primer ensayo técnico **sin falsificar barras ni declarar que todas corresponden a festivos**: 26 eventos de discontinuidad M1 se identificaron en la auditoría y deben conservarse en los informes de calidad. La comparación 735 completas/39 REVIEW coincide con el registro histórico; no afirmar equivalencia bar-a-bar certificada de merges sin artefactos del NT8.

## Evidencia real ya obtenida en la instalación del usuario

- **NQNativeM1DataAuditV1**: output histórico 2020-01-02 a 2022-12-30: `full390=735 partial=39 invalidOhlcOrGrid=0 missingMinuteGaps=26`. Auditor nativo **ejecutado realmente** en NinjaTrader Windows.
- **NQNativeGeneticLabV1**: primer backtest fijo de 2020-01-01 a 2022-12-31, instrumento visual `NQ DEC26` con merge histórico **confirmado por usuario**; entradas fijas AType=0 (SMA slope) APeriod=12; BType=7 (RSI band) BPeriod=14; CombineMode=AND; Reverse=0; StopTicks=20; TargetTicks=32; MaxDaily=2. Standard fill, Last/M1, slippage 2, `Fill limit orders on touch=false`, plantilla `NinjaTrader Brokerage...` con comisiones activadas.
- **Resultados de control observados**: 1.546 trades, neto **-US$43.554,96**, PF **0,64**, max DD cerrado **-US$44.380,44**, win rate **32,28%**, comisiones **US$8.904,96** = **US$5,76/trade RT**. Rechazo económico del genotipo base; esta prueba NO fue optimización, ni seleccionado ganadores, ni portafolio.
- **Precaución**: 39 sesiones REVIEW incluyen cierres/horarios reducidos y **algunas discontinuidades dentro de RTH**, así que no afirmar «todas fueron festivos»; por decisión del usuario se incluyen provisionalmente en la exploración inicial y se contrastarán al certificar finalistas.

## Configuración pre-registrada del primer ensayo genético

Strategy Analyzer: `Backtest type=Optimization`; `Strategy=NQNativeGeneticLabV1`; **Optimizer=Genetic**; **Optimize on=Max. net profit** (exploratorio, nunca filtro final); `Keep best # results=30`.

### Rangos de genes (Min / Max / Increment en Strategy Analyzer)

| Parameter | Min | Max | Increment | Criterio |
|---|---:|---:|---:|---|
| A type (0..9) | 0 | 9 | 1 | Todas las 10 primitivas disponibles |
| A period | 6 | 30 | 3 | 9 valores |
| B type (0..9) | 0 | 9 | 1 | Todas las 10 primitivas disponibles |
| B period | 6 | 30 | 3 | 9 valores |
| AND=0 OR=1 | 0 | 1 | 1 | Ambas estructuras |
| Reverse (0/1) | 0 | 1 | 1 | Ambas direcciones |
| Stop ticks | 12 | 50 | 2 | Provisional < cap $300 según chequeo de código |
| Target ticks (0=none) | 20 | 100 | 4 | 21 valores; NO target=0 en primera prueba |
| Max daily entry submissions | 2 | 2 | 1 | No optimizar el riesgo/actividad |

**Genetic:** `Generation size=50`, `Generations=20`, nominal **1.000 evaluaciones**, **no necesariamente 1.000 genotipos únicos**; `Crossover rate=80%`, `Mutation rate=20%`, `Minimum performance=0` (desactivar salida anticipada por threshold); restante por defecto (entre ellos Strength/Convergence/Reset/Stability) y documentar valor efectivo al ejecutar.

**Datos y fill** sin variar del backtest control: NQ con merge confirmado por usuario, Last, 1 Minute, Trading Hours template CME RTH verificada, start 2020-01-01 end 2022-12-31 (no 2023+), Break at EOD, include commission, misma plantilla NinjaTrader Brokerage, Standard (Fastest), fill limit orders on touch desactivado, slippage 2, Time In Force GTC, un contrato y máximo dos órdenes de entrada por día. Verificar en el resultado que las comisiones RT siguen alrededor de US$5,76 por trade si la plantilla no cambia.

## Protocolos para juzgar la salida, NO elegir ganadores por fitness

1. Guardar capturas de toda la sección **Optimization** y de los 9 rangos antes del Run, para reproducibilidad.
2. Guardar **Optimization Results** y parámetros de **los 30 mejores** sin afirmar que ya fueron 1.000 genotipos **únicos**; guardar un Backtest detallado de los 3–5 mejores.
3. Registrar por genotipo: AType, APeriod, BType, BPeriod, CombineMode, ReverseSignals, StopTicks, TargetTicks, MaxDailyEntrySubmissions, número trades, neto con comisión, PF, max DD cerrado, tasa de acierto, comportamiento por año 2020/2021/2022. Comparar contra **control negativo** anterior.
4. **Rechazar**, no promover, variantes que solo destaquen por beneficio neto histórico: luego requerimos PF>=1,25; >=150 trades; >=5 operaciones/mes (con definición reproducible), DD cerrado<=US$2.000, análisis de DD flotante y riesgo efectivo MFFU, estabilidad temporal y sensibilidad. La compuerta nativa `NQNativeResearchFitnessV1` codifica provisionalmente solo trades/PF/net/DD cerrado y podría aplastar la señal genética si todas las propuestas fallan; por ello en esta PRIMERA prueba usar **Max. net profit** para verificar exploración, y hacer screening independiente después.
5. No abrir ISV1 (2023) ni ISV2 (2024), y tampoco 2025/2026. No cambiar el modelo de Standard ni los costes al comparar genotipos en este experimento.
6. S0.42 es **optimización técnica de 10 tipos de señales y 2 condiciones**, NO búsqueda final de 10.000 AST únicas, 132 indicadores nativos, ni estrategia MFFU. Continuar ampliando gramática, indicadores, y optimizador propio tras el smoke real.

**Estado:** se ha documentado el ensayo; **no se ha ejecutado esta optimización desde GitHub**. El usuario ejecutará el Run en NinjaTrader Desktop y aportará los resultados de la grilla. Se puede detener la optimización si consume demasiada memoria; revisar el uso efectivo de recursos, no presumir duración.
