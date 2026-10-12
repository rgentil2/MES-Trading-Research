# NQ-B05H-01 — Prerregistro antes de rentabilidades: expansión de rango y aceleración de prints con alineación de contexto

**Fecha 2026-10-11 (America/Bogota).** Fase: **reglas congeladas ANTES de evaluar el histórico**. Una sola familia económica `H01_PRINT_EXPANSION_CONTINUATION`; no crear 150 variaciones a ciegas. Solo **siete releases originales NQ Tick_Last DEV octubre2025–abril2026**, 140 sesiones fuente/135 elegibles. **PROHIBIDO** descargar/adquirir nueva historia o fuente/Replay/L2. Holdouts T mayo–junio y julio–septiembre 2026 y H 2025–2026 sellados sin tocar.

## Hipótesis económicamente diferenciada de T05

T05 revierte **ruptura fallida de la apertura**. H01 propone algo **distinto**: después de que aumente la frecuencia de transacciones y se expanda el rango en una barra de **233 prints Last**, una ruptura direccional en esa misma barra **CONTINÚA** a corto plazo **solo** cuando barras anteriores completas de **4181 y 10946 prints** confirman tendencia del mismo signo. No usar opening range como disparador, delta agresor, L2, VWAP global de 5s o las señales 5s anteriores. 377 prints se mantiene como **comparador técnico potencial no activo** (no optimizarlo en este test). Fibonacci define longitud candidata, **no** ventaja matemática supuesta.

## Unidad causal y reglas exactas congeladas

Cada barra es umbral de **>= N transacciones Last** (NO contratos); un grupo de igual timestamp es indivisible, la barra cierra solo después de incluirlo completo. Las barras pueden exceder 233/4181/10946. Exige `qty` positivo, precio grilla 0.25 NQ, fecha y contrato DEV válidos, 08:00–12:00 ET. Para una señal al terminar barra 233 en tiempo `T`, leer solo sus dos barras 233 previas `A,B` y **dos barras de 4181 y dos de 10946** cuyo `end_timestamp < T`, además de `C` barra corta recién cerrada. Jamás incluir impresión con timestamp mayor a T o hacer entrada dentro de T. Precio resumen de barra = VWAP aritmético exacto por qty (numerador/denominador enteros); high/low invariante ante el orden dentro del mismo timestamp; sin utilizar `close` del último print.

- Intervalo decisión: **09:30 <= T < 11:15 ET**. La hora solo recorta ventana de ejecución; **no hay barras de 5 segundos, ni de minuto, en el disparador**.
- Dos contextos completos estrictamente anteriores: VWAP de la barra más reciente 4181 vs su anterior, y de la más reciente 10946 vs su anterior, deben avanzar **al menos 1 tick NQ** a favor del lado; último contexto 4181 no más viejo que **40 minutos** y último 10946 no más viejo que **60 minutos**, medidos respecto a T.
- Direccionalidad short 233: `VWAP(C)-VWAP(B) >= +2 ticks` para LONG, <=−2 para SHORT, usando productos cruzados exactos; `high(C) >= max(high(A),high(B)) + 4 ticks` LONG o `low(C) <= min(low(A),low(B)) - 4 ticks` SHORT.
- Expansión: `range(C) >= 8 price ticks` y `range(C) >= 1.25*range(B)` (productos enteros, no redondeo), sin condición de `close` arbitrario.
- Aceleración de prints: duración positiva entre primer y último grupo del bar C y B; duración(C) <= 0.80 × duración(B) (`5*dur(C)<=4*dur(B)`). La barra se mide en número de transacciones no intervalo temporal.
- Si simultáneamente LONG y SHORT (no debería ser posible) **fail closed**. Señales de un mismo lado repetidas se generan solo si **>=10 minutos** desde la anterior señal emitida; máximo **2 oportunidades candidatas H01 por día**, sin tomar decisiones según outcome. No optimizar esos valores post factum.

## QC y comparación de cuenta compartida

