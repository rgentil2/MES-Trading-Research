# NQ-B05F — PRERREGISTRO INMUTABLE: suficiencia de Last y barras por prints EXISTENTES

Fecha 2026-10-11. Estado: diseño ANTES de código/resultados. **Ninguna estrategia ni parámetro se optimiza** en este bloque. Fuente: exclusivamente NQ `Tick_Last` de los **siete releases mensuales YA EXISTENTES** octubre 2025–abril 2026 en `rgentil2/NQ-Ticks-Dev-2026`, mismos SHA256 y misma ventana de 08:00–12:00 ET, 140 días fuente / 135 previamente elegibles T05. Los mismos ficheros se vuelven a procesar en un runner para QC, **no se adquiere, descarga ni genera NUEVO HISTORIAL de mercado**, ni se compra proveedor, Replay o L2. Si no están accesibles los archivos existentes, registrar BLOQUEO, no sustituirlos por otro proveedor o un intervalo distinto.

## Definiciones causales inmodificables

- 1 print = **una fila Last válida**, independientemente de `qty` negociado. Precios en ticks NQ de $0.25, timestamps UTC 100ns. Day ET `America/New_York` (DST real). Archivo y contrato trimestral deben coincidir con fecha ET.
- QC hard fail: inválidos/no numéricos, qty <=0/no entero, precio fuera de grilla/no finito, tiempo decreciente/fuera de 08:00–12:00 ET, contrato o día ajeno al mes, dato vacío o violación de conservación entre resoluciones; **no eliminar ni corregir filas para mejorar ganancia**. Mismo timestamp se considera ambigüedad de orden, **no corrupción demostrada**. Archivo crudo y hash intactos, no exportar series.
- Cada 5s bin `i` incluye `lo+5s*i <= timestamp < lo+5s*(i+1)`; 2880 bins/día. Histograma interno permite computar sin trades completos en RAM; contar bins sin Last y cobertura 09:40–11:10 ET (1080 bins de 5s: índices 1200..2279).
- Gate de T05 PREEXISTENTE, sin leer retornos: opening range 09:30–09:35 = índices 1080..1139 debe contener Last en **cada** bin; alto-bajo >=4 ticks de precio, en otro caso skip `SKIP_MISSING_OPENING_RANGE` o `SKIP_TINY_OPENING_RANGE`. Reproducir **EXACTAMENTE 140 source / 135 READY / 5 skips**, el denominador no debe cambiar silenciosamente. Estos gates no son selección a posteriori.
- Contextos preregistrados `L=(233,377,4181,10946)` operaciones/prints Last, **dos barras COMPLETAS previas necesarias** para diferencia entre sus cierres. Ancla `08:00 ET`. Para cada decisión de barra de 5s cerrada en `09:40..11:10 ET` (índices **1200..2279**), usar solo `count(Last event timestamp < fin de la barra señal)`. Marcar `n//L >= 2`, barras parciales excluidas; también cobertura a 09:30, 10:00 y 11:10 ET. Incluye todas las decisiones de 5s independientemente de que se opere; no optimizar L ni elegir minutos por P&L.
- Contar `Last same_timestamp`, `same_timestamp_price_change`, saltos entre prints >=60 segundos; no asumir secuencia Last/quotes misma marca, agresor real, L2 ni fills del broker.
- En los agregados NO publicar precios, quotes, timestamps exactos, archivos privados, días de operaciones, trades individuales ni resultado monetario diario. Solo 7 filas mensuales con source/eligible/skips, errores por categoría, totales de prints y cantidades, 5s completeness y elegibilidad de 2 barras por tamaño, y un agregado general con control de 140/135. Si un solo mes falla integridad, no ocultarlo ni corregir datos; Action falla y se documenta.
- **NO leer** NQ Minute H 2025/2026, T 2026-05..09; **NO realizar** backtest, evaluación de retornos o búsqueda de nuevas estrategias en esta auditoría.

## Criterios de cierre

1. Pruebas sintéticas: DST ET/UTC, dos barras completadas en cada L, exactamente cutoff excluye prints a misma marca de cierre, qty no equivale a prints, gaps de 5s detectados, timestamp decreciente y day sealed rechazados **ANTES de apertura de filesystem**. Sin inventar precios.
2. Los siete meses DEV producen manifiestos seguros separados y el agregador exige 7/7, 140/135, sumas de cantidades y conservación y ausencia de apertura OOS.
3. Reportar la disponibilidad real de **233/377/4181/10946** en la ventana sin afirmar que haya alfa o fills reales. Contextos largos quizás no están formados temprano; si no, clasificar insuficiencia en vez de rellenarlos con futuro.
4. Comparar a posteriori con T05 **115 trades +$5102.50 stress, PF1.31826 y PF stress+$10 1.23717** solo como referencia histórica congelada; **no se recalculan ni cambia ninguna operación**.
5. Registrar decisión objetiva sobre si la fuente existente soporta nuevas hipótesis de barra Last; no forzar pruebas nuevas sobre mismo DEV. Actualizar master + log para siguiente bloque; mantener B06–B10 bloqueados.

**Decisión user B05E permanece: ZERO NEW DATA ACQUISITION.** Únicamente reprocesar mismos meses archivados y checksums en GitHub controlado si es indispensable para contar completitud.
