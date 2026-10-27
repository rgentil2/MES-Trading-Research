# NQ M1 — Descubrimiento en Python con etapas temporales tipo StrategyQuant (27-oct-2026)

**Estado:** PROTOCOLO / PREPARACIÓN; no constituye ejecución de backtest ni aprobación de estrategia. Se inicia un programa H-M1 nuevo, **sin sobrescribir H01–H78** ni los resultados T ni sus políticas congeladas.

## Decisión y propósito

Por decisión del usuario: regresar a **NQ con Python** y empezar por los **datos históricos de un minuto**, replicando la disciplina temporal útil del proyecto SQX 6E: ventana de negociación fija, fase de desarrollo (IST), validación interna (ISV) y pruebas sucesivas en períodos posteriores. El generador produce **estrategias ejecutables completas**, no solo correlaciones de señales; se reutilizan los sistemas existentes de datos, calidad, estadística, costes, robustez y cartera de GitHub. **NO** se abre adquisición de datos ni se modifica el motor de validación establecido.

El cambio de activo es importante: **NO transportar a NQ** el slippage en pips 6.25 ni los parámetros monetarios de 6E. NQ tick = 0.25 puntos, $5 por tick de 1 NQ ($20/punto); MNQ tick = 0.25, $0.50 por tick ($2/punto). El coste de referencia investigado para MFFU Rapid EOD era $4.68 por ida/vuelta NQ y $1.90 MNQ en 13-oct-2026, pero se exige verificar la vigencia antes de operar. Para simulación exploratoria usar **2 ticks de deslizamiento por lado**, contados una sola vez, además de comisión y escenarios 1.5× costes totales y recargo fijo de $10 RT; todos los supuestos y variantes se registran.

## El reloj: igual método de SQX, no igual instrumento

- Zona horaria de señales: **America/New_York**, DST verdadero, nunca convertir por UTC-5 fijo.
- Primera campaña **NQ M1**, ventana RTH de **09:30 a 11:29 ET**, **última salida y cancelación de pendientes a 11:29 ET**. No confundir límite de última entrada con liquidación de posiciones.
- Los minutos fuente históricos están etiquetados por **fin de barra** (ej. 09:31 representa 09:30–09:31). Una decisión que use cierre 09:31 solo puede ejecutar **desde el siguiente open elegible**; descartar entradas o salidas que no se puedan representar antes de 11:29.
- Señales solo con barras terminadas y contexto previo; evento ambiguo stop/target en M1 => stop primero o invalidez técnica documentada, nunca escoger el desenlace más rentable.
- En la fase de **exploración de señales** no imponer artificialmente `max_trades_per_day=3`; en el **backtest ejecutable y router de una cuenta** usar política de exposición fija y límite efectivo de operaciones (referencia vigente para comparabilidad: máx. 2 entradas/día, una posición simultánea, corte en PnL diario cerrado −$600), con resultados de señales brutas y ejecutadas claramente separados.
- Campaña secundaria **M1 08:00–11:29 ET** y posterior M5 **solo como familias nuevas independientes y registradas por adelantado**; no escoger entre horarios por PnL observado y afirmar que es OOS.

## Calendario secuencial de seis puertas

| Puerta | Datos | Función | Qué se permite | Estado |
| --- | --- | --- | --- | --- |
| S0 — Manifest + pruebas técnicas | Solo código/catálogo; **sin retornos** | Congelar 100–150 candidatos diversos, familias, semillas, coste, señales, SL/TP, reloj, métricas y multiplicidad | Verificar catálogo, reloj, parsers y cortafuegos | PREPARACIÓN |
| S1 — IST | **2020-01-01 a 2022-12-31** | Generación, evaluación y ranking de desarrollo | Examinar y ordenar candidatas completas; preservar todos los intentos | NO EJECUTADO |
| S2 — ISV1 | **2023-01-01 a 2023-12-31** | Validación interna cronológica de catálogo/reglas congeladas | Reejecutar SIN optimización ni cambiar parámetros. Registrar aprobadas y fallidas | NO EJECUTADO |
| S3 — ISV2 / stress cronológico | **2024-01-01 a 2024-12-31** | Segunda comprobación retrospectiva sucesiva | Solo estrategia congelada desde S1, resultados de todos los candidatos prefijados; cero rescate | NO EJECUTADO |
| S4 — Auditoría global DEV | **2020–2024** | Estabilidad anual, walk-forward retrospectivo, cartera/riesgo y controles estadísticos | Resumen y comparadores; **no** denominar OOS independiente a 2023 o 2024 | NO EJECUTADO |
| S5 — Reserva H 2025 | **2025** SELLADO | Holdout H prospectivamente definido | **No leer** sin candidatura completa congelada, prerregistro, puerta de aprobación y autorización explícita | BLOQUEADO |
| S6 — Reserva H 2026 | **2026** SELLADO | Pseudo-forward H separado de T | **No leer** hasta superar S5 y conseguir autorización explícita; no reutilizar reserva T | BLOQUEADO |

