# NQ-B05E — Decisión del investigador: SOLO datos ya disponibles (11-oct-2026)

**Estado:** política y protocolo congelados ANTES de ejecutar nuevas pruebas de calidad/estrategia; **NO introduce una hipótesis nueva** ni recalcula P&L.

## Restricción EXPLÍCITA del usuario (prioritaria)

- **Continuar investigando NQ/MNQ usando exclusivamente los históricos que ya tenemos**: Tick Last/Bid/Ask de DEV Oct-2025..Abr-2026 y las velas históricas NQ/MNQ existentes. Reutilizar archivos/releases ya subidos al proyecto y resultados agregados calculados; las copias técnicas de los mismos archivos existentes dentro de GitHub Actions, si son indispensables para calcular, NO se consideran adquisición de nueva historia, pero **no extender su intervalo ni solicitar fuentes nuevas**. Preferir no hacer descargas siquiera de los archivos existentes cuando basten los artifacts y resúmenes disponibles.
- **PROHIBIDO** proponer como requisito, adquirir, comprar o descargar **más data**, un nuevo histórico, feed CME con AggressorSide, fuentes nuevas, Market Replay adicional, Level 2 adicional, otros proveedores, o extender NQ hasta otras fechas, **hasta que el usuario cambie expresamente esta decisión**.
- Esta regla **supersede la recomendación B05D** de Market Replay/seq o B05E original de consultar nuevos proveedores. No hay estrategia válida que obligue a comprar datos para investigarla. Si una hipótesis no puede medirse de manera honesta con nuestras columnas existentes, **descartarla o etiquetarla como no identificable**, nunca inventar agresión, delta comprador-vendedor, profundidad ni fills.
- Conservar **2026-05..06 T** reservado, **2026-07..09 T** sellado, y **2025–2026 H** de minuto sellado conforme las normas separadas del master. No usar holdouts para limpiar a conveniencia ni buscar estrategias.

## Qué significa limpiar SIN introducir sesgo

1. **Proteger crudos:** archivos originales y hashes NO se modifican, borran, sobrescriben, reordenan a mano, ni se publican.
2. **Calidad de fuente independiente del P&L**: fallar una sesión completa si faltan datos que impiden construir barras causalmente, existen timestamps decrecientes, precios fuera de grilla, tamaño Last inválido, día/contrato incorrecto, vacíos que afectan el contexto señal o aperturas ausentes. Determinar estos flags *sin leer ganancia/pérdida de la sesión o de una operación*. Registrar conteos por mes y causa. No imputar precio ni inventar ticks faltantes.
3. **Solo 135 sesiones previamente elegibles de 140 fuente para referencia T05**; las otras cinco ya están fuera por QC de opening range. Estas cifras se conservarán como baseline exploratorio (T05 115 trades, +$5.102,50 estrés, PF1,31826, Last DD $1.797,50). No cambiar universo a posteriori silenciosamente.
4. **T10 113/115** T05 tienen BBO anteriores estrictos con <=250ms en ambos endpoints; **2/115 son cotizaciones anticuadas (febrero)**. Son **dos fallas de evidencia de quote**, **NO dos corrupciones probadas en la serie Last**. NO borrar esas dos operaciones del P&L original ni adjudicarles beneficio/pérdida arbitrariamente. Fuente Last sigue admitida para señales basadas en OHLCV/prints. No usar un filtro por calidad conocido **después** de abrir la operación (ej.: quote stale al salir) como regla ejecutable o exclusión ex-ante.
5. **Misma timestamp entre Last/Bid/Ask:** no asociar secuencia confiable ni tratar valores en el futuro como conocidos. Usar quotes estrictamente anteriores para QC; si es imposible determinar orden, etiqueta `AMBIGUOUS_CROSS_STREAM_SEQUENCE`, **no eliminar una fila Last válida sin causa independiente**.
6. **Comparar como diagnósticos, no escoger ganadores:**
   - A: `PRIMARY_LAST_DEV_UNMODIFIED`, replay de las 115 T05 baseline y costo estrés de referencia.
   - B: `QUOTE_COVERAGE_DIAGNOSTIC_ONLY`, datos de cobertura 113/115 vs 2 sin quotes válidas. Si se requiere cuantificar P&L dentro de subconjuntos, informar **ambos grupos y el P&L conjunto sin descartar los dos**; no usar la partición como filtro causal de operaciones, ni como estimador honesto de nuevo rendimiento.
   - C: `COST_STRESS_ACCOUNTING_ONLY`, T05 a +$10 RT adicional, PF1,23717; sin simular fills reales ni modificar stops.
7. **Cuándo un problema de dato implica no operar:** si el sistema real no puede observar a tiempo una variable imprescindible para decidir, el nuevo modelo no podrá usarla; separar **calidad del dato al generar la señal** (causal) de **quality flags encontrados después de operar** (solo diagnóstico). Un error de fuente genuino que impida determinar señales => excluir la sesión completa sin consideración de P&L y mostrar denominador cambiado.
8. **No se arregla la falta de un campo eliminando filas**: las variables no observadas (agresor verdadero, orden de eventos del exchange, L2/colas) siguen no observadas para TODAS las filas.

## Siguiente tarea de ingeniería NQ-B05F: diagnóstico de QC con *nuestros datos*, NO búsqueda de información externa

- Revisar los códigos de QC disponibles (`nq_tick_short_horizon.py`, `qc_tick_day.py`, `nq_t10_t05_bbo_endpoints.py`), verificar que la frontera DEV sea `dev_day` y que validación de origen falle cerrado; priorizar T05 reproducido 115/115 operaciones bajo base/estrés.
- Codificar **manifiesto auditable de calidad** de las siete mensualidades ya subidas al repo privado (cuando haga falta cargar un archivo **ya almacenado**, usar únicamente ese archivo, con SHA256; no adquirir ni descargar intervalos adicionales). Reportar únicamente recuentos por mes y tipo de defecto, sin precios individuales, timestamps, day-level trade list, provider raw data o trades; no seleccionar parámetros por sus ganancias.
- Verificar continuidad de barras de 233 y 377 prints Last con pruebas causales; contexto medio/largo 4181/10946 prints si su completitud es suficiente, sin inventar prints y sin considerar Fibonacci una ventaja por sí misma.
- Posteriormente, formular UNA hipótesis que sí pueda probarse con estas variables observadas y con frecuencia mensual apropiada, presupuesto de hipótesis acotado, costes base/estrés+$10 y capital compartido con T05. Si falla, reportarla; jamás forzar 2–3 estrategias.

## Meta y restricciones de aprobación no cambian

Aún no hay segunda estrategia rentable en cartera (T09/T11/T12/T13 fallaron), T05 sigue exploratoria, no garantizar retorno >max(15 %, VOO total return, QQQM total return), no confundir nocional $50k con capital propio, no presentar DD modelo Last como regla verificada de fondeo, **NO abrir OOS** antes de B07 formal.

**Decisión B05E:** `ONLY_EXISTING_DATA_ALLOWED`; `NO_MORE_DATA_DOWNLOADS_OR_PURCHASES`; `NO_OUTCOME_BASED_DATA_CLEANING`; `DO_NOT_DROP_TWO_BBO_STALE_TRADES_FROM_T05`; `NEXT_B05F_EXISTING_QC_AND_MEASURABLE_LAST_HYPOTHESIS`.
