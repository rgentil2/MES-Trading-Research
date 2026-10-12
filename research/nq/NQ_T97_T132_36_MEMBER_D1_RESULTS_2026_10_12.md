# NQ T97–T132 — D1 COMPLETO DE LA FAMILIA k=36, resultado no aprobatorio

**12-oct-2026.** [GitHub Action 38318511015 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38318511015) · [artefacto agregado SEGURO 11777853779](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38318511015/artifacts/11777853779), digest SHA256 `04feccb80476d4dd939c9d06b79a356633113e2d064ccb269f5a07c9d2ac5d8f`. [D1 prorregistrado ANTES del D0](NQ_T97_T132_D1_WHOLE_COHORT_PREREG_2026_10_12.md), commit `060c3f03e7c45639a1373e55aaa2bc71023f389d`; [D0 prueba de amplitud 36→30→26](NQ_T97_T132_SIX_BLOCKS_D0_RESULTS_2026_10_12.md) y [conteos congelados por ID](NQ_T97_T132_D0_FROZEN_COUNTS_2026_10_12.json). Fuentes LAST DEV preexistentes 7/7 meses, **140 fuente / 135 READY**, checksum original validado, limpieza de vectores diarios privados y archivos Last al terminar. El artifact contiene únicamente el agregado seguro `report.md/summary.json`, sin sesión individual ni ticks.

## Resultado real: corte por familia COMPLETA, no hipótesis aislada

**q-BH36 mínima = 0,263973602639736**, por encima del gate exploratorio q≤0,10; **0/36 candidatas pasan**, aun cuando **7/36 tienen IC90 L5 individual favorable**: T100, T103, T108, T111, T112, T119, T130. En particular **T112** (barrera de 233 prints): N CASE39 / CTRL96, delta **+69,985 ticks de PRECIO NQ** y **IC90 L5 [+23,592;+122,477]**, p unilateral 0,0132, pero **q-BH36 0,264**, no apta para avanzar. No se invierte la dirección para 'rescatar' hipótesis.

**Resumen de los 36:** 24 `INCONCLUSIVE`, 6 `NOT_SUPPORTED` (signo desfavorable), 6 `NOT_ESTIMABLE` (T110, T125, T127, T128, T129, T132). Las 36 entraron en BH36, incluidas no evaluables y duplicadas de D0 (T102/T114/T115/T120); para las no estimables se usa sentinel p=1 solo durante BH, sin inventar su p/IC90/q propia. Las asociaciones en DEV reutilizada son **EXPLORATORIAS**, no Holm confirmatorio ni OOS.

Endpoint: `sign(VWAP_q(E377)−VWAP_q(D377)) × [VWAP_q(primer grupo entero estrictamente después E.end+300 s) − VWAP_q(E377)]`; **Δ media CASE−media CONTROL**, unidades TICKS NQ, no USD ni ejecución de cuenta. Bootstrap moving block no circular **B10.000, L5 primario**, sensibilidad L3/L10 en `summary.json` seguro. Si CASE/CTRL n<15, inferencia N/D y no se promueve.

