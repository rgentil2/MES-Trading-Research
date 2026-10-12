# NQ T14–T19 — PRIMERA MEDICIÓN ECONÓMICA Y PREDICTIVA COMPLETA (DEV solamente)

**12-oct-2026. Estado: `T14_T19_EXPLORATORY_DEV_ECONOMIC_AND_MAGNITUDE_COMPLETE`.** Se evaluaron **seis preguntas diferentes**, no se recalibró T05, ni se alteraron stops/umbral de las nuevas señales. **Ninguna nueva hipótesis aprobó los gates de rentabilidad o validación estadística.**

## Fuentes y trazabilidad

- [Prerregistro de seis hipótesis T14–T19](NQ_T14_T19_NEW_MECHANISMS_REGISTER_2026_10_12.md) y [pantallas de frecuencia](NQ_T14_T16_SIGNAL_SCREEN_RESULTS_2026_10_12.md), [T17–T19](NQ_T17_T19_SIGNAL_SCREEN_RESULTS_2026_10_12.md). Antes de medir P&L quedaron fijados [T14–T16 riesgo/ejecución/cartera](NQ_T14_T16_ECONOMIC_FIRST_PASS_PREREG_2026_10_12.md) commit `62fe9d60bd83f9d4ff8e0938b89c31505da309c0`, y [T18 mismo riesgo; T17/T19 objetivo rango futuro de 15m](NQ_T17_T19_PREDICTIVE_T18_ECONOMIC_PREREG_2026_10_12.md), commit `3c085a3ea46aca9c43cecd18903952ff56f319a5`.
- Motor [nq_t14_t19_economic_and_magnitude.py](../../local_nq_tick_2025_2026/nq_t14_t19_economic_and_magnitude.py) commit `ed270bef2564cb0675f1b62614157568c1ca6e06`, [agregador estadístico](../../local_nq_tick_2025_2026/nq_t14_t19_economic_aggregate.py) commits `1ccae2c2316561317208ea3a6187307bbd0e9653`, `1da915ab9173b6eb6202278beb580d85fe53d9c8` y corrección de salida `7b1d072951aa9c346d1e0b38c4b1296774b639d3`; [siete pruebas sintéticas](../../local_nq_tick_2025_2026/test_nq_t14_t19_economic.py), commit `ae9b7f12378fd513ecffa5be20d23af8057231e0`.
- [**GitHub Actions 38279226193 SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38279226193), siete pruebas PASS y corrida completa. Artifact seguro `nq-t14-t19-six-questions-economic-magnitude-aggregates-safe` ID **11760293834**: `summary.json`/`report.md`; se descargó y verificó. **140 días fuente/135 elegibles, 7 meses, T05 PARIDAD EXACTA 115 trades, +USD5.102,50 estrés, +USD3.952,50 estrés+$10 RT fijo, PF estrés1,31826, DD Last1797,50.** Ninguna fuente nueva, no datos sellados T/H, no 5s en señales nuevas (T05 histórico solo benchmark), no datos de trade/día publicados; `_private` borrado del runner.
- Auditoría de ejecuciones anteriores: [38278574936 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38278574936) por sintaxis YAML del nombre antes de lectura; [38278644491 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38278644491) procesó correctamente los siete meses pero el agregador abortó al buscar la clave `extra10_fixed_path` diferente de la etiqueta del escenario; corregido solamente el nombre del campo, **no señales/costes/órdenes**. No se usó el resultado fallido para seleccionar variantes; el último Action completó controles completos.

## 1. Cuatro hipótesis direccionales: cuenta individual, 1 NQ bajo estrés

Reglas congeladas: barra ≥377 prints Last, primer evento de la sesión en 09:45–11 ET, entrada sintética tras timestamp completo, SL=32 ticks de precio NQ, TP=48 ticks, 300s máximo, latencia 1ms, slip2 ticks adversos por lado, comisión US$7,50 RT; coste adicional US$10 RT sobre ruta sin recalcular stops. No hay garantías de Bid/Ask ejecutable.

| Hipótesis / pregunta | N trades ejecutados (simulados) | Meses +/7 | P&L neto estrés USD | PF estrés | DD Last estrés USD | Neto +$10 RT USD | PF +$10 | IC90 media neta USD/sesión extra$10 L5 | BH q* | ¿Cumple? |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| **T14** ¿Persistencia suave anticipa continuidad? | **115** | 2 | **−4192,50** | 0,69030 | **5862,50** | **−5342,50** | 0,62555 | **[−65,63,−14,31]** | 1,00 | **NO** |
| **T15** ¿Aceptar niveles redondos genera continuación? | **133** | 0 | **−3437,50** | 0,77095 | **3797,50** | **−4767,50** | 0,69859 | **[−57,59,−7,02]** | 1,00 | **NO** |
| **T16** ¿Qty por print alto sin desplazamiento anticipa reversión? | **0** | 0 | 0 | N/D | 0 | 0 | N/D | N/D, sin operaciones | 1,00 por convención | **NO SEÑALES** |
| **T18** ¿Persistencia de dirección de la subasta preopen? | **98** | 3 | **−1050** | 0,89899 | **3630** | **−2030** | 0,81470 | **[−36,76,+4,91]** | 1,00 | **NO** |
| **T05 congelada** (control histórico, NO hipótesis nueva) | 115 | 6 | **+5102,50** | 1,31826 | 1797,50 | **+3952,50** | 1,23717 | **[−4,82,+62,50]** | N/D | No aprobada para fondeo |

