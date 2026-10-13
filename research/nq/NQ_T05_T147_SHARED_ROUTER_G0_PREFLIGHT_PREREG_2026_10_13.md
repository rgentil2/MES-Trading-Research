# NQ T05-377 + T147 — G0 PREFLIGHT de compatibilidad ANTES de router monetario

**Congelación prospectiva:** 2026-10-13, ANTES de cualquier ejecución conjunta nueva T05+T147. Se conservan las dos estrategias originales y sus simuladores; el presente G0 no diseña una tercera alpha ni selecciona parámetros a partir de beneficios. **Estado:** PREREGISTRADO, resultados aún NO observados.

## Pregunta falsable y propósito

¿Podemos reproducir en un único lector causal los resultados monetarios INDIVIDUALES de T05 y T147 y reconstruir exposición temporal sin ambigüedades de Last, **antes** de diseñar un router de una cuenta compartida? Un Sí técnico habilita exclusivamente el siguiente diseño metodológico; **no es rentabilidad incremental** ni D2 oficial. Un No documentará el impedimento y no supondrá una entrada/salida rentable.

## Universo, seguridades y fuente

- Siete meses DEV Last existentes **2025-10…2026-04** (desde 15-oct-2025); deben ser exactamente **140 sesiones fuente, 135 READY**; solo la fuente ya subida a releases privados con SHA256. Antes de intentar IO, denegar cualquier mes ajeno a la lista fija, incluidos mayo–sept2026. H2025–26 sellado. NO comprar ni descargar nueva información; uso de los siete archivos licenciados **preexistentes** ya almacenados.
- Reader original `source_events`; T05 congelada `frozen_t05` que hereda barras de 5s legacy + 377 registros; T147 `T133_T152_EXECUTABLE_D0_PREREG` regla/prioridad `reject_macro4181_extreme`, señal primera E377 completa [10:00,10:15) ET, clase CASE, stop físico, TP1,25R, máximo15min.
- Costes congelados propios: T05 estrés NQ 2 ticks adversos por lado, fee $7,50 RT; T147 D1 2 ticks adversos/lado, NQ fee $4 RT o MNQ fee $1,50 RT, 1 contrato elegido ex ante por riesgo <=$250. **NO declarar costes armonizados por repetir un recargo común**.
- No modificar T05 legacy, ni D1 de las 36, ni las fechas, ni reinterpretar D1 `entry_group_ambiguous` como fill verificable. Todos los resultados son ficticios bajo Last, no cotizaciones Bid/Ask negociables.

## Comprobaciones G0 congeladas, por orden; abortar si alguna paridad falla

1. **Cobertura/estanquidad:** solo meses permitidos, 140 fuente y 135 READY; solo outputs agregados; ninguna fila Last, fecha de trade, señal puntual, precio individual ni vector diario pueden salir del runner.
2. **Paridad T05:** exactamente **115 operaciones**, **+$5.102,50** neto estrés con mismos 7 meses; la ruta de DD original Last $1.797,50 NO se recalcula aquí ni se reemplaza por DD cerrado. Si no coincide N y PnL, fallo G0.
3. **Paridad T147:** exactamente **20 operaciones modeladas** y **+$642,25** base D1, calculadas mediante las mismas funciones `classify_day/prepare_context/stop_and_side/first_future_groups/model_one`; más el conteo agregado de CASE, clasificación NQ/MNQ, entradas `entry_group_ambiguous`, salidas `HORIZON_NOT_FULLY_OBSERVED`, y casos sin un resultado monetario.
4. **Compatibilidad de exposición:** si alguna T147 ejecutada tiene `entry_group_ambiguous=True`, la exposición temporal en ese grupo es indeterminable: **G0=BLOCKED_SHARED_ROUTER** aunque se conserve su beneficio D1 a efectos de paridad. Nunca sumar o simularla como una secuencia segura. Si no se puede recuperar inicio y fin de operación de cada T147 sin modificar los resultados D1, mantener bloqueo.
5. **Contraste de colisión informativo:** contar días que T05 y T147 generan señales, sin interpretar coocurrencia como independencia/diversificación; no hacer aún arbitraje ni medir delta PnL de cartera.
6. **Comparabilidad económica:** T05 es siempre 1NQ, mientras T147 puede ser NQ/MNQ; una cartera debe exponer riesgo y fricción por contrato, contabilizar posición exclusiva y abandonar si no puede reconciliar la trayectoria de cada padre. Este G0 no adapta automáticamente todas las operaciones a MNQ ni reduce stops o mueve timestamps.

## Resultado permitido y barreras

- Salida pública SOLO `source_sessions,eligible_sessions,T05_N,T05_net_stress,T147_N,T147_net_base,T147_case_count,T147_ambiguous_entry_groups,T147_instrument_counts,days_both_signals,QC_status`. Si la paridad falla: error FAIL CLOSED, **ningún informe de PnL de cartera**.
- Si paridad y cero ambigüedades: estado `G0_PARENT_PARITY_OK_EXPOSURE_REPLAY_REQUIRED` (todavía sin router).
- Si paridad y ambigüedades: `G0_PARENT_PARITY_OK_SHARED_ROUTER_BLOCKED`; pasar solo a estudio de ejecución que resuelva causalmente ambigüedades, nunca elegir un movimiento dentro del mismo timestamp para fabricar un resultado.
- Cualquier proceso posterior deberá ser **otro prerregistro** con decisiones de prioridad por timestamp (empate T05), una posición, máximo dos nuevas entradas/día, stop diario por PnL cerrado −$600, riesgo compartido, entradas/salidas, reducción de capacidad y costes por instrumento; escenarios con 1NQ T05 original, no 8 PnL sumados.
- Si alguno de los padres no puede reconstruirse bajo un motor que respete contratos originalmente congelados, N/D y no inversión. OOS T y H siguen sellados, ninguna compra de fondeo.

## Controles de calidad obligatorios

- Tests unitarios sintéticos independientes del mercado, validación whitelist antes de filesystem, fail-closed ante entrada ambigua, conteo y no filtración. Ejecutar tests ANTES del acceso a los releases.
- Registrar el workflow real, estado de ejecución, recuentos e incertidumbre en [NQ_PROJECT_MASTER.md](../../NQ_PROJECT_MASTER.md) y [NQ_RESEARCH_LOG.md](../../NQ_RESEARCH_LOG.md). No declarar éxito solo por programar el workflow.
- **No cambiar umbrales de aprobación tras observar resultados de este preflight.**

Fuentes de padres: [comparación T05/T147 existente](NQ_D2_SHADOW_T147_VS_T05_BASELINE_COMPARISON_2026_10_12.md) · [T147 resultados congelados](NQ_T133_T168_FULL36_ECONOMIC_D1_RESULTS_2026_10_12.md) · [T05 orden y costes](NQ_T05_T147_T186_RISK_FEASIBILITY_AUDIT_2026_10_13.md).
