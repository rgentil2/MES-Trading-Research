# NQ / MES / ES — Gate económico adicional para estrategias y carteras

**Vigencia:** 2026-10-10, para evaluaciones de estrategias y carteras preparadas **después** de esta decisión. **Tipo:** política prospectiva aditiva, no modificación retroactiva de hipótesis ni de familias ya congeladas. **Estado de las carteras actuales:** `NOT_ASSESSED` bajo este gate: no existe todavía una comparación de retorno total verificable contra los ETF ni una simulación íntegra de riesgo de fondeo.

## Objetivo acordado

Buscar que una **estrategia completa o cartera** genere una rentabilidad anualizada neta **estrictamente superior** al mayor de:
1. **15 % anual** (hurdle económico fijo del proyecto);
2. **CAGR de VOO** (retorno total, dividendos reinvertidos, USD, exactamente mismas fechas);
3. **CAGR de QQQM** (retorno total, dividendos reinvertidos, USD, exactamente mismas fechas).

Formalmente `portfolio_cagr > max(0.15, voo_cagr, qqqm_cagr)`. Un 12 % anual sigue siendo un **indicador de progreso**, no permite superar el gate. El resultado de los ETF puede ser mayor o menor que 12–15 %; esos porcentajes son el **objetivo propio**, no un rendimiento garantizado ni un pronóstico de ETF. Comparar CAGR no exime evaluar riesgo relativo y apalancamiento.

### Ventanas comparables y datos

- **Desarrollo:** únicamente 2020–2024. No se cargan ni usan resultados de operaciones de 2025/2026 sin sus autorizaciones y registros de validación independientes.
- **Comparación primaria VOO frente a QQQM:** ventana común que comienza **no antes de 2020-10-13**, fecha de lanzamiento de QQQM, y termina en la última fecha elegible de 2024 disponible para los tres. Fechas exactas y cobertura deben documentarse *antes* de comparar resultados. La curva de trading, VOO y QQQM se evalúan con los **mismos puntos inicial/final**, precios ajustados para total return y dividendos reinvertidos; no usar retornos de precio sin dividendos.
- **Complementaria 2020 completo:** VOO y un benchmark sustituto **QQQ** para el tramo anterior al lanzamiento de QQQM. Rotularlo siempre `QQQM/QQQ_PROXY`, documentar empalme y posible diferencia de comisiones, y **no** informar ese compuesto como historia real de QQQM.
- ETF, cartera y costes expresados en **USD nominales**, sin mezclar rentabilidad en COP, márgenes, deuda ni dividendos sin reinversión. Documentar proveedor, fecha de descarga, versión del archivo y ajuste de dividendos/splits.
- `CAGR = (V_final / V_inicial)^(365.2425 / dias_calendario) - 1`, si `V_inicial > 0`, `V_final > 0`, duración positiva y curva reproducible. Cuando hay aportaciones/retiros, usar **TWR** para evaluar habilidad inversora y **XIRR / money-weighted return** para el resultado personal, no aplicar CAGR ingenuo al valor final.

### DOS bases de retorno obligatorias y nunca intercambiables

**A. Comparación nominal de desempeño (diagnóstico):** simular capital de referencia USD 50.000, curva diaria de P&L **neto** y posiciones dimensionadas desde una política causal congelada. Si no hay flujos, puede calcularse el CAGR *equivalente* con `50,000 + P&L acumulado`. El valor nominal de una evaluación de fondeo NO es dinero invertido del usuario. Este CAGR equivale a una normalización de rendimiento, no constituye ROI personal, resultado garantizado, ni justifica comparar sin controles un activo ETF sin leverage con futuros apalancados. Es obligatorio acompañarlo de riesgo y exposición.

**B. Rentabilidad de bolsillo del fondeo (resultado personal):** registrar cronológicamente **desembolsos** (evaluaciones, comisiones, suscripciones, resets, costes de operación y otros cargos no incluidos) y **entradas reales** (retiros/payouts netos y cualquier devolución, fechas y moneda). Mostrar flujo neto acumulado, capital total efectivamente aportado y **XIRR** solo cuando existan flujos y fechas suficientes. Una cuenta sin payouts realizados **no** posee ROI cobrado aunque muestre P&L nominal positivo. No usar USD 50.000 como denominador de capital propio arriesgado.

### Costes y resistencia

- Comisiones, spread/slippage y ejecución correspondientes al instrumento real (NQ/MNQ o ES/MES) y a la cuenta concreta. **NinjaTrader Free no equivale a MyFundedFutures.** Evitar doble contar costes ya descontados.
- Reportar sensibilidad a **1.5 × costes totales de transacción**, actividad efectiva mensual, peor racha, drawdown de cierres e **intradía/flotante** y necesidad de capital/collateral. Un `CAGR` superior sin supervivencia a esos costes/risks **no aprueba**.
- Evaluar la cuenta elegida con reglas vigentes documentadas: *trailing* sobre equity flotante, colchón de pérdida, límites de contratos, normas de payout/consistencia e inactividad. Para el escenario histórico de MFFU 50K estudiado, la referencia de pérdida fue USD 2.000, pero se deben revalidar condiciones reales al decidir operar. **Un drawdown de cierres inferior a USD 2.000 no acredita cumplimiento sobre equity flotante.**
- Reportar drawdown máximo, volatilidad/Sharpe, Sortino, Calmar, retorno/risgo, correlación con VOO y QQQM y concentración de P&L por año. Comparar también métricas **ajustadas por riesgo**, porque un CAGR de futuros con apalancamiento no equivale directamente a inversión no apalancada en ETF.
- Un portafolio debe eliminar señales duplicadas, consolidar exposición correlacionada ES/MES y NQ/MNQ, resolver prioridad causal de señales y probar router/slippage realista. No sumar P&L de señales coincidentes como ganancias independientes.

