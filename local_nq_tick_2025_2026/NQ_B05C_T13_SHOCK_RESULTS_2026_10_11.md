# NQ-B05C/T13 — Shock de volumen Last con reversión: resultado auditado (NO PROMOVER)

**Fecha:** 2026-10-11. **Decisión preregistrada: `B05C_T13_FAIL_DO_NOT_PROMOTE`.** Todos los resultados son simulaciones Last en siete meses ya explorados, **NO validación OOS, fills del broker ni límite de cuenta de fondeo certificado**.

## Fuentes auditables e ingeniería

- [Prerregistro ANTERIOR a la ejecución T13](NQ_B05C_T13_VOLUME_SHOCK_REVERSAL_PREREG_2026_10_11.md), commit `4d1030343ee69647c9683da2dd6917c3c767554c`.
- [GitHub Actions FINAL 38183250984](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38183250984) **COMPLETED SUCCESS** 7/7 meses y agregador; artifact `b05c-seven-month-safe-summary`, `report.md` y `summary.json` inspeccionados y cifras abajo verificadas.
- Historial de fallas de **ingeniería** (no de resultados): [38183066864](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38183066864) terminó antes de cargar datos al apuntar al nombre antiguo del test; workflow corrigió solo patrón del test, commit `659d169d3e1d96136db384f656e081a2ed0c1c22`. [38183096846](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38183096846) completó **7/7 jobs mensuales**, pero falló el agregador al buscar el prefijo T12 `nq_b05b_*.json` en vez de `nq_b05c_*.json`; solo se corrigió el patrón del agregador, commit `da99656e33e2a89ae80c9d9573f399a7a9be1f3a`. Ninguna corrección modificó parámetros, rutas, resultados o señal T13.
- **Código causal:** [nq_b05c_t13_shock.py](nq_b05c_t13_shock.py) commit `8fcd4092ba9f600afc3f724bc093deedb0902687`. Ejecución [nq_b05c_t13_month.py](nq_b05c_t13_month.py) commits `153728db3b31ea978fe48e2e5d7fc702a040f74e`, `ecdcb047e28e484e3bad113a707665ce40b2601e`, `fa82e9f309331abccc155c773e4e351f30674ab9`; [agregador](nq_b05c_t13_aggregate.py) commits `550480d5e2dccc4288399237a230e66261bd9c2f` / `da99656e33e2a89ae80c9d9573f399a7a9be1f3a`; [tests](test_nq_b05c_t13_shock.py) commit `28cbec825c0b44c7ff60390b6a2a8d2c407038b4`; workflow `.github/workflows/nq-b05c-t13-shock-dev.yml`.
- Fuente **NQ Tick Last** de DEV privado con SHA256 verificado en 7 releases de 2025-10-15 a 2026-04-30. **140 días fuente, 135 elegibles**, 115 T05 inalteradas, neto base $6.220 y estrés $5.102,50, DD Last cronológico base $1.725, estrés $1.797,50 y estrés+$10 $1.887,50, paridad exacta. MAY–JUN 2026 outcomes, JUL–SEP y H sellados, no consultados. No exportar prints licenciados, precios, timestamps ni operaciones individuales.

## 1. Hipótesis predefinida y cinco alternativas separadas

T13: 24 barras previas de 5s para actividad habitual, cuatro barras de shock con `qty` >=2x volumen por barra habitual y desplazamiento >=12 **ticks de precio**, 3 barras siguientes que revierten >=50% del desplazamiento y cuerpo contrario, señal 10:00–11:10 ET; **solo primera señal del día**. No usa opening-range ni VWAP como disparador, pero conserva ancho OR para tamaño de stop T04 (16–48 ticks) por comparabilidad. `qty` no es signed delta ni identifica agresor.

| Alternativa | Trades | Neto base USD | Neto estrés USD | PF estrés | DD Last estrés USD | Neto estrés+$10 RT USD ruta inalterada |
|---|---:|---:|---:|---:|---:|---:|
| **T05-377** referencia | 115 | **+6.220** | **+5.102,50** | **1,31826** | **1.797,50** | +3.952,50 |
| **T13_FULL (shock+reversión)** | **133** | −4.130 | **−5.562,50** | **0,75447** | **6.320** | −6.892,50 |
| A13_NO_VOLUME (control no independiente) | 135 | −855 | **−3.262,50** | 0,85577 | 5.775 | −4.612,50 |
| A13_WEAK_RETRACE (control no independiente) | 135 | −6.365 | **−7.727,50** | 0,68661 | 10.120 | −9.077,50 |
| **Router T05+T13 con 1 cuenta NQ** | **210** | **+450** | **−1.810** | **0,94620** | **4.837,50** | **−3.910** |