| ID | Mecanismo | CASE / CTRL | Δ ticks | IC90 L5 | p / q-BH36 (exploratorias) | Estado D1 |
|---|---|---:|---:|---|---|---|
| T97 | B12_MICRO_233 | 115/20 | +24.014 | [-16.050, +61.335] | 0.127 / 0.305 | INCONCLUSIVE |
| T98 | B12_MICRO_233 | 117/18 | -19.682 | [-69.138, +29.395] | 0.756 / 1.000 | NOT_SUPPORTED |
| T99 | B12_MICRO_233 | 101/33 | +48.410 | [-1.336, +95.132] | 0.044 / 0.264 | INCONCLUSIVE |
| T100 | B12_MICRO_233 | 88/47 | +60.770 | [+16.683, +110.483] | 0.022 / 0.264 | INCONCLUSIVE |
| T101 | B12_MICRO_233 | 109/22 | -34.175 | [-95.174, +23.270] | 0.815 / 1.000 | NOT_SUPPORTED |
| T102 | B12_MICRO_233 | 107/24 | +12.037 | [-32.380, +54.085] | 0.322 / 0.511 | INCONCLUSIVE |
| T103 | B13_MACRO_4181 | 69/64 | +33.047 | [+2.899, +69.795] | 0.071 / 0.291 | INCONCLUSIVE |
| T104 | B13_MACRO_4181 | 75/60 | +33.679 | [-8.446, +76.565] | 0.097 / 0.291 | INCONCLUSIVE |
| T105 | B13_MACRO_4181 | 48/87 | -24.112 | [-70.714, +22.677] | 0.813 / 1.000 | NOT_SUPPORTED |
| T106 | B13_MACRO_4181 | 67/65 | +20.255 | [-15.024, +62.140] | 0.228 / 0.431 | INCONCLUSIVE |
| T107 | B13_MACRO_4181 | 67/65 | +16.681 | [-12.543, +52.622] | 0.241 / 0.434 | INCONCLUSIVE |
| T108 | B13_MACRO_4181 | 69/64 | +55.349 | [+18.812, +102.849] | 0.026 / 0.264 | INCONCLUSIVE |
| T109 | B14_CROSS_BARRIER | 58/77 | +38.114 | [-5.287, +88.081] | 0.108 / 0.299 | INCONCLUSIVE |
| T110 | B14_CROSS_BARRIER | 14/120 | +67.125 | N/D | N/D / N/D | NOT_ESTIMABLE |
| T111 | B14_CROSS_BARRIER | 57/76 | +60.348 | [+11.545, +115.838] | 0.035 / 0.264 | INCONCLUSIVE |
| T112 | B14_CROSS_BARRIER | 39/96 | +69.985 | [+23.592, +122.477] | 0.013 / 0.264 | INCONCLUSIVE |
| T113 | B14_CROSS_BARRIER | 40/95 | +39.779 | [-9.844, +93.973] | 0.116 / 0.299 | INCONCLUSIVE |
| T114 | B14_CROSS_BARRIER | 92/43 | +29.745 | [-19.452, +81.465] | 0.179 / 0.372 | INCONCLUSIVE |
| T115 | B15_RETEST_LOCATION | 120/15 | +50.941 | [-2.743, +98.022] | 0.039 / 0.264 | INCONCLUSIVE |
| T116 | B15_RETEST_LOCATION | 89/46 | +27.047 | [-22.006, +74.765] | 0.171 / 0.372 | INCONCLUSIVE |
| T117 | B15_RETEST_LOCATION | 90/45 | +13.969 | [-40.149, +67.984] | 0.352 / 0.529 | INCONCLUSIVE |
| T118 | B15_RETEST_LOCATION | 88/47 | +21.069 | [-25.872, +73.416] | 0.281 / 0.481 | INCONCLUSIVE |
| T119 | B15_RETEST_LOCATION | 105/29 | +45.875 | [+0.405, +101.895] | 0.089 / 0.291 | INCONCLUSIVE |
| T120 | B15_RETEST_LOCATION | 92/43 | +45.023 | [-3.571, +91.443] | 0.056 / 0.287 | INCONCLUSIVE |
| T121 | B16_PACE_CONTRACTION | 74/60 | +8.601 | [-36.157, +46.117] | 0.326 / 0.511 | INCONCLUSIVE |
| T122 | B16_PACE_CONTRACTION | 108/27 | +16.219 | [-21.956, +47.567] | 0.186 / 0.372 | INCONCLUSIVE |
| T123 | B16_PACE_CONTRACTION | 43/91 | -42.888 | [-85.423, -9.113] | 0.951 / 1.000 | NOT_SUPPORTED |
| T124 | B16_PACE_CONTRACTION | 63/69 | -5.846 | [-44.830, +31.333] | 0.576 / 0.830 | NOT_SUPPORTED |
| T125 | B16_PACE_CONTRACTION | 135/0 | N/D | N/D | N/D / N/D | NOT_ESTIMABLE |
| T126 | B16_PACE_CONTRACTION | 118/17 | -16.908 | [-67.851, +22.933] | 0.694 / 0.961 | NOT_SUPPORTED |
| T127 | B17_CONSENSUS_INTERACTION | 61/9 | +13.920 | N/D | N/D / N/D | NOT_ESTIMABLE |
| T128 | B17_CONSENSUS_INTERACTION | 76/14 | +31.011 | N/D | N/D / N/D | NOT_ESTIMABLE |
| T129 | B17_CONSENSUS_INTERACTION | 62/13 | +15.778 | N/D | N/D / N/D | NOT_ESTIMABLE |
| T130 | B17_CONSENSUS_INTERACTION | 36/30 | +47.159 | [+4.052, +100.909] | 0.076 / 0.291 | INCONCLUSIVE |
| T131 | B17_CONSENSUS_INTERACTION | 49/31 | +47.788 | [-1.282, +106.478] | 0.092 / 0.291 | INCONCLUSIVE |
| T132 | B17_CONSENSUS_INTERACTION | 63/9 | +57.797 | N/D | N/D / N/D | NOT_ESTIMABLE |

## Decisión del embudo

**C97–132: 36 preregistradas →30 D0 TESTABLE →26 D0 distintas →36 D1 evaluadas →0 filtros estadísticos aprobados →0 D2.** No se estudia T112 ni T100 por separado ni se juntan las siete señales individuales favorables de forma retrospectiva para obtener un sistema.

**N_trades=0; fill/orden ejecutable, costos, PnL neto, PF, DD, margen de cartera, ROI, Holm y OOS=N/D.** No interpretar markout VWAP firmado como ganancia comercial: Last no asegura precio de orden, bid/ask, prioridad ni slippage. No se adquirieron otros datos ni se abrieron holdouts; no hay estrategia monetizable confirmada. Las preguntas deben evolucionar en una **cohorte posterior y diferente**, sin retunear umbrales de las fallidas.

[Motor D1](../../local_nq_tick_2025_2026/nq_t97_t132_d1_batch.py) · [Action](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38318511015) · [política de cohortes](NQ_COHORT_FUNNEL_POLICY_2026_10_12.md)
