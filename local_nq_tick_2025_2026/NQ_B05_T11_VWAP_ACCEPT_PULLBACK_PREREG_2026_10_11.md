# NQ-B05 / T11 — Prerregistro de hipótesis NQ independiente: aceptación de VWAP + retroceso + actividad

**Congelado el 2026-10-11 ANTES de leer un solo resultado T11.** Universo DEV 2025-10-15..2026-04-30, 7 meses/140 días fuente; mayo–junio reservado para validación y julio–septiembre sellado. H 2025/2026 sellado. Estos siete meses ya han servido para construir T05; por tanto T11 es *exploración adaptativa*, NO OOS estadísticamente independiente.

## Motivación causal y contraste

- **T05-377** apuesta por reversión de ruptura fallida del opening range con participación desacelerada; tiene 115 trades y fragilidad a costes en B03/B04. **T09** trampa rápida falló como complemento.
- **T11** plantea mecanismo *opuesto y no condicionado a T02*: si el precio acepta dirección por encima/debajo del VWAP de la sesión cash y luego vuelve al VWAP sin perder la aceptación, una reanudación de actividad puede sustentar continuación intradía. No usa ruptura ni reentrada de niveles del opening range para señal. Puede usar ancho opening range únicamente para **mismo stop de T04** que T05.
- No se afirmará que VWAP, Fibonacci o aceleración tienen ventaja estadística hasta estimar un cambio NETO **del router común** frente al mismo T05 bajo estrés y costes extra.

## Construcción causal de la señal T11

- Tick exportado es cada fila Last PRINT, no un contrato ni el tick mínimo de precio; precio representa grid de 0,25 NQ y volumen viene de cantidad `qty`.
- **VWAP real de prints**: `sum(price_tick * qty) / sum(qty)` desde **09:30:00 ET** hasta la **barra de 5 segundos completada**; no usa Bid/Ask ni sesión futura, se reinicia todos los días. Barras LAST 5s se anclan 08:00 ET, sin imputar bares faltantes.
- Señales una vez cerrada la barra 5s `i`, hora desde **09:40 hasta antes 11:10 ET**, y solo si las 30 barras precedentes y la actual están completas; `LAST_SIGNAL=2280` como en T04.
- Para dirección `s∈{+1,-1}`: **aceptación** en barras `i-30 ... i-7` (24 barras): al menos **18 de 24** cierres a **2 ticks de precio** o más al lado `s` del VWAP que existía AL cerrar cada barra; y barra `i-6` al menos **6 ticks** al lado del VWAP.
- **Retroceso causal** en las seis barras `i-6 ... i-1`: para largos al menos una `low <= VWAP_de_esa_barra + 3 ticks`, para cortos alguna `high >= VWAP_de_esa_barra - 3 ticks`; cierres durante el retroceso nunca a más de 8 ticks en contra del VWAP contemporáneo. Ninguna condición usa barras siguientes.
- **Reanudación**: cierre de `i` a al menos 2 ticks del VWAP en dirección de operación y cuerpo de 5s en la misma dirección (close > open largo / close < open corto); cierre `i-1` no mayor que VWAP+2 para largo (análogo corto). **Actividad:** suma prints `i-5...i` >= **115%** del conteo `i-11...i-6`, con conteo anterior >=20. La actividad solo incluye prints ya vistos.
- **Cooldown:** 60 barras de 5s (5 minutos) desde la señal T11 anterior, independientemente del lado. Un mismo bar nunca crea simultáneamente long y short; resolver conflicto como NO SIGNAL.
- Si opening range 09:30–09:35 no tiene barras completas o ancho <4 ticks, excluir día idéntico a T05.

## Ablations prerregistradas (NO estrategias independientes)

