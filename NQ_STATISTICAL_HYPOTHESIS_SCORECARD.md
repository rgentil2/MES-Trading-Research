# NQ — Tabla estadística de hipótesis (Gate 1, q-BH e IC90)

**Última revisión: 11 de octubre de 2026; añadido diagnóstico estadístico T de siete meses, ejecutado 12-oct UTC.** Fuente: [Gate exploratorio original](research/es/ES_STAGE_GATES_EXPLORATORY_AMENDMENT_2026_10_09.md), [confirmatorio original](research/es/ES_STAGE_GATES.md), [gobernanza Holm](research/RESEARCH_CONTROLS_POLICY.md). Evaluación automatizada [código](research/nq/nq_gate1_statistical_scorecard.py) · [GitHub Action 38198391656 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38198391656) (6 pruebas PASS; resumen estadístico reproducible).

**Gate 1 prospectivo:** N>150 eventos elegibles independientes; efecto medio neto favorable; intervalo bilateral **IC90** en el lado preregistrado (>0 si la hipótesis es positiva); **q Benjamini–Hochberg ≤0,10 sobre los miembros completos de la familia**; ≥3/5 años positivos. Todo obligatorio. Holm con α_k=0,05/[k(k+1)] es confirmación separada, no reemplaza q ni las reservas OOS. Este Gate 1 es exploratorio: PASS no permitiría fondeo. Los preregistros antiguos más estrictos permanecen intactos.

## H67–H78: MNQ simulado con datos NQ minuto 2020–2024 (NO ticks T)

| Hipótesis | Pregunta | N | Promedio neto/trade USD | IC90 USD/trade | q BH | Años + | PF | P&L USD | ¿Gate 1? |
|---|---|---:|---:|---|---:|---:|---:|---:|---|
| NQ-H67 | ¿H09 o consenso H55+H56 agrega valor? | 239 | 9.23 | [0.71, 17.74] | 0.1152 | 4/5 | 1.295 | 2205.18 | **NO CUMPLE** |
| NQ-H68 | ¿H09 o H55 sin H56 funciona mejor? | 348 | 5.36 | [-1.47, 12.18] | 0.1585 | 4/5 | 1.164 | 1863.76 | **NO CUMPLE** |
| NQ-H69 | ¿H09 o H56 mejora la cartera base? | 262 | 10.32 | [2.15, 18.48] | 0.1152 | 4/5 | 1.335 | 2704.44 | **NO CUMPLE** |
| NQ-H70 | ¿Añadir H29 aporta rentabilidad? | 279 | 5.84 | [-1.65, 13.60] | 0.1585 | 4/5 | 1.179 | 1628.48 | **NO CUMPLE** |
| NQ-H71 | ¿Agregar ruptura tardía H54 genera ventaja? | 1051 | -1.83 | [-5.62, 2.01] | 0.8687 | 3/5 | 0.947 | -1923.88 | **NO CUMPLE** |
| NQ-H72 | ¿El router según volatilidad mejora retornos? | 582 | -3.27 | [-8.11, 1.57] | 0.8687 | 3/5 | 0.911 | -1904.66 | **NO CUMPLE** |
| NQ-H73 | ¿Volatilidad alta H09/baja H56 mejora H69? | 139 | 8.20 | [-3.20, 19.71] | 0.1567 | 4/5 | 1.252 | 1140.18 | **NO CUMPLE** |
| NQ-H74 | ¿Volatilidad baja H09/alta H56 mejora H69? | 132 | 12.56 | [1.24, 23.89] | 0.1149 | 5/5 | 1.438 | 1657.84 | **NO CUMPLE** |
| NQ-H75 | ¿Premercado contraído H09/expandido H56 mejora H69? | 165 | 7.26 | [-3.03, 17.83] | 0.1567 | 4/5 | 1.225 | 1197.30 | **NO CUMPLE** |
| NQ-H76 | ¿Premercado expandido H09/contraído H56 mejora H69? | 92 | 11.86 | [-0.95, 24.75] | 0.1214 | 3/5 | 1.417 | 1091.04 | **NO CUMPLE** |
| NQ-H77 | ¿Alineación gap H09/oposición H56 mejora H69? | 140 | 17.04 | [5.72, 28.60] | 0.0468 | 4/5 | 1.632 | 2385.30 | **NO CUMPLE** |
| NQ-H78 | ¿Oposición gap H09/alineación H56 mejora H69? | 129 | 3.32 | [-8.27, 15.18] | 0.3249 | 3/5 | 1.096 | 427.98 | **NO CUMPLE** |

