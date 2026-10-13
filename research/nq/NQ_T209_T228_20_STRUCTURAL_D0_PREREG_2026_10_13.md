# T209–T228 — Cohorte T-C: veinte preguntas estructurales de Last, congeladas antes de G0/D0

**Fecha:** 2026-10-13, investigación exclusivamente NQ/MNQ. **Registro machine-readable con las 20 preguntas, condiciones exactas, umbrales y lados:** [JSON congelado](NQ_T209_T228_20_STRUCTURAL_D0_PREREG_2026_10_13.json). La versión 2 precisa los disparadores **ANTES de observar resultados**. Aceptamos que algunas sean demasiado raras; no bajaremos filtros ni cambiaremos el lado para rescatar CASE.

**Objetivo:** comprobar si existen 20 hipótesis de cuatro mecanismos distintos que se activen de manera suficiente, en lugar de seguir buscando variantes de T05/T147/H69. D0 verifica elegibilidad y diversidad, **NO** ventaja económica. La independencia se estima con solapamiento de activaciones y contenido causal, no con títulos diferentes. **0 OOS, 0 profit estimado en esta fase.**

## Cuatro bloques, veinte preguntas y condición crítica

| Bloque | IDs | Preguntas independientes | Datos necesarios |
|---|---|---|---|
| A. Eficiencia y recorrido del precio | T209–T213 | Continuación en desplazamientos eficientes; reversión tras oscilación sin desplazamiento; aceleración tardía; alternancia repetida; rechazo de salto entre grupos atómicos | Primera barra 377 íntegra de 09:40–10:00 ET; trayectoria por grupos timestamp |
| B. Distribución de cantidad por precio | T214–T218 | Aceptación en tercio del rango; migración del POC vs cuerpo; atracción por niveles concentrados; rechazo de extremo con volumen; escape por nivel de bajo volumen | Primera barra 377 íntegra de 10:00–10:15 ET; perfil de qty por cada nivel |
| C. Segmentación por tamaño de print | T219–T223 | Divergencia precios grandes vs pequeños; expansión de tamaño medio; divergencia grandes prints vs precio; cantidad concentrada temprano; lotes de transacciones y compresión | Primera barra 377 íntegra de 10:20–10:40 ET; `qty` real por fila y timestamp (NO agresor) |
| D. Tiempo de aceptación y régimen | T224–T228 | Tiempo negociando sobre VWAP macro; cruces repetidos de VWAP; cruce de POC largo; desaceleración temporal/rotación; cambio de eficiencia frente a barra anterior | Primera barra 377 íntegra de 10:45–11:05 ET, solo macro4181/10946 ya completa |

**Todos los umbrales exactos son los 20 valores `trigger_definitions` del JSON**, no los nombres abreviados anteriores. Contamos como *distintos* los mecanismos si no son reglas semánticamente idénticas y su Jaccard de CASE es menor que 0,85; si se repiten, pierden diversidad aunque el ID sea nuevo. Varias preguntas pueden ser complejas y ninguna está garantizada.

## Reglas congeladas de activación

- Fuente **YA EXISTENTE** Last: meses octubre2025–abril2026, desde 15-oct; **140 días fuente, 135 READY** esperados. No se descargará nueva historia ni se abrirá mayo–sept2026 T ni 2025/26 H. El motor usa releases preexistentes y SHA256; los bytes privados solo permanecen en el runner.
- Bloques en barras de **377 prints agregando timestamp COMPLETO**, reiniciadas 08:00 ET; no se usa barra de 5 segundos para las **nuevas** decisiones. La infraestructura legacy `frozen_t05` solo verifica la elegibilidad original 135/140 para comparar cobertura; no modifica T05 ni condiciona SIDE. Las barras contextuales 4181/10946 deben terminar estrictamente antes de la barra señal.
- Una sola oportunidad por ID y día: **primera E377 que termina en la ventana preregistrada**. Si no hay barra con al menos cuatro grupos atómicos previos, contexto imprescindible, cantidad o precisión suficiente: NOT_EVALUABLE. Si no existe condición CASE pero hay datos suficientes: CONTROL.
- Side LONG/SHORT fijado por cada `trigger_definition`; entrada propuesta NO EJECUTADA en el primer grupo de timestamp completamente posterior a cierre E377. Stop a **2 ticks fuera de máximo/mínimo** de E377 según dirección; referencia preliminar de riesgo con VWAP del último grupo atómico, entre 8 y 400 ticks, y riesgo nominal máximo $250 en 1 NQ cuando permita o 1 MNQ en los otros casos, sin obligar a operar. Si supera límites, OTHER (no “trade perdido”). **D1 futura deberá recalcular todo al precio peor del próximo grupo, con slippage realista, y podría declarar NOT_ESTIMABLE.**
- TP 1,5R, salida máxima 15 minutos, capacidad de 1 posición por cuenta y máximo 2 entradas/día, corte por PnL diario cerrado −$600. Estas son reglas **potenciales de ejecución**, no órdenes ni simulación efectivamente realizada en D0. Horizonte no cruza el tope 11:30 ET de investigación.
- D0 para cada uno: N CASE/CONTROL/OTHER/MISSING; mínimo ≥15 CASE y ≥15 CONTROL, Jaccard CASE menor 0,85 y objetivo ≥20 modelos *distintos y testables* para autorizar un siguiente prerregistro económico D1 de cohorte. **Si no se alcanza, NO se fuerza D1: registrar INSUFFICIENT y pasar de bloque, sin resucitar señales.** Nada de PnL, PF, IC90, drawdown o variables futuras en G0/D0.
- Si D0 pasa: ejecutar D1 en bloque completo con resultados de los 20 IDs, sin filtrar por mejores casos, IC90 por bloques de días y q-BH/Holm para familia; exigir reglas de stops y costos verificables, estabilidad mensual y separaciones por régimen. Aún no autorizado y la misma DEV nunca constituye OOS confirmatorio.
- No publicar precios individuales, fechas de trades, archivos Last, vectores por sesión ni ubicaciones de eventos; salida **agregados solo**; fail-closed ante paridad o embargo roto.

## Punto metodológico: evitar sobreanálisis

Esta es **una cohorte, una ejecución G0/D0, un dictamen para TODOS los IDs y cambio de bloque**. No generar T229–T248 modificando cinco ticks de umbral si el resultado es malo; aprender qué estructuras observables se activan y cuál información falta. Posterior **fase D/NinjaTrader SIM** para estrategias congeladas y pruebas de paridad de señales antes de fondeo 50K.

**Fuentes:** [política rotación](NQ_RESEARCH_ROTATION_BATCH_POLICY_2026_10_13.md) · [T189–208 previo](NQ_T189_T208_20_MONETARY_RESULTS_2026_10_13.md) · [programa original 36 G0/D0](NQ_T133_T168_FULL36_EXECUTABLE_D0_RESULTS_2026_10_12.md). **Estado:** D0 aún no ejecutado al prerregistrar este documento.
