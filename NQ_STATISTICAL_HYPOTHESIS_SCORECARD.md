# NQ — Tabla estadística de hipótesis (Gate 1, q-BH e IC90)

**Última revisión: 12 de octubre de 2026; cohorte T59–T96 de 38 hipótesis completó D0 y D1 como BLOQUE, cero estadísticamente promovidas.** Fuente: [Gate exploratorio original](research/es/ES_STAGE_GATES_EXPLORATORY_AMENDMENT_2026_10_09.md), [confirmatorio original](research/es/ES_STAGE_GATES.md), [gobernanza Holm](research/RESEARCH_CONTROLS_POLICY.md). Evaluación automatizada [código](research/nq/nq_gate1_statistical_scorecard.py) · [GitHub Action 38198391656 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38198391656) (6 pruebas PASS; resumen estadístico reproducible).

**Gate 1 prospectivo:** N>150 eventos elegibles independientes; efecto medio neto favorable; intervalo bilateral **IC90** en el lado preregistrado (>0 si la hipótesis es positiva); **q Benjamini–Hochberg ≤0,10 sobre los miembros completos de la familia**; ≥3/5 años positivos. Todo obligatorio. Holm con α_k=0,05/[k(k+1)] es confirmación separada, no reemplaza q ni las reservas OOS. Este Gate 1 es exploratorio: PASS no permitiría fondeo. Los preregistros antiguos más estrictos permanecen intactos.

## T59–T96 — 38 hipótesis en BLOQUE, D0 y D1 CERRADOS (12-oct-2026)

**[Tabla completa con las 38 filas de N, efecto Δ, IC90 L5, p, qBH38 y decisión](research/nq/NQ_T59_T96_38_MEMBER_WHOLE_COHORT_D1_RESULTS_2026_10_12.md)**, [Action D1 38313582820 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38313582820) y [artifact seguro 11776430223](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38313582820/artifacts/11776430223), SHA256 `f4253ceacfad3707fa43185f6e1935ce00794b9eced6f266c16069c73f968e3c`. [Prerregistro anterior a resultados](research/nq/NQ_T59_T96_COHORT_38_D1_PREREG_2026_10_12.md). **D0** [Action 38313046875 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38313046875): 38 registradas, **36 TESTABLE y 31 diversas**, 2 LOW_POWER (T60/T77). **D1** 38/38 medidas, **qBH38 mínima 0,239376>0,10**, 22 inconclusas, 14 no respaldadas por efecto desfavorable, 2 no estimables, **0/38 PASAN BH**; bandeja D2 económica=0, sin estrategia validada.

| ID observado favorable individualmente | Pregunta / bloque | N CASE/CTRL | Δ observacional ticks | IC90 L5 (ticks) | p L5 EXP | **q BH38** | Gate D1 |
|---|---|---:|---:|---|---:|---:|---|
| T65 | Cambio del valor negociado entre mitades de PM | 79/56 | +53,224 | [+10,99,+96,31] | 0,0202 | 0,2470 | **NO** |
| T75 | Pendiente causal B→A en barras377 anteriores | 66/69 | +57,201 | [+26,23,+95,23] | 0,0063 | **0,2394** | **NO** |
| T84 | Diferencia de VWAP temprano/tardío por prints E | 94/41 | +65,727 | [+18,81,+116,30] | 0,0148 | 0,2470 | **NO**, casi duplicado de T88 en CASE |
| T88 | Valor temprano/tardío de grupos timestamp en E | 96/39 | +65,449 | [+16,77,+120,53] | 0,0260 | 0,2470 | **NO** |
| T93 | Precio atómico al cierre de E frente POC E | 77/57 | +41,005 | [+8,66,+81,75] | 0,0493 | 0,3496 | **NO** |
| T94 | Precio atómico al cierre de E frente medio rango E | 82/53 | +46,388 | [+11,63,+93,99] | 0,0552 | 0,3496 | **NO** |
| T95 | Precio atómico al cierre de E frente medio rango D | 112/22 | +50,283 | [+0,38,+114,02] | 0,1032 | 0,4902 | **NO** |

