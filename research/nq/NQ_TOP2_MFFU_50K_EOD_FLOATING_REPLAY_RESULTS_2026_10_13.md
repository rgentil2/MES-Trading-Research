# RESULTADO — Rapid EOD 50K, evaluación y riesgo flotante Last de las dos carteras finalistas

**Fecha de ejecución:** 2026-10-13. **[Action 38443947480 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38443947480)**, 10 pruebas sintéticas PASS, 7 meses Last DEV originales con SHA256 correctos, 140 sesiones fuente/135 READY, datos privados por sesión borrados al acabar, [artifact SAFE 11837533672](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38443947480/artifacts/11837533672) ZIP SHA256 `26776bf8bd75aaa160b7dbb88fd56d0beb5d4e45527eb681d634c884bbff7631`. [Prerregistro anterior a la corrida](NQ_TOP2_MFFU_50K_EOD_FLOATING_REPLAY_PREREG_2026_10_13.md). **Sin abrir holdouts, sin adquirir nuevos datos ni alterar reglas.** Dos runs anteriores fallaron antes de market IO por nombre constante y aserción sintética, reparados sin modificar precios/estrategias/gates.

## Reglas y costos oficiales usados

MFFU [Rapid EOD 50K, vigente comprobado](https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look): evaluación +$3.000, MLL $2.000 EOD, 30% consistencia, >=4 días trading, sin DLL, max3 minis/30 micros, inactividad7 días. Después de aprobar, etapa **sim-funded reinicia P&L a $0**, pérdida máxima $2.000 con MLL EOD y lock de piso+$100, buffer retiro inicial $2.100, retiro mínimo $500, reparto 90/10, no Tier1 noticias. [Costos MFFU](https://help.myfundedfutures.com/en/articles/9735811-futures-instrument-list): NQ $4,68 RT, MNQ $1,90 RT, mismas 1NQ/1MNQ del padre. Los límites de la cartera (stop diario voluntario -$600, máximo2 operaciones/día, máximo una posición simultánea) **no fueron modificados**.

## Paridad y riesgo: no confundir DD CLOSED con DD Last

| Indicador USD | A: T05+T215 | B: T05+T186+T215 |
|---|---:|---:|
| Total de operaciones | 123 | 172 |
| Distribución contratos | 121 NQ / 2 MNQ | 170 NQ / 2 MNQ |
| PnL con MFFU fees tras reemplazar originales | **+$6.996,67** | **+$8.052,35** |
| Operaciones cambiadas por recalcular el stop diario con fees MFFU | **0** | **0** |
| **Drawdown de cierre EOD** | $1.110,20 | $1.152,12 |
| **Cota conservadora de DD adverso Last** | $1.528,08 | $1.711,80 |
| Peor excursión adversa respecto al inicio de su sesión | −$594,36 | −$594,36 |
| Aumento de DD Last frente A | — | +$183,72 |
| Modelo de fills broker | NO verificado | NO verificado |

La `cota conservadora DD Last` une capital cerrado con el rango extremo por grupos de mismo timestamp suponiendo un orden adverso, **NO** es drawdown flotante de brokerage comprobado. La cotización Last no contiene bids/asks ejecutables, ni prioridad de órdenes stop ni secuencia de fills intratimestamp. Un error de slippage/gaps/exchange puede dar excursion peor o distinta. El umbral MFFU EOD solo se desplaza después del cierre; el motor evalúa posible contacto con el piso INTRADÍA fijo para ser prudente.

## Replay cronológico: evaluación y sim-funded separados

| Fase / métrica | A | B |
|---|---:|---:|
| **Evaluación** — sesión READY en que se cumplen +$3k/30%/4 días | **52** | **35** |
| Beneficio EVAL al cumplir criterios | +$3.675,17 | +$3.152,61 |
| Días realmente operados durante evaluación | 31 | 27 |
| Operaciones hasta aprobación simulada | 48 | 40 |
| Primer contacto potencial con piso EVAL según Last adverso | **Ninguno** | **Ninguno** |
| Distancia mínima entre marca Last adversa y límite EVAL | $756,60 | $932,88 |
| Gaps entre días con trades >7 días calendario (EVAL) | 0 | 0 |
| **Sim-funded** — beneficio posterior tras reset inicial a $0 | **+$3.321,50** | **+$4.899,74** |
| Operaciones en sim-funded hasta fin DEV | 75 | 132 |
| Días operados sim-funded | 52 | 81 |
| Primera sesión de funded en alcanzar buffer $2.100 | 30 | 37 |
| Primer contacto potencial con piso FUNDED según Last adverso | **Ninguno** | **Ninguno** |
| Distancia mínima entre marca Last adversa y límite FUNDED | $971,28 | $797,88 |
| Gaps >7 días calendario entre días con trades (FUNDED) | 0 | 0 |

**Importante:** numeración de sesiones READY desde inicio del desarrollo, no días naturales ni promesa de tiempo a aprobar. En la fase funded, el índice de llegada al buffer está contado **desde el inicio de esa fase**. La fase funded es otra partición **del mismo DEV reutilizado**, NO out-of-sample; la cuenta fondeada real podría empezar otra fecha con distinto régimen.

**Sensibilidad de evaluación con hipotético lock del umbral en +$100:** la misma aprobación (52/35), sin contactos, distancias mínimas $1.007,81 (A) y $1.215,69 (B). El artículo oficial Rapid EOD aclara lock+$100 expresamente en sim-funded; el detalle de lock en evaluación no estaba totalmente especificado; se informó sensibilidad sin utilizar el escenario favorable para escoger cartera.

## Proyección de retiro revisada (REEMPLAZA interpretación anterior de 7 meses enteros como funded)

El objetivo EVAL de $3.000 **no** se retira ni se transfiere a sim-funded. Tomar únicamente el beneficio DESPUÉS de la evaluación, suponer sin retiros anteriores, mantener buffer MFFU $2.100 en la cuenta, aplicar split 90% al excedente, hipotéticamente sin news Tier1 ni otras reglas incumplidas.

| Valor USD | A | B |
|---|---:|---:|
| Beneficio acumulado condicionado en etapa sim-funded | $3.321,50 | $4.899,74 |
| Reserva/buffer que permanece en la cuenta | −$2.100,00 | −$2.100,00 |
| Excedente potencial para payout antes del split | $1.221,50 | $2.799,74 |
| **Payout al trader, al 90%** | **$1.099,35** | **$2.519,77** |
| Si se pagó compra promo referencial $135 (no garantizada) | **$964,35** | **$2.384,77** |

Estas cifras **corrigen** la simplificación anterior que trataba todos los 7 meses como fondeados (A $4.407,B $5.357 payouts en aquella premisa). Ahora eval y sim-funded están separadas de forma causal. Un buffer no es comisión y permanece inmovilizado, las ganancias eval no retiran. No incluye posibles impuestos, plataformas adicionales ni transición a Live. Si precio de compra cambia, recalcular solo esa fila.

## Decisión responsable

- **B supera A en velocidad de evaluación (17 sesiones READY), ganancia funded (+$1.578,24), y potencial payout al trader (+$1.420,42), bajo este histórico exacto.** Las 49 operaciones adicionales aportan flujo pero también elevan el DD intratrade adverso $183,72 y reducen el margen mínimo en funded $971,28→$797,88.
- **En LAST conservador ambas rutas permanecieron por encima del MLL** del plan, pero esto NO certifica supervivencia real: nivel observado no incluye Bid/Ask, spread cambiante, gaps, rechazos de stops, noticias Tier1 funded ni comienzo de cuentas en fechas diferentes. La regla de inactividad necesita certificación contra fechas efectivas de inicio y cierre de cuenta, aunque el máximo entre trades observados sea <=7.
- **T215, crítica para las dos, fue seleccionada entre 255 combinaciones y solo tiene 14 operaciones parentales**, por debajo de D1 N>=15; no hay validación estadística confirmatoria/OOS; el beneficio del máximo retrospectivo de 255 está sesgado hacia arriba. No reutilizar holdouts para optimizar.
- **Decisión de avance:** mantener B como *candidata de mayor beneficio y rapidez*, A como *candidata de menor DD y mayor expectativa por operación*. Enviar a paridad NinjaTrader SIM / ejecución broker y exposición con bid/ask verificable antes de considerar compra/evaluación. Ambas siguen `RESEARCH_ONLY_NOT_FUNDED_APPROVED`.

**Código reproducible**: [motor](../../local_nq_tick_2025_2026/nq_top2_mffu_eod_float_replay.py), [pruebas](../../local_nq_tick_2025_2026/test_nq_top2_mffu_eod_float_replay.py), [workflow](../../.github/workflows/nq-top2-mffu-rapid-eod-50k-last-risk-replay.yml).