**Resultado: 0/12 cumplen Gate 1.** H69 tiene IC90 favorable pero q=0,1152; H77 tiene IC90 favorable y q=0,0468, pero N=140 (inferior a 151). La auditoría de Holm sobre los p bilaterales de las familias 6 y 7 tampoco arroja confirmados. Se conserva el detalle de cada puerta y p-values en el artefacto del Action.

## Adaptación T verificable con la muestra actual (135 sesiones / 7 meses)

**Regla adicional, no reemplazo Gate H:** [Política estadística T siete meses](research/nq/NQ_TICK_SEVEN_MONTH_STATISTICAL_POLICY_2026_10_11.md), [resultado con IC90 mensual, signo y LOMO](research/nq/NQ_TICK_SEVEN_MONTH_STATISTICAL_RESULTS_2026_10_11.md), [Action 38200366148 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38200366148) y [código/test 6 PASS](research/nq/nq_tick_seven_month_diagnostic.py). Reutiliza SOLO el safe summary T05/H02 ya guardado, sin reabrir archivos Last, sin nuevos datos ni OOS.

**IMPORTANTE:** `N_sessions=135` vs `N_trades` y **solo siete unidades de inferencia MENSUAL disponibles en el artifact**. Estos son intervalos t-Student 90% de la **MEDIA USD/MES** sobre 7 meses, no IC90 de efecto por trade o efecto diario por semanas. Los meses consecutivos quizá no son independientes. No reportar q BH/Holm ni declaración de "pasa Gate1" derivada de estos IC mensuales.

| Hipótesis/contrafactual | Pregunta | N trades | Meses con P&L +/7 | Neto estrés USD | IC90 **media mensual** USD/mes | p de signo mensual unilateral* | q BH | ¿Cumple estadísticamente? |
|---|---|---:|---:|---:|---|---:|---|---|
| **T05-377** | ¿La reversión T05 aporta beneficio mensual neto constante? | 115 | **6/7** | +5.102,50 | **[+98,03, +1.359,83]** | **0,0625** | N/D | **NO EVALUABLE formalmente**, solo favorable descriptivamente |
| **B05H-02** | ¿La reversión VWAP genera ventaja con 377 prints? | 75 | 2/7 | −1.427,50 | [−576,31, +168,45] | 0,9375 | N/D | **NO EVALUABLE formalmente**, descartada económicamente |
| **Router T05+H02** | ¿Compartir ambas señales aumenta el neto en la cuenta? | 166 | 6/7 | +2.195,00 | [−221,53, +848,67] | 0,0625 | N/D | **NO EVALUABLE formalmente**, peor que T05 sola |
| **Δ Router−T05** | ¿Agregar H02 crea P&L incremental en mismas fechas? | Emparejado 7 meses | **0/7** | **−2.907,50** | **[−777,42, −53,29]** | **1,0000** para mejora positiva | N/D | **NO CUMPLE económicamente**; inferencia formal pendiente |

* El p binomial exacto supone siete meses con signos independientes y equiprobables; es un **diagnóstico posterior de estrategias YA probadas**, no q BH ni una prueba confirmatoria. Para T05, incluso el IC90 positivo de media mensual **no** aprueba simulación de fondeo: bajo estrés+$10 RT PF=1,23717. Si se omite cualquier mes, ΔRouter−T05 sigue negativo: neto LOMO de 6 meses entre **−US$2.895 y −US$1.442,50**.

**Precaución:** octubre-2025 inicia a mitad de mes (15-oct) mientras otras observaciones son meses completos; los siete P&L mensuales no tienen exactamente la misma exposición. El IC90 en USD/mes es solo descriptivo y debe sustituirse para inferencia por estadísticas sobre las 135 sesiones elegibles, incluidos ceros.

