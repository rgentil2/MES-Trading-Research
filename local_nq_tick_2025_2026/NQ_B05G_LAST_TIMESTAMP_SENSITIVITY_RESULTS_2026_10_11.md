# NQ-B05G — Resultado FINAL: sensibilidad de T05 al orden de Last con timestamp idéntico

**Fecha:** 2026-10-11 ET/Colombia, ejecución madrugada UTC 2026-10-12. **Estado científico:** `COMPLETADO_TECHNICAL_SUCCESS_T05_RISK_ORDER_SENSITIVE_NOT_LIVE_APPROVED`.

## 1. Procedencia verificable

- [Prerregistro previo](NQ_B05G_LAST_SAME_TIMESTAMP_ORDER_SENSITIVITY_PREREG_2026_10_11.md), commit `5b070eef525dc26e24b5e9006c97915fffde6cf2`, ANTES de las nuevas pruebas monetarias.
- [Motor mensual](nq_b05g_same_timestamp_month.py) commit `3fac50ead8f02df8e24335ea9174b607a9b7daef`, [agregador](nq_b05g_same_timestamp_aggregate.py) commit `39c1dc79180ee480315e81ec5cf7514977af5d00`, [tests](test_nq_b05g_same_timestamp.py) commits `9e4045737f8856ff7248ea280e3a8c4d661bf6b9` y `3d421d0ff327b82d1e80395545bfb91f90136083`, [workflow](../.github/workflows/nq-b05g-same-timestamp-dev.yml) commit `11a672174370034d37ec882628fd7ce6c3821de7`.
- [**GitHub Actions FINAL 38188240187**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38188240187): **COMPLETED SUCCESS, 9/9 jobs** (1 synthetic + 7 meses + agregador), 15/15 pruebas unitarias PASS (5 B05G + 10 T05 preexistentes), sin abrir holdouts. Artifact seguro `b05g-seven-month-order-sensitivity-safe-report` ID **11720700262**, `report.md` y `summary.json` descargados y leídos para este informe.
- [**Run previo 38188206072**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38188206072) **FAILURE DE TEST SINTÉTICO PRE-DATA**: el test esperaba erróneamente 3 en vez de 4 filas consecutivas con timestamp igual en un array de 7 filas [(3-1)+(3-1)=4]; corregido solo el test en commit `3d421d0ff327b82d1e80395545bfb91f90136083` ANTES de abrir DEV. Ninguna regla de T05 ni fuente fue modificada tras resultados.
- Datos del experimento: únicamente los **siete releases NQ Tick Last DEV que el usuario ya tenía**, 2025-10-15..2026-04-30, mismos archivos verificados con SHA256, **140 días fuente, 135 elegibles**. Los archivos licensiados fueron borrados de runners antes de publicar resúmenes; no se adquirió ni descargó nuevo historial de mercado, ni proveedor, ni Bid/Ask adicional, ni Replay, ni L2. T resultados 2026 mayo–septiembre, H 2025–26 y futuros reservados permanecieron CERRADOS.

## 2. Pregunta específica

¿La rentabilidad y el riesgo del modelo `T05-377` dependen materialmente del **orden de filas Last que comparten exactamente el MISMO timestamp**, dado que B05F encontró 15.979.304 prints que repiten el tiempo del evento anterior?

Para comprobarlo usamos **cuatro PERMUTACIONES ex-ante, no cuatro estrategias ni cuatro feeds**: `ORIGINAL_SOURCE_ORDER`, `REVERSE_WITHIN_EQUAL_TS`, `PRICE_ASC_WITHIN_EQUAL_TS` y `PRICE_DESC_WITHIN_EQUAL_TS`. Cada grupo preserva exactamente su multiconjunto de (timestamp,price,qty); nada se mueve de timestamp, día, contrato ni ventana ET. Dentro de empates de precio, ASC/DESC conserva orden estable de entrada. No fingir que ninguna refleja la secuencia verdadera del exchange.

Las reglas originales T02/T05-377/T04 se mantienen: mismo filtro de 377 Last prints completados, 5s, 1 NQ, máximo 2 operaciones/día, daily loss gate cerrado −$600, 16..48 ticks SL, TP2R, hold 300s, fills Last sintéticos con escenarios base ($5 RT,1 tick adverso/lado) y estrés ($7,50 RT,2 ticks adversos/lado) y suplemento fijo contable +$10 RT. DD calculado en orden cronológico ET como envolvente adversa Last, no trailing real broker.

