# Cohorte NQ T97–T132 — nuevo embudo por SEIS BLOQUES de hipótesis de decisión, G0/D0

**Prerregistro ANTES de la evaluación**, 12-oct-2026. [Registro JSON inmutable de 36 ID/preguntas](NQ_T97_T132_SIX_BLOCKS_D0_PREREG_2026_10_12.json) commit `74042210540c73134fa4d00ae65fb9bb504955c0`. El usuario exige que pasen **COHORTES completas** G0→D0→D1→D2; no optimizar T05/T75 ni repetir la familia T59–T96 que [no pasó BH38](NQ_T59_T96_38_MEMBER_WHOLE_COHORT_D1_RESULTS_2026_10_12.md).

## Pregunta económica/direccional, antes de mirar resultados

**Hipótesis de arquitectura:** ¿Podemos distinguir CONTEXTOS en los que el impulso intrasesión NQ en 377 prints es más apto para continuación inmediata, usando barras 233 (entrada corta), 4181 (macro) y niveles efectivos previos, en vez de 36 variantes de T75? La diferencia prevista en una futura D1 será un **markout firmado** de precio, no P&L ni fills. D0 es **SOLO viabilidad causal**, por lo tanto no se inspecciona ningún resultado futuro.

- **Fuente:** los mismos 7 archivos Last DEV 2025-10…2026-04; 140 sesiones fuente, 135 READY, checksum verificable. Last 08:00–12:00 ET, sin datos nuevos, ni barras nuevas de 5 segundos, ni OOS. Sin agresor Bid/Ask verificado. Grupos de timestamp completos e indivisibles.
- **Momento único de decisión:** fin de la primera barra E completamente formada de 377 prints con `10:00≤E.end<10:15 ET`; D377 inmediatamente previa. Bars de 233 y 4181 utilizadas únicamente si **end_timestamp≤E.end**; en comparaciones con partes de E utilizar E.end completo, nunca un fragmento posterior. Cada grupo atómico igual timestamp indivisible.
- **Side de referencia:** `sign(VWAP_qty(E377) − VWAP_qty(D377))`; side=0 ⇒ NOT_EVALUABLE para hipótesis de lado, sin inventar dirección. Para `REGIMEN` (T121–T126), comparación de magnitudes causales de actividad, sin usar retorno futuro.
- **Clasificación congelada:** VOTO=sign(side×señal causal de precio). CONSENSO=CASE solo si **ambas** fuentes de dirección coinciden con el side, CONTROL solo si **ambas** lo contradicen; desacuerdo o cero ⇒ OTHER. REGIMEN=CASE cuando actividad/rango aumentan versus referencia anterior, CONTROL si se reducen, OTHER igual. Contexto necesario ausente ⇒ NOT_EVALUABLE. No modificar umbrales para incrementar N: se comparan signos y magnitudes, no optimizan Fibonacci ni umbrales retrospectivos.
- **B12 T97–T102:** direccionalidad de la última 233 completada, slope entre 2 y 3 VWAP 233, cuerpo de grupos atómicos, cierre-vwap, cambio de máximos y mínimos.
- **B13 T103–T108:** contexto 4181 completo: pendiente de VWAP de las dos últimas barras 4181, cuerpo, diferencia VWAP 4181/233, migración de máximo, mínimo y cierre respecto VWAP 4181 previo.
- **B14 T109–T114:** barreras: distancia con signo del cierre atómico de E al **extremo del lado del impulso** del PM, primer RTH 09:30–10:00, D/C377, tres previas 233, previa 4181, y VWAP premercado. CASE está del lado del rompimiento, CONTROL sin alcanzar barrera, misma condición antes del futuro. Los controles constituyen referencia mecánica, NO operación invertida.
- **B15 T115–T120:** localización/retest: distancia del cierre de última 233 frente VWAP D377 y VWAP 4181; cierre E377 frente centros de rango PM, apertura 09:30–10:00, tres 233 anteriores y último 4181.
- **B16 T121–T126:** régimen de variación de rango, cantidad por tiempo, densidad de timestamps, rango 4181, rango 233 normalizado respecto a macro 4181 y velocidad E377 frente D377.
- **B17 T127–T132:** **interacciones deductivas de dos padres distintos:** micro233 con cuerpo PM, micro233 con apertura RTH, micro233 con pendiente macro4181, macro4181 con PM, macro4181 con apertura, micro233 con D−C377. Solo consenso doble vs oposición doble. 6 preguntas de confluencia sin rescatar T75.
- En ausencia de **dos barras 4181 completas** (o ventana necesaria), las filas de ese bloque son NOT_EVALUABLE; se contabilizan en 135 READY, jamás se rellenan con una ventana parcial. Nunca usar 10946 si no es necesario: usuario prefiere no descargar nuevos ticks y no sobreajustar longitudes.

## Gate de cohorte

Todos los 36 ID T97…T132 deben obtener CASE/CONTROL/OTHER/NOT_EVALUABLE y pairwise Jaccard CASE. `TESTABLE` si N CASE≥15 y N CONTROL≥15; casi duplicados Jaccard≥0,85 NO cuentan dos veces para amplitud. Si **≥20 distintas TESTABLE**, y solo entonces, congelar D1 en familia **k36 todos los miembros** con signo/endpoint antes de mirar futuro; si no, formular **OTROS BLOQUES** sin retocar T97–132. D0 no mide delta, IC90/p/q, USD, N trades, PF, DD, Holm ni ROI. D1 predictiva no autoriza D2 económica si no hay dos mecanismos ejecutables y costos realistas.

### Calidad

Las medidas de 233 y 4181 son por número de prints y nunca dividen un timestamp. Las ventanas premkt y apertura se evalúan completas [08:30,09:30), [09:30,10:00), y solo son causales si el fin E ocurre después de 10:00 ET. No interpretar grupos de Last como agresores ni precio VWAP como broker fill. **Una hipótesis D0 viable NO es una ventaja monetaria**, y repetir datos DEV implica selección exploratoria. El archivo de configuración se congeló antes de la primera evaluación empírica de este bloque.
