# NQ T97–T132 — 36 preguntas nuevas en seis bloques, D0 cerrado SIN OUTCOMES

**12-oct-2026.** [GitHub Action 38318189842 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38318189842), [artefacto seguro 11777123195](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38318189842/artifacts/11777123195) SHA256 `b6a9eac2a9924dd18f9c9c9664ba0b1ef7529c02fe9cf254c6fbac29cfb677d0`, 7/7 archivos DEV NQ Last existentes, 140 fuente/135 READY; 8 pruebas sintéticas PASS y 7 trabajos mes PASS, raw borrado. [Prerregistro ANTES del resultado](NQ_T97_T132_SIX_BLOCKS_D0_PREREG_2026_10_12.md) y [JSON congelado](NQ_T97_T132_SIX_BLOCKS_D0_PREREG_2026_10_12.json).

**Embudo D0:** 36 hipótesis → **30 TESTABLE** (CASE y CTRL ≥15) → **26 distintas** (Jaccard CASE <0,85, cinco? se detectaron 4 casi duplicados) → **GATE de 20 satisfecho**. LOW_POWER: **T110 (14/120), T127 (61/9), T128 (76/14), T129 (62/13), T132 (63/9)**; UNIDENTIFIABLE: **T125 (135/0)**. Casi duplicados excluidos de diversidad, no del universo estadístico: **T102≈T97 (0,85), T114≈T117 (0,957), T115≈T97 (0,850394), T120≈T116 (0,885417)**. El rango 4181 carece de dos contextos completos en 2 READY para ciertas preguntas, se conservan como NO EVAL. No se retocan tamaños 233/377/4181.