Los controles son *ablations* de la misma familia T13, no fuentes independientes de alpha. Las diferencias de resultados no demuestran que el criterio volumen fuera causalmente útil; sin filtro de volumen pierde menos pero sigue siendo claramente negativo. Resultado bajo estrés+$10 del router tiene PF **0,88811** y DD Last **$5.507,50**. El recargo es contable sobre rutas congeladas, no nuevo replay de SL/TP, ejecución ni stops diarios.

## 2. Riesgo y desplazamiento REAL dentro del simulador de una cuenta

- T05 standalone: **115 operaciones, +$5.102,50** estrés.
- Router: **210 operaciones, −$1.810** estrés = **−$6.912,50** comparado contra T05 bajo mismo calendario/cuenta, y **−$7.862,50** con estrés+$10 RT sobre rutas congeladas.
- En router: **91 operaciones T05** y **119 T13**, resultado de T13 atribuible **−$6.572,50** estrés; por diferencia T05 atribuido dentro del router **+$4.762,50**. T13 desplaza **24 trades** que T05 ejecutaría sola, aun con máximo **una señal T13 por día**. La exigencia PREDECLARADA de conservar **al menos 104 de 115 T05** se incumple.
- No existieron empates de decisión entre T05/T13 en la misma barra; prioridad T05 en empate no resuelve ocupación previa de plaza diaria. El router produjo 210 frente a 115 T05 = 95 trades netos adicionales, pero **pérdida neta y DD mucho mayor**.
- **Ningún gate económico obligatorio pasó:** router estrés+$10 no incrementa ganancia vs T05, PF estrés 0,94620 <1,25, PF estrés+$10 0,88811 <1,25, DD Last $4.837,50 > referencia ilustrativa **NO VERIFICADA** de $2.000, T13 atribuye −$6.572,50, y solo 91 T05 retenidos <104. Solo PASS frecuencia >=5 trades/mes y diagnóstico opcional presencia T13 en >=5/7 meses.
- En el hipotético programa de fondeo **NO** asumir que nominal $50.000 equivale a pérdida permitida: verificar DD máximo/ trailing y condiciones del proveedor antes de usar cualquier estrategia.

## 3. Todos los meses, incluido febrero rentable para T13

| Mes ET | T05 trades / neto estrés USD | T13 trades / neto estrés USD | Router trades / neto estrés USD | T13 ejecutadas router |
|---|---|---|---|---:|
| 2025-10 desde el 15 | 15 / +137,50 | 13 / **−612,50** | 21 / **−727,50** | 12 |
| 2025-11 | 8 / +760 | 19 / **−537,50** | 26 / **−240** | 18 |
| 2025-12 | 22 / +1.450 | 21 / **−227,50** | 35 / +1.057,50 | 18 |
| 2026-01 | 19 / +1.572,50 | 21 / **−1.832,50** | 33 / **−482,50** | 18 |
| 2026-02 | 13 / **−827,50** | 19 / +1.357,50 | 30 / +975 | 19 |
| 2026-03 | 21 / +1.372,50 | 20 / **−1.235** | 33 / **−407,50** | 14 |
| 2026-04 | 17 / +637,50 | 20 / **−2.475** | 32 / **−1.985** | 20 |
| **TOTAL** | **115 / +5.102,50** | **133 / −5.562,50** | **210 / −1.810** | **119** |

Febrero invierte el signo de T05 (T13 +$1.357,50 versus T05 −$827,50); **NO** seleccionar retrospectivamente «operar T13 solo en febrero», otros meses positivos ni un régimen definido por el resultado futuro. Una regla causal de régimen definida ANTES y validada de manera independiente haría falta, junto con control de múltiples pruebas. Siete meses DEV ya utilizados en T05, T09, T11, T12 y T13 NO ofrecen evidencia de robustez multianual ni OOS.

## 4. Decisión y cambio de dirección de investigación

**T13 RECHAZADO para portafolio y fondeo, B06 bloqueado**, así como T09/T11/T12. T05 conserva únicamente condición de candidato exploratorio con fragilidad de costes (estrés+$10 PF1,23717). Tras tres nuevas causas con expectativa negativa y capacidad saturada, **no ampliar indiscriminadamente a T14 con los mismos siete meses** sin antes establecer un estudio de falsación/suficiencia de datos y un protocolo de espacio de hipótesis/presupuesto de búsquedas, y sin evaluar alternativas de capital/riesgo. La siguiente tarea **NQ-B05D** propuesta: auditar comparabilidad real de datos NQ Last versus quotes, determinar qué mecanismos de microestructura se pueden identificar **sin simular agresor ni colas**, evaluar un dispositivo *ex ante* de reserva de capacidad que no use futuras señales T05, y decidir si hay base informacional para otra hipótesis independiente. Sin abrir holdouts y sin prometer ventaja monetaria no demostrada.

Referencia financiera final > max(15%, VOO total return, QQQM total return), fricciones reales y DD/payout siguen pendientes. **Este informe es investigación, no validación para operaciones reales.**
