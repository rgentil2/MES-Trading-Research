# NQ-B05B/T12 — resultado real: compresión local, ruptura y aceleración de prints

**Fecha:** 2026-10-11. **Decisión preregistrada: `B05B_T12_FAIL_DO_NOT_PROMOTE`.** T12 NO se incorpora al portafolio NQ.

**Trazabilidad:**
- [Prerregistro ANTES de resultados T12](NQ_B05B_T12_COMPRESSION_RELEASE_PREREG_2026_10_11.md), commit `c79b615b23d18bd377df4b20ae7f4b6eaa4dd15e`.
- [GitHub Actions **38182508684**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38182508684) **COMPLETED SUCCESS**, siete meses + agregador, tests sintéticos y conciliación T04/T05.
- Artifact seguro `b05b-seven-month-safe-summary`, auditado leyendo `report.md` y `summary.json`. Solo agregados, sin datos licenciados ni transacciones individuales.
- Código: `nq_b05b_t12_compression.py` commit `4d0024b71b6ef19149fc8471045809a8f930f4ff`; `nq_b05b_t12_month.py` commit `5215c8e417cc9732be26ae526ecb6de0f94d5242`; `nq_b05b_t12_aggregate.py` commit `cd79d1da796fa2e624d381644d06867a7975a1bd`; [tests](test_nq_b05b_t12_compression.py) commits `5712626ab0f1d68bec988d74ba4970bda84fde0f` / ajuste únicamente de fixtures `7bb05697b5e5ece4e5007d3439f1e19179e552d7`; [workflow](../.github/workflows/nq-b05b-t12-compression-dev.yml) commit `68e2f88358a48307539eda0836bf2484917d9b3f`.

## 1. Universo, reglas, validación

- Contrato NQ ticks Last DEV de 2025-10-15 a 2026-04-30; **140 días fuente, 135 elegibles**, siete releases privados verificados con SHA256; fuentes/licencia no expuestas. Outcomes mayo–junio 2026 NO consultados, julio–septiembre T sellado, H sellado.
- T12 mide compresión de precio de 60s relativa al rango de 4min previos, ruptura causal de compresión por al menos 2 price ticks y **125%** prints recientes respecto a los 30s previos; 5min cooldown. No usa OR como nivel de señal ni VWAP. Se implementaron ablations sin actividad o sin compresión, mismas reglas originales para el resto.
- Reutiliza exactamente T04 para simulador Last, stop/take profit dinámicos por OR 16–48 price ticks, 1 NQ, 2 trades/día, bloqueo de nuevas entradas si saldo diario cerrado <=-$600, no solapamiento y 300s. Una sola cuenta router T05 prioridad si coinciden en la misma barra 5s. Recargo +$10 RT de estrés es solo contabilidad sobre **ruta congelada**.
- Paridad temporal y contable T05 (en cada uno de los siete meses) **PASS**: 115 trades +$6.220 base, +$5.102,50 estrés y DD Last base $1.725/estrés $1.797,50, DD estrés+$10 $1.887,50; sin reoptimización.

## 2. Resultado completo de cinco alternativas separadas

| Alternativa | Trades estrés | Neto base USD | Neto estrés USD | PF estrés | DD Last estrés USD | Neto estrés +$10/RT (ruta fija) |
|---|---:|---:|---:|---:|---:|---:|
| **T05-377 referencia** | 115 | **+6.220** | **+5.102,50** | **1,31826** | **1.797,50** | +3.952,50 |
| **T12_FULL compresión + escape + prints** | **268** | +815 | **−2.440** | **0,94494** | **6.052,50** | **−5.120** |
| A12_NO_ACTIVITY (control) | 269 | −10.140 | **−13.247,50** | 0,72950 | 15.742,50 | −15.937,50 |
| A12_NO_COMPRESSION (control) | 268 | −12.420 | **−16.135** | 0,67764 | 16.135 | −18.815 |
| **T05+T12 router compartido** | **268** | +55 | **−2.890** | **0,93514** | **5.837,50** | **−5.570** |

Los controles eliminan selectivamente SOLO una condición; el mismo conteo de operaciones no implica señales idénticas cuando el límite diario ya satura la ejecución. De hecho, P&L muy diferentes para A12 y FULL prueban rutas distintas; **NO considerar los controles nuevas estrategias independientes**. Actividad y compresión de T12 parecen útiles como filtros relativos DENTRO de esta familia, pero FULL sigue perdiendo neto.

## 3. Efecto incremental de usar UNA cuenta

