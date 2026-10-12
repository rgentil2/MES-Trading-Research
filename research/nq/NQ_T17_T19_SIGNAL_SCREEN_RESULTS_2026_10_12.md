# NQ — T17/T18/T19 tres hipótesis nuevas (primera pantalla en 135 sesiones)

**Fecha 2026-10-12.** [Prerregistro de seis preguntas](NQ_T14_T19_NEW_MECHANISMS_REGISTER_2026_10_12.md) y [reglas de esta segunda familia](NQ_T17_T19_STAGE0_RULES_2026_10_12.md), commit `0c5a15f741a7d8c2d0578a84d1b0e2a732833d17`, ambos anteriores a estos resultados. **NO hubo backtest de P&L, ni ejecución NQ, ni cálculo IC90, p o q.**

[**GitHub Actions 38266818415 COMPLETED SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38266818415), **6 tests sintéticos PASS, siete meses y agregador SUCCESS**; artifact seguro `t17-t19-seven-month-safe-opportunity-screen` ID **11755037378**, resumen y reporte leídos. [Motor](../../local_nq_tick_2025_2026/nq_t17_t19_signal_feasibility.py) · [tests](../../local_nq_tick_2025_2026/test_nq_t17_t19_signal_feasibility.py) · [workflow](../../.github/workflows/nq-t17-t19-distinct-print-mechanisms-screen.yml).

| Hipótesis | Pregunta causal | Días con evento / N elegibles | N trades monetarios | IC90 | q BH | ¿Cumple ventaja monetaria? |
|---|---|---:|---|---|---|---|
| **T17** | ¿Aumentan los prints/segundo sin expandirse contemporáneamente el rango, prediciendo volatilidad futura? | **135/135** | N/D: MAGNITUD | N/D | N/D | **NO EVALUADO** |
| **T18** | ¿La dirección del valor negociado preopen persiste tras 09:30 ET? | **98/135** | N/D | N/D | N/D | **NO EVALUADO** |
| **T19** | ¿Una trayectoria de VWAP 377 poco eficiente anticipa magnitud futura? | **135/135** | N/D: MAGNITUD | N/D | N/D | **NO EVALUADO** |

| Mes | Días fuente | Sesiones elegibles | T17 | T18 | T19 |
|---|---:|---:|---:|---:|---:|
| 2025-10 | 13 | 13 | 13 | 13 | 13 |
| 2025-11 | 20 | 19 | 19 | 12 | 19 |
| 2025-12 | 22 | 21 | 21 | 11 | 21 |
| 2026-01 | 21 | 21 | 21 | 13 | 21 |
| 2026-02 | 20 | 20 | 20 | 17 | 20 |
| 2026-03 | 22 | 21 | 21 | 17 | 21 |
| 2026-04 | 22 | 20 | 20 | 15 | 20 |
| **TOTAL** | **140** | **135** | **135** | **98** | **135** |

**Solapamiento de DÍAS de evento:** T17 y T19 coinciden en **135/135** sesiones (no significa que sean los mismos instantes de señal), y T18 coincide con cada uno en **98/135**. Patrones T17/T19 son prácticamente ubicuos en la ventana y necesitan medir **poder predictivo de una variable cuantitativa, no celebrar frecuencia**. No alterar umbrales para generar menos señales ahora: diseñar preregistro separado de efecto FUTURO por sesión para distinguir verdadera predictibilidad antes de traducirlo a órdenes. **T17 y T19 no tienen lado long/short**: N eventos no equivale a N trades y está prohibido asignarles un PF fingido.

**Lecciones del programa T14–T19:** 6 preguntas registradas y 6 pantallas de viabilidad completadas sin tocar entradas de T05; T14/T15 tienen alto solapamiento a nivel días, T16 cero; T17/T19 comunes, T18 más selectiva. Falta **prueba monetaria y/o de valor predictivo**. La [familia económica T14–T16](NQ_T14_T16_ECONOMIC_FIRST_PASS_PREREG_2026_10_12.md) quedó preregistrada **pero NO ejecutada en esta pantalla**; no declarar éxito monetario ni q estadístico.

Sin proveedores de datos nuevos, sin 5s para señales nuevas, sin lectura OOS, sin compra fondeo.