| ID | Bloque | Pregunta original preregistrada | N CASE | N CONTROL | OTHER | NO EVAL | Gate D0 | ¿Cuenta diversa? |
|---|---|---|---:|---:|---:|---:|---|---|
| T97 | B12_MICRO_233 | ¿La pendiente entre los dos últimos bloques completos de 233 prints acompaña el impulso E377? | 115 | 20 | 0 | 0 | TESTABLE | SÍ |
| T98 | B12_MICRO_233 | ¿El desplazamiento del VWAP de 233 prints entre los últimos tres bloques confirma el impulso E377? | 117 | 18 | 0 | 0 | TESTABLE | SÍ |
| T99 | B12_MICRO_233 | ¿El cuerpo entre grupos atómicos de la última 233 acompaña el impulso E377? | 101 | 33 | 1 | 0 | TESTABLE | SÍ |
| T100 | B12_MICRO_233 | ¿El cierre atómico de la 233 queda al lado del impulso respecto a su VWAP? | 88 | 47 | 0 | 0 | TESTABLE | SÍ |
| T101 | B12_MICRO_233 | ¿La migración de máximos en 233 prints acompaña el impulso E377? | 109 | 22 | 4 | 0 | TESTABLE | SÍ |
| T102 | B12_MICRO_233 | ¿La migración de mínimos en 233 prints acompaña el impulso E377? | 107 | 24 | 4 | 0 | TESTABLE | NO |
| T103 | B13_MACRO_4181 | ¿El VWAP de una barra 4181 completa cruza al lado impulsivo respecto a la 4181 previa? | 69 | 64 | 0 | 2 | TESTABLE | SÍ |
| T104 | B13_MACRO_4181 | ¿La dirección del cuerpo de grupos atómicos de la barra 4181 última acompaña el impulso 377? | 75 | 60 | 0 | 0 | TESTABLE | SÍ |
| T105 | B13_MACRO_4181 | ¿La diferencia del VWAP 4181 y el VWAP 233 confirma el lado E377? | 48 | 87 | 0 | 0 | TESTABLE | SÍ |
| T106 | B13_MACRO_4181 | ¿La migración de máximos de contexto 4181 señala continuidad a favor del impulso 377? | 67 | 65 | 1 | 2 | TESTABLE | SÍ |
| T107 | B13_MACRO_4181 | ¿La migración de mínimos 4181 confirma el impulso 377? | 67 | 65 | 1 | 2 | TESTABLE | SÍ |
| T108 | B13_MACRO_4181 | ¿El último precio atómico de 4181 frente al VWAP macro anterior acompaña el impulso E377? | 69 | 64 | 0 | 2 | TESTABLE | SÍ |
| T109 | B14_CROSS_BARRIER | ¿El cierre E377 supera la barrera extrema de premercado a favor del impulso, frente a no alcanzarla? | 58 | 77 | 0 | 0 | TESTABLE | SÍ |
| T110 | B14_CROSS_BARRIER | ¿El cierre E377 rompe el extremo del rango RTH inicial conocido de 09:30–10:00 en dirección del impulso? | 14 | 120 | 1 | 0 | LOW_POWER | NO |
| T111 | B14_CROSS_BARRIER | ¿El cierre E377 rompe el extremo de D/C (377 prints) a favor del impulso? | 57 | 76 | 2 | 0 | TESTABLE | SÍ |
| T112 | B14_CROSS_BARRIER | ¿El cierre E377 rompe el extremo de las tres 233 completas anteriores a E? | 39 | 96 | 0 | 0 | TESTABLE | SÍ |
| T113 | B14_CROSS_BARRIER | ¿El cierre E377 atraviesa el extremo de la barra 4181 COMPLETA anterior a E? | 40 | 95 | 0 | 0 | TESTABLE | SÍ |
| T114 | B14_CROSS_BARRIER | ¿El cierre E377 está al lado del VWAP del premercado en dirección del impulso? | 92 | 43 | 0 | 0 | TESTABLE | NO |
| T115 | B15_RETEST_LOCATION | ¿El último bloque 233 mantiene el VWAP de D377 en el sentido del impulso de E? | 120 | 15 | 0 | 0 | TESTABLE | NO |
| T116 | B15_RETEST_LOCATION | ¿El cierre de 233 respecto a VWAP 4181 favorece el impulso E? | 89 | 46 | 0 | 0 | TESTABLE | SÍ |
| T117 | B15_RETEST_LOCATION | ¿El cierre E377 se mantiene respecto a centro rango PM del lado impulsivo? | 90 | 45 | 0 | 0 | TESTABLE | SÍ |
| T118 | B15_RETEST_LOCATION | ¿El cierre E377 permanece del lado impulsivo del centro de la apertura 09:30–10:00? | 88 | 47 | 0 | 0 | TESTABLE | SÍ |
| T119 | B15_RETEST_LOCATION | ¿La ubicación del cierre E377 respecto a centro de las últimas tres 233 confirma el impulso? | 105 | 29 | 1 | 0 | TESTABLE | SÍ |
| T120 | B15_RETEST_LOCATION | ¿La ubicación del cierre E377 respecto a centro 4181 último confirma el impulso? | 92 | 43 | 0 | 0 | TESTABLE | NO |
| T121 | B16_PACE_CONTRACTION | ¿Una expansión del rango de la última 233 frente a la anterior favorece la continuidad de E? | 74 | 60 | 1 | 0 | TESTABLE | SÍ |
| T122 | B16_PACE_CONTRACTION | ¿Aumento de cantidad por tiempo entre las 233 completas favorece el impulso E? | 108 | 27 | 0 | 0 | TESTABLE | SÍ |
| T123 | B16_PACE_CONTRACTION | ¿El aumento de grupos únicos timestamp por print en 233 favorece continuación? | 43 | 91 | 1 | 0 | TESTABLE | SÍ |
| T124 | B16_PACE_CONTRACTION | ¿Expansión del rango de 4181 frente a su barra anterior favorece E? | 63 | 69 | 1 | 2 | TESTABLE | SÍ |
| T125 | B16_PACE_CONTRACTION | ¿Rango relativo de 233 frente a 4181 ajustado por conteo imprime un régimen favorable? | 135 | 0 | 0 | 0 | UNIDENTIFIABLE | NO |
| T126 | B16_PACE_CONTRACTION | ¿La barra E377 tarda menos tiempo que D377 y aumenta actividad antes del resultado? | 118 | 17 | 0 | 0 | TESTABLE | SÍ |
| T127 | B17_CONSENSUS_INTERACTION | ¿La coincidencia de micro pendiente 233 y cuerpo PM ofrece continuidad frente a contradicción doble? | 61 | 9 | 65 | 0 | LOW_POWER | NO |
| T128 | B17_CONSENSUS_INTERACTION | ¿Acuerdo micro233 y cuerpo apertura RTH 09:30–10:00 frente a doble oposición? | 76 | 14 | 45 | 0 | LOW_POWER | NO |
| T129 | B17_CONSENSUS_INTERACTION | ¿Alineación simultánea de VWAP 233 y 4181 con E frente a oposición doble? | 62 | 13 | 58 | 2 | LOW_POWER | NO |
| T130 | B17_CONSENSUS_INTERACTION | ¿La pendiente macro4181 y el PM cuerpo respaldan simultáneamente E frente a oposición doble? | 36 | 30 | 67 | 2 | TESTABLE | SÍ |
| T131 | B17_CONSENSUS_INTERACTION | ¿Concordancia de 4181 y la apertura RTH frente a doble rechazo del impulso? | 49 | 31 | 53 | 2 | TESTABLE | SÍ |
| T132 | B17_CONSENSUS_INTERACTION | ¿Concordancia de 233 inmediata con pendiente D−C377 frente a doble oposición? | 63 | 9 | 63 | 0 | LOW_POWER | NO |

**D1 de BLOQUE COMPLETO**: [prerregistro prospectivo k36](NQ_T97_T132_D1_WHOLE_COHORT_PREREG_2026_10_12.md) quedó sellado **antes** de los datos D0. Por superar 20 candidatas TESTABLE diversas, se habilitó una sola D1 conjunta de **TODOS LOS 36 IDs** (incluidos no estimables y redundantes) con markout firmado VWAP+300s, IC90 y BH36. **No interpretar los 26 como estrategias rentables o 26 pruebas que pasaron D1.**

En D0 nunca se calcularon outcomes, N_trades, P&L, PF, DD, p/q, IC90, Holm ni delta de cartera: todos N/D. Sin nuevas descargas, OOS, 5s o fuentes de agresor; Last por timestamp atómico, sin asumir broker fills.
