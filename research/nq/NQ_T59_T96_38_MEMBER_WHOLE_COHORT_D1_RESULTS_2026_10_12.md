# NQ C59–C96 — D1 FAMILIAR REAL: 38 hipótesis, cero pasan BH38

**12-oct-2026.** [GitHub Action 38313582820 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38313582820) · [artefacto SAFE 11776430223](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38313582820/artifacts/11776430223), digest SHA256 `f4253ceacfad3707fa43185f6e1935ce00794b9eced6f266c16069c73f968e3c`. [Prerregistro BH38 ANTES de futuros](NQ_T59_T96_COHORT_38_D1_PREREG_2026_10_12.md), commit `a8913f2301f5dd1f575c533e084421a9889d6afb`; [D0 del bloque](NQ_T59_T96_SIX_BLOCK_COHORT_D0_RESULTS_2026_10_12.md), 36 TESTABLE y 31 diversas. **7/7 meses NQ Last DEV ya existente, 140 fuente y 135 READY**, privado borrado al terminar. Artefacto con solo `summary.json` y `report.md` agregados, sin markouts por sesión ni datos licenciados.

## Decisión de cuello de botella D1

**Ningún integrante cumple Δ favorable + IC90 inferior positivo + q-BH38 ≤0,10.** **q-BH mínima=0,239376** (T75), por encima del umbral. **7 miembros** muestran IC90 individual L5 enteramente positivo (T65/T75/T84/T88/T93/T94/T95), **pero q familiar NO cumple** en todos ellos; T84 y T88 son cercanas por máscara CASE. **22 inconclusos, 14 de signo desfavorable y 2 no estimables (T60 y T77)**. Descriptivo sobre la misma DEV reutilizada, no Holm ni OOS. No invertir signos posteriores ni filtrar pérdidas.

Los endpoints son **físicos, no fills negociables**: T59 markout firmado VWAP +300s desde 09:45 ET; T60 rango físico 15min desde 09:45; T61–T96 VWAP markout firmado +300s después del fin de barra E377 en [10:00,10:15) ET, side de VWAP E−D. Δ es media CASE−media CONTROL en *ticks de PRECIO NQ*, nunca USD/trade o trades efectivos. Bootstrap moving-block no circular B=10.000, bloque L5 y sensibilidad L3/L10; q BH del universo **38** incluidas dos no estimables con p=1 SOLO para corrección. N efectivo independiente N/D.

