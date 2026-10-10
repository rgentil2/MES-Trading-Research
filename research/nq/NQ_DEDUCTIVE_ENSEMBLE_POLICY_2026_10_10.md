# Política prospectiva de hipótesis conjuntas y aprendizaje deductivo — H67–H150

**Aprobada:** 2026-10-10. **Ámbito:** nuevas familias que se propongan a partir de H67 en el programa de investigación NQ (y sus posibles componentes ES/MES verificados). **Estado:** adición prospectiva; NO modifica ni reetiqueta H01–H66, las cinco familias congeladas, Gate 1, las auditorías Holm, ni el acceso a 2025/2026. *H150 es un techo de exploración, no una cuota que deba agotarse.*

## 1. Unidad central: hipótesis conjunta, no señales sueltas

Una nueva H67+ debe proponer y medir **una decisión conjunta y ejecutable**, basada en **dos o más componentes/funciones con mecanismos distinguibles**: p. ej. disparador H09 + estado de mercado observado antes de la entrada; o consenso H55/H56 + política de prioridad; o señales de dos índices sincronizados, únicamente cuando existan datos causalmente emparejados.

- **Componentes:** cada fuente (H09, H55, H56, H29, H36, H54, etc.) se conserva con su definición y fallos. Una condición contextual aislada puede investigarse como diagnóstico, pero **no cuenta como nueva hipótesis estratégica H67+** salvo que se formule como **valor incremental de una decisión compuesta**.
- **Formas permitidas:** conjunción `A AND B`, consenso, `A IF regime R ELSE B`, reglas `A OR B` con router/prioridad congelado, veto de conflictos, combinación de señales horarias distintas. No se obliga a que todas ocurran simultáneamente ni se permite crear exposición doble por señales coincidentes.
- **Unidad de selección:** **estrategia/cartera conjunta completa** con entradas, horarios, lados, no-trade, resolución de conflictos, stops, TP, salida por tiempo, sizing y ejecución. La señal de 30 min es un diagnóstico de mecanismo, no rentabilidad de la cartera.
- **No pedir independencia artificial:** H55/H56 compartieron 67 fechas con igual dirección en 2020–24; ES/MES y NQ/MNQ de sus respectivos índices comparten factores. Correlación y solapamiento quedan explícitos.

## 2. Cada nueva prueba debe derivarse de evidencia previa

Preregistro **obligatorio**, con estos campos rastreables:

1. `parent_ids`, archivos de resultados, fechas/años y **observación concreta** (incluidos N, incertidumbre, costos, años negativos, falla de Gate y sesgos reconocidos).
2. `causal_explanation`: mecanismo que conectaría los componentes **antes** de ver resultados de la nueva combinación.
3. `incremental_prediction`: qué se espera que mejore **contra sus padres por separado** y contra un router base razonable. Se elegirá **una métrica primaria** y el signo antes del test; las restantes son secundarias y se reportan íntegras.
4. `component_roles`: señal primaria / filtro de régimen / confirmación / veto / alternativa / control de exposición, evitando pseudodiversificación.
5. `signal_times_and_available_data`: timestamps de información, señal, orden y salida; anti-lookahead, rollover y semanas festivas.
6. `combination_logic`, `conflict_resolution`, `duplicate_signal_policy`, `max_open_risk`, `execution_instrument`, `sizing`, `fee_model`, `SL_TP_time_exit`.
7. `comparators_and_ablations`: padres individualmente congelados, cartera base sin el componente nuevo, y versión conjunta, **todos con los mismos costos, tamaño de cuenta, período y riesgo**. Prueba *leave-one-component-out* para saber si cada bloque añade valor. Informar también si solamente se redujo o cambió la frecuencia.
8. `family_and_multiplicity`: enumerar **todas** las variantes, lados, gates, horarios, valores de SL/TP, pesos y comparaciones seleccionables. El presupuesto Holm y BH es sobre la familia completa. Variantes derivadas tras ver resultados constituyen **otra familia exploratoria**, no una réplica independiente.
9. `falsification_conditions`: resultado que invalidaría la mejora, incluyendo perder la ventaja al quitar un año, costos 1.5×, inestabilidad de parámetros, contracción a pocos trades o un empeoramiento de drawdown.
10. `data_split_and_holdout_policy`: diagnóstico en **2020–24 ya reutilizado**; 2025 sellado hasta aprobación explícita de una cartera completamente congelada; 2026 reservado a pseudo-forward con reglas fijas. Para confirmación, necesitar datos realmente no examinados.

Sin estos campos, **no ejecutar outcomes** ni llamar al experimento «H67» o posterior: sigue siendo una idea no registrada.

## 3. Ciclo deductivo por ronda

**Observar → explicar → formular combinación falsable → congelar familia + tests sintéticos → calcular outcomes → comparar ablations y cartera → auditar riesgo/benchmark → conservar aprendizaje → decidir siguiente ronda.**

No se seleccionan retrospectivamente subgrupos/años que maximicen el P&L; las fallas o efectos nulos son evidencia para la siguiente explicación y se conservan. Una mejora del PF o del promedio sin su comparación con actividad, exposición, costes y riesgo **no** acredita valor incremental.