**Siguiente nivel pendiente:** a partir de **todas** las 135 sesiones con P&L diario **incluyendo ceros**, estimar IC90/p exploratorio de bloques móviles **5 sesiones con 10.000 bootstrap**, sensibilidad 3/10, unidad **USD/día**, intervalos de incremento diario router−padre emparejado, LOMO y precisión/poder. q BH solo si la familia **completa** y los p están definidos *antes de outcomes*, Holm sigue siendo requisito separado. No inventar N independiente mínimo de 75, 100 o 115 trades para promover estrategias. El programa H de cinco años y su propio Gate 1 no se tocan.

## B05K ejecutado — T05 con 135 retornos diarios y estadística de dependencia temporal

[Prerregistro B05K](research/nq/NQ_B05K_T05_DAILY_BLOCK_BOOTSTRAP_PREREG_2026_10_11.md) · [informe completo y sensitivity L=3/5/10](research/nq/NQ_B05K_T05_DAILY_BLOCK_BOOTSTRAP_RESULTS_2026_10_11.md) · [Action 38201169890 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38201169890) con **6 tests PASS**, ningún tick nuevo, datos T/H reservados sin abrir. **135 sesiones elegibles, 77 días con trade, 115 trades, 29 semanas calendario**, N efectivo independiente **N/D**. Reconciliación T05 original EXACTA +$5102,50 estrés /+$3952,50 estrés+$10 RT fijo.

| Hipótesis/escenario | Pregunta | N sesiones / N trades | N activos | Media USD/sesión | IC90 bootstrap L5 USD/sesión | IC90 sensibilidad L3 y L10 USD/sesión | p unilateral exploratorio L5* | q BH / Holm | ¿Cumple estadísticamente? |
|---|---|---|---:|---:|---|---|---:|---|---|
| **T05-377, estrés** | ¿La esperanza neta diaria permanece positiva con costes de estrés? | 135 /115 | 77 | +37,80 | **[+3,83,+71,02]** | L3 **[−0,62,+74,17]**; L10 [+7,09,+67,93] | **0,0293** | **N/D** | **NO confirmado**; IC90 L3 incluye 0, prueba postselección |
| **T05-377, estrés+$10 RT** | ¿Resiste US$10 RT adicionales sobre la misma trayectoria? | 135 /115 | 77 | +29,28 | **[−4,63,+62,22]** | L3 [−9,08,+65,69]; L10 [−1,33,+59,48] | **0,0692** | **N/D** | **NO CUMPLE robustez de precisión** (todos IC90 incluyen 0) |

* p bootstrap centrado con B=10.000 y bloques móviles no circulares de **5 sesiones**; sensibilidad 3/10 preregistrada. **NO es un p válido de selección adaptativa ni q de Benjamini–Hochberg**, y no abre confirmación. 38 días de P&L positivos, 39 negativos, 58 cero; 6/7 meses positivos; LOMO de seis meses mantiene neto estrés entre +US$3530 y +US$5930. El cost extra no recalcula decisiones de riesgo ni stops. Con +$10RT el PF congelado T05 **1,23717 <1,25**. Bajo perturbación de orden de mismo timestamp, DD Last llegó a $2462,50 (umbral $2000 meramente orientativo, no firma verificada). **T05 sigue CANDIDATA EXPLORATORIA, no cumple aprobacion de estrategia, fondeo ni Gate1 confirmatorio.**

**El contraste principal aquí es de MEDIA USD/SESIÓN con ceros**, no de USD/mes ni USD/trade. No inventar N efectivo ni años 3/5. El programa histórico H y Holm original se conservan; el resto del panel de T sigue con IC90/q N/D hasta ejecutar el análisis correspondiente con fuente y reglas congeladas.

## T20–T25 — ETAPA 0 CONTROLADA COMPLETADA 2026-10-12 (SEIS PREGUNTAS, NO P&L)

