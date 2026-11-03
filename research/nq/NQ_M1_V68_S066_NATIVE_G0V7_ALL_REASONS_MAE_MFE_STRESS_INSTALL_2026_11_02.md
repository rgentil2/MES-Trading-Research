# S0.66 — G0 V7: motivos de rechazo simultáneos + stress drawdown MAE/MFE en M1

**Estado:** nuevos archivos de código integrables en NinjaTrader; pruebas ejecutables de C# puro y un adaptador con API simulada aprobadas en [GitHub Actions #41559098712](https://github.com/rgentil2/MES-Trading-Research/actions/runs/41559098712). **FALTA compilación F5 contra NinjaTrader Windows e inspección de backtests reales con fitness V7.** No modificar ni borrar V3/V4/V5 ni G0 V6. No usar V7 para operación real.

## Objetivo y alcance exacto

La validación del G0 V6 en S0.65 fue concluyente: 20/20 estrategias rechazadas, pero solo muestra el **primer** motivo de cada rechazo. En las mismas 20 había 20 PF<1,25, 19 DD de operaciones cerradas>$2.000, 15 meses deficientes y 2 estrategias con menos de 150 operaciones, categorías solapadas.

G0 V7 añade:

1. **Diagnóstico múltiple sin cambiar ningún límite de V6**: `INSUFFICIENT_TRADES`, `MONTHLY_FREQUENCY` (>=5 entradas **cada** uno de los 36 meses), `NEGATIVE_NET`, `LOW_PROFIT_FACTOR` (<1,25), `EXCESS_CLOSED_DRAWDOWN` (>$2.000) y `EXCESS_M1_MAE_MFE_STRESS_DD` (>$2.000).
2. **Riesgo de equity en posición aproximado con MAE/MFE nativos de NinjaTrader**: para cada operación cerrada extraemos `Trade.MaeCurrency` y `Trade.MfeCurrency` (historical Standard M1 calcula excursiones por máximos/mínimos OHLC de las barras). Llevamos saldo neto después de trades cerrados y un pico de equity *potencial* que incluye MFE, y para cada nueva operación calculamos el peor valle inferible con MAE. Se acumula drawdown de estrés máximo, siempre no menor que drawdown cerrado.
3. **Fail-closed** ante MAE/MFE NaN, infinitos o negativos, trade fuera de 2020–2022, orden temporal inválido o pérdidas por comisión mal conciliadas.
4. **Sin efecto en V5 ni G0 V6**: nuevo fitness `NQNativeG0RiskFitnessV7` obtiene score **-1e12** si falla cualquiera de las condiciones y solo publica una señal `NQ_G0_V7 PASS` *provisional* si todo cumple.

**Límite científico importante:** MFE y MAE son extremos de precios OHLC de barra M1; **no indican el orden cronológico de esos extremos**, y la excursión monetaria podría no descontar comisiones intrabar. El indicador **es una prueba de estrés de equity posible, NO un drawdown flotante exacto, NO una cota demostrada de peor caso real y NO implementa el trailing drawdown, MFFU o Bid/Ask/tick**. Puede sobreestimar lo ocurrido si supone que MFE precedió MAE cuando en realidad fue al revés; una ejecución real con gaps/slippage puede ser peor. Si se requiere precisión de cuenta fondeada hay que instrumentar equity mark-to-market en barras y después ticks, junto con la regla efectiva de cuenta.

## Dos fuentes nuevas y carpeta de instalación

En `Documentos\\NinjaTrader 8\\bin\\Custom`:

| Código | Carpeta |
|---|---|
| `research/nq/ninjatrader/NQNativeG0DiagnosticsV7.cs` | `Strategies` |
| `research/nq/ninjatrader/NQNativeG0RiskFitnessV7.cs` | `OptimizationFitnesses` |

Los archivos V6 `NQNativeG0RulesV6.cs` y `NQNativeG0FitnessV6.cs` instalados deben **quedarse**. V7 depende del **motor V6** pero no de que se seleccione la función Fitness V6.

### Prueba de compilación y backtest

1. Cerrar NinjaTrader, copiar estos dos archivos desde el botón **Raw** de GitHub sin renombrarlos. Abrir `New → NinjaScript Editor`, pulsar **F5**. Si hay error de API (en especial `MaeCurrency` o `MfeCurrency`), detenerse y compartir mensaje exacto; nunca sustituir por valores cero.
2. Abrir Strategy Analyzer y **cargar la plantilla conservada** `NQ_V5_G0_20_2020_2022` (si se guardó después de S0.65). Si no se guardó, partir de `NQ_V5_UNIQUE20_2020_2022` y configurar Optimization, `Strategy=NQNativeGeneticLabV5`, `Optimizer=NQNativeUniqueOptimizerV5`, seed20261102, target20, maxAttempts2000, mismos 20 rangos, 2020–22.
3. Guardar **COPIA NUEVA** `NQ_V5_G0V7_MAE_20_2020_2022`, sin sobrescribir las anteriores.
4. Cambiar exclusivamente **Optimize on → `NQNativeG0RiskFitnessV7`**, manteniendo instrumento NQ DEC26 merged Last M1, CME US Index Futures RTH, Standard (Fastest), `Include commission` activado con plantilla correcta y slippage2.
5. Ejecutar los mismos **20** candidatos. En `New → NinjaScript Output`, verificar `NQ_V5 BEGIN target=20 seed=20261102 ...`, `NQ_V5 END executed=20 generatedUnique=20 ... failure=0` y 20 logs de `NQ_G0_V7 REJECT reasons=...`, uno por identidad, incluyendo `closedDD=...` y `stressDD=...`.
6. **Éxito esperado:** 20/20 rechazos, mismos 20 identificadores `NQEX5_` y mismo resultado económico de S0.63/S0.65; **no es posible calcular el stressDD esperado sin nuevos datos MaeCurrency/MfeCurrency por trade**. El valor tiene que ser finito, >=0 y >=`closedDD` para cada candidato. El desempate de rechazados seguirá siendo -1e12; no seleccionar por orden visual de filas.
7. Si aparece `NQ_G0_V7 REJECT reasons=INVALID_MAE_MFE`, `PNL_MISMATCH`, `EXCEPTION`, ID cambiado o G0 PASS inesperado: detener y compartir captura/log. Puede haber una línea duplicada de candidato al seleccionarlo en Strategy Analyzer; comparar IDs únicos con los 20 `PRE_RUN`.

Envíanos captura de **Optimization Results** y texto de **NQ_G0_V7** y **NQ_V5 END**. No ejecutar 2023–26 ni aumentar a miles hasta validar V7.

## Interpretación

- 20 estrategias rechazadas *no* significa fallo técnico: las condiciones económicas siguen incumpliéndose.
- Mínimo cinco entradas cada mes implica >=180 en 36 meses. Se mantiene de V6 intencionadamente; distinta de >=5 operaciones/mes **de promedio**.
- En V7 la mejora es transparencia y una barrera conservadora contra drawdown flotante potencial. El análisis científico posterior debe incluir barras por estrategia, orden real de ticks/fills, riesgo diario/trailing y estabilidad.
- El motor sigue siendo 10 primitivas de señales, no el catálogo futuro de 132; el generador V5 usa búsqueda pseudoaleatoria sin cruce/mutación real.
