# NQ T133–T152 — D0 FINAL cuatro bloques de estrategias completas

**12-oct-2026.** [Action FINAL corregida 38324292967 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38324292967) · [artifact safe 11779419992](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38324292967/artifacts/11779419992), SHA256 `aad65e794f5dee30fa27b543fe692ee2409535438ca11d187f4ec891be8d43c3`. Las 20 estrategias fueron [prerregistradas ANTES de D0](NQ_T133_T152_EXECUTABLE_D0_PREREG_2026_10_12.md) y [congeladas en JSON](NQ_T133_T152_EXECUTABLE_D0_PREREG_2026_10_12.json), commit `aea7a3dda1cb57be65c5f4c9f47b06e72848946e`. **7/7 DEV existentes, 140 sesiones fuente, 135 READY. No se abrieron OOS ni se adquirió data nueva.**

**Embudo:** 20 estrategias definidas con entrada, stop, TP y timeout → **15 D0 TESTABLE** (CASE y CONTROL≥15) → **15 no redundantes** (Jaccard CASE<0,85). D1 exige **20 TESTABLE distintas**, así que **D1 BLOQUEADO**. Cinco LOW_POWER: **T134/T138/T139/T143/T144**. Ninguna casi duplicada entre las 15. Sin retorno económico observado ni prueba de fill.

| Hipótesis | Familia | Pregunta preregistrada | CASE | CONTROL | OTHER | NO EVAL | CASE oct–dic/53 | CASE ene–abr/82 | D0 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| T133 | A_BREAKOUT_RETEST | ¿La ruptura del extremo premercado en dirección del impulso permite una operación de continuación? | 52 | 77 | 6 | 0 | 26 | 26 | TESTABLE |
| T134 | A_BREAKOUT_RETEST | ¿La ruptura del extremo de los primeros 30 minutos RTH permite continuar hacia el mismo lado? | 14 | 121 | 0 | 0 | 6 | 8 | LOW_POWER |
| T135 | A_BREAKOUT_RETEST | ¿Superar el extremo conjunto de las dos barras 377 anteriores confirma ruptura aprovechable? | 56 | 79 | 0 | 0 | 18 | 38 | TESTABLE |
| T136 | A_BREAKOUT_RETEST | ¿Superar el extremo de tres barras 233 completas recientes favorece ruptura? | 36 | 99 | 0 | 0 | 15 | 21 | TESTABLE |
| T137 | A_BREAKOUT_RETEST | ¿Romper el extremo de la última barra 4181 completa puede activar continuidad? | 38 | 96 | 1 | 0 | 12 | 26 | TESTABLE |
| T138 | B_PULLBACK_CONTINUATION | ¿El retroceso en la última 233 al VWAP premkt seguido de recuperación permite continuación? | 5 | 130 | 0 | 0 | 0 | 5 | LOW_POWER |
| T139 | B_PULLBACK_CONTINUATION | ¿El retroceso de 233 al VWAP primeros 30min RTH seguido de recuperación confirma entrada? | 3 | 132 | 0 | 0 | 1 | 2 | LOW_POWER |
| T140 | B_PULLBACK_CONTINUATION | ¿Tocar el VWAP de D377 y recuperarlo durante la 233 confirma continuación? | 61 | 70 | 4 | 0 | 24 | 37 | TESTABLE |
| T141 | B_PULLBACK_CONTINUATION | ¿Tocar VWAP de las tres 233 previas y volver al lado impulsivo permite continuación? | 73 | 59 | 3 | 0 | 26 | 47 | TESTABLE |
| T142 | B_PULLBACK_CONTINUATION | ¿Retroceder al VWAP 4181 y recuperarlo en 233 favorece continuación? | 17 | 116 | 2 | 0 | 5 | 12 | TESTABLE |
| T143 | C_FALSE_BREAK_REVERSAL | ¿Barrida de máximo/mínimo premkt en E377 y cierre de regreso al rango permite reversión? | 9 | 126 | 0 | 0 | 2 | 7 | LOW_POWER |
| T144 | C_FALSE_BREAK_REVERSAL | ¿Barrida del rango RTH inicial en E377 y cierre de regreso al rango permite reversión? | 5 | 130 | 0 | 0 | 2 | 3 | LOW_POWER |
| T145 | C_FALSE_BREAK_REVERSAL | ¿Barrida de D377 previa en E377 y cierre de vuelta al rango anticipa reversión? | 51 | 69 | 15 | 0 | 22 | 29 | TESTABLE |
| T146 | C_FALSE_BREAK_REVERSAL | ¿Barrida del extremo de tres 233 completas y rechazo al rango permite reversión? | 32 | 100 | 3 | 0 | 15 | 17 | TESTABLE |
| T147 | C_FALSE_BREAK_REVERSAL | ¿Barrida del rango 4181 completo y rechazo permite reversión? | 21 | 113 | 1 | 0 | 9 | 12 | TESTABLE |
| T148 | D_REGIME_RISK_ROUTER | ¿Alinear impulso E377 con pendiente entre dos 233 es condición para activar una continuación? | 102 | 20 | 13 | 0 | 40 | 62 | TESTABLE |
| T149 | D_REGIME_RISK_ROUTER | ¿Alinear E377 con la pendiente de VWAP de dos barras 4181 evita trades de contratrend? | 58 | 64 | 11 | 2 | 20 | 38 | TESTABLE |
| T150 | D_REGIME_RISK_ROUTER | ¿Alinear E377 con cuerpo 09:30–10:00 RTH permite continuar? | 72 | 53 | 10 | 0 | 28 | 44 | TESTABLE |
| T151 | D_REGIME_RISK_ROUTER | ¿Una 233 más rápida que su predecesora permite operar impulso E377? | 93 | 28 | 14 | 0 | 38 | 55 | TESTABLE |
| T152 | D_REGIME_RISK_ROUTER | ¿La contracción del rango E377 frente a D377 ofrece una entrada de expansión posterior? | 29 | 96 | 10 | 0 | 15 | 14 | TESTABLE |

