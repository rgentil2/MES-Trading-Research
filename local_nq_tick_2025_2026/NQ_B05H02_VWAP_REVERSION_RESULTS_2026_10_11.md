# NQ-B05H-02 — RESULTADO FINAL: reversión al VWAP 377 prints RECHAZADA (7/7 meses)

**Fecha:** 2026-10-11 Colombia (GitHub Actions 2026-10-12 UTC). Estado: **`B05H02_REJECT_DO_NOT_PROMOTE`**. La simulación terminó correctamente de forma técnica; la **hipótesis económica FALLÓ**. No confundir workflow SUCCESS con estrategia PASS.

## Universo, alcance y ciencia preregistrada

- [PRERREGISTRO B05H02](NQ_B05H02_PRINT_BAR_VWAP_REVERSION_PREREG_2026_10_11.md) **ANTES DE RESULTADOS**, commit **`76467b109501aabcf59d5f344506ba23bb058a15`**. UNA hipótesis nueva, **reversión hacia VWAP en lateralidad**, económicamente distinta de H01 expansión/continuación y T05 fallida apertura.
- Disparador H02: barra **>=377 PRINTS Last** con giro de VWAP de >=3 ticks precio desde un extremo de >=12 ticks respecto a VWAP previo 4181, todavía >=4 ticks lejos del valor; confirmación high/low +2 ticks, `range<=48 ticks`, contexto **4181/10946 PRINTS** anterior en rango lateral `abs(VWAP change)<=24/36 ticks`, freshness 40/60min; 10:00–11:15 ET **solo ventana horaria**, no rejilla de señales de tiempo fijo. **Máximo 1 oportunidad H02 por día**. Grupos con timestamp igual indivisibles. VWAP racional exacto/prints no qty como unidad. **NO USAR 5s ni 1min para disparar H02**. T05 usa su señal 5s histórica SOLO comparador congelado, nunca fuente de H02.
- Riesgo H02 1 NQ, SL32 ticks precio/TP48/5min; coste base $5 RT +1tick por lado, estrés $7,50 RT +2ticks por lado, escenario extra+$10 RT contable misma ruta; T05 stop original 16..48 ticks/TP2R, ambos bajo mismo router 1 contrato, 2 trades diarios, daily closed gate -$600 y no overlap. Si ambigüedad de entrada/salida, `FAIL CLOSED`, sin reconstrucción de ganancias.
- **ÚNICAMENTE los siete archivos privados de NQ Last DEV YA existentes**, octubre 2025–abril 2026, SHA256 verificados; 140 días fuente /135 elegibles, sin obtener otros periodos/fuentes, sin abrir T mayo–septiembre 2026 ni H 2025–26, sin Replay/L2 y sin exportar datos privados.

## Evidencia verificable y fail/error técnico transparente

- [Motor H02](nq_b05h02_reversion_month.py) commit `0b9fd841105c71cc1213cd3b0ca168405b256998`, [agregador](nq_b05h02_reversion_aggregate.py) commit `36e899fece51378de7c1b1bab17768856f6175b7`, [tests sintéticos](test_nq_b05h02_reversion.py) commit `595ac95e9c8dd081f713dffbdce36290d02bc67a`, [workflow](../.github/workflows/nq-b05h02-print-vwap-reversion-dev.yml) commit `2ed7e4d79920b3b22a8e2df066ee12583fb36dde`.
- [Run 38193862954](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38193862954): **FAILURE PRE-DATA solo test**: cuando no había barras previas suficientes, `Counter` omitió clave cero `ready_context_decisions`; corregida **solo la aserción** para `.get(...,0)`, commit `758a779ad0177d538881fa131113eb169bf45407`. NO cambiaron triggers, costes, muestras ni parámetros tras mirar P&L.
- [**RUN FINAL 38193895252 — COMPLETED SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38193895252): **16/16 pruebas sintéticas PASS**, siete jobs meses PASS y agregador PASS (**9/9**); artifact seguro `b05h02-seven-month-safe-reversion-report` **ID 11722303789**, con `report.md` y `summary.json`, descargados/leídos para escribir este informe.
- La versión de T05 se reprodujo EXACTAMENTE: 115 trades, base +$6220, stress **+$5102.50** PF1.31826/Last DD $1797.50; stress+$10 fixed path +$3952.50/Last DD $1887.50, PF1.23717. Fuente 140/135 PASS.

## Los TRES modelos alternativos, nunca sumar standalone

| Escenario estrés Last sintético | Operaciones | Neto USD | PF | Drawdown Last USD | Neto estrés+$10 RT (ruta fija) USD | PF estrés+$10 |
|---|---:|---:|---:|---:|---:|---:|
| **T05 original congelada** | **115** | **+5.102,50** | **1,31826** | **1.797,50** | **+3.952,50** | **1,23717** |
| **H02 sola** | **75** | **−1.427,50** | **0,82431** | **1.597,50** | **−2.177,50** | **0,74577** |
| **T05+H02 en UNA cuenta** | **166** | **+2.195,00** | **1,10001** | **2.477,50** | **+535,00** | **1,02334** |

