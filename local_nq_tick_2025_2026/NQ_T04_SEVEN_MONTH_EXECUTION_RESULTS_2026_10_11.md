# NQ T04 — resultado exploratorio de ejecución T02 vs C02, 2026-10-11

**Código congelado antes de ejecutar**: [prerregistro de stops, costes y riesgo](./NQ_T04_CONSERVATIVE_T02_EXECUTION_PREREG_2026_10_11.md). Se probó en [GitHub Actions 38162567546](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38162567546), **7/7 trabajos SUCCESS**, solo **octubre 2025–abril 2026**, 140 sesiones de datos y 135 aptas. No se accedió a mayo–junio para outcomes ni a julio–septiembre 2026 sellado. Modelo Last-only, no evidencia de fills del broker. Stop 16–48 ticks según 25 % del rango de apertura, TP 2x, límite 5 minutos, 1 NQ, máximo 2 operaciones/día. Costes **supuestos, no verificados**: baseline $5 RT + 1 tick adverse por lado; estrés $7,50 RT + 2 ticks adverse por lado.

## Resumen sobre los siete meses

| Cartera | Escenario | Trades simulados | P&L neto simulado USD | Media neta/trade USD | PF neto | Win rate | Max DD cerrado usando curva diaria USD | Mayor DD intrames aproximado de Last USD |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T02 reversión con desaceleración | Base | 190 | +8.420,00 | +44,32 | 1,309 | 43,16 % | 2.740,00 | **3.175,00** |
| T02 reversión con desaceleración | Estrés | 190 | +6.860,00 | +36,11 | 1,244 | 43,16 % | 2.912,50 | **3.367,50** |
| C02 reversión sin desaceleración | Base | 217 | +6.490,00 | +29,91 | 1,199 | 41,47 % | 2.845,00 | 2.540,00 |
| C02 reversión sin desaceleración | Estrés | 217 | +2.842,50 | +13,10 | 1,083 | 40,09 % | 4.015,00 | 2.860,00 |

**No sumar** las columnas de P&L como si fueran estrategias simultáneas; se simulan carteras alternativas sobre el mismo capital. El máximo DD `intra` es diagnóstico basado en `Last` y el método del simulador; no implementa las reglas reales de trailing sobre equity flotante de la empresa de fondeo.

## T02 mensual (neto hipotético)

| Mes | Trades | Base USD | Estrés USD | Máx. DD flotante aproximado intrames, base USD |
|---|---:|---:|---:|---:|
| Oct-2025 | 23 | −840,00 | −1.062,50 | **3.175,00** |
| Nov-2025 | 17 | +1.445,00 | +1.302,50 | 1.215,00 |
| Dic-2025 | 30 | +1.270,00 | +1.005,00 | 1.115,00 |
| Ene-2026 | 32 | +2.510,00 | +2.290,00 | 1.545,00 |
| Feb-2026 | 22 | +1.655,00 | +1.470,00 | 850,00 |
| Mar-2026 | 32 | +1.570,00 | +1.310,00 | 1.755,00 |
| Abr-2026 | 34 | +810,00 | +545,00 | 1.885,00 |

**Interpretación: NO APROBADA PARA FONDEO.** Aun si la referencia histórica de ~USD 2.000 de pérdida máxima de la cuenta 50K fuera aplicable (verificar siempre reglas vigentes), T02 excede esa referencia tanto en DD cerrado (USD 2.740) como en la aproximación flotante (USD 3.175) en el escenario base. El estrés tiene PF **1,244 < 1,25** de referencia de robustez, y base solo 1,309. Tampoco se verificaron comisiones reales, ejecución de stops, payouts ni retorno total comparable VOO/QQQM. No anualizar +USD 8.420 en siete meses como una estrategia garantizada ni derivar ROI personal de una cuenta de fondeo nominal de USD 50K.

**Aprendizaje para siguiente hipótesis deductiva:** la desaceleración sobre reversión mostró aportación exploratoria respecto a C02 (menor frecuencia, mejor PF y resistencia relativa a costes), pero la estrategia no resuelve drawdown/variación de régimen. Probar **por separado y prerregistrado** si el contexto causal de barras de 233/377 operaciones añade valor selectivo comparado con T02 sin filtros, con ablation y control de frecuencia; no ajustar valores retrospectivamente ni usar resultados de validación.

**Estado:** `PROMISING_DIRECTIONAL_EXPLORATORY_BUT_FUNDED_RISK_FAIL` — no operar, no comprar fondeo, no abrir pseudo-forward.
