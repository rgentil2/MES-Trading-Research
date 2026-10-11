# NQ — DOCUMENTO MAESTRO DE INVESTIGACIÓN, REGLAS Y BACKLOG

> **LEE ESTE DOCUMENTO PRIMERO AL INICIAR CUALQUIER CONVERSACIÓN SOBRE NQ.**
>
> **Última revisión documental:** 2026-10-11 (America/Bogota).
> **Alcance activo:** EXCLUSIVAMENTE NQ/MNQ. MES/ES queda en pausa por decisión del usuario.
> **Estado general:** investigación retrospectiva exploratoria; **NINGUNA ESTRATEGIA NI CARTERA ESTÁ VALIDADA PARA OPERAR O COMPRAR FONDEO**.
> **Fuente de verdad:** este archivo para reglas/objetivos/decisiones; [NQ_RESEARCH_LOG.md](NQ_RESEARCH_LOG.md) para el historial cronológico; prerregistros, código, artefactos y GitHub Actions para los resultados reproducibles.
> **Mantenimiento obligatorio:** al finalizar CADA bloque de investigación, actualizar aquí el estado/backlog y **añadir** una entrada al registro histórico antes de dar el trabajo por cerrado. No borrar experimentos fallidos ni sustituir resultados antiguos sin un registro de corrección y su motivo.

## 0. EN 60 SEGUNDOS: ¿QUÉ HACEMOS Y DÓNDE ESTAMOS?

**OBJETIVO:** descubrir, definir, validar y finalmente operar —solo si la evidencia lo permite— **un portafolio de varias estrategias genuinamente complementarias sobre Nasdaq futuros NQ/MNQ**, generando oportunidades suficientes cada mes con expectativa neta positiva, un único presupuesto de riesgo y cumplimiento realista de una cuenta de fondeo de referencia de US$50.000. No basta con encontrar una estrategia; tampoco queremos múltiples filtros de **la misma** señal que aparenten diversificación.

**ESTILO DE INVESTIGACIÓN:** científico/deductivo y acumulativo. Formular hipótesis a partir de hechos anteriores, probar combinaciones y mecanismos causales, evaluar contra componentes individuales y cartera compartiendo riesgos. **Hasta 150 hipótesis** era el techo exploratorio del programa histórico H; **NO es una cuota**, y el programa reciente de ticks T tiene su propio registro, sin fingir equivalencia entre H y T.

**OBJETIVO ECONÓMICO:** buscar un rendimiento anualizado neto de la **cartera completa** estrictamente superior al mayor de **15 %**, CAGR de **VOO total return** y CAGR de **QQQM total return**, bajo **idénticas fechas y riesgo comparable**. ROI personal de fondeo se calcula por costos efectivamente pagados y payouts cobrados; no usar US$50.000 nominales como si fueran capital propio. Siete meses de P&L simulado NO prueban CAGR ni superación de ETF.

**CANDIDATO PRINCIPAL HOY:** **T05-377** (NQ reversión de ruptura fallida T02, filtrada por el estado causal de barras de **377 prints Last**), **solo candidato exploratorio de desarrollo**: 115 operaciones, **+$6.220 base / +$5.102,50 estrés**, PF estrés **1,31826**, drawdown de envolvente Last continua estrés corregido por orden cronológico ET **US$1.797,50** (**T08 había publicado $1.825**), frecuencia mínima **8 trades/mes**, sobre 135 días elegibles de octubre 2025–abril 2026. Su margen de DD respecto a una referencia histórica **no verificada** de $2.000 es **$202,50** bajo el modelo base de estrés, pero con **solo +$10 adicionales por trade PF cae a 1,23717 (<1,25)**. No se verificó DD de broker, slippage real ni reglas de fondeo.

**SEGUNDA ESTRATEGIA:** AÚN NO IDENTIFICADA. T09 falló como candidata incremental; no sumar T05 y T09. T05-233+377 es un subconjunto del mismo disparador, NO alfa independiente.

**ESTADO ACTUAL (2026-10-11): NQ-B05/T11 EJECUTADO Y RECHAZADO POR GATE INCREMENTAL.** [GitHub Actions 38181697215](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38181697215) **SUCCESS 7/7 meses y agregador**, 140 días fuente / 135 elegibles; [informe B05](local_nq_tick_2025_2026/NQ_B05_T11_VWAP_ROUTER_RESULTS_2026_10_11.md). **T05** 115 operaciones +$5.102,50 estrés PF1,31826 DD Last $1.797,50. **T11 VWAP FULL** 85 operaciones **−$382,50 estrés**, PF0,97183 y DD Last $3.960. **Router T05+T11** 155 operaciones +$5.622,50 estrés PF1,25081 pero DD $2.082,50; estrés más +$10 RT PF1,17486 DD $2.417,50. El router hizo **100 trades T05 +55 T11**; T11 aportó **−$147,50** y desplazó **15 trades T05** que sumaban −$667,50, de ahí incremento mecánico relativo +$520, **NO alpha independiente probado**. La ablation NO_PULLBACK es tautológicamente redundante con cierre previo del VWAP, descubierto y documentado postprerregistro, sin reoptimizar. **T11 NO SE PROMUEVE; B06 BLOQUEADO para T11; ninguna estrategia validada para fondeo ni OOS abierto.**