| ID | N CASE/CTRL | Δ ticks | IC90 L5 ticks | p exploratoria L5 | q BH38 | Estado D1 |
|---|---:|---:|---|---:|---:|---|
| T59 | 45/42 | 33.126 | [-21.29, 84.49] | 0.1406 | 0.5342 | INCONCLUSIVE |
| T60 | 71/6 | 105.913 | N/D | N/D | N/D | NOT_ESTIMABLE |
| T61 | 72/63 | 18.179 | [-16.90, 54.93] | 0.2246 | 0.6521 | INCONCLUSIVE |
| T62 | 71/64 | -13.099 | [-50.46, 26.25] | 0.7207 | 0.9362 | NOT_SUPPORTED_DESCRIPTIVE |
| T63 | 68/67 | 35.151 | [-7.05, 88.04] | 0.1399 | 0.5342 | INCONCLUSIVE |
| T64 | 64/71 | 16.297 | [-19.09, 59.91] | 0.3089 | 0.6521 | INCONCLUSIVE |
| T65 | 79/56 | 53.224 | [10.99, 96.31] | 0.0202 | 0.2470 | INCONCLUSIVE |
| T66 | 69/66 | -1.716 | [-47.34, 45.44] | 0.5284 | 0.8548 | NOT_SUPPORTED_DESCRIPTIVE |
| T67 | 74/61 | 19.491 | [-27.03, 75.61] | 0.3047 | 0.6521 | INCONCLUSIVE |
| T68 | 93/42 | -14.628 | [-57.21, 33.75] | 0.7348 | 0.9362 | NOT_SUPPORTED_DESCRIPTIVE |
| T69 | 82/53 | 21.990 | [-23.05, 72.18] | 0.2554 | 0.6521 | INCONCLUSIVE |
| T70 | 64/71 | 15.429 | [-27.25, 67.83] | 0.3592 | 0.7183 | INCONCLUSIVE |
| T71 | 89/46 | 5.805 | [-38.94, 54.36] | 0.4452 | 0.8195 | INCONCLUSIVE |
| T72 | 75/60 | 15.616 | [-19.02, 56.06] | 0.2729 | 0.6521 | INCONCLUSIVE |
| T73 | 74/61 | 19.581 | [-11.20, 62.67] | 0.2653 | 0.6521 | INCONCLUSIVE |
| T74 | 60/75 | -4.560 | [-49.39, 38.11] | 0.5556 | 0.8548 | NOT_SUPPORTED_DESCRIPTIVE |
| T75 | 66/69 | 57.201 | [26.23, 95.23] | 0.0063 | 0.2394 | INCONCLUSIVE |
| T76 | 114/18 | 23.198 | [-45.03, 85.04] | 0.2778 | 0.6521 | INCONCLUSIVE |
| T77 | 119/12 | 21.897 | N/D | N/D | N/D | NOT_ESTIMABLE |
| T78 | 102/33 | 2.324 | [-32.73, 50.44] | 0.5830 | 0.8548 | INCONCLUSIVE |
| T79 | 82/52 | -12.368 | [-45.61, 25.87] | 0.7546 | 0.9362 | NOT_SUPPORTED_DESCRIPTIVE |
| T80 | 81/54 | -26.477 | [-67.70, 19.64] | 0.8661 | 0.9680 | NOT_SUPPORTED_DESCRIPTIVE |
| T81 | 80/54 | -14.628 | [-47.08, 27.10] | 0.8005 | 0.9506 | NOT_SUPPORTED_DESCRIPTIVE |
| T82 | 98/37 | -0.223 | [-40.78, 51.78] | 0.5848 | 0.8548 | NOT_SUPPORTED_DESCRIPTIVE |
| T83 | 71/64 | -28.844 | [-71.03, 7.37] | 0.8562 | 0.9680 | NOT_SUPPORTED_DESCRIPTIVE |
| T84 | 94/41 | 65.727 | [18.81, 116.30] | 0.0148 | 0.2470 | INCONCLUSIVE |
| T85 | 94/40 | 16.499 | [-32.39, 64.82] | 0.2928 | 0.6521 | INCONCLUSIVE |
| T86 | 95/40 | -1.359 | [-35.98, 43.73] | 0.6151 | 0.8658 | NOT_SUPPORTED_DESCRIPTIVE |
| T87 | 79/56 | -53.961 | [-91.70, -9.36] | 0.9881 | 1.0000 | NOT_SUPPORTED_DESCRIPTIVE |
| T88 | 96/39 | 65.449 | [16.77, 120.53] | 0.0260 | 0.2470 | INCONCLUSIVE |
| T89 | 80/55 | 39.997 | [-6.21, 89.22] | 0.0912 | 0.4902 | INCONCLUSIVE |
| T90 | 69/66 | -30.087 | [-71.41, 14.82] | 0.8917 | 0.9681 | NOT_SUPPORTED_DESCRIPTIVE |
| T91 | 76/59 | -20.327 | [-66.86, 19.59] | 0.7637 | 0.9362 | NOT_SUPPORTED_DESCRIPTIVE |
| T92 | 63/72 | 1.551 | [-45.00, 45.49] | 0.4529 | 0.8195 | INCONCLUSIVE |
| T93 | 77/57 | 41.005 | [8.66, 81.75] | 0.0493 | 0.3496 | INCONCLUSIVE |
| T94 | 82/53 | 46.388 | [11.63, 93.99] | 0.0552 | 0.3496 | INCONCLUSIVE |
| T95 | 112/22 | 50.283 | [0.38, 114.02] | 0.1032 | 0.4902 | INCONCLUSIVE |
| T96 | 112/20 | -3.041 | [-53.75, 41.44] | 0.4994 | 0.8548 | NOT_SUPPORTED_DESCRIPTIVE |

## Conclusión y transición a D2

**D0:** cohorte de 38 →36 testables →31 distintas, gate≥20 SUPERADO. **D1:** se midieron LOS 38 en conjunto (no 31 seleccionadas) → **0 supervivientes por BH38**, cohorte CERRADA. **D2:** **0** elegibles; no estudiar T75 individualmente ni usar T84/T88 como combinaciones seleccionadas tras ver resultados.

**N trades simulado=0, P&L/PF/DD/costes/DeltaRouter/Holm/ROI/fondeo/OOS no estimados**, sin precio de ejecución verificable. Markout VWAP puede ser favorable sin existir beneficio después de órdenes y fricciones. No comprar data, abrir reservas ni simular ejecuciones ficticias. [Motor D1](../../local_nq_tick_2025_2026/nq_t59_t96_d1_cohort.py) · [workflow CI](../../.github/workflows/nq-t59-t96-full-cohort-38-d1-dev.yml) · [política de embudo](NQ_COHORT_FUNNEL_POLICY_2026_10_12.md).
