# T169–T188 — cierre monetario V3 de cuatro bloques (13-oct-2026)

**Evidencia efectiva:** [GitHub Action 38350552598 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38350552598), [artefacto SAFE 11790253664](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38350552598/artifacts/11790253664), ZIP SHA256 `68a27cc5f9536faedb75b2088eb6b132496cecddaf99b7fa580084045be9ea6a`. 7 pruebas sintéticas PASS, siete meses DEV de oct2025 a abr2026 SUCCESS, agregado SUCCESS, muestra 140 fuente/135 READY, T05 115 operaciones, US$5.102,50 estrés, US$3.952,50 estrés+$10 RT, Last DD US$1.797,50 reproducidos EXACTOS. **No son fills reales** ni salida habilitada a fondeo. Holdouts T mayo–sept 2026/H no abiertos, ni datos nuevos, ni señales nuevas sobre 5s.

**Antecedentes obligatorios:** [V1 falló por ventanas fuera del simulador](NQ_T169_T188_MONETARY_BLOCKS_V2_EXECUTION_COMPATIBILITY_2026_10_13.md) Action [38350008027](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38350008027), [V2 terminó seis meses pero abril falló por exposición ambigua](NQ_T169_T188_V3_FAIL_CLOSED_AMBIGUOUS_EXPOSURE_2026_10_13.md) Action [38350174954](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38350174954). La V3 **censura** exposiciones intratimestamp que no puede reconstruir, sin imputar ganancia, pérdida ni cero. Esta enmienda es posterior a seis jobs DEV; no produce una nueva muestra OOS. **T176** quedó no estimable en ambos modelos (sola y router) de los siete meses, sin PnL/PF/DD asignado. **Ninguna estrategia pasó la pantalla monetaria exploratoria**.

**Gates monetarios del router por cada candidata (todas las condiciones):** delta neto T05+alternativa vs T05 bajo estrés+$10 RT >US$0; PF router con estrés y con extra$10 RT ≥1,25; drawdown envolvente Last ≤US$2.000 (referencia NO verificada de fondeo); ≥104 de 115 operaciones T05 conservadas; ≥5 operaciones del router cada mes; nueva estrategia ejecutada al menos una vez. Las 20 candidatas deben figurar incluidas aunque sean N/D. Los routers de 20 filas son 20 simulaciones de UNA cuenta por separado, **no una cartera de 20 operaciones concurrentes**.

## Bloque A: 09:40–10:00 (VERSIÓN V2, NO premercado) ET — 0/5 PASS; 0 N/D

| ID | N operaciones sola | Incremento router estrés+$10 RT, USD | PF router+$10 | DD Last estrés, USD | Resultado |
|---|---:|---:|---:|---:|---|
| T169 | 76 | -5.147,50 | 0,94 | 3.267,50 | FAIL |
| T170 | 92 | -6.830,00 | 0,88 | 3.460,00 | FAIL |
| T171 | 1 | -147,50 | 1,23 | 1.797,50 | FAIL |
| T172 | 50 | -4.682,50 | 0,97 | 2.260,00 | FAIL |
| T173 | 41 | -2.017,50 | 1,10 | 2.330,00 | FAIL |

## Bloque B: 09:30–09:40 ET — 0/5 PASS; 1 N/D

| ID | N operaciones sola | Incremento router estrés+$10 RT, USD | PF router+$10 | DD Last estrés, USD | Resultado |
|---|---:|---:|---:|---:|---|
| T174 | 115 | -4.192,50 | 0,99 | 2.652,50 | FAIL |
| T175 | 72 | -3.905,00 | 1,00 | 2.372,50 | FAIL |
| T176 | N/D | N/D | N/D | N/D | NO ESTIMABLE |
| T177 | 66 | -2.875,00 | 1,05 | 2.362,50 | FAIL |
| T178 | 40 | -2.312,50 | 1,08 | 2.227,50 | FAIL |

## Bloque C: 10:20–10:40 ET — 0/5 PASS; 0 N/D

| ID | N operaciones sola | Incremento router estrés+$10 RT, USD | PF router+$10 | DD Last estrés, USD | Resultado |
|---|---:|---:|---:|---:|---|
| T179 | 96 | -6.477,50 | 0,90 | 3.875,00 | FAIL |
| T180 | 16 | -640,00 | 1,18 | 2.230,00 | FAIL |
| T181 | 30 | -3.620,00 | 1,02 | 2.070,00 | FAIL |
| T182 | 18 | -445,00 | 1,20 | 1.727,50 | FAIL |
| T183 | 0 | 0,00 | 1,24 | 1.797,50 | FAIL |

## Bloque D: 11:10–11:30 ET — 0/5 PASS; 0 N/D

| ID | N operaciones sola | Incremento router estrés+$10 RT, USD | PF router+$10 | DD Last estrés, USD | Resultado |
|---|---:|---:|---:|---:|---|
| T184 | 53 | -520,00 | 1,17 | 1.850,00 | FAIL |
| T185 | 4 | -330,00 | 1,21 | 1.797,50 | FAIL |
| T186 | 70 | 280,00 | 1,20 | 2.130,00 | FAIL |
| T187 | 0 | 0,00 | 1,24 | 1.797,50 | FAIL |
| T188 | 44 | -382,50 | 1,18 | 2.077,50 | FAIL |

## Lectura financiera y continuidad

- **19 candidatas estimables:** 16 empeoran el PnL incremental del router con +US$10 RT, 2 lo dejan sin cambios (**T183, T187**) y **solo T186** produce mejora **+US$280** sobre T05. T176 no puede estimarse.
- **T186**: modelo standalone 70 operaciones y **−US$970 estrés**; router compartido ejecuta 50 T186, conserva las 115 T05 y mejora **+US$780 estrés** / **+US$280 bajo extra US$10 RT**, pero **PF extra10=1,20198 <1,25** y **DD Last estrés US$2.130 > referencia US$2.000**. **FAIL**, no seleccionar retrospectivamente para operar. El aparente aporte proviene de la selección causal de capacidad/solapamiento con T05, no de ganar en standalone ni de evidencia broker.
- **T184/T188** son ejemplos contrarios: resultado individual standalone estrés +US$337,50/+US$280, pero delta de router estrés+$10 RT −US$520/−US$382,50. **Rentabilidad independiente ≠ aporte económico a T05**.
- No reducir stops, retirar periodos malos, invertir signos ni modificar el DD/PF para rescatar T186. Mantener T05 y V3 congeladas, considerar nuevos mecanismos económicos realmente distintos solo con nuevo prerregistro y evidencia independiente. Formal D1 T133–168 sigue con 0 de 36 aprobadas; D2 formal vacía. Sin OOS ni fondos, los resultados son solo exploratorios.
