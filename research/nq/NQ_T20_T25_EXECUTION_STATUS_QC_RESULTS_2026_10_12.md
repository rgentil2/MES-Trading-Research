# NQ T20–T25 — cierre del QC de estados de ejecución Last (sin P&L)

**Resultado verificado:** [Action 38293741380 COMPLETED/SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38293741380), commit `8c3e6fbcc8acb9f643b168c5078e7ab33eb14d2c`. **7 pruebas sintéticas PASS, 7/7 meses DEV, SHA256 originales OK, fuente 140, elegibles 135**. [Artifact agregado seguro 11766819383](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38293741380/artifacts/11766819383), digest **sha256:93ae35ddc6832639dd55f56f80188b4942558ce52b836895123475fdb2fec027** (1.974 bytes). Se verificaron jobs `synthetic` y `qc` SUCCESS y línea de resumen `NQ_T20_T25_QC_FINAL` en logs. El reporte NO constituye backtest ni broker fills.

## Contexto y corrección íntegra del problema previo

[Action anterior 38287092666 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38287092666): aunque había procesado 140/135, el agregador confundió `NOT_EVALUABLE` por hipótesis con falta de la ancla 377 del día, y abortó. **La ancla existía en 135/135 días**; `NOT_EVALUABLE` es una etiqueta válida de alguna pregunta ante insuficiencia de contexto causal. Se cambió SOLAMENTE la guarda: suma de `CASE/CONTROL/OTHER/NOT_EVALUABLE` = sesiones elegibles, preservando conteos originales, sin tocar señales, umbrales, SL/TP, costos, rellenos Last, fuentes ni retornos. Código `5638b4a`, tests `8c3e6fb`, [workflow](../../.github/workflows/nq-t20-t25-fill-status-only-qc.yml).

## Conteos técnicos reconciliados

| Hipótesis | N casos/control (etapa 0 idéntica) | Casos con estado ambiguo de ejecución Last | Controles ambiguos de Last | Conclusión |
|---|---:|---:|---:|---|
| T20 `BAR_VALUE_SKEW` | 0/100 | 0 (no hay casos) | 1 | No identificable como efecto caso/control |
| T21 `EXTREME_REJECTION` | 38/40 | **0** | **1** | Señal caso medible técnicamente standalone; control requiere manejo de ambigüedad |
| T22 `QTY_WITH_PROGRESS` | 1/113 | **0** | **1** | Caso n=1, baja potencia |
| T23 `TEMPO_DECELERATION` | 1/8 | 0 (magnitud NO ejecución) | 0 (magnitud NO ejecución) | No prueba direccional y n muy bajo |
| T24 `SIGN_ALTERNATION` | 39/50 | **0** | **1** | Caso standalone sin bloqueo; control ambiguo |
| T25 `CROSS_SCALE_DIVERGENCE` | 47/59 | **0** | **1** | Caso standalone sin bloqueo; control ambiguo |

Los conteos de estados ambiguos **son por miembro/grupo, NO días distintos**; no sumar los cinco controles ambiguos como cinco sesiones únicas. El log resumido confirma esos conteos, pero no muestra en abierto la distribución exacta de `NO_ENTRY`, `SIDE0` y `SYNTHETIC_FILL_MODEL_ONLY` de cada grupo: se conserva esa información en el artifact seguro. No inferir otros conteos sin inspeccionarlo.

## Decisión y transición al nuevo método

- `G0/QC_OK` **solo para la clasificación standalone de estados**; elegibilidad y grupo caso/control reconciliados. `D0`: T21/T24/T25 `TESTABLE` con N casos 38/39/47 y controles 40/50/59; **baja precisión esperable**. T20 `UNIDENTIFIABLE`; T22/T23 `LOW_POWER`. Estas etiquetas son diagnóstico descriptivo, **no PASS económico/estadístico**; no se alteran preregistros congelados.
- **La etapa económica T20–T25 [Action 38286173182 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38286173182) permanece BLOQUEADA**, incluso si el QC standalone ve 0 ambigüedades entre casos. No se reconcilió el router completo T05+CASO, no se resolvió ejecución Last ni se publicó agregado monetario de 7 meses.
- Todos `N_trades/P&L/IC90/p/q/PF/DD/Δrouter/Holm/años/ROI` **siguen N/D** para la fase económica T20–T25. Los controles ambiguos no pueden excluirse selectivamente para subir expectativa. Ningún alfa validado, no fondeo ni holdout.
- Siguiente paso bajo [política de descubrimiento G0→D0→D1→D2](NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md): si se realiza un contraste predictivo de horizonte prefijado con una referencia **invariante por grupo de timestamps**, prerregistrar por separado, incluir toda familia T20–T25 y dejar claro que es **markout observacional, NO precio negociable ni P&L de fills**. Sin cambiar señal caso/control ni sustituir resultados previos.
