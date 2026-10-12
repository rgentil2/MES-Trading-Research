# NQ T26–T28 — nuevo lote G0/D0, prerregistro prospectivo SIN outcomes

**Fecha:** 2026-10-12 America/Bogota · **política activa:** [NQ-DISCOVERY-STAGED-GATES-V1](NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md) · **fase autorizada:** solo G0 y D0 de viabilidad. Documento congelado **ANTES** de leer categorías/conteos de T26–T28 y ANTES de cualquier retorno. Estos mecanismos NO son variantes ni refinamientos de T05/233, T21/T24/T25, ORB/VWAP fade o cantidad promedio T22; son preguntas ex ante sobre distinta información microestructural. La investigación T14–T25 previa influye en la **selección** conceptual; por eso cualquier D1 posterior en DEV reciclado será descriptivo, NO OOS independiente.

## Seguridad, reloj común y rol temporal

- Datos existentes exclusivamente NQ **Tick Last DEV** de los siete Releases privados `nq-tick-2025-10`…`nq-tick-2026-04` ya almacenados. Workflow privado solo descarga de sus **releases existentes** para procesar, no adquirir o descargar historia adicional de proveedor. SHA256 cada archivo antes de analizar, mantener datos temporales privados, borrar en `if:always()`; publicar **solamente agregados**.
- Lista estricta T DEV 2025-10…2026-04, 140 sesiones fuente / 135 elegibles `frozen_t05 == READY`, incluyendo días sin CASO como 0; 135 anclas esperadas. Fechas T mayo–junio 2026 y julio–septiembre 2026, y H 2025–26, siguen **reservadas**, no abrirlas. Sin nuevo proveedor, Market Replay, L2, agresor ni cambios a código de estrategias.
- **Sin 5 segundos para nuevas señales.** Compartir ancla causal independiente del resultado con T20–T25: primera barra 377 prints completada por grupo de timestamp con fin en [10:00,10:15) ET, llamada E, con su barra 377 anterior D. Un grupo de timestamp con múltiples prints entra completo e indivisible. D y E deben tener fin de timestamp estrictamente creciente y todos los datos de features terminar **a más tardar al cierre E**.
- Cada hipótesis etiqueta la misma sesión/ancla como **CASE, CONTROL, OTHER o NOT_EVALUABLE**; estas son categorías distintas. **Un día elegible con señal de otro miembro o sin categoría caso/control se conserva**, sin inventar trade. N eventos/clusters independientes N/D; N_trades, IC90/p/q/Holm/PF/DD/P&L/Δrouter **N/D (no medidos)**. El éxito de Action solo certifica el software.

## Tres mecanismos y umbrales completos congelados

**Funciones exactas comunes:**
- `R(B)=max(price_ticks_B)-min(price_ticks_B)` para barra por prints completa B.
- `groupVWAP(g)=sum(price_ticks*qty)/sum(qty)` en **cada grupo completo de timestamp** de la barra, con Fraction exacta. `PATH(B)=Σ_{i=2..n_groups} |groupVWAP_i-groupVWAP_{i-1}|`; para `R(B)>0`, `CHOP(B)=PATH(B)/R(B)`. No usar `close` arbitrario dentro de timestamp empatado.
- `VWAP(B)=sum(price_ticks*qty)/sum(qty)`, `MEAN_PRINT(B)=sum(price_ticks)/number_of_prints`. Ambas rationals exactas.
- `GAPS(E)` son diferencias **positivas** de timestamps de grupos enteros consecutivos de E, en unidades originales UTC100ns. `CV2(E)=len(GAPS)*Σ gap_i²/(Σ gap_i)²-1` (coeficiente de variación poblacional al cuadrado, sin hacer ventanas temporales ni barras de 5 segundos).
- Todos los CASE/CONTROL quedan mutuamente excluyentes, con precedencia CASE antes que CONTROL. Cualquier error de grupo/qty/tiempo: fail-closed, nunca eliminar ese día.