## 3. Conciliación histórica T05 original OBLIGATORIA: PASS

- `ORIGINAL_SOURCE_ORDER`: exactamente **115 trades, base +USD6.220; estrés +USD5.102,50; PF estrés 1,31826; DD Last estrés USD1.797,50; estrés +$10 RT fijo +USD3.952,50 y DD USD1.887,50.** Coincide con T05/B03/B05C sin alterar ningún dato ni operación de referencia.
- El consolidado recuperó exactamente **15.979.304 filas Last con timestamp igual al anterior**, misma cifra B05F: fuente invariante. Contó **5.837.079 grupos de tiempo con ≥2 prints**, **3.412.972 grupos con ≥2 precios distintos**. En las alternativas se cambió el orden interno, jamás los registros existentes.

## 4. Todos los resultados, sin escoger variante favorable

| Orden intratimestamp | Trades | Neto estrés USD | PF estrés | DD Last estrés USD | Neto estrés+$10 RT fijo USD | PF estrés+$10 RT | DD Last estrés+$10 RT | Días elegibles en que cambiaron señales |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Original** | **115** | **+5.102,50** | **1,31826** | **1.797,50** | **+3.952,50** | **1,23717** | **1.887,50** | 0 |
| Reverse | 118 | +5.520,00 | 1,33429 | **2.462,50** | +4.340,00 | 1,25284 | 2.612,50 | **10** |
| ASC precio | 114 | +5.820,00 | 1,36952 | 1.865,00 | +4.680,00 | 1,28585 | 1.985,00 | **6** |
| DESC precio | 119 | +5.522,50 | 1,33394 | **2.090,00** | +4.332,50 | 1,25204 | 2.230,00 | **4** |

**Neto estrés mínimo de las cuatro hipótesis = +USD5.102,50 (original), TODAS positivas bajo Last sintético. Pero DD estrés máximo = USD2.462,50 (Reverse), superior en USD462,50 a la pantalla histórica USD2.000 NO VERIFICADA de fondeo.** DESC también USD2.090. Bajo +$10 RT fijo, **ORIGINAL PF1,23717 <1,25**; no pasan todas las variantes el gate robusto. En octubre la variante original tuvo +$137,50, mientras Reverse tuvo −$1.367,50; las diferencias por subperiodo pueden ser grandes aunque el total de siete meses sea positivo. Estas son perturbaciones de orden, no backtests independientes ni bandas de confianza.

Se registraron cambios de señales, no solo cambios de fills: Reverse **10 días**, ASC **6**, DESC **4** de las 135 sesiones elegibles. La estrategia usa cierres de barras por transacciones, cuyo precio de cierre cambia al permutar impresiones del mismo timestamp, y su salida/entrada Last también depende del orden supuesto. Cero cambios de señales no implica igualdad de P&L.

## 5. Decisión y siguiente bloque

- **`B05G_T05_LAST_ORDER_SENSITIVE_RISK_SCREEN_FAIL_UNDER_SOME_STRESS_VARIANTS`**. B05G no demuestra que el exportador original tenga datos malos; sólo mide cuánto depende nuestro modelo de su orden. **No borrar trades, no cambiar timestamps, no reemplazar el histórico por ASC para elevar resultados.**
- Sigue el supuesto Last sin BBO secuenciado, cola ni fills broker; el DD USD2000 histórico es referencia ilustrativa no validada. T05 continúa **candidato de investigación** y no estrategia validada o apta para comprar cuenta fondeada.
- **Siguiente NQ-B05H — mecanismo order-invariant con datos ya existentes**, no otro retune sobre T05: diseñar hipótesis de *tendencia/contexto multiescala* o actividad/volatilidad combinadas en barras de 5s con estadísticas independientes del orden intratimestamp (ej. `high/low/rango/volumen/precio mediano o VWAP` calculados de todos los Last del bin terminado), y comparar con T05 en capital/riesgo compartidos solo tras prereg de reglas/ablations/costes, techo de búsqueda finito. Las barras 4181/10946 desde 08 ET se pueden usar SOLO cuando estén causalmente completas; no presuponer que Fibonacci por sí misma da edge. T09/T11/T12/T13 negativas permanecen en registro.
- **NO descargar más data, no abrir períodos reservados 2026 mayo–septiembre ni holdouts H 2025–26**, no comprar fondeo ni promover B06 antes de estrategia complementaria con rentabilidad atribuible y robustez real.
