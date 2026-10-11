# NQ T05 — Barras de 233 / 377 operaciones: resultados DEV 2025-10–2026-04

**Fecha 2026-10-11. Estado: EXPLORATORY, NOT FOR LIVE OR FUNDED TRADING.** Registro de fórmulas ANTES de outcomes: [NQ_T05_FIB_TICK_BARS_233_377_PREREG_2026_10_11.md](./NQ_T05_FIB_TICK_BARS_233_377_PREREG_2026_10_11.md). [Prueba inicial 4/4 PASS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38163029842). [Siete meses 7/7 PASS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38163149913). Datos Last NQ privados de Dev, SHA256 mensual verificado y ningún minuto de outcome mayo–junio ni periodo sellado julio–septiembre 2026 abierto.

El usuario utiliza barras NinjaTrader de **233 o 377 ticks** para ES. Aquí significa **233/377 registros/operaciones Last por barra**, sin fijar duración y **NO movimiento del precio de 233/377 ticks**. Construimos barras completas reiniciadas a **08:00 ET** (inicio del fichero de NinjaTrader); el anclaje puede diferir de una gráfica NinjaTrader con sesión electrónica completa. Es una hipótesis de cambio de dirección/contexto de segundos-minutos, **NO HFT ni optimización de latencia**.

## Reglas T05 y comparador

- **T02_PARENT:** retorno a rango de apertura tras ruptura fallida + desaceleración de prints (5s), señales 09:40–11:10.
- **T05_233:** mantener T02 si el último cierre de barra **233** completa se mueve en la dirección de la reversión frente al cierre de la barra 233 anterior.
- **T05_377:** mantener T02 si el último cierre de barra **377** completa todavía refleja movimiento **opuesto** a la dirección de reversión, frente a su barra 377 anterior.
- **T05_233_AND_377:** exigir ambas, buscando tendencia previa contraria en 377 con giro temprano en 233.
- Barras solo **estrictamente anteriores** al cierre de la barra 5s generadora de señal. Se mantiene el tick Last individual para entrada/salida hipotética. Misma política previa T04: 1 NQ, máximo 2 trades/día, stop dinámico predefinido acotado 16–48 ticks, TP 2x stop, time stop 300s, base **comisión supuesta USD 5 RT +1 tick adverso/side**, estrés **USD 7,50 RT +2 ticks adversos/side**. Costes NO verificados con proveedor de fondeo.

## Resultados de 140 sesiones de origen / 135 aptas (7 meses)

| Cartera (simuladas de manera alternativa) | Señales elegibles | Trades simulados | P&L modelo base USD | P&L modelo estrés USD | Media/trade base USD | Meses positivos base | Max DD cerrado en curva diaria base / estrés USD | Max DD Last aproximado **dentro de un mes** base / estrés USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **T02_PARENT** | 298 | 190 | **+8.420,00** | +6.860,00 | +44,32 | 6/7 | 2.740 / 2.912,50 | 3.175 / 3.367,50 |
| **T05_233** | 169 | 142 | +5.510,00 | +4.115,00 | +38,80 | 6/7 | 2.335 / 2.837,50 | 1.940 / 2.035 |
| **T05_377** | 137 | 115 | +6.220,00 | +5.102,50 | **+54,09** | 6/7 | **1.375 / 1.450** | **1.255 / 1.310** |
| **T05_233_AND_377** | 59 | 59 | +5.395,00 | +4.657,50 | **+91,44** | **7/7** | **1.250 / 1.297,50** | **1.265 / 1.325** |

**Advertencias sobre DD:** `max DD cerrado` se calcula sobre equity de fin de día, enlazando los siete meses. `DD Last dentro de un mes` es un **máximo entre los DD mensuales**, no el máximo flotante calculado de manera continua sobre toda la curva de siete meses; falta auditoría de equity flotante continua para aprobar reglas fondeo. Últimos precios `Last` no son fills garantizados. Riesgo intrames puede estar subestimado si hay gaps, órdenes reales y reglas trailing sobre máximos intradía.

## Resultado mensual de T05_377 frente a 233+377

| Mes | 377 trades | 377 base USD | 377 estrés USD | 233+377 trades | 233+377 base USD | 233+377 estrés USD |
|---|---:|---:|---:|---:|---:|---:|
| Oct-25 | 15 | +495 | +137,50 | 7 | +790 | +497,50 |
| Nov-25 | 8 | +830 | +760 | **2** | +900 | +885 |
| Dic-25 | 22 | +1.655 | +1.450 | 14 | +285 | +155 |
| Ene-26 | 19 | +1.710 | +1.572,50 | 9 | +630 | +552,50 |
| Feb-26 | 13 | **−725** | **−827,50** | **4** | +510 | +490 |
| Mar-26 | 21 | +1.520 | +1.372,50 | 13 | +1.030 | +922,50 |
| Abr-26 | 17 | +735 | +637,50 | 10 | +1.250 | +1.155 |

## Deducción falsable

**233 aporta un cambio temprano de orientación, 377 aporta contexto de impulso previo.** En este desarrollo específico el filtro 377 logró 115 trades en siete meses (~16,4 trades/mes de calendario), más expectativa/trade que T02 padre y menos DD simulado; dejó un mes negativo febrero. La combinación 233+377 elevó la media neta/trade (~USD 91) y resultó positiva en cada uno de los siete meses, pero redujo frecuencia a **59 trades (~8,4/mes)**, con dos meses que no llegan al umbral orientativo de **cinco trades/mes**. La disminución de trades explica parte de la reducción de DD y debe evaluarse contra exposición/actividad en riesgo equivalente. Es desarrollo ya observado; NO es evidencia fuera de muestra.

**La hipótesis nueva no cambia el tick mínimo de precio** de NQ (0,25 puntos / USD 5 por tick para NQ), ni necesita ticks individuales como gráfico visual todo el tiempo. Los 233/377 son una transformación del flujo Tick Last; conservar raw para todos los stops y QA.

## Gate pendiente antes de fondeo

1. Auditar **equity flotante continua**, max trailing equity DD y pérdidas diarias **según reglas vigentes específicas de la firma**, con fricciones verificadas, stop gaps y slippage realista. Comparar T05_377 y T05_233_AND_377 con T02 bajo mismo riesgo, tanto *por trade* como *por sesión y mes*.
2. Revisar si el **anclaje 08:00 ET** de las barras 233/377 coincide con lo que el usuario observa en NinjaTrader al operar ES/NQ; si no, es **una prueba nueva** y no debe reemplazar selectivamente la primera tras observar los resultados.
3. No declarar alpha confirmada por 7/7 meses. Cuatro variantes y dos costes **en desarrollo**; sin Holm/corrección de selección confirmatoria, broker real, ni conciliación Tick vs Minute completa, no afirmar 15% CAGR/ROI ni posibles payouts.
4. Si tras las auditorías de ejecución el candidato es viable, **congelar** todos los parámetros y evaluar **mayo–junio 2026** como validación interna una única vez. **Julio–septiembre 2026** continúa sellado hasta la estrategia final, reglas SL/TP, sizing y coste fijados.

**Estado de decisión:** mantener T05_377 como posible candidato por frecuencia y drawdown; T05_233_AND_377 como posible candidato selectivo condicionado a frecuencia; conservar T02 y T05_233 como comparadores. Ninguno es todavía `VALIDATED_FOR_TRADING`.
