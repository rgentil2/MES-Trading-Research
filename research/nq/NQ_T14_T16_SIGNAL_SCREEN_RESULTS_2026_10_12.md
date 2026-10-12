# NQ — T14/T15/T16 nuevas preguntas: PRIMERA PANTALLA DE VIABILIDAD (7/7 meses)

**Fecha 2026-10-12.** Prerregistro de seis mecanismos [T14–T19](NQ_T14_T19_NEW_MECHANISMS_REGISTER_2026_10_12.md) commit `269a9d50c1a5fa5408576a809d2eb1959ab64fa3`, congelado antes de observar estos conteos. **NO se calcula beneficio, fills, PF, IC90 o p/q estadísticos en esta pantalla**. La señal es solo un evento Last por barra de ≥377 PRINTS con grupos timestamp completos e indivisibles, y se toma máximo una señal por sesión/hipótesis.

**GitHub Actions [38265573879 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38265573879)**: 6 pruebas sintéticas PASS, siete meses SUCCESS y agregador SUCCESS; artifact público seguro `t14-t16-seven-month-opportunity-screen-no-PnL` ID **11754686801**. Previo run pre-data [38265463713 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38265463713) y [38265511877 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38265511877) por construcción incorrecta de diccionario en test sintético, sin leer datos DEV; corregido SOLO test. [Motor](../../local_nq_tick_2025_2026/nq_t14_t16_signal_feasibility.py), [agregador](../../local_nq_tick_2025_2026/nq_t14_t16_signal_screen_aggregate.py), [tests](../../local_nq_tick_2025_2026/test_nq_t14_t16_signal_feasibility.py), [workflow](../../.github/workflows/nq-t14-t16-distinct-print-mechanisms-screen.yml). Todos los datos provienen de los 7 releases privados **YA guardados**, con SHA256 verificado, sin adquisición nueva ni OOS. T05 usó internamente reglas legacy de cobertura para reconciliar 135 días, pero sus señales NO se usan para T14–T16.

## Tabla de hipótesis (fase 0: no prueba económica)

| Hipótesis | Pregunta falsable | N días con señal/135 | N trades ejecutados | Neto US$ | IC90 | q BH | ¿Cumple como estrategia? |
|---|---|---:|---|---|---|---|---|
| **T14** | ¿El desplazamiento direccional suave persiste sin expansión? | **115** | N/D | N/D | N/D | N/D | **NO EVALUADO** |
| **T15** | ¿Aceptar el precio cada 25 puntos NQ anticipa continuidad? | **133** | N/D | N/D | N/D | N/D | **NO EVALUADO** |
| **T16** | ¿Contratos por print elevados sin avance anticipan reversión? | **0** | 0 oportunidades con regla congelada | N/D | N/D | N/D | **NO VIABLE con los requisitos actuales** |

N para estas filas es **días de oportunidad**, no N efectivo independiente, N trades ni número de filas Last.

| Mes | Fuente | Sesiones elegibles | T14 días | T15 días | T16 días |
|---|---:|---:|---:|---:|---:|
| 2025-10 | 13 | 13 | 13 | 13 | 0 |
| 2025-11 | 20 | 19 | 17 | 19 | 0 |
| 2025-12 | 22 | 21 | 20 | 19 | 0 |
| 2026-01 | 21 | 21 | 20 | 21 | 0 |
| 2026-02 | 20 | 20 | 15 | 20 | 0 |
| 2026-03 | 22 | 21 | 12 | 21 | 0 |
| 2026-04 | 22 | 20 | 18 | 20 | 0 |
| **TOTAL** | **140** | **135** | **115** | **133** | **0** |

## Deducciones sin ajustar umbrales

- **T14 y T15 comparten 113 sesiones con oportunidad**, sobre los 115 días T14: el gran solapamiento en DÍAS alerta de posible redundancia. NO prueba que sean las mismas entradas, dirección o operación: eso requeriría medir tiempos/signos y cuenta única; NO declararlas estrategias ortogonales ni sumar resultados futuros standalone.
- **T15 presenta señal en 133/135 sesiones**. “Una señal por casi todos los días” no prueba una ventaja ni crea 133 trades ejecutables; la prueba económica podría fallar completamente.
- **T16 presenta cero oportunidades** con sus umbrales exactos de qty por print y compresión de rango, conservados SIN retune. No alterar ratio 2× / rango ½ / VWAP ≤2ticks mirando esta pantalla; mantener como pregunta fallida/escasa y proseguir con T17–T19.
- **N no es N independiente**; sin retornos diarios no hay IC90, q BH ni PF. No declarar PASS de alfa.
- La investigación **CAMBIA DE FOCO**: no tratar B05L/T05 como proyecto exclusivo ni variar T05 para “rescatar” sus costes. Próximo: pantalla independiente T17–T19, después evaluación económica de las preguntas que tengan reglas ejecutables prerregistradas, mismos siete meses, riesgos y corrección por familia.

**Límites:** sin histórico nuevo ni 5s en señales nuevas, holdouts cerrados, T05 congelada y sin fondeo.
