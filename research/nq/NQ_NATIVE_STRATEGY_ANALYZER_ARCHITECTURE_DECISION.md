# Decisión obligatoria de arquitectura — investigación NQ **dentro de NinjaTrader 8**

**Aclaración explícita del usuario (noviembre 2026):** «la idea es que **todo corra directamente en NinjaTrader y el Strategy Analyzer**». No pedir exportación histórica de `.txt`, enviar archivos por chat, ejecutar scripts en PowerShell ni usar la CLI `.NET8` como camino principal para descubrir estrategias. El histórico M1 ya está instalado en NinjaTrader. Esta decisión prevalece sobre instrucciones antiguas del README V25 que dependían de un puente offline.

## Estado verificado vs. requisito

- **Hoy instalado por el usuario:** `NQ_V25_FrozenAnalyzer` compila y aparece en Strategy Analyzer. **Únicamente ejecuta un candidato EXCANv19 congelado** y exige handoff de portafolio aprobado. NO genera estrategias, NO crea rankings, NO selecciona portafolio. No pedir pulsar Run ni rellenar campos inventados.
- **Hoy implementado en GitHub:** V23 genera estrategias/filtra/ranquea mediante un ejecutable .NET8 **externo**; V24 aceleró 100.700 simulaciones **sobre fuente sintética** también fuera de NT8. Ese diseño no satisface el requisito de interfaz/ejecución 100% interna de NinjaTrader. Mantener esos motores como bibliotecas matemáticas reutilizables, no presentar su CLI como obligación del usuario.
- **Nativo NT8 disponible oficialmente:** Strategy Analyzer > **Optimization** (Default / Genetic), **Walk Forward Optimization**, **Monte Carlo** sobre resultados y `OptimizationFitness` personalizada en NinjaScript. La implementación exacta de los 20 genes, filtros G0 y portafolios requiere adaptación propia, sin asumir que el Genetic nativo replica el GA V23 ni que evaluará 100.700 escenarios a la misma velocidad.
- **No demostrado:** ejecución de búsqueda real M1 de NQ DEC2026, ganador congelado, paridad de fills y portafolio validado. No inventar tiempos ni rentabilidad.

## Diseño de la entrega dentro de Strategy Analyzer

1. **`NQ_NativeResearchAnalyzer` (NinjaScript Strategy)**: seleccionar desde la UI, barras **Last / Minute 1 / NQ DEC26 / 2020–2022**, sin abrir la base de datos externa. Exponer los parámetros genéticos/formulas (120 familias, 1.320 variantes y los 20 genes canonicales) como propiedades `NinjaScriptProperty`. Evaluar únicamente barras históricas que NT8 proporciona; orden cronológico. Debe usar la biblioteca matemática V19 y preservar ATR, criterios de costes, time exits y horarios.
2. **Optimization / Genetic nativo**: lanzar búsqueda desde Strategy Analyzer. Si el genetic nativo no puede cubrir eficientemente el espacio gramatical de 20 genes o su identidad canónica, crear `Optimizer` NinjaScript personalizado con `OnOptimize` / `RunIteration`, **sin** ejecutar un proceso externo. Registrar IDs únicos/canonizados por iteración.
3. **`NQ_NativeRiskFitness`**: `OptimizationFitness` NinjaScript que penalice/cierre candidaturas sin ≥150 trades, ≥5/mes, PF neto≥1,25, neto positivo tras costes 1.5×, DD≤USD 2k, pausa diaria ≤USD 1k. Registrar métricas/rechazos en UI o informes generados por script (nunca solicitar subida al chat).
4. **Robustez**: walk-forward cronológico y Monte Carlo de datos de trades propios. La capacidad de Strategy Analyzer de hacer WFO no equivale por sí sola a todas las reglas de V22; validar 3 años y dependencia de trades explícitamente.
5. **Portafolio dentro de NinjaTrader**: lógica NinjaScript de selección de **3–5** candidatos según correlación mensual, beneficio concentrado≤40%, simultaneidad, M1 MAE/MFE y riesgo conjunto. Los optimizers NT8 presentan resultados por estrategia, pero **no** eligen automáticamente portafolios 3–5 según estas reglas: esto es desarrollo adicional obligatorio, no funcionalidad que pueda darse por hecha.
6. **Validación V25**: solo después de portafolio real que aprobó todos los filtros, congelar genes exactos e invocar la estrategia `NQ_V25_FrozenAnalyzer` ya instalada, contrastando órdenes históricas/SL/TP/costos, sin reentrenar ni operar en vivo. Mantener 2023–24 y 2025–Oct2026 cerrados hasta aprobar la etapa previa.

## Criterio de entrega que exige el usuario

**Un solo flujo desde NinjaTrader > New > Strategy Analyzer** para búsqueda, filtros, rankings, Monte Carlo, WFO, selección 3–5 y validación final, con el histórico que NinjaTrader ya gestiona. **Cero exportaciones manuales obligatorias; cero archivos enviados al chat; cero instaladores/PowerShell externos obligatorios.**

**No está completo todavía.** El primer entregable debe ser una estrategia de **descubrimiento/optimización nativa**, que hoy falta. No confundir la compilación de `NQ_V25_FrozenAnalyzer` con ese motor. Se conserva la descripción de V25 como *integración y validación final en NT8*, sin inventar una versión nueva.
