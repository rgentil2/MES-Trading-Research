# NQ-B05B / T12 — prerregistro: compresión local + expansión de actividad (NO OR/VWAP)

**Fecha:** 2026-10-11. **Congelado ANTES de resultados T12.** Nueva familia adaptativa NQ `T12`, no la reparación de T11, no hipótesis OOS. Solo DEV 2025-10-15..2026-04-30 (los 7 meses 140 días fuente / 135 elegibles) ya usados en T05/T11. 2026-05/06 resultados reservados, 2026-07..09 sellados; programa histórico H no se abre.

## Deducción

T05 usa **reversión de ruptura fallida del opening range** con barras de 377 prints; B05/T11 aceptaba VWAP y retroceso pero fue negativo y su ablation no-pullback era lógicamente redundante. T12 propone un mecanismo distinto de **contracción de rango local previo a escape direccional con aceleración de transacciones**. Se anticipa que un segmento de precio poco desplazado respecto al régimen 5min anterior, seguido de desplazamiento nuevo y participación creciente, aumenta probabilidad de continuación breve. No usar niveles OR ni VWAP ni la condición de reversión T02. Opening range se utiliza **únicamente para mantener el mismo stop** de T04 y excluir días con OR incompleto.

## Señal causal congelada T12

- Fuente: **Last prints** `(timestamp 100ns UTC, price_ticks NQ, qty)`; un registro no es un contrato y ticks de precio son de 0,25 puntos NQ. Crear barras 5s `[O,H,L,C,prints,qty]`, ancla 08:00 ET; no interpolar barras ausentes.
- Permitir señales al cerrar barra **i** entre **09:40:00 y 11:10:00 ET** (última decisión antes del índice `LAST_SIGNAL`). Deben existir todas las **61 barras** `[i-60..i]` (5 min antes + barra disparadora), con cronología intacta. Después de 11:10 no generar trades.
- **Contexto anterior** de 48 barras `[i-60 .. i-13]` (4 minutos) con high-low `Rprev`. Exigir `Rprev >= 32` ticks de precio (8 puntos). Esto evita etiquetar compresión en sesiones completamente inmóviles.
- **Compresión más reciente** `[i-12..i-1]` (60s antes de trigger), con rango `Rshort` high-low; exigir `Rshort <= max(8, floor(0.40*Rprev))`, además `Rshort>=2` ticks. Es una compresión *relativa*, no basada en mejores meses.
- **Ruptura de compresión en barra i**: para largo cierre `C_i >= Hshort + 2` ticks y cuerpo `C_i > O_i`; corto `C_i <= Lshort-2` y `C_i < O_i`. La barra i no participa en calcular Hshort/Lshort, evitando lookahead.
- **Participación causal**: suma `prints` en **6 barras `[i-5..i]`** (30s, incluye barra trigger cerrada) >= **125%** suma en `[i-11..i-6]` (30s previos); periodo anterior >= **20 prints**. Prohibido leer prints de barras siguientes.
- Un único disparador por barra y **cooldown 60 barras (5 minutos)** tras anterior señal T12, sin dirección preferida y sin seleccionar lado por resultado. No usa información de otros días.

## Controles predefinidos

- `T12_FULL`: compresión + ruptura + aceleración, tal como está escrito.
- `A12_NO_ACTIVITY`: mismo contexto, compresión y ruptura pero se elimina *solo* la aceleración de prints (mismo cooldown).
- `A12_NO_COMPRESSION`: mantener `Rprev>=32`, condición `Rshort>=2`, ruptura y aceleración, pero elimina solo requisito `Rshort<=max(8,floor(.40*Rprev))`. No retener condición que implique matemáticamente la compresión; probar contraste por conteos de señales en dataset antes de interpretar (si son iguales, marcar ablation REDUNDANTE como sucedió en T11).
- Estas ablations son controles relacionados con T12, **no** nuevas fuentes independientes de alpha ni se promocionan selectivamente por mayor P&L.

## Simulador fijo y cartera compartida

- Reusar `nq_t04_execution` y `nq_b05_t11_month.trace` **sin cambios de lógica**, parametrizar nombres de propietarios cuando sea necesario. Dos rutas alternativas `T05_377` y `T12_FULL`, y **un solo router** `T05_PLUS_T12_ROUTER`: por horario de barras, empate resuelto con prioridad fija T05, una posición a la vez, máximo 2 trades/día entre ambas, no entradas si equity intradía *cerrado* <= -$600, 1 NQ, stop 25% OR [16..48] price ticks, TP 2R, 300s, 09:40..11:10 para T12. Ni simulador ni costes existentes se reoptimizan. T05 debe reproducir exactamente 115 operaciones, P&L base +$6220 y estrés +$5102,50, DD 1725/1797.50, en 140/135 días fuente/elegibles.
- Escenarios de costes: base T04 ($5 comisiones RT +1 tick adverse/side), estrés T04 ($7,50 RT +2 ticks adverse/side) y **recargo contable adicional estrés+$10 RT** sobre rutas idénticas, sin recalc SL/TP/riesgo por recargo. No son fills reales, quote-pricing o límites de broker.
- Cada alternativa tendrá conteos por mes, P&L neto, PF estrés, DD adverso continuo Last estimado, y sensibilidad extra+$10; router: trades por owner, solapamiento, capacity, prioridad y cambio **incremental router versus T05**. Meses/ganancias negativas se publican; solo agregados por mes, no datos de precio, timestamp ni trades individuales.

## Criterio predefinido de admisión (exploratorio, no OOS)

**NO PROMOVER** si cualquiera falla: a) incremento de neto de **router estrés+$10** respecto a T05 estrés+$10 <=0; b) DD Last estrés original conjunto >= **$2000** (referencia ilustrativa no verificada); c) PF estrés original router <1.25; d) PF router estrés+$10 <1.25 (conservador); e) T12 ejecutadas en router =0 o P&L atribuible T12 estrés original <=0; f) frecuencia total router <5 trades en cualquier mes; g) muestras/QC, costos/temporalidad o enlace al source fallan. **Extra objetivo no mandatorio:** 5 trades de T12 en cada mes; reportarlo por separado. Requisito OOS y multinálisis familiar pendiente aunque los indicadores pasen en DEV.

- Hipótesis diferenciadora debe verificarse **por mecanismos, no por coincidencia de ganancias**. Si T12 solo desplaza trades T05 negativos sin ganar dinero, rechazar como segunda estrategia independiente al igual que T11. No recortar febrero u octubre retrospectivamente.
- Varios estudios ya usan los mismos 7 meses: NO declarar prueba estadística independiente, no estimar confianza/alpha ajustado como si no hubiera selección histórica.

## Ingeniería y privacidad

- Un solo workflow GitHub Actions con 7 releases privados verificados SHA256, lectura de `NQ-Ticks-Dev-2026` únicamente, rechazar mes prohibido **ANTES** de filesystem. Tests sintéticos incluyen timestamp sin futuro, umbral de rango y breakout, no confundir price ticks con prints, controles no redundantes, router y paridad. Nunca publicar tick raw, trade timestamps, órdenes individuales, archivos licenciados en artifact. No abrir `NQ-Ticks-Sealed`.
- Registrar código y hashes, tests, URL/action, resultados negativos y recomendaciones como `NQ-B05B` en ambos **NQ_PROJECT_MASTER.md** y **NQ_RESEARCH_LOG.md**. Si FAIL de T12, siguiente **B05C nueva hipótesis** o auditoría de ejecución; **B06 permanece bloqueado**. Si PASS exploratorio, B06 conduce evaluación ampliada bajo frozen router y no abre OOS automáticamente.
