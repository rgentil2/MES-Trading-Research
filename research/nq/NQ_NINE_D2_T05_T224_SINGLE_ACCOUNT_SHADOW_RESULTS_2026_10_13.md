# Cohorte de nueve: D2 sombra T05 + T224 cronológica COMPLETADA (D2 FORMAL FAIL)

**Fecha:** 2026-10-13. **Referencia:** [prerregistro ANTES de ejecución](NQ_NINE_D2_T05_T224_SHARED_ACCOUNT_SHADOW_PREREG_2026_10_13.md); [cohorte y nueve fichas originales](NQ_NINE_D2_FULL_COHORT_ROSTER_2026_10_13.md).

**EVIDENCIA EJECUTADA:** [GitHub Action 38429799987 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38429799987), 7/7 tests sintéticos PASS antes de IO, archivos Last DEV existentes oct2025–abr2026, checksums OK, **140 fuente/135 READY**, paridad 20/20 máscaras originales. [Artifact SAFE 11829834428](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38429799987/artifacts/11829834428), ZIP SHA256 `3bc4956c434b9325d4879122814dc5503f53dfc0a13a62402fbb6aa5561da7b9`. Se eliminaron fuentes licenciadas y vectores individuales de los runners antes de publicar. **Sin datos nuevos ni holdouts abiertos.**

## Paridad de padres y única exposición

- **T05-377** original 1NQ Last STRESS N**115** y beneficio **+$5.102,50**: reproducido exactamente. El original tenía DD **Last 1.797,50**, mientras que su nuevo DD exclusivamente **cerrado al cierre de sesión 1.310,00**: ambas métricas son distintas y no se reemplazan mutuamente.
- **T224** original E377-macro4181, N**106**, beneficio **+$1.256,00 BASE**: reproducido exactamente, D0 20/20 máscaras CASE, **0 entradas intratimestamp ambiguas** documentadas en el primer modelo. No se alteró SL2 ticks fuera E377, TP1,5R, timeout15min, tamaño 1 NQ/MNQ ni fricción original.
- **Cartera B:** una sola posición de cuenta, señales ordenadas por timestamp y T05 prioritario en empate, máximo dos entradas/día, stop de nuevas entradas cuando PnL cerrado<=-$600. Quedaron **112 operaciones T05 + 82 T224 = 194**; total de eventos señal originales mayor que 194 por restricciones de capacidad; se registraron **49 rechazos de capacidad** sobre todas las oportunidades brutas (incluidas señales de T05 que tampoco se habrían ejecutado en su benchmark). NO interpretar estos 49 como 49 trades rentables suprimidos. No se declaró colisión por simultaneidad no demostrada.

## Economía D2 SOMBRA comparada — misma muestra T, NO familia H

| Modelo de UNA CUENTA | N ejecutadas proxy | Neto USD | PF | DD **cerrado** USD | Explicación |
|---|---:|---:|---:|---:|---|
| A: T05 standalone con su estrés congelado | 115 | +5.102,50 | 1,3183 | 1.310,00 | BENCHMARK, distinto del DD Last1.797,50 |
| **B: T05 estrés + T224 BASE** | **194** | **+6.849,25** | **1,3255** | **1.641,00** | CONVENCIONES COSTOS MIXTAS, no contrato bróker homologado |
| B: T224 a fricción1,5×, T05 estrés sin cambiar | 194 | +5.967,75 | 1,2780 | 1.718,25 | El costo T224 degrada $881,50 |
| B: ambos padres con sobretasa fija adicional +$10 RT sobre mismas decisiones | 194 | +4.909,25 | **1,2223** | 1.811,00 | **FALLA PF≥1,25** bajo mayor costo; DD es cerrado no floating |

