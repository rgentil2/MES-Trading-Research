# NQ T189–T208 — Cierre REAL de investigación monetaria 233 prints en cuatro bloques

**13-oct-2026.** [Action GitHub 38385387908 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38385387908), [artefacto seguro 11806450603](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38385387908/artifacts/11806450603), ZIP SHA256 `e870212d31b459e6c6c597c801dab47d4797c586a5c0432a5768c043920ed90a`. Verificado: ZIP solo incluye `report.md` y `summary.json`, sin prints, señales fechadas ni trades individuales. Pruebas sintéticas **8/8 PASS** en run final, siete meses terminados y agregador SUCCESS; muestras **140 sesiones fuente/135 READY**. Paridad T05 ESTRICTA 115 trades, US$5.102,50 neto estrés, PF1,31826 y DD Last US$1.797,50; con $10 RT adicional, +US$3.952,50, PF1,23717 y DD Last US$1.887,50.

**Secuencia técnica fiel:** primer run Action [38385234454 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38385234454) falló antes de datos por dos pruebas sintéticas: literal de descripción T05 distinto del identificador y fixture de giro con lado erróneo. Se corrigieron respectivamente la comparación con el literal congelado (commit `f81e904e7fe0032c17290e46f9323b3a954ca679`) y SOLO la entrada de prueba sintética (commit `df04d089be53008321b7b0f1b7a4be9280a1fd3a`). Sin cambiar ninguna de las 20 reglas, señales, stops/TP, tiempo, costes, D1/D2, datos o ventanas. Action final completada; sin OOS.

**Resultado de la cohorte:** 20 prerregistradas, **18 estimables, 2 N/D (T189 y T193 por exposición Last irresoluble), 9 deltas netos negativos, 9 cero, 0 positivos, 0/20 PASS**. N/D NO implica PnL cero ni evidencia de ganancia/pérdida. Un delta cero de un candidato sin trades representa router idéntico a T05, NO diversificación. q-BH/IC90 no forman parte del filtro EXPLORATORIO solicitado; no hay confirmación estadística ni broker fills.

**Gates monetarios aplicados a cada router T05+ID por separado**: delta estrés+$10RT >US$0 frente a T05; PF estrés y PF extra10 ≥1,25; DD Last estrés ≤US$2.000 solo referencia hipotética; retener ≥104 trades T05; ≥5 trades globales por mes; nueva estrategia ejecutar ≥1. Baseline T05 tiene PF extra10 1,23717, por lo que un router idéntico no puede pasar. Modelo Last con latencia1ms, slip2ticks/lado, fee estrés supuesto, 1 NQ, SL24ticks, TP48, salida300s, 2 entradas/día y stop closed −US$600. +$10 RT es contable sobre mismo camino, no fills reales.

## Bloque A: actividad y velocidad de 233 prints (09:30–09:45 ET)

**Estado: COMPLETADO, 0/5 PASS; 0 deltas negativos, 3 nulos, 2 no estimables.**

| ID | N trades standalone | N trades router | Nuevas router | T05 retenidas | Incremento neto estrés+$10 RT USD | PF router+$10 | DD Last estrés USD | Estado |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| T189 | N/D | N/D | N/D | N/D | N/D | N/D | N/D | NO ESTIMABLE |
| T190 | 0 | 115 | 0 | 115 | 0 | 1,24 | 1.797,50 | FAIL |
| T191 | 0 | 115 | 0 | 115 | 0 | 1,24 | 1.797,50 | FAIL |
| T192 | 0 | 115 | 0 | 115 | 0 | 1,24 | 1.797,50 | FAIL |
| T193 | N/D | N/D | N/D | N/D | N/D | N/D | N/D | NO ESTIMABLE |

## Bloque B: aceptación y barrido de rango (09:50–10:10 ET)

**Estado: COMPLETADO, 0/5 PASS; 4 deltas negativos, 1 nulos, 0 no estimables.**

