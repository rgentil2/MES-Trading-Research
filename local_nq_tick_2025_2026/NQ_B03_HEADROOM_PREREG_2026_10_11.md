# NQ-B03 — Prerregistro de diagnóstico de ejecución (2026-10-11)

**Estado: ANTES DE NUEVOS RESULTADOS.** No es una hipótesis nueva de rentabilidad ni valida ejecución real.

**Pregunta:** ¿cuánto margen conserva T05-377 si la ejecución cuesta más que lo asumido? ¿El drawdown de T08 cambia si se procesan las fechas ET cronológicamente durante los rollovers?

**Evidencia previa:** T05-377, siete meses DEV oct-2025 a abr-2026, 115 trades, +USD6.220 base y +USD5.102,50 estrés. T08 reportó DD de envolvente Last $1.750 base y $1.825 estrés; la referencia histórica $2.000 de fondeo NO se ha verificado. T10 113/115 pares Bid/Ask frescos, dos excepciones febrero. B02 240/240 velas OHLCV iguales para un día.

**Riesgo de ingeniería descubierto antes del estudio:** `month_days` ordena archivos por nombre de contrato, lo que puede desordenar días durante el rollover; T08 podría haber trazado DD en una secuencia incorrecta. B03 ordenará explícitamente `sorted(month_days(...))` por fecha ET y documentará si el DD de referencia cambia, sin editar ni ocultar resultados T08.

**Experimento congelado:** mismos ticks Last y misma estrategia T05-377, mismas entradas y salidas T04 (NO modificarlas), mismos SL/TP/daily stop y exposición. Para los dos escenarios `baseline` y `stress_1p5_fee_2ticks_each_side`, aplicar un recargo fijo adverso a cada trade congelado de **0, 1, 2 o 4 ticks por lado** adicionales, equivalentes en 1 NQ a **$0, $10, $20 o $40 por round-trip**. Ocho resultados alternativos, sin seleccionar meses ni señales. El recargo cambia solo contabilidad hipotética de cada trade fijo y su equity en la envolvente Last, no recalcula cuándo se llenaría una orden o se activaría un stop.

**Medir:** exacta paridad de 115 trades y netos congelados con 0 recargo; neto, PF, DD adverso de envolvente Last, DD de cierres, concentración por mes y margen sobre $2.000 **ilustrativos** en cada caso. Un resultado bajo recargos NO es backtest broker, ni límite garantizado de pérdidas, ni validación OOS. El objetivo es detectar fragilidad del modelo de costes.

**Privacidad:** solo releases privados Last octubre 2025–abril 2026 con SHA256 verificado; nada de mayo–septiembre, ningún dato individual al repositorio público. Fallar si faltan fechas/datos, hay resultados distintos del T04 original o cambios en decisiones.

**Decisión:** reportar escenarios favorables y desfavorables completos; si DD 0 recargo difiere de T08 por ordenación, anotarlo como corrección de secuencia, no ajustar retrospectivamente stop. Próximo paso será B04 (robustez) y luego B05 (hipótesis causal nueva NQ), actualizando master/log.