**PRÓXIMO PASO:** **NQ-B05B** — formular una hipótesis NUEVA con mecanismo diferente, tras auditar aprendizajes negativos T09 y T11 y evitar reparar retroactivamente T11 en los mismos siete meses como si fueran un holdout limpio. Evaluar un estado observable de expansión/contracción de actividad y desplazamiento de precio en ventanas de prints de corto plazo, con criterios causales propios y controles de no-selección; preregistrar parámetros, coste y router de riesgo compartido ANTES de retornos. **B06 solo se reactiva si un nuevo componente supera incremento monetario bajo estrés y DD/PF conjunto**. También sigue pendiente ingeniería real de ejecución/BBO y reglas de fondeo; **nunca abrir mayo–junio 2026 outcomes o julio–septiembre sellado** para rescatar estrategias.

## 1. ALCANCE, OBJETIVO Y PRINCIPIOS INNEGOCIABLES

1. **Solo NQ/MNQ** hasta nueva instrucción. ES/MES y la cartera multíndice son proyectos conservados, **pausados**, no descartados.
2. **Portafolio real:** dos o más estrategias con lógicas económicamente distinguibles, evaluadas sobre la MISMA cuenta, cronología y riesgo. Objetivo de mediano plazo: aproximadamente 2–3 estrategias de NQ **si y solo si** se descubren, validan y aportan valor incremental; no forzar un número.
3. **Corto plazo con ticks:** “scalping” aquí se refiere a horizontes intradía cortos, mejores señales/entradas, SL pequeños y actividad económica, **NO** a competir en latencia, colocation o HFT.
4. Las barras **233, 377, 4181, 10946** provienen de referencias prácticas del usuario (ejecución/contexto corto/medio/largo), pero no tienen valor estadístico garantizado por ser Fibonacci. **Una barra de 377 “ticks” equivale aquí a 377 operaciones/prints Last, NO a un desplazamiento de 377 ticks de precio ni 377 contratos.**
5. La granularidad de 5 segundos, prints Last, barras por número de transacciones, 1 minuto, contextos de volatilidad/regímenes se elige por mecanismo y calidad. No afirmar que más granularidad siempre mejora retorno.
6. **Falsación e integridad:** documentar cada resultado positivo y negativo, no cambiar retrospectivamente meses, prioridad, costos ni parámetros para recuperar un mal resultado.
7. **Datos privados licenciados:** jamás copiar tick data, gráficos privados con datos sin permiso, secretos, ZIP completo de fuentes mixtas, ticks individuales ni trade logs sensibles a un repo público, artefactos o respuestas. Procesar en runners controlados y publicar solo estadísticas agregadas apropiadas.

## 2. DOS PROGRAMAS HISTÓRICOS SEPARADOS — NO MEZCLAR SUS HOLDOUTS

| Programa | Claves | Desarrollo ya inspeccionado | Validación / reserva | Regla |
|---|---|---|---|---|
| **H: NQ/MNQ minuto histórico** | H01–H78 completadas; futuro H79–H150 según justificación | **2020–2024**; muy reutilizado | **2025 y 2026 sellados** para el programa H | No abrir para escoger H ni asumir que resegmentar 2020–24 crea un OOS nuevo. |
| **T: NQ ticks Last/Bid/Ask** | T01–T10; familia experimental **distinta** de H | **2025-10-15 a 2026-04-30**: 7 meses, 140 días fuente, 135 elegibles en los principales tests | **mayo–junio 2026 = validación interna**; **julio–septiembre 2026 = pseudo-forward histórico sellado** | No leer **retornos** de mayo/junio para ajustar ni abrir julio/septiembre hasta tener cartera y parámetros completos congelados. |
| **QC técnico de ticks T** | calidad de archivo, BBO, husos, integridad | Inspecciones QC de hasta junio 2026 ya documentadas para diagnóstico de datos | QC **no equivale** a abrir outcomes de trading; mantener los usos separados | No transformar una inspección de calidad en una selección de meses o señales favorables. |

El estudio T no convierte 2025 en una validación limpia de H. **Los periodos y muestras de H y T no son intercambiables.** Un pseudo-forward sobre julio–septiembre 2026 es una prueba cronológica histórica con reglas congeladas, NO trading real a futuro.