**Los 31 nombres D0 viables NO son alfas; las siete medias con IC90 individual positivo NO alcanzaron la corrección BH sobre los 38 miembros**, incluidos T60/T77 no estimables y T71/T81/T82/T83/T84 casi duplicadas. No se cambian side, CASE/CONTROL ni umbrales para rescatar q. [Detalle D0 de los 38 y redundancia](research/nq/NQ_T59_T96_SIX_BLOCK_COHORT_D0_RESULTS_2026_10_12.md) y [scorecard D1 los 38](research/nq/NQ_T59_T96_38_MEMBER_WHOLE_COHORT_D1_RESULTS_2026_10_12.md) contienen TODAS las decisiones. **N_trades=0; USD neto/PF/DD/Δrouter/Holm/OOS/ROI=N/D**: markout VWAP o rango 15m físicos NO son ejecuciones de cuenta.

## AMPLIACIÓN PROSPECTIVA T153–T168 — 16 estrategias nuevas SIN resultados D0 aún

**Prerregistro anterior a evaluación:** [JSON T153–T168](research/nq/NQ_T153_T168_FOUR_STRATEGY_BLOCKS_D0_PREREG_2026_10_12.json), [narrativa de cuatro bloques](research/nq/NQ_T153_T168_FOUR_STRATEGY_BLOCKS_D0_PREREG_2026_10_12.md). Originales T133–T152 **15 D0 testables/diversas** sin alteraciones. Nueva D0 evalúa **20+16=36** mecanismos económicos con CASE/CONTROL/OTHER/MISSING, coteja exactamente las 20 máscaras congeladas (140 sesiones fuente/135 elegibles) y mide Jaccard de CASOS entre todos ocho bloques. [CI Action 38325498797](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38325498797) **lanzada**, sin D0 real confirmado en este registro. Los nuevos mecanismos son E fade VWAP, F confirmación subasta, G ubicación rango, H estructura de cinta. **NO correr D1 hasta ≥20 testables distintas y preregistro separado de economía, fills/costos y familia BH36**; cada métrica de retornos PnL/PF/DD/IC90/p/q/Holm está N/D.

## T133–T152 — Primer lote de ESTRATEGIAS COMPLETAS: D0 FINAL, D1 NO AUTORIZADA

**[Prerregistro de las 20 estrategias](research/nq/NQ_T133_T152_EXECUTABLE_D0_PREREG_2026_10_12.md)**, [política de pruebas económicas](research/nq/NQ_EXECUTABLE_STRATEGY_COHORT_POLICY_2026_10_12.md), [Action D0 FINAL 38324292967 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38324292967), [artifact SAFE 11779419992](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38324292967/artifacts/11779419992). [**Tabla definitiva de 20 hipótesis, N y cada pregunta**](research/nq/NQ_T133_T152_FOUR_COMPLETE_STRATEGIES_BLOCKS_D0_RESULTS_2026_10_12.md), [JSON de conteos congelados](research/nq/NQ_T133_T152_D0_COUNTS_FROZEN_2026_10_12.json).

| Bloque | IDs | TESTABLE y distintas | LOW_POWER | D1 / economía |
|---|---|---:|---|---|
| Ruptura de niveles | T133–T137 | **4** | T134 | **NO EVALUADA** |
| Pullback VWAP | T138–T142 | **3** | T138, T139 | **NO EVALUADA** |
| Falsa ruptura y reversión | T143–T147 | **3** | T143, T144 | **NO EVALUADA** |
| Régimen de ejecución | T148–T152 | **5** | Ninguna | **NO EVALUADA** |
| **TOTAL** | **20** | **15** | **5** | **D1 BLOQUEADA** (requiere ≥20) |

**140 fuente/135 elegibles, oct2025–abr2026**; diversidad Jaccard CASE<0,85 (0 duplicadas entre testables). Prueba cronológica interna: 53 READY oct–dic 2025, 82 READY ene–abr 2026; **NO OOS independiente**. Cinco LOW_POWER por N_CASE<15; ninguna recuperación de datos futuros se utilizó. **N_trades (efectivos o simulados), PF, DD, P&L, p/q, IC90, Holm, ROI y ΔRouter=N/D**. No confundir CASE con operación ejecutada.

**Auditoría:** resultado 13/20 de Action 38323990208 era PRELIMINAR por dos referencias T146/T147 no enlazadas; reparadas solo lecturas existentes, Action final 38324292967 da **15/20**, no se retocaron condiciones, stops ni TP. D1 de familia económica no registrada/ejecutada ni autorizada al faltar cinco candidatas viables. Siguiente cohorte debe plantear **nuevos mecanismos distintos**, no optimizar las cinco bajas N.

