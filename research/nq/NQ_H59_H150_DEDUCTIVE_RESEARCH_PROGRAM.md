# Programa NQ H59–H150 — investigación deductiva de estrategias conjuntas

Estado: plan de investigación. **H59–H66, H67–H72 y H73–H78 ya se registraron y evaluaron; H79–H150 no están preregistradas.** A partir de H67, la unidad principal será **una estrategia/hipótesis conjunta** con dos o más componentes funcionales distintos y una predicción incremental falsable contra sus padres y la cartera de referencia, no una señal individual. Las definiciones futuras surgirán de diagnósticos anteriores y quedarán congeladas antes de leer nuevos outcomes.

## Punto de partida: 58 hipótesis numeradas, no 58 ensayos independientes

Se observaron 2020–2024 repetidas veces. El conjunto de pruebas no produce evidencia out-of-sample. Las ventanas 2025 y 2026 siguen selladas. H09, H29, H36, H54, H55 y H56 permanecen en la biblioteca, además de H02 y otras señales exploratorias. Cada candidato incluye origen, regla de señal, regla de salida, estado de la prueba, costes, frecuencia, correlaciones y solapamientos. No se borra un candidato por fallar un gate; se restringe su **autoridad**.

## Decisión metodológica 2026-10-10 — COMBINACIONES + APRENDIZAJE ACUMULATIVO

**Dos cambios obligatorios para H67–H150:**
1. **Evaluar sistemas conjuntos desde la formulación:** una H67+ será una regla causal de coordinación de componentes (señal + contexto ex ante, confirmación, veto, regla de cambio de régimen o router multiseñal). Debe especificar sin ambigüedad condiciones AND/OR, prioridad, resolución de conflictos, entrada, exposición no duplicada, sizing, salida/SL/TP y costes. No se exige simultaneidad de todas las señales: también se admiten sistemas que cambian de componente según el estado del mercado. Las señales anteriores quedan como **componentes**, no se descartan. Un nuevo patrón individual puede examinarse como diagnóstico pero no cuenta como nueva H67+ de estrategia sin una decisión compuesta.
2. **Deductivo, no aleatorio:** antes de registrar cada combinación, citar la observación y resultados de su(s) padre(s) (N, años, incertidumbre, defectos y concentración), proponer una explicación causal y **predecir una mejora incremental** contra cada componente y un comparador de cartera con las mismas fechas, tamaño, costes y riesgo. Registrar ablation `leave-one-component-out`, hipótesis nula, controles complementarios y condiciones explícitas de falsación.

**Ejemplo informativo — no ejecutado ni preregistrado:** combinar la señal H09 de continuación del gap con una condición de volatilidad preapertura conocida antes de entrar, y compararla contra H09 sin filtro (mismo riesgo), otras señales por separado y el mismo router sin esa condición. Otro ejemplo: tratar H55+H56 como **consenso único**, no como dos contratos independientes, y examinar su contribución a un sistema que también considere H09. Los 67 días compartidos por H55/H56 y la concentración de H09 en 2022 son hallazgos **de desarrollo ya observados**, no pruebas de ventaja futura.

**Pruebas comparativas obligatorias:** cada combinación debe informar el incremento real en P&L y CAGR, PF, frecuencia, exposición, drawdown flotante/cerrado, estrés a 1.5× costes, ingresos por período y beneficio frente a eliminar cada componente; no atribuir mejoras a seleccionar menos operaciones o mayor leverage. Corregir todas las variantes dentro de la familia; 2020–2024 sigue siendo **exploratorio**, aun con una aparente mejora.

**Documento rector:** `research/nq/NQ_DEDUCTIVE_ENSEMBLE_POLICY_2026_10_10.md` y `research/nq/NQ_DEDUCTIVE_ENSEMBLE_POLICY_2026_10_10.json`. No cambia el Gate 1 original ni se abre 2025/2026.

## Secuencia de investigación

