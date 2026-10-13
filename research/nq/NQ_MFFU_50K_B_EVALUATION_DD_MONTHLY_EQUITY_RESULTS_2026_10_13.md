# Informe VERIFICADO: B=T05+T186+T215 — DD evaluación y timeline mensual MFFU $50K

**13-oct-2026.** [GitHub Action 38466592972 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38466592972), pruebas sintéticas de línea mensual y antigua cuenta Last PASS, siete releases Last DEV existentes (2025-10 a 2026-04) y SHA256 verificados, 140 sesiones fuente/135 elegibles. [Artefacto SAFE con summary.json y report.md](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38466592972/artifacts/11850020199). [Prerregistro antes del cálculo](NQ_MFFU_50K_B_EQUITY_TIMELINE_DIAGNOSTIC_PREREG_2026_10_13.md). Nada de holdouts T mayo–sept2026 ni H2025/26, sin data adicional, sin cambiar cartera ni parámetros. Resultados solo agregados por mes, no entradas/fechas/prints de mercado individuales.

## Drawdown: TRAMO EVALUACIÓN VS SIM-FUNDED VS HISTÓRICO COMPLETO

| Métrica US$ | Evaluación primeras 35 READY | Funded desde sesión 36 con ganancias reiniciadas a 0 | DEV completa sin reset (**solo diagnóstico, no cuenta real**) |
|---|---:|---:|---:|
| Operaciones | 40 | 132 | 172 |
| Beneficio P&L acumulado | +3.152,61 | +4.899,74 | +8.052,35 |
| **DD peak-to-trough diario CERRADO** | **862,44** | **1.152,12** | **1.152,12** |
| **DD Last adverso conservador** | **1.222,44** | **1.711,80** | **1.711,80** |
| Peor excursión respecto apertura de día (datos disponibles) | −509,36 | N/D en esta salida pública | −594,36 |
| Distancia mínima del equity Last adverso al piso dinámico MFFU | 932,88 | 797,88 (estudio anterior) | No aplicable, porque la evaluación/funded reinician |
| Fase y días operados | 27 días reales de trades en 35 sesiones READY | 81 días con trade | 108 días con trade |

**Interpretación rigurosa:** DD Last US$1.222,44 **es el máximo retroceso adverso estimado de la curva respecto a máximo intrasesión**, no equivale al mayor déficit frente a saldo nominal 50K ni al **mínimo margen frente al piso móvil US$932,88**. El MLL oficial USD$2.000 se recalcula EOD, pero debe respetarse intrasesión; el riesgo Last puede sobreestimar por orden de impresiones iguales, también puede subestimar por spreads, stops/gaps/fills desconocidos. **No certificar "nunca incumpliría" una cuenta real.** Los máximos de DD de fase funded sucedieron tras la evaluación; no fueron pérdidas de la fase de reto.

## Línea de tiempo por mes ET, FEES MFFU, sin double charge

| Mes ET | Beneficio mes EVAL | Saldo acumulado EVAL | Ops EVAL | Beneficio mes SIM-FUNDED | Saldo acumulado SIM-FUNDED | Ops SIM-FUNDED | P&L total DEV sin reset |
|---|---:|---:|---:|---:|---:|---:|---:|
| Oct-2025 | +907,97 | 907,97 | 17 | 0,00 | 0,00 | 0 | 907,97 |
| Nov-2025 | +1.158,04 | 2.066,01 | 18 | 0,00 | 0,00 | 0 | 2.066,01 |
| Dic-2025 | +1.086,60 | **3.152,61** | 5 | +1.523,00 | 1.523,00 | 25 | 4.675,61 |
| Ene-2026 | — | 3.152,61 **terminada** | 0 | +1.213,96 | 2.736,96 | 28 | 5.889,57 |
| Feb-2026 | — | 3.152,61 **terminada** | 0 | +237,68 | 2.974,64 | 24 | 6.127,25 |
| Mar-2026 | — | 3.152,61 **terminada** | 0 | +509,92 | 3.484,56 | 31 | 6.637,17 |
| Abr-2026 | — | 3.152,61 **terminada** | 0 | +1.415,18 | **4.899,74** | 24 | **8.052,35** |

Evaluación se alcanza en **sesión READY nº35 (diciembre 2025)**, con **40 operaciones** y **27 días operados**. En diciembre la **primera parte del mes** todavía pertenece a la evaluación y el **resto** a sim-funded: **no son dos cuentas en paralelo**. La línea investigativa $8.052,35 suma meses sin reset solo como comparador; la ganancia de evaluación $3.152,61 **NO es retirable ni trasladable** a sim-funded. La cuenta sim-funded partiría de **USD0 de ganancias** tras cumplir evaluación; alcanza $4.899,74 de PnL simulado al fin de DEV. Preservando buffer inicial de USD$2.100, el máximo neto condicional a payout al 90% sería **USD$2.519,77**, excluyendo gastos/otras reglas, NO revenue cobrado.

## Qué queda incierto

- No hubo pérdidas mensuales NETAS en este itinerario, pero **sí retrocesos diarios/flotantes significativos**, que la tabla mensual no muestra. Febrero fue el mes sim-funded menos productivo, +$237,68.
- NQ solo Last, no Bid/Ask/orden de eventos exchange, spreads reales, reject stops, news Tier1 sim-funded no auditadas.
- Recompra/reinicio de una evaluación real, inactividad anterior a la primera operación, comisiones/plataforma, posibles pagos intermedios e impuestos no modelados. La fecha del comienzo real puede cambiar totalmente la trayectoria.
- **El pseudo-forward T julio–sept2026 sigue sellado**; evidencia exclusiva de desarrollo, no promesa de pasar fondeo.

Código [motor original](../../local_nq_tick_2025_2026/nq_top2_mffu_eod_float_replay.py), [reporte particionado por cuenta](../../local_nq_tick_2025_2026/nq_mffu_b_evaluation_revenue_timeline.py), [tests](../../local_nq_tick_2025_2026/test_nq_mffu_b_evaluation_revenue_timeline.py) y [workflow](../../.github/workflows/nq-mffu-b-eval-only-dd-revenue-timeline.yml).
