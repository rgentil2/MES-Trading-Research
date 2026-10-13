# Paso D — Puerta técnica de Python a NinjaTrader SIM (NO fondeo) · 2026-10-13

**Propósito:** impedir que una señal rentable en backtest Python se transforme en una estrategia diferente al portarla a NinjaTrader. Documento de ingeniería y control de errores; **ningún NinjaScript entregado ni SIM ejecutado aún**. El proyecto en prioridad sigue investigación por bloques completos, sin abrir OOS ni comprar data nueva.

## Momento correcto para entrar a NinjaTrader

- **Se permite prototipo SIM antes de confirmación estadística** si se trata de una de las estrategias con lógica/entradas/salidas congeladas y sirve para detectar divergencias de datos o ejecución; etiquetar `PORTABILITY_EXPERIMENT_ONLY`, nunca `VALIDATED_TRADING_SYSTEM`.
- **No se permite fondeo/cuenta real** hasta que la cartera tenga valor monetario incremental positivo robusto con costos reales, DD *floating* de cuenta y reglas aplicables, histórico genuinamente independiente cuando se autorice, y evidencia de fills o simulación prudente revisada.
- No tenemos que aprobar las 208 hipótesis ni preparar ocho estrategias juntas. Pasar de forma **reversible** una candidata bien especificada y usar la disparidad NinjaScript-Python para medir riesgo de modelo, no retunear signos/horarios para que gane.
- **No confundir muestra:** T Last DEV oct2025–abr2026 (7 meses) no equivale al programa H minuto 2020–2024; no sumar curvas ni cambiar 1NQ a 1MNQ multiplicando resultados.

## Condiciones de paridad obligatorias

| Control | Requisito comprobable NinjaTrader vs Python | Fail closed |
|---|---|---|
| Source | Instrumento y contratos/rollover, zona America/New_York ET, trading-hours template 08:00–12:00 y elegibilidad en cada fecha | Sí; no abrir sealed ni buscar resultado tras ver PnL |
| Evento Last | Un print del archivo licenciado = una fila, timestamp UTC con precisión fuente; `qty` original; preservar grupos de tiempo idéntico ATÓMICOS | Sí: la llamada `OnMarketData` no asegura una correspondencia idéntica con archivos tick si la importación agrega eventos |
| Barras de transacciones | 233/377/4181/10946 **contadas por filas Last completas**, no por contratos negociados; reset 08:00 ET; si grupo timestamp rebasa conteo, cerrar TODA la marca temporal | Sí: barras nativas `Tick` de NinjaTrader NO se dan por equivalentes sin cotejo |
| Instante de decisión | Nunca decidir con una barra incompleta, ni dentro de un grupo de Last que todavía puede tener otro evento con el mismo timestamp; decisión solo tras siguiente grupo cronológico confirmado | Sí |
| Precio de ejecución | Comparar señal → decisión → llegada de orden → fill simulado bid/ask/spread/slippage; Last no implica precio realizable ni prioridad en cola; no usar `Close[0]` como fill verificado | Sí |
| Riesgo y posición | Máximo de posiciones de **una cuenta**, stops reales y OCO, TP, timeout, gate diario, prioridad de señales y riesgo por contrato, incluyendo otros sistemas si coexistieran | Sí |
| Orden temporal | Stop primero si grupo ambiguo; más adverso si gaps; no recrear trades ambiguos como ganancias | Sí |
| Estadística | Paridad de lista de decisiones/entradas/tamaños/salidas por día (datos **privados**, no publicar). Publicar solo métricas agregadas, N, causas de desacuerdo, DD Last vs DD equity de SIM | Sí |

**Detalles delicados:** T05-377 es LEGACY con disparador de 5s + filtro de barras de 377 transacciones, no algoritmo puro 377; T147 usa primer cierre atómico E377 10:00–10:15, último contexto 4181, riesgo mixto NQ/MNQ y entradas Next Atomic Group. Por lo tanto, portar T147 con `BarsPeriodType.Tick` sin comprobar el criterio de conteo no es reproducción; portar T05 sin 5s cambia completamente la señal.

## Flujo de prueba técnico, acotado

1. Definir **una** especificación congelada (ID, versión de JSON/reglas, timestamps ET, costos/contratos, OCO/stop/TP, máximo órdenes/día).
2. Implementar adaptador de ticks/Last que mantenga grupos completos por timestamp; tests deterministas en secuencias artificiales que incluyan empates, salto de precios, cierre por rollover, DST, falta de ticks.
3. **Sin optimizar**, confrontar secuencia privada de señales y órdenes NinjaTrader vs Python con la MISMA muestra de desarrollo ya existente. Exigir paridad exacta de señal y causa documentada de todo desacuerdo de entrada/stop/target antes de comparar PnL.
4. Paper/sim para órdenes y ejecución; reportar comisiones, spread, fill realista, drawdown flotante, stops diarios y pausas. Si falta fuente para reconstruir el fill, N/D, no inventar trade.
5. Solo al pasar gates estadísticos, económicos, ejecución y riesgo de firma se consideraría una evaluación MFFU 50K real.

## Decisión por bloques

El paso actual es T-C **G0/D0 veinte candidatas**, no traducción prematura de T209–T228: ninguna de esas veinte ha demostrado siquiera activación adecuada hasta conocer G0/D0. Sin embargo, este documento deja la salida técnica hacia NinjaTrader preparada y acotada. Al cerrar T-C, pasar al control D/SIM en lugar de volver a optimizar T05 o abrir más variantes sobre la misma DEV.

**Estado:** `SIM_PARITY_SPECIFICATION_DOCUMENTED_NO_NINJASCRIPT_NO_SIM_RUN`; gate a fondeo=NO.