1. **Hallazgo previo:** referenciar padres, N, años, intervalos, q, correlación y fallos; incluir lo que **no** funcionó.
2. **Explicación causal y combinación:** plantear por qué coordinar 2+ componentes puede aportar ventaja, evitar conflictos o diversificar exposición.
3. **Predicción incremental falsable:** declarar condición ex ante, reglas completas de router/AND/OR/consenso/veto y comparación contra componentes + cartera base, con ablation predefinida.
4. **Registro previo y tests sintéticos:** congelar familia completa, variantes, comparadores, fuente y costes, preservando el presupuesto Holm y BH sin reciclar alfa.
5. **Diagnóstico 2020–2024 de la decisión conjunta:** resultados netos y sensibilidad temporal, IC y q (Gate 1 original intacto), pero sin tratar años reutilizados como replicación independiente.
6. **Backtest ejecutable de la combinación:** stops, TP, límite temporal, contrato real, sizing y ejecución causales **fijados antes de medir**; no seleccionar retrospectivamente parámetros ganadores.
7. **Ablation y cartera:** confrontar combinación con cada padre y versiones sin cada bloque; unificar duplicados, exposición y máximo una posición por regla de router congelada; evaluar frecuencia, concentración, drawdown cerrado y flotante.
8. **Gate económico prospectivo:** CAGR neto conjunto > mayor entre **15 % anual y retornos totales de VOO/QQQM** con fechas iguales, más 1.5× costes, riesgos ajustados, restricciones reales de fondeo y retorno de bolsillo por separado. Si faltan series o auditoría, `ECONOMIC_DATA_PENDING`.
9. **Actualizar banco de aprendizaje:** incorporar evidencia favorable/adversa, contribución marginal, interacciones, errores y límites de conocimiento; no borrar señales por fallar individualmente.
10. **Confirmación:** 2025 sellado hasta aprobación explícita de un candidato **completo y congelado**; 2026 para pseudo-forward posterior sin ajustes.

## Nuevo objetivo de rentabilidad económica (aprobado 2026-10-10)

Además de medir si las hipótesis tienen un efecto estadístico, **cada estrategia o cartera** debe aspirar a superar **estrictamente** el mayor de: (i) **15 % de CAGR neto anual**, (ii) CAGR por retorno total de **VOO**, y (iii) CAGR por retorno total de **QQQM**, calculados sobre la misma ventana temporal, en USD y con dividendos reinvertidos. El **12 % es una referencia diagnóstica**, no un pase del gate. La prueba económica no se aplica como filtro retroactivo que elimine H01-H66 ni reescribe sus conclusiones.

- **Ventana primaria 2020–2024 comparable con QQQM:** desde el **13-10-2020 o posterior** hasta una misma última fecha disponible en 2024. QQQM no existía antes; para estudiar 2020 completo se puede usar **QQQ como proxy etiquetado**, nunca como QQQM real.
- **Capital de referencia USD 50.000:** su CAGR equivalente sirve solo para normalizar una curva de estrategia; una cuenta fondeada **no** equivale a haber invertido personalmente USD 50.000. Presentar también el retorno monetario real sobre evaluaciones/fees/resets y payouts, usando flujos fechados/XIRR cuando corresponda.
- **Costes y supervivencia:** desglosar NinjaTrader Free frente a costes reales de la firma elegida, hacer estrés 1.5×, comprobar drawdown de cierres **y flotante**, restricciones MFFU, riesgo correlacionado y retornos ajustados por riesgo frente a ETF. Ningún CAGR alto aprueba por sí solo.
- **Señales conservadas:** H09, H29, H36, H44, H45, H54, H55, H56 y demás quedan en el banco exploratorio incluso si fracasan individualmente. El gate económico califica **carteras completas congeladas**, no borra hipótesis.
- **Estados:** `ECONOMIC_DATA_PENDING` si faltan ETF/curva/costes; `BELOW_ECONOMIC_HURDLE` si no vence al mayor; `ECONOMIC_HURDLE_MET_RISK_PENDING` si sí vence pero falta riesgo; `PROMISING_PORTFOLIO_EXPLORATORY` únicamente si desarrollo económico y controles de riesgo son satisfactorios (no validación OOS).
- **Evidencia intacta:** Gate 1 y gates confirmatorios Holm originales no cambian, ni 2025/2026 se abren por una comparación de CAGR.

**Documento rector del nuevo Gate:** `research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.md`; especificación legible por software: `research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.json`.

## Primera ronda de estrategias conjuntas completada (2026-10-10): H67–H72

Se congeló oficialmente la familia **`NQ-DEDUCTIVE-ENSEMBLE-H67-H72-V1` (índice 6, α=0.00119047619)** y se corrieron seis routers de un contrato MNQ hipotético sobre precios NQ minuto 2020–2024, una operación máxima por sesión, SL 0.15 rango mediano previo, TP 1.5R, salida 30min. Se probó contra padres y se registraron ablations. Auditoría oficial: sin respaldos formales, 15 tests sintéticos correctos. **No se abrieron 2025/2026.**

