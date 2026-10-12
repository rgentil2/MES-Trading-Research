# NQ T29–T58 — RESULTADOS D1 completos de la familia k=30 (NO TRADING)

**12-oct-2026. Ejecución real [Action 38300856124 COMPLETED/SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38300856124).** Siete meses de Last DEV preexistentes y checksum, 140 fuente/135 READY, job sintético **7/7 tests PASS**, siete meses procesados con fuente privada borrada, bootstrap 10.000 bloques no circulares L3/L5/L10 y agregado seguro. [Artifact de resultados 11770745392](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38300856124/artifacts/11770745392), SHA256 ZIP `710d19b99c383f22c43ba7de923ce91a83479269857326a5ca1a98fffedbd989`, con `summary.json/report.md`, verificado y tabulado. [Prerregistro previo al primer outcome](NQ_T29_T58_30_HYPOTHESES_D1_BATCH_PREREG_2026_10_12.md), commit `4a9dc3880441aa59f7e003bcf9f9f38bec1cc7d1`. Sin datos nuevos, sin señales nuevas 5s, sin T/H holdouts, ni orden/fill monetario simulado.

## Resultado ejecutivo del lote, con TODAS las hipótesis

- **D0 previo:** 30 preregistradas, 27 `TESTABLE`, 25 shortlist diversa; gate de amplitud>=20 cumplido. [D0 y pares Jaccard](NQ_T29_T58_30_HYPOTHESES_G0_D0_RESULTS_2026_10_12.md).
- **D1 de 30 familiares:** **3** individuales `PROMISING_PREDICTIVE_IN_SAMPLE_NOT_TRADABLE` (T29, T45, T49), **13** `INCONCLUSIVE`, **11** con diferencias puntuales desfavorables `NOT_SUPPORTED_DESCRIPTIVE`, **3** `NOT_ESTIMABLE` (T48/T50/T51). **Ninguna** alcanza corrección BH familiar exploratoria `q<=0,10`: q mínima **0,2122288**. Este `q` ya sería exploratorio y **no confirmatorio** por repetición de DEV/selección adaptativa: aquí ni siquiera pasa q descriptiva.
- **EndPoints en TICKS del NQ, no USD ejecutables**: B1 geometría y B3/B4/B5 volumen/llegada/topología = diferencia en **rango realizado futuro 15min**, CASE−CONTROL. **B2 contexto** = contraste de VWAP futuro firmado por desplazamiento VWAP D→E, +300s, NQ price ticks; los valores no son comparables como el mismo tipo de retorno y NO se deben sumar como P&L.
- **Banderas de seguridad:** `N_trades=0`, `net_PnL=null`, `PF=null`, `DD=null`, `portfolio_delta=null`, broker fills=no, holdouts abiertos=no, nueva data=no. Holm, 3/5 años y Gate1 independiente N/D. **0/30 estrategias demostradas monetizables o autorizadas a fondeo**.

| ID | Bloque / outcome | N caso/control | Δ ticks | IC90 bilateral L5 (ticks) | p L5 exploratoria | q BH k30 descriptiva | D1 |
|---|---|---:|---:|---|---:|---:|---|
| T29 | B1 rango | 80/31 | 61,96 | [14,43, 114,56] | 0,0252 | 0,2122 | PREDICTIVE_IN_SAMPLE |
| T30 | B1 rango | 44/72 | -24,72 | [-83,20, 29,38] | 0,7639 | 1,0000 | NOT_SUPPORTED |
| T31 | B1 rango | 65/65 | 2,46 | [-47,22, 56,15] | 0,4938 | 0,9258 | INCONCLUSIVE |
| T32 | B1 rango | 85/40 | 52,93 | [-0,10, 98,41] | 0,0283 | 0,2122 | INCONCLUSIVE |
| T33 | B1 rango | 72/59 | 1,17 | [-51,32, 52,10] | 0,4858 | 0,9258 | INCONCLUSIVE |
| T34 | B1 rango | 46/67 | -9,48 | [-60,61, 54,80] | 0,6762 | 1,0000 | NOT_SUPPORTED |
| T35 | B2 dirección | 45/60 | -4,56 | [-52,31, 50,08] | 0,5847 | 1,0000 | NOT_SUPPORTED |
| T36 | B2 dirección | 66/64 | -15,33 | [-58,77, 26,36] | 0,7075 | 1,0000 | NOT_SUPPORTED |
| T37 | B2 dirección | 68/62 | -43,91 | [-83,53, -5,57] | 0,9639 | 1,0000 | NOT_SUPPORTED |
| T38 | B2 dirección | 61/68 | -39,78 | [-97,38, 4,19] | 0,8628 | 1,0000 | NOT_SUPPORTED |
| T39 | B2 dirección | 62/30 | 7,22 | [-34,56, 54,84] | 0,4497 | 0,9258 | INCONCLUSIVE |
| T40 | B2 dirección | 31/36 | 42,38 | [-16,76, 105,18] | 0,1282 | 0,6409 | INCONCLUSIVE |
| T41 | B3 rango | 15/17 | 76,85 | [-26,13, 183,06] | 0,1162 | 0,6409 | INCONCLUSIVE |
| T42 | B3 rango | 45/42 | -6,72 | [-62,51, 65,98] | 0,6374 | 1,0000 | NOT_SUPPORTED |
| T43 | B3 rango | 60/40 | 17,42 | [-39,79, 84,85] | 0,3801 | 0,9258 | INCONCLUSIVE |
| T44 | B3 rango | 79/51 | -34,46 | [-85,34, 25,49] | 0,8767 | 1,0000 | NOT_SUPPORTED |
| T45 | B3 rango | 79/39 | 62,76 | [7,73, 109,43] | 0,0165 | 0,2122 | PREDICTIVE_IN_SAMPLE |
| T46 | B3 rango | 48/39 | -28,11 | [-88,66, 25,65] | 0,7827 | 1,0000 | NOT_SUPPORTED |
| T47 | B4 rango | 28/100 | -32,83 | [-83,89, 10,86] | 0,8467 | 1,0000 | NOT_SUPPORTED |
| T48 | B4 rango | 89/14 | 43,89 | N/D | N/D | N/D | NOT_ESTIMABLE |
| T49 | B4 rango | 101/23 | 76,28 | [18,08, 133,03] | 0,0135 | 0,2122 | PREDICTIVE_IN_SAMPLE |
| T50 | B4 rango | 14/93 | -14,45 | N/D | N/D | N/D | NOT_ESTIMABLE |
| T51 | B4 rango | 13/84 | -82,49 | N/D | N/D | N/D | NOT_ESTIMABLE |
| T52 | B4 rango | 67/46 | 10,51 | [-39,80, 64,30] | 0,4139 | 0,9258 | INCONCLUSIVE |
| T53 | B5 rango | 80/32 | 32,86 | [-17,91, 84,33] | 0,1515 | 0,6492 | INCONCLUSIVE |
| T54 | B5 rango | 50/44 | -10,56 | [-64,34, 45,45] | 0,6383 | 1,0000 | NOT_SUPPORTED |
| T55 | B5 rango | 69/55 | 19,83 | [-34,57, 68,34] | 0,2314 | 0,7713 | INCONCLUSIVE |
| T56 | B5 rango | 60/64 | 22,37 | [-33,68, 68,34] | 0,1919 | 0,7196 | INCONCLUSIVE |
| T57 | B5 rango | 53/27 | 18,70 | [-48,78, 80,23] | 0,3056 | 0,9167 | INCONCLUSIVE |
| T58 | B5 rango | 58/58 | 7,64 | [-35,76, 60,36] | 0,4873 | 0,9258 | INCONCLUSIVE |

