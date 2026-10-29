# NQ S0.28 — Backtest de portafolio ganador en NinjaTrader 8: comparación obligatoria con Python

**Decisión del usuario:** Después de identificar el portafolio NQ M1 ganador, **volver a correr ese mismo portafolio en el Strategy Analyzer de NinjaTrader 8** para detectar errores de reglas, horarios, entradas, salidas, costes, simultaneidad o drawdown. Esta comprobación forma parte de la ruta obligatoria hacia MFFU 50K, NO es una validación opcional.

**Estado actual:** NO hay ganador. No se han ejecutado backtests económicos sobre los 10.000 AST. Los 13 controles de autorización original permanecen 0/13 `PASSED_VERIFIED`; ISV1 2023, ISV2 2024 reservados, 2025–2026 sellados. En S0.28 solo se entrega un contrato de comparación **sintético**, no NinjaScript compilado ni un backtest NinjaTrader real.

## Embudo actualizado: añadir N8 después del portafolio

```text
Generador 10.000 AST (hecho, estructural)
  ↓ 13 gates técnicos y económicos certificados (PENDIENTES)
  ↓ G0 → D0 → D1 → D2 (SIN EJECUCIÓN REAL)
  ↓ ISV1 2023 → ISV2 2024 (RESERVADOS; PROHIBIDO FIT)
  ↓ Portfolio Builder / Portfolio Allocator
  ↓ FREEZE DE LA CARTERA: lista de AST, prioridad, reglas de riesgo,
    SHA, bloque calendario, versión del código y M1 source hash
  ↓ N8a: backtest NinjaScript del portafolio COMPARTIDO con las mismas
    reglas conservadoras (comparador trade-by-trade)
  ↓ N8b: NinjaTrader Strategy Analyzer con su motor Standard M1,
    documentando y estresando las diferencias de fills
  ↓ Comprobación independiente de historial/sesiones/series/horarios
  ↓ Resolución de discrepancias y replay sin modificar la selección congelada
  ↓ Revisión, autorización y elegibilidad para MFFU 50K
```

No hay 'candidatos aprobados N8' y no se asignan resultados a ninguna estrategia sin evidencia real. **No se permite modificar las estrategias tras ver las discrepancias para mejorar el backtest**: cualquier corrección de bug exige versión nueva, justificación técnica y repetir las pruebas exigibles sin contaminar ISV.

## Lo que tendrá que ser idéntico

- **Mismo mercado/datos:** NQ, 1 contrato global entre todas las estrategias, fuente `Minute_Last` M1 2020–2022 de SHA `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8`. Misma resolución OHLC, mismo contrato trimestral exacto (rollover jueves -8 días antes del tercer viernes), sin back-adjust ni empalmes distintos. Para validar períodos posteriores se requiere autorización separada de cada etapa.
- **Mismo reloj real:** `America/New_York` con DST; señales solo con vela cerrada; ventana desde 09:35 ET; nada de nuevas posiciones después de 11:28; flat 11:29; un ID por señal, estructura de barra end-labeled. Timestamps exportados en UTC con sufijo `Z` para evitar interpretaciones de timezone local de la PC.
- **Mismo portafolio:** un único NinjaScript que coordina todas las estrategias, no múltiples estrategias de Strategy Analyzer sumadas como si compartieran un contrato. Prioridad fija, máximo **1 NQ abierto**, no apilar posiciones/opuestas, pausa por pérdida diaria según perfil MFFU 50K exacto y límites de riesgo compartidos.
- **Misma matemática:** señales LONG/SHORT/UNAVAILABLE por cada AST, parámetros de las 132 rutas relevantes seleccionadas, stop inicial, objetivos, trailing/breakeven, caducidad de órdenes pendientes, misma convención de una vela completada. Versión y huella SHA congelada para cada AST y para el portafolio.
- **Misma contabilidad:** US$20 por punto, grid de 0,25 punto (US$5 por tick), comisiones por roundtrip desglosadas y slippage comparables, entrada/salida/orden ejecutada, motivos SL/TP/gap/timeout/flat, PnL por operación y acumulado, DD cerrado y DD intradía según las reglas exactas del programa fondeado.

## NinjaTrader 8: diferencias de motor que NO deben ocultarse

La documentación oficial de NinjaTrader señala que **Standard Historical Fill Processing divide las velas M1 en tres segmentos virtuales** usando la proximidad entre OPEN y HIGH/LOW. No reconstruye necesariamente el recorrido intraminuto real. Python S0.24 usa un modelo deliberadamente más conservador: **SL primero si SL y TP se tocan en la misma vela**. Es habitual que estas dos técnicas produzcan resultados diferentes sin que necesariamente exista un bug. No se permite 'corregir' Python reemplazando el STOP por TP para cuadrar beneficios.

Además, NinjaTrader permite `Fill limit orders on touch`: fijar **FALSE** para el escenario base (nuestro modelo exige trade-through 1 tick, o apertura marketable), aunque la ejecución depende del algoritmo Standard de NinjaTrader y NO garantiza equivalencia exacta con esa regla. La documentación aclara también que NinjaTrader limita el slippage simulado al rango HIGH/LOW de la barra siguiente; Python puede modelar gaps adversos y slippage peores. La diferencia debe registrarse explícitamente, no normalizar precios sin evidencia.