Hallazgos acumulativos:
- H67 (H09 OR consenso H55/H56): 239 operaciones, net +$2205.18 MNQ, PF1.295, q=.115, 4/5 años positivos. El consenso añade $130.92 respecto a H09-only.
- H69 (H09 OR H56): 262 operaciones, net +$2704.44 MNQ, PF1.335, q=.115, 4/5 positivos, DD cerrado $890.64. H56 aporta $630.18 respecto a H09-only; **no** supera Gate 1 ni el hurdle 15% (CAGR nominal de $50k ~1.06%). Conservar exploratoriamente.
- H68 (H09 OR H55) pierde $210.50 de contribución incremental de H55 sobre H09-only; H70 fallback H29 pierde $576.70; H71 fallback H54 pierde $4129.06 y aumenta a 1051 operaciones; H72 régimen simple vuelve a perder.
- **Deducción para H73–H78 (ideas, NO tests aún):** investigar qué estado ex ante explica la mejora asociada a H56 sin convertir el filtro en rescate retrospectivo; estudiar por qué la entrada fallback H54 aumenta la frecuencia pero empeora la rentabilidad; verificar primero transferencia MNQ/NQ y costes de ejecución. Los próximos miembros deberán definirse como **estrategias compuestas**, con comparadores y condiciones de falsación, y registrarse **antes** de resultados.

Reportes: `research/nq/NQ_H67_H72_RESULTS_2020_2024.md` y `results/nq_h67_h72/NQ_H67_H72_REPORT_2020_2024.json`. Condiciones económicas `research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.md`.

## Nuevo paso prioritario — estudiar microestructura NQ Tick antes de H79 (2026-10-10)

A partir de los hallazgos **H09, H56, H69, H74 y H77**, decidimos evaluar **datos tick reales** de NQ para estudiar si la **entrada antes del cierre de 09:45 ET**, la confirmación de flujo y un **stop técnico más estrecho** mejoran el resultado por unidad de riesgo. La mayor resolución **no garantiza** ejecuciones mejores: puede aumentar falsos positivos, stopouts, spread, slippage y sensibilidad al coste.

**Etapa previa no numerada:** auditoría de disponibilidad, timestamps y derechos de una muestra **NQ 03-24 Tick Last** (idealmente Bid y Ask auténticos), pilotaje de **2024-02-05 a 2024-02-16 ET, 08:30–11:30**, sin elegir días por rentabilidad. Verificar resolución subsegundo, contrato, UTC/ET, cobertura y reconstrucción de velas versus Minute Last original. Herramienta `research/nq/nq_tick_pilot_qc.py`, pruebas `research/nq/test_nq_tick_pilot_qc.py`. **Sin archivos NQ Tick Last/Bid/Ask aún disponibles, no se ejecutan ganancias nuevas.**

**Dos investigaciones separadas:**
1. **Ejecución de estrategias congeladas a igual señal 09:45:** ticks solo para resolver orden de stop/TP, MFE/MAE, spread y flotación; no es un hallazgo de señal nueva.
2. **Entrada anticipada H79+ preregistrada:** H09/H56 + condición causal formada con ticks **conocidos al instante de entrar** + reglas de confirmación/veto y stops estructurales; comparar contra H69/H74/H77 con misma base de riesgo y ablation. A las 09:35 **no se conoce el cierre de 09:45**. Si solo hay Last, no inferir Bid/Ask ni delta agresor.

La siguiente familia H79–H90 continúa **NO preregistrada** hasta verificar calidad/acceso y especificar completa la variante conjunta. Ninguna conclusión sobre 2025/2026; ambos holdouts siguen sellados. Publicar únicamente código y estadísticas agregadas porque el GitHub es público; los ticks originales quedan privados.

**Documento rector:** `research/nq/NQ_TICK_EXECUTION_FEASIBILITY_PROTOCOL_2026_10_10.md`.

## Cambio de enfoque — NQ primero, mantener MNQ como instrumento de ajuste de riesgo (2026-10-10)

