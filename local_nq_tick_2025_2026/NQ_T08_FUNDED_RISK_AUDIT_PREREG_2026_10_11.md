# T08 — Prerregistro de auditoría continua de riesgo de fondeo (2026-10-11)

**Tipo:** auditoría de riesgo post-selección, NO nueva hipótesis de entrada ni confirmación estadística OOS. Se documenta antes de ejecutar el nuevo evaluador de drawdown. Padres T02/T04, T05-377 y T05-233+377; no se alterarán señales ni parámetros históricos. Se conserva T05-233 como ablación ya observada, sin selección en este test. **Ninguna estrategia queda autorizada para fondeo o trading.**

## Motivo y observaciones previas

- T02 padre: 190 trades, +USD 8.420 baseline; DD cerrado sobre curva diaria USD 2.740 y DD Last intrames indicativo USD 3.175.
- T05-377: 115 trades, +USD 6.220 baseline, 6/7 meses positivos, DD diario cerrado USD 1.375; actividad de 8–22 operaciones/mes.
- T05-233+377: 59 trades, +USD 5.395 baseline, 7/7 meses positivos, DD diario cerrado USD 1.250; **noviembre 2 operaciones y febrero 4**.
- T07 triple 233/4181/10946 falla gate de frecuencia y rendimiento incremental: no reoptimizar en T08.
- La métrica anterior `floating_last_mark_min_vs_day_start_usd` conserva un mínimo intradía, no una secuencia conectada de máximos y mínimos de equity flotante entre todos los meses. Un DD continuo/trailing puede diferir.

## Congelamiento de universo y límites de resultados

1. Solo NQ Tick **Last** privado, desarrollo **2025-10-15 a 2026-04-30**, los siete meses predeterminados. El evaluador llama `dev_day` antes de abrir datos y `month_days` rechaza meses externos. No abrir mayo–junio (validación interna), julio–septiembre (sellado), 2025 original H01–H78 ni 2026 original H01–H78.
2. **Tres alternativas separadas, nunca sumables:** `T02_PARENT`, `T05_377`, `T05_233_AND_377`. Padre de señal T02 y filtros congelados de T05; no mezclar portfolios ni habilitar trades por haber rechazado antes una señal.
3. Política T04 **invariable**: hasta 2 operaciones/día, una posición, stop de 25% de rango apertura (16–48 ticks), TP 2R, timeout 300s, entradas 09:40–11:10 ET, corte 11:30, no abrir nuevo trade con P&L cerrado diario <= -USD600. Entrada/slippage y stop-first por timestamp siguen siendo los de `simulate_single_trade`.
4. Escenarios preexistentes: baseline 1 tick adverso **por lado** + USD 5 RT, estrés 2 ticks por lado + USD 7,50 RT. NO representan tarifa ni fill verificado de firma y no equivalen mecánicamente a multiplicar por 1,5 cada componente total.

## Método de auditoría conservadora de equity

- Reproducir **exactamente** los resultados de `simulate_portfolio` para cada día/alternativa/escenario; si hay diferencia de trades, P&L, errores o abandonos por ambigüedad, **FAIL CLOSED**.
- Reconstruir cada operación a partir del **mismo** `simulate_single_trade`. Evaluar todas las observaciones Last posteriores a la entrada y hasta la salida, descontando comisión RT y slippage de salida supuesto en marcas hipotéticas; los costes de entrada están embebidos en el precio de entrada.
- A cada grupo de Last con idéntico timestamp asignar intervalo plausible de equity (low/high); para peor DD conservador actualizar primero el máximo permitido y luego el mínimo del grupo. **NO conocemos el orden intratimestamp**, por lo que esto es una envolvente de drawdown adversa, no un máximo intradía exacto realizable ni el cálculo oficial del broker. Registrar aparte mínimos de Last/closed y cualquier intervalo vacío.
- Concatenar sesiones y meses en el mismo orden temporal y con el P&L realizado acumulado; no reiniciar high-water marks al cambiar mes. Registrar DD máximo `last_envelope_dd`, DD de cierres de operación, peor pérdida diaria, racha perdedora, saldo de cierre final, máximo/mínimo de equity, trades y frecuencia por mes. Errores/ambigüedades sin cierre seguro bloquean aprobación.
- Comparar contra **USD 2.000 solo como umbral de referencia histórica NO VERIFICADA**, NO como regla actual universal de cuenta de USD 50.000. No afirmar infracción real a una empresa con base en esta aproximación. Es necesaria la especificación escrita vigente de la firma, termasuk EOD/intraday, trailing, floor y payout.
- Si un candidato se aproxima o rebasa el umbral de referencia en esta envolvente, marcar `RISK_REVIEW_REQUIRED` o `FAIL_REFERENCE_SCREEN`; aunque no lo rebase, marcar `CONDITIONAL_ONLY` hasta validar ticks BID/ASK ejecutables, costes vigentes y reglas de firma.

## Criterios definidos ANTES de reportar

- **Gate preliminar económico/riesgo** por candidato: neto baseline >0, estrés >0, PF estrés >=1,25, frecuencia mínima orientativa de **5 trades en cada uno de los siete meses**, ninguna ambigüedad sin resolver, y envelope DD Last bajo referencia USD 2.000. **Estos tests orientativos NO bastan para aceptar fondeo**; estados conservadores, sin rescatar ventanas elegidas a posteriori.
- Prioridad comparativa entre candidatos que cumplan igual gate: primer criterio menor `last_envelope_dd`; segundo mayor neto por oportunidad T02 original; tercero estabilidad mensual. Si ninguno cumple, no seleccionar ganador: explicar qué condición falló.
- Dejar en `ECONOMIC_DATA_PENDING` comparación CAGR vs max(15%, VOO TR, QQQM TR) y ROI de bolsillo hasta que exista ventana comparable y datos verificables; 7 meses exploratorios no prueban CAGR durable. La documentación de la familia H67–H150 y correcciones Holm/BH continúa vinculante para *hipótesis conjuntas nuevas*, no adjudicar confirmación a T08 por esto.
- Reporte completo por los siete meses con los tres candidatos y ambos escenarios, incluidos **resultados negativos**, no solo el mejor. Ninguna mejora de P&L ajustará parámetros de entrada ni de gestión.

## Siguiente gate condicionado

Conciliación independiente Minute Last vs Tick Last y control BBO/ejecución (privados); después obtener las condiciones de la empresa de fondeo; si un candidato sobrevive, congelar código/config/fees y seleccionar una sola estrategia **antes** de probar mayo–junio 2026 una sola vez. **Julio–septiembre 2026** solo se abre después de que la estrategia completa (entrada, SL/TP, sizing, router, costes) esté sellada y haya pasado los preflight. Preservar todos los reportes malos, sin mover periodos.
