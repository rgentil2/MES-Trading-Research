# T97–T132 — D1 de la familia NUEVA de 36 hipótesis: PRERREGISTRO ANTES DE CONOCER D0/OOS

**12-oct-2026; creado ANTES del resultado completo de D0**. [D0 prereg 36](NQ_T97_T132_SIX_BLOCKS_D0_PREREG_2026_10_12.json), [descripción de seis bloques](NQ_T97_T132_SIX_BLOCKS_D0_PREREG_2026_10_12.md). Este protocolo NO autoriza saltar D0: D1 solo si mínimo 20 TESTABLE y diversas por Jaccard<0,85 **y** 7/7 meses con fuente 140/135 completa, todas las reglas congeladas, y reporte D0 en GitHub antes del primer futuro. El D0 se ejecuta primero como bloque 36, sin elegir individuales. Si falla, D1 BLOQUEADA y se trabaja otra familia distinta.

**Denominador multiplicidad INMUTABLE: k=36 T97,T98…T132 TODOS**, incluidos casi duplicados, LOW_POWER y faltantes de 4181. No reoptimizar longitudes 233,377,4181, umbrales, CASE/CONTROL, sentidos o horarios tras ver resultados. T59–T96 y T29–T58 son familias D1 previas cerradas y NO se reexaminan ni agregan a esta BH36.

## Endpoint D1 primario y signo

- Para **cada ID T97..T132**, etiquetas CASE/CTRL/OTHER/NOT_EVALUABLE se calculan SOLO con los mismos atributos causales a E377 (primer bar completo terminando 10:00–10:15 ET). Side para outcome=`sign(VWAP_q(E) - VWAP_q(D))`; registro de E completo por grupos atómicos. Etiquetas REGIMEN son distintas porque comparan expansión frente a contracción, pero **el outcome es el mismo markout firmado por el impulso común** (comparación de continuación bajo un régimen vs otro).
- **Outcome PRIMARIO exactamente UNO por miembro**: `Y=side × (VWAP qty del PRIMER grupo completo estrictamente después E.end+300 segundos − VWAP_q(E))`, unidades **ticks de PRECIO NQ**, sin inventar Fill, no intrabar highs seleccionados, no P&L. CASE y CTRL comparan el **mismo endpoint**. Hipótesis alterna unilateral fijada: `mean(Y CASE) − mean(Y CTRL) >0`. No cambiar a reversión si lo observado da negativo.
- Side E−D igual cero, no hay dirección observada; outcome N/D tanto en CASE como CONTROL y debe registrarse con frecuencia de falta (D0 clasifica las hipótesis REGIMEN aun cuando side0, pero D1 debe marcar missing Y sin excluir silenciosamente días).
- Cobertura futura: grupo completo estrictamente después umbral; si no hay, falla QC de horizonte para esa sesión. Resto de sesiones se conservan como `OTHER`/`NO_EVAL`, no se cuenta ni en N operaciones ni en retornos.

## Inferencia y decisión

- Únicamente siete Last DEV SHA256 existentes, 140 sesiones fuente, 135 READY. `frozen_t05`, mismas 36 máscaras CASE/CTRL D0 por mes y totales antes de inferir. Guardar 135 vectores diarios SOLOS en runner privado, borrarlos incluso después de error. Artefacto final SAFE solo agregados. NO 5s nuevas, NO licencias nuevas ni OOS.
- Contraste por **sesiones** (una por día y señal), bootstrap moving block **no circular** 10.000 replicaciones por miembro; **L5 primario**, L3/L10 sensibilidad. IC90 bilateral, p unilateral centrada EXPLORATORIA. Miembros sin al menos **15 outcomes observados por clase**: p N/D, IC N/D, q de ese miembro N/D, **sentinel p=1 solo en ajuste BH de los 36**.
- q Benjamini–Hochberg por las **36 hipótesis registradas**, no solo los testables/efectos positivos. `D1_PASS_EXPLORATORY` solo si signo Δ>0, límite inferior IC90 L5 >0 y q BH36 ≤0,10; `INCONCLUSIVE` Δ>0 pero falla IC o BH; `NOT_SUPPORTED` Δ≤0; `NOT_ESTIMABLE` missing o falta potencia. p/q de DEV repetida son DESCRIPTIVAS, no prueba confirmatoria ni Holm/Gate1.
- Reporte por CADA ID: bloque, pregunta, N CASE/CTRL D0, N observed, Δ ticks, IC90 L3/L5/L10, p, q BH36, Holm N/D, PF/DD/P&L/ROI/DeltaRouter=N/D, categoría y motivo. Documento maestro, scorecard, log, ledger y tablero sincronizados al cierre.

## Significado para D2

Incluso si salen varios D1 PASS, son **markouts direccionales de precio**, NO trades ejecutables ni carteras rentables. Pasar a D2 solo cuando se haya especificado/validado un mecanismo de orden causal verificable con Last disponible, gastos, fricción bid/ask, prioridad de fills, costes (base/1,5x/+10RT), pérdida máxima, PF y mejora monetaria conjunta de al menos dos mecanismos **no redundantes**, con una sola cuenta. Sin esos elementos, `D2 BLOCKED_EXECUTION`, sin abrir holdouts. No concluir que mayor rango o VWAP se monetiza.

Este protocolo no utiliza ni una observación futura al registrarse. **Si D0 no alcanza 20 distintas, NO ejecutar D1.**
