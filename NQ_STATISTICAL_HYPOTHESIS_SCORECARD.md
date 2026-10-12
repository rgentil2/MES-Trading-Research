# NQ — Tabla estadística de hipótesis (Gate 1, q-BH e IC90)

**Última revisión: 11 de octubre de 2026.** Fuente: [Gate exploratorio original](research/es/ES_STAGE_GATES_EXPLORATORY_AMENDMENT_2026_10_09.md), [confirmatorio original](research/es/ES_STAGE_GATES.md), [gobernanza Holm](research/RESEARCH_CONTROLS_POLICY.md). Evaluación automatizada [código](research/nq/nq_gate1_statistical_scorecard.py) · [GitHub Action 38198391656 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38198391656) (6 pruebas PASS; resumen estadístico reproducible).

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
