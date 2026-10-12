# NQ T59–T60 — G0/D0 COMPLETADO de dos mecanismos nuevos inspirados en H77/H69

**2026-10-12.** [GitHub Actions 38306833847 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306833847): ocho pruebas sintéticas SUCCESS, siete meses de [NQ Last DEV ya almacenados y SHA256 verificados], siete jobs mes SUCCESS y aggregate SUCCESS, **140 sesiones fuente / 135 elegibles**, eliminación de raw privado `always()`. [Artefacto agregado 11773042751](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306833847/artifacts/11773042751), SHA256 `75c467dd21291e4f0bfe2dd63ac9eedc27d6ed3c78557533d2ffb367c8ea60c4`. [Prerregistro de dos preguntas, congelado antes de leer D0](NQ_T59_T60_LEGACY_MECHANISM_ADAPTATION_D0_PREREG_2026_10_12.md), commit `324cd688419f488c493d0013ceea21d3234c22ec`, [código de features y clasificador](../../local_nq_tick_2025_2026/nq_t59_t60_d0_premarket.py), [workflow](../../.github/workflows/nq-t59-t60-d0-premarket-dev.yml).

**IMPORTANTE: NO SON H77/H69 ORIGINALES.** [Auditoría de portabilidad](NQ_LEGACY_H77_H69_H74_T26_PORTABILITY_GATE_2026_10_12.md) demuestra que Last DEV existente de 08:00–12:00 carece de CLOSE RTH previo 16:00 ET y de ATR14/rangos RTH completos previos 20+. Las T59/T60 son hipótesis **nuevas** con nuevos identificadores, normalización/rango del premarket actual, no incluyen retornos, stops, P&L ni el router histórico.

## Tabla D0 real — UNA sesión por miembro, NO trades

| ID | Pregunta causal ex ante | N CASE | N CONTROL | G0/D0 | N trades / PF/DD/NETO | IC90/p/q/Holm | ¿Cumple pase D1? |
|---|---|---:|---:|---|---|---|---|---|
| **T59 — PM_BODY_OPPOSITION** | ¿Contraste reversión RTH 09:30–09:45 frente continuación del cuerpo PM 08:30–09:30, ambos >= mínimos relativos, aporta valor? | **45** | **42** | **TESTABLE** con N>=15 por clase, solo VIABILIDAD | N/D | N/D | **NO TODAVÍA**; solo 1 nueva candidata |
| **T60 — PM_VWAP_OPEN_DISLOCATION** | ¿Dislocación de apertura desde PM VWAP a favor vs en contra del cuerpo PM? | **71** | **6** | **LOW_POWER** por 6 CONTROLES | N/D | N/D | **NO**; sin ajustar umbral |

**Ambos** tienen `N_other`/`N_not_evaluable` reportados en [artifact D0](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306833847/artifacts/11773042751) y no deben tratarse como CONTROL. `T59=TESTABLE` significa únicamente grupos identificables en 135 sesiones, NO edge, q, potencia de P&L o una nueva estrategia de 45 trades. Un día puede clasificar como CASE/CONTROL en ambos miembros, no hay independencia garantizada. Los 135 días de DEV se habían utilizado en lotes T anteriores y la selección futura es adaptativa.

**Calidad de las ejecuciones:** primer [Action 38306662238 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306662238) con tests de reloj no-ISO; [Action 38306828923 FAILURE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306828923) disparado después de la corrección de código y antes de completar test, sin outcomes; [Action FINAL 38306833847 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38306833847), sin cambio de reglas CASE/CONTROL desde prerregistro. No se inspeccionó información futura en ninguno de los tres.

## Gate siguiente

- **NO correr D1** de T59/T60 por el nuevo requisito [amplitud de bloque >=20 candidatas diversas en D0](NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md). La cohorte T29–T58 de 25 diversas ya fue sometida a D1 **y se cerró**; no permite agregar retroactivamente T59 a su BH familiar ni afirmarla validada. T59 queda **en inventario** para la próxima nueva cohorte, T60 LOW_POWER sin tuning.
- Si una futura cohorte suma >=20 candidatas distintas, preregistrar desde cero reloj 09:45, endpoint direccional, costos y comparación CASE/CONTROL, bootstrap y BH de todo el universo antes del primer retorno. T59 no puede ser convertido retrospectivamente en H56/H77 exitosas o combinado por hindsight en router H69.
- No nuevas fuentes, 5s ni holdouts, no funding; H77/H69/H74 siguen bloqueados como reproducciones exactas y T26 D1 ya resultó negativo para signo positivo [informe](NQ_T26_T28_D1_OBSERVATIONAL_RESULTS_2026_10_12.md).