1. `T11_FULL`: todas las condiciones.
2. `A11_NO_ACTIVITY`: misma aceptación + retroceso + reanudación pero sin volumen de prints, mismo cooldown.
3. `A11_NO_PULLBACK`: misma aceptación de 24 cierres y cierre de barra `i-6`, reanudación y actividad, **sin necesidad de tocar VWAP** en seis barras previas, mismo cooldown. Siguen presentes las condiciones de no perder VWAP y cruce de cierre anterior; esto es un control mecánico, no nueva estrategia.

Ninguna ablation se seleccionará por max P&L para reetiquetarla T11; resultados positivos y negativos se registran completos. Recuento no implica independencia.

## Ejecución, riesgo y comparadores

- Reusar sin cambios `simulate_single_trade`, `risk_policy` y `simulate_portfolio` T04: 1 NQ, apertura de rango 09:30–09:35, stop = 25% OR [16,48] ticks, objetivo = 2R, expiración 300s, señal al fin de barra+1ms, máximo 2 trades al día, no simultáneos, no nueva entrada si P&L **cerrado <= -$600**. Ventana límite cierre 11:30 ET.
- Estimar para `T05_377` benchmark, `T11_FULL`, `A11_NO_ACTIVITY`, `A11_NO_PULLBACK`, y router compartido `T05_PLUS_T11_FULL` **con PRIORIDAD FIJA T05 cuando coinciden en la misma barra**; router ordenado por tiempo para el resto; la misma cuenta de riesgo no permite ocupar dos trades a la vez.
- Estimar escenarios T04 **base** ($5 fee RT y 1 tick adverso/lado) y **estrés** ($7,50 fee RT y 2 ticks adversos/lado). Sensibilidad adicional estrés **+$10 fijos RT** sobre rutas congeladas por modelo **sin reevaluar stops, daily stop ni decisiones**; en su informe distinguir ese ejercicio contable de un nuevo backtest.
- Paridad obligatoria: T05 reproduce 115 trades, +$6.220 base, +$5.102,50 estrés en los 7 meses. Si no hay paridad, no interpretar T11 ni el router.
- Medidas de todos los 7 meses: oportunidades y trades, winners/losers, P&L neto, PF, min trades/mes, negativos por mes, DD Last envelope para T05,T11,router si técnicamente factible; aportación incremental `router menos T05` comparando dos **cuentas alternativas** (NO suma de backtests autónomos); enrutador con atribución por origen y oportunidades perdidas por overlap / límite.
- **Gate primario predefinido** de segunda estrategia: `router estrés+$10 supera T05 estrés+$10` en neto, `router estrés original DD` no mayor que referencia ilustrativa $2.000 y sin violar mismos límites; estrés original PF conjunto ≥1,25 y bajo +$10 preferible PF ≥1,25; al menos **5 oportunidades ejecutadas por mes** de contribución adicional solo si factible sin desplazar T05. Si no se cumplen gates, T11 no se promueve, aunque standalone gane. No inventar fills reales ni condiciones de una firma.
- El gate no es inferencia estadística formal (múltiples búsquedas adaptativas; al menos T09 antes). Una sola familia T11, control de búsqueda retrospectiva y reporte de todos los comparadores; no atribuir p-valores validados ni abrir OOS.

## Seguridad y continuidad

Prohibido publicar precios, fills, trades individuales, timestamps o archivos NinjaTrader. Usar solo resúmenes por **mes de DEV** en artifacts, SHA256 del release original verificado antes de procesar; no tocar `NQ-Ticks-Sealed`. Tests sintéticos para anti-lookahead, frontera 09:30, cooldown, prioridades y paridad de router con T04. Registrar aun con 0 trades o resultado FAIL en `NQ_PROJECT_MASTER.md` y `NQ_RESEARCH_LOG.md` después de la ejecución. El siguiente paso **B06** solo incorpora T11 si su mejora incremental pasa los umbrales; de lo contrario guardar la hipótesis negativa y revisar otro mecanismo, sin reoptimizar los números de T11 vistos en esta muestra.