## REGLA NUEVA PARA TODAS LAS SIGUIENTES PRUEBAS T133–T152 (12-oct-2026)

**El usuario aprobó un cambio de metodología:** no basta con intervalos de `markout` o predicción de rango; desde la cohorte T133–T152 las preguntas definen estrategias **completas** (activación, dirección, parada, objetivo, horizonte, costes y ruta de ejecución) con cuatro mecanismos en bloque: ruptura/retest, continuación/pullback, falsa ruptura/reversión y filtro régimen/riesgo. [Enmienda de pruebas económica/estadística vinculante](research/nq/NQ_EXECUTABLE_STRATEGY_COHORT_POLICY_2026_10_12.md). 

**Tabla de salida estándar obligatoria:** `ID | bloque | pregunta | long/short | trigger | entrada teórica | SL | TP | timeout | N_CASE | N_CONTROL | N_OTHER | N_MISSING | N_active_days/weeks/months | TESTABLE | Jaccard | N_trades hipótesis | instrumento | costes/slippage | neto e IC90 L3/L5/L10 | p/q BH familia completa | Holm | PF/DD | DeltaRouter | estados G0/D0/D1/D2 | por qué PASS/FAIL/N/D`. D0 no utiliza futuro, por tanto columnas de trades/costes realizados/neto/IC90/p/q/PF/DD en D0 siempre **N/D**, no cero inventado. Las fechas oct–dic 2025 / ene–abr 2026 son **diagnóstico y validación cronológica interna exploratoria**, NO nuevo OOS debido a reutilización previa.

**Puertas sin excepciones:** caso y control≥15, shortlist≥20 TESTABLE distintas Jaccard CASE<0,85 para nueva D1; BH/Holm según jerarquía anterior y universo original congelado. No relajar umbrales para que exactamente 20 'pasen', ni reinterpretar Last como fill o beneficio en cuenta fondeada. Baselines previos T05 congelado y 104 D1 de cohortes grandes con 0 supervivientes familiares. D2 de **cartera agrupada**, no de hipótesis única.

## T97–T132 — 36 hipótesis en SEIS BLOQUES, D0/D1 CERRADOS (12-oct-2026)

**D0** [Action 38318189842 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38318189842): 7 DEV SHA256 140/135, **36 registradas→30 TESTABLE→26 diversas (gate20 PASS)**, [tabla de casos y controles de los 36](research/nq/NQ_T97_T132_SIX_BLOCKS_D0_RESULTS_2026_10_12.md), [conteos congelados](research/nq/NQ_T97_T132_D0_FROZEN_COUNTS_2026_10_12.json). T110/T127/T128/T129/T132 LOW_POWER, T125 135/0 UNIDENTIFIABLE; T102/T114/T115/T120 cerca de duplicados CASE.

**D1 de TODO k36**, preregistrado ANTES de mirar D0/outcomes [protocolo](research/nq/NQ_T97_T132_D1_WHOLE_COHORT_PREREG_2026_10_12.md), [Action 38318511015 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38318511015), artifact seguro [11777853779](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38318511015/artifacts/11777853779), sha256 `04feccb80476d4dd939c9d06b79a356633113e2d064ccb269f5a07c9d2ac5d8f`. **Tabla de TODOS los 36 con N, efecto, IC90 L5, p, qBH36, PASS/NO PASS:** [informe completo](research/nq/NQ_T97_T132_36_MEMBER_D1_RESULTS_2026_10_12.md). **24 INCONCLUSIVE, 6 NOT_SUPPORTED por signo desfavorable y 6 NOT_ESTIMABLE**. Siete IC90 L5 positivos de markout firmado +300s, pero **qBH36 mínima = 0,2639736 > 0,10: 0/36 PASA**, por tanto **0 para D2**.

| Hipótesis / mecanismo | N CASE/CTRL | Efecto `Δ` ticks PRECIO, no PnL | IC90 L5 | p exploratoria | q BH36 | ¿Cumple D1? |
|---|---:|---:|---|---:|---:|---|
| T100, micro233 | 88/47 | +60,770 | [+16,683;+110,483] | 0,0223 | 0,2640 | **NO** |
| T103, macro4181 | 69/64 | +33,047 | [+2,899;+69,795] | 0,0712 | 0,2910 | **NO** |
| T108, contexto4181 | 69/64 | +55,349 | [+18,812;+102,849] | 0,0259 | 0,2640 | **NO** |
| T111, barrera 377 | 57/76 | +60,348 | [+11,545;+115,838] | 0,0353 | 0,2640 | **NO** |
| **T112, barrera 233** | 39/96 | **+69,985** | **[+23,592;+122,477]** | **0,0132** | **0,2640** | **NO** |
| T119, centro 233 | 105/29 | +45,875 | [+0,405;+101,895] | 0,0890 | 0,2910 | **NO** |
| T130, confluencia 4181/PM | 36/30 | +47,159 | [+4,052;+100,909] | 0,0764 | 0,2910 | **NO** |

