# NQ — Política de investigación en embudo POR COHORTES

**Vigencia:** 12-oct-2026. **Decisión explícita:** dejar de trabajar hipótesis aisladas y avanzar BLOQUES completos por G0, D0, D1 y D2. Enmienda prospectiva ADITIVA a [política original](NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md): NO cambia Gate1/Holm, requisitos económicos ni permisos sobre datos. La unidad operativa es **COHORTE**, nunca T05 o T59 individual. [Contrato JSON](NQ_COHORT_FUNNEL_POLICY_2026_10_12.json) · [ledger](NQ_COHORT_FUNNEL_LEDGER_2026_10_12.json) · [tablero](NQ_COHORT_FUNNEL_STATUS_2026_10_12.md).

## Pasar bloques completos, no una hipótesis por vez

| Fase | Protocolo por bloque | Salida al cuello de botella |
|---|---|---|
| **IDEAS** | Prerregistrar mecanismo, pregunta falsable, caso/control, reloj, familias y umbrales *antes* de examinar datos. Variedad de mecanismos; no variantes de T05. | Familia completa hacia G0. |
| **G0** | QC, fuente permitida, causalidad y portabilidad. Grupos timestamp indivisibles; ninguna descarga nueva. | Familia a D0 o bloqueo explícito, sin sustituir variables faltantes por proxies. |
| **D0** | Ejecutar TODOS los IDs juntos: N caso/control/otros/no evaluables, Jaccard de casos. `TESTABLE` si ambos N≥15 sesiones; máscara redundante si Jaccard≥0,85. Sin retornos. | Para NUEVA D1 esperar **≥20 distintas y testables**. Si menos, prerregistrar OTROS bloques y continuar D0, no retunar. |
| **D1** | Congelar signos/endpoints por mecanismo ANTES del resultado; ejecutar **UNA corrida familiar** de todos los IDs originales (incluidos descartes D0), bootstrap de bloques 10k L5/L3/L10, IC90, q BH de familia completa. | Supervivientes registradas por **tipo**: dirección, régimen/volatilidad, o ventaja económica. Filtro exploratorio favorable: signo original, IC90 inferior>0 y q BH≤0,10; esto NO es confirmación OOS. Si no se cumple, cero avance. |
| **BANDEJA POST-D1** | Reunir supervivientes de cohortes D1 CERRADAS y medir redundancia cruzada. Efectos de mayor RANGO se guardan como contextos, **no estrategias monetarias**. | Si existe solo una ruta ejecutable, dejarla en espera; preparar un D2 agrupado cuando haya **≥2 mecanismos no redundantes** con ruta direccional/económica plausible. No profundizar una sola ganadora. |
| **D2** | Bloque común con router de **UNA cuenta**, precios ejecutables verificables, costos base/1,5×/+10RT, P&L incremental, PF, DD, interferencias, capacidad, frecuencia. Si Last no prueba fill, BLOCKED. | Se reportan TODAS las sobrevivientes/descartes del lote y riesgos, sin rescatar parámetros. |
| **CONFIRMACIÓN** | Solo cartera congelada con autorización independiente OOS, Holm, Gate1, robustez por años y reglas de fondeo. | No se abre holdout automáticamente ni se compra fondeo. |

**Importante:** 20 es un requisito de amplitud para entrar a **D1 nueva**, NO es el mínimo de aprobadas a D2. La diferencia entre D1 y D2 es que un markout VWAP o rango futuro NO es P&L de entrada ejecutable. q de DEV reciclada sigue siendo **exploratoria**, aunque supere 0,10. No mezclar el BH de una cohorte CERRADA con hipótesis nuevas. La bandeja D2 espera supervivientes económicas/direccionales; 2 no es un criterio de retorno o alfa, solo protege el trabajo por bloques.

## Estado al adoptar la política (evidencia archivada, no reetiquetada)

| Cohorte | D0 | D1 | D2 |
|---|---|---|---|
| **T29–T58**, 30 preregistradas | 27 TESTABLE, **25 diversas** | 30 medidas, T29/T45/T49 IC90 individuales favorables de RANGO, **q mínimo 0,2122: 0 superan filtro** | 0 |
| **T20–T25**, 6 históricas | 3 TESTABLE | 6 markouts evaluados, 0 alfas respaldadas, fills económicos ambiguos | 0 |
| **T26–T28**, 3 históricas | T26 18/36 viable | T26 rango Δ−67,75 y q1 (contrario al signo); T27/28 no estimables | 0 |
| **T59–T60**, semilla siguiente cohorte | T59 **45/42 TESTABLE**, T60 **71/6 LOW_POWER** | **BLOQUEADA**, solo 1 nueva TESTABLE; faltan ≥19 distintas | 0 |

**T05-377 es únicamente COMPARADOR CONGELADO**, no una superviviente para escalar individualmente: 115 trades, +$5102,50 estrés DEV pero PF con +$10 RT =1,23717, incertidumbre de fills y DD. H69/H74/H77 no reproducibles con Last 08:00–12:00 por ausencia cierre previo RTH 16:00/ATR de días completos; no heredan evidencia histórica.

## Disciplina de salida y gobernanza

- **Por cada ID:** cohorte, pregunta y familia, G0/D0/D1/D2, N_case/ctrl/otros, sesiones/trades, Δ, IC90, p/q + denominador completo, Holm, neto/PF/DD/Δrouter, razón PASS/FAIL/BLOCKED, workflow/artifact/hash; `N/D` cuando etapa no ha medido.
- Cada etapa se **cierra en bloque** con reporte y versión: no publicar «T05 pasó a D2» cuando las otras siguen en D0. Conservar miembros descartados en biblioteca y familia original.
- Solo siete meses Last DEV existentes oct2025–abr2026, 140/135, NO nueva fuente, NO 5s nuevas señales, NO holdouts; sin inventar Bid/Ask agresor o fills.
- **Siguiente acción obligatoria:** ampliar **la cohorte nueva que contiene T59** con mecanismos genuinamente diferentes hasta 20+ D0 viables/diversos, congelar D1 familiar, evaluar todo el lote junto; después agrupar supervivientes en D2. No reoptimizar T59 ni T05 para inflar el embudo.

Fuente de verdad para nuevo trabajo: [tablero de cohortes](NQ_COHORT_FUNNEL_STATUS_2026_10_12.md), complementado por [maestro](../../NQ_PROJECT_MASTER.md), [scorecard](../../NQ_STATISTICAL_HYPOTHESIS_SCORECARD.md) y [log](../../NQ_RESEARCH_LOG.md).
