# NQ S0.32 — auditoría de warmup sin precios para las 10.000 estrategias AST

**29-oct-2026.** Después del primer piloto de mercado S0.31 de 120 reglas de control, se generó una auditoría estática separada sobre la cohorte congelada **original 10.000** de estructura de 132 indicadores. Aquí **no** se leyó OHLC real ni sintético, no se midió PnL y no se descartó ninguna AST.

[Implementación](nq_m1_v37_10k_intraday_warmup_audit.py) vuelve a generar 10.000 estrategias de semilla fija `20261028`, y bloquea cualquier discrepancia frente a SHA del lote `b9d2915fc55f86546ef63d74a588df5244d094eeecb4a7c900a4000d47660be9`. Cada AST se analiza como árbol AND/OR y se calcula una cota mínima de barras cerradas para un subconjunto de indicadores con warmup conocido: SMA/EMA/WMA/RMA/DEMA/TEMA/TRIMA/T3/APO/TRIX/KAMA/ATR/NATR/TR/Donchian/MACD/HMA/ALMA/ZLEMA/StdDev/Variance. A esos mínimos se agregan retrasos y cruces de la condición. El límite es **117 barras cerradas** a las 11:27 ET (09:31 índice0 a 11:27 índice116), justo antes de entrada límite 11:28 y flat 11:29.

**Resultado [CI #40871008503 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40871008503): 368 tests PASS** (5 pruebas nuevas). Categorías inferiores para el hipotético historial solo intrasesión:

| Clasificación de ruta estática | AST |
|---|---:|
| No se detectó barrera estática de dos direcciones en las rutas auditadas | 9.130 |
| Una dirección no puede dar TRUE antes de 11:27 bajo ese supuesto | 846 |
| Las dos direcciones no pueden dar TRUE antes de 11:27 bajo ese supuesto | 24 |
| **Total regeneradas sin alteración** | **10.000** |

[Artefacto ZIP de 10.000 fichas técnicas](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40871008503/artifacts/12895153689); SHA256 `dd8492b276a66462aee373a54089798b3132acc9eda6fad169df2c28bc70dd50`. [Evidencia persistente](NQ_M1_V37_S032_FROZEN_10K_INTRADAY_WARMUP_EVIDENCE_2026_10_29.json).

**Interpretación obligatoria:** es una auditoría condicionada a NO transportar valores desde sesiones RTH anteriores. Ese transporte puede habilitar indicadores de período largo del mismo contrato; en los bloques cuyo mínimo no se modela la conclusión por defecto es «posible/indeterminado», no «aprobado». La evaluación posterior del AST completo puede descubrir otros bloqueos. **No se eliminan las 870 estrategias señaladas**, ni se promociona G0 formal, ni se publican clasificaciones de aptitud económica.

Esta auditoría tampoco declara «9.130 estrategias listas»: solo 9.130 sin impedimento *probado por este test limitado*. Continúan 0/13 puertas de aprobación económica y la futura necesidad de validación obligatoria de la cartera en NinjaTrader 8.
