# NQ T133–T168 — D1 ECONÓMICA de los 36 miembros, únicamente simulación Last

**Ejecución 38326216082 COMPLETED SUCCESS**, [Action](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38326216082), [artifact seguro 11781138134](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38326216082/artifacts/11781138134) SHA256 `aa587d6edfc5f3ec19dcda527ba4452fda15828c59d6477198121f481acb67af`. Solo report.md y summary.json agregados; raw Last y vectores por sesión privados borrados. 140 sesiones fuente, 135 elegibles, siete meses DEV oct2025–abr2026. [Prerregistro económico prospectivo](NQ_T133_T168_36_MEMBER_ECONOMIC_D1_PREREG_2026_10_12.md) commit `8d03615c78536cd0271bfab96b053071039a9f50`, ANTES de resultados y [D0 congelado 36→29→27](NQ_T133_T168_36_MEMBER_D0_FROZEN_COUNTS_2026_10_12.json). Las 36 máscaras CASE/CONTROL/OTHER/NO EVAL fueron cotejadas de nuevo contra D0.

**D1 k36: 26 NOT_SUPPORTED_NET, 5 INCONCLUSIVE_OR_GATE_FAIL, 5 NOT_ESTIMABLE_LOW_PROXY_FREQUENCY, 0 PASS.** Mínima q-BH36 **1,00** entre los estimables; D2=0. Para 5 de N bajo (T134/T138/T139/T143/T144), IC90/p/q=N/D, pero todos 36 cuentan en corrección BH mediante sentinel p=1. Los siete D0 low-power permanecen (T153/T154 tienen muchos trades proxy pero casi ningún CONTROL y por tanto NO se consideran testable en D0).

**Reglas del MODELO, NO hechos de bróker:** entrada sobre peor Last del siguiente grupo timestamp atómico +2 ticks adversos; stop primero ante timestamps simultáneos, +2 ticks salida; NQ valor tick $5 y fee supuesta $4 RT, MNQ $0,50/tick y fee $1,50 RT; estrés de fricción 1,5× y +$10 RT; TP congelado por familia 1,25–2R; horizonte 15/30min; stop dist 8–400 ticks/riesgo nominal hasta $250; IC90 moving-block 10.000 L5 por días, sensibilidad L3/L10. Oct–dic2025 y ene–abr2026 son DEV reexaminada, NO un OOS nuevo. Todo PnL, PF y DD es exclusivamente del MODELO y no de operaciones llenadas por el bróker.