A petición del usuario, el objetivo principal para **las familias nuevas desde H79** es diseñar sistemas conjuntos ejecutables con **1 NQ como escenario principal** (US$20 por punto) y costes/órdenes específicos del NQ. MNQ (US$2 por punto) **permanece** como alternativa de tamaño cuando el NQ incumpla el riesgo por operación, y como comparador a iguales supuestos. El cambio no modifica el código, señales, reglas, resultados ni hashes de H01–H78.

**Contraste realizado con los mismos trades ya congelados** (NQ Minute Last como proxy; datos de desarrollo 2020–2024, sin nueva inferencia):
- H69 1 NQ: beneficio US$30,466.12 en cinco años, CAGR nominal equivalente sobre USD50k **9.98%**, DD cerrado **US$8,214.22**.
- H74 1 NQ: US$18,302.32, CAGR **6.44%**, DD cerrado **US$4,179.80**.
- H77 1 NQ: US$25,681.40, CAGR **8.64%**, DD cerrado **US$5,414.42**.
- Los siete sistemas reescalados a un contrato NQ **fallan tanto la meta 15% como el colchón ilustrativo USD2k de pérdida cerrada**. El trailing sobre equity flotante no ha sido validado; futuros mini amplifican también pérdidas. No confundir el capital nominal 50k con capital propio invertido.

Para cada nuevo sistema conjunto, antes de outcomes especificar **riesgo máximo permitido por operación en USD**, stop NQ en puntos, costes NQ reales, router causal, SL/TP, política de conflicto, sizing y drawdown flotante; detener una variante si **1 NQ supera su límite de riesgo**. Comparar valor incremental y ablation frente a padres en igual riesgo. No aprobar por escalamiento de tamaño ni retocar stops retroactivamente.

**Documentos:** `research/nq/NQ_FIRST_EXECUTION_POLICY_2026_10_10.md` y `research/nq/NQ_VS_MNQ_EXECUTION_TRANSFER_DIAGNOSTIC_2020_2024.md`.

## H73–H78 completada (familia 7) — nuevas evidencias para H79–H90

Prerregistro y código de seis routers conjuntos congelados, 17 tests sintéticos correctos, corrección de familia. Compararon **H09+H56** eligiendo por: rango RTH anterior (H73/H74), compresión premercado (H75/H76) o alineación gap/impulso premercado (H77/H78). Ninguna mejoró el P&L total del comparador H69 (+US$2,704.44 en 1 MNQ); **ninguna supera Gate 1**.

H74 logró cinco años positivos pero solo N132 y q0.1149. H77 presentó PF1.632 con N140 y q0.0468 e IC90>0, pero **falla N>150**, no mejora H69 y concentra ~75% de sus ganancias en 2022. En transferencia teórica a NQ su DD cerrado excede el colchón de fondeo.

**Deducción para H79–H90:** no seguir segmentando retrospectivamente los mismos años para forzar frecuencia o PF. Investigar mecanismos de **riesgo por operación, gestión causal de posiciones e información complementaria real** al sistema H09+H56 (p. ej. validación cruzada ES/NQ si se sincronizan datos). Las nuevas hipótesis deben ser **conjuntas y definidas desde el principio para NQ**, comparar su contribución al sistema base bajo riesgo equivalente y congelarse formalmente antes de ver nuevos resultados.

Reporte: `research/nq/NQ_H73_H78_RESULTS_2020_2024.md`. H79–H150 son todavía **ideas, no tests preregistrados**.

## Hasta H150: combinaciones hipotéticas, no señales individuales independientes

El bloque H59–H66 quedó evaluado como interacciones. **H79–H150 son cupos máximos para hipótesis conjuntas nuevas; H67–H78 ya ejecutadas:** cada ID debe expresar una decisión coordinada distinta y estar motivado por evidencia acumulada. Si no hay mecanismo o datos, se dejará sin ejecutar en vez de fabricar una prueba. Los rangos siguientes son líneas de trabajo, no familias ya congeladas.

## Presupuesto máximo de 92 hipótesis adicionales (objetivo H150)

