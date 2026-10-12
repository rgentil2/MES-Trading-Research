# NQ Tick — Política estadística adaptada a 135 sesiones/7 meses (sin relajar puertas históricas)

**Vigencia prospectiva 2026-10-11 Colombia**, revisión metodológica solicitada por el usuario. **NO altera retroactivamente** `research/es/ES_STAGE_GATES.md`, `research/es/ES_STAGE_GATES_EXPLORATORY_AMENDMENT_2026_10_09.md`, los resultados H67–H78 de cinco años, las familias Holm previamente congeladas ni las puertas económicas originales T05/H01/H02. **No constituye preregistro de una NUEVA hipótesis monetaria**; únicamente adapta evaluación descriptiva y futuros diagnósticos de sensibilidad de T tick existentes.

## 1. Universo y unidades que realmente tenemos

- Programa T NQ: **140 días fuente, 135 sesiones DEV elegibles**, entre octubre de 2025 y abril de 2026; siete meses de calendario. No son 135 sesiones aleatorias independientes, 7 años ni 7 mercados independientes. Dos trades de un día pueden estar correlacionados; múltiples estrategias comparten sesiones y subyacente.
- **N_trades** = operaciones efectivamente ejecutadas por modelo/escenario (por ejemplo T05=115, B05H02 standalone=75, router=166). **N_sessions** = 135 incluyendo días con cero operaciones; **N_months** = 7; **N_active_days** aún no disponible en agregados; **N_effective** nunca se equipara a N_trades ni se inventa. Día de negociación unidad mínima razonable para retornos; semanas completas contiguas como bloques de dependencia y mes como diagnóstico de estabilidad.
- Fuente para **el diagnóstico A ahora**: SOLO `summary.json` agregado seguro de B05H02 `b05h02-seven-month-safe-reversion-report`, [Actions 38193895252](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38193895252); no abrir Last ni un holdout. Para reconstruir un **diagnóstico B por día/semana** haría falta usar internamente los mismos Last DEV existentes y sus reglas congeladas; NINGUNA nueva descarga de mercado a proveedor ni fechas reservadas. No publicar ticks, entradas ni retornos por fecha.
- Holdouts T mayo–junio y julio–septiembre de 2026 siguen sellados; historia H 2025/26 sellada. No usar 5s en señales nuevas; el legacy T05 puede usar su definición pasada únicamente de benchmark.

## 2. Escala A — diagnóstico REALIZABLE YA con 7 agregados mensuales

Con `m=7` meses completos y retorno neto USD por mes de cada modelo/compartido bajo **los mismos costes y mismo capital**, medir lo siguiente SIN fingir IC por trade ni significancia por día:

1. **7/7 valores mensuales**, cantidad de meses positivos, mínimo/máximo, peor mes y dependencia de un mes. No seleccionar "operar los mejores meses" a posteriori.
2. **IC bilateral 90% de la MEDIA MENSUAL** usando t-Student n=7, df=6 y `t(0.95,6)=1.9431802805`, en USD/mes: `mean ± t * stdev(monthly) / sqrt(7)`. **Supone meses aproximadamente independientes/estacionarios y datos apropiados para t**; con solo siete meses y estacionalidad/escalada temporal el resultado es **DESCRIPTIVO FRÁGIL**, no IC90 diario o por trade y NO alcanza Gate1.
3. **Test binomial exacto de signo mensual**, unilateral bajo `H0:p_meses_positivos<=0.5`, solo si se admite la fuerte hipótesis de signos mensuales independientes/equiprobables bajo H0: `p = sum_{j=k}^7 comb(7,j)/2^7`. Reportar p como **diagnóstico dependiente de supuestos, NO p confirmatorio**; se usa signo estrictamente positivo, cero no cuenta como positivo. Por ejemplo, 6/7 meses positivos solo arroja p=0.0625 (no es q BH).
4. **LOMO**: quitar un mes completo a la vez (7 escenarios) y mostrar rango del neto de seis meses, cantidad 7/7 de signos positivos de contribución e incremento cuando corresponda. NO usar el mejor LOMO para recalibrar reglas.
5. Evaluar el **incremento EMPAREJADO** del router vs T05 por MES, no restar intervalos no emparejados de dos estrategias. Posible que ambos modelos tengan retorno total positivo pero incremento negativo: solo mejora el modelo si el incremento es positivo bajo el mismo presupuesto.
6. **Control de cobertura:** exigir siete meses EXACTOS / fuente 140 / elegibles 135 / paridad T05 115 operaciones y USD5102,50 estrés / H02 75 operaciones −USD1427,50 / router 166 operaciones +USD2195 / delta −USD2907,50. Inconsistencia => ABORT.

**Duración desigual de los meses:** octubre-2025 empieza el 15, mientras los meses siguientes abarcan calendarios completos; incluso con siete netos mensuales, distintas cantidades de sesiones/operaciones cambian la exposición. El IC de USD/mes mezcla frecuencia y expectativa. La versión definitiva debe analizar **USD por sesión elegible con ceros** y un bloque semanal sobre las 135 sesiones, no extrapolar el intervalo mensual a un mes típico uniforme.

