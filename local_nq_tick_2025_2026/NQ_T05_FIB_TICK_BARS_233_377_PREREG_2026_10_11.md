# NQ T05: contexto de barras de 233 y 377 operaciones, prerregistro 2026-10-11

**Estado antes de ver los resultados:** diseño `PREREGISTERED_EXPLORATORY`. Padre: T02 (ruptura fallida de apertura + desaceleración de operaciones), seleccionado exploratoriamente en T01–T03 y posterior T04. No equivale a prueba estadística confirmatoria en desarrollo. El estudio solo considera NQ Tick Last (cada fila de exportación NinjaTrader = 1 operación registrada); **233/377 son número de prints, no desplazamientos de precio ni duraciones constantes**. Reinicio de conteo a 08:00 ET por disponibilidad de fuente; barras sintéticas no tienen por qué coincidir exactamente con gráficas NinjaTrader cuyo conteo empezó antes de 08:00.

## Objetivo y explicación causal

Operar movimientos de segundos a minutos, usando barras de 233 ticks para detectar un cambio de dirección a corto plazo y barras de 377 ticks para identificar el movimiento previo del que la ruptura fallida puede revertirse. Se conservan **ticks individuales** para trayectoria y fills aproximados; barras de 5 segundos para señal y velocidad de actividad. No HFT, no optimización de latencia.

## Reglas congeladas antes del análisis

- Padre **T02**: tal como quedó en `nq_tick_short_horizon.py`, señales entre 09:40–11:10 ET, rango de 09:30–09:35, reversión de falsa ruptura y desaceleración de número de operaciones en 30 segundos.
- Construir OHLCV de barras de **233** y **377 registros Tick Last**, desde 08:00 ET con primer registro del día como inicio. No contar volumen como número de trades; un registro corresponde a un print exportado, aunque su volumen de contratos pueda ser mayor. Solo usar **barras completas que hayan cerrado estrictamente ANTES de la marca de decisión**; no usar la barra 233/377 que todavía está formándose ni asumir orden entre eventos del mismo timestamp.
- Comparadores/variantes preestablecidas, todas sobre las mismas señales T02:
  - **T02_PARENT:** sin filtro adicional.
  - **T05_233:** último cierre 233 es mayor que el cierre 233 anterior para long, o menor para short: cambio direccional confirmado por dos barras de 233 terminadas.
  - **T05_377:** último cierre 377 es menor que el cierre 377 anterior para long, o mayor para short: contexto previo contrario a la reversión propuesta.
  - **T05_233_AND_377:** ambas condiciones a la vez, 233 confirma nueva dirección mientras 377 mantiene el contexto de movimiento opuesto previo.
- Si no hay dos barras completas 233 o 377 antes del momento de decisión, marcar señal como **no elegible**, no interpolar ni rellenar. Para cada variante conservar el cooldown original de T02; el filtro puede reducir oportunidades pero NO se permite volver a traer una señal vieja por ser filtrada la anterior.
- **Sin cambio de ejecución de T04:** misma entrada posterior al cierre de señal, 1 NQ, máximo 2 trades/día, stop 25% rango inicial acotado 16..48 ticks, TP 2× stop, máximo 300 segundos, costes supuestos base ($5 RT + 1 tick adverso cada lado) y estrés ($7,50 RT + 2 ticks cada lado). Son fricciones hipotéticas, no tarifas de la firma de fondeo.

## Evaluación y control de overfitting

**Desarrollo exclusivo** 2025-10-15 a 2026-04-30 (7 meses), excluyendo mayo–junio de retornos y julio–septiembre 2026 sellado. Mismo calendario y datos para cuatro variantes. Reportar completo: señales elegibles, pérdida de frecuencia, trades ejecutados, meses positivos/negativos, expectativa neta, PF neto, DD cerrado y flotante aproximado, peor racha y peor día, costes 1× y estrés. Comparar ganancia neta/margen y DD **sin confundir reducción del número de trades con más alpha**, y nunca sumar P&L de variantes solapadas.

**Métrica primaria exploratoria:** cambio de expectativa neta por trade de T05_233_AND_377 frente a T02_PARENT **con mismo stop/riesgo y costes**. Secundarias: eficiencia por oportunidad original, DD, tasa mensual, impacto 233 y 377 separados. Cuatro variantes/2 costes forman una única familia de selección prospectiva; ver todos los resultados, incluidos negativos. Pérdidas/meses malos, menos de 5 trades/mes en muchos meses, PF neto <=1,25 bajo estrés, o DD incompatible con el programa 50K invalidan la adopción. Ningún resultado de desarrollo confirma valor predictivo sin validación aislada. No seleccionar después de ver resultados `144`, `610`, otros períodos Fibonacci o condiciones nuevas sin una nueva familia explícita.

**Resultados T04 padre (antes del nuevo experimento):** 190 trades simulados y +USD 8.420 bajo costes asumidos, PF 1,309, pero DD intrames indicativo hasta USD 3.175 y cerrado USD 2.740; **NO aprobado para fondeo 50K**. La nueva familia busca comprender si estructuras de operaciones mejoran selectividad y riesgo. No existe ROI real ni evidencia de rendimiento anual garantizado.