**N_trades=0; fills Last no verificables; USD neto/PF/DD/ROI/DeltaRouter/Holm/OOS=N/D.** L5 bootstrap bloques por sesiones B=10.000, L3/L10 sensibilidad en artifact. Reutilización DEV ⇒ q/p DESCRIPTIVAS, no autorización de fondeo, no extraer ocho mejores ni retunar T112. Siguiente cohorte debe **formular mecanismos económicamente ejecutables nuevos y preregistrar validación cronológica interna** antes de ver resultados.

## Embudo global obligatorio POR COHORTES (actualización 12-oct-2026)

[Política completa](research/nq/NQ_COHORT_FUNNEL_POLICY_2026_10_12.md) · [Ledger máquina](research/nq/NQ_COHORT_FUNNEL_LEDGER_2026_10_12.json) · **[TABLERO DE CUELLO DE BOTELLA](research/nq/NQ_COHORT_FUNNEL_STATUS_2026_10_12.md)**. En lugar de una estrategia individual T05→D1→D2, ahora **cada fase evalúa el BLOQUE completo** y solo sus supervivientes se agrupan en la bandeja siguiente.

| Cohorte | Número original | D0 TESTABLE | D0 diversas | D1 analizadas | Calificadas por familia/ejecución para D2 | Etapa |
|---|---:|---:|---:|---:|---:|---|
| T29–T58 | 30 | 27 | **25** | 30 | **0** (q mínima0,2122>0,10; indicadores de rango no operativos) | D1 CERRADO |
| T20–T25 | 6 | 3 | No medida bajo nueva regla histórica | 6 | **0** | D1 CERRADO LEGACY |
| T26–T28 | 3 | 1 | No medida bajo nueva regla histórica | 3 | **0** (T26 signo contrario, T27/T28 no estimables) | D1 CERRADO LEGACY |
| **T59–T96 (cohorte NUEVA cerrada)** | **38** | **36** | **31** | **38** | **0**, BH38 q mínima0,2394 | **D1 CERRADO**; T60/T77 LOW_POWER |

**Estados por hipótesis permanecen en las tablas originales siguientes**, con N, IC90, q, PF, DD etc., y se muestran N/D cuando la etapa NO midió esas variables. No sumar q/PF de H históricos, no asignar USD a markout/rango futuro. D1 se ejecuta únicamente en lote de 20+ distintas; D2 agrupa mecanismo ejecutables aprobados en D1 bajo un solo router, nunca un resultado retrospectivo aislado. T05 congelada como benchmark, no aprobada para fondeo.

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

## T20–T25 con política G0→D0→D1→D2: QC y D1 predictivo CERRADOS (12-oct-2026)

**Política activa:** [documento y gates](research/nq/NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md) / [CI 38295393496 SUCCESS, 8 pruebas](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38295393496). **QC de estados Last** [38293741380 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38293741380), 140/135/7 meses, [informe](research/nq/NQ_T20_T25_EXECUTION_STATUS_QC_RESULTS_2026_10_12.md). **D1 de markout observacional** [38296113086 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38296113086), 8 tests, 7/7 DEV, [artifact 11767833548](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38296113086/artifacts/11767833548), [informe completo](research/nq/NQ_T20_T25_D1_ATOMIC_TIMESTAMP_MARKOUT_RESULTS_2026_10_12.md). **D1 = VWAP de barra E a VWAP de primer grupo completo POST+300s en ticks, T23 rango 15m, NO operaciones ni rentabilidad monetaria**.

