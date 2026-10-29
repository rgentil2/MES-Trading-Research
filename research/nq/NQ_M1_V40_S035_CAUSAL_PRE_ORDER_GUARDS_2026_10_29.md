# S0.35 — Corrección causal de órdenes: riesgo, stop y objetivos ANTES de enviar una entrada

**29-oct-2026.** La primera ejecución económica exploratoria S0.34 del AST 10K en NQ M1 real detectó **143 eventos POST_FILL_* sin protección o riesgo/modelado aceptable**, frente a solo 14 operaciones completamente modeladas, 2.060 decisiones sin datos. [Run histórico original](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/40896676531). No se deben tratar esas 143 entradas proxy como si fueran órdenes reales canceladas sin riesgo. Este defecto de secuenciación fue detectado antes de seleccionar finalistas.

## Corrección en el nuevo motor experimental

[Archivo `nq_m1_v39_ast_ist_exploratory_order_replay.py`](nq_m1_v39_ast_ist_exploratory_order_replay.py), versión de investigación S0.35:

- Al cerrar la vela de señal, calcular **antes de la orden** stop/protección, riesgo monetario y objetivo usando SOLO la información disponible en esa vela y un precio de referencia reproducible: para MARKET, close ± 2 ticks adversos; para LIMIT/STOP, el nivel solicitado. Orden con protección ausente, riesgo de referencia por encima de US$300 o nivel de objetivo no especificado se clasifica **PRE_ORDER_*** y no se simula ejecución.
- Si el próximo open o un gap empeora el riesgo *después de una orden autorizada*, clasificar **POST_FILL_*_UNMODELLED** y considerar incompleto cualquier PnL parcial correspondiente. No asumir que se pudo cancelar una orden que ya habría tocado su trigger ni dar un resultado de cartera completo.
- Mantener sin cambios el algoritmo histórico de SL-first, trade-through de target LIMIT, comisiones US$4.68 round trip, dos ticks slippage por lado, flat 11:29, max 2 operaciones por sesión, misma fuente y los mismos 12 AST y tres sesiones predeterminadas. Los parámetros de coste/límite siguen **provisionales** y no se afirma conformidad MFFU.
- Se preserva el módulo S0.26 estrictamente sintético; la implementación S0.35 modifica solo la investigación económica limitada. Cualquier diferencia con el primer replay se registra como corrección metodológica de bug, no como mejora económica ni búsqueda adaptativa.

[CI de corrección 40897125808 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40897125808): **381/381 pruebas**, 2 nuevas. Entre ellas rechazo PRE_ORDER de stop excesivo, referencia PIVOT sin semántica definida y chequeo independiente de que el fill futuro no puede autorizar retroactivamente un stop.

## Estado y límites

- **NO** se han backtesteado las 10.000 estrategias; sigue un piloto de 12 AST sobre solo tres sesiones.
- La versión previa sigue archivada con 143 posfill no modelados y no debe mezclarse su PnL con S0.35.
- Los resultados históricos tras la corrección deben confirmarse en la misma fuente ZIP SHA congelada, en el runner privado, y añadirse al maestro/bitácora con un nuevo artifact SHA.
- 13 gates pre-económicos siguen 0/13 verificados y ejecutabilidad real/NinjaTrader sin certificar; años 2023–26 sin leer, selección/portafolio todavía no habilitados.