Métricas mínimas de cada combinación (mismo calendario):
- oportunidades elegibles, días/operaciones realmente ejecutados, frecuencia por mes, vacíos >7 días;
- media neta, PF, expectativa, IC por semanas, BH q de **todas** las variantes de la familia, corrección Holm; años positivos 2020–24;
- atribución de P&L y pérdidas por componentes, consenso, exclusividad, conflictos y exclusiones; ganancia marginal en prueba *leave-one-out*;
- riesgo realizado y flotante, apalancamiento, no duplicación de NQ/MNQ/ES/MES, máxima exposición correlacionada, sensibilidad a 1.5× costos;
- capital nominal de referencia USD 50k y **Gate Económico**: CAGR neto **estrictamente mayor** que el máximo de 15 %, VOO total return y QQQM total return, todos en la misma ventana. Separar ROI de bolsillo con flujos y payouts. Si faltan comparables, indicar pendiente, no aprobado.

**Gate 1 original sigue inalterado** en la evaluación exploratoria estadística. La hipótesis compuesta H67+ debe declarar su propio endpoint direccional o de cartera para evitar trasladar mecánicamente un IC de una señal individual al rendimiento de una cartera. Nuevas hipótesis no sustituyen los resultados familiares ya congelados.

## 4. Banco acumulativo y prioridades fundamentadas

Ningún candidato se elimina por un gate fallido. El banco conserva `candidate_id`, `parent_ids`, diagnóstico favorable/adverso, incertidumbre, intervalos, cobertura temporal, frecuencia, costes y contribución marginal cuando exista. Una señal guardada puede servir de filtro o cobertura; eso **no la valida**.

**Observaciones que motivan investigación, no señales confirmadas:**
- H09: continuación de gap con expectativa positiva histórica, pero concentración en 2022; contrastar una **combinación con estado ex ante** respecto a H09 sin filtro y controles completos. No seleccionar estados por su retorno observado.
- H55 + H56: 67 coincidencias y mismo lado histórico; consenso relativamente más favorable que exclusividad. **No contar como dos fuentes de alpha independientes**; probar un router con una sola posición o un veto, comparando ablations.
- H54: señal frecuente y prácticamente neutra por sí sola; posible variable de estado/veto, **sin asumir** que mejora otras estrategias.
- H29, H36, H44, H45, H57: señales escasas o no respaldadas, conservar como ideas de componente solo bajo límites de complejidad y sin declararlas diversificadoras por intuición.
- H02 y H05: mantener procedencia y advertencias de concentración/rollover.
- Cartera histórica H09/H29/H55/H56: frecuencia mejorada pero drawdown cerrado de ~US$2,718 sobre MNQ y gaps prolongados; **comparador exploratorio, no estrategia fondeable**.

## 5. Construcción orientativa de la siguiente familia (NO preregistro ni resultados)

**H67–H78**: asignación prevista a combinaciones de H09 con régimen de volatilidad observado antes de su entrada, H55/H56 como consenso único o veto, prioridad de entradas entre H09 y consenso VWAP/premarket, H54 como estado de ruptura/veto y controles de pérdida de frecuencia. Contrastar **AND, OR/router o estados mutuamente excluyentes** solo cuando exista una predicción causal distinta y sea realizable sin conocer el futuro.

Los 12 IDs son **posiciones reservadas en el programa**, no 12 resultados ni 12 variantes definidas. Antes de abrir datos se registrará la familia efectiva completa con fórmulas, comparadores y origen concreto. Si el diagnóstico no fundamenta 12 hipótesis, crear menos; no agotar un cupo inventando variantes.

Luego cada familia H79–H150 debe revisar explícitamente la anterior y proponer **combinaciones**; ES–NQ sólo con datos sincronizados y tick-flow sólo si existe Bid/Ask/Last de calidad. No inferir delta de OHLCV minuto.

## 6. Prohibiciones y clasificación

- Prohibido transformar 2020–24 repetidamente examinados en OOS mediante nuevas etiquetas, subperíodos, walk-forward retrospectivo o elección de ganadores tras observar retornos.
- Prohibido construir cartera sumando señales/ganancias con posiciones superpuestas sin modelar router causal y exposición real.
- Prohibido informar un CAGR equivalente de USD 50k fondeados como ROI real del usuario. Exigir costes de la cuenta fondeada, drawdown flotante, reglas de inactividad, retiros, y comparables de ETF.
- Estados permitidos: `NOT_PREREGISTERED`, `EXPLORATORY_LIBRARY`, `NOT_SUPPORTED_EXPLORATORY`, `INSUFFICIENT_EVIDENCE`, `ECONOMIC_DATA_PENDING`, `BELOW_ECONOMIC_HURDLE`, `PROMISING_PORTFOLIO_EXPLORATORY` (solo desarrollo, no trading), `CANDIDATE_FOR_NEW_DATA`.
- La decisión de investigar H67–H150 **no** autoriza apertura de 2025/2026, operaciones reales ni compra de fondeo.

**Referencias de política:** `research/nq/NQ_H59_H150_DEDUCTIVE_RESEARCH_PROGRAM.md`, `research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.md`, `research/RESEARCH_CONTROLS_POLICY.md`. Implementaciones nuevas deben pasar el control de familia existente antes de cargar outcomes.