**Incremento monetario B−A en costo mixto:** **+$1.746,75**; pero B pierde 3 operaciones T05 contra padre (115→112) y solo se ejecutan 82/106 de T224, por lo que la suma ingenua **+$6.358,50 = 5.102,50+1.256,00** tampoco correspondería al router (el router +$6.849,25 es superior por selección de capacidad). La diferencia **Bextra−Aextra = +$956,75**, pero **PF extra10 1,2223 incumple gate**. Es evidencia de complemento **condicional y seleccionado post-D0**, NO de ventaja robusta ni certificación estadística. Los gastos son distintos (T05 fee/slip bajo STRESS, T224 NQ/MNQ bajo BASE) por conservación de modelos congelados; comparar solo como *shadow* de arquitectura. El estrés T224 1,5x no es una homologación integral T05/T224.

## Estabilidad por mes — agregados de una cuenta (USD)

| Mes | T05 A | B mixto | B +$10 fijo | B T224 costo1,5× |
|---|---:|---:|---:|---:|
| 2025-10 | +137,50 | +882,50 | +692,50 | +822,50 |
| 2025-11 | +760,00 | +159,00 | −61,00 | −9,00 |
| 2025-12 | +1.450,00 | +2.931,50 | +2.611,50 | +2.809,75 |
| 2026-01 | +1.572,50 | +1.805,50 | +1.505,50 | +1.683,75 |
| 2026-02 | −827,50 | −489,50 | −789,50 | −642,25 |
| 2026-03 | +1.372,50 | +1.280,75 | +970,75 | +1.169,25 |
| 2026-04 | +637,50 | +279,50 | −20,50 | +133,75 |

B mixto gana **6/7 meses**, B extra10 solo **4/7**. Esto es diagnóstico dentro de DEV reutilizada, no OOS, y muestra fragilidad monetaria con costos y meses, incluso si PF base aparente supera 1,25.

## Nueve miembros: decisión de D2 por mecanismo

| Hipótesis | Rol efectivamente evaluado en D2 | Estado |
|---|---|---|
| **T05-377** | BENCHMARK A y padre en B, paridad exacta | Interesante observacional; PF +$10RT falla gate individual y Last-DD sensibilidad >$2k |
| **T224** | Padre complementario B, paridad exacta | **Shadow incremento positivo, no D1/D2 formal**; PF extra10 cartera FALLA |
| T147 | Candidata T mismo calendario, G0 parent parity anterior | FALTA replay temporal de su ejecución para cartera homogeneizada |
| T186 | Candidata T mismo calendario, router anterior T05+T186 | Router anterior FAIL PF extra10 1,202 / DD Last2.130 |
| H09 | Padre H 2020–24 minuto | NO COMPARABLE en cartera con T2025–26 |
| H56 | Padre H 2020–24 minuto | NO COMPARABLE en cartera con T2025–26 |
| H69 | Router H09/H56 | NO fuente independiente; período diferente |
| H74 | Router H09/H56 | NO fuente independiente; período diferente |
| H77 | Router H09/H56 | NO fuente independiente; período diferente |

**Dictamen cerrado:** `D2_SHADOW_COMPLETED__INCREMENT_POSITIVE_BUT_STRESS_PF_FAIL__D2_FORMAL_BLOCKED`. La cohorte de nueve **fue evaluada en la siguiente fase D2 como ejercicio**, pero NINGUNA nueve estrategia/aprobación formal ha surgido. Tampoco hay DD flotante Last de B, trailing EOD/Intraday 50K, paridad de Bid/Ask, límites de firmas ni NinjaTrader SIM, y no se abrirá OOS para “ver si sale mejor”. Mantener T05/T224 como observación de complementariedad; siguiente actividad razonable ingeniería de ejecución de una especificación congelada (NinjaTrader SIM), o rotación de mecanismo distinto, **sin volver a retocar estos dos**.

**Código:** [motor D2](../../local_nq_tick_2025_2026/nq_nine_d2_t05_t224_shadow.py), [tests](../../local_nq_tick_2025_2026/test_nq_nine_d2_t05_t224_shadow.py), [workflow](../../.github/workflows/nq-nine-d2-t05-t224-shared-account-shadow.yml). La fuente de dinero y N de la tabla es el artefacto SAFE descargado/verificado, NO suma manual de nueve estrategias.