## Evidencia deductiva incremental en carteras conjuntas (aprobado 2026-10-10)

El **objeto principal del Gate Económico** para las nuevas H67–H150 es la **estrategia/cartera conjunta completa**, no la suma hipotética de CAGR o P&L de señales individuales. Las nuevas hipótesis deben integrar dos o más funciones de decisión distintas (disparador, contexto ex ante, filtro, veto, selector de régimen o router), predefinir la simultaneidad, la prioridad y los límites de riesgo, y probar la ejecución verdadera sobre un único capital común.

El test económico de una combinación incluye **comparadores incrementales obligatorios**: cada estrategia progenitora, un router de referencia, la combinación y sus ablations (retirar cada componente), con **idénticas fechas, riesgo, capital, costes, reglas de sizing y comparables VOO/QQQM**. Mostrar no solo CAGR y P&L, sino también frecuencia, trades perdidos por filtros, exposición, fuentes de correlación, drawdown flotante/cerrado y efecto de costes multiplicados por 1,5. Una combinación que gana más debido únicamente a más riesgo, o que reduce operaciones hasta muestras no informativas, **no demuestra mejora económica robusta**.

La deducción debe partir de hechos concretos de los padres, incluyendo **resultados negativos**, y declarar antes de mirar retornos la predicción incremental y condiciones de falsación. La familia completa de combinaciones y comparadores seleccionables está sujeta a prerregistro, múltiples pruebas y candados temporales del proyecto. Los años 2020–2024, previamente revisados, siguen siendo exploratorios.

Referencias vinculantes:
`research/nq/NQ_DEDUCTIVE_ENSEMBLE_POLICY_2026_10_10.md` y
`research/nq/NQ_DEDUCTIVE_ENSEMBLE_POLICY_2026_10_10.json`.

## Estados y reglas de avance

| Estado | Cuándo aplica | Permite operar / abrir holdout |
|---|---|---|
| `EXPLORATORY_LIBRARY` | Hipótesis, filtro o estrategia conservada para investigación, incluso si no supera el Gate 1. | No |
| `ECONOMIC_DATA_PENDING` | Faltan curva neta replicable, benchmarks exactos o modelado de riesgo. | No |
| `BELOW_ECONOMIC_HURDLE` | CAGR nominal neto <= mayor de 15 %, VOO y QQQM en misma ventana. | No |
| `ECONOMIC_HURDLE_MET_RISK_PENDING` | Objetivo de retorno alcanzado, pero aún faltan auditorías de riesgo/ejecución. | No |
| `PROMISING_PORTFOLIO_EXPLORATORY` | Retorno objetivo y puertas de riesgo pertinentes acreditados en desarrollo, manteniendo etiquetas originales y advertencia por reutilización de datos. | No |
| `VALIDATED_FOR_REVIEW` | Separadamente: validación independiente y protocolo preregistrado completos, sin invadir 2026, y autorización explícita de nueva fase. | No, no es licencia de trading |

**El rendimiento no sustituye la evidencia:** mantener Gate 1 exploratorio (N>150, efecto neto>0, IC90 favorable, BH q<=0.10, >=3/5 años), confirmación Holm y gates históricos originales **sin cambios**. Gate 1 fallido no borra un registro de la biblioteca, pero prohíbe etiquetarlo como `CONFIRMED`. No elevar una cartera exploratoria a validada por mezclar hipótesis rechazadas.

**Pre-registro previo:** antes de medir el Gate económico de un candidato final, congelar sizing, universo y fechas, reglas de entrada/salida, costes, aportes/retiros, métricas y benchmarks. No optimizar stop, riesgo o ventana de ETF después de observar resultados. Registrar todos los integrantes del portafolio y sus variantes; misma muestra histórica ya explorada implica solo evidencia exploratoria.

**Holdouts:** 2025 sigue sellado hasta aprobación explícita del usuario para validar un candidato completamente congelado; 2026 reservado a una cartera ejecutable congelada con stops/TP/router para pseudo-forward posterior. Ninguna de estas ventanas se abre por el solo hecho de mejorar CAGR.

## Requisitos reproducibles del reporte económico

El informe de cada cartera contendrá `evaluation_window_start/end`, `benchmark_data_provenance`, `capital_basis`, `daily_net_equity`, `nominal_cagr`, `voo_total_return_cagr`, `qqqm_total_return_cagr`, `hurdle=max(...)`, `hurdle_pass`, `transaction_cost_model`, `1_5x_cost_stress`, `closed_drawdown`, `floating_drawdown`, `funded_rule_audit`, `cash_flows`, `investor_xirr_if_defined`, `risk_adjusted_metrics`, `overlap_audit`, `decision_status` y `holdout_access_flags`. Ningún campo desconocido puede transformarse implícitamente en `PASS`.

Ver `research/nq/NQ_H59_H150_DEDUCTIVE_RESEARCH_PROGRAM.md`, `research/RESEARCH_CONTROLS_POLICY.md` y el JSON de reglas económicas de la misma fecha.
