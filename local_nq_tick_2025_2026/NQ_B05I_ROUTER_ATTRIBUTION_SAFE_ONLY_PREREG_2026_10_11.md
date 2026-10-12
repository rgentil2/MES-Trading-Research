# NQ-B05I — Auditoría de atribución exclusivamente sobre resúmenes existentes

Fecha 2026-10-11 Colombia. **Auditoría NO ALPHA**: no se estudian nuevas hipótesis, no se abre nueva fuente/data/OOS, no señales de 5 segundos, ni se recupera tick data de releases. Se usa **únicamente** el JSON seguro `summary.json` del artifact `b05h02-seven-month-safe-reversion-report` ID **11722303789**, producido por [Actions 38193895252 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38193895252) y ya contiene los siete meses completos DEV y la atribución de dueños H02. Este protocolo fija la matemática y la conclusión aceptable **antes de ejecutar el código específico de atribución**; no puede rejuvenecer DEV ni crear nueva estrategia.

## Preguntas y ecuaciones congeladas

Para cada mes histórico m, las tres alternativas `T05_377`, `H02_PRINT_VWAP_MEAN_REVERSION`, `T05_PRIORITY_H02_SHARED_ROUTER` comparten costos y la misma cuenta NQ:

- `PnL_T05_retenido_m = PnL_router_m - PnL_H02_owner_en_router_m`.
- `PnL_T05_desplazado_m = PnL_T05_original_m - PnL_T05_retenido_m`; si es negativo, las operaciones T05 omitidas fueron en neto perdedoras **en el escenario histórico**, sin convertirlo en señal causal para elegir cuándo omitirlas.
- `Delta_router_m = PnL_H02_owner_en_router_m - PnL_T05_desplazado_m` debe coincidir exactamente con `router_m - T05_original_m`.
- `Delta_total = sum(Delta_router_m)` debe coincidir exactamente con el dato congelado **−USD2907,50 estrés**. H02 contributed suma **−USD2530**, T05 desplazadas suma **+USD377,50**, router neto **+$2195** y baseline **+$5102,50**.
- `H02 standalone_m` es un modelo distinto del `H02 owner en router`; calcular explícitamente brecha de selección/capacidad sin alegar alpha. En diciembre 2025 H02 standalone **+$530**, H02 owner router **−$605**.
- Verificar `source_days=140`, `eligible_days=135`, 7 meses exactos, `decision=B05H02_REJECT_DO_NOT_PROMOTE`, `holdouts_opened=false`, `new_history_acquired=false`, `H02_uses_5s_signals=false`; que el modelo T05 conserva 115 trades y H02 en router 60 trades. Rechazar cualquier JSON que viole estos controles.
- Reportar mensualmente **solo** cuentas netas de escenarios estrés originales (y contabilidad +$10 del resultado congelado) y agregados, jamás fechas de trades, precio, timestamp ni filas Last.
- Clasificar de forma OBSERVACIONAL qué meses el H02 fue neto negativo, pero **prohibido** crear o sugerir una regla `operar solo marzo`/cuanto más favorable ex post, porque sería p-hacking.
- Output `DECISION_B05I_AUDIT_COMPLETED_H02_INCREMENTAL_FAIL`. Siguiente bloque deberá justificar por mecanismo independiente y diseño causal si hay alguna familia nueva; no ajustar H02, no promocionar T05 ni comprar fondeo.

Cualquier discrepancia contable = **FAIL CLOSED**; no tratar números de standalone como PnL real de portafolio, ni inventar acceso a precios ejecutables en Last.