- Benchmark T05 estrés = **+$5.102,50 con 115 trades**.
- Router estrés T05+T12 = **−$2.890 con 268 trades**, diferencia **−$7.992,50**. Bajo estrés +$10 RT (sobre rutas congeladas): router **−$5.570**, T05 solo **+$3.952,50** → delta **−$9.522,50**.
- Dentro del router: **36 trades T05** y **232 trades T12**; T12 aporta **−$3.755 estrés** y T05 conserva **+$865 estrés**. T12 anticipa señales/ocupa plazas del cupo de 2 operaciones diarias, desplazando **79 trades** que T05 habría ejecutado de forma aislada; **ningún empate exacto de barra** en los siete meses, por lo que prioridad T05 en empate no evita desplazamiento anterior.
- En la mayor parte de la muestra, T12 se aproxima a la capacidad máxima diaria: en octubre **26 trades en 13 días elegibles**, en noviembre 38, diciembre 40, enero 42, febrero 40, marzo 42 y abril 40. El objetivo de mayor actividad se logra a costa de pérdida de expectativa y fuerte riesgo.
- Riesgo del router: DD adverso Last **$5.837,50** estrés vs referencia histórica **NO VERIFICADA** $2.000 (FAIL); estrés+$10 DD **$7.712,50**, PF **0,87965**; no es drawdown de broker ni garantía sobre pérdidas.

## 4. Todos los meses de estrés, incluidos resultados negativos

| Mes ET | T05 (trades, neto USD) | T12_FULL (trades, neto USD) | Router T05+T12 (trades, neto USD) | T12 en router |
|---|---|---|---|---:|
| 2025-10 desde 15-oct | 15 / +137,50 | 26 / **−2.935** | 26 / **−2.965** | 23 |
| 2025-11 | 8 / +760 | 38 / +2.995 | 38 / +2.995 | 35 |
| 2025-12 | 22 / +1.450 | 40 / **−3.360** | 40 / **−4.450** | 32 |
| 2026-01 | 19 / +1.572,50 | 42 / +2.005 | 42 / +4.955 | 36 |
| 2026-02 | 13 / **−827,50** | 40 / **−1.590** | 40 / **−2.420** | 37 |
| 2026-03 | 21 / +1.372,50 | 42 / +1.805 | 42 / +335 | 37 |
| 2026-04 | 17 / +637,50 | 40 / **−1.360** | 40 / **−1.340** | 32 |
| **Siete meses** | **115 / +5.102,50** | **268 / −2.440** | **268 / −2.890** | **232** |

Estos meses ya se han visto: prohibido excluir retrospectivamente octubre, diciembre, febrero o abril o utilizar noviembre/enero/marzo como selección de regímenes sin una regla previa y nueva validación.

## 5. Gates y decisión

- Incremento router estrés+$10 >0: **FAIL (−$9.522,50)**.
- PF router estrés >=1,25: **FAIL (0,93514)**.
- PF router estrés+$10 >=1,25: **FAIL (0,87965)**.
- DD Last router estrés <$2.000 de referencia **no verificada**: **FAIL ($5.837,50)**.
- Beneficio T12 *atribuible al router* estrés >0: **FAIL (−$3.755)**.
- Al menos cinco trades totales por mes: **PASS**. Frecuencia adicional T12 ≥5/mes (objetivo optativo): **PASS**, pero no compensa los gates perdidos.
- **Conclusión científica:** hay señal causal que produce eventos suficientes, pero no ventaja monetaria probada bajo costes y riesgo. **T12 RECHAZADA**; no sumar más estrategias solo para incrementar frequency. Los siete meses son desarrollo adaptativo, no OOS, y no existe aprobación de operación/fondeo.

## 6. Siguiente decisión de investigación

**NQ-B05C (por diseñar)**: en vez de proponer otra familia de ruptura muy frecuente, analizar con prerregistro causal **estados en que el flujo de transacciones cambia el resultado económico esperado** sin consumir los dos cupos diarios antes de una señal T05. Explorar mecanismos genuinamente distintos con presupuesto de nuevos tests, evitar condicionar retrospectivamente por los meses que ganaron, y evaluar distribución de pérdidas/gains antes de añadir riesgos. Una opción es investigar dinámica de presión/absorción sin inferir delta de compra/venta real solo de Last; secuenciación Bid/Ask confiable sigue faltante. De ser posible, proteger capacidad de T05 **con prioridad temporal explícita** y validar contra T05 con gate de incremento neto real y DD, sin reconstruir artificialmente el pasado como OOS.

**B06 BLOQUEADO para T12**, tanto como lo está para T11; B07/holdouts siguen sellados. Meta económica final >max(15%,VOO-TR,QQQM-TR) permanece sin demostrar.
