# T169–T188 — Enmienda técnica V3: exposición ambigua en Last (13-oct-2026)

La Action [38350174954](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38350174954) de V2 completó tests y seis meses DEV, pero **abril 2026 falló cerrado** con `B05H UNRESOLVED SYNTHETIC EXPOSURE FAIL CLOSED`; el agregador fue omitido. **No existen resultados monetarios completos de siete meses** ni operaciones broker. Los seis archivos parciales NO se usan para aprobar ni seleccionar miembros.

**Esta enmienda se hace después de algunos jobs DEV parcialmente terminados, no es un prerregistro limpio de resultados.** No se alteran los 20 disparadores, dirección, ventanas V2, stop24, TP48, horizonte300s, fee, slippage, contrato, capacidad de cuenta o señales legacy T05. Únicamente se separa el resultado de un modelo cuyo simulador original no puede reconstruir por timestamp u horizonte: se marca `NOT_ESTIMABLE_UNRESOLVED_EXECUTION` para **toda la evaluación de siete meses** de ese modelo. Está prohibido convertir una operación ambigua en pérdida, ganancia o PnL=0 y está prohibido puntuar modelos con meses faltantes. No se modifica ni elimina ningún día del denominador 140/135.

Reglas de integridad:

1. Si T05 benchmark legacy presenta ambigüedad, **ABORTAR todo** (no puede haber comparación económica). Para una alternativa individual o router concreto, conservar el error en conteos agregados sin revelar fechas/prints, NO exportar PnL parcial de ese modelo.
2. El resto de modelos independientes puede terminar; modelos individual+router de una candidata deben tener 7/7 meses completos para recibir métricas monetarias. Si cualquiera de ambos está no estimable, esa candidata = `NOT_ESTIMABLE_UNRESOLVED_EXECUTION`, PnL/PF/DD y deltas = **N/D**, sin PASS.
3. 20 IDs reportados, no seleccionar solo ganadores: candidatos censurados siempre cuentan en la cohorte y en los resultados públicos con estado y falta de datos. No se realiza imputación. El número de modelos censurados por mes se publica solo agregado.
4. Todos los siete meses deben seguir 140/135, tests antes de datos, paridad T05 115/+5102,50/+3952,50/DD1797,50, fricción y riesgos originales. Los seis meses iniciales se **recalculan íntegramente** bajo la política técnica nueva. Los datos Last licenciado solo están dentro del runner y se borran antes de artifact.
5. La enmienda NO mejora la validez estadística/OOS: periodo 2025-10 a 2026-04 reiteradamente usado; mayo–septiembre 2026/H sellados; broker fills no verificados; ninguna aprobación oficial.

Se preservan el [prerregistro inicial V1](NQ_T169_T188_MONETARY_BLOCKS_PREREG_2026_10_13.md) y la [compatibilidad de ventanas V2](NQ_T169_T188_MONETARY_BLOCKS_V2_EXECUTION_COMPATIBILITY_2026_10_13.md). La V3 es solo una **reparación de reporte de exposiciones no observables**, no un ajuste para favorecer el PnL.
