# NQ S0.31 — Primera búsqueda histórica exploratoria real IST M1 (cohorte de control de 120 reglas)

**Fecha:** 2026-10-29. El usuario solicita **empezar a buscar estrategias**, sin seguir aplazando el inicio. Esta etapa es una búsqueda histórica **exploratoria** sobre 2020–2022 usando un catálogo anterior, preregistrado de **120 reglas de control** con 5 familias: breakout, reversal, continuation, VWAP pullback y volatility expansion; 3 variantes × 2 lookbacks × 2 stops × 2 objetivos por familia. **No se evaluó la cohorte congelada de 10.000 AST ni los 132 indicadores** en esta etapa.

## Diseño exacto

- [Implementación](nq_m1_v36_ist_exploratory_120.py), separados del motor certificado y del ledger de 10K.
- ZIP privado original fuente **SHA256 `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8`**, validado antes de abrir los 15 miembros NQ `Minute_Last` 2020–2022. Debe coincidir con auditoría de 735 sesiones completas, 39 parciales excluidas y 12 rollovers.
- Señales de cierre 09:35–11:27 NY como máximo; entrada MARKET en apertura de barra siguiente 09:36–11:28 con dos ticks adversos; salida SL conservadora primero si SL y TP tocan simultáneamente; objetivo LIMIT requiere atravesar al menos un tick o ser marketable en apertura; cierre 11:29 ET con dos ticks adversos; comisión provisional **US$4.68 round-trip**.
- 1 contrato NQ por regla, máximo 2 entradas por día, pausa si PnL cerrado diario cae bajo -US$600, stop inicial de referencia **≤ US$300, incluyendo slippage de stop y comisión**. Estas reglas NO confirman el perfil oficial MFFU ni garantizan que la orden se cancelaría antes del fill real.
- Para cada alternativa: beneficio neto en USD, gross profit/loss, PF solo si pérdidas brutas positivas, DD máximo de **operaciones cerradas** (no intradía flotante), número de operaciones, frecuencia de meses con ≥5 operaciones, meses sin trades, años positivos y resultados anuales. No se suman las 120 alternativas como cartera; compartirían cuenta y deben recomputarse mediante portfolio builder.
- **No** se evalúan límites de drawdown flotante/floor EOD real ni colisiones entre estrategias, ni slippage de libro real. Ningún resultado del piloto se declarará ganador operativo, aprobado MFFU o liberado de los 13 controles técnicos.
- Un backtest de 2020–2022 sigue sujeto a múltiples pruebas y data-snooping: históricamente parte del material fue inspeccionado en otros experimentos; no se publicarán p-values de validación OOS no ejecutados. **2023/2024 sin abrir** y 2025/2026 sellados.

## Implementación y evidencia inicial

Preflight [run #40869842823](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40869842823) **363/363 pruebas PASS** (8 nuevas). Los tres fallos de la primera corrida [#40869676090](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40869676090) fueron relativos a pruebas sintéticas: falta de contador opcional y secuencias artificiales sin una señal real; quedaron corregidos sin alterar las reglas ni los resultados reales.

La primera ejecución de mercado deberá producir un artefacto privado **solo agregado**: 120 filas de resumen por regla, no OHLC, sin señales ni operaciones individuales. Recuentos y SHA de origen deben persistirse junto al archivo maestro.

**Decisión de alcance:** S0.31 es un **pilot de control** que permite detectar problemas de fills, costes y frecuencia sobre la fuente IST. La búsqueda masiva de la cohorte 10K con 132 fórmulas requiere implementar adaptador económico propio y evidencia del resto de validaciones; el **N8 NinjaTrader 8** sobre el portafolio ganador congelado continúa siendo obligatorio después de ISV/Portfolio.
