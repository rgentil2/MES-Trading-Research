# NQ T189–T208 — cohorte monetaria de 20 hipótesis distintas con 233 prints

**Prerregistro 13-oct-2026 antes de ver outcomes de T189–T208.** Orden del usuario: continuar por bloques monetarios complementarios a T05, NO reducir gates ni optimizar T186. No se interpreta que 20 preguntas son 20 alphas independientes. T05 permanece legado congelado; su antigua gráfica 5s solo para benchmark, las señales nuevas 100% barras **233 prints** completas con timestamp atómico (no 5s nuevas).

### Ejecución única y reglas monetarias congeladas

- **Primer cierre 233 por ventana** ET, nunca buscar la segunda barra favorable. C, D, E son las tres últimas barras 233 *completas*, la barra E dispara la decisión. Calcular VWAP precio ponderado por cantidad Last; duración y volumen de la barra con grupos completos. Tratar falta de dos previas como SIN SEÑAL.
- **Entrada:** exactamente el simulador existente T04/B05H con precio Last hipotético, 1ms de latencia, salida adversa y slippage 2 ticks por lado bajo estrés, 1 NQ, SL 24 ticks, TP 48 ticks, timeout 300 segundos; fee estrés de T04, no tarifa broker comprobada. No usar lookahead ni inferir agresor, bid/ask real o stops precisos a igual timestamp.
- **Router compartido uno-a-uno**: por cada T189–T208 construir alternativa sola y T05+esa alternativa; máximo 2 entradas/día, 1 posición, cierre diario detiene nuevas entradas cuando PnL≤−US$600, prioridad señal cronológica con T05 ante empate exacto. Nunca sumar resultados standalone de las 20 como cartera.
- **Muestra:** exclusivamente 7 meses Last DEV preexistentes oct2025–abr2026 140 fuente/135 READY. SHA256 de los siete archivos. Paridad obligatoria T05 115 trades, +US$5.102,50 estrés, +US$3.952,50 en estrés+$10 RT, DD Last US$1.797,50; cualquier diferencia = FALLÓ. Holdouts mayo–sept2026 y H sellados. Sin datos nuevos.
- **Gates económicos exploratorios simultáneos:** delta de router−T05 en estrés+$10 RT >0, PF router estrés ≥1,25 y extra10 ≥1,25, DD Last estrés ≤US$2.000 (solo referencia, no broker), retener ≥104/115 T05, ≥5 trades router por mes y ≥1 nueva trade ejecutada. Reportar todas las 20, incluso sin señal o no estimables. q/IC90 deliberadamente FUERA de puerta exploratoria, NO fuera de futura validación.
- **Censura conservadora preregistrada:** ante exposición intratimestamp irresoluble en cualquier mes, ambos modelos individual/router para esa candidata se reportan **N/D** durante 7/7 meses, jamás imputar ganancia/pérdida/0, jamás PASS. Si sucede en T05 ABORTAR estudio. El extra10 es contable sobre camino fijo (no recalcula stop diario). No divulgar ticks, trades ni diarios individuales.

## Bloque A: ACTIVITY_TEMPO (09:30–09:45 ET)

| Hipótesis | Pregunta/regla de activación exacta | Estado |
|---|---|---|
| T189 | Duración de E233 ≤2/3 de D233, rango E≥16 ticks y desplazamiento VWAP E−D≥4; seguir desplazamiento | PRERREGISTRADA, P&L N/D |
| T190 | Duración E233≥2×D233 y movimiento D−C≥4 ticks; tomar contrasentido del movimiento D−C | PRERREGISTRADA, P&L N/D |
| T191 | Cantidad total E233≥2×D233 y |VWAP E−D|≥4; continuar | PRERREGISTRADA, P&L N/D |
| T192 | Cantidad E233≤1/2 D233, |VWAP D−C|≥4 y E−D opuesto a D−C ≥2 ticks; seguir giro | PRERREGISTRADA, P&L N/D |
| T193 | Grupos timestamp íntegros E233/prints≤0,65, rango E≥20 y |VWAP E−D|≥4; revertir | PRERREGISTRADA, P&L N/D |

## Bloque B: MICRO_AUCTION_LEVELS (09:50–10:10 ET)

| Hipótesis | Pregunta/regla de activación exacta | Estado |
|---|---|---|
| T194 | VWAP E233≥máximo high de las dos 233 anteriores +2 ticks; largo | PRERREGISTRADA, P&L N/D |
| T195 | VWAP E233≤mínimo low de las dos 233 anteriores −2 ticks; corto | PRERREGISTRADA, P&L N/D |
| T196 | High E233≥máximo high de 2 previas+4 y VWAP E por debajo de ese máximo; corto | PRERREGISTRADA, P&L N/D |
| T197 | Low E233≤mínimo low de 2 previas−4 y VWAP E por encima del mínimo; largo | PRERREGISTRADA, P&L N/D |
| T198 | Rangos D233 y C233≤12, rango E≥20 y |VWAP E−D|≥4; seguir quiebre | PRERREGISTRADA, P&L N/D |

## Bloque C: VOLUME_PRICE_EFFICIENCY (10:25–10:45 ET)

| Hipótesis | Pregunta/regla de activación exacta | Estado |
|---|---|---|
| T199 | Volumen E233≥1,5×D233, |E−D VWAP|≤2 y |D−C VWAP|≥4; revertir dirección D−C, proxy Last NO absorción real | PRERREGISTRADA, P&L N/D |
| T200 | Volumen E233≤0,7×D233 y |VWAP E−D|≥6; seguir desplazamiento E−D | PRERREGISTRADA, P&L N/D |
| T201 | Rango E233≥2×D233, volumen E≥1,2×D, |VWAP E−D|≥4; continuar | PRERREGISTRADA, P&L N/D |
| T202 | Rango E233≤0,5×D233, volumen E≥D, |VWAP D−C|≥4; revertir D−C | PRERREGISTRADA, P&L N/D |
| T203 | Volumen E233≥2×D233, rango E≤rango D, |VWAP E−D|≥3; continuar | PRERREGISTRADA, P&L N/D |

## Bloque D: MICRO_SEQUENCES (11:00–11:20 ET)

| Hipótesis | Pregunta/regla de activación exacta | Estado |
|---|---|---|
| T204 | VWAP C<D<E por ≥2 ticks cada paso, rangos C<D<E estrictos; largo | PRERREGISTRADA, P&L N/D |
| T205 | VWAP C>D>E por ≥2 ticks cada paso, rangos C<D<E estrictos; corto | PRERREGISTRADA, P&L N/D |
| T206 | VWAP E−D opuesto a D−C, |E−D|≥5, |D−C|≥2, rango E<rango D; seguir giro E−D | PRERREGISTRADA, P&L N/D |
| T207 | Duración E≥1,5×D y D≥1,5×C, rango E≤12, |VWAP D−C|≥4; revertir D−C | PRERREGISTRADA, P&L N/D |
| T208 | Duración E≤1/2 D, cantidad E≥1,5×D, |E−D|≤2, |D−C|≥4; revertir D−C | PRERREGISTRADA, P&L N/D |

**Evidencia y conclusión pendiente**: nunca escribir P&L ni 'PASS' de esta cohorte hasta Action final SUCCESS y artifact SAFE 7/7 verificados, con ambos documentos maestro y log actualizados tras cada bloque. Los resultados de T169–T188 siguen intactos y no sirven como OOS.
