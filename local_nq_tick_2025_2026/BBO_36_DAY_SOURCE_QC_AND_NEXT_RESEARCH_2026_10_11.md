# NQ ticks — diagnóstico de 36 sesiones y decisiones de investigación (2026-10-11)

**Estado:** `SOURCE_QC_DIAGNOSTIC_ONLY`. **No es una estrategia, ni prueba de rentabilidad, ni simulación de fills.** Fecha del análisis: 2026-10-11.

**Fuente:** NinjaTrader NQ Tick `Last/Bid/Ask`, archivada en `rgentil2/NQ-Ticks-Dev-2026` (privado); acceso solo lectura con secreto Dev-only. Fechas ET octubre 2025-junio 2026; junio/mayo para QC y validación interna, **no** P&L exploratorio. `NQ-Ticks-Sealed` y el pseudo-forward **julio-septiembre 2026** no se abrieron.

**Ejecución reproducible:** [GitHub Actions 38147297938](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38147297938), nueve trabajos completados (`success`), runner estándar público, checksum SHA-256 antes de extraer. Código: [qc_bbo_dislocation.py](./qc_bbo_dislocation.py), [qc_bbo_month_batch.py](./qc_bbo_month_batch.py). Selección de fechas **fijada antes de mirar los resultados**, exclusivamente desde la cobertura `download_manifest.csv`: cuatro fechas por mes, repartidas en semanas y días laborales. No es muestra probabilística del período completo. Cada mes se descargó **una sola vez** y se reutilizó para cuatro análisis; total **36 sesiones**.

## Resultado — exclusivamente 09:30–11:30 ET

| Mes | Cuatro días, operaciones Last | Mediana diaria fuera del BBO anterior | Rango de cuatro días | Re-clasificación con BBO del mismo timestamp (NO CAUSAL)* |
|---|---:|---:|---:|---:|
| 2025-10 | 605.528 | 25,68 % | 23,72–29,11 % | 85,37 % |
| 2025-11 | 846.388 | 31,97 % | 27,47–33,39 % | 85,56 % |
| 2025-12 | 707.201 | 26,92 % | 26,18–28,53 % | 85,22 % |
| 2026-01 | 789.973 | 32,94 % | 29,01–35,31 % | 84,45 % |
| 2026-02 | 797.560 | 35,16 % | 32,22–38,60 % | 84,61 % |
| 2026-03 | 660.616 | 33,98 % | 33,01–36,15 % | 86,23 % |
| 2026-04 | 584.337 | 29,82 % | 28,31–36,44 % | 82,45 % |
| 2026-05 | 755.294 | 32,52 % | 28,71–35,59 % | 87,50 % |
| 2026-06 | 705.303 | 37,88 % | 30,53–39,42 % | 88,42 % |
| **TOTAL** | **6.452.200** | **32,13 % mediana de 36 días** | **23,72–39,42 %** | **85,63 % agregado** |

*El último porcentaje considera **solo operaciones fuera del BBO anterior** que compartían timestamp con actualizaciones de cotización. Al reemplazar hipotéticamente el BBO previo por el **posterior en ese mismo timestamp**, esa proporción queda dentro de la cotización. La sustitución es expresamente **NO CAUSAL**, no informa qué evento ocurrió primero y **no** habilita comprar/vender a ese precio.

### Estadística diaria, no falsa independencia de millones de ticks

- **Mediana entre 36 tasas diarias:** 32,13 %; percentiles 25 y 75 de las tasas diarias: **28,67 % y 34,90 %**. El 32,10 % ponderado por tick es **descriptivo**, no se debe tratar como estimación con 6,45 millones de observaciones independientes.
- **Antigüedad cotizaciones:** medianas de tasa fuera del BBO: máximo 50 ms **32,22 %**, máximo 250 ms **32,14 %**, máximo 1000 ms **32,13 %**. El simple ajuste de edad **no** resuelve el problema.
- **Segmentación temporal, medianas diarias:** 09:30–10:00 **34,31 %**; 10:00–10:30 **32,00 %**; 10:30–11:30 **29,21 %**. La primera franja tiene más anomalías que la última en **33 de los 36 días**, descripción de esta muestra, no regla de trading.
- **Mediana diaria de sensibilidad NO causal:** 84,88 %; el porcentaje agregado por casos afectados es 85,63 %. Un mismo timestamp se comparte frecuentemente entre trades y actualizaciones Bid/Ask.

### Qué sabemos y qué NO sabemos

