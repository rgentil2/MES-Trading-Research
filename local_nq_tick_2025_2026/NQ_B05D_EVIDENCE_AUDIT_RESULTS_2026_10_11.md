# NQ-B05D — Informe verificado: identificabilidad, ejecución, fricción y saturación

**Fecha:** 2026-10-11. **Decisión:** `B05D_AUDITED_DECISION_NO_NEW_TRADE_HYPOTHESIS_TESTED`. Auditoría de **fuentes y evidencia ya existente**, no nueva hipótesis de alpha; **no se ha abierto ningún OOS** ni se han simulado nuevas operaciones.

## 1. Procedencia, pruebas y reproducibilidad

- Protocolo [NQ_B05D_EXECUTION_AND_IDENTIFIABILITY_AUDIT_PROTOCOL_2026_10_11.md](NQ_B05D_EXECUTION_AND_IDENTIFIABILITY_AUDIT_PROTOCOL_2026_10_11.md), **congelado antes de implementar la auditoría**, commit `8f8022d3ffaed13d9414bc7f8bc4d53ef41004bb`.
- Script [nq_b05d_evidence_audit.py](nq_b05d_evidence_audit.py), commit `623b0ce919c6a5b8d0a12037b989355c664be775`. Workflow [nq-b05d-evidence-audit.yml](../.github/workflows/nq-b05d-evidence-audit.yml), commit `c2ca1826fc4cff7745bb3886346f37459f6838cd`.
- [**GitHub Actions 38184798602 — COMPLETED SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38184798602). Artifact seguro **`b05d-audited-evidence-safe-report`**, archivos `summary.json` y `report.md` descargados y verificados. Self-tests: **`PASS_3_SYNTHETIC_FAIL_CLOSED_MUTATIONS`** (cobertura BBO alterada, holdout flag alterado y T05 displacement adulterado bloquean el informe).
- Fuentes de entrada, **solo artefactos de resúmenes inalterados**: [T10 run 38177582699](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177582699) `t10-seven-month-safe-report/t10_strict_bbo_qc.json`; [B03 run 38179855851](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38179855851) `b03-seven-month-safe-summary/summary.json`; [B05C run 38183250984](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38183250984) `b05c-seven-month-safe-summary/summary.json`.
- **7 meses 2025-10..2026-04, 140 días fuente/135 elegibles.** Ningún ZIP Last/Bid/Ask, release privado, serie 2026-05..09 o serie H sellada se ha abierto en B05D. El workflow solo usa permisos `contents:read` y `actions:read` en el repo público, sin secreto DEV ni exportaciones tick.

## 2. ¿Qué podemos medir realmente con Last/Bid/Ask?

| Elemento | Estado actual | Consecuencia |
|---|---|---|
| Last: precio + cantidad negociada `qty` | **Observado** | Permite estudiar barras por prints, volumen, rangos, volatilidad y reacciones locales retrospectivas |
| Best Bid/Ask anterior al hipotético fill | **Parcialmente observado** | T10 solo confirma timestamps estrictamente anteriores; no son los precios ejecutados |
| Secuencia de todos los eventos Last, Bid, Ask cuando comparten timestamp | **NO identificada** en tres TXT exportados por separado | No adjudicar causalmente un trade a la última modificación BBO del mismo timestamp |
| Lado agresor real de la transacción | **NO incluye campo CME `5797 AggressorSide`** | No llamar `qty` a delta comprador/vendedor ni agresión observada |
| Order book profundidad L2, posición en cola, cancelaciones | **NO presente** | No modelar absorción pasiva, liquidity replenishment, fill por cola o desbalance L2 como hechos |
| Ejecución broker con slippage/stop/TP dinámicos | **No observada** | No reportar last-only como fill real ni reemplazar BBO endpoint congelado para obtener una estrategia operable |