[Prerregistro previo a datos](research/nq/NQ_T20_T25_FIXED_ANCHOR_CONTROLLED_STAGE0_PREREG_2026_10_12.md) · [Resultado T20–T25 real de 7 meses](research/nq/NQ_T20_T25_CONTROLLED_STAGE0_RESULTS_2026_10_12.md) · [Action 38284276320 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38284276320), 9 tests sintéticos PASS, **140 fuente, 135 elegibles y 135 anclas idénticas**. Los seis contrastes comparten la primera barra 377 acabada de 10:00 a 10:15 ET, caso/control definidos ANTES de resultados, no se eligió primer evento posterior rentable. Los números **NO son trades ni N independientes; NO se midió respuesta económica o predictiva**.

| ID | Pregunta falsable (familia T20–25) | N casos | N controles | N eventos independientes | N trades | Efecto neto/PF/DD/Δ router | IC90 | p unilateral | q BH | Holm | 3/5 años | Gate1 | Estado |
|---|---|---:|---:|---|---|---|---|---|---|---|---|---|---|---|
| **T20** | ¿VWAP extremo en barra predice continuidad vs VWAP centrado? | **0** | 100 | N/D, 0 casos | N/D | N/D | N/D | N/D | N/D | N/D | N/D | FAIL viabilidad, sin caso | **NO IDENTIFICABLE** |
| **T21** | ¿Rechazo del máximo/mínimo anterior predice reversión vs aceptación? | **38** | 40 | N/D, hasta 38 días de caso | N/D | N/D | N/D | N/D | N/D | N/D | N/D | INFERENCIA N/D; muestra <151 | **CONTROL VIABLE; NO ALFA** |
| **T22** | ¿Alza de qty/print con avance supera qty/print estable? | **1** | 113 | N/D, 1 día caso | N/D | N/D | N/D | N/D | N/D | N/D | N/D | MUESTRA CASO INSUFICIENTE | **NO ALFA** |
| **T23** | ¿Desaceleración predice menor rango a +15min vs cadencia estable? | **1** | 8 | N/D, 1 día caso | No direccional | N/D | N/D | N/D | N/D | N/D | N/D | MUESTRA INSUFICIENTE | **SOLO MAGNITUD; NO ALFA** |
| **T24** | ¿Alternancia de signos VWAP aventaja a continuidad? | **39** | 50 | N/D, hasta 39 días de caso | N/D | N/D | N/D | N/D | N/D | N/D | N/D | INFERENCIA N/D; muestra <151 | **CONTROL VIABLE; NO ALFA** |
| **T25** | ¿Desacuerdo 233/4181 predice reanudación de tendencia vs acuerdo? | **47** | 59 | N/D, hasta 47 días de caso | N/D | N/D | N/D | N/D | N/D | N/D | N/D | INFERENCIA N/D; muestra <151 | **CONTROL VIABLE; NO ALFA** |

**No hay razón para calcular q/Holm todavía:** un control presente NO da el p de un contraste de outcomes; tampoco una cuenta de 135 sesiones garantiza N independiente >150. Todos los campos sin datos reales figuran N/D y ningún gate estadístico/económico PASS. Próximo bloque formal: prerregistro económico/predictivo de toda la familia sin alterar parámetros post-screen, con riesgos compartidos, multiprueba y holdouts cerrados.

## T20–T25 — FASE1 INTENTO REAL FALLIDO (NO RESULTADO ECONÓMICO)

**[Action 38286173182 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38286173182)**: 20/20 tests sintéticos PASS; ejecuciones de mercado DEV 2025oct–dic terminaron con paridad T05, pero en enero 2026 el motor Last devolvió una condición de **ejecución ambigua/no resuelta**, activando `T20_T25_AMBIGUOUS_EXECUTION_FAIL_CLOSED`. **No agregado de los siete meses, NO fill aceptado selectivamente, NO resultado de ventaja ni pérdida válido**. [Reporte de bloqueo y traceback](research/nq/NQ_T20_T25_STAGE1_FAILED_AMBIGUOUS_EXECUTION_2026_10_12.md). Por tanto, T20–T25 conservan los N caso/control de fase0, pero **N trades, expectativa, PF, DD, IC90 de retornos, p/q BH, Holm, incremento router y Gate1 = N/D/NO EVALUABLE** para toda la familia. El fallo es de **identificación de ejecuciones**, no una medición negativa de la rentabilidad. No retocar entradas/SL/TP/ventanas para rescatar el resultado. Próximo trabajo: diagnóstico técnico de estados de fill sin P&L, si procede, manteniendo H/T OOS cerrados.