| ID | Pregunta | N casos/ctrl (markouts observables) | D0 | D1 caso media ticks | D1 control media ticks | Δ pred. ticks | IC90 L5 Δ ticks | p L5 DESCRIPTIVO | q BH 6 DESCRIPTIVA | Gate D1 predictivo | Trade neto/PF/DD/ΔRouter | ¿Estrategia validada? |
|---|---|---|---|---:|---:|---:|---|---:|---:|---|---|---|
| T20 | Valor extremo vs centrado | 0/100 (0/88; 12 ctrl side0) | UNIDENTIFIABLE | N/D | +23,411 | N/D | N/D | N/D | N/D | NOT_ESTIMABLE | N/D por fill Stage1 | **NO** |
| T21 | Rechazo extremo vs aceptación | 38/40 | TESTABLE | **−34,816** | +12,632 | **−47,448** | [−106,832,+10,708] | 0,9043 | **1,00** | NOT_SUPPORTED_DESCRIPTIVE, IC cruza0 | N/D por fill Stage1 | **NO** |
| T22 | Qty/print con avance | 1/113 | LOW_POWER | +366,218 | +12,612 | +353,606 (1 caso) | N/D | N/D | N/D | NOT_ESTIMABLE | N/D por fill Stage1 | **NO** |
| T23 | Desaceleración vs rango futuro | 1/8, rango no trade | LOW_POWER | 452,000 rango | 287,375 rango | −164,625 (control−caso) | N/D | N/D | N/D | NOT_ESTIMABLE | N/A magnitud | **NO** |
| T24 | Alternancia de VWAP vs continuidad | 39/50 | TESTABLE | +8,676 | +28,310 | **−19,635** | [−91,243,+30,139] | 0,6181 | **1,00** | NOT_SUPPORTED_DESCRIPTIVE, IC cruza0 | N/D por fill Stage1 | **NO** |
| T25 | Divergencia 233/4181 vs alineación | 47/59 | TESTABLE | +27,663 | +17,007 | **+10,657** | [−23,192,+56,899] | 0,4334 | **1,00** | INCONCLUSIVE | N/D por fill Stage1 | **NO** |

**Diferenciación de inferencia obligatoria:** Los IC90, p y q de esta sección se refieren **solo a desplazamiento observacional en TICKS** con bootstrap no circular de 135 días L5 y sensibilidad L3/L10; **no se trasladan a expectativa económica USD, PF, DD ni q de una estrategia ejecutada**. Los tres miembros no estimables permanecen en la familia BH con p=1 **sentinela contable**, pero sus q individuales inferenciales siguen N/D. Ninguna de las tres medidas estimables tiene IC90 favorable completo, todas q=1,00 descriptiva; selección previa adaptativa invalida confirmación. Holm, 3/5 años, OOS y fondeo siguen N/D/bloqueados; no se ha abierto información reservada.

**Decisión:** 0/6 alfa confirmada. D1 T21/T24 con signo puntual adverso (no es inferencia robusta de pérdida porque sus IC cruzan0), T25 positivo pequeño INCONCLUSO y no se promueve; T22 caso único no permite selección de parámetro ni trading. **La fase1 económica original continúa FAIL-CLOSED [38286173182](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38286173182)**. Próximo backlog: D0 de mecanismos NUEVOS con preregistro previo y control observacional, sin nuevas fuentes ni 5s.

## T26–T28 — D0 y D1 FAMILIAR CERRADOS, resultado negativo/no estimable (12-oct-2026)

[Prerregistro original T26–T28](research/nq/NQ_T26_T28_D1_OBSERVATIONAL_PREREG_2026_10_12.md), congelado antes de outcomes; [D0](research/nq/NQ_T26_T28_G0_D0_RESULTS_2026_10_12.md), 140/135, casos/controles 18/36, 6/65 y 3/0. [**D1 Action 38306171742 COMPLETED SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306171742), [informe 3 integrantes](research/nq/NQ_T26_T28_D1_OBSERVATIONAL_RESULTS_2026_10_12.md), [artifact 11772618236](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306171742/artifacts/11772618236), digest `b5fd4fafdd5379cbfa1448d36a6a8ea1a5ce2f9e0cc118d86b92ed84649cce01`. 7 DEV meses existentes, 140 fuente/135 READY. Primer Action 38306058654 FAILURE por argumento fecha en `file_for`, corregido sin variar hipótesis.

