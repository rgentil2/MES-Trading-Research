# NQ — Tablero del embudo por COHORTES

**Control de flujo:** unidad operativa = BLOQUE COMPLETO. D1 nueva exige ≥20 candidatas D0 diversas, y el universo BH sigue incluyendo todos los miembros prerregistrados.

| Cohorte | D0: registradas → testables → diversas | D1: medidas → selección familiar | D2: calificadas | Estado |
|---|---:|---:|---:|---|
| NQ-C29-58 | 30 → 27 → 25 | 30 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C20-25 | 6 → 3 → N/D (legacy) | 6 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C26-28 | 3 → 1 → N/D (legacy) | 3 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C59-NEXT | 38 → 36 → 31 | 38 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C97-132 | 36 → 30 → 26 | 36 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C133-168 | 36 → 29 → 27 | 0 → 0 | 0 | **D1 en ejecución (SIN RESULTADOS AÚN)** |

## Estado del NUEVO EMBUDO ECONÓMICO de 36 miembros T133–T168

- **Ocho bloques de estrategias completas**, 20 T133–T152 originales INMUTABLES +16 T153–T168 prerregistradas. **D0: 36 registradas → 29 TESTABLE → 27 diversas**; **gate D1 de >=20 CUMPLIDO**. Auditoría de las 20 etiquetas originales reproducida exactamente; seven DEV 140/135.
- **Siete bajas N:** T134/T138/T139/T143/T144/T153/T154. Duplicados de CASE: T150≈T158 (Jaccard 1,0), T164≈T163 (0,951456). Se conservaron los 36 ID para la familia estadística D1.
- **D1 económica experimental:** protocolo prospectivo de market PROXY adverso, stop-first ante timestamps simultáneos, 2 ticks entrada y salida, fees hipotéticas NQ/MNQ, estrés 1,5x y +US$10 RT, 10k bootstrap BH36. El motor D1 no verifica llenados reales de bróker.
- **Estado actual D1:** RUNNING_FULL36_ECONOMIC_PROXY_UNVERIFIED ([Action 38326216082]) sin resultados monetarios declarados antes de revisión. La cola D2 permanece vacía hasta verificaciones económicas y OOS.
- **Cortes cronológicos DEV:** oct–dic2025 53 READY, ene–abr2026 82 READY; periodos previamente explorados y NO OOS nuevo. Nunca abrir mayo–septiembre 2026.
- **Cohortes históricas T29–T58/T59–T96/T97–T132:** 104 D1 físicas/observacionales en bloques, 0 superaron BH de sus familias. T05 se mantiene baseline congelado.

**Fuentes:** [D0 36 completos](NQ_T133_T168_FULL36_EXECUTABLE_D0_RESULTS_2026_10_12.md) · [Costos/ejecución D1 prereg](NQ_T133_T168_36_MEMBER_ECONOMIC_D1_PREREG_2026_10_12.md) · [Código de pruebas](../../local_nq_tick_2025_2026/nq_t133_t168_economic_d1_batch.py).

Esta fotografía solo lee ledger agregado; no consulta mercado ni trade-by-trade privado.
