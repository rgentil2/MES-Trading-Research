# NQ T133–T168 — sensibilidad económica quitando q-BH e IC90, manteniendo TODAS las demás puertas

**Fecha local: 12 de octubre de 2026. Auditoría completada en [GitHub Action 38333406107](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38333406107) (SUCCESS)**, [artifact agregado de 36 filas 11783168846](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38333406107/artifacts/11783168846), SHA256 `1edeeaefb4b300a1676bc0e8416ece481316c34cce4ba2f66d58c195b63e3236`. **Lectura exclusivamente de [summary.json SAFE original](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38326216082/artifacts/11781138134)** de D1 económica de 36 hipótesis, no ticks, no nuevas descargas, no reejecución del trading ni datos por sesión. [Código reproducible](../../tools/nq_t133_t168_economic_no_q_ci_audit.py); informe por los 36 miembros y todos los filtros en el artifact adjunto.

## Petición de investigación: quitar únicamente el componente estadístico

Para el ejercicio **exploratorio post-hoc** se retiran únicamente `q_BH36≤0,10` e `IC90 L5 límite inferior>0`. No se modifican estrategias, datos, precio de entrada proxy, fricción, tasas, TP, stop, riesgo, timeframe, selección, ni límites económicos históricos. Se mantienen DIEZ condiciones: (1) N proxy trades≥15, (2) neto modelo>0, (3) expectativa neta/trade>0, (4) PF neto≥1,25, (5) neto bajo estrés1,5×>0, (6) neto con +US$10 RT>0, (7) Q4 2025>0, (8) enero–abril 2026>0, (9) drawdown proxy≤US$1.500, (10) concentración del mes favorable máximo inferior a40% de la suma de meses positivos. Una operación semanal era criterio *deseable*, no puerta dura.

## Resultado completo resumido

| Embudo económico sin q ni IC90 | Número | Estrategias |
|---|---:|---|
| Estudiadas | 36 | T133–T168 |
| Neto positivo SIMULADO | 10 | T133, T134, T135, T137, T138, T139, T143, T144, T145, T147 |
| Neto positivo + mínimo 15 operaciones proxy | 5 | T133, T135, T137, T145, T147 |
| Neto positivo + mínimo 15 operaciones + PF≥1,25 | 1 | **T147** |
| **Cumplen los 10 criterios económicos sin q/IC90** | **0** | Ninguna |
| Cumplen estadística D1 original | 0 | Ninguna |
| Habilitadas para D2 o fondeo | 0 | Ninguna |

**Cumplimientos individuales entre las 36**, NO acumulables ni equivalentes a aprobación: N≥15 31/36; neto>0 10/36; esperanza/trade>0 10/36; PF≥1,25 5/36; estrés1,5× positivo 8/36; estrés+$10 RT positivo 7/36; Q4 positivo 19/36; enero–abril positivo 6/36; DD≤$1.500 17/36; concentración mensual<40% 6/36.

## Las 10 estrategias de neto positivo simulado (con TODOS los motivos de fallo)

| ID | N proxy | Neto modelo USD | PF modelo | Estrés1,5× USD | Estrés +$10 RT USD | Q4 2025 USD | Ene–Abr 2026 USD | Concent. máximo mensual | Descartada por |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| T133 | 52 | +606,75 | 1,178 | +198,00 | +86,75 | +724,25 | −117,50 | 64,1% | PF, segundo período, concentración |
| T134 | 14 | +846,50 | 2,153 | +760,50 | +706,50 | +642,25 | +204,25 | 55,4% | **N insuficiente**, concentración |
| T135 | 56 | +93,75 | 1,026 | −229,75 | −466,25 | +1.399,25 | −1.305,50 | 52,2% | PF, ambos estrés, segundo período, concentración |
| T137 | 38 | +139,25 | 1,052 | −132,25 | −240,75 | +861,50 | −722,25 | 73,7% | PF, ambos estrés, segundo período, concentración |
| T138 | 5 | +267,50 | 2,682 | +248,50 | +217,50 | 0,00 | +267,50 | 91,8% | **N insuficiente**, Q4 no positivo, concentración |
| T139 | 3 | +20,00 | 1,161 | +14,75 | −10,00 | −36,00 | +56,00 | 100,0% | N, PF, estrés+$10, Q4, concentración |
| T143 | 8 | +330,75 | 2,429 | +296,25 | +250,75 | +334,12 | −3,38 | 70,4% | **N insuficiente**, segundo período, concentración |
| T144 | 5 | +225,00 | 1,676 | +165,00 | +175,00 | −41,75 | +266,75 | 38,9% | **N insuficiente**, Q4 negativo |
| T145 | 51 | +788,00 | 1,238 | +278,50 | +278,00 | +317,62 | +470,38 | 45,4% | PF inferior 1,25, concentración>40% |
| **T147** | **20** | **+642,25** | **1,499** | **+433,00** | **+442,25** | **−567,00** | **+1.209,25** | **36,8%** | **Q4 de 2025 negativo** |

**T147 satisface los otros nueve requisitos, pero NO la estabilidad positiva de los dos subperíodos**. Elegir mirar solo ene–abril porque allí gana sería selección retrospectiva; no está permitido. **T145 falla dos requisitos** pese a tener suficiente frecuencia y ambos escenarios de estrés favorables: PF1,238<1,25 y concentración 45,4%>40%. No reducir PF o el 40% para rescatarla. T134/T138/T143/T144 son muestras demasiado pequeñas; sus PF elevados no se sostienen para evaluación formal.

## Interpretación y siguientes pruebas

El obstáculo económico central **no es solamente el filtro de multiplicidad**: de 36 simulaciones 26 pierden dinero bajo costos base y, entre las positivas con frecuencia aceptable, solo T147 supera PF≥1,25. Incluso esa señal no es estable entre los dos períodos. La revisión solicitada es una **ablación de criterios**, no una validación independiente.

Los fills derivan de **transacciones Last** (precio adverso del siguiente grupo timestamp, +2 ticks entrada, +2 salida, stop-first en empate) y tasas RT asumidas $4 NQ/$1,50 MNQ; los precios de orden y comisiones del broker NO están verificados. Los siete meses ya fueron explorados repetidas veces y **NO forman un conjunto OOS independiente**. No abrir holdouts ni ejecutar D2 automáticamente. Recomendación: auditar supuestos de ejecución, fuentes/costos verificables y diseños que no reutilicen los mismos retornos antes de continuar con más hipótesis.

**Esta sensibilidad NO cambia la decisión oficial:** D1 familiar original no tiene PASS; D2 sigue vacía; no hay estrategias validadas para operar fondeo.
