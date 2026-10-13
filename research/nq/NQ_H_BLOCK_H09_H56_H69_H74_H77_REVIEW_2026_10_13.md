# BLOQUE H-B — cinco ID, dos mecanismos padres, decisión de cartera (revisión documental)

**Fecha:** 2026-10-13. **Estado:** revisión de resultados congelados de **2020–2024 NQ 1m**, **SIN backtest nuevo**, sin alterar padres, costos, ventanas, filtros ni elegir una configuración post hoc. Esta revisión materializa la **rotación fuera de T05/T147**; los holdouts H 2025/26 siguen sellados.

## Pregunta

¿Son H09/H56/H69/H74/H77 cinco fuentes de beneficio realmente distintas capaces de formar varias posiciones, o una sola familia de rutas alternativas cuyos cambios reducen frecuencia sin incrementar retorno?

**Respuesta basada en datos ya auditados:** es una familia de dos señales originales H09 y H56. H69, H74 y H77 se construyen con esas mismas señales; no hay cinco alphas. H74 y H77 mostraron mejor PF/DD cerrado, pero pierden neto total frente al router H69 en un contraste emparejado.

## Cuadro monetario y regla de decisión

| ID | Rol | Periodo / unidad | N trades | Neto USD | PF | DD USD | Evidencia que impide promoción |
|---|---|---|---:|---:|---:|---:|---|
| H09 | Padre: gap a favor del impulso temprano | 2020–24 1NQ barra 1m, bracket central | 173 | ~+18.874 | 1,369 | 8.122 DD cerrado | 1NQ excede DD ilustrativo US$2.000; 1MNQ central N173 ~+1.661 DD~860 pero no fills MNQ |
| H56 | Padre: reversión contra cuerpo premercado | 2020–24 1NQ barra 1m, bracket central | 100 | +8.697,98 | 1,269 | 3.599,09 DD cerrado | N100 y DD 1NQ alto; años/IC/q insuficientes |
| H69 | Router H09 OR H56 | 2020–24 1MNQ PROXY | 262 | +2.704,44 | 1,335 | 890,64 DD cerrado | BH q0,115; DD *floating* no estudiado; 78 pausas >7 días; CAGR nominal ref 50K 1,06% |
| H77 | Si gap/premercado alineados H09, si opuestos H56 | 2020–24 1MNQ PROXY | 140 | +2.385,30 | 1,632 | 584,54 DD cerrado | -319,14 vs H69, 75,2% de beneficio en 2022, N140 |
| H74 | Volatilidad heredada baja H09; alta H56 | 2020–24 1MNQ PROXY | 132 | +1.657,84 | 1,438 | 444,10 DD cerrado | -1.046,60 vs H69, N132 y q0,1149 |

**Comparaciones emparejadas que sí son válidas dentro de la familia H:** H74 menos H69 = **-$1.046,60**; H77 menos H69 = **-$319,14**; H69 al añadir H56 a H09 en ablation documentada = **+$630,18** (no es una nueva validación). Los cinco ID NO operan concurrentemente; todos comparten fechas, entradas base y riesgos. **No se suma** el neto de H09+H56+H69+H74+H77. El H09 1NQ original tiene parámetros/fricción distintos del router 1MNQ, y tampoco se añade a los valores H69.

**Hallazgos que evitan otra ronda de optimización:**
- Ninguna de las seis variantes H73–H78 mejoró el beneficio total de H69; no necesitamos una octava variante de selector de volatilidad/gap sobre los mismos años.
- El mejor PF H77 es producto también de MENOR exposición (140 vs 262 trades), no superioridad económica confirmada. H77 tiene 2022 concentrado, la muestra es pequeña y supera por poco q nominal sin controlar la adaptación previa.
- H69 y H77 no alcanzan la meta anual nominal del proyecto (15%) con 1MNQ en USD50k, independientemente de la comparación ETF aún pendiente.
- H09 1NQ muestra potencial neto pero DD cerrado~8.122 >US$2.000; cambiar a MNQ exige ejecución/fees/modelado, no multiplicación ingenua.
- H69 puede conservarse como comparador H para una eventual validación independiente *autorizada*, no implica necesidad ni permiso de abrir 2025/26 ahora.

## Decisión y cambio de bloque

**Resultado de la revisión H-B: NO_PROMOTE, NO_NEW_H_VARIANT.** Conservar H09 y H56 como mecanismos distintos y H69 como router comparador; H74/H77 como investigación de selectividad, no alphas nuevos. **Cerrar el turno H-B**, no volver a optimizar H09 stops ni crear H79–H90 sobre los mismos años por mero aumento de PnL.

**Siguiente bloque de la rotación:** estudiar una cohorte diversa T-C de mecanismos Last atómicos que no sea T05/T147/H gap; diseñar preguntas con stops causales antes de simulación, cohortes completas (≥20 solo si realmente distintas) y una sola pasada G0/D0. Si no hay evidencia de mecanismo nuevo en los Last existentes, registrar que es insuficiente y priorizar NinjaTrader SIM para contrastar una especificación congelada con ejecución más realista (sin declarar aptitud de fondeo).

**Documentos históricos consultados:** [H09 escenario central 2020–24](NQ_H01_H02_H05_H09_EXECUTION_EXPLORATION_RESULTS_2020_2024.md), [H56 resultados](NQ_H53_H58_RESULTS_2020_2024.md), [H69 frente a componentes](NQ_H67_H72_RESULTS_2020_2024.md), [H74/H77 régimen](NQ_H73_H78_RESULTS_2020_2024.md).
