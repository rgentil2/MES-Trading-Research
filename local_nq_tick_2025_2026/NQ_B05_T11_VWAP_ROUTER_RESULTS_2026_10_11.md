# NQ-B05 / T11 — Resultado real de segunda estrategia VWAP y enrutador T05 compartido

**Fecha:** 2026-10-11. **Decisión: `DO_NOT_PROMOTE_T11_B05_INCREMENTAL_GATE_FAIL`.**

- [Prerregistro de T11 ANTES de resultados](NQ_B05_T11_VWAP_ACCEPT_PULLBACK_PREREG_2026_10_11.md), commit `4c8cdc78563ca6e0a5ece63ac9bb129785611c28`.
- [Acción FINAL 38181697215](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38181697215): **COMPLETED SUCCESS**, 7/7 meses DEV, agregado SUCCESS; artifact `b05-seven-month-safe-summary` contiene `summary.json` y `report.md`. Resultado verificado leyendo dicho artifact.
- **Primer intento fallido** [38181654036](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38181654036): fallo únicamente por tipo de argumento `str` vs `datetime.date` en prueba sintética de causalidad antes de descargar datos; corregido en test commit `8f331cb553029ae7949e108b68edb0034016a2bb`, reglas y parámetros estratégicos intactos. Workflow actualizado commit `b90c859b6fd63e0034705aa9d2fe5e159849e5eb`.
- **Universo:** 2025-10-15..2026-04-30 (7 meses, 140 días fuente, 135 elegibles). NQ Tick Last privado DEV, SHA256 verificado para cada mes; 2025/2026 H sellados, outcomes 2026-05/06 no abiertos, 2026-07..09 sellados.
- **Ejecución:** mismo motor T04 para operaciones teóricas NQ Last (1 NQ, stop OR 16–48 ticks, TP 2R, 300 s, máximo 2 operaciones por día, límite diario de nuevas entradas −$600, riesgo único). Sin confirms de Bid/Ask y sin fills broker. Variantes `A11` NO cuentan como estrategias independientes.

## 1. Resultados por ALTERNATIVA, no sumables

| Alternativa | Trades base | Neto base USD | Trades estrés | Neto estrés USD | PF estrés | DD Last estrés USD | Neto estrés+$10 RT USD, ruta congelada |
|---|---:|---:|---:|---:|---:|---:|---:|
| **T05-377 original** | 115 | +6.220,00 | 115 | **+5.102,50** | **1,31826** | **1.797,50** | +3.952,50 |
| **T11 VWAP aceptación+retroceso+actividad** | 85 | +335,00 | 85 | **−382,50** | **0,97183** | **3.960,00** | **−1.232,50** |
| A11 sin confirmación de actividad | 128 | −5.530,00 | 128 | **−7.365,00** | **0,68340** | **8.887,50** | −8.645,00 |
| A11 sin requisito explícito de retroceso | 85 | +335,00 | 85 | **−382,50** | **0,97183** | **3.960,00** | −1.232,50 |
| **T05+T11, UNA cuenta y prioridad T05** | **155** | **+7.080,00** | **155** | **+5.622,50** | **1,25081** | **2.082,50** | **+4.072,50** |

El DD estrés+$10 de router es **$2.417,50** y PF **1,17486**; sin recargo adicional el DD estrés router **$2.082,50** excede una referencia histórica **NO VERIFICADA** de $2.000. El recargo +$10 se imputa a las rutas congeladas, **NO** recalcula nuevas órdenes ni dispara un daily stop dinámico.

## 2. Pregunta central: ¿T11 APORTA rentabilidad incremental?

- T05 alternativa de 115 operaciones estrés: **+$5.102,50**.
- Router 155 operaciones estrés: **+$5.622,50** → **+$520** de mejora neta relativa.
- Router estrés con recargo +$10: +$4.072,50 frente a T05 +$3.952,50 → **+$120** relativos, margen prácticamente agotado.
- **Atribución REAL dentro del router (no suma de backtests autónomos):** **100 trades T05 = +$5.770 estrés**, **55 trades T11 = −$147,50 estrés**. El router desplaza **15 trades de T05** del benchmark standalone, que sumaban **−$667,50**, y los sustituye/complementa con T11 que aporta **−$147,50**. El delta **+$520** surge de ese cambio de asignación, no de que el nuevo mecanismo de VWAP gane por sí mismo. Bajo estrés+$10 RT: 100 T05=+$4.770,00 y 55 T11=**−$697,50**, conjunto +$4.072,50.
- Total trades del router 155 versus 115 solo T05 = **40 operaciones netas adicionales**, NO 55 netas, porque 15 T05 quedan desplazadas por límite/solapamiento. **0 empates de señal en la misma barra de 5s** en la muestra.
- Los gates predefinidos: delta estrés+$10 >0 **PASS (solo +$120)**; PF estrés ≥1,25 **PASS marginal (1,25081)**; DD estrés Last estimado inferior a $2.000 **FAIL (2.082,50)**; PF estrés+$10 ≥1,25 **FAIL (1,17486)**; ≥5 T11 ejecutadas por mes **FAIL (enero solo 3)**; 5 trades totales mensuales router **PASS**. **Decisión inequívoca FAIL de promoción**.