| ID | Mecanismo | Trades proxy | Neto modelo USD | PF modelo | DD modelo USD | IC90 L5 diario USD | qBH36 | D1 |
|---|---|---:|---:|---:|---:|---|---:|---|
| T133 | A | 52 | $+606.75 | 1.18 | $814.00 | [-9.25,+19.68] | 1.00 | INCONCLUSIVE |
| T134 | A | 14 | $+846.50 | 2.15 | $280.50 | N/D | N/D | LOW_N |
| T135 | A | 56 | $+93.75 | 1.03 | $1357.00 | [-14.95,+15.87] | 1.00 | INCONCLUSIVE |
| T136 | A | 36 | $-147.00 | 0.95 | $1065.25 | [-14.36,+12.32] | 1.00 | NEG_NET |
| T137 | A | 38 | $+139.25 | 1.05 | $1013.00 | [-11.63,+12.96] | 1.00 | INCONCLUSIVE |
| T138 | B | 5 | $+267.50 | 2.68 | $88.50 | N/D | N/D | LOW_N |
| T139 | B | 3 | $+20.00 | 1.16 | $124.50 | N/D | N/D | LOW_N |
| T140 | B | 59 | $-1802.00 | 0.69 | $2756.00 | [-33.57,+6.79] | 1.00 | NEG_NET |
| T141 | B | 72 | $-2219.50 | 0.68 | $3203.50 | [-38.37,+6.53] | 1.00 | NEG_NET |
| T142 | B | 17 | $-521.00 | 0.62 | $525.50 | [-11.49,+4.57] | 1.00 | NEG_NET |
| T143 | C | 8 | $+330.75 | 2.43 | $144.00 | N/D | N/D | LOW_N |
| T144 | C | 5 | $+225.00 | 1.68 | $333.00 | N/D | N/D | LOW_N |
| T145 | C | 51 | $+788.00 | 1.24 | $614.50 | [-8.58,+20.60] | 1.00 | INCONCLUSIVE |
| T146 | C | 32 | $-750.50 | 0.68 | $1191.25 | [-16.65,+3.38] | 1.00 | NEG_NET |
| T147 | C | 20 | $+642.25 | 1.50 | $567.00 | [-3.68,+13.29] | 1.00 | INCONCLUSIVE |
| T148 | D | 101 | $-2354.25 | 0.69 | $3291.00 | [-35.94,-1.16] | 1.00 | NEG_NET |
| T149 | D | 58 | $-217.00 | 0.94 | $1301.25 | [-13.89,+10.68] | 1.00 | NEG_NET |
| T150 | D | 72 | $-1453.50 | 0.76 | $2800.00 | [-28.49,+6.55] | 1.00 | NEG_NET |
| T151 | D | 93 | $-1290.00 | 0.79 | $2546.75 | [-26.76,+7.25] | 1.00 | NEG_NET |
| T152 | D | 28 | $-1715.75 | 0.34 | $1715.75 | [-19.40,-5.43] | 1.00 | NEG_NET |
| T153 | E | 86 | $-921.75 | 0.86 | $1537.50 | [-27.26,+15.13] | 1.00 | NEG_NET |
| T154 | E | 87 | $-1933.00 | 0.72 | $2460.75 | [-34.39,+7.11] | 1.00 | NEG_NET |
| T155 | E | 34 | $-1036.00 | 0.61 | $1443.00 | [-18.35,+3.95] | 1.00 | NEG_NET |
| T156 | E | 72 | $-1803.75 | 0.71 | $2299.75 | [-28.00,+6.33] | 1.00 | NEG_NET |
| T157 | F | 61 | $-902.25 | 0.76 | $1435.25 | [-18.25,+4.32] | 1.00 | NEG_NET |
| T158 | F | 72 | $-1453.50 | 0.76 | $2800.00 | [-28.54,+6.38] | 1.00 | NEG_NET |
| T159 | F | 71 | $-1493.75 | 0.73 | $2090.50 | [-25.57,+2.98] | 1.00 | NEG_NET |
| T160 | F | 62 | $-589.50 | 0.87 | $1945.75 | [-21.85,+11.31] | 1.00 | NEG_NET |
| T161 | G | 80 | $-2269.50 | 0.66 | $3196.50 | [-33.77,-0.81] | 1.00 | NEG_NET |
| T162 | G | 79 | $-1217.50 | 0.81 | $2807.25 | [-25.77,+8.34] | 1.00 | NEG_NET |
| T163 | G | 101 | $-1897.50 | 0.76 | $3561.25 | [-34.37,+6.69] | 1.00 | NEG_NET |
| T164 | G | 98 | $-1580.50 | 0.79 | $3359.25 | [-31.19,+8.94] | 1.00 | NEG_NET |
| T165 | H | 61 | $-2653.00 | 0.48 | $3031.50 | [-34.76,-5.44] | 1.00 | NEG_NET |
| T166 | H | 65 | $-2003.00 | 0.58 | $2538.00 | [-29.83,-1.60] | 1.00 | NEG_NET |
| T167 | H | 43 | $-927.00 | 0.71 | $1109.50 | [-17.43,+2.60] | 1.00 | NEG_NET |
| T168 | H | 93 | $-1490.00 | 0.78 | $2620.25 | [-28.60,+6.58] | 1.00 | NEG_NET |

## Ejemplos que descartan una promoción selectiva

**T147:** 20 trades proxy, neto +US$642,25, PF1,499; **IC90 L5 [-US$3,68;+US$13,29] por día** y qBH36=1,00; en octubre–diciembre 2025 perdió **US$567**, compensado por +US$1.209,25 en enero–abril 2026. No pasa robustez por ambos segmentos.

**T145:** 51 trades proxy, +US$788 neto, PF1,238 inferior al mínimo1,25, IC90 L5 [-US$8,58;+US$20,60] y qBH36=1,00. Concentración en un mes favorable ~45,4%, superior al 40% preregistrado. NO PASS.

**T133:** 52 trades proxy, +US$606,75, PF1,178, IC90 L5 [-US$9,25;+US$19,68], Q4 +US$724,25 contra ene–abr -US$117,50. NO PASS.

**T134:** 14 trades proxy, +US$846,50, PF2,15 pero muestra insuficiente para inferencia; D0 low-power (14 CASE /121 CONTROL), IC90/p/q=N/D. No rescatar.

**T140/T141** de pullbacks: 59 y 72 trades proxy, netos **-US$1.802 y -US$2.219,50**, PF0,69/0,68, DD alto. Frecuencia elevada NO implica ventaja.

## Veredicto

**Ninguna candidata cumple los gates económicos/estadísticos de D1.** No se evalúa D2 ni una cartera, no se abre un holdout sellado ni se hacen afirmaciones de ROI, alpha o fills reales. Los resultados son desfavorables **bajo este protocolo específico de fricción y ejecución modelada**, no prueban imposibilidad de cualquier ventaja NQ. Cualquier futura cohorte debe justificar mecanismos nuevos sin reciclar selectivamente los positivos ni ampliar tests indefinidamente sobre estas 135 sesiones.
