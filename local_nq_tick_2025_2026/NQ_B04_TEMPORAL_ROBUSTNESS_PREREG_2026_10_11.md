# NQ-B04 — Prerregistro de robustez temporal de T05-377

**Fecha:** 2026-10-11. **Estado:** PRERREGISTRADO antes de ejecutar nuevos diagnósticos B04. **No** se prueban nuevos parámetros ni se abre OOS.

## Pregunta y evidencia previa

¿La expectativa aparente de T05-377 se distribuye entre semanas, meses y trimestres o depende de unos pocos bloques? El diagnóstico B03 mostró fragilidad a costes: escenario estrés original 115 trades, +USD 5.102,50, PF 1,31826 y DD Last cronológico USD 1.797,50; estrés más USD 10 adicionales por operación deja +USD 3.952,50 y PF 1,23717. El estudio B04 **no** cambiará la señal, sus barras de 377 prints, su ventana ni su ejecución congelada.

## Fuente autorizada y ventanas

Siete meses de NQ Tick Last DEV de **2025-10-15 a 2026-04-30** en repositorio privado con SHA256 mensual verificado. Exactamente los mismos 140 días fuente y 135 elegibles, 115 operaciones en cada escenario T04. Nunca leer retornos mayo–junio ni la reserva julio–septiembre 2026; programa H permanece aislado.

**Unidades temporales predefinidas:** semanas **ISO lunes–domingo en calendario ET**, incluidos días sin trading dentro del universo fuente; meses naturales de fuente (7); **2025-Q4 parcial 15 oct–dic**, **2026-Q1 ene–mar** y **2026-Q2 parcial solamente abril**, sin anualizar estas particiones. Una semana de transición de mes es una sola semana ISO cuando se agregan resultados mensuales, no dos observaciones. Diagnóstico se hace sobre **operaciones existentes**, asignadas a su fecha de sesión ET, sin rebalanceos retrospectivos.

## Escenarios predefinidos

- **S0:** escenario T04 `baseline` original, USD 6.220 en 115 operaciones.
- **S1:** escenario T04 `stress_1p5_fee_2ticks_each_side` original, USD 5.102,50.
- **S2:** escenario T04 `stress_1p5_fee_2ticks_each_side` + **USD 10 fijos por round-trip** de 1 NQ, sin alterar entradas, salidas, stop, TP o selección. Por B03, neto previsto USD 3.952,50; PF previsto 1,23717. Los costes son contabilidad Last congelada, **no fills**.
- No ejecutar después variantes 20/40 solo para rescatar un resultado: B03 ya los informó y se mantienen documentados, no son hipótesis seleccionables B04.

## Métricas diagnósticas congeladas

1. Paridad exacta de operaciones, ganancias netas y conteos por mes contra T04/B03.
2. Para cada mes: trades, neto, PF si hay pérdidas, win rate, promedio neto/trade y cantidad de semanas ISO activas. Mostrar los **siete meses**, incluso los perdedores, pero no publicar órdenes individuales.
3. Para cada trimestre/parcial: trades, neto, PF, meses positivos/negativos, y fracción del neto total asociada al trimestre; los parciales se rotulan explícitamente.
4. Semanas ISO (una semana que cruza dos meses cuenta una sola vez): total de semanas de universo, activas, positivas, negativas, cero; porcentaje positivo entre semanas activas; peor semana y mejor semana **sin fecha ni trade-level**; suma neta y discrepancia contra meses. Evaluar además concentración top-1 y top-3 semanas positivas como fracción del **total de contribuciones positivas**, jamás de un denominador cero/negativo.
5. Bloques en pérdidas: número de meses negativos, máximo de meses negativos consecutivos y de semanas activas negativas consecutivas. Si muestras son pequeñas reportar INSUFICIENTE, no confianza artificial.
6. **Estabilidad descriptiva, no prueba inferencial ni causal**; para S1/S2 comparar la expectativa neta, la frecuencia y la concentración. No tomar semanas rentables como filtro a operar (sería look-ahead) ni proponer exclusivamente un trimestre positivo como cartera validada.
7. Falsación exploratoria: falla la robustez preliminar si S2 presenta neto <=0, si algún trimestre de 3 meses es negativo, si 4/7 meses son negativos, si ganancias se concentran excepcionalmente en pocos bloques o si costes dejan PF <1,25 (ya advertido por B03). **No** inventar PASS formal: solo siete meses y dos periodos parciales impiden robustez anual.

## Procedimiento reproducible

Implementar `nq_b04_temporal_month.py` usando exclusivamente `replay_frozen`, `simulate_portfolio`, `selected_families` y eventos Last autorizados (mismos motores T05/T04). No modificar código T04, T05 ni B03. Procesar días **ordenados por fecha ET**, controlar que los 7 meses estén y que `holdouts_opened=false`. Unir semanas ISO antes de los resúmenes finales. Publicar solo estadísticas semanales consolidadas **sin fecha/semana individual**, recuentos mensuales y trimestres, nunca los precios, timestamps de trades, señales u operaciones individuales. Guardar de modo transitorio contadores ISO semanales para unir meses, sin P&L de transacción. Testear sintéticos y ejecución GitHub Actions.

## Decisión posterior

Documentar TODAS las métricas y pérdidas. Si se confirma fragilidad, conservar T05 solo como **benchmark/estrategia componente exploratoria** y priorizar **B05**: nueva fuente causal de alpha verdaderamente distinta, sometida a validación incremental bajo riesgo compartido. Si B04 es favorable, igualmente NO aprobar fondeo sin fills/riesgo real/OOS y benchmark económico >max(15%,VOO-TR,QQQM-TR). Actualizar `NQ_PROJECT_MASTER.md` y `NQ_RESEARCH_LOG.md` tras validar los siete meses o dejar bloqueo explícito.
