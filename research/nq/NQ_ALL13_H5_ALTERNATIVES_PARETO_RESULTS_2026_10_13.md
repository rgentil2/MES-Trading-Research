# Rama H de la búsqueda ALL13 — cinco alternativas históricas comparables

**Verificado 2026-10-13:** [GitHub Action 38435339403 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38435339403), pruebas sintéticas PASS, [artifact seguro 11832109790](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38435339403/artifacts/11832109790). **Sin consultar nuevos datos de mercado.** Se reutilizan únicamente reportes agregados congelados NQ minuto **2020–2024**, expresados como un único **proxy de 1 MNQ**, NO ejecuciones verificadas. No abrir 2025/26 H ni los meses sellados T.

| H | N operaciones | Beneficio neto MNQ proxy USD | Drawdown CERRADO USD | Neto/DD | USD/operación | PF* | Pareto neto/DD |
|---|---:|---:|---:|---:|---:|---:|---|
| H09 | 173 | +2.074,26 | 763,56 | 2,7166 | 11,99 | N/D | Dominada por H77 |
| H56 | 100 | +749,50 | 365,52 | 2,0505 | 7,50 | N/D | No dominada por menor DD |
| H69 | 262 | +2.704,44 | 890,64 | 3,0365 | 10,32 | 1,335 | No dominada por mayor beneficio |
| H74 | 132 | +1.657,84 | 444,10 | 3,7330 | 12,56 | 1,438 | No dominada |
| **H77** | **140** | **+2.385,30** | **584,54** | **4,0806** | **17,04** | **1,632** | No dominada; mayor ratio histórico |

*PF de H09 y H56 no está disponible en este universo de **comparadores MNQ**: no trasladar el PF de su backtest alternativo 1NQ y otro bracket. Los ratios son descriptivos del histórico conocido, NO validación fuera de muestra ni ajuste por exposición flotante. Los cinco son **ALTERNATIVAS mutuamente excluyentes** de una política H de una sola cuenta, porque H69/H74/H77 ya reutilizan H09/H56. No sumar sus beneficios. H77 N140 (<150 exigido para H por el protocolo de búsqueda) y 75,2% de su neto concentrado en 2022; H69 N262 pero q previo ~0,115 y exposición anual nominal baja. Ninguno se promueve.

**Decisión H actual:** conservar la frontera de Pareto `[H56,H69,H74,H77]`; si el objetivo descriptivo es máximo NETO/DD cerrado, H77 lidera, pero queda **REVIEW_ONLY_NOT_CONFIRMED**. No existe una respuesta defendible de “mejor combinación de las 13” hasta que la rama T pruebe los 255 subconjuntos en su calendario y se establezca una ventana H/T compatible; las fechas selladas permanecen cerradas.

**Código:** [nq_all13_h5_comparable_options.py](nq_all13_h5_comparable_options.py). **Prerregistro de 13:** [JSON](NQ_ALL13_PORTFOLIO_SEARCH_PREREG_2026_10_13.json).
