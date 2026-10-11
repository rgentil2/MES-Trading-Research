# NQ — BITÁCORA CRONOLÓGICA DE INVESTIGACIÓN Y DECISIONES

> **Registro acumulativo (append-only). NO borrar una entrada anterior al corregirla:** escribir una nueva entrada que indique qué se corrigió, por qué y con qué evidencia. Las fechas, runs, muestras y limitaciones son parte del resultado.
>
> **Lee primero:** [NQ_PROJECT_MASTER.md](NQ_PROJECT_MASTER.md). Allí están el estado actual, los gates y el backlog con prioridades.
>
> **No confundir programas:** H01–H78 sobre NQ minuto 2020–2024 y T01–T10 sobre NQ ticks DEV 2025-10–2026-04 tienen políticas de holdout separadas.

## Plantilla OBLIGATORIA para próximos cambios

Copiar esta estructura **al final del archivo** cuando cierre un bloque, y actualizar simultáneamente la sección 0, el histórico breve y el backlog en el documento maestro.

```markdown
### AAAA-MM-DD — [ID] Título

- Objetivo/mecanismo; padres y comparadores:
- Decisión previa y prerregistro (enlace/commit):
- Universo exacto, fuente de datos y periodos que siguen sellados:
- Acción completada y cambios de código (commit SHA):
- Pruebas ejecutadas, GitHub Actions URL/ID, estado real:
- Resultados completos con costes/actividad/PF/DD y resultados negativos:
- Gate(s) cumplidos y fallidos, error/incertidumbre:
- Decisión: PASA EXPLORACIÓN / FALLA / INSUFICIENTE / PENDIENTE — NUNCA aprobación para fondeo sin su gate:
- Próximo paso vinculado a ID del backlog:
- Correcciones a entradas previas (si aplica):
```

---

## Periodos históricos previos conservados

### Hasta 2026-10-10 — Programa NQ minuto H01–H78, y cambio de método

- **Objetivo:** descubrir hipótesis cuantitativas direccionales y **combinaciones** ejecutables, no señales aisladas optimizadas infinitamente; límite 150 como techo, no cuota obligatoria.
- **Datos:** NQ 1 minuto **2020–2024** reutilizados para desarrollo, 2025/2026 reservados para ese programa H.
- **H67–H72:** ninguna aprobó Gate 1, aunque H69 (OR de gap continuation H09 y reversión premarket H56) generó 262 trades, **+$2.704,44**, PF 1,335, BH q 0,115 > 0,10 y retorno nominal equivalente sobre US$50k bajo el piso 15 %.
- **H73–H78:** seis routers ex ante por estado. **0/6** mejoraron H69 incrementalmente con significancia; 0/6 pasó todos los gates. H77 +$2.385,30/PF 1,632, pero N140 <150 y ~75,2 % del beneficio concentrado en 2022.
- **Conclusión:** la multiplicidad y reutilización del mismo desarrollo obligan a buscar nuevas fuentes y mecanismos; no fingir que recortes por años son OOS. Registro científico: [H67–H72](research/nq/NQ_H67_H72_RESULTS_2020_2024.md), [H73–H78](research/nq/NQ_H73_H78_RESULTS_2020_2024.md).
- **Cambio de política 10-oct-2026:** fórmulas explícitas de pruebas conjuntas, ablations, costo, datos sincronizados, portfolio de riesgo único y evaluación > max(15 %, VOO, QQQM). Ver [política deductiva](research/nq/NQ_DEDUCTIVE_ENSEMBLE_POLICY_2026_10_10.md) y [gate económico](research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.md).

### 2026-10-10 a 2026-10-11 — Recuperación y protección de datos NQ

