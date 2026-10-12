# NQ T26–T28 — D1 observacional preregistrado (solo DEV; no fills/P&L)

**2026-10-12 America/Bogota. Congelado ANTES de leer cualquier outcome futuro T26–T28.** Política [NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md](NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md). D0 fue procesado sin retornos: [informe 18/36, 6/65, 3/0](NQ_T26_T28_G0_D0_RESULTS_2026_10_12.md) y [Action 38297611186 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38297611186). Estos conteos son conocimiento PREVIO a este prereg, **ningún retorno futuro T26–T28 ha sido leído**. No modificar condiciones D0 ni elegir retrospectivamente versiones por resultados.

## Muestra G0 y seguridad

- **Únicamente siete archivos NQ Last DEV YA existentes**: octubre2025–abril2026 en release privado existente, SHA256 checks, fuente 140/READY135/anclas135 y **3** IDs de familia completos: T26, T27, T28. No adquirir historia nueva, Market Replay, Bid/Ask adicionales, ni 5s para señales nuevas; holdouts T mayo–septiembre 2026 y H 2025–26 bloqueados. El benchmark T05 legacy solo define 135 elegibles, no da signals D1.
- Una decisión por día al fin de la primera barra completa de 377 prints entre 10:00–10:15 ET, grupos con timestamp igual indivisibles. D y E determinadas sin mirar futuro. Comparar exclusivamente CASE/CONTROL congelados [G0/D0](NQ_T26_T28_G0_D0_NEW_MECHANISMS_PREREG_2026_10_12.md), no convertir OTHER en control ni filtrar malos resultados/meses.
- Respuesta de cada sesión con todos los tres miembros, incluyendo OTHER/NOT_EVALUABLE y cero operaciones, permanece **PRIVADA**; publicar solo agregados mensuales de conteos y estadísticos por miembro, nunca Last, fechas, timestamps, markouts individuales o ticks licenciados. No se simula **ningún** trade, stop, fee, router, fill Last, P&L, PF, DD, CAGR ni riesgo fondeo.

## Endpoints congelados

| ID | Hipótesis primaria D1 | Outcome medido DESPUÉS del ancla, no usado como señal | Signo previsto |
|---|---|---|---|
| **T26_PRICE_PATH_CHOP** | La fragmentación creciente del recorrido implica **mayor rango** posterior que estable | `range15m = max(price_ticks)−min(price_ticks)` de todos Last con `t > E.end` y `t<=E.end+900s`; fuente debe extenderse a `>=end+900s` y tener observaciones; bloque incompleto => FAIL CLOSED (no excluir sesión) | `mean(range_CASE)−mean(range_CONTROL)>0` ticks |
| **T27_PRINT_SIZE_PRICE_PREMIUM** | La prima positiva de volumen alineada con la migración VWAP anticipa **continuación direccional** superior a ausencia de prima | `signed_markout = side*(VWAP_{first_complete_timestamp_group_STRICTLY_AFTER(E.end+300s)} − VWAP_E)` en ticks, side D0 ±1 de SAME time; grupo futuro completo quantity-weighted, nunca last arbitrario | `mean(markout_CASE)−mean(markout_CONTROL)>0` ticks |
| **T28_ARRIVAL_BURSTINESS** | Las llegadas irregulares inducen mayor rango próximo que llegadas uniformes | Igual `range15m` de T26, con CASE/CNTRL T28 propios (control D0 N=0), no inventar contrafactual | `mean(range_CASE)−mean(range_CONTROL)>0` si identificable, de lo contrario N/D |

**T26/T28 son magnitud, NO entradas long/short**; ni siquiera una magnitud futura superior implica rentabilidad. **T27 usa VWAP de decisión y outcome no negociables**, NO inferir fill, costo descontable, USD netos ni rentabilidad. La cuenta económica T05/T20–T25 sigue bloqueada por ambigüedad Last.

## Inferencia de efecto y decisión

- Reportar N cases/controls D0 exactos 18/36, 6/65 y 3/0, y N markouts observables/side0. **Preservar los 135 vectores diarios privados** en orden cronológico con registros OTHER/NOT_EVALUABLE y sin resultado para esos grupos; **no atribuirles retorno 0** en medias condicionales. N efectivo independiente N/D, N_trades=0.
- Contraste primario `Δmean = mean(CASE)−mean(CONTROL)`, en ticks; T27 firmado y T26/T28 rango absoluto; intervalo **IC90 bilateral por bootstrap moving block no circular**, 10.000 resamples de **135 sesiones**, bloque principal L5, sensibilidades L3/L10. Semilla `random.Random(20261012+100*L+int(ID[1:3]))`. IC90 percentil; p unilateral exploratorio centrado `(1 + count(boot_delta−observed_delta>=observed_delta))/(B+1)`.
- **N insuficiente**: si <15 observaciones con outcome en CASO o CONTROL o <90% bootstrap resamples válidas, **CI90/p=N/D** (corte de precisión D1 usado para el screen T20–T25, no Gate1 y no permiso para modificar T27/T28); reportar media descriptiva de grupo disponible pero ningún p significativo.
- **BH familia completa k=3** para p unilateral L5. p=1 **solo sentinela de denominador BH** en T27/T28 no estimables, manteniendo sus p/q inferenciales **N/D**. Toda p/q en DEV reutilizada adaptativamente es **DESCRIPTIVA NO confirmatoria**; Holm, Gate1 >150 independientes /3de5, OOS y fondeo no se evalúan.
- D1 `NOT_ESTIMABLE` si grupo no identificable/n<15; `NOT_SUPPORTED_DESCRIPTIVE` si Δ<=0 con datos; `INCONCLUSIVE` si Δ>0 pero IC90 cruza0; `PROMISING_PREDICTIVE_IN_SAMPLE_ONLY` si Δ>0 e IC90 L5 entero >0, **pero sin habilitar D2 económico automáticamente, ya que T26/T28 no tienen dirección**. No mejorar umbrales CHOP/price premium/CV2 tras ver resultados. **Cerrará** con 7/7 meses 140/135, hashes, tests de grupo atómico y artefacto seguro, + N/CI/p/q y no-estrategia en maestro/log/scorecard.
