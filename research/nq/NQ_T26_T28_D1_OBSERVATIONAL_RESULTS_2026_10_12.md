# T26–T28 D1 — resultado REAL del prerregistro original de la familia k=3

**12-oct-2026, America/Bogota.** [Action 38306171742 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306171742) verificada: seis tests sintéticos SUCCESS, reutilizó 7/7 archivos NQ Last DEV OCT2025–ABR2026 ya almacenados, SHA256 validado y borrado de todos los datos privados, **140 sesiones fuente / 135 elegibles**, **sin nuevos históricos, sin holdouts, sin 5s como señales**. [Artefacto seguro agregado 11772618236](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306171742/artifacts/11772618236), ZIP SHA256 `b5fd4fafdd5379cbfa1448d36a6a8ea1a5ce2f9e0cc118d86b92ed84649cce01`, inspeccionado: `report.md/summary.json` únicamente (sin sesiones individuales, precios de entrada, ticks Last ni trayectorias privadas). [D1 preregistrado ANTES de outcomes](NQ_T26_T28_D1_OBSERVATIONAL_PREREG_2026_10_12.md), commit `367bff5caa12e84a22db93ea49206ddd0b7e93f5`; [D0 original de T26–T28](NQ_T26_T28_G0_D0_RESULTS_2026_10_12.md).

La primera ejecución [38306058654 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306058654) se bloqueó ANTES de calcular outputs por incompatibilidad técnica `str` versus `date` en `file_for`, NO por señal estadística; _private eliminado como requisito. Corrección [commit `dfc846cf54820cb058f89bb3d60dde6127f9d7d8`](../../local_nq_tick_2025_2026/nq_t26_t28_d1_observational.py) convierte el argumento con `dev_day(day)`; **no altera características D0, lados, horizonte, estadística, umbrales, períodos ni outcomes**. Reejecución íntegra completada SUCCESS.

## Informe familiar completo (135 sesiones, no N independientes)

| ID | Hipótesis primaria congelada | N CASE | N CONTROL | Media CASE | Media CONTROL | Δ esperado ticks | IC90 L5 | p unilateral L5 EXPLORATORIA | q BH familia k3 DESCRIPTIVA | Decisión |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| **T26** | ¿Mayor zigzag relativo implica **mayor** rango futuro 15min? | **18** | **36** | **307,111** | **374,861** | **−67,750** | **[−136,302, −5,412]** | **0,948105** | **1,000000** | **NOT_SUPPORTED_DESCRIPTIVE** |
| **T27** | ¿Prima VWAP precio según cantidad anticipa continuación relativa +300s? | **6** | **65** | −28,264 markout | +10,332 markout | −38,596 | N/D, 6 CASE | N/D | N/D (sentinela p1 para BH) | **NOT_ESTIMABLE** |
| **T28** | ¿CV² irregularidad de llegada implica mayor rango? | **3** | **0** | 335,667 | N/D | N/D | N/D, CONTROL=0 | N/D | N/D (sentinela p1 para BH) | **NOT_ESTIMABLE/UNIDENTIFIABLE** |

**T26 sensibilidad a bloques no circulares, B=10.000 por condición:** L3 IC90 `[−140,589, −0,887]`, L5 **`[−136,302, −5,412]`**, L10 `[−128,818, −22,483]`. Los tres son negativos pero el signo contrastado *antes* de ejecutar era positivo; **NO invertirlo retrospectivamente ni afirmar `alfa short` o `edge contrario`**. Un mayor zigzag se asoció en estos 135 días con *menor* rango futuro, lo opuesto a la pregunta original, bajo alta incerteza y selección adaptativa de DEV. No es una estrategia monetizable.

T27 tiene un contraste observado puntual con 6 casos, **NO inferible** como p/IC90. T28 carece de grupo CONTROL, **NO IDENTIFICABLE**. Los tres se mantuvieron en la familia BH de 3, sin excluir los fallidos. Toda p/q histórica basada en DEV reutilizada es DESCRIPTIVA, sin Holm confirmatorio. Ninguno cumple `q BH≤0,10`, ni Gate1/Holm ni criterio monetario.

## Decisión operativa

- **Cerrar D1 de T26–T28 sin promover ninguno a estrategia ni D2.** T26 no respalda la hipótesis con signo positivo preregistrado. Conservar efecto de signo opuesto solo como observación para desarrollo deductivo futuro, sin selección posterior de signo ni tuning de ratios.
- **T26 y T30** hablan de recorrido/chop; NO contarlos como fuentes independientes de alfa ni sumar evidencias de desarrollo reciclado.
- **No hay simulación de broker fills, expectativa neta USD, costes, PF, DD, margen de cartera, ROI, OOS o fondeo:** `N_trades=0`, `Pnl/PF/DD/portfolio_delta/Holm/N_effective=N/D`; los valores de ticks de rango NO son ganancias en dólares.
- H77/H69/H74 mantienen `G0 NOT_PORTABLE` en el Last 08:00–12:00 existente: [auditoría original](NQ_LEGACY_H77_H69_H74_T26_PORTABILITY_GATE_2026_10_12.md). Las nuevas hipótesis inspiradas T59/T60 tienen registro independiente y G0/D0 sin haber visto sus outcomes; no se incorporan a la familia antigua.
