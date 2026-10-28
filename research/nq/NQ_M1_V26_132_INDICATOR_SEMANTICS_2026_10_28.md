# NQ M1 V2.6 — 132/132 implementaciones matemáticas, NO certificación de estrategias

**Fecha:** 2026-10-28 · **universo:** exactamente NQ M1, 1 contrato · **campaña:** S0.21 · **estado:** únicamente técnico, sin datos históricos, sin PnL, sin uso de 2023–2026.

## Recuento comprobable

| Conjunto de nombres registrados | Cobertura de funciones | Habilitado en V2.1 de generación económica |
|---|---:|---|
| Motor V2.1 original inalterado | 38 | No, campaña de calidad bloqueada |
| Incubadoras V2.2 DEMA/TEMA/TRIMA/APO/TRIX | 5 | No |
| Incubadoras V2.5 escalares y patrones | 24 | No |
| Implementaciones experimentales V2.6 nuevas | 65 | No |
| **Total con ruta de cálculo comprobable** | **132 / 132** | **0 formalmente liberados** |

Se creó [lector de 132](nq_m1_v26_all_132_router.py) que cruza el **ID/nombre** del catálogo, comprueba todos los dominios numéricos/enumerados, detecta parámetros ausentes/sobrantes, corta las velas futuras y devuelve `None` cuando falta warmup o contexto causal. El catálogo original no se sustituyó.

**¡Importante!** Cobertura de código no implica 132 fórmulas correctas para TA-Lib, NinjaTrader o StrategyQuant. Algunos nombres de origen multisalida y parámetros del catálogo de diseño original eran imprecisos: a continuación se especifican las elecciones provisionales que deben certificar oráculos independientes ANTES de buscar estrategias.

## Contrato de cálculo y sesgos

- Cualquier lectura se limita a velas COMPLETADAS (`i` incluido), con validez OHLCV; nunca se extrapola hacia el futuro. Los valores no disponibles devuelven `None`. Las pruebas cambian deliberadamente velas posteriores para comprobar causalidad.
- Para indicadores con el campo `threshold`, el lector devuelve **valor bruto menos umbral**; el AST nuevo usa comparaciones respecto de cero. `RSI` usa la distancia mínima a los límites inferior/superior, ambos efectivos, hasta aprobar semántica definitiva. `Williams %R` pasa el módulo de %R a escala positiva antes de restar su umbral. Esto NO puede confundirse con el RSI/%R sin transformación.
- Donde el catálogo registraba `multiplier`, se aplica explícitamente como escala o amplitud. El bloque `True Range` con período en el catálogo se implementó provisionalmente como **TR último / media de TR del período × multiplicador**, NO como TR nativo; exige renegociación semántica antes de certificación.
- `MACD` y `PPO` representan el **histograma**, así se usan los tres parámetros registrados. `Stochastic` representa línea %D; `Stochastic RSI` es un cálculo K/D sobre RSI. El catálogo de estos indicadores debe incluir selectores de salida si se quiere abarcar líneas principales y de señal como hipótesis diferentes.
- `Bollinger Bands`, `Keltner` y `Acceleration Bands` admiten salida superior/inferior/ancho; se evita seleccionar la línea central en el generador cuando eso dejaría inactivo el multiplicador. Los pivots permiten superior/inferior/central, con rango definido a partir del ancla escogida.
- `Opening Range` y `Initial Balance` devuelven **ancho**, no nivel superior e inferior separado. `Previous Day High/Low` admite selección de alto/bajo/centro/ancho en V2.6.
- `Anchored VWAP`, `VWMA` y pivots con `causal_timestamp` exigen índice de ancla, nunca uno posterior al índice evaluado. Pivots `previous_completed_session` y `Previous Day High/Low` exigen sesiones RTH completas previas del **mismo contrato** entregadas explícitamente por el llamador. No suponen un empalme distinto.
- `Klinger Oscillator`, `TTM Trend`, `Chande Kroll Stop`, `QQE`, `SMI Ergodic`, `NR4/NR7`, `Connors RSI` y otros bloques antes ausentes usan fórmulas experimentales documentadas en código: sus nombres son descriptivos, pero la paridad exacta con StrategyQuant no ha sido demostrada.
- `Hilbert` utiliza analítica FFT causal en ventana acabada (no método recursivo HT_* de TA-Lib). La familia Ehlers utiliza los filtros causales explícitos. No se confundirán con los indicadores comerciales sin verificación.
- Los 12 patrones de velas V2.5 son detectores geométricos definidos localmente, no las reglas implícitas de CDL_* TA-Lib/StrategyQuant.

## Vínculo con generador y QA

El [generador V2.6](nq_m1_v26_structural_generator.py) recorre los **132 IDs**, con manifiesto de cobertura uno-a-uno, además de población amplia con muestras RANDOM, MUTATE y CROSSOVER, línea de salida explícita, SHA canónico, padres, umbrales tipados, NQ 1 contrato y únicamente IST 2020–2022 permitido *para una futura fase económica*. **El generador actual no lee los años IST ni evalúa fitness**. No modifica las 100 estrategias congeladas del experimento V2.1.

Suite [test_nq_m1_v26_all_132.py](test_nq_m1_v26_all_132.py), [test_nq_m1_v26_structural_generator.py](test_nq_m1_v26_structural_generator.py), [test_nq_m1_v26_external_talib.py](test_nq_m1_v26_external_talib.py) y [GitHub Actions v26](../../.github/workflows/nq-m1-v26-132-qa.yml) junto con pruebas heredadas. Se coteja solamente un subconjunto de indicadores mainstream ADX, MACD, KAMA, T3, STOCH y BBANDS contra TA-Lib sobre series **sintéticas**; esto no certifica todas las fórmulas.

## Pendientes NO negociables para evaluación real

1. Auditoría independiente para equivalencia de los 132 nombres y sus salidas en NinjaTrader/StrategyQuant o especificación científica; revisar fórmulas personalizadas, warmup/semántica de parámetros, rangos y tests con datos reales permitidos (IST). **132/132 funciones programadas != 132/132 certificadas**.
2. Datos de ticks NQ Last/Bid/Ask de IST 2020–2022 o protocolo alternativo de OHLC conservador explícitamente aprobado; no afirmar fills con ticks que no existen en nuestros releases.
3. Cierre de 13 puertas de calidad, adapters G0/D0/D1/D2, riesgo plan MFFU confirmado, cartera de una sola cuenta y autorización final SHA-bound.
4. Mantener sin cambios rollover del jueves ocho días antes del tercer viernes trimestral y sin abrir ISV1 2023, ISV2 2024, 2025 ni 2026 para generar/seleccionar estrategias.

**Decisión:** el hito de *programar rutas para los 132* queda completado únicamente si CI valida 132/132 y conserva BLOQUEO ECONÓMICO. La evaluación real no puede empezar solo por este número.
