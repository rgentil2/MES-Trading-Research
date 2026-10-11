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