**Timezone:** ET = America/New_York con DST; grabación de ticks NinjaTrader en UTC (100ns, conversiones explícitas). El proyecto local del usuario opera en America/Bogota UTC-5. Confirmar timestamp de entradas, rollover y ancla de sesión. Las barras por prints T05 reinician a 08:00 ET y no reproducen automáticamente las barras históricas ETH/daily del NinjaTrader original.

## 3. REGISTRO DE DATOS / REPOSITORIOS / SEGURIDAD

| Recurso | Uso permitido | Advertencias |
|---|---|---|
| [MES-Trading-Research](https://github.com/rgentil2/MES-Trading-Research) (público) | Código, prerregistros, tests, resúmenes agregados, este manual | No publicar raw NQ licenciado ni las listas privadas de operaciones derivadas. |
| [NQ-Ticks-Dev-2026](https://github.com/rgentil2/NQ-Ticks-Dev-2026) (privado) | Releases mensuales NQ **Last/Bid/Ask** de octubre 2025–junio 2026, autorizados según cortafuegos | SHA256 obligatorio, acceso read-only con secreto Dev; no tocar meses fuera del protocolo activo. |
| [NQ-Ticks-Sealed](https://github.com/rgentil2/NQ-Ticks-Sealed) (privado) | Reserva julio–septiembre 2026 | **NO ABRIR** hasta preregistro de estrategia/cartera completa y gate formal. |
| [NQ-Tick-Data release](https://github.com/rgentil2/NQ-Tick-Data/releases/tag/nqmnq-minute-2020-2026-v1) (privado) | Archivo independiente histórico **NQ/MNQ 1 minuto** | ZIP **contiene material mixto incluido reservado**. No dar acceso a ZIP entero desde Actions público ni descomprimirlo allí. Extraer solo día/contrato DEV necesarios en entorno privado autorizado. SHA256 original registrado: `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8`, 65.405.000 bytes. |

**Fuente de archivos concreta:** `local_nq_tick_2025_2026/`; programas H en `research/nq/`. Mantener prerregistros y reportes con links a commits y Actions. **Si falta acceso, nunca sustituir por datos sintéticos afirmando que son resultados reales.**

### Conciliación independiente aún pendiente

`compare_independent_nq_minutes.py` y sus **34 pruebas sintéticas** pasaron, pero **NO se realizó la comparación real fuente Minute ↔ ticks Last**. Primer día congelado: **NQ 12-25, 2025-10-15**, 240 barras originales de minuto etiquetadas **08:01–12:00 ET** (fin de vela), total de volumen informado **262.422**. Las barras de tick corresponden a **08:00–12:00 ET**; no confundir 08:00 con el cierre de 08:01. Ver [estado independiente](local_nq_tick_2025_2026/INDEPENDENT_MINUTE_RECONCILIATION_STATUS_2026_10_11.md).

## 4. REGLAS DEL PROCESO DE INVESTIGACIÓN

**Secuencia obligatoria:** observar evidencia → explicación falsable → definir familia completa y comparadores → **prerregistrar en GitHub ANTES** de abrir nuevos outcomes → pruebas sintéticas de cronología, causalidad, QC y seguridad → ejecutar TODOS los periodos DEV predefinidos → estudiar resultados y pérdidas → riesgo/costos/frecuencia/estabilidad → registrar decisión → si pasa, congelar sistema y habilitar test reservado solo en puerta formal.

Para **cada hipótesis/estrategia nueva**:
- Parent IDs, manifest/pruebas previas, mecanismo económico y variables disponibles **antes de decidir**.
- Unidad: decisión ejecutable **conjunta** de dos o más funciones con roles distintos (disparador, confirmación, contexto, veto, router, exposición), no un indicador aislado contado como nuevo alpha.
- Predicción **incremental primaria** frente al padre y al **portafolio base con mismo capital/tiempo/costos**; unidad estadística día/semana, no asumir millones de ticks independientes.
- Ablations: padre, componente individual, combinado, filtro retirado, router base. Reportar si al incluir un nuevo mecanismo se pierden trades valiosos de la cartera.
- Especificación completa de horario, lado, datos, entradas, SL, TP, time-out, priorización de simultáneas, tamaño, precio sintético, comisiones, slippage, fecha/régimen, fuente y UTC/ET.
- Familia de alternativas y control estadístico **Holm/BH** acorde al registro pertinente; correlación/selección múltiple, tamaño muestral e incertidumbre explícitos. La política H67–H150 NO asigna automáticamente ese mismo presupuesto alfa a T10 ni a cada experimento T.
- Excepciones de ejecución, huecos, noticias, caída de conexión y ambigüedad = **fail closed**. Retornos posteriores al evento nunca participan en la decisión de entrada.
- Dividir la evidencia por semana/mes (diagnóstico), trimestre/semestre (evaluación), años (robustez) y régimen **definido causalmente**, sin escoger subperiodos rentables a posteriori.
- No promover a estrategia porque PF suba al reducir operaciones, ni porque sobrevivan algunos meses favorables. No mezclar pruebas de ingeniería con pruebas de rentabilidad ni llamar validación OOS a desarrollo reutilizado.
- **Criterios de referencia**, NO un gate único sin contexto: expectativa neta >0, PF neto estrés preferiblemente >=**1,25**, sensibilidad adversa (base, estrés 1,5× de costos totales claramente modelado), actividad orientativa de **>=5 trades/mes** para una cartera/fuente que deba operar regularmente, drawdown continuo y tolerancia a pérdidas de fondeo. El histórico H tenía además >=150 trades 2020–24, >=4/5 años favorables, concentración anual <40 %, walk-forward interno y corrección estadística; **NO atribuir automáticamente una aprobación H a solo 7 meses T**.
- Evaluar en cartera real: posiciones que se solapan, prioridad congelada, un único límite de riesgo global, correlación, pérdida diaria/trailing, contrato mini vs micro; no sumar P&L de backtests alternativos.
- No usar ganancias de desarrollo para dimensionar agresivamente NQ. **1 NQ = 10 MNQ en multiplicador nominal**, pero costos, spread y dinámica de fills pueden diferir. **USD2.000 DD** es solo referencia histórica de fondeo 50K, NO permiso de pérdida, ni reglas actuales verificadas de una firma.

### Gate económico

`portfolio_cagr > max(15%, VOO_total_return_CAGR, QQQM_total_return_CAGR)`, con fechas iguales y USD, datos de dividendos ajustados, exposición/riesgo y costos auditados. Separa **(A) CAGR equivalente sobre capital nominal de referencia** (ilustrativo) de **(B) XIRR/flujo neto de bolsillo** de evaluaciones pagadas y payouts reales. Capital US$50k en una evaluación **no equivale** a US$50k propio invertido; no prometer ROI sobre cifra nominal. Con solo 7 meses de desarrollo la comparación robusta sigue **NO DISPONIBLE**.

## 5. ÚLTIMO MOTOR NQ CONGELADO PARA COMPARACIONES (T04/T05)

**No cambiar estos parámetros al auditar T08/T10:**
- Datos: NQ prints `Last` 08:00–12:00 ET; señales a partir de barras **completas** de 5 s.
- Apertura de referencia: rango **09:30–09:35 ET**; nuevas entradas hasta **11:10 ET** y cierre hasta **11:30 ET**.
- T02: ruptura fallida / reversión y desaceleración de número de prints Last, según código congelado. **T05-377** toma señales T02 con condición de últimas dos barras completas de **377 prints** que difieren contra la dirección de señal; no cuenta prints posteriores al instante de decisión.
- 1 NQ, 1 posición concurrente, **máx. 2 operaciones diarias**, bloqueo de entradas cuando P&L cerrado del día <= **−US$600**.
- SL = 25 % del rango de apertura, acotado a **16–48 ticks de precio**; TP **2R**; timeout **300 s**; stops conservadores ante evento ambiguo según motor T04.
- **Base:** US$5 RT de comisión supuesta + **1 tick adverso por lado**.
- **Estrés T04:** US$7,50 RT + **2 ticks adversos por lado**. Es estrés predefinido, **NO** una certificación de tarifa/fill real ni necesariamente 1,5× exacto de TODOS los costos.
- `NQ_TICK_USD=5` por NQ; NO confundir Last prints con precio de ticks.
- Los registros T04/T05 provienen de una muestra altamente explorada; son **simulación**, no operaciones reales ni garantía.

## 6. HISTORIAL RESUMIDO (PARA NO REPETIR INVESTIGACIONES)

| Programa/bloque | Resultado verificado | Decisión / aprendizaje |
|---|---|---|
| **H01–H66, H67–H72** — NQ 1 minuto 2020–24 | H69 (H09 OR H56) 262 trades, **+$2.704,44**, PF **1,335**, pero BH q **0,115>0,10** y CAGR nominal ref 50k ~1,06 % | **0/6 H67–H72 aprueban Gate 1**. No avanzar H69 como cartera aprobada. Reutilización histórica, 2025/26 intactos. |
| **H73–H78** — routers por estado NQ minuto | H77 140 trades, +$2.385,30, PF 1,632, BH q 0,0468, pero N<150 y 75,2 % P&L depende 2022; 0/6 mejoran incrementalmente H69 significativamente | **0/6 aprobados**; conservar mecanismo como biblioteca, no declarar nueva validación. |
| **BBO source QC** | 36 días Last/Bid/Ask, mediana diaria ~32,13 % de Last prints fuera del BBO estrictamente anterior; secuencias de timestamp compartido no resueltas | Evitar inferir delta real/agresor o fills ejecutables de las tres exportaciones separadas. |
| **T01–T03** | Continuación/reversión/primer router sobre barras 5s; T02 mecanismo de reversión prometedor de forma exploratoria | Motivaron ejecución T04 y filtrado T05. Ver sus prerregistros y resultados, no inventar nuevas confirmaciones. |
| **T04** | Modelo 1 NQ con slippage/SL/TP/capacidad. T02 padre 190 trades, **+$8.420 base / +$6.860 estrés** | Más P&L que filtrado, pero riesgo elevado en T08: DD Last estrés **$3.385**, PF estrés **1,24356**, incumple pantalla indicativa. |
| **T05** | 377-print: 115 trades, **+$6.220 base / +$5.102,50 estrés**; 233+377: 59 trades, +$5.395 base / +$4.657,50 estrés | 377 = candidato principal; 233+377 PF mejor pero solo **2 trades** en un mes: **falla frecuencia** y es subconjunto. |
| **T06** | Control 233/377 frente 250/400 y vecindades de escala: control 250+400 52 trades, **+$1.275 base** | No hay evidencia para declarar mágicos los números Fibonacci. |
| **T07** | Combinación 233/4181/10946: 29 trades y +$790 base; comparador cercano 240/4200/11000: −$980 | Multiescala estricta reduce demasiado oportunidades; útil como contexto, no imponer tres filtros. |
| **T08** | Auditoría continua Last envelope: T05-377 **DD $1.750 base / $1.825 estrés**; 115 trades, PF estrés 1,31826, mín. 8/mes; todos los tests y 7 meses GitHub SUCCESS | **Único PASS PRELIMINAR CONDICIONAL** entre T02, T05-377 y T05-233+377. **No aprobado para fondeo**. |
| **T09** | Segunda estrategia propuesta: T01 aceleración→fallo rápido confirmado <=60s y retorno al rango. Solo **+$160 base / −$2.087,50 estrés**. Router T05+T09 **+$3.520 base / +$630 estrés**, vs T05 solo +$6.220/+5.102,50 | **FAIL incremental**: **−$2.700 base**, **−$4.472,50 estrés**; 170 operaciones compartidas (86 T05, 84 T09) pero destruye eficiencia. **NO añadir T09**. |
| **B05 T11 VWAP y router compartido** | T11 standalone 85 trades, estrés −$382,50 PF0,97183; router T05+T11 155 trades, +$5.622,50 vs T05 +$5.102,50, pero DD estrés $2.082,50 y PF estrés+$10 1,17486. Dentro del router, T11 55 trades −$147,50, se sustituyeron 15 trades T05 negativos. | **FAIL gate incremental / NO PROMOVER**; ablation NO_PULLBACK redundante de lógica, no alfa independiente. [Reporte B05](local_nq_tick_2025_2026/NQ_B05_T11_VWAP_ROUTER_RESULTS_2026_10_11.md) · [Action 38181697215 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38181697215). |
| **B04 estabilidad temporal** | Estrés T05: 115 trades, +$5.102,50, 6/7 meses positivos y 16/29 semanas positivas, 13 negativas; febrero −$827,50. Estrés +$10 RT: +$3.952,50, 5/7 meses positivos, PF 1,23717, febrero −$957,50 | **Diagnóstico completo, sin validación robusta**. [Reporte B04](local_nq_tick_2025_2026/NQ_B04_TEMPORAL_ROBUSTNESS_RESULTS_2026_10_11.md) · [Action SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38180451505). |
| **B03 fragilidad de coste y DD** | Siete meses DEV 115 trades; estrés T05 PF original 1,31826 y DD Last cronológico $1.797,50; +$10 RT extra PF **1,23717**, +$40 RT extra DD **$2.157,50** | **GATE de holgura ejecución FALLA bajo pequeño recargo, no aprobación broker**. [Reporte](local_nq_tick_2025_2026/NQ_B03_T05_EXECUTION_HEADROOM_RESULTS_2026_10_11.md), [run SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38179855851). |
| **B02 piloto fuente independiente** | Comparación **NQ 12-25 2025-10-15**: 240 velas OHLCV exactas, volumen 262.422 y SHA256 idéntico Minute original vs Tick Last | **PASS de integridad para un día**, no para todos los rollovers ni la ejecución. [Resultados](local_nq_tick_2025_2026/NQ_B02_INDEPENDENT_MINUTE_TICK_MATCH_RESULTS_2026_10_11.md) y 2 runs independientes SUCCESS. |
| **T10 (cerrado)** | 7 meses DEV, 115 trades originales reproducidos; **113/115 (98,26 %) tienen BBO previo <=250ms en ambas puntas**, 2 casos no emparejados en febrero; T05 neto base +$6.220 / estrés +$5.102,50 **sin cambios** | **PASS de ejecución del AUDIT, FAIL de cobertura técnica 100% predefinida; NO se certificaron fills ni rentabilidad ejecutable**. [Reporte](local_nq_tick_2025_2026/NQ_T10_FROZEN_T05_ASOF_BBO_QC_RESULTS_2026_10_11.md), [Actions 38177582699 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177582699). |

**Resultados y evidencia primarios:**
- [T08 audit y gates](local_nq_tick_2025_2026/NQ_T08_FUNDED_RISK_AUDIT_RESULTS_2026_10_11.md) · [run](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38175102957)
- [T09 prueba incremental y tabla mensual](local_nq_tick_2025_2026/NQ_T09_FAST_TRAP_SEVEN_MONTH_RESULTS_2026_10_11.md) · [run](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38176029358)
- [B05 T11 VWAP, ablation redundante y router con pérdidas](local_nq_tick_2025_2026/NQ_B05_T11_VWAP_ROUTER_RESULTS_2026_10_11.md) · [Action 38181697215 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38181697215)
- [B04 semanal/mensual/trimestres y resultados negativos](local_nq_tick_2025_2026/NQ_B04_TEMPORAL_ROBUSTNESS_RESULTS_2026_10_11.md) · [Action 38180451505 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38180451505)
- [B03 ocho recargos y drawdown cronológico](local_nq_tick_2025_2026/NQ_B03_T05_EXECUTION_HEADROOM_RESULTS_2026_10_11.md) · [Action 38179855851 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38179855851)
- [B02 piloto real OHLCV 240/240](local_nq_tick_2025_2026/NQ_B02_INDEPENDENT_MINUTE_TICK_MATCH_RESULTS_2026_10_11.md) · [Minute privado 38179138403](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/38179138403) · [Tick DEV 38179259265](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38179259265)
- [T10 resultado consolidado de 7 meses](local_nq_tick_2025_2026/NQ_T10_FROZEN_T05_ASOF_BBO_QC_RESULTS_2026_10_11.md) · [Action final SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177582699) · [prerregistro](local_nq_tick_2025_2026/NQ_T10_T05_377_BBO_EXECUTION_QC_PREREG_2026_10_11.md)
- [Control H67–H72](research/nq/NQ_H67_H72_RESULTS_2020_2024.md) · [Control H73–H78](research/nq/NQ_H73_H78_RESULTS_2020_2024.md)
- [Política deductiva H67–H150](research/nq/NQ_DEDUCTIVE_ENSEMBLE_POLICY_2026_10_10.md) · [Gate económico](research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.md)
- [BBO QC 36 días](local_nq_tick_2025_2026/BBO_36_DAY_SOURCE_QC_AND_NEXT_RESEARCH_2026_10_11.md)

**IMPORTANTE:** las cifras T01/T03 exactas, periodos y variantes se recuperan en sus propios reportes. **Ningún dato agregado de esta tabla debe considerarse fuente primaria para repetir cálculos.** Consultar scripts/artifacts versionados.

## 7. BACKLOG PRIORIZADO (LISTA DE TRABAJO EJECUTABLE)

| ID | Prioridad | Estado al corte | Entregable / criterio de cierre | Dependencias |
|---|---|---|---|---|
| **NQ-B00** | P0 | **COMPLETADO** | Manual maestro + registro append-only + acceso desde README. Actualizar por cambio | GitHub público |
| **NQ-B01** | P0 | **COMPLETADO 2026-10-11** | T10: **113/115 BBO previos válidos (98,26%)**, 2 febrero sin pareja fresca; 115 trades y netos base/estrés idénticos. Gates: cobertura 100% **FAIL**, retorno operable **NO EVALUADO**. [Run 38177582699 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38177582699) y reporte completo | No optimizar T05 ni inferir fills de BBO |
| **NQ-B02** | P0 | **COMPLETADO (PILOTO PASS 2026-10-11)** | Fuente original Minute versus Tick Last NQ 12-25 15-oct-2025: **240/240 OHLCV exactas**, volumen 262.422, SHA256 canónico igual. Dos Actions independientes SUCCESS. [Informe verificado](local_nq_tick_2025_2026/NQ_B02_INDEPENDENT_MINUTE_TICK_MATCH_RESULTS_2026_10_11.md). No extrapolar a otros días ni ejecución real | Historial ZIP en repo PRIVADO; datos tick DEV. Cierre solo del día piloto |
| **NQ-B03** | P1 | **COMPLETADO — DIAGNÓSTICO 2026-10-11** | **7/7 meses SUCCESS, 115 trades invariantes**. DD T08 corregido cronológicamente $1.725 base / $1.797,50 estrés. Con estrés +$10 RT PF cae 1,31826→**1,23717**; estrés +$40 RT DD **$2.157,50**. **Ruta congelada, NO se recalculó fill/SL/TP**, broker sigue sin verificar. [Reporte y escenarios](local_nq_tick_2025_2026/NQ_B03_T05_EXECUTION_HEADROOM_RESULTS_2026_10_11.md) · [Action 38179855851](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38179855851) | B01/B02 completados; no tocar períodos OOS |
| **NQ-B04** | P1 | **COMPLETADO — TEMPORAL EXPLORATORIO 2026-10-11** | [Reporte B04](local_nq_tick_2025_2026/NQ_B04_TEMPORAL_ROBUSTNESS_RESULTS_2026_10_11.md), [run 38180451505 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38180451505): 7 meses, 29 semanas activas, 115 trades inalterados. Estrés **6/7 meses positivos, 16/29 semanas positivas**, febrero −$827,50; estrés +$10 **5/7 meses positivos**, octubre −$12,50 y febrero −$957,50; PF 1,23717. Dos trimestres parciales, sin años/OOS | B03 previo, no inventar regla por mes |
| **NQ-B05** | P1 | **COMPLETADO — T11 VWAP FAIL GATE 2026-10-11** | [B05 reporte 7 meses](local_nq_tick_2025_2026/NQ_B05_T11_VWAP_ROUTER_RESULTS_2026_10_11.md) · [Action 38181697215 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38181697215). **T11 85 trades, −$382,50 estrés PF0,97183 DD $3.960**. T05+T11 **155 trades**, +$5.622,50 vs T05 +$5.102,50, DD router **$2.082,50 > ref $2.000 NO verificada**; estrés+$10 PF1,17486 y DD $2.417,50. T11 en router 55 trades **−$147,50**, desplazó 15 T05 perdedores; NO nuevo alpha probado. A11 NO_PULLBACK redundante matemáticamente, no reparar post hoc. | T05/T09/B01–B04; OOS cerrado |
| **NQ-B05B** | P1 | **EN CURSO — T12 PRERREGISTRADO / RUN 38182508684** | Diseñar una segunda causa realmente distinta después de que T09 y T11 fallaran incrementalmente. Prevenir lookahead y la reparación de umbrales de T11 conocidos; tomar aprendizajes de actividad sin convertir un filtro VWAP redundante en evidencia. Fijar nueva familia/presupuesto de búsqueda y contrastar bajo router T05 sin riesgo adicional. | Hallazgo B05 NEGATIVO |
| **NQ-B06** | P1 | **BLOQUEADO PARA T11 — REQUIERE CANDIDATO NUEVO** | Solo evaluar candidata que pase B05B: incremento neto compartido bajo estrés y coste adicional, riesgo DD y PF conjunto, estabilidad y actividad. T11 no habilita OOS ni etapa final. | B05B preliminar PASS; T11 FAIL |
| **NQ-B07** | P2 | **PENDIENTE / BLOQUEADO** | Seleccionar y **CONGELAR** cartera NQ final, fuente/contrato, reglas de un solo router, SL/TP, sizing, política de costos, riesgo global, calendario, versiones y código SHA **antes** de holdouts | B01–B06, evidencia robusta |
| **NQ-B08** | P2 | **BLOQUEADO** | Abrir **mayo–junio 2026** para validación interna solo después del gate explícito; reportar resultados positivos/negativos completos, sin ajustes para rescate | B07 |
| **NQ-B09** | P2 | **BLOQUEADO — SEALED** | Abrir **julio–septiembre 2026** solo con estrategia completa congelada tras gates y decidir PASS/FAIL/INSUFICIENTE, jamás reutilizar OOS para volver a seleccionar | B07+B08 + consentimiento/control formal |
| **NQ-B10** | P2 | **BLOQUEADO** | Verificar términos de fondeo vigentes, órdenes en NinjaTrader/Market Replay, cuenta simulada actual, precio ejecutable, limitaciones de automatización/noticias, capital real y payout; luego, si pasa, evaluar compra | B07–B09 |
| **NQ-B12** | P1/P2 | **OPCIONAL — PENDIENTE** | Ampliar concordancia OHLCV Minute↔Tick a fechas/rollovers elegidos por manifiesto antes de resultados; no abrir otros periodos H/OOS para seleccionar trading. El piloto B02 solo cubre 15-oct-2025 | B02 piloto PASS; protocolo prospectivo propio |
| **NQ-B11** | Continuo | **OBLIGATORIO** | Antes/después de cada T o H: prerregistro + código + tests + Action + resultado + decisión + actualización de ESTE backlog y nueva entrada a [NQ_RESEARCH_LOG.md](NQ_RESEARCH_LOG.md) | Todos |

**Orden al reanudar AHORA:** **verificar B05B/T12 run 38182508684 y registrar gates → B06 solo si PASS**. [T11 B05](local_nq_tick_2025_2026/NQ_B05_T11_VWAP_ROUTER_RESULTS_2026_10_11.md) concluyó FAIL pese a 155 operaciones en cuenta compartida, porque su DD estrés $2.082,50 > referencia NO VERIFICADA $2.000 y PF con +$10 RT =1,17486; T11 standalone P&L negativo, y 55 trades de T11 en router también pierden. Mantener aprendizaje causal: la condición NO_PULLBACK es redundante matemáticamente; no ajustar retroactivamente sobre los mismos datos. Mantener periodos sellados y registrar ambos MD tras cada bloque.

### Política de actualización de tareas

Al iniciar un bloque: cambiar estado a `EN CURSO`, vincular prerregistro y commit, recordar datasets autorizados. **Al finalizar**, actualizar resumen/resultado exacto, estado `COMPLETADO` / `FALLÓ` / `BLOQUEADO`, ejecución de GitHub, **fecha** y decisión, más una entrada sin borrar el historial en el log. Si un gate falla, NO silenciarlo ni reetiquetarlo.

## 8. CÓMO RETOMAR EN OTRA CONVERSACIÓN (PROMPT LISTO PARA COPIAR)

> Estamos trabajando en el repositorio GitHub **rgentil2/MES-Trading-Research**, pero **ahora solo investigamos NQ/MNQ**. Abre y lee primero **NQ_PROJECT_MASTER.md** y **NQ_RESEARCH_LOG.md** del branch main, luego verifica el último GitHub Actions de la tarea activa y sus logs/artefactos (B05/T11 FAIL, B05B nueva familia siguiente). **No confíes en el estado documental si un run posterior lo supera**: actualiza primero el documento. Respeta las políticas de hipótesis/prerregistro, análisis deductivo, cartera con riesgo compartido, costos, calidad de datos, holdouts H vs T separados y gate económico > max(15 %, VOO, QQQM). **No abrir mayo–junio 2026 para resultados ni julio–septiembre 2026** antes del gate formal. Prosigue con el primer backlog P0 pendiente, ejecuta lo posible en GitHub sin solicitarme tareas que puedas hacer y **actualiza la bitácora/backlog antes de terminar**. Si una prueba falla, repórtala y conserva el resultado. Recuerda que el objetivo es un **portafolio de estrategias NQ complementarias**, no solo T05 ni 150 hipótesis por obligación.

## 9. ÍNDICE DE NAVEGACIÓN Y NORMA DE CONTINUIDAD

- **Este archivo**: único punto de entrada, objetivo, reglas, estado y backlog.
- **[NQ_RESEARCH_LOG.md](NQ_RESEARCH_LOG.md)**: fechas, evidencias, decisiones y correcciones registradas cronológicamente; **añadir, nunca borrar**.
- **Prerregistros y reports**: `local_nq_tick_2025_2026/` y `research/nq/`. Si el master contradice el último registro científico congelado, **NO alterar aquel documento**: emitir nota de discrepancia y corregir el master con historial.
- **GitHub Actions**: estado/ejecución reales, commits y artefactos de cada experimento; un archivo de resultados escrito a mano no reemplaza un workflow fallido.
- Antes de responder "ya está": comprobar enlace, commit, run exitoso, hash y guardas de acceso a datos. Si no se completó, declarar `INCOMPLETO` y registrar el bloqueo.

**Este manual documenta decisiones de investigación, NO ofrece asesoría financiera personalizada ni promete rentabilidad.**

## 10. CONTRATO DE CONTINUIDAD PARA CADA NUEVA CONVERSACIÓN

**Protocolo obligatorio:** leer este documento y `NQ_RESEARCH_LOG.md` completos, comprobar el último GitHub Actions, y anunciar qué ID `NQ-Bxx` se va a ejecutar. Tras cada bloque técnico, escribir una NUEVA entrada `NQ_RESEARCH_LOG.md` (append-only) con fuente autorizada, contrato, fecha ET, prereg/commit, tests, enlace y estado real de Actions, resultados completos incluyendo fallos, limitaciones, decisión y siguiente ID. Actualizar **simultáneamente** la sección 0, la fila de historial y el estado/backlog de este master. No sustituir hechos por promesas de trabajos futuros. Si una ejecución queda inconclusa, registrar `EN CURSO` o `BLOQUEADO` y las condiciones de cierre. Registrar cualquier corrección sin borrar errores pasados.

**Reinicio en un chat nuevo:** proporcionar solo este enlace `https://github.com/rgentil2/MES-Trading-Research/blob/main/NQ_PROJECT_MASTER.md` y decir «Continúa por el primer NQ-B pendiente, lee también el log y actualiza ambos». La conversación nueva no necesita reconstruir el historial oral; los enlaces a código y Actions son la trazabilidad. No abrir periodos sellados ni continuar MES/ES sin nueva autorización.
