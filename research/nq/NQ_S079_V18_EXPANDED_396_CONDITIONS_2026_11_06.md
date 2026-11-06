# NQ S0.79 — V18: 36 feature formulas / 396 directional conditions
Fecha: 2026-11-06 | Estado: C# pure-source QA 3/3 verde, investigación únicamente

## Decisión de ejecución vigente

El instrumento de destino es **NQ DEC2026**, y el usuario confirmó que su NinjaTrader 8 puede mostrar M1 2020–2022 directamente sobre ese instrumento. No hacer auditorías adicionales de contratos ni rollovers como paso previo; **terminar primero el generador**. **NO ejecutar, exportar, compilar ni validar parcialmente en NinjaTrader**. Migrar al final y realizar **UNA única validación integral** con NQ DEC2026.

## Qué cambió

- `NQNativeConditionCatalogV18.cs`: preserva **los 132 IDs originales V11**, sin cambiar nombre, valor, warmup ni predicados previos. Añade 24 **nuevas fórmulas matemáticas** basadas exclusivamente en OHLCV pasado: regresión lineal de precio, desviación de VWAP, Hull MA, ZLEMA, DEMA, OBV, Chaikin Money Flow, impulso ADL, Force Index, EOM, DMI, DMI×DX (ADX **proxy**, no cálculo Wilder ADX oficial), Aroon, Vortex, efficiency ratio de Kaufman, CMO, TSI, TRIX, DPO, MACD histograma, price-volume trend, Fisher transform, RVI y range-expansion impulse.
- Total **36 familias de fórmulas × 11 predicados históricos = 396 condiciones**, IDs **0–395**. Esto NO equivale a 396 indicadores independientes; varios comparten información de precio, tendencia o volumen y pueden estar correlacionados. Tampoco demuestra tener 100 indicadores técnicos independientes: esa meta de diversidad permanece pendiente.
- `NQNativeExitCanonicalV18.cs`: identidad booleana y de salidas versionada `EXCANv18`, registros `NQEX18_`, con los mismos 20 genes económicos y valores de salida, pero dominio de búsqueda de 396 IDs por cada una de las cuatro hojas booleanas. El canonicalizador V11 original se conserva sin modificaciones.
- `NQNativeEvolutionCoreV12.cs`: inyección **opcional** de canonicalizador nuevo en el mismo motor genético real (tournaments, cruzamiento por bloques, mutación, élites, inmigrantes y reinicio por estancamiento). Las llamadas antiguas siguen usando el canonicalizador V11 por defecto.
- `NQNativeHistoricalEvaluatorV12.cs`: nueva entrada explícita para evaluar un catálogo externo de señales + identidad, reutilizando **exactamente el mismo motor económico de simulación conservadora M1, stops, take-profit, comisiones, slip, horarios, 11:28/11:29 flatten y puntuación V9**. No modifica el motor nativo de fills de NT8.
- `NQNativeSignalCacheV14.cs`: catálogo y lector configurables; caché LRU de señales y ATR existente reutilizada sin romper el V14 anterior.
- `NQNativeScoreJournalV17.cs`: journal append-only con canonicalizador opcional, de modo que un V18 con 396 tipos se pueda reanudar mediante replay sin recalcular scores ya guardados. Cada versión nueva del scorer/catálogo usa identidad SHA distinta.
- `NQNativeExpandedResearchV18.cs`: ejecutor completo **V18 GA de 396 condiciones → cache de señales → simulador M1 V12 → fitness económico V9 → journal reanudable**. **Desarrollo 2020–22 únicamente**; sin datos reales disponibles para CI.

## Evidencia de CI

[GitHub Actions 42257874795 — 3/3 jobs SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42257874795)

1. **Cobertura / fórmulas**: **17.424** comparaciones de predicados (9.380 direccionales) en todos los 396 IDs, períodos 6, 12, 24 y 30; los **132 IDs V11 permanecen bit-a-bit iguales**; 19 fórmulas nuevas cotejadas contra casos monótonos alcistas/bajistas de referencia, cero divisiones inválidas con velas planas y volumen cero.
2. **Simulación histórica interna**: GA con **180 candidatos únicos**, los **36 tipos de familia** explorados, comparación de **24 genomas originales V11** cuyo P&L por trade, tiempo de cada operación, score V9 y costo son iguales en el evaluador original y el extendido. Probaron cache extendida y persistencia-replay del mismo genoma/score.
3. **Escala ampliada**: población 600, 190 generaciones, 24 élites, **109.464 genomas únicos puntuados** por una **función de fitness sintética**, **396/396 condiciones visitadas**, 4.857 duplicados omitidos y 65 estructuras redundantes. El CI de ese run informó 1.682 ms solo para generación/canonicalización/oracle sintético. **No** es tiempo ni rendimiento de 109.464 backtests reales de NQ.

## Estado de las limitaciones

- No hay estadísticas de **beneficio, PF, drawdown y supervivencia G0 sobre NQ DEC2026 real**. Las barras sintéticas prueban software, no edge; no se ha migrado ni ejecutado nada en NT8.
- El catálogo tiene **36 fórmulas**, no 100 indicadores estadísticamente independientes. Faltan familias verdaderamente distintas, sin inflar conteos con umbrales o reglas Booleanas.
- El **V18 generador ampliado ya calcula fitness económico V9 internamente**, pero el orquestador V16 de selección de portafolio, la congelación OOS y los validador walk-forward permanecen conectados al catálogo V11 original; todavía deben integrarse para aceptar **genomas EXCANv18** sin tratarlos como V11. Hasta entonces no afirmar un pipeline completo de portafolio con 396 condiciones.
- El rendimiento de 100k candidatos con **backtest M1 histórico real**, los costos de CPU/memoria y la caché para 396×7 períodos en 36 meses aún requieren ingeniería y pruebas masivas; el journal de V17 permite reanudar las evaluaciones.
- Fórmulas de indicadores en V18 no son necesariamente idénticas a indicadores preinstalados de NinjaTrader: requiere comparación al **final**, no ahora.

## Prioridad siguiente

**V19**: ampliar diversidad de fórmulas genuinas progresivamente sin pseudodiversidad; optimizar caché compactada/bulk M1 para valorar cientos de miles de candidatos, integrar el motor V18 con evaluación walk-forward y filtros/portafolio V13–V16, perfiles de tiempo/memoria y paquetes de resultados reproducibles. **Solo cuando el sistema completo esté listo, migrarlo a NinjaTrader 8 y validar una vez con NQ DEC2026**.
