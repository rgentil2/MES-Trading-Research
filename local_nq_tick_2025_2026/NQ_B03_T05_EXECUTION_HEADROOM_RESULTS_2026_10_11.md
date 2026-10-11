# NQ-B03 — resultado: sensibilidad de T05-377 a fricción y drawdown en orden cronológico

**Fecha:** 2026-10-11. **Estado:** `B03_COMPLETED_TECHNICALLY_EXECUTION_FRAGILE`.
**Evidencia:** [GitHub Actions 38179855851](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38179855851) **SUCCESS**, 7/7 meses, pruebas sintéticas, conciliación de todos los meses, agregador y artifact `b03-seven-month-safe-summary`. [Prerregistro previo](NQ_B03_HEADROOM_PREREG_2026_10_11.md).

**Importante:** estos son **escenarios contables de coste añadido sobre las MISMAS operaciones simuladas**, NO backtests ejecutables. No se recalculan señales, entradas/salidas, órdenes STOP/TP, daily stop ni actividad al cambiar costes. El supuesto de cargo uniforme no modela velocidad, ejecución real, rechazo de órdenes, liquidez o spread dependiente de régimen. Los tests reales se ejecutaron solo sobre Last DEV histórico.

## 1. Diseño congelado

- T05-377 sin tocar, 1 NQ, los mismos 115 trades T04 de desarrollo 2025-10-15 a 2026-04-30; **140 sesiones fuente y 135 sesiones elegibles**; ninguna serie reservada se abrió.
- Exacta reproducción de beneficios Last preexistentes: **USD +6.220 baseline / +5.102,50 estrés**; mismos costes originalmente definidos: base $5 RT y 1 tick adverso por lado, estrés $7,50 RT y 2 ticks adversos por lado.
- Recargos adversos fijos definidos **antes de correr la prueba**: **0, 1, 2 o 4 ticks de precio adicionales POR LADO**, equivalentes a **$0, $10, $20, $40 extra por operación completa de 1 NQ**. No equivalen a un slippage real confirmado.
- Trazado de equity de cada operación preservando ruta Last, aplicando el cargo extra en mark-to-market y al cerrar; days ET ordenados cronológicamente con `sorted(month_days(...))`, high-water mark concatenado entre meses como en T08. La envolvente es conservadora frente al orden indeterminado de prints idénticos, NO DD certificado por broker o firma.
- QCs previos: T10 encontró **113/115** pares de Bid/Ask previos frescos; B02 coincidencia Minute↔Tick **240/240 OHLCV en un día**. No se afirma capacidad de ejecutar sobre esas cotizaciones.

## 2. Resultados de las ocho alternativas, ordenadas como fueron prerregistradas

| Modelo original | Recargo USD/RT | Trades congelados | Neto ajustado USD (no ejecutable) | Profit Factor | DD máximo envolvente Last USD | Margen sobre referencia no verificada $2.000 |
|---|---:|---:|---:|---:|---:|---:|
| Base | $0 | 115 | **+6.220** | 1,39923 | **1.725** | +275 |
| Base +1 tick/lado | $10 | 115 | +5.070 | 1,31277 | 1.815 | +185 |
| Base +2 ticks/lado | $20 | 115 | +3.920 | **1,23278** | 1.905 | +95 |
| Base +4 ticks/lado | $40 | 115 | +1.620 | 1,08940 | **2.085** | **−85** |
| Estrés T04 | $0 | 115 | **+5.102,50** | **1,31826** | **1.797,50** | +202,50 |
| Estrés +1 tick/lado | $10 | 115 | +3.952,50 | **1,23717** | 1.887,50 | +112,50 |
| Estrés +2 ticks/lado | $20 | 115 | +2.802,50 | **1,16195** | 1.977,50 | **+22,50** |
| Estrés +4 ticks/lado | $40 | 115 | +502,50 | **1,02699** | **2.157,50** | **−157,50** |

El Profit Factor del estrés original es **1,31826**, apenas por encima de la pantalla exploratoria **PF≥1,25**. Con **solo 1 tick de precio adicional por lado ($10 RT)** pasa a **1,23717**, **por debajo de la pantalla**. Dos ticks extra dejan solo **$22,50 de margen** sobre un límite histórico de referencia no verificado; cuatro ticks lo superan por **$157,50**. Los recargos reducen el beneficio total linealmente a razón de **$10×115=$1.150** por cada tick extra por lado, pero el PF y el DD dependen de la secuencia de operaciones.

### 2.1 Corrección obligatoria de cronología frente a T08

Al preparar B03, **antes de observar resultados nuevos**, se detectó que `month_days` clasificaba archivos alfabéticamente por contrato; durante rollover, esto podía desordenar fechas ET. B03 recorrió los **días ET cronológicamente** y conservó el mismo motor `mark_trade_envelope` y las mismas operaciones T04.

| Auditoría | DD base Last | DD estrés Last |
|---|---:|---:|
| T08 publicado (orden de archivos por contrato) | $1.750 | $1.825 |
| **B03, orden ET cronológico, recargo 0** | **$1.725** | **$1.797,50** |
| Corrección descriptiva | −$25 | −$27,50 |

La diferencia se registra como **corrección de auditoría cronológica**, sin borrar T08, sin atribuir mejor operativa y **sin convertir ninguna cifra en equity real de fondeo**. Todos los netos/trades Last originales conciliaron exactamente.

## 3. Decisión y siguiente fase

- **Resultado:** `T05_377_COST_FRAGILE_ON_FROZEN_DEV_PATH`. El sistema conserva P&L positivo en ocho recargos, pero deja de superar la pantalla PF 1,25 bajo estrés +$10/operación. También puede superar $2.000 de DD con recargos mayores, bajo un límite meramente **ilustrativo**. **No son certificaciones de fallas reales con tarifas o reglas vigentes.**
- T10 nunca demostró fills reales: con quotes previas frescas en 113/115 extremos, todavía hay incertidumbre de timestamps idénticos, profundidad, cancelaciones, stop/market gaps y latencia; esta incertidumbre **no se resuelve** con un recargo constante.
- **NO comprar cuenta fondeada basándose en T05**, no optimizar el stop/TP o borrar febrero para recuperar PF.
- **NQ-B03 COMPLETADO** como diagnóstico de fragilidad contable, ejecución real **PENDIENTE**. La investigación NQ no está cerrada y T05 se mantiene en biblioteca como benchmark exploratorio.
- **Siguiente NQ-B04:** estabilidad por semana, mes, trimestre/semestre y otros regímenes causales; comprobar robustez de retorno y riesgo antes de abrir nuevas ventanas, comparando las mismas siete muestras y los peores periodos, sin escoger parámetros.
- **Después NQ-B05/B06:** definir una estrategia NQ independiente de T05/T09, prerregistrar mecanismo y comparadores, ejecutar router con capital y DD compartidos, buscar incremento de eficiencia y oportunidades mensuales, sin contar T05-233+377 como segundo alpha.
- La meta económica del portafolio completo sigue > max(15% anual, VOO retorno total, QQQM retorno total), con riesgo comparable, horizonte multianual y ROI de bolsillo separado. **No validado por esta evidencia.**

**Reproducción:** `nq_b03_execution_headroom.py`, `nq_b03_aggregate.py`, `test_nq_b03_execution_headroom.py`, workflow `.github/workflows/nq-b03-t05-headroom-dev.yml` y artifact seguro `b03-seven-month-safe-summary`. Datos privados SHA256 verificados, solo agregados públicos. Ningún período de resultados reservado consultado.
