# NQ M1 — Decisión de fuente y protocolo conservador OHLC (S0.24)

**Fecha 2026-10-28. Decisión expresa del usuario:** «Por ahora quedémonos con los datos de M1». Se mantiene como fuente única de búsqueda económica futura **NQ OHLCV de un minuto, IST 2020–2022, un contrato**. No se exige descargar ticks IST de 2020–2022 para la fase de descubrimiento. Tampoco se permitirá fingir que los fills OHLC son ejecutados realmente.

## Alcance y límites irrevocables por ahora

- **NQ** (no usar MNQ para validar supuesta PnL/estrategias), 1 contrato, barras Minute Last fuente original con identidad por contrato; OHLCV sin back-adjust; **jueves ocho días antes del tercer viernes** para escoger rollover trimestral, tal como congeló el usuario.
- Horario America/New_York con DST, **RTH 09:30–16:00**; señales únicamente después de vela cerrada, intervalo de búsqueda 09:35–11:30 siguiendo especificaciones anteriores, cierre forzoso **11:29 ET**. La integración debe resolver de manera consistente el límite de última entrada para no colisionar con 11:29.
- Fuente autorizada IST **2020, 2021, 2022** con 735 sesiones RTH completas ya contrastadas; 39 parciales excluidas según manifiesto congelado. **ISV1 2023 e ISV2 2024 siguen reservados; 2025–2026 completamente sellados.**
- La falta de ticks **ya no bloquea como requisito de adquisición** nuestra investigación económica M1, pero la auditoría OHLC, las fórmulas de indicadores, la cuenta MFFU exacta y los 13 gates sí deben estar terminados antes de autorizar el backtest.

## Hipótesis de ejecución M1 para someter a pruebas independientes

[Referencia sintética ejecutable](nq_m1_v29_ohlc_conservative_protocol.py) define un **borrador** versionado, sin leer precios históricos ni modificar V2.1:

| Evento | Regla provisional y pesimista |
|---|---|
| Entrada MARKET | siguiente OPEN conocido tras la señal completada, con slippage adverso de 2 ticks por lado (base revisable) |
| Entrada STOP | si cruza el trigger se supone entrada al peor entre precio trigger y apertura de gap, más slippage adverso |
| Entrada LIMIT | un **simple toque exacto no equivale a fill**; para candidato de fill se exige atravesar el límite 1 tick o ser ejecutable en apertura; aun así la cola real no se conoce |
| Dos barreras SL y TP en misma vela | **SL siempre primero** (peor hipótesis); registrar vela ambigua, no inferir secuencia real |
| SL con gap adverso | salida en la apertura del gap adverso, con slippage extra en contra; **no** asumir precio stop |
| TP con gap favorable | reconocimiento máximo al nivel TP, **sin mejora favorable gratuita** |
| Orden pendiente con TP en su vela de entrada | TP favorable **suprimido** por secuencia desconocida; SL posible se imputa conservadoramente |
| Break-even y trailing | actualizar solo con la barra PREVIA completada, no con máximos/mínimos aún desconocidos del bar activo |
| STOP / LIMIT pendientes | caducidad de orden por barras explícitas; jamás adjudicar fills por información posterior a la expiración |
| Costes | referencia heredada **US$4,68 round trip**, 2 ticks adversos por lado en caso base y pruebas extra **1,5x** antes de certificar D1; verificar tarifas reales antes de decidir |
| Riesgo | NQ punto US$20, tick 0,25 = US$5; una única cuenta MFFU 50K bajo perfil exacto aún pendiente de confirmar |
| Sesiones sin evidencia suficiente | marcar unavailable o escenario conservador, nunca imputar TP optimista, jamás alterar el horario/rollover para sacar más trades |

**Advertencia clave:** los extremos high/low de una vela no indican quién llegó primero ni la prioridad del order book. El conjunto de reglas anteriores estima un escenario de investigación, NO demuestra la secuencia real, queue priority, tamaño ejecutado o garantías de stops. Los resultados futuros deberán etiquetarse `ESTIMATED_M1_CONSERVATIVE_OHLC` y acompañarse de porcentaje de velas ambiguas y estrés de costes.

## Divergencia descubierta y trabajo pendiente

El motor V2.1 `nq_m1_v2_orders._pending_fill` acepta para LIMIT un toque exacto. **El protocolo nuevo NO lo acepta**. La prueba técnica documenta la divergencia; antes de abrir D1 hay que integrar la decisión en el simulador definitivo, probar MARKET/LIMIT/STOP completos, expiración y riesgo conjunto, además de corregir cualquier regla con lookahead. No cambiar silenciosamente la cohorte original ni el código congelado.

El protocolo M1 sustituye la dependencia de **descargar ticks** para descubrimiento, **no la necesidad de evidencia auditable**: los restantes controles de procedencia, paridad de fórmulas, tiempo, M1 bounds, multiplicidad, adaptadores G0/D0/D1/D2, cuenta MFFU y aprobación final por SHA siguen activos. Matriz actual: **0/13 PASSED_VERIFIED / EXECUTION_BLOCKED**. El usuario ha escogido el **tipo de datos**, no ha certificado por sí solo la simulación.

## Evidencia ejecutada

[CI S0.24](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40784552670) terminó SUCCESS con **286 pruebas sintéticas y de regresión PASS**, incluidas 15 pruebas nuevas con velas artificiales de gaps, stops, targets, limits y validación fail-closed; no cargó precios 2020–2022, no produjo trades/PnL ni abrió ISV/holdouts. Este resultado valida el código aislado y los supuestos verificables; **no certifica el motor para operar o seleccionar estrategias**.