**Advertencia epistemológica:** todos los años **2020–2024** han sido inspeccionados en H01–H78. La partición 2020–22 / 2023 / 2024 reproduce el **proceso temporal SQX**, pero NO convierte ISV1/ISV2 en muestras vírgenes. Tampoco constituye autorización para leer 2025/26. Este programa no consume los datos sellados T: mayo-junio2026 internos y julio-septiembre2026 pseudo-forward T permanecen separados.

## Generación de estrategias: exploración amplia pero finita

- Lote inicial **120 candidatos** distribuidos en 5 familias con *mecanismos* distintos (ruptura, reversión, continuación, retroceso a VWAP y expansión/contracción); fuente NQ minuto y condiciones causales.
- Cada candidata: reglas de entrada long/short, horas, no-trade, máximo dos condiciones de entrada simples, SL obligatorio **con riesgo monetario comprobable** (estructural o ATR), TP opcional, tiempo de salida obligatorio y tamaño de posición fijo. No aceptar un SL sin límite por creer que el DD histórico lo sustituye.
- El catálogo de alternativas, SL/TP, épocas, direcciones y tiempo/horizontes forman el **presupuesto total de búsqueda**. No seleccionar retrospectivamente combinaciones adicionales en S2/S3 como si fueran preespecificadas.
- Ranking exploratorio **multiobjetivo**: expectativa neta, PF, neto/DD, frecuencia, dependencia de días/operaciones, sensibilidad a costes; ningún ranking por Net Profit aislado sustituye el filtro de riesgo. Registrar todos los rechazos con motivos. Umbrales finales siguen políticas existentes del maestro; no rebajar gates para producir finalistas.
- Se probarán ablations y controles para familias que aparenten aportar beneficio; correlación y contribución incremental en **un solo router/cuenta**, no suma de curvas individuales. No contar dos tamaños o dos períodos sobre mismos signals como muestras independientes.

## Contrato operativo para cada ejecución

1. *Antes de cargar datos*: SHA de archivos de reglas, código, costes y catálogo; comprobar whitelist de **años permitidos por puerta**; nunca extraer materiales sellados de ZIP privados a artefactos públicos.
2. Para pasar **S1→S2**: cerrar la búsqueda; fijar el catálogo elegible y su tamaño, **congelar reglas, parámetros y código** (commit SHA), registrar los resultados íntegros IST; para **S2→S3**, prohibido reordenar por ganancias ISV1 y alterar hipótesis.
3. Para datos minuto, el ZIP privado puede incluir años H reservados: **abrir solo miembros 2020–22 en S1**, 2023 en S2 y 2024 en S3, con comprobaciones de nombres y contenido. Obtenerlo mediante el acceso privado ya existente, no publicar datos brutos.
4. Output privado: operaciones/sesiones; output público seguro: conteos por etapa/año, PF, neto, DD, distribución de frecuencia, estrés, motivos de rechazo, incidentes, status `REUSED_DEV_EXPLORATORY`; hash de insumos y bitácora de selección.
5. Validación económica, estadística, BH/Holm y umbral >max(15%,VOO TR,QQQM TR), adaptados a ventanas comparables, **siguen vigentes**; un pase IST o ISV retrospectivo **no es aprobación de trading**.
6. Si un candidato viola el tamaño del stop/riesgo por operación con 1 NQ, registrar `RISK_INELIGIBLE_NQ` y evaluar MNQ **como familia/tamaño predeclarado**, no reducir el sizing retrospectivamente para rescatar un resultado.

## Primer entregable

Publicar el manifiesto y un **preflight sin precios** que compruebe las ventanas temporales, cuotas por familia y años explícitamente permitidos, con tests sintéticos; después correr IST 2020–2022 sobre la fuente Minute privada existente **cuando el runner pueda accederla**. No publicar números de estrategias ni desempeño antes de ejecutar realmente. Mantener `2025/2026=SEALED` y detenerse ante acceso inesperado.