| ID | Pregunta falsable / mecanismo distinto | CASE (condiciones TODAS) | CONTROL (en mismo ancla) | Variable futura **que se prerregistraría en D1, NO se lee en D0** |
|---|---|---|---|---|
| **T26-PRICE-PATH-CHOP** | ¿La *fragmentación del recorrido* dentro de barras completas, independientemente del lado, anticipa **mayor rango** en los siguientes 15min que una trayectoria comparable? | `R(D)>=8`, `R(E)>=8`, `CHOP(D)>0`, y `CHOP(E)/CHOP(D)>=3/2` | Las mismas condiciones base y `4/5<=CHOP(E)/CHOP(D)<=6/5` | Diferencia `mean(range15m_CASE)-mean(range15m_CONTROL)>0` ticks, sin dirección, no estrategia de posiciones |
| **T27-PRINT-SIZE-PRICE-PREMIUM** | ¿La concentración de volumen a precios diferentes del promedio por transacción favorece continuación direccional frente a la ausencia de tal prima, a igual señal de migración de valor? | `abs(VWAP(E)-VWAP(D))>=4` ticks, `abs(VWAP(E)-MEAN_PRINT(E))>=2` ticks, y signos `VWAP(E)-VWAP(D)` y `VWAP(E)-MEAN_PRINT(E)` **iguales** | `abs(VWAP(E)-VWAP(D))>=4` ticks, `abs(VWAP(E)-MEAN_PRINT(E))<=1/2` tick. Lado `sign(VWAP(E)-VWAP(D))` **en ambos grupos** | Markout observacional a +300s `side*(VWAP_FUTURO−VWAP(E))` en ticks, caso-control; **no fills ni P&L** |
| **T28-ARRIVAL-BURSTINESS** | ¿La irregularidad de intervalos entre timestamps de impresiones (no la duración total de barra) anticipa mayor volatilidad futura que transacciones con llegadas homogéneas? | Barra E con **>=30 grupos completos**, `CV2(E)>=4` | Misma exigencia de grupos y `CV2(E)<=1` | Diferencia `mean(range15m_CASE)-mean(range15m_CONTROL)>0` ticks; no lado ni fills |

- **T26:** si alguna barra D/E tiene R=0 o menos de 2 grupos enteros, `NOT_EVALUABLE`; cuando R válida y ratio no está en extremos CASE/CONTROL, `OTHER`. No se elige otro par de barras según resultados.
- **T27:** `VWAP(D)` y `VWAP(E)` son de barras 377 completas. Un lado = ±1 cuando migración>=4, independiente de volumen. Si D/E con qty inválida, abort. Si movimiento <4, `OTHER`; ausencia de prima exigida en control; prima desalineada no se fuerza a contraevidencia y queda `OTHER`. No se usan Bid/Ask/agresor.
- **T28:** si menos de 30 grupos completos o no hay al menos dos timestamps distintos, `NOT_EVALUABLE`; CV2 no negativo salvo error numérico, usar aritmética racional exacta. No se infiere latencia ni orden de impresiones con un mismo timestamp.
- Comparadores son exclusivamente **grupos CASE vs CONTROL del mismo ancla**, no se adoptan reglas de D1 hasta cerrar D0. Los posibles efectos son *hipótesis*, no afirmaciones sobre patrones observados.

## QC, clasificación, reportes y decisiones D0

1. Pruebas sintéticas por caso/control/other, grupos de igual timestamp permutados (resultado **idéntico**), look-ahead/no futuro, días sellados rechazados **antes** de leer archivo, y ausencia de rangos/retornos/ejecuciones monetarias.
2. Ejecutar **los siete meses completos** con SHA; reconciliar 140/135 y 135 anclas, exactamente una etiqueta por ID/sesión elegible, todos los 3 IDs; tabla por mes con CASE/CONTROL/OTHER/NOT_EVALUABLE, lados T27, solapamientos de casos entre pares. Totales que no cuadran => fail-closed; no liberar artefacto incompleto.
3. D0 `UNIDENTIFIABLE` si CASE=0 o CONTROL=0; `LOW_POWER` descriptivo si alguno <15 sesiones (orientación para no gastar en D1, **no un nuevo gate histórico**); `TESTABLE` si ambos >=15. La dependencia reduce N efectivo desconocido; ni `TESTABLE` ni la frecuencia implican alfa. Toda la familia de tres, incluidos no estimables, permanece en ledger/denominador de BH de un D1 futuro si se prerregistra.
4. Después de informe D0, cualquier D1 observacional debe congelar horizonte, retorno físico, q-BH familia completa, estadística de bloque L5/3/10 y tratamiento de casos/control antes de leer outcomes; D2 económico solo si hay evidencia razonable y fills identificables, siempre una cuenta y comparación incremental. No rescatar D0 retocando porcentajes/umbral o filtrando meses.

**Prohibiciones:** no nuevo histórico; no 5s; no romper timestamps; no optimizar T05/T20–T25; no abrir H/T holdouts; no converter magnitud en tradable; no comprar fondeo. Los resultados negativos se conservan en log/scorecard.