* q Benjamini–Hochberg sobre la **familia completa de cuatro** tests económicos nuevos T14/T15/T16/T18, usando p unilateral de bootstrap centrado bajo +$10, T16 p=1; **q es DESCRIPTIVA IN-SAMPLE**, NO un valor confirmatorio ajustado por las muchas hipótesis adaptativas anteriores. El histórico 135 sesiones no es muestra independiente de la selección. Holm y validación OOS permanecen N/D.

**Gates que fallan T14/T15/T18**: expectativa +$10 neta no positiva, PF estrés y extra <1,25, DD Last estrés por encima de US$2000 de referencia ILUSTRATIVA NO VERIFICADA de fondeo, IC90 +$10 L5 inferior <=0, y contribución incremental en router negativa. El volumen mínimo ≥5 trades/mes sí se observa en las tres; **más frecuencia no implica edge**. T15 además perdió en 7/7 meses standalone.

## 2. Interferencia real con T05, sin sumar backtests independientes

En la misma cuenta, 1 NQ, máximo 2 operaciones por día, sin solapamiento y stop de nuevas entradas tras −$600 realizado:

| Contrafactual de cartera | N trades | P&L cartera estrés USD | Diferencia versus T05 estrés USD | Diferencia versus T05 con +US$10 RT USD | IC90 del INCREMENTO diario +$10 L5 |
|---|---:|---:|---:|---:|---|
| **T05 sola** | 115 | **+5102,50** | 0 | 0 | N/A |
| **T05 + T14** | 198 | −290 | **−5392,50** | **−6222,50** | [−80,28, −13,68] |
| **T05 + T15** | 212 | +110 | **−4992,50** | **−5962,50** | [−76,24, −11,63] |
| **T05 + T16** | 115 | +5102,50 | 0 | 0 | [0,0]; no señales |
| **T05 + T18** | 180 | +720 | **−4382,50** | **−5032,50** | [−68,19, −8,22] |

**Tres incorporaciones activas empeoran el resultado y sus intervalos de la diferencia +$10 son completamente negativos** bajo el bootstrap por bloques principal. Las carteras T05+T15/T18 mantienen rentabilidad nominal marginal, pero **no superan T05**, que es el contrafactual correcto. No construir un filtro retrospectivo de señales ganadoras basado en retornos.

## 3. Dos preguntas de MAGNITUD futura, distintas de trading

Para la **primera ocurrencia diaria** del evento y los 15 minutos siguientes (`t>t_decisión` y `t<=t_decisión+15min`), se midió el rango high−low de Last:

| ID | Pregunta | N días con evento y horizonte | Media de rango posterior, ticks NQ | Contrafactual sin evento | Efecto estadístico / P&L |
|---|---|---:|---:|---|---|
| **T17** | ¿Aceleración de prints sin expansión contemporánea predice amplitud futura? | **135/135** | **421,74 ticks** (105,44 puntos índice) | **0 días sin evento** | **NO IDENTIFICABLE / N/D** |
| **T19** | ¿Trayectoria poco eficiente predice amplitud futura? | **135/135** | **446,50 ticks** (111,63 puntos índice) | **0 días sin evento** | **NO IDENTIFICABLE / N/D** |

**No podemos decir que T17/T19 predigan una amplitud *mayor*** porque no existe un grupo sin evento. Los rangos observados no son beneficios monetarios y las señales no especifican dirección ni políticas de trading. No ajustar retrospectivamente umbrales para crear controles favorables.

## 4. Conclusión y siguiente programa de investigación

1. **T14, T15, T18: HIPÓTESIS ECONÓMICAS RECHAZADAS bajo sus reglas originales**, no reoptimizar sobre estos 135 días.
2. **T16: SIN SEÑALES**, congelar resultado negativo de viabilidad.
3. **T17 y T19: magnitud post-evento DESCRITA pero poder predictivo NO IDENTIFICABLE** con eventos todos los días; no convertir en estrategias direccionales por intuición.
4. **T05 queda congelada** como única referencia histórica, sigue exploratoria y falla PF con extra$10 RT y riesgo de ejecución. Ninguna estrategia ni cartera aprobada para fondeo, sin OOS abierto.
5. **Siguiente bloque: T20–T25, NUEVAS PREGUNTAS de mecanismos realmente diferentes**, diseñar preregistro de variables, contrafactuales y observabilidad, evitando filtros nuevos T14/T15/T18 o binning optimizado de magnitud T17/T19. Buscar pruebas con controles contemporáneos identificables y muestras suficientes, corrigiendo el presupuesto de hipótesis. La meta no es conseguir falsamente 150 variantes ni continuar análisis de T05.

**Nota de reproducibilidad estadística:** el preregistro T18 mencionó semilla `20261012+L`; la implementación usó una **semilla determinista previamente codificada por modelo y bloque** (`20261012+L+len(modelo)`) para IC90. Se registra como divergencia técnica del texto de preregistro y **no se escoge otra semilla ni se recalcula para obtener resultados favorables**. El rechazo económico es independiente de las semillas y los netos/paridades son exactos; q/p siguen solo descriptivos.