| ID / pregunta | D0 CASE/CTRL | N trades / N efectivo | Δ esperado (ticks de precio) | IC90 L3 | **IC90 L5** | IC90 L10 | p L5 exploratorio | q BH3 descriptivo | D1 | PF/DD/NETO/Holm/OOS | ¿Gate1/monetizable? |
|---|---:|---|---:|---|---|---|---:|---:|---|---|---|
| **T26** ¿mayor chop implica mayor rango próximo? | **18/36** | 0 / N/D | **−67,750** rango 15min | [−140,589,−0,887] | **[−136,302,−5,412]** | [−128,818,−22,483] | **0,948105** | **1,000** | **NOT_SUPPORTED_DESCRIPTIVE** | N/D | **NO** |
| **T27** ¿prima qty/VWAP anticipa continuación? | **6/65** | 0 / N/D | −38,596 markout +300s con 6 casos | N/D | N/D | N/D | N/D | N/D (p=1 sentinela solo BH) | NOT_ESTIMABLE | N/D | **NO** |
| **T28** ¿CV2 de llegadas anticipa rango? | **3/0** | 0 / N/D | N/D | N/D | N/D | N/D | N/D | N/D (p=1 sentinela solo BH) | NOT_ESTIMABLE/UNIDENTIFIABLE | N/D | **NO** |

**Importante:** Los IC negativos del rango de T26 son contrarios a la dirección POSITIVA prerregistrada. No invertir signo ahora para anunciar un sistema ganador ni convertir rango físico en USD. **0/3** cumplen BH familiar ≤0,10, todo DEV reutilizado => inferencia solo descriptiva, no independencia ni Holm. T26 no se suma a T30 como mecanismo diferente. Para recuperar H77/H69/H74 históricos, [G0 original no portable con Last 08–12](research/nq/NQ_LEGACY_H77_H69_H74_T26_PORTABILITY_GATE_2026_10_12.md); sus nuevas variantes T59/T60 conservan IDs distintos y solo D0.

## T59–T60 — NUEVAS hipótesis de premercado inspiradas en H77/H69 (NO REPRODUCCIONES), D0 CERRADO 12-oct-2026

[Prerregistro ex ante](research/nq/NQ_T59_T60_LEGACY_MECHANISM_ADAPTATION_D0_PREREG_2026_10_12.md), [Action 38306833847 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306833847), 8 tests, 7/7 meses DEV, 140 fuente/135 READY; [informe](research/nq/NQ_T59_T60_NEW_PREMARKET_D0_RESULTS_2026_10_12.md); [artifact 11773042751](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306833847/artifacts/11773042751), digest `75c467dd21291e4f0bfe2dd63ac9eedc27d6ed3c78557533d2ffb367c8ea60c4`. H77/H69/H74 originales `NOT_PORTABLE` con Last 08–12: [auditoría](research/nq/NQ_LEGACY_H77_H69_H74_T26_PORTABILITY_GATE_2026_10_12.md).

| Hipótesis nueva / pregunta | N CASE | N CONTROL | D0 | N trades y N efectivo | Delta futuro/IC90 | p / BH q / Holm | P&L/PF/DD/DeltaRouter | ¿Cumple gate? |
|---|---:|---:|---|---|---|---|---|---|
| **T59** ¿oposición cuerpo PM vs primer15 RTH frente a alineación? | **45** | **42** | **TESTABLE** por frecuencia de grupos | N/D | N/D **SIN OUTCOMES** | N/D | N/D | **NO, D1 BLOQUEADO hasta 20+ nueva cohorte** |
| **T60** ¿dislocación apertura RTH frente a VWAP PM alineada/opuesta a PM body? | **71** | **6** | **LOW_POWER** | N/D | N/D **SIN OUTCOMES** | N/D | N/D | **NO, y no ajustar umbrales** |

N son sesiones categorizadas, NO trades. `N_eff`, IC90 de ventaja, q-BH monetaria y 3/5 años NO se evaluaron. No sumar H77/H69 q y PF históricos a estos nuevos patrones; ni abrir holdouts ni comprar datos. La nueva familia tiene solo 1 TESTABLE, no supera por sí misma el requisito de **20 candidatas distintas D0** para lanzar nueva D1.

## T29–T58 — cinco bloques, 30 hipótesis, D0 y D1 VERIFICADOS 12-oct-2026

