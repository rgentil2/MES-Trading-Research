# NQ T20–T25 — D1 de desplazamiento observacional por grupos timestamp, RESULTADOS COMPLETOS

**12-oct-2026 · [Action 38296113086 COMPLETED/SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38296113086) · [artifact agregado seguro 11767833548](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38296113086/artifacts/11767833548)** · digest ZIP `sha256:04842011206b34c24d2645f911ecbbf44c54a9f8920b9c4d10dea19aadfc8f3e` · contiene `summary.json` y `report.md`, inspeccionados directamente tras descargar el artifact. **8/8 pruebas sintéticas PASS, 7/7 meses DEV SHA256 OK, 140 días fuente/135 elegibles**, 0 trades simulados, 0 P&L y 0 broker fills. Fuente solo releases preexistentes, directorios privados eliminados. Prerregistro completo antes de outcome: [T20–T25 D1](NQ_T20_T25_D1_ATOMIC_TIMESTAMP_MARKOUT_PREREG_2026_10_12.md), commit `1c7a3a41b619c1f7b6b1a054b087fb95630b05f4`.

## Qué mide realmente

- **Cinco direccionales:** valor inicial `V(E)` de VWAP de barra de 377 PRINTS completa de 10:00–10:15 ET (información causal), contra VWAP del **primer grupo completo Last con timestamp estrictamente posterior a E+300 segundos**, en dirección `side` original del prereg Stage0. `markout_ticks = side*(VWAP_future_group - VWAP_E)` y efecto principal `media_CASE - media_CONTROL`, expresado en **ticks de precio del NQ**, NO USD, NO fills ni P&L.
- **T23:** `rango` futuro high−low de los siguientes 15min, contraste original `media_CONTROL−media_CASE>0`; tampoco es estrategia long/short.
- **Estadística:** 135 sesiones con etiquetas originales, 10.000 bootstrap moving blocks no circulares L5, sensibilidades L3 y L10, IC90 bilateral en ticks del diferencial; p unilateral **exploratorio centrado**, q BH de seis miembros con p=1 solo como sentinela para los tres NO ESTIMABLES. Holm, independencia OOS, retorno de fondeo y Gate1 histórico = N/D. Muestra DEV adaptativa reutilizada: los p/q aquí **NO son inferencia selectiva confirmatoria**.
- Los grupos de timestamps idénticos son indivisibles en decisión y resultado; todas las señales provienen de barras PRINTS; N trades real=0, N independiente desconocido. Los valores 7,5 ticks de fricción presupuestaria en el JSON son un **umbral ilustrativo**, que jamás se deduce de un VWAP no negociable para afirmar ganancias.

## Cuadro integral de seis preguntas

| ID | Pregunta | N casos/controles Stage0 | N markouts caso/control | Media caso (ticks) | Media control (ticks) | Diferencial sentido prereg. (ticks) | IC90 L5 (ticks) | p L5 descriptivo | q BH 6 descriptiva | Resultado D1 |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| **T20** | VWAP extremo contra centrado | 0/100 | **0/88** (12 controles side0) | N/D | +23,411 | N/D | N/D | N/D | N/D (p=1 sentinela) | **NO ESTIMABLE**, 0 casos |
| **T21** | Rechazo de extremo vs aceptación | 38/40 | 38/40 | **−34,816** | +12,632 | **−47,448** | **[−106,832,+10,708]** | 0,904310 | **1,000** | **NO RESPALDADA descriptivamente**, caso pierde dirección relativa |
| **T22** | Qty/print alto con avance | 1/113 | 1/113 | +366,218 | +12,612 | +353,606 | N/D | N/D | N/D (p=1 sentinela) | **NO ESTIMABLE**, n caso 1 |
| **T23** | Desaceleración vs rango 15m | 1/8 | 1/8 (sin operaciones ni signo) | +452,000 rango | +287,375 rango | **−164,625** rango ctrl−caso | N/D | N/D | N/D (p=1 sentinela) | **NO ESTIMABLE**, n caso 1 |
| **T24** | Alternancia VWAP vs continuidad | 39/50 | 39/50 | **+8,676** | **+28,310** | **−19,635** | **[−91,243,+30,139]** | 0,618138 | **1,000** | **NO RESPALDADA descriptivamente**, control superior |
| **T25** | Divergencia 233/4181 vs alineación | 47/59 | 47/59 | **+27,663** | +17,007 | **+10,657** | **[−23,192,+56,899]** | 0,433357 | **1,000** | **INCONCLUSA**, IC incluye efectos negativos |

### Sensibilidad de inferencia al tamaño de bloques

| ID estimable | IC90 L=3 | IC90 L=5 principal | IC90 L=10 | Veredicto |
|---|---|---|---|---|
| T21 | [−109,471,+11,757] | [−106,832,+10,708] | [−109,767,+15,198] | Negativo observado; todos cruzan cero |
| T24 | [−84,227,+29,946] | [−91,243,+30,139] | [−104,417,+32,647] | Negativo observado; todos cruzan cero |
| T25 | [−28,314,+57,641] | [−23,192,+56,899] | [−19,302,+60,210] | Positivo pequeño, sin precisión; todos cruzan cero |

**Precaución de interpretación:** T21 y T24 tienen un diferencial puntual desfavorable, pero **ninguno tiene un IC90 totalmente por debajo de 0**, así que no se ha probado una pérdida sistemática con este test; la decisión racional de cartera es **no priorizar más optimizaciones sobre esas señales** en el mismo DEV. T25 no supera el IC90, q, medibilidad de ejecución, Holm, ni riesgo de fondeo: en D1 queda `INCONCLUSIVE`. El punto +353,606 de T22 depende de UN solo caso y no justifica un filtro post-hoc.

## Cierre formal / próximos gates

1. **D1 predictivo T20–T25 COMPLETADO técnico** 7/7, outcome descriptivo reportado sin cherry-picking; **0/6 hipótesis validadas**, 0 modelos ejecutables.
2. **T20** `UNIDENTIFIABLE`, **T22/T23** `LOW_POWER/NOT_ESTIMABLE`. **T21/T24** `NOT_SUPPORTED_DESCRIPTIVE`, **T25** `INCONCLUSIVE`. No promover T25 por ser mayor media observada, ya que q=1 y CI incluye cero; no retocar umbrales ni seleccionar meses ganadores.
3. **La fase1 ECONÓMICA congelada permanece BLOQUEADA** por ambigüedad intratimestamp en simulación Last/una cuenta, [Action 38286173182 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38286173182). Este D1 **NO calcula** N trades económico, USD neto, PF/DD, incremento router ni CAGR/ROI; todos esos campos N/D, no FAIL monetario ficticio.
4. Si se desea seguir buscando, próximo backlog prioritario bajo [política nueva](NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md): **D0 de lote pequeño de mecanismos NUEVOS** que no sean subfiltros T05, preregistro de caso/control y endpoint antes de leer outcomes, solo datos DEV existentes y sin 5s ni reservas. No repetir variantes T20/T22/T23/T25 mirando el resultado para rescatarlas. Un markout de T25 no habilita D2/fondeo por sí solo.
