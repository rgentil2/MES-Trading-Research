# NQ T14–T19 — cartera de PREGUNTAS nuevas, no 6 modificaciones de T05

**Prerregistro de programa 2026-10-12, Bogotá. Estado inicial: T14–T16 registro de señales/viabilidad solamente; T17–T19 cola de investigación sin ejecutar.** Este bloque responde a instrucción expresa del usuario de **dejar de sobreoptimizar T05** y explorar más mecanismos distintos. Nombres de hipótesis consecutivos T14–T19 del programa **tick Last**, diferentes del H01–H150 de velas de un minuto.

## Invariantes
- T05-377 sigue **CONGELADA** y solo benchmark para pruebas económicas posteriores, **NUNCA filtro de elegibilidad de señal**. No ajustar parámetros T05, no más trabajos B05L para “arreglarla”. La selección adaptativa previa se contabiliza en toda inferencia futura.
- Usar SOLO NQ Last ya disponible de los siete releases DEV 2025-10 a 2026-04. SHA256 al transportarlo dentro de GitHub Actions, sin adquirir data nueva, sin Market Replay/L2, sin 5 segundos NI minutos como unidad de señal nueva, sin abrir T mayo–sept 2026 ni H holdouts.
- Trade-print bar = fila Last por ejecución, **NO cantidad de contratos**. Barras 377 prints, con timestamps iguales tratados como grupo indivisible; 4181/10946 solo contexto si se completa causalmente. No inferir agresor Bid/Ask, delta, absorción real, L2 ni fills del export.
- **Unidad de evaluación definitiva:** retornos diarios por sesión incluyendo 0, bootstrap por bloques 5 sesiones B10000/sensibilidad 3/10, intervalo IC90 del efecto neto, p unilateral exploratorio; BH sobre toda la familia FINITA preregistrada de preguntas ejecutadas (sin alterar número de pruebas), Holm confirmatorio separado si procede. 135 sesiones elegibles no son 135 eventos independientes. Incluso señal “favorable” in-sample no prueba alfa ni compra fondeo.
- **Primera pantalla T14–T16 SOLO FASE 0:** cobertura, señales causalmente construibles, distribución mensual y consistencia en todas las sesiones. **NO P&L**, PF, p o q en esta pantalla. No contar N señales como N fills ni aprobar ganancias. No relajar filtros si una pregunta arroja 0 señales.
- **Etapa económica posterior, NO ejecutada en la Fase 0:** T14/T15/T16 comparadas individualmente y contra una cartera compartida 1 NQ, capacidad máx 2 trades/día, stop de nuevas entradas −$600 realizado, comparador T05 congelado, costes estrés y +$10 RT; registrar no desplazamiento, PF/DD y respuesta incremental. Stop/TP y horario se deberán CONGELAR en un prerregistro económico separado ANTES de calcular retornos. Prohibido sumar P&L standalone o seleccionar mejor familia por el resultado del screen.
- En la tabla pública cada hipótesis tiene ID, pregunta falsable, variable informativa, unidad, N señales, N trades, IC90, q BH y gates explícitos; métricas no probadas = N/D, **NO EVALUADA**, nunca “cumple”.

## Primer lote T14–T16: mecanismos distintos (preregistro de condición de señal)

Ventana común **09:45–11:00 ET**, sobre cierre completo de barra >=377 prints Last; máximo **una oportunidad por sesión por hipótesis** para evitar múltiples resultados altamente solapados. Estadística de VWAP racional exacta de cantidades negociadas, no “bar close” arbitrario. Tres señales generan solo `(timestamp,side)` privado dentro de runner, reportando públicamente únicamente conteos mensuales, 140/135 source coverage. Ninguna señal antes de terminar su grupo de igual timestamp.

