# Resultado verificable del espacio de las 13 hipótesis

**Fuente:** [Action GitHub 38434756094 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38434756094); validación de [código enumerador](nq_all13_subset_search.py) y [prerregistro previo](NQ_ALL13_PORTFOLIO_SEARCH_PREREG_2026_10_13.json), sin datos de mercado, sin abrir ningún holdout.

| Categoría exhaustiva | Subconjuntos brutos | Qué puede medirse honestamente |
|---|---:|---|
| Mezclas de al menos una H y una T | 7.905 | **No estimable:** H 2020–24 1 minuto y T oct2025–abr2026 Last no comparten misma historia; no sumar rentabilidades/DD. |
| Solo H (5 IDs) | 31 | Cinco alternativas genuinas de routing; otras 26 duplican padres H09/H56 y routers H69/H74/H77 |
| Solo T (8 IDs) | 255 | Igual calendario y fuente Last DEV; **exige motor cronológico de una cuenta con paridad de las ocho padres**, no ocho equities sumadas |
| **Total 13** | **8.191** | Ninguna cifra de “mejor cartera global 13” confirmada; el espacio queda cubierto estructuralmente |

**5 decisiones H verificadas** en [Action 38435339403 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38435339403); [tabla H y frontera Pareto](NQ_ALL13_H5_ALTERNATIVES_PARETO_RESULTS_2026_10_13.md), con H77 ratio neto/DD cerrado4,0806 como mejor histórico descriptivo, no estrategia confirmada.

**T255:** [un solo motor de ocho reglas congeladas](../../local_nq_tick_2025_2026/nq_all13_t8_shared_portfolios.py), sin escoger T05+T224 en particular. Se exige contabilidad de N y PnL parental original para ocho antes de ordenar. Los costos originales son heterogéneos; +$10RT común y 1,5x quedan como análisis de estrés descriptivo, DD diario cerrado NO es DD flotante. Auditoría de sesgo de búsqueda sobre 255 alternativas necesaria incluso si sale ganadora. Si cualquier subconjunto no es estimable, informar N/D.

**Estado fuente:** H/T OOS sellados, no descarga ni compra de nuevas series, no broker fill verificado, D1/D2 formal no autorizados, cuenta 50K como objetivo futuro.
