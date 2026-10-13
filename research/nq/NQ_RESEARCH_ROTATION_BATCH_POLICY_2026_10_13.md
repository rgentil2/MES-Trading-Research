# Rotación por bloques y límite de análisis adaptativo NQ/MNQ — 13-oct-2026

**Decisión explícita del usuario:** no sobreanalizar T05 ni cualquier conjunto pequeño de hipótesis. Se investiga por BLOQUES de mecanismos, se mueve el conjunto por fases y se conserva un embudo de candidatos; una candidata fallida queda documentada y el turno avanza, **no se rescata** con sucesivas variaciones de parámetros o recortes del histórico. Se mantiene como opción futura cuenta US$50K; ninguna cuenta se compra aún.

## Regla de rotación vigente

| Bloque de investigación | Material existente y pregunta | Límite de trabajo del turno | Decisión de cierre |
|---|---|---|---|
| **BLOQUE T-A (terminación actual)** | T05+T147: ¿se pueden reconstruir dos padres y riesgo compartido sin reinterpretar Last? | **Una** ejecución G0 de paridad precongelada; si pasa, **un** protocolo cerrado de router shadow sin optimizaciones; si bloqueado, documentar razón y parar | No retocar stops ni horarios según P&L. Es un G0 técnico; no confundir con una estrategia validada |
| **BLOQUE H-B (siguiente)** | H09/H56 padres + H69 comparador; H74/H77 routers de régimen | Una matriz de verificación de riesgos y aportes marginales con resultados ya disponibles, misma contabilidad proxy 1MNQ 2020–24 | No reexplorar los 18 brackets ni usar 2025/26 H; deduplicar mecanismos |
| **BLOQUE T-C (siguiente ronda de descubrimiento)** | Mecánicas en barras 233/377/4181/10946 Last atómicas, distintas de falsa ruptura T05 y barrida T147 | Nuevas candidatas SOLO si pueden registrarse **en cohorte completa de >=20 preguntas distintas**, cada una causal, con stops, TP, horizonte y riesgo definidos *antes de leer outcomes*; G0/D0 de cohorte completa antes de D1; no 5s nuevas | No crear veinte variaciones de una sola premisa ni bajar gates para llegar a veinte; si no hay veinte *distintas* justificables, registrar insuficiencia y cambiar mecanismo |
| **BLOQUE D (arquitectura de riesgo/NinjaTrader)** | Transición a NinjaTrader para comprobar señales y órdenes, primero SIM | Reglas congeladas, timestamps/segmentación coherentes, fricción y DD Last adversos, pruebas de paridad por sesión y por trade **sin publicar datos privados** | Programar NinjaScript para VALIDACIÓN DE IMPLEMENTACIÓN puede adelantarse, pero NO tratarlo como aprobación para fondeo |

## Política operativa

1. **Prohibido túnel de optimización:** por hipótesis o combinación concreta máximo una auditoría G0 y una prueba económica original preregistrada por ciclo. Errores de software se corrigen únicamente con prueba sintética y reconciliación; nunca tuneos por ganancias.
2. **Dar prioridad a experimentos que discriminen mecanismos distintos.** H69/H74/H77 derivan de H09 y H56: no cuentan como tres alphas independientes; su comparación es dentro de una familia. T05/T147/T186 tampoco se suman sin router de cuenta compartida.
3. **Mover el bloque incluso si el resultado es desfavorable.** Fallo/NO EVALUABLE con motivo y límites de datos significa archivado, no obligación de rescatar. Nuevo análisis del mismo mecanismo solo con evidencia nueva y decisión registrada.
4. **No abrir holdouts H 2025/26 ni T mayo–sept2026, no descargar/comprar más historia** sin autorización explícita por separado. Un bloque temporal dentro de DEV reutilizada nunca es nuevo OOS.
5. **Estado estadístico y económico inalterado:** D1 formal T133–T168 0/36 PASS; familias recientes T169–208 0 aprobadas; D2 formal vacío; H tampoco OOS confirmado. Un PF prometedor de la misma DEV no certifica edge futuro.
6. **Puerta NinjaTrader (SIM primero):** al menos un candidato con reglas causales congeladas y código reproducible, paridad de señales/posiciones bajo la misma unidad contractual NQ o MNQ, verificación de ejecución Last/BidAsk o sensibilidad adversa, riesgo por operación/sesión/cuenta definido; comparación emparejada y documentada con Python. **No es necesario completar 208 hipótesis para construir un prototipo SIM**, pero sí evitar importar lógicas aún ambiguas como si sus resultados estuviesen confirmados.
7. **Puerta a cuenta real de fondeo 50K:** adicional a SIM, robustez real de stops/fills/costos, cola de max DD *floating* vs trailing de plan elegido, flujo de trades legítimos suficiente, estabilidad multimensual y confirmación prospectiva/OOS auténtica autorizada. Un trade de MNQ exclusivamente para satisfacer actividad no forma parte de ventaja demostrada y debe analizarse con costos/rules futuros.

## Seguimiento / checkpoint

- Al iniciar un nuevo ciclo elegir una fila/BLOQUE y registrar ID(s) y resultado medible; no permanecer en uno por más de dos pasos formales. G0 y D1 no son una misma prueba.
- Maestro y log deben actualizarse al cerrar cada estudio. Cuando una prueba esté ejecutándose debe marcarse **RUNNING**, no declarar PASS hasta Action SUCCESS y archivo SAFE verificado.
- Próximo cambio de foco tras G0 T05/T147: **H-B**, incluso si el G0 es favorable. Si G0 es favorable, preparar como máximo un protocolo shadow y dejarlo en cola, no desplazar H-B hasta hallar resultado 'ganador'.