## T14–T19 — MEDICIÓN ECONÓMICA Y PREDICTIVA COMPLETA 2026-10-12, SEIS PREGUNTAS

**[INFORME COMPLETO: T14–T19](research/nq/NQ_T14_T19_SIX_HYPOTHESES_ECONOMIC_RESULTS_2026_10_12.md)** · [**GitHub Actions 38279226193 COMPLETED SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38279226193), 7 tests PASS, fuente **140/135** DEV, T05 congelada **115/+US$5102,50 PF1,31826** paridad exacta. Datos Last de los siete meses ya adquiridos, sin 5s en señales nuevas ni OOS. **Fase económica T14/T15/T16/T18 ya calculada; NO confundir este panel con la FASE 0 de señales más abajo.**

| Hipótesis | Pregunta | N trades | Neto estrés US$ | PF estrés | DD Last US$ | Neto con +$10 RT US$ | IC90 bootstrap L5 USD/sesión extra$10 | q BH descriptivo familia 4 | Δ router vs T05 +$10RT US$ | ¿Cumple? |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| **T14** | ¿Persistencia suave anticipa continuación? | 115 | **−4192,50** | 0,6903 | 5862,50 | **−5342,50** | [−65,63,−14,31] | 1,00 | **−6222,50** | **NO** |
| **T15** | ¿Aceptación de precio redondo anticipa continuación? | 133 | **−3437,50** | 0,7710 | 3797,50 | **−4767,50** | [−57,59,−7,02] | 1,00 | **−5962,50** | **NO** |
| **T16** | ¿Esfuerzo qty/print sin desplazamiento anticipa giro? | 0 | 0 | N/D | 0 | 0 | N/D | 1,00 por convención | 0 | **NO SEÑALES** |
| **T18** | ¿La subasta preapertura anticipa continuidad? | 98 | **−1050** | 0,8990 | 3630 | **−2030** | [−36,76,+4,91] | 1,00 | **−5032,50** | **NO** |

**q BH=1.00 es solo DIAGNÓSTICO postselección**, no q confirmatorio: cuatro miembros T14/T15/T16/T18 conservados y p bootstrap centrado sobre retornos diarios 135 sesiones, 10k bloques móviles 5/3/10. Holm confirmatoria/OOS=**N/D**. La DD referencia $2000 es ilustrativa y no contrato real de fondeo. Las tres señales activas fallaron neto, PF 1,25, DD e incremento positivo; **no retocar reglas para rescatarlas**. Contrafactual router en una sola cuenta: T05+T14 **−$290** estrés, T05+T15 **+$110**, T05+T18 **+$720**, TODOS debajo T05 sola +$5102,50; no sumar standalone.

| Hipótesis NO DIRECCIONAL | Pregunta | N días con evento | Movimiento posterior 15m | Diferencia vs grupo sin evento | ¿Cumple ventaja estadística/económica? |
|---|---|---:|---|---|---|
| **T17** | ¿Más actividad sin rango anticipa amplitud posterior? | 135/135 | Rango medio **421,74 ticks** | N/D: 0 sesiones sin evento | **NO IDENTIFICABLE** |
| **T19** | ¿Recorrido ineficiente anticipa amplitud posterior? | 135/135 | Rango medio **446,50 ticks** | N/D: 0 sesiones sin evento | **NO IDENTIFICABLE** |

En T17/T19 se midió el rango real de los 15min siguientes a cada primera señal, pero **no se demuestra predictibilidad incremental** al no existir controles y tampoco hay lado, fills, PF o P&L. No convertir amplitud de mercado en rentabilidad.

