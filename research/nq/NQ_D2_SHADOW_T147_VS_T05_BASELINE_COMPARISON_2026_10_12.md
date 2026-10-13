# D2 SHADOW — T147 versus T05-377, dos estrategias candidatas distintas; NO router conjunto comprobado

**12 de octubre de 2026. Respuesta a la solicitud «¿Y T147 y T05?»** Se registra la comparación de ambos modelos dentro del ejercicio D2, pero sin modificar la cohorte original ni promocionar una estrategia. **T147 ya fue evaluada como sexto escenario D2 SHADOW** en [Action 38335007318 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38335007318) y [reporte de las seis carteras](NQ_T133_T168_SHADOW_D2_SIX_PORTFOLIOS_RESULTS_2026_10_12.md). **T05 no se incluyó entre esos escenarios** porque pertenecía a una línea legacy anterior y emplea un simulador y señales distintas: se presenta aquí como **BENCHMARK independiente preexistente**, no como miembro T133–T168.

| Métrica reportada | T05-377 referencia LEGACY | T147 única, D2 SHADOW post-hoc |
|---|---:|---:|
| Período DEV original | Oct2025–Abr2026, 140/135 sesiones | Mismos siete meses, 140/135 |
| N operaciones *simuladas* | **115** | **20** |
| Frecuencia aproximada por mes | **16,4** | **2,86** |
| Neto en modelo estresado original USD | **+$5.102,50** | **+$433,00** (escenario fricción 1,5×) |
| PF de los modelos estresados respectivos | **1,31826** | **1,4992** (PF base de T147; PF estrés 1,5× no confirmado en el informe resumido) |
| DD USD reportado por modelo | **$1.797,50** de **envolvente Last** para T05 | **$567,00** de **equity CERRADA** para T147 |
| Neto tras **$10 RT extra** USD | **+$3.952,50** | **+$442,25** |
| PF con $10 RT adicional | **1,23717**, menor que mínimo 1,25 | N/D en este contraste |
| Estado | `BENCHMARK LEGACY, NO APROBADA` | `SHADOW_D2_POSTHOC, NO APROBADA` |

**Cuidado con las diferencias**: T05 fue formada a partir de T02 fallida con señales de barras de **5 segundos** y filtros causales de **377 transacciones Last**, 1 NQ, máximo **2 operaciones/día**, stops según ancho de apertura, TP=2×stop y salida máximo **5 minutos**, bajo fricción vieja (2 ticks/lado y fee $7,50 RT en su estrés). T147 es una **reversión al falso rompimiento del último contexto 4181 completo**, señal de E377 en 10:00–10:15 ET, máximo **1 operación/día**, 1 NQ o MNQ conforme riesgo nominal $250, TP=1,25R, máximo **15 minutos**, entrada proxy peor Last de primer grupo timestamp posterior, coste base NQ $4/MNQ $1,50 RT y 2 ticks/lado. **No son simuladores, tarifas, stops ni DD comparables sin estandarización, y las columnas de PF no usan exactamente el mismo escenario**. La tabla es trazabilidad de dos evidencias existentes, no ranking de estrategias.

**Fragilidad T05 documentada:** 115 operaciones, neto estrés+$10 RT +$3.952,50 con **PF1,23717** por debajo del gate1,25, DD Last hasta **$2.462,50** bajo una perturbación de orden intratimestamp, y sus 135 días DEV ya fueron examinados adaptativamente. [Informe de costes y DD B03](../../local_nq_tick_2025_2026/NQ_B03_T05_EXECUTION_HEADROOM_RESULTS_2026_10_11.md) · [B05G sensibilidad mismo timestamp](../../local_nq_tick_2025_2026/NQ_B05G_LAST_TIMESTAMP_SENSITIVITY_RESULTS_2026_10_11.md).

**Fragilidad T147 documentada:** 20 trades proxy, neto base +$642,25, PF base 1,4992, estrés fricción1,5× +$433,00, costes extra+$10 RT +$442,25, DD cerrado $567, **Q4 2025 −$567**, Ene–Abr2026 +$1.209,25 y muestra insuficiente para alcanzar al menos cinco trades/mes. [D1 económica de los 36](NQ_T133_T168_FULL36_ECONOMIC_D1_RESULTS_2026_10_12.md) · [D2 SHADOW seis carteras](NQ_T133_T168_SHADOW_D2_SIX_PORTFOLIOS_RESULTS_2026_10_12.md). Fue elegida por resultados observados, por tanto POST-HOC.

## Qué falta para probarlas JUNTAS de manera válida

**No existe todavía una medición emparejada T05+T147 en una sola cuenta. Está prohibido sumar $5.102,50 + $433,00 como si fuera un resultado de cartera.** Se requiere un router nuevo CONGELADO que reproduzca primero exactamente los 115 trades T05 bajo su motor legacy y los 20 trades proxy T147 bajo el motor E377, especifique un arbitraje **causal por hora** (no escoger el ganador del día), limite posiciones/trades/riesgo compartido, evite solapamientos y atribuya trades de cada estrategia **ejecutados/desplazados**. Debe controlar ambos simuladores a costos comunes de forma explícita, sin alterar señales T05 heredadas ni simular que dejaron de depender de 5s. Medir neto incremental del router vs T05 sola, DD intradía proxy e impacto de costes y mes. Hasta ello, **no se afirma diversificación, mejora de rentabilidad ni segundo sistema**.

**Gobierno formal intacto:** ninguna T05 ni T147 cumple validación independiente o requisitos de ejecución verificada; el D1 formal T133–T168 permanece 0 aprobadas, bandeja D2 formal 0, holdouts sellados. Esta comparación es descriptiva y educativa sobre **Last DEV explorada**, no un sistema preparado para operar con fondeo de $50.000.