Referencias oficiales:
- https://ninjatrader.com/support/helpGuides/nt8/backtest_a_strategy.htm
- https://static.ninjatrader.com/support/helpGuides/nt8/understanding_historical_fill_.htm
- https://static.ninjatrader.com/support/helpGuides/nt8/historical_order_backfill_logic.htm

**Diseño de doble comprobación cuando exista ganador:**

**N8a — Paridad matemática replicada.** Implementar NinjaScript que use el mismo orden de prioridades, el mismo algoritmo pesimista de fills y las mismas barreras que Python. Registros de señal y de operaciones completos permiten identificar dónde comienza un desacuerdo. Criterio de salida deseado (sujeto a validación): cero señales distintas no justificadas, cero posiciones superpuestas, cero violaciones de cuenta, timestamps exactos, precios mismo tick, contabilidad con diferencia ≤US$0,01 por operación. Afirmar 'paridad' SOLO después de importación correcta y pruebas reales.

**N8b — Backtest independiente con Standard de NinjaTrader.** Ejecutar adicionalmente el Strategy Analyzer M1 nativo en Standard, `Fill limit orders on touch=false`, comisiones y slippage documentados, usando los mismos contratos y el mismo NinjaScript con prioridad de portafolio. Clasificar casos de TP/SL en la misma vela, gaps/limit-touch; si el rendimiento se degrada, reportarlo, incluso si N8a fue idéntico.

El estándar de aceptación final debería incluir beneficio neto y PF con costes, drawdown compartido (incluyendo pérdidas flotantes donde aplique), operaciones por mes, estabilidad anual, períodos sin actividad y tasas de discrepancias. **No basta con que el neto final coincida**.

## Contrato de CSV por operación congelada y comparador S0.28

[Comparador S0.28](nq_m1_v33_nt8_portfolio_parity_contract.py) define el esquema idéntico, en orden fijo:

```csv
session,portfolio_sequence,strategy_id,contract,side,quantity,signal_time_utc,entry_time_utc,exit_time_utc,entry_price,exit_price,commission_usd,net_usd,exit_reason
```

`portfolio_sequence` es la secuencia de operaciones por día de la **cuenta única** (1 y 2 bajo el perfil provisional; reemplazarlo cuando el perfil comprado exacto esté confirmado). Las fechas son locales de Nueva York, timestamps en UTC `YYYY-MM-DDTHH:MM:SSZ`. Se rechazan duplicados, 2 contratos, órdenes contrarias simultáneas, calendarios DST incorrectos, cambio de vencimiento distinto al congelado, operaciones fuera del horario, 2023+ y PnL inconsistente con US$20/punto menos comisión.

Las categorías de discrepancias, cuando lleguen datos de ambos motores: señales/identidad de estrategia, cambio de contrato, tiempo/precio de entrada, tiempo/precio de salida, comisiones, PnL y razones de cierre. Si ambos archivos están vacíos el resultado es **INCONCLUSO**, nunca aprobado.

Los manifests del lado Python y NT8 deberán tener la misma SHA de portafolio, AST, cronograma/priority, fuente, motor Python, NinjaScript y parámetros. El comparador S0.28 RECHAZA cualquier pretensión de portafolio congelado o backtest histórico real en su versión actual. Los hashes artificiales en sus tests son únicamente fixtures y **no** evidencias auténticas de NinjaScript.

**Pruebas ejecutadas:** [S0.28 CI 40804135861 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40804135861), **345 tests técnicos** totales incluyendo 19 pruebas de comparación artificial (DST, grid, rollover, importes, superposición, límites, diferencia de PnL, logs vacíos y prohibición de reabrir 2023–2026). No se ejecutó NinjaTrader ni se modificó fuente M1 real.

## Pendientes para lanzar el primer backtest real del ganador

- Terminar y certificar 13 requisitos originales del motor M1 y de las 132 fórmulas efectivamente utilizadas, reglas exactas MFFU por cuenta/fase y ejecución de G0–D2.
- Seleccionar y congelar estrategias IST/ISV1/ISV2 sin filtración de años; combinar cartera única con drawdown/colisión de señales compartidos.
- Escribir y **compilar dentro de NinjaTrader 8 en Windows** el NinjaScript único del portafolio (AutoStrategy), y su exportación de señales/trades al CSV especificado. Este archivo NO se ha generado ni probado en NinjaTrader y NO debe considerarse listo hasta su compilación y pruebas.
- Importar o validar mismo M1 NQ por contratos en NT8, no usar series de fuentes distintas sin anotar diferencias de datos/horario. Ejecutar N8a y N8b sobre períodos autorizados idénticos y resolver divergencias sin optimización posterior.
- Conservar los resultados congelados, reporte de diferencias y firma de revisión antes de considerar entrada a la cuenta fondeada. No sustituye forward/live fill verificado, ni garantiza beneficios futuros.