| Fase | IDs previstos | Conteo | Pregunta deductiva, a ajustar según pruebas anteriores |
|---|---|---:|---|
| 1 | H59–H66 | 8 | ¿Las coincidencias y la exclusividad de H09/H29/H54/H55/H56 alteran la expectativa, duplican riesgo o agregan información? |
| 2 | H67–H78 (12/12 probadas, sin confirmación) | 12 | **Sistemas combinados:** H09 + régimen ex ante + veto/consenso H55/H56, con router causal y ablation frente a padres para explicar la concentración de H09 sin seleccionar años retrospectivamente. |
| 3 | H79–H90 (NQ Tick Last/Bid/Ask factibilidad pendiente) | 12 | **Carteras conjuntas con entrada intraminuto y riesgo del NQ:** consenso H55/H56 y alternativa H09/H36 según régimen de volatilidad observable antes de la orden; medir valor añadido de cada bloque y frecuencia. |
| 4 | H91–H102 | 12 | **Confirmación o veto ES–NQ:** incorporar relaciones causales entre índices a las señales NQ previas, solo con fuente ES sincronizada y validada; comparar sistemas con/sin señal intermercado. |
| 5 | H103–H114 | 12 | **Router aceptación/rechazo:** combinar H53/H54/H05/H07 con filtros ex ante y elección mutuamente excluyente de ruptura o reversión; contrastar alternativa conjunta vs cada señal. |
| 6 | H115–H126 | 12 | **Sistemas multianclaje VWAP:** combinar H55 con apertura, niveles y participación para gobernar entrada/veto/salida; ablation por cada anclaje y control sin VWAP. |
| 7 | H127–H138 | 12 | **Sistemas existentes + microestructura** como confirmación/veto de H09/H55/H56, **solo** si Tick Last/Bid/Ask reales y calidad están verificados; nunca simular flujo de órdenes a partir de minuto. |
| 8 | H139–H150 | 12 | **Carteras multicomponente:** combinar componentes distintos mediante router, exposición y riesgo ex ante; ablation completa, compatibilidad fondeo y Gate Económico con benchmarks. |
| **Total** | **H59–H150** | **92** | No se obliga a ejecutar una fase si no hay datos o mecanismo defendible; 150 es techo, no una cuota de p-hacking. |

## Hipótesis heredadas, no descartadas

H09 (gap continuation), H29 (reversión de impulso corto, muy baja N), H36 (reversión apertura), H55 (acercamiento VWAP nocturno), H56 (reversión premercado), H54 (ruptura premercado, casi neutra); H02 (ruptura fallida) y H05 (barrida high/low con contaminación de rollover) se conservan para auditoría/cartera. H44/H45 (N muy pequeñas) y H57 se conservan como pistas, no como estrategias validadas. La biblioteca registra estado y nunca borra métricas adversas.

## Riesgos de inferencia y derechos de datos

- H59–H66 son **derivaciones explícitas de resultados ya observados**; sus intervalos y p-values dentro de 2020–2024 son descriptivos, no descubrimientos independientes.
- Las pruebas con pocas señales conservan q y N como fallos; no se les fabrican más datos por correlación de índices (MES/ES y MNQ/NQ no son réplicas independientes).
- No depositar en un GitHub **público** ni los ZIP brutos de NinjaTrader ni el registro individual de operaciones, si su redistribución no está verificada.
- Los presupuestos de alfa para futuras familias los determinará `research_governance.py` al momento del preregistro, respetando el historial; no ampliar/quitar miembros después de observar resultados.

## Rama independiente para scalping 2026 — pseudo-forward histórico offline

**Nuevo permiso del usuario (2026-10-10) limitado a investigación tick/scalping NQ**, sin alterar H01–H78 ni sus holdouts: **enero–abril 2026** para desarrollo, **mayo–junio** para validación interna (reutilizable, no OOS final) y **julio–septiembre 2026** reservado como **único pseudo-forward histórico offline**. Octubre–diciembre 2026 y 2025 quedan fuera; 2026 sigue sellado para el programa histórico de minutos, aunque la nueva rama sí permite enero–junio.

Solo si datos de cobertura sin precios muestran falta objetiva de disponibilidad se permite **una reducción previa** a agosto–septiembre o septiembre, siempre antes de observar retornos. No utilizar el comportamiento de las estrategias para escoger el test. Enfocar las nuevas hipótesis en estrategias **conjuntas NQ** derivadas de hallazgos previos, con stops/take profit, orden de ejecución y contratos congelados antes de una sola apertura final. El pseudo-forward de 1–3 meses no valida por sí solo un CAGR sostenible del 15% anual.

**Regla concreta:** `research/nq/NQ_TICK_SCALPING_2026_OFFLINE_PSEUDO_FORWARD_POLICY_2026_10_10.md`. No implica descarga de mercado ya realizada ni que ticks de 2026 estén disponibles.
