# NQ-B04 — Resultado real de robustez temporal T05-377 (sin abrir holdouts)

**Fecha:** 2026-10-11. **Decisión:** `B04_COMPLETE_TEMPORAL_FRAGILITY_DIAGNOSTIC_ONLY`. **Acción:** [NQ B04 38180451505](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38180451505) **SUCCESS**, 7/7 meses y agregador. **Prerregistro anterior a outcomes B04:** [NQ_B04_TEMPORAL_ROBUSTNESS_PREREG_2026_10_11.md](NQ_B04_TEMPORAL_ROBUSTNESS_PREREG_2026_10_11.md), commit `2c40e09dc53e564a8b083e109b08d5d3b7ccef40`. Artifact público **b04-seven-month-temporal-summary**: `summary.json` y `report.md` con estadísticas agregadas.

**Advertencias:** todos los resultados son simulaciones Last congeladas, ya exploradas, no trades reales ni inversión en ETF/fondeo. Los 7 meses contienen dos trimestres parciales y **no ofrecen robustez multianual/OOS**. Mayo–junio 2026 no abiertos a outcomes, julio–septiembre sellado. No se modificaron señales, stops, take profits, horarios, límites diarios o tamaño NQ.

## Integridad de ejecución del experimento

- Fuente autorizada: siete releases mensuales NQ **Tick Last** privados, verificados con SHA256 de archivo, de **oct-2025 a abr-2026** (140 días fuente, 135 elegibles).
- Mecanismo fijo de T05-377, un NQ; los 115 trades originales de T04/T05/T08/T10/B03 se replicaron exactamente en los siete meses y en los grupos semanales.
- Unidades: semanas **ISO lunes–domingo** en ET, unidas correctamente entre meses; 7 meses naturales; tres particiones: `2025-Q4 parcial desde 15-oct`, `2026-Q1 completo` y `2026-Q2 solo abril`.
- Escenarios PRERREGISTRADOS y no optimizados en B04: base T04, estrés T04, estrés T04 + **$10 adicionales fijos por round-trip** (1 tick de precio por lado). Este último NO recalcula la ruta ni emula slippage dinámico, apenas sustituye contabilidad neta.
- Pruebas sintéticas ISO boundary, semanas vacías, semana/mes sumas, confidencialidad por agregado y bloqueo de periodos reservados `test_nq_b04_temporal_robustness.py`; todos los jobs mensuales SUCCESS.
- No se exportaron señales, timestamps/entradas/salidas, precios NQ ni trade logs individuales. La concentración semanal se publica en cifras consolidadas, no por operación.

## 1. Panorama global

| Métrica | Base T04 | Estrés T04 | Estrés +$10 por operación |
|---|---:|---:|---:|
| Operaciones | 115 | 115 | 115 |
| Beneficio Last teórico USD | **+6.220,00** | **+5.102,50** | **+3.952,50** |
| PF neto sobre ruta fija | 1,39923 | 1,31826 | **1,23717** |
| Trades ganadores / perdedores | 52 / 63 | 52 / 63 | 51 / 64 |
| Meses positivos | **6/7** | **6/7** | **5/7** |
| Semanas ISO activas positivas | 17/29 | 16/29 | 16/29 |
| Semanas ISO negativas | 12/29 | 13/29 | 13/29 |
| Peor semana, sin identificar fecha (USD) | **−795,00** | **−822,50** | **−852,50** |
| Mejor semana, sin identificar fecha (USD) | +1.160,00 | +1.130,00 | +1.090,00 |
| Las 3 mejores semanas / suma de todas las semanas positivas | 31,96 % | 33,25 % | 34,59 % |
| Racha más larga de semanas activas negativas | 2 | 2 | 2 |

**Lectura:** en estrés se observaron **más semanas positivas (16) que negativas (13)**, no lo contrario; la muestra **no garantiza** una frecuencia positiva futura. La contribución del top-3 (33–35 % de los dólares de semanas positivas) es descriptiva, no evidencia de concentración excesiva sin comparación de referencia. En ambos escenarios de estrés el mejor mes no basta para explicar por sí solo la ganancia global.

## 2. Mes por mes, sin descartar perdedores

