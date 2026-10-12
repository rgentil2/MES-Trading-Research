# NQ-B05G — PROPUESTA PRERREGISTRADA: sensibilidad al orden de prints Last con timestamp idéntico

Fecha 2026-10-11. Estado: **PRERREGISTRO, SIN EJECUTAR P&L NUEVO**. Nace del [B05F observado](NQ_B05F_EXISTING_LAST_QC_RESULTS_2026_10_11.md), **no de escoger resultados rentables**.

## Motivación y objetivo

B05F leyó sobre los 7 meses DEV NQ **30.850.741** prints Last; detectó **15.979.304** eventos cuya marca temporal coincide con la del registro anterior, **5.390.040** con precio diferente. T05-377 usa orden de impresiones por 233/377 y T04 toca stops/TP según trayectoria Last. Queremos determinar si el resultado es frágil al **orden de las filas dentro de un grupo de timestamp igual**, no falsificar qué orden transmitió realmente CME ni asumir que el exportador pierde necesariamente el orden.

## Universo y límites (congelados antes de resultados)

- **ÚNICAMENTE** los mismos siete releases Last NQ privados DEV octubre 2025–abril 2026, **140 días fuente/135 elegibles** según las reglas de apertura originales. Misma verificación SHA256. Si se requiere cargar los ficheros ya archivados dentro de un runner temporal, no ampliar nada. **PROHIBIDO** adquirir datos, otros proveedores, Replay o extender fechas.
- Prohibido abrir H minuto 2025/26, T mayo/junio 2026 y T julio–septiembre 2026.
- Preservar los datos crudos intactos. Grupos de timestamps con 1 print se dejan idénticos. Para cada grupo con 2+ prints de timestamp exactamente igual, mantener su multiconjunto **(timestamp,price,qty)** sin pérdida de cantidad, sin mover prints fuera del timestamp ni entre días/contratos.
- Variantes ex-ante: `ORIGINAL_SOURCE_ORDER`, `REVERSE_WITHIN_EQUAL_TS`, `PRICE_ASC_WITHIN_EQUAL_TS`, `PRICE_DESC_WITHIN_EQUAL_TS`. Para empate de precio conservar orden original de filas (estable). **Son perturbaciones de sensibilidad, no prueba de equivalencia con ejecución CME, ni procedimiento para limpiar fuente.**
- T05 congelado: mismo generador causal T02 y filtro 377 Last, sin cambiar 233/377 a valor más favorable. Una sola cuenta, 1 NQ, 2 operaciones/día, daily closed PnL gate -$600, mismo T04 fixed 16–48 ticks risk stop/2R y 300s timeout; base 1 tick adverso/lado+fee$5 RT, estrés 2 ticks adversos/lado+fee$7.50 RT y estrés+$10 por trade fijo contable. Se mantiene emparejamiento estricto de días/contrato, ET/DST e imposibilidad de explotar datos de futuro.
- **Control principal:** `ORIGINAL_SOURCE_ORDER` debe recuperar EXACTAMENTE T05 115 trades /+$6220 base y 115/+$5102.50 estrés, DD Last cronológico estrés **$1797.50** antes de considerar perturbaciones. Toda violación aborta la tarea.
- Output solo contadores e indicadores agregados: por escenario/variante, cobertura, número de señales T05, número de trades, P&L estrés, PF, DD Last envelope, porcentaje de sesiones con cambios de señales, casos en que resultado depende de empate. Nunca exportar timestamp/precio/trade individual. Todas las variantes de perturbación (incluso negativas) se informan.
- Comparación científica: los resultados de las 4 variantes son un rango **adversarial de hipótesis de orden**, NO intervalo probabilístico de fills ni elección del escenario favorable. Evitar cambiar criterios después para rescatar T05.
- B05G es auditoría de **robustez sobre el DEV ya explorado**, no 4 estrategias adicionales ni OOS. Si T05 se deteriora materialmente, bajar su prioridad y describir el problema; no filtrar los grupos sensibles a posteriori como sistema causal.
- Después de B05G, el siguiente programa para beneficio incremental NQ tendrá mecanismos independientes con variables verdaderamente observadas (precio, trade-rate/volatilidad y contexto de 4181/10946 prints) y límites de búsqueda; incluso si B05G sale bien, no significa T05 apta para fondeo.

**No ejecutar todavía fuera de un GitHub Action versionado y probado**; prerregistro no es resultado científico por sí mismo.
