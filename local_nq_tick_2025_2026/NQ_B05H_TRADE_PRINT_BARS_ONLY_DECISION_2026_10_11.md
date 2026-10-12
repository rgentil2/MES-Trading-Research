# NQ-B05H — Decisión del investigador: SIN barras de 5 segundos en las hipótesis nuevas

**Fecha:** 2026-10-11 (America/Bogota). **Estado:** diseño de unidad de observación y contrato de implementación, **NO resultado de alpha ni backtest**. Prevalece la instrucción explícita «No me gustaría mirar 5 segundos». Esta política actualiza y **reemplaza SOLO la propuesta futura B05H** de análisis de indicadores 5s que figuraba en el master y en el dictamen de B05G. Los informes históricos B05F/B05G y el baseline T05 permanecen intactos.

## Decisión de granularidad

- **NO utilizar barras de 5 segundos** para generar señales nuevas, formar estados/regímenes de mercado, optimizar entradas ni filtrar decisiones en B05H. Tampoco rediseñar la nueva familia con velas de 1 minuto como sustituto implícito.
- Analizar **barras de transacciones Last (tick bars / trade-print bars)**: barra corta candidata de **233 impresiones** para decisiones; **377 impresiones** como comparador predefinido alternativo de corto plazo, sin suponer que Fibonacci crea rentabilidad. Contexto medio **4181 impresiones** y largo **10946 impresiones**. No hay que usar las cuatro por obligación: los comparadores y filtros deben preregistrarse y aportar beneficio incremental genuino.
- Cada print = **fila Last**, **no** un contrato ni un tick de desplazamiento del precio. `qty` mide contratos negociados; precio en ticks de 0,25 puntos NQ. La duración cronológica de cada barra es **variable** según la actividad: el tiempo solo se usa para determinar sesiones ET, antigüedad de información, ventanas permitidas y SL/TP/timeout de riesgo; no existe una rejilla de cinco segundos.
- **No adquirir, comprar ni descargar historial adicional**. Usar solo los releases tick DEV NQ ya existentes oct-2025–abr-2026, 140 sesiones fuente /135 elegibles según la muestra histórica. No abrir mayo–junio / julio–septiembre 2026 T ni H 2025/26.

## Problema ya demostrado por B05G: empates de timestamp

Al haber muchos prints Last con timestamp idéntico, la regla usual `cerrar barra exactamente cada N filas y tomar el último precio` puede cambiar si el orden de esas filas es diferente. No debemos prometer simultáneamente **exactamente** 233 prints por barra **y** invariancia completa a permutar filas idénticamente fechadas.

**Convención nueva que debe implementarse y probarse ANTES de cualquier P&L nuevo:**

1. Tratar **todos los prints de un mismo timestamp como un grupo indivisible** (atomizar la marca de tiempo completa). No tomar decisiones ni permitir entrada a mitad de ese grupo, porque no sabemos el orden de negociación exacto. No confundir esto con conocer el orden real CME.
2. **Barras de umbral mínimo de N transacciones:** acumular grupos completos desde el ancla de sesión 08:00 ET. Cuando el número acumulado de prints alcanza o supera N, cerrar la barra **después de incorporar el grupo entero**. La barra puede contener **N o más** impresiones por sobresalto del grupo final. Reportar exceso de impresiones por barra; **no etiquetarlas falsamente como barras exactas N**.
3. Dentro del grupo/barra, utilizar estadísticas que no dependen del orden: cantidad de prints, suma `qty`, high/low del precio, VWAP calculado exactamente con `sum(price_en_ticks * qty)/sum(qty)`, rango, cambio de VWAP entre barras **completadas**, duración por timestamp inicial/final y actividad prints/segundo observado. Nunca usar como `close` el último print arbitrario del grupo. El inicio de barra no será automáticamente el precio del primer print si comparten marca.
4. Una señal generada al finalizar un grupo con timestamp `T` solo puede usar datos **hasta el grupo T íntegro**; **primera ejecución modelable en un evento con timestamp estrictamente mayor que T**, nunca en el mismo grupo ni al supuesto precio VWAP como fill. El `T05` baseline histórico se conserva sin modificar y sin confundir sus señales 5s ya publicadas con el nuevo disparador por conteo de prints.
5. Para contexto 4181/10946, exigir barras de umbral completamente cerradas **antes** de la decisión, y declarar `CONTEXT_NOT_READY` si faltan. No usar barras parciales, futuro, datos inventados ni una limpieza orientada al P&L.
6. **Prueba de invariancia:** tomar muestras sintéticas de Last, permutar dentro de cada grupo con timestamp idéntico (original / reverse / precio ASC / precio DESC), demostrar exactamente la misma serie de barras terminadas, estadísticas y oportunidades de señal. Un `FAIL` bloquea cualquier experimento económico. Usar aritmética entera para VWAP numerador/denominador, evitando diferencias por acumulación flotante.
7. No exigir igualdad de **simulador de fills Last T04** ante permutaciones: B05G mostró fragilidad; reportarla aparte. Robustez de **señal** ≠ certeza de fill ni orden real del exchange.

## Dirección deductiva, no descubrimiento aún

- **Hipótesis potencial B05H-01** (no activar ni computar hasta prerregistro de reglas exactas): si hay una aceleración de actividad de prints y expansión de rango **en barras de 233 prints completamente cerradas**, y el contexto de 4181/10946 prints confirma estado sin lookahead, buscar una oportunidad de continuación o reversión solo tras definir el mecanismo, horizonte, ventanas ET, lado, stops y costes y comparar ambas explicaciones con un número limitado de pruebas. Esta es una **idea**, NO señal comprobada. Debe aportar alfa distinto de la reversión del opening range T05.
- Registrar un máximo pequeño de variantes/modelos y comparadores predefinidos, cuantificar frecuencia mensual y rentabilidad **por una sola cuenta/router** con T05, 1 NQ, máximo 2 trades/día, bloqueo diario -$600, estrés de slippage/costes y +$10 RT fixed-path diagnóstico, DD compartido. No sumar dos P&L aislados ni escoger retrospectivamente la mejor agrupación.
- Los siete meses DEV han sido usados adaptativamente; no se convierten en OOS por cambiar unidad de barra. H y T holdouts siguen bloqueados hasta freeze formal.

## Entregable inmediato

Implementar y probar exclusivamente el constructor causal `NQ_B05H_TIMESTAMP_ATOMIC_PRINT_BARS` y pruebas con datos sintéticos **SIN leer datos privados ni probar P&L**. Si pasa, después congelar por separado una hipótesis NQ-B05H-01 antes de estudiar esos mismos DEV históricos. **No generar señales con rejillas de 5s.**

**Limitaciones:** no inventar agresor, delta real, profundidad L2, orden temporal global entre Last/Bid/Ask ni fills broker. No promover T05 ni abrir fondeo. El resultado de B05G [SUCCESS 38188240187](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38188240187) sigue vigente como riesgo de fills y señal histórica T05, no como autorización de utilizar 5s ahora.