**Decisión histórica T14–T19:** seis preguntas han recibido su primera medición completa o el dictamen formal de inidentificabilidad; ninguna supera Gate económico/estadístico. Se continuó con **T20–T25, cuya etapa 0 ya concluyó (tabla superior)**, no volver a optimizar T05 ni filtros de T14/T15/T18. [Reporte fuente auditable](research/nq/NQ_T14_T19_SIX_HYPOTHESES_ECONOMIC_RESULTS_2026_10_12.md).

## REGISTRO FASE 0 ANTERIOR del programa T14–T19 — seis preguntas genuinamente distintas, ambos lotes FASE 0 COMPLETADOS (12-oct-2026)

El usuario decidió **cambiar de objetivo: dejar de sobreoptimizar T05** y pasar a múltiples preguntas causales. [Registro de seis mecanismos T14–T19](research/nq/NQ_T14_T19_NEW_MECHANISMS_REGISTER_2026_10_12.md) · [prerregistro de T17–T19](research/nq/NQ_T17_T19_STAGE0_RULES_2026_10_12.md), antes de las respectivas mediciones; los cinco segundos quedan reservados únicamente a benchmark antiguo T05, nunca al disparador de estas hipótesis.

| Hipótesis | Pregunta falsable | N días con señal /135 | N trades monetarios | Media neta | IC90 | p | q BH | Holm | ¿Cumple / estado? |
|---|---|---:|---|---|---|---|---|---|---|
| **T14 — persistencia** | ¿Una serie de avances VWAP suaves mantiene la dirección sin expansión? | **115** | N/D | N/D | N/D | N/D | N/D | N/D | **PATRÓN DISPONIBLE, ALFA NO EVALUADA** |
| **T15 — precio redondo** | ¿Aceptar un nivel de 25 puntos NQ aporta continuidad? | **133** | N/D | N/D | N/D | N/D | N/D | N/D | **PATRÓN DISPONIBLE, ALFA NO EVALUADA** |
| **T16 — esfuerzo sin progreso** | ¿Mucho qty/print con poco avance precede reversión? | **0** | 0 con parámetros iniciales | N/D | N/D | N/D | N/D | N/D | **NO VIABLE sin alterar condición; NO RETUNEAR** |
| **T17 — intensidad vs rango** | ¿Más prints/segundo sin mayor rango anticipa volatilidad? | **135** | N/D, MAGNITUD | N/D | N/D | N/D | N/D | N/D | **PREDICCIÓN DE MAGNITUD NO EVALUADA** |
| **T18 — subasta apertura** | ¿La dirección preopen 08:00–09:30 persiste postapertura? | **98** | N/D | N/D | N/D | N/D | N/D | N/D | **PATRÓN DISPONIBLE, ALFA NO EVALUADA** |
| **T19 — trayectoria ineficiente** | ¿Mucho recorrido con escaso desplazamiento anticipa volatilidad? | **135** | N/D, MAGNITUD | N/D | N/D | N/D | N/D | N/D | **PREDICCIÓN DE MAGNITUD NO EVALUADA** |

**N de esta sección = sesiones en las que aparece al menos una señal; NO N trades ejecutados ni N efectivo estadístico.** Todos los tests de las pantallas son de **viabilidad**, sin P&L, precios de ejecución, SL/TP, IC90, q BH, Holm o declaración de rentabilidad. No dar PASS de Gate1 a ningún T14–T19. **T14 y T15 comparten 113 días de señal** (no demuestra mismo timestamp/side). T17 y T19 comparten 135 días; T18 coincide con ambos en 98. Por eso multiplicidad e independencia económica exigen pruebas futuras, no sumar oportunidades como si fueran tres estrategias distintas.

Fuentes verificadas con 140 días fuente/135 DEV elegibles, 7/7 meses y SHA256 de historial ya almacenado: [T14–T16 informe](research/nq/NQ_T14_T16_SIGNAL_SCREEN_RESULTS_2026_10_12.md) · [Action 38265573879 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38265573879), [T17–T19 informe](research/nq/NQ_T17_T19_SIGNAL_SCREEN_RESULTS_2026_10_12.md) · [Action 38266818415 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38266818415). 6+6 pruebas sintéticas PASS; sin historia nueva ni periodos sellados.