Se preserva la muestra de desarrollo histórica **135 días elegibles** usando **solo para comparador/QC T05** las antiguas reglas de opening range; no son señales nuevas y no altera 115 operaciones baseline. Si source day excluido bajo T05, excluir de AMBOS modelos para misma muestra y reportar 5 casos. Se usan los datos Last originales, sin limpiar trades por beneficio, sin elegir reordenamiento rentable; estudiar invarianza de H01 respecto a ORIGINAL/REVERSE/ASC/DESC dentro de equal-timestamp groups con tests sintéticos ANTES de resultados y, si caben recursos, como stress retrospectivo separado. **La ejecución Last continúa incierta aun cuando H01 sea invariante.**

- Rutas congeladas: **`T05_ONLY`** (legacy; únicamente para benchmark, mantiene disparador viejo sin modificar), **`H01_ONLY`**, **`T05_PRIORITY_SHARED_ROUTER`**. Las tres alternativas comparten los mismos días, 1 NQ máximo, **hasta 2 ejecuciones/día**, no superposición temporal, detener nuevas entradas después de P&L diario cerrado <= −$600.
- Para H01 nuevo: stop fijo **24 price ticks NQ (6 puntos)**, objetivo 48 ticks (2R), timeout **300 segundos**; 1ms mínimo + entrada posterior estricta a tiempo `T`, fill conservador con el **peor Last de la primera marca de tiempo elegible**, stop prioritario si stop y TP en una misma marca; ambigüedad en timestamp de entrada implica abortar la tarea, NO omitir la operación silenciosamente.
- Para T05 antiguo mantener stop histórico 25 % de amplitud opening range, limitado a 16–48 price ticks; en caso de señal a mismo instante, **prioridad T05**; H01 no usa esta amplitud ni los bares 5s.
- Escenarios estándar T04: **BASE 1 tick adverso por lado + USD5 RT**; **STRESS 2 ticks adversos por lado + USD7,50 RT**, y sensibilidad contable extra **USD10 por trade RT** SOBRE rutas congeladas (no recalcular stops, capacidad y gates).
- Performance mensual y total en 7 meses: trades, win/loss, net, PF, envolvente adversa Last cronológica, DD closed, frecuencia >=5 operaciones combinadas/mes, H01 attributed trades/net en router, T05 desplazadas, costo estrés y +$10, y solo 1 cuenta de riesgo, NO suma de resultados standalone.
- **Paridad obligatoria antes de interpretar H01:** T05 115 trades, base +USD6220, estrés +USD5102,50, DD estrés +USD1797,50 (magnitud), stress+$10 RT +USD3952,50, DD +USD1887,50; fuente **140/135**. De lo contrario **FAIL** sin alterar baseline.
- **Gates a priori:** router minus T05 extra+$10 net **>0**; router estrés PF>=1.25, estrés+$10 PF>=1.25; DD Last estrés **<USD2000** como REQUISITO ILUSTRATIVO NO firma verificada; >0 operaciones H01 ejecutadas y attributed net >0; retención T05 >=104/115 (>=90%) como indicador de costo de oportunidad; router >=5 trades cada mes; estabilidad dirección por mes. **Fallo de cualquier gate = NO PROMOVER**. Incluir toda la tabla de meses incluso pérdidas; nunca ocultarlas.
- Datos agregados públicos solamente, NO trades/ticks/precios/timestamps privados ni lista diaria; licencia y hashes originales no modificados. No usar resultados de este mismo DEV para diseñar otra variante rescatada sin nuevo prereg / presupuestar su dependencia. **La muestra ya está explorada adaptativamente; esto sigue siendo in-sample, NO OOS o recomendación de comprar fondeo.**

## Orden de ejecución

1. Congelar este documento, versionar motor 233 / señales H01 / runner, test synthetic de no-futuro y invariancia.
2. Validar los 7 releases YA EXISTENTES en runner protegido con SHA256, costo real modelado, T05 paridad y shared router.
3. Publicar todos los meses, PASS/FAIL, interpretación y siguiente paso; actualizar `NQ_PROJECT_MASTER.md` + `NQ_RESEARCH_LOG.md`. No abrir holdout ni datos nuevos.
