# NQ — D1 económica completa T133–T168 (36 estrategias)

**Evaluación cerrada, 12-oct-2026**. [Action 38326216082 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38326216082) · [artefacto seguro 11781138134](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38326216082/artifacts/11781138134) SHA256 `aa587d6edfc5f3ec19dcda527ba4452fda15828c59d6477198121f481acb67af`. El artefacto contiene `report.md` con las **36 filas completas** y `summary.json` con medidas exactas por ID, costos, IC90, p/q, PF/DD, temporalidad y frecuencia. Sin archivos Last ni datos de operación individual publicados.

**Fuente 140 sesiones, 135 READY, 7/7 meses DEV existentes**. D0 familiar ya cerrado **36 inscritas→29 TESTABLE→27 distintas**; las mismas 36 etiquetas D0 se cotejaron EXACTAS antes de inferir retornos. [D0 completo](NQ_T133_T168_FULL36_EXECUTABLE_D0_RESULTS_2026_10_12.md). [Prerregistro D1 ex ante](NQ_T133_T168_36_MEMBER_ECONOMIC_D1_PREREG_2026_10_12.md).

## Decisión del embudo económico

| Resultado D1 k36 | Cantidad |
|---|---:|
| NETO NO RESPALDADO (simulación neta negativa) | 26 |
| INCONCLUSIVE_OR_GATE_FAIL (neto positivo, otros requisitos incumplidos) | 5 |
| NOT_ESTIMABLE_LOW_PROXY_FREQUENCY (menos de 15 trades) | 5 |
| **Pasan todos los filtros, incluido BH36** | **0** |

La **q BH36 mínima=1,000**; **0 IC90 L5 del beneficio diario enteramente positivos**. No hay supervivientes económicos. Los cinco insuficientes son T134/T138/T139/T143/T144, y se mantienen en el universo familiar sin inventar p/q.

| Ejemplo | N operaciones simuladas | Neto base teórico | PF teórico | Problema que impide avanzar |
|---|---:|---:|---:|---|
| **T133** | 52 | +US$606,75 | 1,178 | Pérdida neta enero–abril; CI incluye cero; q=1 |
| **T145** | 51 | +US$788,00 | 1,238 | PF inferior al gate 1,25; CI incluye cero; q=1 |
| **T147** | 20 | +US$642,25 | 1,499 | Pérdida neta Q4 2025; CI incluye cero; q=1 |
| T134 | 14 | +US$846,50 | 2,153 | N<15: IC90/p/q individuales N/D |

**Advertencia metodológica obligatoria:** estos dólares son **P&L DE UN MODELO PROXY**, no fills reales ni beneficios obtenidos. Entrada simulada en peor precio Last de grupo atómico siguiente +2 ticks adversos, salida +2 ticks adversos, stop primero en timestamp ambiguo, cargos round-trip SUPUESTOS NQ US$4/MNQ US$1,50, riesgo nominal ≤US$250 y estrés 1,5× costos / +US$10 RT. Sin Bid/Ask negociable, prioridad ni tarifa verificada de bróker. Bootstrap por día no circular B=10.000 L5 (L3/L10 sensibilidad), BH completa 36. Los meses oct–dic 2025 y ene–abr 2026 fueron previamente explorados y **NO son OOS**.

**D2 permanece VACÍA**. No sumar P&L de las 36 reglas solapadas como si fueran una cartera. No abrir mayo–septiembre 2026 ni comprar nuevas series por inercia. Con esta DEV, recomendamos auditar costos y ejecución verificables o reconsiderar el diseño de investigación antes de multiplicar pruebas.
