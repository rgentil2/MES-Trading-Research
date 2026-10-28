# NQ M1 — S0.26 simulador completo de ciclo de orden, solo datos artificiales

**Fecha:** 2026-10-28. **Universo:** NQ 1 contrato M1, velas cerradas 09:31–16:00 ET en RTH. **Scope técnico:** SIN abrir archivos históricos 2020–2022, NI ISV1 2023, ISV2 2024, 2025–26; ninguna estrategia real evaluada ni certificada.

## Implementación

El nuevo `nq_m1_v31_full_synthetic_lifecycle.py` conecta por primera vez señales M1 causales con todo el ciclo **únicamente sobre precios inventados internamente**:
```text
V2.6 AST 132 rutas -> señal LONG/SHORT/UNAVAILABLE
 -> orden MARKET/LIMIT/STOP
 -> espera de 1 a 30 velas o cancelación por expiración antes de 11:29
 -> comprobación inicial de distancia SL y cap de riesgo NQ de referencia
 -> posición única -> SL/TP/trailing/breakeven/cierre por barras
 -> cierre forzado 11:29 y registro sintético de coste/resultado
 -> posible siguiente señal si no superó dos entradas/día
```

Las 132 rutas matemáticas y sus predicados fueron integrados técnicamente en S0.25; **no** hay todavía certificación de equivalencia externa de las 132. Las funciones nuevas calculan SL `FIXED_POINTS`, `ATR`, `STRUCTURE` y `CHANDELIER`; TP `NONE`, `FIXED_POINTS`, `R_MULTIPLE`, `ATR` y `CAUSAL_LEVEL=VWAP`. Para `CAUSAL_LEVEL=PIVOT` o `PREVIOUS_COMPLETED_SESSION_LEVEL` **no hay referencia direccional ni banda exacta en el AST**: se declara `LEVEL_REFERENCE_NEEDS_FORMAL_DEFINITION` y no se atribuyen operaciones ficticias, en lugar de suponer un nivel ventajoso.

Los datos son creados internamente por `artificial_m1()` y el runner exige el objeto `Fixture` con semilla y hash de modificaciones de escenarios sintéticos. **No acepta** matrices OHLC externas ni carga archivos del repositorio, GitHub releases, broker, mercado o holdouts. Esto es deliberado para que un test artificial no sea presentado como backtest real.

## Conservadurismo y advertencias

- Señal cerrada en índice 4–116; próxima apertura de entrada hasta índice 117, flat en índice 118 = 11:29 ET; ventanas end-labeled sin tomar señales posteriores al cierre obligatorio.
- LIMIT necesita apertura marketable o **trade-through ≥1 tick**, no un toque exacto. El TP también se trata como orden LIMIT: el toque exacto sin avance ≥1 tick ni apertura marketable **no cuenta como TP ejecutado**, una precaución adicional al modelo S0.24. Si TP y SL se tocan en una sola vela, el **SL gana**.
- Si existe gap adverso cruzando SL, usa apertura peor más dos ticks adversos. No reconocer precio favorable extra por apertura por encima del objetivo TP.
- Si la entrada es pendiente LIMIT/STOP, no usar máximos/mínimos anteriores al llenado en la vela para acreditar TP favorable. SL adverso puede contabilizarse de forma conservadora, aunque el orden intraminuto siga desconocido.
- El stop solo se aprieta con **velas anteriores completadas**. Distinguir actualización de MARKET al cierre de la primera vela posterior a la entrada; pendientes requieren la siguiente vela completada posterior al instante de entrada, porque su propio máximo/mínimo pudo precederla.
- El coste base **ilustrativo** es US$4,68 comisión round trip y deslizamiento adverso de dos ticks de referencia para MARKET/STOP y salidas STOP/horario. **TP LIMIT se considera al nivel objetivo (sin mejora ni deslizamiento)** únicamente si atraviesa el nivel o abre marketable. Esta hipótesis exige estrés independiente de costes, no supone fill broker.
- El modelo de riesgo previo usa US$20/punto, 1 NQ, máximo ilustrativo US$300 por stop inicial + slippage salida + comisión, dos entradas diarias, pausa por PnL sintético cerrado -US$600; estas reglas **NO son el perfil oficial MFFU comprado ni sustituyen un portafolio compartido**. Bajo gap posterior el stop puede perder más que el cap. Un fill técnicamente detectado que se descarta por riesgo al observar la apertura siguiente es `MODEL_ENTRY_RISK_NON_EXECUTABLE`, NO se interpreta como cancelación ex-ante verdadera. Faltan política y señales combinadas del portafolio.

## Lo que NO está listo

- La simulación NO contiene datos históricos, ni evaluación económica de las 10.000 estructuras, ni clasificación por Profit Factor, drawdown o frecuencia: resultados monetarios de esta función están etiquetados `synthetic_net_usd` y proceden exclusivamente de los datos creados por la propia prueba.
- Faltan certificar todas las fórmulas matemáticas contra oráculos independientes; completar semántica exacta de niveles previos/pivots; verificar que la semántica del ATR y señales cruzadas entre sesiones coincide con las referencias deseadas; motor real de fuente M1 y validación independiente de reloj/rollover/fills; riesgos EOD/shared account; G0–D2, y aprobación formal.
- El hard stop previo de 13 puertas mantiene **0/13 `PASSED_VERIFIED`** y `EXECUTION_BLOCKED`. Es un motor técnico aislado **no utilizable para elegir ganadoras**.

## Evidencia

Primera ejecución sintética [40787295227 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40787295227), 318 tests, 15 nuevos: LONG/SHORT, expiración pendiente, dual-touch stop-first, cuatro tipos de stops, TP, break-even/trailing, límites diarios, timeout y flat 11:29. Revisión posterior agrega prueba de TP LIMIT a toque exacto y requiere trade-through 1 tick; consultar la ejecución posterior de CI para veredicto final de esta mejora.

La implementación es versionada y separada de V2.1, V2.6, el ledger congelado de 10.000 y el motor futuro de backtest real.