| ID | N trades standalone | N trades router | Nuevas router | T05 retenidas | Incremento neto estrés+$10 RT USD | PF router+$10 | DD Last estrés USD | Estado |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| T194 | 18 | 129 | 18 | 111 | -1.100 | 1,16 | 1.905 | FAIL |
| T195 | 11 | 123 | 11 | 112 | -500 | 1,20 | 1.797,50 | FAIL |
| T196 | 35 | 139 | 31 | 108 | -2.440 | 1,08 | 1.947,50 | FAIL |
| T197 | 24 | 131 | 24 | 107 | -1.845 | 1,12 | 2.127,50 | FAIL |
| T198 | 0 | 115 | 0 | 115 | 0 | 1,24 | 1.797,50 | FAIL |

## Bloque C: eficiencia de precio/volumen (10:25–10:45 ET)

**Estado: COMPLETADO, 0/5 PASS; 2 deltas negativos, 3 nulos, 0 no estimables.**

| ID | N trades standalone | N trades router | Nuevas router | T05 retenidas | Incremento neto estrés+$10 RT USD | PF router+$10 | DD Last estrés USD | Estado |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| T199 | 0 | 115 | 0 | 115 | 0 | 1,24 | 1.797,50 | FAIL |
| T200 | 0 | 115 | 0 | 115 | 0 | 1,24 | 1.797,50 | FAIL |
| T201 | 1 | 116 | 1 | 115 | -147,50 | 1,23 | 1.797,50 | FAIL |
| T202 | 1 | 116 | 1 | 115 | -152,50 | 1,23 | 1.797,50 | FAIL |
| T203 | 0 | 115 | 0 | 115 | 0 | 1,24 | 1.797,50 | FAIL |

## Bloque D: streaks, giro y desaceleración (11:00–11:20 ET)

**Estado: COMPLETADO, 0/5 PASS; 3 deltas negativos, 2 nulos, 0 no estimables.**

| ID | N trades standalone | N trades router | Nuevas router | T05 retenidas | Incremento neto estrés+$10 RT USD | PF router+$10 | DD Last estrés USD | Estado |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| T204 | 10 | 125 | 10 | 115 | -825 | 1,17 | 2.127,50 | FAIL |
| T205 | 3 | 117 | 2 | 115 | -295 | 1,22 | 1.797,50 | FAIL |
| T206 | 12 | 122 | 8 | 114 | -577,50 | 1,19 | 1.930 | FAIL |
| T207 | 0 | 115 | 0 | 115 | 0 | 1,24 | 1.797,50 | FAIL |
| T208 | 0 | 115 | 0 | 115 | 0 | 1,24 | 1.797,50 | FAIL |

## Interpretación y siguiente decisión

- **No se identificó aporte monetario incremental positivo** a T05 en T189–T208 con los costos definidos. La familia A tiene T189/T193 85/88 días con señal pero resultados censurados por exposición Last no reconstruible; las otras tres no activaron. No tratar N/D como estrategias fallidas monetarias comprobadas ni ajustarles señales retroactivamente.
- B: T196 empeoró el router US$2.440 extra10, aunque su standalone tiene 35 operaciones simuladas. D: T204 empeoró US$825. La forma causal complementaria no garantiza monetización.
- Todos los resultados reutilizan 7 meses DEV explorados adaptativamente; no hay muestra independiente. El límite DD US$2K no representa reglas reales de firma. No abrir mayo–sept 2026 ni holdouts H, no añadir data, no inferir mercado BID/ASK ni delta/agresor de Last.
- Próxima acción razonable no es retocar estos 20: auditar el **modelo monetario de ejecución y filtrado causal de capacidad**, además de diseñar estrategias orientadas a beneficio neto incremental que no replique la misma señal, conservando D1 formal T133–168 0 aprobadas y D2 formal 0. Si se registra otra cohorte, debe ser de hipótesis realmente nuevas y prerregistradas antes de outcomes, no filtros post-hoc.