| Mes ET | Trades | Neto base USD | Neto estrés USD | Neto estrés +$10 USD |
|---|---:|---:|---:|---:|
| 2025-10 (desde día 15) | 15 | +495,00 | +137,50 | **−12,50** |
| 2025-11 | 8 | +830,00 | +760,00 | +680,00 |
| 2025-12 | 22 | +1.655,00 | +1.450,00 | +1.230,00 |
| 2026-01 | 19 | +1.710,00 | +1.572,50 | +1.382,50 |
| 2026-02 | 13 | **−725,00** | **−827,50** | **−957,50** |
| 2026-03 | 21 | +1.520,00 | +1.372,50 | +1.162,50 |
| 2026-04 | 17 | +735,00 | +637,50 | +467,50 |
| **Total** | **115** | **+6.220,00** | **+5.102,50** | **+3.952,50** |

**Hechos:** febrero es negativo en los tres supuestos; octubre se vuelve ligeramente negativo con solo +$10/RT. La frecuencia mínima mensual fue **8 operaciones** (noviembre), pero rentabilidad y PF mensual no se conservan uniformes: en estrés octubre PF 1,06807; febrero 0,63983; abril 1,24709, y bajo estrés +$10 octubre PF 0,99405, febrero 0,59895, abril 1,17444. Ningún resultado admite elegir arbitrariamente otro horario o excluir un mes a posteriori.

## 3. Particiones trimestrales, con límites explícitos

| Periodo | N.º meses | Trades | Base USD | Estrés USD | Estrés +$10 USD |
|---|---:|---:|---:|---:|---:|
| 2025-Q4 **parcial desde 15-oct** | 3 | 45 | +2.980,00 | +2.347,50 | +1.897,50 |
| 2026-Q1 completo | 3 | 53 | +2.505,00 | +2.117,50 | +1.587,50 |
| 2026-Q2 **abril solamente** | 1 | 17 | +735,00 | +637,50 | +467,50 |

La positividad de estas tres particiones en desarrollo **no** implica tres trimestres completos positivos, mucho menos una estabilidad de varios años. En Q1 febrero siguió siendo negativo, compensado por enero/marzo.

## 4. Conclusión y decisiones sin selección retrospectiva

1. **B04 está completado como AUDITORÍA temporal**, no como validación de robustez OOS. Los siete meses de DEV continúan reutilizados y no pueden tratarse como siete experimentos independientes.
2. T05-377 es una **fuente candidata de desarrollo con beneficio teórico global positivo**, pero variabilidad elevada: 13 semanas negativas en estrés, febrero negativo y PF por debajo de 1,25 con +$10 extra/RT. Ninguno de los umbrales o límites actuales de fondeo se ha acreditado.
3. **No** filtrar febrero, octubre, semanas o periodos de menor PF usando resultados conocidos. Para controlar régimen hace falta definir un estado **observable antes de la decisión**, con componentes contrastados incrementalmente y validación aislada.
4. La comparación de ROI >max(15%, VOO-TR, QQQM-TR) permanece pendiente para la cartera completa, junto con fills reales, drawdown broker, muestras multianuales y periodos sellados.
5. **NQ-B05 (SIGUIENTE):** prerregistrar **otra lógica causal** (p.ej. aceptación direccional y pullback en VWAP intradía y confirmación de actividad, distinta de la reversión de ruptura fallida T05 y la trampa rápida T09). Debe ser una unidad ejecutable con parámetros congelados, ablations y router común; el gate primario será **incremento neto bajo estrés y riesgo compartido**, no el P&L independiente máximo. La preferencia del usuario por 233/377 y 4181/10946 prints puede servir de contexto, pero sin imponer combinaciones que demostraron baja frecuencia (T07).
6. Seguir guardando `NQ_PROJECT_MASTER.md` y `NQ_RESEARCH_LOG.md` después de cada paso, con enlace a run/commits. Mayo–septiembre 2026 mantiene el firewall.

**Código:** `nq_b04_temporal_month.py`, `nq_b04_temporal_aggregate.py`, `test_nq_b04_temporal_robustness.py`, `.github/workflows/nq-b04-temporal-dev.yml`. Informe adicional automático accesible en artifacts de [run 38180451505](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38180451505). No incorporar resultados parciales como nueva señal.
