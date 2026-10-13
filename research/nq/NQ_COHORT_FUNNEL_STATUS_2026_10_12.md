# NQ — Tablero del embudo por COHORTES

**Control de flujo:** unidad operativa = BLOQUE COMPLETO. D1 nueva exige ≥20 candidatas D0 diversas, y el universo BH sigue incluyendo todos los miembros prerregistrados.

| Cohorte | D0: registradas → testables → diversas | D1: medidas → selección familiar | D2: calificadas | Estado |
|---|---:|---:|---:|---|
| NQ-C29-58 | 30 → 27 → 25 | 30 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C20-25 | 6 → 3 → N/D (legacy) | 6 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C26-28 | 3 → 1 → N/D (legacy) | 3 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C59-NEXT | 38 → 36 → 31 | 38 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C97-132 | 36 → 30 → 26 | 36 → 0 | 0 | D1 cerrado (sin calificadas) |
| NQ-C133-168 | 36 → 29 → 27 | 36 → 0 | 0 | D1 cerrado (sin calificadas) |

## 2026-10-13 — COHORTE ACTIVA DE NUEVE EN D2 SOMBRA (NO PROMOCIÓN FORMAL)

| Cohorte / conjunto | Participantes | D1 | Ejercicio D2 por calendario | Estado |
|---|---:|---|---|---|
| **NQ-NINE-H/T-2026-10-13** | **9** = 5 H + 4 T (T05,T147,T186,T224) | 0 promoción D1 formal (T224 falla PF/q y D0 amplitud 5/20) | [Action 38429799987 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38429799987): **T05+T224 1 cuenta** N194 neto mixto+$6.849,25, PF1,3255, DD CLOSED1.641 vs T05 sola N115+$5.102,50. **Extra+$10RT PF1,2223 falla**. H 2020–24 y T Last2025–26 no se suman; T147 necesita timeline, T186 FAIL previo. | **SHADOW D2 COMPLETADO, D2 FORMAL BLOQUEADO** |

**Fuentes:** [registro original de nueve](NQ_NINE_D2_FULL_COHORT_ROSTER_2026_10_13.md) · [prerregistro ex ante del D2 sombra](NQ_NINE_D2_T05_T224_SHARED_ACCOUNT_SHADOW_PREREG_2026_10_13.md) · [reporte verificado](NQ_NINE_D2_T05_T224_SINGLE_ACCOUNT_SHADOW_RESULTS_2026_10_13.md) · [artifact seguro](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38429799987/artifacts/11829834428). No cartera de nueve realmente operada, no Bid/Ask ni DD flotante, 50K no adquirida, holdouts cerrados. T210/T212/T215/T217 fuera del conjunto **activo** pero preservadas en archivo.

## Estado del NUEVO EMBUDO ECONÓMICO de 36 miembros T133–T168 — D1 CERRADA

- **Ocho bloques de estrategias completas**, 20 originales T133–T152 INMUTABLES +16 nuevas T153–T168 registradas antes D0. **D0 36→29 TESTABLE→27 diversas**, supera gate20; semilla original CASE/CONTROL reproducida EXACTA.
- **D1 ECONÓMICA PROXY completada en los 36** ([Action 38326216082](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38326216082)). **q BH36 mínima=1,0, 0/36 con IC90 L5 enteramente positivo, 0/36 aprueban los filtros.** 26 netos negativos, 5 positivos pero inconclusos, 5 insuficientes (<15 operaciones proxy).
- **Ejemplos que NO son alfa:** T133 +US$606,75 pero año 2026 DEV negativo, T145 +US$788 pero PF≈1,238 y q1, T147 +US$642,25 con Q4 2025 negativo. Todos son PnL de MODELO HIPOTÉTICO y sin confirmación broker.
- **Ejecución** en Last: peores precios atómicos, 2 ticks de fricción entrada/salida, stop primero si barreras coinciden, fees SUPUESTAS NQ/MNQ, estrés 1,5x y +US$10 RT. 10k bootstrap bloque por día, BH familiar k36.
- **Cortes cronológicos 53/82 DEV**, previamente explorados y NO un OOS nuevo; holdouts mayo–septiembre 2026 SELLADOS.
- **Bandeja D2:** 0 candidatas, no permite fondeo ni una cartera monetizada. No sumar PnL de hipótesis solapadas.
- **Cohortes observacionales anteriores T29–T58/T59–T96/T97–T132:** 104 estudios D1 en bloques y ninguna sobrevivió BH familiar; T05 solo baseline legacy congelado.

## D2 SHADOW — ejercicio solicitado, NO aprobación D2 oficial

- **Action SHADOW 38335007318 SUCCESS**: seis carteras independientes, una sola señal por día/cuenta, 135 DEV. Reproducción exacta de 36 D1 en N/neto y costes estresados. Auditoría SAFE 38335648618.
- **Tres carteras sin selección por ganancias** perdieron: 36 prioridad −$1.063 PF0,895 DD$2.947; 36 rotación −$1.840,62 PF0,826 DD$3.379,62; 27 diversas −$2.164,38 PF0,795 DD$3.454,12. Todas rebasan DD cerrado $2.000 ilustrativo.
- **Ganadoras RETROSPECTIVAS**: top10 +$774,50 y top5 +$683,12 (PF1,098 y 1,086), pero los dos escenarios de costes ESTRESADOS resultan NEGATIVOS. Elegidas tras mirar la MISMA DEV: sobreajuste.
- **T147 sola RETROSPECTIVA**: +$642,25 PF1,499, estrés positivo, pero Q4 2025 −$567 y solo20 trades (2,86 al mes). No aprobada como cartera de fondeo.
- **D2 FORMAL=0** y 0 fills reales. Las cifras son proxies Last con fees asumidas, DD de equity cerrada NO trailing intradía real.

**[Informe SHADOW D2 de seis carteras](NQ_T133_T168_SHADOW_D2_SIX_PORTFOLIOS_RESULTS_2026_10_12.md)** · [Action original](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38335007318) · [Auditoría SAFE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38335648618).

**Próxima prioridad:** en lugar de incrementar miles de contrastes en las mismas 135 DEV, examinar si se puede validar ejecución/costos reales y planificar una muestra verdaderamente independiente antes de otro bloque.

**Fuentes:** [Reporte D0 completo](NQ_T133_T168_FULL36_EXECUTABLE_D0_RESULTS_2026_10_12.md) · [Reporte D1 económico](NQ_T133_T168_ECONOMIC_D1_FULL36_RESULTS_2026_10_12.md) · [Prerregistro de D1](NQ_T133_T168_36_MEMBER_ECONOMIC_D1_PREREG_2026_10_12.md).

El ledger resume únicamente agregados seguros; sin filas de mercado ni operaciones privadas.
