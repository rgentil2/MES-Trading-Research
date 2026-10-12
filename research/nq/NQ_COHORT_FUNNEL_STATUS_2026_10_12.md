# NQ — Tablero del embudo por COHORTES

**Control de flujo:** unidad operativa = BLOQUE COMPLETO. D1 nueva exige ≥20 candidatas D0 diversas, y el universo BH sigue incluyendo todos los miembros prerregistrados.

| Cohorte | D0: registradas → testables → diversas | D1: medidas → selección familiar | D2: calificadas | Estado |
|---|---:|---:|---:|---|
| NQ-C29-58 | 30 → 27 → 25 | 30 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C20-25 | 6 → 3 → N/D (legacy) | 6 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C26-28 | 3 → 1 → N/D (legacy) | 3 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C59-NEXT | 2 → 1 → 1 | 0 → 0 | 0 | **ESPERA:** completar bloque D0 |

## Cuello de botella actual

- **Candidatas viables y diversas acumuladas en NUEVA cohorte:** **1 / 20**. Faltan **19**; T59 viable (45 CASE/42 CONTROL), T60 LOW_POWER (71/6).
- **T29–T58 ya cerró D1:** 30 medidas; T29/T45/T49 tienen IC90 individuales de RANGO futuro favorable, pero q-BH mínima 0,212229; **0/30 pasan filtro**. Los tres quedan como variables contextuales NO monetarias, NO entrada D2.
- **T26–T28:** D1 cerrada, T26 signo contrario; T27/28 no estimables. **T20–T25:** D1 predictiva cerrada, economía no ejecutable por fills ambiguos.
- **Bandeja D2:** **0** candidatas agrupadas de mínimo 2 mecanismos distintos; **vacía** hasta superar D1 y comprobar ruta de ejecución. No saltar desde D0 a riesgo/fondeo.

## Próximo trabajo (no repetir señales individuales)

1. **Solo cohorte siguiente D0:** prerregistrar nuevos bloques de preguntas verdaderamente distintas que se añadan al inventario T59; jamás relajar ratios T59/T60 por N observado.
2. Cuando existan ≥20 D0 TESTABLE distintas, congelar y ejecutar D1 de la familia NUEVA COMPLETA, con endpoints y denominador BH establecidos antes de ver retorno. Evaluar TODOS los miembros y documentar descartar/fallar.
3. Agrupar en bandeja POST-D1 sobrevivientes de TODAS las cohortes; esperar grupo ejecutable plural para D2 con UNA cuenta, costos/riesgo y DeltaRouter neto. Confirmación/OOS solo bajo autorización independiente.

**T05-377:** benchmark histórico congelado, NO integrante de cohorte D2, ni prueba de renta fondeable. H69/H74/H77 no portables con Last 08–12 sin cierre RTH del día previo ni ATR de sesión completa.

**Evidencia D0/D1:** [T29–T58 D0](NQ_T29_T58_30_HYPOTHESES_G0_D0_RESULTS_2026_10_12.md) · [T29–T58 D1](NQ_T29_T58_30_HYPOTHESES_D1_BATCH_RESULTS_2026_10_12.md) · [T26–T28 D1](NQ_T26_T28_D1_OBSERVATIONAL_RESULTS_2026_10_12.md) · [T59–T60 D0](NQ_T59_T60_NEW_PREMARKET_D0_RESULTS_2026_10_12.md).

Esta fotografía se genera SOLO desde el ledger agregado; no abre ni recuenta datos de mercado, no ejecuta trades ni abre holdouts.
