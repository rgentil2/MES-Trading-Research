# Cohorte C59–C96: PRERREGISTRO D1 prospectivo para TODOS los 38 IDs

**Registro 12-oct-2026, ANTES de leer ningún futuro D1.** **NO EJECUTAR** a menos que G0/D0 de 7 meses de los 38 esté completado, T59/T60 tenga paridad exacta con D0 original y la nueva cohorte reúna **≥20 hipótesis TESTABLE y diversas (Jaccard CASE <0,85)**. El script D1 debe negar inicio si no se satisfacen esos requisitos y si el JSON de resultados D0 no está congelado en el repositorio. Esta definición existe **antes del cierre de D0 T61–T96**, así que los resultados N y las asociaciones futuras no pueden determinar el endpoint.

**Familia BH FIJA de k=38:** [T59, T60, T61, …, T96] originales, exactamente cada uno una vez, incluidos todos los D0 `LOW_POWER`, `UNIDENTIFIABLE` o redundantes. Si una hipótesis no permite contraste min15 por grupo, asignar sentinel p=1 **solo en el ajuste BH**, dejando p/CI/q de la propia hipótesis N/D. No sumar T29–T58 a esta familia cerrada; no sacar retrospectivamente un nuevo universo favorable.

## Variables de decisión y outcomes físicos, congelados

| IDs | Hipótesis primaria D1 | Ancla causal y side fijados sin futuro | Resultado futuro que D1 observará | Signo ORIGINAL |
|---|---|---|---|---|
| **T59** | ¿La oposición del cuerpo PM/RTH al inicio explica continuación mejor que su alineación? | D0 T59 usa 08:30–09:30 PM y 09:30–09:45 RTH; lado = `sign(RthClose−RthOpen)` (pre-09:45), referencia VWAP del último grupo timestamp completo anterior a 09:45 | `side × [VWAP_{primer grupo completo estrictamente después 09:50 ET} − RthClose]` NQ precio ticks | `mean CASE − mean CONTROL >0` |
| **T60** | ¿Dislocación premarket alineada genera **MAYOR RANGO** 15min vs dislocación opuesta? | D0 T60 etiquetas construidas antes 09:45; referencia reloj 09:45 ET | `max−min` en Last dentro de `(09:45,10:00]` ET, en ticks | `mean CASE − mean CONTROL >0` |
| **T61–T96** | ¿Cada uno de 36 mecanismos causalmente distintos que **CONCUERDA** con impulso E−D precede continuación mejor que si lo contradice? | D0 registrado, side=`sign(VWAP_E−VWAP_D)`, E primera 377 bar completa fin [10:00,10:15) ET, grupos timestamp atómicos | `side × [VWAP_{primer grupo completo estrictamente después E.end+300s} − VWAP_E]` NQ precio ticks | `mean CASE − mean CONTROL >0` para cada uno |

Se respetan las antiguas preguntas T59/T60 de **09:45**, aunque las T61–T96 deciden después, entre 10:00–10:15. Son D1 de una **familia de experimentos por día** con distintos relojes preregistrados, NO una cartera ni 38 trades diarios; una sesión puede aparecer en más de un contraste y la corrección BH trata correlación sin asumir independencia real. Si no se observa el resultado tras la hora exigida, registrar valor N/D y motivo; no excluir sesión ni imputar 0 en la media condicional. Para T59, side0 ⇒ outcome N/D conservando la etiqueta (no recodificarla).

## Inferencia completa y criterio

- Únicamente siete releases DEV NQ Last preexistentes oct2025–abr2026; 140 sesiones fuente/135 `frozen_t05 READY`. Whitelist por mes antes de I/O, SHA256 de archivo, destruir datos privados. Los vectores diarios de 135 etiquetas/outcomes permanecen SOLO dentro del runner temporal, nunca en el artefacto. Salida: agregados únicamente.
- Cada ID reporta `N_case,N_control,N_observables,OTHER,MISSING`, media caso/control, Δ ticks, bootstrap moving block de **135 sesiones diarias ordenadas**, **10.000 resamples no circulares**, L5 principal y L3/L10 sensibilidad, IC90 bilateral y p unilateral centrada EXPLORATORIA. Test si N_outcome_case ≥15 y N_outcome_control ≥15; no usar N trades como independiente.
- q Benjamini–Hochberg por familia completa de **38 miembros** incluso los inestimables y duplicados D0. En DEV adaptativo, cualquier q es **DESCRIPTIVA**, no Holm confirmatorio.
- Etiquetas de cierre: `NOT_ESTIMABLE` si faltan grupos o >=15 observables; `NOT_SUPPORTED_DESCRIPTIVE` si Δ≤0 (sin invertir signo), `INCONCLUSIVE` si Δ>0 pero IC90 inferior≤0 o BH q>0,10, `PREDICTIVE_SHORTLIST_ONLY` solo si Δ>0, IC90 inferior>0 y **q_BH38≤0,10**. Cualquier notable individuales con q>0,10 NO pasa filtro del embudo. Las variables de magnitud/rango pasan como `CONTEXT_ONLY`, no estrategias monetarias.
- Incluso un `PREDICTIVE_SHORTLIST_ONLY` **NO pasa automáticamente a D2**: no se simulan fills Last, órdenes, slippage, comisiones, PF, DD, DeltaRouter ni ROI. Requiere después un protocolo económico/ejecutable distinto, cuando haya **al menos dos mecanismos no redundantes** para la bandeja común de D2. Ninguna observación de markout VWAP se transforma en rentabilidad neta de trading.
- No abrir OOS, no data nueva ni 5s para señales, no retocar voto/side, no inferir agresor ni escoger meses favorables. Las 36 características y las etiquetas T59/T60 siguen sus JSON/prerregistros originales sin cambios; el gate de amplitud conserva 20 distintos y el universo BH38.

**Referencia:** [D0 prereg 36](NQ_T61_T96_SIX_BLOCK_D0_PREREG_2026_10_12.md), [D0 máquina](NQ_T61_T96_SIX_BLOCK_D0_FROZEN_2026_10_12.json), [T59/T60 prereg](NQ_T59_T60_LEGACY_MECHANISM_ADAPTATION_D0_PREREG_2026_10_12.md), [política embudo](NQ_COHORT_FUNNEL_POLICY_2026_10_12.md).