**No reportar q BH ni Holm como computados:** los tests mensuales son diagnósticos a posteriori sobre estrategias ya seleccionadas y no se estableció la familia completa para ese endpoint de selección. Es matemáticamente incorrecto llamar `q` al p mensual, aplicar BH sobre tres estrategias post hoc o recalificar T05 como confirmada. En la tabla escribir `q = NO EVALUABLE`.

## 3. Escala B — estándar recomendado para futuras familias T, antes de leer resultados

Solo cuando se disponga de vector **por sesión elegible** de P&L estrés congelado, **incluyendo los días con cero operaciones**, y una familia de contrastes enumerada ex ante:

- **Unidad de análisis primaria:** `daily_net_return_USD` sobre **135 sesiones** con coste real de escenario y stop/sizing congelados. Para cartera incremental: `delta_d = Router_daily_net - T05_daily_net` EMPAREJADO en la MISMA sesión y cuenta. N eventos independientes **DESCONOCIDO**; N sesiones ≠ N_eff.
- **Dependencia:** bootstrap de bloques móviles de **5 sesiones consecutivas**, al menos **10.000 repeticiones con semilla congelada**, bloque circular opcional especificado antes de resultados; comparar por sensibilidad bloques de 3 y 10 sesiones **sin escoger longitud posterior por P&L**. Reportar IC90 bilateral de la media por sesión y p unilateral exploratorio basado en distribución bajo nulo centrada, explicando aproximaciones/autocorrelación. Con pocos días activos el IC puede ser muy ancho; NO imputar ganancia en días sin operación.
- **Robustez temporal:** siete meses con todos sus P&L, sensibilidad de **retirar cada uno de los siete meses** sin optimización; sumar cuántos tienen efecto en signo favorable como **consistencia descriptiva**, no fingir que sustituye `3/5 años`. Opcional indicador orientativo **≥5/7** meses favorables, explícitamente *no* evidencia de significancia (bajo independencia p exacto ≥5/7 es 0.22656). Nada de filtros ex post por meses.
- **Precisión/poder:** reportar amplitud del IC90, error estándar y efecto mínimo detectable (MDE) con el tamaño de muestra actual (sin declarar arbitrariamente "N mínimo=30/50/100" ni forzar que 115 trades sean 115 eventos independientes). Si intervalo compatible con ganancia y pérdida, `INSUFFICIENT_PRECISION`, aunque media >0.
- **Multiplicidad:** registrar **todos** los miembros de la familia/variantes y su endpoint ANTES de outcomes; para una futura familia válida, BH q≤0,10 exploratorio sobre esa familia entera, y Holm con presupuesto original de familias separado como confirmatorio. Para el histórico T ya inspeccionado, q post hoc sería *solo exploratorio descriptivo no inferencia independiente* y no se permite retro-certificación por rediseñar la familia después.
- **Definición operativa completa:** N operaciones, exposición única, retorno medio, PF, stress 1,5×/extra RT, drawdown Last e intratrade, estabilidad meses, incremento router vs T05, costes de oportunidad y controles de fondos. Se mantiene el hurdle económico `CAGR neto > max(15%, VOO TR, QQQM TR)` en ventana comparable y con trailing-risk verificado. Un análisis estadístico favorable NO reemplaza riesgo ni validación OOS.

## 4. Gate dual y estados explícitos

| Nivel | Requisitos | Estado máximo permitido en DEV |
|---|---|---|
| A: **7 meses agregados** | Cobertura/fuente congeladas y estadísticos mensuales exactos; información insuficiente para día/semana/q formal | `MONTHLY_DIAGNOSTIC_ONLY` |
| B: **135 sesiones, bloques semana** | Diario con ceros, IC90 y sensibilidad bloques, LOMO 7/7, familia congelada+q ajustado si existe | `PROMISING_IN_SAMPLE_ONLY` si efecto neto positivo y precisión/robustez e incremento favorables; **nunca confirmed** |
| C: **confirmación** | Holm y criterios antiguos aplicables, ejecución/financiación, periodos independientes explícitamente autorizados | Pendiente y NO autorizado para T ni H |
| H histórico 2020–24 | N>150, IC90, q BH≤0,10, ≥3/5 años y su preregistro original | Conservar política histórica íntegra |

**Prohibido declarar 'Gate1 PASA' basándose solo en siete puntos mensuales o en umbrales cambiados después de observar resultados.** No sustituir `N>150` del programa H por `N>=75 trades` arbitrario en T. La adaptación cambia **la unidad y la jerarquía de evidencia**, no el nivel de exigencia confirmatoria. Los resultados T02/T05/H02 siguen exploratorios y H01 indeterminada por entradas ambiguas. No comprar fondeo.

## 5. Tabla obligatoria

`ID | pregunta | muestra/meses | N_sesiones | N_active_days | N_trades | mean_net por sesión/mes y unidad | IC90 + unidad + método | p del diagnóstico y supuesto | q BH/N/D | Holm/N/D | meses positivos /7 | LOMO | PF estrés | DD Last | delta router estrés | costo extra | nivel estadístico | pasa/NO/insuficiente`.

**Regla de conservación:** no sobreescribir conclusiones originales, reporte aditivo en `NQ_PROJECT_MASTER.md` y `NQ_STATISTICAL_HYPOTHESIS_SCORECARD.md`; anotar en `NQ_RESEARCH_LOG.md`. Implementar y testear sin historia adicional ni OOS.