- **Hecho:** el usuario subió al almacenamiento privado NQ ticks de **octubre 2025–junio 2026** y el histórico **NQ/MNQ minuto 2020–2026** en un release de GitHub privado. Se verificaron manifiestos/hashes y disponibilidad, sin necesidad de reenviar archivos grandes.
- **Repo:** [NQ-Ticks-Dev-2026](https://github.com/rgentil2/NQ-Ticks-Dev-2026) privado, Last/Bid/Ask en releases mensuales; [NQ-Ticks-Sealed](https://github.com/rgentil2/NQ-Ticks-Sealed) privado julio–septiembre sellado; ZIP minuto en [NQ-Tick-Data release](https://github.com/rgentil2/NQ-Tick-Data/releases/tag/nqmnq-minute-2020-2026-v1).
- **Pendiente crucial:** **conciliación real exacta** fuente minuto independiente ↔ ticks Last. Hay 34 tests sintéticos de comparador, pero no demostraron paridad entre archivos reales. Piloto definido NQ 12-25 2025-10-15.
- **BBO QC preliminar:** 36 días de tres flujos separados, mediana diaria ~32,13 % Last fuera de la cotización anterior; incertidumbre de secuencia compartiendo timestamp. No inferir ejecuciones reales, ni usar quotes futuras para simular mejores precios. [Informe BBO](local_nq_tick_2025_2026/BBO_36_DAY_SOURCE_QC_AND_NEXT_RESEARCH_2026_10_11.md).
- **Decisión:** el estudio reciente T sobre ticks usa **DEV 2025-10-15–2026-04-30**, interna mayo–junio, pseudo-forward julio–septiembre sellado. La investigación H conserva sus otras fechas.

## 2026-10-11 — Trabajos T01–T09, todos sin fondeo autorizado

### 2026-10-11 — T01–T03: hipótesis direccionales de apertura

- **Objetivo:** estudiar ruptura de rango, aceleración de transacciones Last, rupturas fallidas y reversión/slowdown con barras de 5 segundos y contexto observado antes de la orden.
- **Datos:** DEV Oct2025–Abr2026, 140 fechas fuente / 135 elegibles.
- **Resultado:** la continuación acelerada por sí sola no se sostuvo como sistema costeado; la **reversión de ruptura fallida** T02 motivó el primer motor de órdenes T04.
- **Decisión:** conservar T01 y controles, desarrollar T02. Los reportes de T01–T03 son la evidencia primaria y deben consultarse antes de atribuir cualquier nuevo efecto estadístico.
- **Gate:** exploratorio; sin OOS, sin prueba de retorno real.

### 2026-10-11 — T04: convertir señales en transacciones con SL/TP y fricciones

- **Especificación congelada:** 1 NQ, máx. 2 trades/día sin posiciones simultáneas; stop 25 % opening range limitado a 16–48 ticks de precio, TP 2R, timeout 300 segundos, entrada hasta 11:10 ET, corte 11:30 ET; detener nuevas entradas con resultado diario realizado <=−$600.
- **Base:** $5 de comisión RT + 1 tick adverso por lado; **estrés:** $7,50 RT + 2 ticks adversos por lado (costes supuestos, no broker verificado).
- **T02 padre:** 190 operaciones, **+$8.420 base / +$6.860 estrés**; su riesgo posterior no pasó la pantalla indicativa T08. No escogerlo por el mayor P&L bruto.
- **Implementación:** [nq_t04_execution.py](local_nq_tick_2025_2026/nq_t04_execution.py).

### 2026-10-11 — T05: hipótesis de barras por prints 233 y 377

- **Causalidad:** 233 y 377 se forman con conteo de transacciones Last, no saltos de precio; comparar **últimas barras completas** a la señal, sin datos futuros. Reinicio de barra 08:00 ET.
- **T05-377:** 115 operaciones, **+$6.220 base / +$5.102,50 estrés** en siete meses. **T05-233+377:** 59 operaciones, +$5.395 base / +$4.657,50 estrés, pero actividad insuficiente (noviembre 2, febrero 4).
- **Decisión:** T05-377 como **benchmark/candidato de investigación**; 233+377 solo subconjunto, NO estrategia independiente para sumar al portafolio.
- **Código:** [nq_t05_fibonacci_bars.py](local_nq_tick_2025_2026/nq_t05_fibonacci_bars.py).

### 2026-10-11 — T06: controles cercanos a Fibonacci

- **Pregunta:** ¿hay ventaja específica por usar 233/377 o señales similares con 250/400?
- **Observación:** control 250+400, 52 operaciones / **+$1.275 base**, comparado con otras variantes registradas.
- **Decisión:** números Fibonacci **no son alpha validada por sí solos**. No hacer barridos masivos de números de barras para escoger un máximo histórico.
- **Ejecución:** [T06 Actions](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38168307588), éxito.

### 2026-10-11 — T07: contexto corto/medio/largo 233/4181/10946

- **Observación:** 233+4181+10946 produjo **29 operaciones, +$790 base, ~4,1 operaciones/mes**; comparador 240/4200/11000 **24 trades, −$980 base**.
- **Decisión:** la exigencia de 3 contextos estrictos reduce demasiado la frecuencia; mantener largos como contexto descriptivo/no-trade si futura evidencia lo justifica. No añadirlo automáticamente a T05.
- **Ejecución:** [T07 Actions](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38168829410), éxito.

### 2026-10-11 — T08: auditoría continua del drawdown de T05

- **Objetivo:** mejorar medida de riesgo de cuenta evaluando equity Last durante operaciones, high-water mark concatenado entre meses y costes; **no probar un mecanismo nuevo**.
- **Resultados:**

  | Alternativa excluyente | Trades | P&L base | P&L estrés | PF estrés | DD Last envolvente estrés | Frecuencia mínima mensual | Decisión |
  |---|---:|---:|---:|---:|---:|---:|---|
  | T02 padre | 190 | +$8.420 | +$6.860 | 1,24356 | $3.385 | 17 | **FAIL** DD de referencia y PF |
  | **T05-377** | **115** | **+$6.220** | **+$5.102,50** | **1,31826** | **$1.825** | **8** | **Solo PASS condicional de pantalla preliminar**, nunca live |
  | T05-233+377 | 59 | +$5.395 | +$4.657,50 | 1,64219 | $1.422,50 | 2 | **FAIL frecuencia** |

- **Limitaciones:** Last envelope **no es broker trailing DD**, secuencia entre prints mismo timestamp desconocida; colchón de T05 al umbral ilustrativo $2.000 solo **$175**, fees/condiciones de firma no verificadas.
- **Código:** [T08](local_nq_tick_2025_2026/nq_t08_risk_audit.py); [informe](local_nq_tick_2025_2026/NQ_T08_FUNDED_RISK_AUDIT_RESULTS_2026_10_11.md); [Actions 38175102957](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38175102957) **SUCCESS**, tests y siete meses.
- **Decisión:** T05-377 benchmark; ejecutar QC de fuente y orden antes de validación cronológica reservada.

### 2026-10-11 — T09: segunda estrategia distinta y test de cartera NQ

- **Prerregistro:** ruptura acelerada T01 que vuelve dentro del rango en **máx. 60 s** sin exigir slowdown T02; contrastes: continuación original, inversión inmediata, fallo rápido, T05-377 y **router con máximo 2 trades/día compartido, una posición NQ**.
- **Resultado 135 sesiones, siete meses:**

  | Modelo ALTERNATIVO (no sumable) | Neto base | Neto estrés |
  |---|---:|---:|
  | T01 continuación acelerada | −$2.345 | −$3.677,50 |
  | T09 inverso inmediato | −$2.385 | −$4.197,50 |
  | **T09 fallo rápido confirmado** | **+$160** | **−$2.087,50** |
  | T05-377 sin cambios | **+$6.220** | **+$5.102,50** |
  | **T05+T09 portafolio compartido** | **+$3.520** | **+$630** |

- **Comparación primaria congelada:** el portafolio T05+T09 **perdió US$2.700 base / US$4.472,50 estrés** respecto a T05 solo. Aunque ejecutó 170 trades (86 de T05 y 84 de T09), T09 desplazó oportunidades buenas del sistema principal.
- **Decisión:** **T09 FAIL para cartera**; conservar evidencia en biblioteca sin permitir filtrar retrospectivamente oct/ene malos ni seleccionar solo abril favorable.
- **Evidencia:** [informe completo y meses](local_nq_tick_2025_2026/NQ_T09_FAST_TRAP_SEVEN_MONTH_RESULTS_2026_10_11.md), [GitHub Actions 38176029358](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38176029358) **SUCCESS**.

### 2026-10-11 — T10: calidad de cotizaciones de T05 en endpoints de entrada/salida (EN PROCESO)

- **Propósito:** confirmar cuántas de las **115 operaciones congeladas** tienen una cotización **Bid/Ask válida estrictamente anterior** (nunca mismo timestamp) tanto a entrada como salida, con ambas quote sides, spread >0 y edad <=250ms.
- **Alcance:** solo 7 meses T DEV, ambos escenarios de costos T04, paridad exacta con trades/P&L previos; **no** simular fills reales a partir de snapshots BBO.
- **Prerregistro escrito antes de outcomes:** [T10](local_nq_tick_2025_2026/NQ_T10_T05_377_BBO_EXECUTION_QC_PREREG_2026_10_11.md), GitHub commits previos; implementación [nq_t10_t05_bbo_endpoints.py](local_nq_tick_2025_2026/nq_t10_t05_bbo_endpoints.py), tests y [agregador](local_nq_tick_2025_2026/nq_t10_aggregate.py).
- **Ejecución 38176910994:** FALLÓ un test sintético por acceso a campo de contabilidad auxiliar inexistente; corregido antes de outcomes.
- **Ejecución 38176951230:** sintéticos PASS; falló QC de flujo lazy `Bid/Ask` en días sin endpoints/trades. Corregido permitiendo `0` quotes consumidos **únicamente si no hay operación congelada** (no es modificación de señal o fill).
- **Nuevo run al crear esta entrada:** [38177036580](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177036580) **INICIADO/PENDIENTE DE VERIFICACIÓN FINAL**. NO afirmar éxito/resultado de quote matches hasta tener los siete jobs y el agregador final.
- **Decisión:** no cambiar T05 ni los datos H/T; resolver problemas de ingeniería sin suavizar thresholds. **Primer P0 del backlog NQ-B01**.
- **Próximo:** revisar jobs, logs de errores, checksum, recuento de ambos escenarios y reporte BBO por mes; registrar falla o éxito en una NUEVA entrada y actualizar el documento maestro.

### 2026-10-11 — Hito: introducción del manual maestro y backlog recuperable

- **Solicitud del usuario:** mantener un backlog y un MD con **todo el historial de avances, reglas, objetivo, estado y próximo paso**, de manera que una conversación nueva se pueda reanudar sin recordar manualmente las decisiones.
- **Entregables creados:** [NQ_PROJECT_MASTER.md](NQ_PROJECT_MASTER.md) como **fuente central legible y actualizable**, este [NQ_RESEARCH_LOG.md](NQ_RESEARCH_LOG.md) como registro **append-only**, enlaces en README principal.
- **Cambio de metodología de trabajo:** **no cerrar un experimento T/H sin actualizar ambos**; conservar evidencia, fallos y vínculos a GitHub Actions. Recuperar el estado **actual** directamente del último run cuando los archivos estén desfasados. El objetivo **prioritario ahora es la cartera NQ**, no expandir MES/ES ni maximizar el número de hipótesis.

---

## Correcciones y precisión: qué NO significa este registro

- “GitHub Action SUCCESS” indica que el **código corrió y pasaron los checks definidos**, **NO** que la hipótesis/estrategia sea rentable, independiente, robusta o apta para fondeo.
- “PF 1,318 estrés / +$5.102,50” es un **backtest simulado de desarrollo**, NO una cuenta real.
- “Drawdown Last de $1.825” es una **envolvente teórica**, NO una medida de equity broker certificada.
- “Hasta 150 hipótesis” pertenece al programa histórico **H** y se usará solo si las pruebas tienen base causal y presupuesto estadístico; T se registra **separadamente**.
- Nunca sumar netos de **alternativas incompatibles** ni comparar las 115 operaciones T05 contra retornos de otros periodos como si fueran el mismo capital.
- Los resultados de calidad de fuente de mayo–junio de 2026 NO constituyen autorización para revisar outcomes de trading allí.
- Las políticas de holdouts y seguridad prevalecen sobre cualquier texto de una respuesta conversacional que proponga “abrir todo”.

### 2026-10-11 — Corrección de estado T10 tras el arranque de la bitácora

- **Corrección a la entrada T10 anterior:** en el tercer intento [38177036580](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177036580), el trabajo de diciembre falló en una comprobación de fechas: los archivos Last pueden estar ordenados por contrato en vez de por fecha cuando hay rollover. **No se cambió T05 ni sus resultados monetarios.**
- **Corrección técnica:** comparar los conjuntos de fechas ordenados cronológicamente; regresión específica con fechas de contrato en orden diferente. Commits [7a4053b](https://github.com/rgentil2/MES-Trading-Research/commit/7a4053b1fabfd272bfeecaa142dca2ca96f68b85) y [d05114c](https://github.com/rgentil2/MES-Trading-Research/commit/d05114c9574d21d6138f0b2bab199daf29f22568).
- **Nuevo intento:** [T10 run 38177582699](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177582699) lanzado, **todavía sin consolidado final comprobado** al registrar esta entrada. También existe un [trabajo técnico para diciembre y consolidación 38177472643](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177472643); comprobar el resultado real antes de declarar cierre.
- **Decisión:** backlog **NQ-B01 EN CURSO**; falta evidencia consolidada de los siete meses y no hay aprobación para fondeo. Registrar nuevo resultado sin reescribir esta historia.

### 2026-10-11 — NQ-B01 CIERRE REAL T10 y bitácora recuperable (corrección documentada)

- **Objetivo:** cerrar auditoría de los Bid/Ask anteriores en T05-377, sin cambiar señal, costes, periodos ni riesgo, y que otra conversación pueda retomarlo desde GitHub sin preguntar por el historial.
- **Evidencia confirmada posterior al corte anterior del log:** [Action 38177582699](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177582699) terminó **SUCCESS**: 7/7 trabajos mensuales, sintéticos y agregador. Existe [informe final T10](local_nq_tick_2025_2026/NQ_T10_FROZEN_T05_ASOF_BBO_QC_RESULTS_2026_10_11.md). La corrección de ordenación por rollover en diciembre fue técnica; no cambió la estrategia ni los rendimientos y queda registrada en la entrada previa, que NO se borra.
- **Universo:** 2025-10-15 a 2026-04-30, 140 días fuente / 135 elegibles; NQ Last/Bid/Ask DEV privado verificado SHA256; mayo/junio para outcomes y julio/septiembre pseudo-forward no consultados. Programa H 2025/2026 sellado.
- **Resultados:** T05-377 reproduce exactamente **115 trades**, **+$6.220 base** y **+$5.102,50 estrés** (modelos Last hipotéticos). **113/115 (98,26%)** de trades tienen Bid/Ask estrictamente previos, spread positivo, edad <=250 ms en entrada y salida; 2 excepciones de febrero. Un precio hipotético de fill fuera del BBO previo **no** certifica fill ni daño de la fuente debido a las exportaciones con sincronización desconocida.
- **Gates:** ejecución reproductible de auditoría **PASS**; cobertura de pares BBO 100% requerida para gate técnico **FAIL**; ejecución broker, DD real, OOS y fondeo **NO EVALUADOS**. T05 sigue candidato exploratorio, T09 NO entra a la cartera.
- **Actualización maestra:** [NQ_PROJECT_MASTER.md](NQ_PROJECT_MASTER.md), commit [3e4575d](https://github.com/rgentil2/MES-Trading-Research/commit/3e4575d846694c551b036594f04bb110f3f61d79). NQ-B01 COMPLETADO; NQ-B02 EN CURSO. Esta entrada es la corrección de estado frente al resumen T10 anterior, obsoleto.
- **Próximo paso:** NQ-B02 — comparar realmente 240 minutos fuente original independiente NQ 12-25 **2025-10-15** versus ticks Last, sin ZIP multianual en repo público, sin abrir otros outcomes. Si no hay permiso de acceso seguro, reportar bloqueo y documentar alternativa. Mantener NQ-B03/B05 para después.
- **Regla de continuidad aceptada:** al finalizar cada bloque, nueva entrada append-only aquí y estado/backlog corregidos en master, con links a evidencia GitHub Actions. Una ejecución inconclusa nunca se etiqueta «completada».

### 2026-10-11 — NQ-B02: primera conciliación REAL de archivos Minute y Tick NQ (PASS 240/240)

- **Objetivo:** verificar integridad cruzada de la fuente `NQ 12-25` por minuto originalmente exportada y archivada por separado frente a `NQ Tick Last`, para el **único día preseleccionado** 2025-10-15, antes de estudiar más mecanismos T o validar fills. B01/T10 ya estaba cerrado.
- **Prerregistro:** [NQ_B02_CROSS_SOURCE_PILOT_2026_10_11.md](local_nq_tick_2025_2026/NQ_B02_CROSS_SOURCE_PILOT_2026_10_11.md), commit `e603733e4ae81a618590bca7622c40a5a477fcdf`, antes de leer los resultados. Contrato NQ 12-25, 08:00–12:00 ET ticks, minuto original etiquetado FIN 08:01–12:00 ET (240 barras).
- **Fuentes independientes de ARCHIVO, NO de proveedor:** `rgentil2/NQ-Tick-Data` privado para ZIP minuto histórico, `rgentil2/NQ-Ticks-Dev-2026` privado para Last de octubre 2025. Ambos son exportaciones históricas NinjaTrader, no feeds diferentes.
- **Integridad/seguridad:** ZIP original minuto privado de 65.405.000 bytes SHA256 `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8` verificado; procesado SOLO un miembro NQ 12-25 y SOLO registros del 15-oct-2025, sin copiar ZIP a público ni mirar P&L/estrategias H. Tick Last archive DEV octubre checksum verificado y solo fecha seleccionada extraída. Ningún archivo/trade/precio individual revelado; `NQ-Ticks-Sealed` jamás abierto.
- **Código y commits:** privado `tools/nq_minute_single_day_digest.py` `efbe5ee959c954152f97fea0a80a04cfb2354e73`, workflow privado `138745fd06028dda18b3e6ffe5f60e1275ca82af`; público [nq_b02_tick_single_day_digest.py](local_nq_tick_2025_2026/nq_b02_tick_single_day_digest.py) `40284861df8af7ff3eb0c6f724676dae67bd8ee3`, tests `9f0f683a2de2b3450fc28e517137f063d1fda5bc`, workflow existente extendido `0431962d0f2f5a3a9bb8e0eca6811564f474b4e7`.
- **GitHub Actions comprobados:** [MINUTO original run **38179138403**](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/38179138403) **SUCCESS**; [TICK DEV run **38179259265**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38179259265) **SUCCESS** (job relevante `source-last (2025-10-15)`; demás trabajos de QC también SUCCESS). Logs revisados y hashes cotejados literalmente.
- **Resultado fuente Minute:** **240 barras**, volumen **262.422**, SHA256 canónico `f6c426c60d5691ddd8341db2c1bcf9f944b283d8533497f0d4efdd11e82afb5a`.
- **Resultado fuente Tick Last:** **240 barras**, volumen **262.422**, SHA256 canónico **idéntico** `f6c426c60d5691ddd8341db2c1bcf9f944b283d8533497f0d4efdd11e82afb5a`.
- **Decisión:** **NQ-B02 PILOTO COMPLETADO / MATCH EXACTO 240/240 OHLCV** con el mismo contrato, ET/DST y etiquetado. Esto supera las 34 pruebas sintéticas previas porque compara **fuentes históricas reales**. **NO prueba continuidad en otros contratos/días, ejecución/BBO, P&L adicional, OOS ni aprobación de fondeo.**
- **Informe de resultado:** [NQ_B02_INDEPENDENT_MINUTE_TICK_MATCH_RESULTS_2026_10_11.md](local_nq_tick_2025_2026/NQ_B02_INDEPENDENT_MINUTE_TICK_MATCH_RESULTS_2026_10_11.md), commit `0c95e96852d2c89f1e713f0ed6cecc0607670488`.
- **Master actualizado:** [NQ_PROJECT_MASTER.md](NQ_PROJECT_MASTER.md), commit `4393e98a970b8c2b9593e4a213fb655d666872c9`, B02 COMPLETADO, B03 siguiente.
- **Próximo paso:** NQ-B03 — ingeniería de secuencia Last/Bid/Ask y estimación de ejecución adversa sin contar quotes snapshot como fills garantizados. Después NQ-B05 — otra fuente real de ventaja incremental para portafolio NQ, con hipótesis preregistrada, comparadores, riesgo compartido, control estadístico y todos los meses negativos. B12 opcional para QC de rollovers por fechas predeclaradas.
- **Corrección a entrada B02 anterior del master:** el texto anterior decía «no se ha ejecutado»; queda reemplazado en estado maestro por **PASS de 1 día**, sin borrar resultados históricos ni cambiar holdouts.

### 2026-10-11 — NQ-B03 CIERRE, fragilidad real del modelo de costes y corrección cronológica T08

- **Objeto:** medir el margen de T05-377 ante recargos de ejecución sin retocar ninguna señal, y verificar posible error de ordenación de fechas ET descubierto al inspeccionar el motor T08. **No es nueva hipótesis de alpha**.
- **Prerregistro ANTES de resultados:** [NQ_B03_HEADROOM_PREREG_2026_10_11.md](local_nq_tick_2025_2026/NQ_B03_HEADROOM_PREREG_2026_10_11.md), commit `4e26f27f2864a7003cec237ed91cd0ddacd6f61c`. Por adelantado se fijaron los DOS escenarios originales y CUATRO recargos de **$0/$10/$20/$40 por round-trip** (0,1,2,4 ticks adversos adicionales por lado), ocho alternativas de contabilidad sobre rutas congeladas.
- **Universo y privacidad:** NQ Last mensual de `rgentil2/NQ-Ticks-Dev-2026`, SHA256 de archivos privados verificado; solo 2025-10 a 2026-04, **140 días fuente / 135 elegibles**, 115 trades congelados; sin lectura de resultados mayo–junio 2026 ni reserva julio–septiembre 2026 ni programa H sellado.
- **Código:** [nq_b03_execution_headroom.py](local_nq_tick_2025_2026/nq_b03_execution_headroom.py), commit `4d6a6f09c0bdaca3efa2507bbf0ade1a6af8a504`; [nq_b03_aggregate.py](local_nq_tick_2025_2026/nq_b03_aggregate.py), commit `01cc7b05bb983fbdb8fe94469405f9e35bb8a62e`; [tests sintéticos](local_nq_tick_2025_2026/test_nq_b03_execution_headroom.py), commit `e573fb552c40a0242523a2d518995d6fc764b56c`; [workflow](.github/workflows/nq-b03-t05-headroom-dev.yml), commit `e00dece6b6753ba41a0ecfa558498c26f985bfc9`.
- **Ejecución real:** [GitHub Actions 38179855851](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38179855851) **COMPLETED SUCCESS** — siete jobs mensuales, tests regresión T08 y sintéticos B03, agregador SUCCESS; artifact `b03-seven-month-safe-summary` con informe y JSON solo agregado; referencia de origen comprobada.
- **Paridad:** mismos **115 trades**, neto sin recargos **+$6.220 baseline** y **+$5.102,50 estrés**. Nada se eligió o descartó basado en retornos. Los stops, TP, horarios, ocupación de capital y daily stops **NO se recalculan** ante recargo; son resultados de ruta fija de Last.
- **Resultado completo (modelo / recargo por trade / P&L USD / PF / DD Last-envelope USD):**
  
  | Alternativa | Recargo RT | Neto USD | PF contable | DD Last continuo |
  |---|---:|---:|---:|---:|
  | Base | $0 | +6.220 | 1,39923 | 1.725 |
  | Base +1 tick/lado | $10 | +5.070 | 1,31277 | 1.815 |
  | Base +2 ticks/lado | $20 | +3.920 | 1,23278 | 1.905 |
  | Base +4 ticks/lado | $40 | +1.620 | 1,08940 | 2.085 |
  | Estrés | $0 | +5.102,50 | 1,31826 | 1.797,50 |
  | Estrés +1 tick/lado | $10 | +3.952,50 | **1,23717** | 1.887,50 |
  | Estrés +2 ticks/lado | $20 | +2.802,50 | 1,16195 | 1.977,50 |
  | Estrés +4 ticks/lado | $40 | +502,50 | 1,02699 | **2.157,50** |

- **Hallazgo técnico de orden cronológico:** T08 original publicó DD Last **$1.750 base / $1.825 estrés**. B03, recorriendo días ET en orden real `sorted(month_days(...))`, registró DD de **$1.725 base / $1.797,50 estrés**, diferencia descriptiva **−$25/−$27,50** con las MISMAS transacciones y método de marcas. Esta es una **corrección de auditoría**, no mejor rendimiento operativo. El T08 previo se conserva sin borrar ni editar.
- **Gates y significado:** estrés +1 tick adicional por lado (solo $10 RT) ya baja **PF 1,31826→1,23717**, FALLA pantalla exploratoria 1,25. Estrés +4 ticks adicionales por lado lleva DD $2.157,50, mayor que referencia **histórica/no verificada** $2.000. Estos recargos NO certifican fills ni son cota garantizada broker; los snapshots BBO de T10 y la paridad OHLCV de B02 tampoco certifican ejecución real.
- **Decisión:** `NQ-B03 COMPLETADO_DIAGNOSTICO`, `T05_377_COST_FRAGILE_EXPLORATORY`, NO aprobado fondeo/OOS. Mantener T09 fuera de cartera (falló incremental); no filtrar febrero ni reoptimizar stops para salvar PF.
- **Informe definitivo:** [NQ_B03_T05_EXECUTION_HEADROOM_RESULTS_2026_10_11.md](local_nq_tick_2025_2026/NQ_B03_T05_EXECUTION_HEADROOM_RESULTS_2026_10_11.md), commit `8fbacd6529c29cace25fdfaeddf420f38d4f0595`.
- **Master actualizado:** [NQ_PROJECT_MASTER.md](NQ_PROJECT_MASTER.md), commit `e1a33d99cabffbe6cd8a68aae9c92601b3b40763`.
- **Próximo paso:** **NQ-B04** estabilidad semana→diagnóstico, mes→diagnóstico, trimestre/semestre→evaluación, régimen causal→interpretación de fragilidad, a partir de mismos siete meses y coste fijo declarado; después **NQ-B05/B06** segunda estrategia realmente independiente, portfolio/router con riesgo compartido y eventual OOS con puertas formales. Los datos/artefactos quedan enlazados para reanudar conversación nueva.

### 2026-10-11 — NQ-B04, cierre real de robustez temporal T05 (29 semanas / 7 meses)

- **Objetivo:** descomponer temporalmente la misma cartera T05-377 ya explorada y determinar si los recargos de B03 desplazan el riesgo a semanas/meses concretos, **sin cambiar ningún trade ni seleccionar meses para un futuro filtro**.
- **Prerregistro y timing:** [protocolo B04](local_nq_tick_2025_2026/NQ_B04_TEMPORAL_ROBUSTNESS_PREREG_2026_10_11.md), commit `2c40e09dc53e564a8b083e109b08d5d3b7ccef40`, ANTES de ver outputs B04: semanas ISO ET lunes–domingo, 7 meses, Q4-2025 desde 15-oct parcial, Q1-2026 completo y Q2-2026 únicamente abril, y escenarios base, estrés, estrés+$10/RT. No se optimizó un nuevo periodo o parámetro.
- **Datos:** solo NQ Tick Last en `NQ-Ticks-Dev-2026` octubre 2025–abril 2026, archivado privado y verificado SHA256. 140 días fuente, 135 elegibles. 2025/2026 histórico H separado; outcomes mayo–junio T y julio–septiembre T **NO ABIERTOS**.
- **Código/versiones:** [nq_b04_temporal_month.py](local_nq_tick_2025_2026/nq_b04_temporal_month.py) commit `9f9f359853e120fa41d4674865723f96446a5673`, comparación contra campos compartidos T04/T10 corregida técnicamente `0484e12eb7c4affefb53d69a8f8a636dba05fadf`; [agregador](local_nq_tick_2025_2026/nq_b04_temporal_aggregate.py) commit `1d6aea3a2d0c5eb52f10e2db12c56636a595f04a`; [tests sintéticos](local_nq_tick_2025_2026/test_nq_b04_temporal_robustness.py) commit `7e4cd60681d682b09e5e768b5bc87fd986e5b170`; [workflow](.github/workflows/nq-b04-temporal-dev.yml) commit `bf07fc2d5bb372bd9fb2974b10793c47d50353ca`.
- **Ejecución comprobada:** [GitHub Actions **38180451505**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38180451505) **COMPLETED SUCCESS** 7/7 meses y agregador. Artifact `b04-seven-month-temporal-summary` (JSON+Markdown seguro) inspeccionado; 115 trades en cada escenario, resultados T04/B03 originales replicados exactamente.
- **Resultado agregado:**

  | Escenario T05 | P&L Last teórico | PF | Meses positivos | Semanas positivas/activas | Semanas negativas | Peor semana | Top3 semanas positivas / total positivo |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | Base | +$6.220 | 1,39923 | 6/7 | 17/29 | 12 | −$795 | 31,96% |
  | Estrés original | +$5.102,50 | 1,31826 | 6/7 | **16/29** | **13** | −$822,50 | 33,25% |
  | Estrés +$10 RT | +$3.952,50 | **1,23717** | **5/7** | 16/29 | 13 | −$852,50 | 34,59% |

- **Diagnóstico meses estrés original:** Oct +$137,50 (15 operaciones), Nov +$760 (8), Dic +$1.450 (22), Ene +$1.572,50 (19), **Feb −$827,50** (13), Mar +$1.372,50 (21), Abr +$637,50 (17). **Estrés +$10 RT:** Oct **−$12,50**, Nov +$680, Dic +$1.230, Ene +$1.382,50, **Feb −$957,50**, Mar +$1.162,50, Abr +$467,50. Nada se excluyó.
- **Trimestres:** Q4-2025 **parcial desde 15-oct** estrés +$2.347,50 / estrés+$10 +$1.897,50; Q1-2026 completo +$2.117,50 / +$1.587,50; Q2-2026 **solo abril** +$637,50 / +$467,50. No decir «tres trimestres completos», no usar CAGR inferido.
- **Gates:** prueba de ejecución ingenieril **PASS**; paridad 115 trades/siete meses **PASS**; **robustez multianual/OOS NO EVALUADA**; sensibilidad a +$10/RT deja PF **<1,25** (pantalla exploratoria FAIL). 16 semanas positivas vs 13 negativas bajo estrés: **NO describir como más semanas negativas que positivas**. 3 semanas explican ~33% de ganancias semanales positivas, cifra descriptiva sin benchmark de concentración. Aún no hay ejecutabilidad ni RR de broker demostrados.
- **Decisión:** `B04_COMPLETE_DESCRIPTIVE_ONLY`, T05 permanece benchmark exploratorio con **febrero adverso en todos los escenarios** y octubre con pérdida si recargo+$10; prohíbase recortar meses retrospectivamente o llamar OOS a particiones ya exploradas. Meta cartera >max(15% VOO-TR QQQM-TR) no probada.
- **Informe definitivo:** [NQ_B04_TEMPORAL_ROBUSTNESS_RESULTS_2026_10_11.md](local_nq_tick_2025_2026/NQ_B04_TEMPORAL_ROBUSTNESS_RESULTS_2026_10_11.md), commit `772f307a62341fe4b73d757d05891f7ce83a8ab8`; [master actualizado](NQ_PROJECT_MASTER.md), commit `61747257cc50b8d34b80b209399fd9d6a95e381d`, también actualiza DD stale de T08 con valor cronológico corregido B03.
- **Próximo:** **NQ-B05**, diseñar una segunda estrategia NQ ejecutable de mecanismo distinto (preferencia de investigación: aceptación VWAP + pullback direccional con actividad causal, no otro filtro para T05/T09), con ablations y router único T05, incluir recargo estresado y pérdidas mensuales sin filtrar; recién B06 estudiar aportación incremental. No abrir OOS antes del gate.