**H02 tuvo 75 oportunidades/75 trades standalone, 60 ejecutadas en router** con contribución neta estrés **−$2.530**. En el router **106/115 operaciones T05** sobrevivieron: T05 contribuía **+$4.725**, frente a +$5.102,50 de T05 original, es decir nueve operaciones desplazadas cuyo aporte era **+$377,50** en conjunto. Cálculo atribuible verificable: `router 4725 - 2530 = 2195`; `delta 2195 - 5102.5 = -2907.5`. La caída de neto no se debe a sumas de modelos independientes, sino a ejecución cronológica real del modelo sintético en UNA cuenta.

**El router menos T05 es −$2.907,50 estrés, y −$3.417,50 al añadir un coste de $10 RT (ruta fija).** Además, el DD Last del router **$2.477,50** supera la referencia histórica meramente ilustrativa de $2.000, que **no es un límite de fondeo contractual comprobado**. Más frecuencia NO implicó rentabilidad incremental.

## Todos los meses, sin ocultar pérdidas

| Mes | T05 operaciones / neto estrés USD | H02 standalone operaciones/neto | Router operaciones/neto | H02 ejecutadas en router / neto |
|---|---:|---:|---:|---:|
| 2025-10 | 15 / +137,50 | 11 / −387,50 | 20 / +120,00 | 8 / −255,00 |
| 2025-11 | 8 / +760,00 | 11 / −442,50 | 19 / +317,50 | 11 / −442,50 |
| 2025-12 | 22 / +1450,00 | 16 / +530,00 | 31 / +1102,50 | 10 / **−605,00** |
| 2026-01 | 19 / +1572,50 | 14 / −945,00 | 27 / +107,50 | 11 / −797,50 |
| 2026-02 | 13 / −827,50 | 9 / −22,50 | 21 / −1072,50 | 8 / −245,00 |
| 2026-03 | 21 / +1372,50 | 5 / +307,50 | 24 / +995,00 | 4 / +85,00 |
| 2026-04 | 17 / +637,50 | 9 / −467,50 | 24 / +625,00 | 8 / −270,00 |
| **Total** | **115 / +5102,50** | **75 / −1427,50** | **166 / +2195,00** | **60 / −2530,00** |

H02 individual fue negativo 5/7 meses y los aportes H02 en router negativos **6/7**. **Diciembre ilustra por qué no sumar resultados standalone**: H02 sola **+$530**, pero las H02 que se ejecutaron tras aplicar la capacidad/orden de T05 aportaron **−$605** en el router.

## Gates preregistrados, sin cambiar para conseguir PASS

- Router estrés+$10 RT incremento neto >0: **FAIL** (−$3417,50).
- Router PF estrés ≥1,25: **FAIL** (1,10001).
- Router PF estrés+$10 ≥1,25: **FAIL** (1,02334).
- DD Last estrés <US$2000 referencia NO verificada: **FAIL** ($2477,50).
- H02 trades en router y neto atribuido >0: **FAIL** (60 trades, −$2530).
- Mantener ≥104 T05/115: **PASS** (106).
- Router ≥5 trades cada mes: **PASS** (meses mínimo 19).
- **Decisión científica: `H02_REJECT_DO_NOT_PROMOTE`.** No reoptimizar 377/4181/10946, stops, horario, lateralidad ni threshold para rescatar el test; no abrir OOS, no promover B06 ni comprar fondeo.

## Deducción para el bloque posterior (sin ejecutar otra hipótesis aquí)

Los dos estudios nuevos por barras print aportan una lección: **H01** generó 266 oportunidades, consumió capacidad y 4 sesiones de entradas irresolubles (no hay P&L 7 meses), mientras **H02** con 75 oportunidades sí permite test 7/7 pero su contribución es **−$2530** y perjudica T05. El problema principal ya no es generar señales o descarga de datos, sino **identificar una oportunidad realmente independiente con margen neto y menos desplazamiento de T05**, y no extraer excesivas familias de 135 sesiones DEV ya muy reutilizadas.

**Siguiente recomendado NQ-B05I — AUDITORÍA DEDUCTIVA DE CONTRIBUCIÓN/INTERFERENCIA EN ROUTER** sin nuevas hipótesis ni lecturas de OOS: cuantificar por mes y horario ya agregado el origen de pérdidas H02 y cómo seleccionar mecanismos genuinamente no correlacionados, sin usar outcome para filtrar meses u horas. Si no existe una justificación económica diferente (y no simplemente otra combinación de umbrales 233/377), considerar pausar nuevas hipótesis sobre este pequeño DEV en lugar de buscar hasta 150 por obligación. Cualquier hipótesis futura: prerregistro previo, solo data histórica existente y sin 5s para señales nuevas.

No hay fills reales, L2, agresor true-delta, DD contractual verificado ni CAGR comparable VOO/QQQM, por lo cual estas simulaciones no autorizan fondeo.
