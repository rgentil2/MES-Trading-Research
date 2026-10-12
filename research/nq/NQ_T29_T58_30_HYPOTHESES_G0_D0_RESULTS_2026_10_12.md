# NQ T29–T58: RESULTADOS G0/D0 de 30 hipótesis en cinco bloques — SIN FUTUROS

**Ejecución comprobada:** [Action 38300121097 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38300121097) · **10 pruebas sintéticas PASS, 7/7 meses DEV SUCCESS, aggregate SUCCESS**, fuente **140**, elegibles y anclas **135**. [Artefacto agregado 11769168793](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38300121097/artifacts/11769168793), SHA256 ZIP `e1e059b9fd61312673967994901ce2b47fa7a6694b133d362f5906aadd8e5ccd`; verificados `summary.json` y `report.md`, con los 30 miembros, 435 pares de solapamiento y los 7 meses. [Prerregistro escrito antes de clasificar](NQ_T29_T58_30_HYPOTHESES_G0_D0_PREREG_2026_10_12.md), [30 reglas máquina congeladas](NQ_T29_T58_30_HYPOTHESES_G0_D0_FROZEN_2026_10_12.json) commit `3e40f15401249acd5d5e28ba5c0070f88312e87f`.

**CONCLUSIÓN:** De **30 preguntas** analizadas, **27 tienen grupos CASE y CONTROL de al menos 15 sesiones**, y **25 constituyen candidatas suficientemente diferenciadas** aplicando la regla prospectiva Jaccard CASE <0,85 contra miembros ya incluidos de la shortlist, selección determinista round-robin por bloque. Se cumplió el gate solicitado de **≥20 candidatas D0 antes de D1**. No se midió ni una sola ganancia, markout o operación: **NO constituye 25 estrategias rentables**, y los 135 días no proporcionan 25 muestras independientes.

## Cuadro exhaustivo de resultados D0 (CASE/CONTROL no son trades)

| ID | Bloque | N CASE | N CONTROL | Gate D0 | Candidata diversa |
|---|---|---:|---:|---|---|
| T29 | B1 Geometría | 80 | 31 | TESTABLE | **SÍ** |
| T30 | B1 Geometría | 44 | 72 | TESTABLE | **SÍ** |
| T31 | B1 Geometría | 65 | 65 | TESTABLE | **SÍ** |
| T32 | B1 Geometría | 85 | 40 | TESTABLE | NO |
| T33 | B1 Geometría | 72 | 59 | TESTABLE | **SÍ** |
| T34 | B1 Geometría | 46 | 67 | TESTABLE | **SÍ** |
| T35 | B2 Contexto | 45 | 60 | TESTABLE | **SÍ** |
| T36 | B2 Contexto | 66 | 64 | TESTABLE | **SÍ** |
| T37 | B2 Contexto | 68 | 62 | TESTABLE | **SÍ** |
| T38 | B2 Contexto | 61 | 68 | TESTABLE | **SÍ** |
| T39 | B2 Contexto | 62 | 30 | TESTABLE | **SÍ** |
| T40 | B2 Contexto | 31 | 36 | TESTABLE | **SÍ** |
| T41 | B3 Volumen | 15 | 17 | TESTABLE | **SÍ** |
| T42 | B3 Volumen | 45 | 42 | TESTABLE | **SÍ** |
| T43 | B3 Volumen | 60 | 40 | TESTABLE | **SÍ** |
| T44 | B3 Volumen | 79 | 51 | TESTABLE | **SÍ** |
| T45 | B3 Volumen | 79 | 39 | TESTABLE | **SÍ** |
| T46 | B3 Volumen | 48 | 39 | TESTABLE | **SÍ** |
| T47 | B4 Llegadas | 28 | 100 | TESTABLE | **SÍ** |
| T48 | B4 Llegadas | 89 | 14 | LOW_POWER | NO |
| T49 | B4 Llegadas | 101 | 23 | TESTABLE | **SÍ** |
| T50 | B4 Llegadas | 14 | 93 | LOW_POWER | NO |
| T51 | B4 Llegadas | 13 | 84 | LOW_POWER | NO |
| T52 | B4 Llegadas | 67 | 46 | TESTABLE | **SÍ** |
| T53 | B5 Topología | 80 | 32 | TESTABLE | NO |
| T54 | B5 Topología | 50 | 44 | TESTABLE | **SÍ** |
| T55 | B5 Topología | 69 | 55 | TESTABLE | **SÍ** |
| T56 | B5 Topología | 60 | 64 | TESTABLE | **SÍ** |
| T57 | B5 Topología | 53 | 27 | TESTABLE | **SÍ** |
| T58 | B5 Topología | 58 | 58 | TESTABLE | **SÍ** |

**Composición de 25 candidatas diversas:** B1=5, B2=6, B3=6, B4=3, B5=5. T48 89/14, T50 14/93 y T51 13/84 quedan `LOW_POWER`. T32 (85/40) es `TESTABLE` pero tiene Jaccard de casos **0,853933 con T29**; T53 (80/32) también `TESTABLE`, pero solapamiento con T29 de **0,927711**. Se excluyen ambas de la shortlist diversificada, **no de la familia estadística**. Alertas adicionales entre pares T32/T45 Jaccard0,929412, T32/T53 0,875, T45/T53 0,870588 (se respetó el algoritmo greedy por bloques y no se reordenó basándose en futuros). La diversidad de máscaras no garantiza descorrelación de P&L ni mecanismos independientes.

## Gates y limitaciones

- **G0:** QC/integridad SUCCESS, Last privado solamente de siete DEV months existentes, SHA256 y destrucción privada; sin datos nuevos, sin 5s nuevos ni holdouts 2026 reservados. Ancla primera barra 377 prints de 10:00–10:15ET. Comparación CASO/CONTROL E/D ratios congelados; ningún umbral ajustado.
- **D0:** 27 `TESTABLE` sobre conteos por sesión, 25 candidatas sin redundancia alta contra selección previa, 3 `LOW_POWER`. `N_effective` desconocido; (N_{sesiones}=135) para todas. T41 15/17 pasa formalmente D0 pero tiene precisión potencialmente muy limitada, no prioridad de inversión automática.
- **D1/D2/confirmación:** **NO EJECUTADOS para T29–T58** en este documento. N trades, esperanza USD, costos, IC90 de outcome, p, q BH, Holm, PF, DD, `Δrouter`, robustez anual, OOS y CAGR siguen **N/D**. No inferir alfa de balance entre clases.
- **Nuevo orden de investigación autorizado:** se cierra ahora la fase de recolección de candidatos y corresponde **prerregistrar la fase D1 conjunta** de la familia original **k=30**, con endpoints/costos por hipótesis congelados antes de leer futuros, manteniendo los cinco miembros no seleccionados como controles de multiplicidad. D1 exploratoria en DEV reciclado no sustituye independiente Gate1/Holm ni autoriza fondeo.
- No se reabren D0 para ajustar reglas, no se filtran meses ganadores, no se suma P&L standalone y no se retunea T05/T20–T28 para «mejorar» la shortlist.