## 3. Meses completos del modelo de estrés

| Mes | T05 trades/net USD | T11 trades/net USD | Router trades/net USD | T11 ejecutadas en router |
|---|---|---|---|---:|
| 2025-10 (desde día 15) | 15 / +137,50 | 11 / −1.072,50 | 19 / +242,50 | 8 |
| 2025-11 | 8 / +760,00 | 8 / −585,00 | 14 / **−40,00** | 6 |
| 2025-12 | 22 / +1.450,00 | 14 / **−1.435,00** | 28 / +260,00 | 8 |
| 2026-01 | 19 / +1.572,50 | 8 / +720,00 | 20 / +2.080,00 | **3** |
| 2026-02 | 13 / **−827,50** | 8 / +155,00 | 18 / **−705,00** | 6 |
| 2026-03 | 21 / +1.372,50 | 17 / +597,50 | 28 / +1.685,00 | 11 |
| 2026-04 | 17 / +637,50 | 19 / +1.237,50 | 28 / +2.100,00 | 13 |
| **Total** | **115 / +5.102,50** | **85 / −382,50** | **155 / +5.622,50** | **55** |

No se excluyeron noviembre/febrero, meses negativos del router, ni octubre–diciembre, meses negativos de T11 aislada.

## 4. Un fallo lógico informativo: ablation «sin pullback» es redundante

La versión FULL y la versión NO_PULLBACK dan exactamente los mismos resultados. **No es prueba estadística de que tocar VWAP no aporte valor**: las reglas codificadas vuelven el requisito explícito **matemáticamente redundante**. Para largos, exigir que el cierre de `i-1 <= VWAP_{i-1}+2 ticks` implica automáticamente que `low_{i-1} <= VWAP_{i-1}+2 <= VWAP_{i-1}+3`. Como la prueba de toque incluye `i-1`, siempre pasa si el cruce previo ya pasó. Para cortos ocurre simétricamente con `high >= close >= VWAP-2`. Esto se descubrió al inspeccionar código/resultados, **después de congelar B05**; no corregir ahora y volver a seleccionar sobre los mismos datos como si fuera nueva prueba independiente. Registrar nueva hipótesis distinta si procede, no atribuir al mecanismo pullback lo que realmente no fue aislado.

Eliminar solo la actividad sí altera materialmente los resultados: 128 trades, −$7.365 estrés, frente a 85 y −$382,50 de FULL; **diagnóstico postselección**, no causalidad estadística confirmada.

## 5. Decisión deductiva y siguiente paso

1. **B05 COMPLETADO como experimento científico con conclusión negativa.** T11 no se promueve, tampoco ablations; T05 se conserva como benchmark exploratorio, nunca como sistema live validado.
2. Incremento de **40 operaciones** en router es real dentro del **simulador**, pero no prueba de generación de ganancia neta ejecutable adicional: T11 aporta P&L negativo y aumenta DD. No sumar T05+T11 standalone ni simular que los DD de dos cuentas independientes se suman.
3. **B06 queda BLOQUEADO para la cartera T05+T11**, pues el gate B05 de DD y PF con recargos FALLÓ. Investigar otro mecanismo causal realmente distinto en un nuevo prerregistro (p.ej. actividad y desequilibrio del flujo Last con contraste contra VWAP neutral, sin usar selección de meses o repintar T11) y priorizar ingeniería de fills, fuente/microestructura y riesgo real antes de OOS. Nunca abrir mayo–septiembre para rescatar T11.
4. Si se investiga una versión mejor de T11, tratarla como **hipótesis nueva postselección con familia/contador y ajuste de búsqueda**, sin fingir que resultados de B05 siguen siendo holdout limpio.
5. Aún falta gate económico anual >max(15%, VOO-TR, QQQM-TR), OOS, fills y reglas vigentes de firma. La referencia $2.000 de DD no es contrato real.

**Reproducción:** `nq_b05_t11_vwap.py` (commit `03d1d5f0b6c577064bd7d1e476080dc95a1d66ad`), `nq_b05_t11_month.py` (commit `e2f904923ac7c696f0fac18c0b2c2bbdedfdbc3c`), `nq_b05_t11_aggregate.py` (commit `e0ec2609593a46f09552c08c1d1180ad1dce2278`), tests `test_nq_b05_t11_vwap.py`, workflow `.github/workflows/nq-b05-t11-vwap-dev.yml`, Action y artifacts seguros citados. Ningún trade ni precio individual exportado.