| Hipótesis | Pregunta falsable | Regla de señal congelada | Predicción / diferencia con anteriores |
|---|---|---|---|
| **T14 Persistencia suave** | ¿Tres barras 377 de avance VWAP pequeño y consecutivo anticipan continuación sin ruptura explosiva? | A,B,C terminadas; para signo s, `VWAP(B)-VWAP(A)>=2 ticks*s`, `VWAP(C)-VWAP(B)>=2 ticks*s`; rango C <= rango B y rango C <=24 ticks; prioridad primer evento/día | Continuación por persistencia sin el criterio de expansión y aceleración T H01; no VWAP de valor H02 |
| **T15 Nivel redondo confirmado** | ¿Una aceptación sobre/bajo nivel cada **25 puntos NQ=100 ticks de precio** precede continuidad? | B VWAP ≥4 ticks antes del nivel; C VWAP ≥4 ticks después; C.low≥nivel (long) o C.high≤nivel (short). C señal solo cuando grupo timestamp C termina; **nivel es múltiplo de 100 price ticks** determinado antes de observar resultado | Microestructura de puntos de referencia, no ruptura de los 5 minutos de apertura ni de 5s |
| **T16 Esfuerzo sin desplazamiento** | ¿Duplica contratos por print sin avanzar precio y precede giro contrario al movimiento previo? | A→B VWAP avanza >=4 ticks en signo s; C **qty/print ≥2×** B qty/print por productos cruzados enteros; rango C <= mitad del rango B y >=1tick; VWAP(C) dentro de ±2 ticks VWAP(B) (razón exacta). Señal lado **−s** | Absorción como **proxy Last**, NO delta de agresores ni shock de print aislado T13 |

**Reglas adversariales:** la construcción de barras no depende del orden de filas dentro de igual timestamp (VWAP/rango/qty invariantes); si B y C acaban en mismo timestamp, rechazar; los 3 mecanismos pueden coincidir sin declararlos independientes a efectos estadísticos y se marca solapamiento. No calcular rentabilidad si la simulación de Last no identifica orden del timestamp de entrada.

## Segundo lote de preguntas T17–T19 — backlog, NO test ejecutado

| Hipótesis | Pregunta | Diferencia causal | Variable primaria futura |
|---|---|---|---|
| **T17 Intensidad vs volatilidad** | ¿Variación fuerte de **prints/segundo** sin volatilidad contemporánea anticipa expansión de amplitud, independientemente del sentido? | PREDICCIÓN DE MAGNITUD, no estrategia direccional H01 ni compresión-release T12. No confundir rapidez de transacciones con latencia HFT | Velocidad de barras 377 vs rango absoluto futuro, sin suponer “lado” ni ejecutar trades |
| **T18 Subasta previa a apertura** | ¿El desequilibrio de valor negociado 08:00–09:30 ET anticipa persistencia o reversión después de apertura? | Referencia de subasta/preapertura Last por volumen; no reutilizar 5s ORB T05. Comparar ambos signos como pregunta predeterminada, no elegir ganador posterior | VWAP preapertura, VWAP 377 posteriores, desviación |
| **T19 Eficiencia del recorrido** | ¿La proporción de desplazamiento neto respecto al movimiento absoluto de precios permite distinguir continuación de ruido? | COMPLEJIDAD DIRECCIONAL de recorrido Last y timestamp groups, distinta de amplitud T12 y expansión H01 | `abs(desplazamiento)/(suma desplazamientos absolutos)` con series de VWAP por grupos completos, test contra forward neto |

## Control de multiplicidad y oportunidad
- **Familia de viabilidad A** contiene T14, T15, T16 (solo N de señales y cobertura, sin p). Si se autorizan pruebas económicas sobre esas tres, **las tres deben evaluarse y permanecer en corrección de pruebas**; no seleccionar post hoc una sola basándose en patrones de retornos.
- T17, T18, T19 pertenecen a futura familia B, sin resultados observados ni p/q que contar por ahora. Registrar hipótesis/contrastes antes de entrar a P&L.
- Mecanismo, datos y salidas de cada intento se congelan; si T14–T16 producen cero señales, reportarlo como evidencia de inviabilidad y continuar con OTRAS preguntas, no flexibilizar retrospectivamente.
- **Siguiente tras esta pantalla:** terminar primero los **tests económicos/falsación por muestra** del lote como grupo (incluidos negativos) con costes y riesgo congelados si la integridad de las señales pasa; en paralelo formalizar T17–T19 como preguntas nuevas. No volver a B05L/T05 retuning.
