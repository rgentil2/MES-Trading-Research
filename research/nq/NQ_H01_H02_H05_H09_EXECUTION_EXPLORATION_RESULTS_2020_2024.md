# Exploración de estrategia NQ/MNQ — H01, H02, H05 y H09

**Fecha de estudio:** 2026-10-09. **Clasificación:** `POST_SELECTION_EXPLORATORY_ONLY_NOT_VALIDATED`. Alcance: **datos de desarrollo 2020–2024**, sin abrir precios ni resultados 2025/2026. Parámetros y código guardados en GitHub antes de generar los nuevos resultados.

## Objetivo y cómo interpretarlo

Esto NO confirma ninguna de las cuatro hipótesis, que habían fallado sus pruebas estadísticas originales. El mismo histórico ya se usó para seleccionarlas. Ahora investigamos si al incorporar órdenes de salida mecánicas algunas pueden formar un mecanismo de ejecución interesante. No podemos seleccionar la combinación más rentable del histórico y considerarla evidencia independiente.

Comparamos tres tamaños de stop (`0.10`, `0.15`, `0.20` del rango RTH mediano de las **14 sesiones anteriores**), tres TP (`1R`, `1.5R`, `2R`) y tiempo máximo (`30` o `60` minutos). Son **18 configuraciones por hipótesis** y para cada una hacemos contabilidad de 1 NQ y 1 MNQ: **144 escenarios individuales**. Además, 36 escenarios de una cartera que toma solamente la primera señal del día. Total: **88.668 ejecuciones hipotéticas** en la malla, NO operaciones independientes observadas.

Entrada a apertura de la siguiente vela, penalización de 2 ticks en entrada y 2 en salida, comisiones Free all-in de NQ $5.74 o MNQ $1.88 por ida y vuelta. Los movimientos MNQ son **simulados con precios NQ**, no con fills observados de MNQ. Si en una vela de un minuto se tocan simultáneamente stop y objetivo, damos prioridad al stop; gaps en contra ejecutan al open adverso. Estas son aproximaciones OHLC de 1 minuto, no reproducción de ticks ni cola de órdenes. Las comisiones Free **NO equivalen automáticamente** a las de MyFundedFutures.

## Universo, integridad y solapamiento

- Historias originales: H01 `1.117`, H02 `636`, H05 `545`, H09 `173` = **2.471 señales**.
- Tras comprobar día, hora, precio de entrada y contrato: H01 `1.117`, H02 `636`, H05 `537`, H09 `173` = **2.463 señales**. Se excluyen exactamente **8 H05 del rollover** en que el precio del contrato nuevo se comparaba con el nivel de otro contrato. No se modifica ningún disparador.
- **913 días** registran señales de al menos dos hipótesis; **352 días** tienen por lo menos tres. **1.175 días** tienen alguna señal, de los que la cartera de primera señal ejecuta una operación diaria como máximo: H01 651, H02 179, H05 172 y H09 173.
- En todos los estudios, años 2025/2026 se mantuvieron cerrados. La elegibilidad actual exige RTH completa y por eso no constituye todavía una prueba prospectiva causal de elegibilidad de sesión.

## Escenario central fijo de la rejilla: stop 15 %, TP 1,5R, 30 min

Se presenta el punto medio de la rejilla para comparar las cuatro ideas sin elegir su mejor parámetro.

| Hipótesis | Señales | NQ neto/op. | PF NQ | DD NQ cerrado | MNQ neto/op. | PF MNQ | DD MNQ cerrado | Años positivos |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| H01 — ORB + volumen | 1.117 | −$5,58 | 0,983 | $28.370 | −$1,86 | 0,945 | $3.563 | 2/5 NQ |
| H02 — ruptura fallida | 636 | +$8,98 | 1,027 | $14.125 | −$0,41 | 0,988 | $1.710 | 2/5 NQ |
| H05 — barrida de nivel previo | 537 | −$11,26 | 0,967 | $28.960 | −$2,43 | 0,931 | $3.501 | 2/5 NQ |
| **H09 — continuación gap** | **173** | **+$109,09** | **1,369** | **$8.122** | **+$9,60** | **1,318** | **$860** | **4/5 NQ** |
| **Cartera primera señal/día** | **1.175** | **+$2,01** | **1,006** | **$34.348** | **−$1,11** | **0,968** | **$4.044** | **2/5 NQ** |

**Interpretación:** con una configuración de referencia uniforme, H01 y H05 pierden, H02 queda cerca de cero y H09 mantiene un comportamiento económicamente más interesante. Juntarlas en un solo flujo **NO mejora** el rendimiento ajustado por riesgo; la cartera MNQ referencia pierde.

## H09: punto descriptivo destacado, sin selección confirmatoria

Entre las combinaciones exploradas, **H09 con stop `0.20 × rango mediano anterior`, objetivo `2R`, tiempo `30 min`** tuvo:

| Estadístico | 1 NQ | 1 MNQ sintético |
|---|---:|---:|
| Señales | 173 | 173 |
| Expectativa neta por trade | **+$208,38** | **+$19,53** |
| P&L neto histórico | +$36.049,98 | +$3.379,06 |
| Profit Factor | 1,625 | 1,576 |
| Win rate | 53,76 % | 53,76 % |
| Drawdown máximo de resultados cerrados | **$8.928,22** | **$929,39** |
| Años positivos | 4/5 | 4/5 |
| IC 90 % semanal bootstrap, media por trade | [$87,21, $341,62] | [$6,89, $32,66] |
| Expectativa con 1,5× costes modelados | +$195,51 | +$17,59 |
| Máximo intervalo entre días con señal | **59 días** | **59 días** |
| Intervalos entre señales de más de siete días | **79** | **79** |

Resultado histórico por año (MNQ sintético, neto): **2020 −$474,19; 2021 +$1.111,12; 2022 +$1.916,75; 2023 +$103,14; 2024 +$722,24.** El **56,7 %** del beneficio acumulado procede de 2022; en 2023 la ganancia es muy pequeña. Por tanto, la consistencia de cuatro años positivos no garantiza estabilidad económica.

Para NQ, el stop nominal incluido coste modelado tuvo mediana **$814,24**, máximo **$1.577,24**, pero el drawdown acumulado entre trades superó por mucho los **$2.000**. **No es compatible con validar una evaluación de 50K tal como está**, y el DD cerrado todavía subestima riesgos de equity intradía, gaps y correlaciones.

Para 1 MNQ, la pérdida nominal por stop tuvo mediana **$82,73** y máximo **$159,03**, pero eso no basta para decir que supera las reglas de MFFU: faltan evaluación de equity flotante, comisiones específicas de fondeo, calendario y mínimos de actividad. Su baja frecuencia (aprox. 173 señales en 5 años, ~3/mes en meses con señal, 79 pausas >7 días) sería insuficiente por sí sola para una estrategia que exija operar regularmente.

**Advertencia metodológica fundamental:** hay 18 variantes de parámetros por señal y cuatro hipótesis elegidas después de ver sus estadísticas previas. Que H09 tenga un intervalo bootstrap positivo en algunas variantes **NO significa que ahora supere retroactivamente Gate 1 ni la corrección BH/Holm original**. Este intervalo no corrige la selección de mejores parámetros realizada sobre las mismas fechas; no justifica abrir 2025 automáticamente.

## La combinación de cuatro estrategias NO funciona como una cartera aprobada

En el escenario aparentemente mejor por ganancia promedio de la **cartera primera señal/día**, también seleccionado *ex post*: stop 20 % / TP 2R / 30 minutos:

| Métrica | 1 NQ | 1 MNQ sintético |
|---|---:|---:|
| Operaciones | 1.175 | 1.175 |
| Expectativa neta | +$29,41 | +$1,64 |
| PF | 1,077 | 1,042 |
| Drawdown máximo cerrado | **$23.790,82** | **$2.598,49** |
| IC 90 % bootstrap | Incluye cero | Incluye cero |
| Expectativa con 1,5× costes | +$16,54 | **−$0,30** |

Las combinaciones de cartera tampoco aportan un mecanismo robusto: en NQ ninguna de las 18 tuvo IC al 90 % totalmente positivo y en MNQ tampoco. Su drawdown **cerrado** mínimo entre las 18 alternativas MNQ fue **$2.598,49**, ya superior al referente de pérdida de $2.000 de una evaluación MFFU EOD de 50K. No hemos calculado pass rates ni se deben deducir de estos resultados.

## Dictamen y siguiente etapa

1. **H09: investigar como un candidato de ingeniería exploratoria, no aprobar.** Es la única de las cuatro que muestra expectativa positiva en casi toda la rejilla, PF algo más interesante y 4/5 años con ganancias en varios escenarios, pero depende bastante de 2022 y tiene largos periodos sin señal. Por ahora podría ser *componente infrecuente*, no motor único para fondeo.
2. **H02: no aprobar;** beneficios débiles/inestables, IC incluye cero en todos los escenarios, consistencia desfavorable.
3. **H01 y H05: no aprobar;** su mejor combinación de desarrollo no justifica el riesgo ni los costes; H05 pierde una parte crucial del resultado histórico tras corregir rollover.
4. **Cartera con las cuatro:** no aprobar. Aun en MNQ conserva un DD cerrado superior al objetivo de cuenta evaluada y un PF marginal.

Antes de cualquier test independiente: (a) especificar causalmente la elegibilidad de días sin seleccionar por completitud al cierre; (b) redondear stops y objetivos al tick; (c) fijar **una** configuración justificable sin optimizar 2020–2024; (d) auditar fills con datos tick y news; (e) incluir proveedor de fondeo exacto, intraday floating DD, daily consistency y pausas reales. **2025 solo se abriría para un candidato realmente congelado bajo protocolo; 2026 queda sellado hasta el portfolio final.** No abrir ninguno como consecuencia automática de esta exploración.

Archivos de auditoría: `INDIVIDUAL_4X18X2_SCENARIOS.csv`, `PORTFOLIO_18X2_SCENARIOS.csv`, `FULL_EXECUTION_GRID_TRADES.csv.gz`, `ELIGIBLE_ORIGINAL_SIGNALS.csv`, `PORTFOLIO_FIRST_SIGNALS.csv`, `REPORT.json`, preregistro, script y tests.