## Tres señales de interés predictivo individual (todavía NO alfas)

| ID | Mecanismo | N casos/controles | Δ rango15m ticks | IC90 L3 | IC90 L5 | IC90 L10 | q BH30 |
|---|---|---:|---:|---|---|---|---:|
| **T29** | Expansión de rango de barra 377 E/D | 80/31 | **+61,96** | [+9,21,+113,69] | [+14,43,+114,56] | [+19,67,+113,41] | **0,2122 FAIL** |
| **T45** | Desviación absoluta de precio ponderada por qty | 79/39 | **+62,76** | [+9,55,+112,50] | [+7,73,+109,43] | [+8,30,+108,52] | **0,2122 FAIL** |
| **T49** | Peso de la máxima pausa entre grupos timestamp | 101/23 | **+76,28** | [+19,48,+132,13] | [+18,08,+133,03] | [+19,64,+135,58] | **0,2122 FAIL** |

Las tres tienen IC90 L3/L5/L10 que no contienen cero, **a nivel de contraste individual y sobre DEV adaptativamente explorada**; pero **ninguna supera q BH≤0,10 de las 30**, y además **no predicen dirección**. Solo indican posible contexto de volatilidad, que por sí mismo puede subir *o bajar* rentabilidad de una estrategia. **NO ascender a Gate1, D2 económico/fondeo ni abrir OOS por estos efectos**.

**T37** del bloque direccional tiene Δ−43,91 ticks, IC90 L5 [−83,53,−5,57], p unilateral por mejora 0,9639: evidencia *descriptiva* en contra de la hipótesis de mejor continuación, no razón para invertir retrospectivamente el signo y declararla ganadora. **T32** casi duplicada de T29 arroja Δ+52,93, IC90 L5 [−0,10,+98,41] e igualmente q0,2122; no rescatarla eligiendo L3 o L10 porque L5 era principal y solapamiento D0 ya identificado.

## Decisión y siguiente bloque

**Los gates históricos y la política G0/D0/D1/D2 permanecen intactos.** La cartera exploratoria 25/30 avanzó a D1 tal como solicitó el usuario; ahora **no existe ventaja económica validada para justificar D2 monetario**. No revisar el mismo DEV con microajustes de 1,1/0,909, horizonte, horas o filtros para fabricar q; no seleccionar una estrategia por ser la de menor p de las 30. Los mecanismos T29/T45/T49 pueden conservarse en la biblioteca **como candidatos de CONTEXTO de régimen**, y estudiarse juntos solo bajo nuevo preregistro explícito de mecanismo/veto/cartera, prueba incremental neta y una sola cuenta, dejando constancia de la selección adaptativa; no abrir holdouts sin política/gate independientemente justificado.

**Estado final:** nueva metodología de bloques IMPLEMENTADA: cinco bloques, 30 preregistradas, 27 viables, 25 diferenciadas, D1 todas30 completada, **3 indicadores no confirmados de volatilidad**, **0 estrategias validadas**. Más historia **NO descargada**.