La persistencia entre días y entre meses hace plausible que la secuenciación de los tres archivos NinjaTrader sea una fuente importante de la discrepancia Last-vs-BBO. **No prueba** que los datos estén corruptos, que un trade sea agresor de compra/venta, que exista arbitraje, ni que un precio de Bid/Ask fuera ejecutable con latencia, prioridad y liquidez reales. Un feed secuenciado por exchange/venue o una grabación nativa ordenada sería necesario para validar esa interpretación microestructural. Ajustar el umbral de edad a posteriori para mejorar una hipótesis estaría prohibido como evidencia confirmatoria.

Los 36 días fueron escogidos por cobertura temporal del manifiesto, no aleatoriamente. Los resultados NO demuestran estabilidad en todas las sesiones de nueve meses. Una estimación inferencial necesitaría preregistro, más días y evaluación por bloques de sesión/día, sin suponer independencia de ticks.

## Decisión de ingeniería (avance permitido, sin revisar retornos)

**A. Señales:** autorizar investigación de señales derivadas únicamente de eventos `Last` hasta el instante de decisión y de barras ya cerradas. Construir volumen/tasa de operaciones, volatilidad reciente y trayectoria del precio; **no** inferir delta real comprador-vendedor de Last ni usar cotizaciones del mismo timestamp como features de entrada.

**B. Contexto/régimen:** condición de apertura, rangos previos y régimen de volatilidad son componentes conjuntos, no estrategias aisladas. Registrar cada ventana y variable antes de mirar retornos. Marcar mayor cautela en 09:30–10:00 y cambios de contrato; no excluir fechas por P&L.

**C. Ejecución:** el histórico BBO es dato de QC con incertidumbre de secuenciación, **no** precio de ejecución garantizado. Primeros backtests exploratorios conservadores usando `Last` **posterior a la señal**, retraso predefinido, slippage adverso y comisiones NQ verificadas por lado. Reportar escenarios de coste 1× y 1,5×, SL/TP intratick, peor caso para ambigüedades, riesgos de 1 NQ ($5/tick) y MNQ como alternativa si el riesgo excede límites de fondeo. No confundir simulación Last-only con fill observado.

## Próximas familias conjuntas: propuestas para PRERREGISTRAR, NO probadas

- **NQ-T01 — Apertura de continuación condicionada:** estructura premarket + rango de apertura observable hasta T + aceleración de tasa de operaciones Last (ventanas cerradas) + régimen de volatilidad + ejecución Last posterior y riesgo estructural. Comparador sin aceleración (ablación).
- **NQ-T02 — Ruptura fallida/reversión condicionada:** exceso sobre rango previo + pérdida *causal* de velocidad de nuevas transacciones + rechazo a zona previa y volatilidad compatible + stop/timeout fijos ex ante. Comparador sin filtro de velocidad.
- **NQ-T03 — Router de combinación:** router estado de mercado hasta T que elige una de las dos reglas anteriores o *no trade*; medir cambio neto vs componentes solos, DD flotante, coincidencias de señales y efecto de costos. No seleccionar el router por meses que rindieron bien.

**Ninguna propuesta es una hipótesis estadística formal aún**: primero fijar definiciones completas, variantes y presupuesto de comparaciones (Holm/alpha por familia), reglas exactas de señal, fill adverso, SL/TP, tamaño, costos y criterio final. La investigación heredada H01–H78 en datos de minutos conserva sus holdouts separados; no reutilizar el bloque 2025 como OOS heredado.

## Gate pendiente antes de declarar una estrategia

1. Conciliación **Tick Last -> OHLCV 1m** en sesiones/rollovers, timestamps ET/DST y volúmenes con los archivos Minute Last; registrar cualquier discrepancia.
2. Prerregistro de familia/ledger y simulación conservadora sin mirar mayo-junio para ajustar parámetros de desarrollo. Mayo-junio es **validación interna ya observada para QC**, nunca el pseudo-forward independiente.
3. Evaluar **por semana, mes, trimestre, semestre y régimen**; fechas son unidades más independientes que ticks; estabilidad, PF, IC, frecuencia, dependencia por año/mes, DD y límites de cuenta fondeada.
4. Abrir **una sola vez julio-septiembre 2026** después de congelar código, reglas, costes, TP/SL y sizing, y documentar resultados completos aunque no sean favorables.

**Ni ROI, ni CAGR, ni CAGR >15%/VOO/QQQM ni operaciones reales fueron calculados aquí.**