**NOTA HISTÓRICA YA SUPERADA (2026-10-12):** preregistro [económico T14–T16](research/nq/NQ_T14_T16_ECONOMIC_FIRST_PASS_PREREG_2026_10_12.md) YA creado, **NO EJECUTADO**: analizar las tres alternativas sin reoptimizar sus señales, stop/TP y costes fijos y su incremento en un solo router con T05 congelada. Se debe incluir T16 sin señales y corregir multiplicidad familiar sin escoger solo “ganadoras”. En paralelo T17/T19 requieren objetivo sobre **amplitud futura**, no falsa dirección; T18 económica en lote separado si se preregistra. **No retomar B05L/T05 retuning.**

## T recientes: NQ Last con 7 meses DEV y estadísticas faltantes

| Hipótesis | Pregunta | N trades | P&L estrés USD | PF estrés | DD Last estrés USD | IC90 | q BH | Holm | Estabilidad 3/5 años | Estado estadístico / económico |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| T02/T04 | ¿Fallo de ruptura de apertura revierte? | 190 | +6.860 | 1,24356 | 3.385 | N/D | N/D | N/D | N/D | NO EVALUABLE / falla PF y DD |
| T05-377 | ¿377 transacciones mejoran reversión T02? | 115 | +5.102,50 | 1,31826 | 1.797,50 | N/D | N/D | N/D | N/D | NO EVALUABLE / PF extra+$10=1,23717 |
| T05-233+377 | ¿Doble filtro compensa pérdida de frecuencia? | 59 | +4.657,50 | N/D | N/D | N/D | N/D | N/D | N/D | NO EVALUABLE / frecuencia min=2 |
| T09 | ¿Fallo rápido de ruptura genera alfa incremental? | N/D standalone (84 en router) | −2.087,50 | N/D | N/D | N/D | N/D | N/D | N/D | NO EVALUABLE / incremental negativo |
| T11 | ¿VWAP, retroceso y actividad añaden ventaja? | 85 | −382,50 | 0,97183 | 3.960 | N/D | N/D | N/D | N/D | NO EVALUABLE / falló gate operativo |
| T12 | ¿Compresión, ruptura y actividad añaden ventaja? | 268 | −2.440 | 0,94494 | 6.052,50 | N/D | N/D | N/D | N/D | NO EVALUABLE / incremental negativo |
| T13 | ¿Shock de volumen y retroceso añaden ventaja? | 133 | −5.562,50 | 0,75447 | 6.320 | N/D | N/D | N/D | N/D | NO EVALUABLE / incremental negativo |
| B05H-01 | ¿Expansión 233 + contexto 4181/10946 continúa? | N/D: 266 señales | N/D | N/D | N/D | N/D | N/D | N/D | N/D | NO EVALUABLE / 4 entradas ambiguas |
| B05H-02 | ¿377 prints revierten al VWAP en contexto lateral? | 75 | −1.427,50 | 0,82431 | 1.597,50 | N/D | N/D | N/D | N/D | NO EVALUABLE / incremental negativo |

**Importante:** En el programa T faltan intervalos IC90 inferidos con dependencia temporal, p y q familiares completos, y una muestra de cinco años para esa versión de las estrategias. N de trades no equivale automáticamente a N eventos independientes. **Nunca estimar q desde P&L agregado** ni presentar N/D como aprobación. Los 135 días DEV están reutilizados adaptativamente y los holdouts siguen cerrados.

## Regla permanente de reporte

Cada nueva hipótesis debe figurar en esta tabla con **ID, pregunta falsable, familia, N eventos independientes y N trades, efecto y costes, IC90 y método, p unilateral y q BH, resultado Holm confirmatorio separado, años/regímenes, PF, DD, frecuencia, P&L incremental en router único, fuente/Action y PASS/FAIL/NO EVALUABLE por condición**. Registrar antes de outcome la familia completa y dirección. La unidad estadística día/semana prevalece sobre la cantidad de prints, y las métricas faltantes son N/D, no inventadas. Históricos H anteriores conservan sus reglas originales, nuevas T siguen por barras de transacciones y **no por 5 segundos**. Sin adquirir nueva data ni abrir periodos reservados.