El proveedor documenta que [Tick Replay de NinjaTrader](https://ninjatrader.com/support/helpGuides/nt8/developing_for__tick_replay.htm) no fue diseñado para estimar fills reales y tiene limitaciones de Bid/Ask; [Market Replay](https://ninjatrader.com/support/helpguides/nt8/playback.htm) mantiene Level I y II sincronizados en un fichero de reproducción, sujeto al feed original. La documentación oficial de [CME MDP Trade Summary](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457418925/MDP%2B3.0%2B-%2BTrade%2BSummary) documenta campos como AggressorSide y secuencias por instrumento que **no están** en los TXT locales. Estos vínculos son especificaciones, no prueban que una fuente esté disponible o que mejore P&L.

## 3. Nueva reconciliación automática de T10 y B03 (sin backtest)

| Métrica | Resultado |
|---|---:|
| T05 simuladas (base / estrés) | **115 / 115** |
| Quote Bid/Ask estrictamente anterior y fresco en ambos extremos | **113/115 = 98,26 %** |
| Trades sin par completo | **2**, ambos **febrero 2026** |
| Entradas con BBO previo anticuado (>250ms) | **2** |
| Salidas con BBO previo anticuado (>250ms) | **1** |
| Fills Last simulados fuera del BBO anterior válido: entrada base | **46/113 = 40,71 %** |
| Fills Last simulados fuera del BBO anterior válido: salida base | **75/114 = 65,79 %** |
| Ídem entrada estrés | **56/113 = 49,56 %** |
| Ídem salida estrés | **79/114 = 69,30 %** |
| T05 neto estrés Last congelado | **+$5.102,50** |
| T05 PF estrés sin recargo | **1,31826** |
| T05 neto estrés +$10/RT contable | **+$3.952,50** |
| T05 PF estrés +$10/RT contable | **1,23717**, inferior al gate 1,25 |
| T05 DD Last cronológico estrés / estrés+$10 RT contable | **$1.797,50 / $1.887,50** |

**La salida/entrada Last fuera de BBO previo NO demuestra datos fraudulentos, ganancias de spread o fills imposibles por sí sola**: son fuentes temporalmente diferentes, y el precio hipotético incluye slippage. No se puede recuperar una expectativa ejecutable mediante sustitución contable del extremo de entrada/salida. Los costes+$10 se descuentan sobre **idénticas rutas**, no recalculan órdenes, stops o riesgo diario.

## 4. Hallazgo causal importante: la limitación diaria hace competir las estrategias

De B05C: T05 standalone **115 trades**, router una cuenta T05+T13 **210**, desglosados **91 T05 +119 T13**. Se desplazaron **24 de los 115 T05 (20,87%)**; T13 contribuyó **−$6.572,50** y el router deterioró el neto de T05 por **−$6.912,50 bajo estrés**. Es demostración técnica, en simulación, de que prioridad T05 cuando coincide la **misma barra** NO reserva capacidad ante una nueva estrategia que entra antes: T12 desplazó 79/115 y T11 15/115 en sus respectivos experimentos, también rechazados.

**No se puede prometer retención 100% de señales T05 futuras sin usar información aún no conocida, una ventana/recursos realmente separados o una regla causal que demuestre su efecto.** Cualquier nuevo candidato deberá pasar router cronológico de 1 NQ, máximo 2 trades/día y bloqueo diario cerrado −$600. La contribución atribuible nueva bajo estrés debe ser positiva, no solo quitar operaciones históricas de T05 con pérdida.

## 5. Dictamen de B05D y siguiente investigación

**Gates comprobados:**
- Cobertura 100% de quotes estrictamente anteriores: **FAIL (98,26%)**.
- Bid/Ask anterior equivale a fill real: **NO demostrado**.
- PF estrés +$10 RT ≥1,25: **FAIL (1,23717)**.
- Retención T05 ≥104 en router T13: **FAIL (91)**.
- Rentabilidad neta incremental de T13 y DD compartido bajo riesgo: **FAIL**.
- Reglas de fondeo vigentes y DD broker: **NO verificadas**.
- Integridad de evidencias, restricciones de meses y pruebas de mutación: **PASS**.

**Decisiones emitidas por código:** `BLOCK_ORDER_FLOW_ALPHA_FROM_EXISTING_EXPORTS`; `BLOCK_LIVE_OR_FUNDING_USE_OF_T05`; `PAUSE_ADAPTIVE_T14_WITHOUT_NEW_INFORMATION`; `REQUIRE_NEW_SEQUENCED_SOURCE_OR_DIFFERENT_TESTABLE_NON_FLOW_MECHANISM`.

**Siguiente bloque B05E propuesto: estudio de factibilidad de fuente, no descarga/costo automáticos.** Evaluar si existe Market Replay NQ sincronizado de la ventana DEV con nivel I/II, qué se puede obtener con licencia y proveedor actuales, cómo documentar precio/contrato/DST/rollover y cómo se validaría un único día de DEV antes de trasladar cualquier flujo real al modelo de ejecución. **No es obligación comprar datos o descartar NQ:** alternativa es diseñar un mecanismo NO order-flow con una muestra de validación efectivamente no utilizada y presupuesto finito de hipótesis; mantener 2026-05..09 y H sellados hasta gate formal. **B06 (portafolio), B07–B09 (congelación/OOS), B10 (fondeo) permanecen bloqueados.**

**Estado final: B05D COMPLETADO como auditoría de evidencia y decisión técnica, no como experimento de alfa.**