[Política de **>=20 candidatas D0 diversificadas**](research/nq/NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md), sección 6. **G0/D0** [Action 38300121097 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38300121097), [informe](research/nq/NQ_T29_T58_30_HYPOTHESES_G0_D0_RESULTS_2026_10_12.md): 30 registradas antes de screen, 27 TESTABLE, 25 shortlist diversa, 7 meses 140/135/135. **D1** [Action 38300856124 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38300856124), [informe de 30 efectos, IC y q](research/nq/NQ_T29_T58_30_HYPOTHESES_D1_BATCH_RESULTS_2026_10_12.md) y [artifact 11770745392](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38300856124/artifacts/11770745392) digest `sha256:710d19b99c383f22c43ba7de923ce91a83479269857326a5ca1a98fffedbd989`. D1 7 meses, bootstrap no circular por 135 sesiones B10000 L5 y sensibilidad L3/10; **B1/B3/B4/B5 rango futuro15min, B2 markout VWAP firmado+300s, TICKS NO P&L**.

| Hipótesis | Bloque / outcome | N CASE/CTRL | D0 | En 25 diversas | Δ D1 ticks | IC90 L5 (ticks) | p L5 EXP | q BH30 DESCR | Estado D1 | N_trades/NETO/PF/DD/Δrouter/Holm/años/ROI | ¿Estrategia validada? |
|---|---|---:|---|---|---:|---|---:|---:|---|---|---|
| T29 | B1 rango | 80/31 | TESTABLE | SÍ | 61,96 | [14,43, 114,56] | 0,0252 | 0,2122 | PREDICTIVE_IN_SAMPLE | N/D | **NO** |
| T30 | B1 rango | 44/72 | TESTABLE | SÍ | -24,72 | [-83,20, 29,38] | 0,7639 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T31 | B1 rango | 65/65 | TESTABLE | SÍ | 2,46 | [-47,22, 56,15] | 0,4938 | 0,9258 | INCONCLUSIVE | N/D | **NO** |
| T32 | B1 rango | 85/40 | TESTABLE | NO | 52,93 | [-0,10, 98,41] | 0,0283 | 0,2122 | INCONCLUSIVE | N/D | **NO** |
| T33 | B1 rango | 72/59 | TESTABLE | SÍ | 1,17 | [-51,32, 52,10] | 0,4858 | 0,9258 | INCONCLUSIVE | N/D | **NO** |
| T34 | B1 rango | 46/67 | TESTABLE | SÍ | -9,48 | [-60,61, 54,80] | 0,6762 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T35 | B2 dirección | 45/60 | TESTABLE | SÍ | -4,56 | [-52,31, 50,08] | 0,5847 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T36 | B2 dirección | 66/64 | TESTABLE | SÍ | -15,33 | [-58,77, 26,36] | 0,7075 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T37 | B2 dirección | 68/62 | TESTABLE | SÍ | -43,91 | [-83,53, -5,57] | 0,9639 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T38 | B2 dirección | 61/68 | TESTABLE | SÍ | -39,78 | [-97,38, 4,19] | 0,8628 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T39 | B2 dirección | 62/30 | TESTABLE | SÍ | 7,22 | [-34,56, 54,84] | 0,4497 | 0,9258 | INCONCLUSIVE | N/D | **NO** |
| T40 | B2 dirección | 31/36 | TESTABLE | SÍ | 42,38 | [-16,76, 105,18] | 0,1282 | 0,6409 | INCONCLUSIVE | N/D | **NO** |
| T41 | B3 rango | 15/17 | TESTABLE | SÍ | 76,85 | [-26,13, 183,06] | 0,1162 | 0,6409 | INCONCLUSIVE | N/D | **NO** |
| T42 | B3 rango | 45/42 | TESTABLE | SÍ | -6,72 | [-62,51, 65,98] | 0,6374 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T43 | B3 rango | 60/40 | TESTABLE | SÍ | 17,42 | [-39,79, 84,85] | 0,3801 | 0,9258 | INCONCLUSIVE | N/D | **NO** |
| T44 | B3 rango | 79/51 | TESTABLE | SÍ | -34,46 | [-85,34, 25,49] | 0,8767 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T45 | B3 rango | 79/39 | TESTABLE | SÍ | 62,76 | [7,73, 109,43] | 0,0165 | 0,2122 | PREDICTIVE_IN_SAMPLE | N/D | **NO** |
| T46 | B3 rango | 48/39 | TESTABLE | SÍ | -28,11 | [-88,66, 25,65] | 0,7827 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T47 | B4 rango | 28/100 | TESTABLE | SÍ | -32,83 | [-83,89, 10,86] | 0,8467 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T48 | B4 rango | 89/14 | LOW_POWER | NO | 43,89 | N/D | N/D | N/D | NOT_ESTIMABLE | N/D | **NO** |
| T49 | B4 rango | 101/23 | TESTABLE | SÍ | 76,28 | [18,08, 133,03] | 0,0135 | 0,2122 | PREDICTIVE_IN_SAMPLE | N/D | **NO** |
| T50 | B4 rango | 14/93 | LOW_POWER | NO | -14,45 | N/D | N/D | N/D | NOT_ESTIMABLE | N/D | **NO** |
| T51 | B4 rango | 13/84 | LOW_POWER | NO | -82,49 | N/D | N/D | N/D | NOT_ESTIMABLE | N/D | **NO** |
| T52 | B4 rango | 67/46 | TESTABLE | SÍ | 10,51 | [-39,80, 64,30] | 0,4139 | 0,9258 | INCONCLUSIVE | N/D | **NO** |
| T53 | B5 rango | 80/32 | TESTABLE | NO | 32,86 | [-17,91, 84,33] | 0,1515 | 0,6492 | INCONCLUSIVE | N/D | **NO** |
| T54 | B5 rango | 50/44 | TESTABLE | SÍ | -10,56 | [-64,34, 45,45] | 0,6383 | 1,0000 | NOT_SUPPORTED | N/D | **NO** |
| T55 | B5 rango | 69/55 | TESTABLE | SÍ | 19,83 | [-34,57, 68,34] | 0,2314 | 0,7713 | INCONCLUSIVE | N/D | **NO** |
| T56 | B5 rango | 60/64 | TESTABLE | SÍ | 22,37 | [-33,68, 68,34] | 0,1919 | 0,7196 | INCONCLUSIVE | N/D | **NO** |
| T57 | B5 rango | 53/27 | TESTABLE | SÍ | 18,70 | [-48,78, 80,23] | 0,3056 | 0,9167 | INCONCLUSIVE | N/D | **NO** |
| T58 | B5 rango | 58/58 | TESTABLE | SÍ | 7,64 | [-35,76, 60,36] | 0,4873 | 0,9258 | INCONCLUSIVE | N/D | **NO** |

