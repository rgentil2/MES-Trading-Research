# NQ T20–T25 — resultado real de seis preguntas con caso/control (etapa 0)
**12-oct-2026 · [GitHub Actions 38284276320 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38284276320) · [artifact final seguro 11762777337](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38284276320/artifacts/11762777337)**

## Qué sí se hizo y qué NO se hizo
- Se creó y congeló [prerregistro T20–T25](NQ_T20_T25_FIXED_ANCHOR_CONTROLLED_STAGE0_PREREG_2026_10_12.md) en commit `8dc46d1ad248258b5557a6974e409a6e4f5dd689` **antes del primer run de mercado**. Motor/pruebas/aggregador ya versionados; 9/9 tests sintéticos PASS antes de lectura histórica. La ejecución final completó los 7 meses y guardó artefacto seguro de 2.386 bytes, checksum SHA256 `dcc4ff0357f9193a88fe5e60db843f2466c28c87b272d2078cd20168b7b98f59`.
- Exclusivamente **NQ Last DEV preexistente** octubre 2025–abril 2026, hashes comprobados; **140 sesiones fuente, 135 elegibles READY**, 135/135 con **un ancla 377-print** entre 10:00–10:15 ET. No data nueva adquirida, ni archivos H/T sellados, ni barras de 5s como señal T20–T25. Los grupos con timestamp igual permanecieron indivisibles.
- Se midió por cada hipótesis la categoría **caso/control/otro/no evaluable** en la misma ancla; **NO se calcularon precios futuros, trades, SL/TP, P&L, IC90, p, q, PF, DD, incremento de cartera o ROI**. `N casos` es número de **sesiones con esa clasificación**, NO observaciones independientes inferidas ni transacciones monetarias. No declarar edge probado.
- [Workflow](../../.github/workflows/nq-t20-t25-controlled-fixed-anchor-stage0.yml), [motor](../../local_nq_tick_2025_2026/nq_t20_t25_fixed_anchor_screen.py), [agregador fail-closed](../../local_nq_tick_2025_2026/nq_t20_t25_stage0_aggregate.py), [tests sintéticos](../../local_nq_tick_2025_2026/test_nq_t20_t25_fixed_anchor.py). Resultado auditado en log del job `aggregate` de Action, con agregado de 7 artefactos mensuales. El artifact incluye `summary.json`/`report.md` y solapamiento caso-caso sin exponer filas Last.

## Hallazgo clave: tres comparaciones viables como diseño, NINGUNA estrategia aún validada

| ID | Pregunta falsable resumida | N casos | N controles | Caso + control | Diagnóstico de identificabilidad descriptiva | N trades | IC90 / q BH / Holm | ¿Cumple estadística/economía? |
|---|---|---:|---:|---:|---|---|---|---|
| **T20** | VWAP extremo vs centrado dentro de barra | **0** | 100 | 100 | **NO: 0 casos**, umbral congelado sin ajustar | N/D | N/D | NO EVALUABLE |
| **T21** | Rechazo de máximo/mínimo vs aceptación | **38** | 40 | 78 | **Sí: ambos grupos observables; asociación aún no medida** | N/D | N/D | NO EVALUABLE |
| **T22** | Qty/print alto **con avance** vs normal | **1** | 113 | 114 | Ambos grupos existen, **N caso=1 insuficiente** | N/D | N/D | NO EVALUABLE |
| **T23** | Desaceleración vs cadencia estable | **1** | 8 | 9 | Ambos existen, **N caso=1 y control=8 insuficientes** | N/D | N/D | NO EVALUABLE |
| **T24** | Alternancia de VWAP vs continuidad | **39** | 50 | 89 | **Sí: ambos grupos observables; efecto no medido** | N/D | N/D | NO EVALUABLE |
| **T25** | Contradicción 233/4181 vs alineación | **47** | 59 | 106 | **Sí: ambos grupos observables; efecto no medido** | N/D | N/D | NO EVALUABLE |

En todo caso T21/T24/T25 siguen **N por debajo del criterio exploratorio >150 eventos independientes** y se han seleccionado preguntas después de investigación adaptativa previa. La comparación de controles no implica independencia, ventaja monetaria ni justificación de fondeo.

## Conteos por mes auditados en logs (casos / controles)
| Mes DEV | Fuente | Elegible | Ancla | T20 | T21 | T22 | T23 | T24 | T25 |
|---|---:|---:|---:|---|---|---|---|---|---|
| 2025-10 | 13 | 13 | 13 | 0/8 | 4/3 | 0/11 | 0/1 | 4/4 | 6/3 |
| 2025-11 | 20 | 19 | 19 | 0/13 | 5/5 | 1/12 | 0/0 | 4/6 | 8/6 |
| 2025-12 | 22 | 21 | 21 | 0/17 | 6/6 | 0/18 | 0/4 | 7/7 | 5/10 |
| 2026-01 | 21 | 21 | 21 | 0/16 | 5/7 | 0/17 | 1/0 | 4/8 | 4/13 |
| 2026-02 | 20 | 20 | 20 | 0/17 | 6/4 | 0/18 | 0/1 | 9/6 | 8/9 |
| 2026-03 | 22 | 21 | 21 | 0/14 | 7/6 | 0/18 | 0/0 | 3/13 | 9/9 |
| 2026-04 | 22 | 20 | 20 | 0/15 | 5/9 | 0/19 | 0/2 | 8/6 | 7/9 |
| **TOTAL** | **140** | **135** | **135** | **0/100** | **38/40** | **1/113** | **1/8** | **39/50** | **47/59** |

## Decisión y siguiente bloque
- **Etapa 0 T20–T25 COMPLETADA técnicamente, sin aprobar rentabilidad.** Conservar seis condiciones originales incluso fallidas: **T20 cero**, **T22/T23 casi sin casos**. Sin bajar umbrales para rescatarlas.
- T21, T24 y T25 permiten una nueva fase **de medición económica/predictiva de seis miembros sin escoger ganadoras**; si se hace, congelar un protocolo separado de endpoints y direcciones, controles comparables, efecto neto estrés+$10RT, ejecución intratimestamp, tiempo de holding, cuenta/router T05, bootstrap por sesiones 3/5/10, familia de seis BH, Holm/OOS por separado. T23 solo pregunta de **rango futuro**, no entrada ficticia long/short. Incluso si alguno arroja neto positivo, la muestra es muy corta y adaptativamente explorada.
- Mantener B06/B07/OOS/fondeo BLOQUEADOS: ningún retorno o PF T20–T25 existe aún. Próximo backlog: **NQ-T20–T25 FASE 1: preregistro de outcomes y ejecución económica/predictiva de la familia completa** si no compromete reglas existentes. No adquirir data nueva, abrir H/T sellados ni modificar T05/T14–T19.
