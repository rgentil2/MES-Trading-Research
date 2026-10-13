# Auditoría documental de riesgo/ejecución T05, T147 y T186 — 13-oct-2026

**Objetivo:** identificar con datos previamente procesados cuál es el obstáculo verificable para construir una estrategia compuesta T que pueda en el futuro estudiarse frente a referencia de cuenta US$50K. **No es un nuevo experimento ni un prerregistro ex ante de resultados.** No se consumen datos brutos; no se abren meses T mayo–sept2026 ni H 2025/26; sin nuevas fuentes ni ajustes.

## 1. T05-377: ventaja positiva, pero no robusta al recargo y a la secuencia Last

T05 congelado original: 115 trades y 135 sesiones elegibles oct2025–abr2026; 1 NQ; max 2 trades/día, SL16–48 ticks, TP2R, timeout300s, estrés slippage2 ticks/lado +fee7,50 RT, fills **solo simulación Last**.

| Prueba ya ejecutada | Neto USD | PF | Drawdown de envolvente Last USD | Criba exploratoria PF>=1,25 y DD<=2.000 |
|---|---:|---:|---:|---|
| Fuente original + estrés | +5.102,50 | 1,31826 | 1.797,50 | PASA solo estas dos columnas del modelo, no gate formal |
| Fuente original + estrés +$10RT | +3.952,50 | 1,23717 | 1.887,50 | **FALLA PF** |
| Fuente original + estrés +$20RT | +2.802,50 | 1,16195 | 1.977,50 | **FALLA PF**; margen DD solo $22,50 |
| Fuente original + estrés +$40RT | +502,50 | 1,02699 | 2.157,50 | **FALLA PF y DD** |
| Reversión secuencia mismo timestamp + estrés | +5.520,00 | 1,33429 | 2.462,50 | **FALLA DD** |
| Reversión mismo timestamp + estrés +$10RT | +4.340,00 | 1,25284 | 2.612,50 | **FALLA DD** |
| Orden descendente por precio mismo timestamp + estrés | +5.522,50 | 1,33394 | 2.090,00 | **FALLA DD** |

La referencia de $2.000 es un filtro ilustrativo de pérdida máxima nominal de 50K, **no una simulación de trailing EOD/intraday, broker, reglas de actividad ni límites diarios**. El PF 1,25 es umbral interno, no regla de My Funded Futures. Recargos monetarios son fixed-path y no recalculan decisiones previas por gate diario.

Bootstrap T05 por bloque móvil principal 5 sesiones: estrés IC90 media neta USD/sesión [+3,83,+71,02], pero bajo recargo $10 RT IC90 **[-4,63,+62,22]**, incluye cero; en TODOS los tamaños de bloques 3/5/10 con recargo $10 el IC90 cruza cero. Selección previa impide llamar esto confirmación.

**Dictamen T05:** benchmark prioritario por 115 trades y PnL, pero NO financiar ni aprobar como 1NQ en cuenta 50K; falta edge robusto ante costes y reconstrucción causal de la secuencia/fills. Riesgo observado Last no es límite superior de riesgo ejecutable.

## 2. T147: posible mecanismo diferente; baja muestra y simulador distinto

T147: reversión a barrida de extremo de contexto previo 4181-print, gatillo E377 10:00–10:15 ET; 20 trades/7 meses (~2,86/mes), base **+$642,25**, PF base **1,4992**, DD **cerrado** $567; fricción1,5x **+$433**, y suplemento fijo +$10/RT **+$442,25** (escenarios separados). Q4 2025 -$567, ene–abr2026 +$1.209,25. Bootstrap L5 IC90 por día **[-3,68,+13,29]**, qBH36 1,00; 0 aprobados en cohorte.

**No sumar su beneficio con T05**: T147 tiene stops físicos y TP1,25R, timeout15m, tarifas, sizing y motor E377 diferentes del legacy 5s+377 T05. DD cerrado T147 no equivale a DD Last T05. No se verificó un router T05+T147.

**Punto de decisión técnica:** antes de autorizar *cualquier* backtest conjunto, documentar la conciliación de entradas timestamp, motor único de riesgo/stop, contabilidad de costes y posición compartida. Probar paridad histórica de los padres; si no se puede, etiquetar NOT_ESTIMABLE, sin estimar ganancia sumada.

## 3. T186: router existente, NO económico y no candidato a rescate

T186 sola N70, neto estrés **-$970**. Con prioridad T05: 50 T186 ejecutadas, las 115 T05 retenidas, incremento +$780 estrés y +$280 después de recargo $10RT; PnL total del router original estrés **$5.882,50** (5.102,50+780), pero **PF tras +$10RT 1,20198<1,25** y **DD Last estrés $2.130>2.000**. Resultado formal del screen: FAIL. Observación de complementariedad post hoc, no seleccionar ventanas o variantes para salvar.

## 4. Orden de trabajo justificado

1. **Barrera inmediata:** calidad de datos/fill y fragilidad de T05 bajo adversidad. Ya documentada suficientemente para NO pasar al fondeo; una nueva corrida de los mismos supuestos DEV no crearía robustez independiente.
2. **Siguiente pregunta diferente:** ¿T147 puede mejorar T05 sin reemplazar operaciones mejores, con 1 cuenta/riesgo, cuando sus entradas se armonizan físicamente? Registrar un motor común causal **antes de cualquier recomputación monetaria**; si no, rechazar comparación. Dado el N20 y selección retrospectiva, incluso PnL positivo sería exploratorio únicamente.
3. **Evitar mejoras cosméticas:** T186 ya mostró que marginal+280 no salva PF/DD; no volver a retocar.
4. **Los routers H NO se mezclan con T** en la misma curva (2020–24 minuto versus 2025–26 tick; H holdout 2025/26); H69 es referencia de familia y H74/H77 contrastes de selección, no 3 fuentes de retorno.
5. **Eventual 50K y tamaño contrato:** no probar 1MNQ multiplicando linealmente PnL/DD de 1NQ: valor tick, fee por contrato, slippage, tick fills y filtros de tamaño pueden variar. Cuando se explore MNQ, establecer motor costos y reglas primero; no usar operaciones sin hipótesis solo para sortear inactividad.

**Resultado de esta auditoría:** no se identificó ninguna cartera nueva que pase gates. **No se hizo backtest nuevo.** Prioridad metodológica = *unificar motor de ejecución y evaluar complementariedad, no generar más variaciones de T05 sobre la misma muestra*.

**Archivos auditados:** [B03 T05 coste/DD](../../local_nq_tick_2025_2026/NQ_B03_T05_EXECUTION_HEADROOM_RESULTS_2026_10_11.md), [B05G orden timestamp](../../local_nq_tick_2025_2026/NQ_B05G_LAST_TIMESTAMP_SENSITIVITY_RESULTS_2026_10_11.md), [B05K bootstrap](NQ_B05K_T05_DAILY_BLOCK_BOOTSTRAP_RESULTS_2026_10_11.md), [T147 D1](NQ_T133_T168_FULL36_ECONOMIC_D1_RESULTS_2026_10_12.md), [T05/T147 SHADOW](NQ_D2_SHADOW_T147_VS_T05_BASELINE_COMPARISON_2026_10_12.md), [T186 routers](NQ_T169_T188_MONETARY_V3_20_RESULTS_2026_10_13.md).
