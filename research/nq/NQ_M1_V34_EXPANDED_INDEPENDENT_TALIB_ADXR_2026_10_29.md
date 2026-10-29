# NQ S0.29 — Auditoría ampliada de paridad matemática contra TA-Lib y corrección ADXR

**29-oct-2026.** NQ OHLCV M1, un contrato, búsqueda futura IST 2020–2022. Esta etapa **no lee ningún archivo de mercado**, no genera señales ni PnL, no selecciona estrategias, no abre 2023–2026 y no altera la cohorte congelada de 10.000 AST.

## Error real descubierto

El experimento `nq_m1_v26_trend_momentum.py` implementaba **ADXR** como el promedio entre `ADX(t)` y `ADX(t-n)`, porque consultaba `data[-n-1]`. La referencia `TA-Lib ADXR` utiliza la separación **n−1 barras**: `(ADX(t)+ADX(t-(n-1)))/2`, `data[-n]`.

La **primera ejecución CI** [40865408719 FAILED](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40865408719) detectó **21 aserciones fallidas** de ADXR con distintos períodos, instantes y trayectorias sintéticas; entre ellas diferencias superiores a varios puntos del índice ADXR. Esto afecta potencialmente predicados LONG/SHORT de estrategias con ADXR. No interpretar esos 21 subtests como 21 estrategias. La corrección cambia **solo el prototipo aislado V2.6** y exige ambas lecturas finitas; V2.1 congelado, 10.000 AST y su SHA original NO se modificaron.

Después de corregir el desfase, la [segunda ejecución CI 40865519690 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40865519690) registró **351/351 tests PASS**, incluyendo **6 nuevas pruebas** de oráculos matemáticos externos.

## Referencias independientes ampliadas

[Archivo de tests](test_nq_m1_v34_expanded_independent_talib.py) compara las rutas NQ M1 contra TA-Lib C v0.6.8 mediante Python (distinta implementación), sobre **tres series OHLCV totalmente artificiales de 1.024 barras cada una**. Recorre períodos, diferentes precios de entrada y los índices completados 440, 720 y 980.

| Fórmulas verificadas en la nueva matriz | Oráculo |
|---|---|
| SMA, EMA, WMA, DEMA, TEMA, TRIMA | TA-Lib sobre close y además open / HL2 |
| APO (con MA tipo EMA) | TA-Lib APO |
| TRIX (triple EMA ROC) | TA-Lib TRIX |
| ATR / NATR | TA-Lib Wilder ATR / NATR, multiplicador NATR=1 |
| ADXR, tras corregir el desplazamiento | TA-Lib ADXR |
| Warmup DEMA y TEMA | 2n−1 y 3n−2 muestras; falta de barras = None |
| Causalidad | Mutación de barras posteriores a señal, misma salida del índice completado |

Estas **11 familias** probadas en esta ampliación no reemplazan las ya contrastadas en otros tests (ADX, MACD, KAMA, T3, Stochastic, Bollinger). Un `PASS` se limita a **los períodos, fuentes y tolerancias explicitados**; no certifica cualquier parámetro, ejecución live, algoritmos comerciales ni 132/132. Algunos nombres de nuestro catálogo son **variantes personalizadas** que necesitan una especificación matemática propia, no una igualdad que no aplica con TA-Lib (Hilbert FFT, Ehlers, patrones geométricos, True Range relativo, RSI transformado).

## Consecuencias para el embudo

- En la primera campaña real futura, **cualquier candidato que utilice ADXR deberá evaluarse con la versión corregida y registrada del motor**, nunca mezclar fitness calculado con una fórmula anterior. No se conservará una evaluación antigua como si fuera comparable.
- No se han medido ni modificado las 10.000 estructuras por causa de este fallo. El criterio de multiplicidad, lineage y separación temporal permanece igual.
- **Los 13 controles formales continúan 0/13 PASSED_VERIFIED y `EXECUTION_BLOCKED`**; esta es evidencia técnica para completar INDICATOR_LIBRARY_132 y PARAMETER_SEMANTICS, no su aprobación final.
- La etapa obligatoria N8 NinjaTrader 8 del **portafolio compartido ganador** sigue después de Portfolio Builder/Allocator; deberá comparar también ADXR y sus señales con la versión del algoritmo congelado, además de ejecuciones, costes, PnL y DD. No se ha ejecutado NinjaTrader.

## Próximo trabajo

Separar formalmente **indicadores estándar con oráculo externo** de **variantes personalizadas que requieren oráculo matemático independiente propio**; registrar cobertura por cada familia de parámetros y construir pruebas de las variantes de entrada/salida con barras M1 antes de liberar la campaña IST. Para cualquier cambio posterior, conservar causa, SHA del motor y resultados previos sin alterar la cohorte.