## Auditoría de versiones y correcciones puramente técnicas

- [Action 38323851560 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38323851560): un bar entero de ≥233 Last perteneciente a **un único timestamp** era erróneamente tratado como inválido por el parser de contexto; se agregó manejo atómico sin dividir ni fabricar orden, más tests.
- [Action 38323990208 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38323990208): agregado **preliminar 13 TESTABLE**; revisión reveló discrepancia de claves de los extremos 233/4181 **T146/T147** contra nombres preregistrados, causando clasificación falsa de 135 NO EVAL en ambas. El código ahora resuelve esas MISMAS referencias estructurales y falla si una clave registrada no existe. Ninguna condición causal, stop, target, timeout, selección temporal o requisito estadístico cambió.
- [**Action 38324292967 COMPLETED SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38324292967): resultado ÚNICO FINAL, **T146 CASE32/CTRL100** y **T147 CASE21/CTRL113**, ambos TESTABLE. **15/20 TESTABLE diversas**, no 13.

## Corte cronológico predefinido

Octubre–diciembre 2025: **53** READY; enero–abril 2026: **82** READY. La tabla separa activaciones causales por período, no beneficios. T138 no activa en oct–dic y T139 aparece solo una vez; advertencia de baja frecuencia. Ambas ventanas fueron investigadas antes y **NO son OOS independiente**. Detalle mensual de todas las hipótesis en el artifact seguro `summary.json`.

## Decisión de etapa

**D0: falta un mínimo de 5 estrategias nuevas, distintas y con casos/controles suficientes** para abrir un nuevo D1; no cambiar parámetros de T134/T138/T139/T143/T144 ni rescatar mejores tras mirar resultados. Las reglas T133–T152 permanecen congeladas. Si se añade otro bloque prospectivo con IDs nuevos, solo podrá analizarse D1 tras registrar TODA la familia original y costos/supuesto de ejecución ANTES de observar retornos.

**N_trades, ejecución real, P&L neto, costes efectivamente pagados, PF, DD, IC90, p, q BH, Holm, DeltaRouter y ROI=N/D:** D0 no observó retornos ni verificó broker fills. Una referencia de VWAP Last NO equivale a orden ejecutada ni a ventaja monetaria. D2 permanece vacío, holdouts sellados.