**Resultado conjunto obligatorio:** T29 **+61,96 rango ticks**, IC90[14,43,114,56], p0,0252/q**0,2122**; T45 **+62,76**, IC90[7,73,109,43], p0,0165/q**0,2122**; T49 **+76,28**, IC90[18,08,133,03], p0,0135/q**0,2122**. **3/30 indicadores predictivos prometedores INDIVIDUALMENTE**, **13 inconclusos**, **11 de signo puntual desfavorable**, **3 no estimables**. **Ninguno** cumple `q BH≤0,10` con k=30, y ninguna prueba constituye beneficio monetario ni fill broker. `IC90/p/q` de esta sección SOLO se refieren a magnitud física o signed markout en precio, no IC de ganancia USD. Los p/q en DEV elegida adaptativamente no son confirmación incluso cuando fueran pequeños.

**Multiplicidad íntegra:** los cinco miembros fuera de shortlist D0 (T32,T48,T50,T51,T53) permanecen dentro del ajuste BH30. Para T48/T50/T51 el motor incorporó `p=1` como *sentinela de corrección*, pero sus valores inferenciales IC/p/q individuales siguen N/D. N independiente efectivo, Holm confirmatoria, N eventos Gate1>150/3de5, cuentas/fees y rentabilidad ETF N/D. Las señales T29/T45/T49 de mayor rango NO son entradas long/short. **No abrir OOS, cambiar thresholds ni usar capital real**. El próximo estudio de mecanismos combinados solo podrá ser prospectivo, con riesgo/ejecución y comparación incremental de una sola cuenta.

## Regla permanente de reporte

Cada nueva hipótesis debe figurar en esta tabla con **ID, pregunta falsable, familia, N eventos independientes y N trades, efecto y costes, IC90 y método, p unilateral y q BH, resultado Holm confirmatorio separado, años/regímenes, PF, DD, frecuencia, P&L incremental en router único, fuente/Action y PASS/FAIL/NO EVALUABLE por condición**. Registrar antes de outcome la familia completa y dirección. La unidad estadística día/semana prevalece sobre la cantidad de prints, y las métricas faltantes son N/D, no inventadas. Históricos H anteriores conservan sus reglas originales, nuevas T siguen por barras de transacciones y **no por 5 segundos**. Sin adquirir nueva data ni abrir periodos reservados.
