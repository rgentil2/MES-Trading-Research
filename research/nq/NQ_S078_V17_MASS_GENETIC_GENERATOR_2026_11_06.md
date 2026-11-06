# NQ S0.78 — V17 generador masivo + puntuación persistente
Fecha: 2026-11-06

## Decisión vigente / referencia única de plataforma

**NQ DEC2026** es la serie que el usuario utiliza directamente en NinjaTrader 8, en la que visualiza M1 **2020–2022**. La auditoría adicional de contratos, rollovers y exportaciones **NO** forma parte del camino crítico. Terminar primero el **generador** y los mecanismos completos de búsqueda, evolución, filtros, riesgo y portafolio en C#; migrar a NT8 y realizar **UNA sola validación integral al final**. No pedir ejecuciones, exportaciones ni compilaciones intermedias.

Esta decisión está registrada en las cabeceras actuales de `NQ_PROJECT_MASTER.md` y en la entrada S0.77 de `NQ_RESEARCH_LOG.md`.

## Entregables verificables V17

1. **Capacidad de generación con puntuación** en el motor C# genuino `NQNativeEvolutionCoreV12.cs`, el canonicalizador V11 y `tests/NQNative100kEvolutionV17Test.cs`.
   - Reproducibilidad: semilla **20261106**, población 600, **190 generaciones**, 24 élites y función de fitness sintética determinista que permite selección real, cruces, mutaciones, inmigrantes y reinicios.
   - **109.464 candidatos únicos efectivamente puntuados** (`600 + 189 × (600-24)`), **114.081 intentos**, **4.447 duplicados rechazados**, **170 estructuras redundantes rechazadas**, **73.757 mutaciones**, **66.753 cruces**, **37.560 inmigrantes**; las **132 condiciones** aparecen entre los candidatos.
   - Dos ejecuciones de CI reportaron un tiempo de núcleo genético de **2.014 y 1.475 ms** en runners GitHub, con el mismo checksum SHA256 de extremos de secuencia y puntuación: `78936c2382f423fabf5bc7a8b7dae224bbff0dc5ec0b1025516952d6c9116c41`.
   - **NO es un benchmark de 109.464 backtests de NQ real**: el scorer usa explícitamente una función sintética, sin millones de barras por candidato, sin fills de NT8 ni beneficios económicos de mercado.

2. **Persistencia y reanudación del fitness**: `research/nq/ninjatrader/NQNativeScoreJournalV17.cs`, con test independiente `tests/NQNativeScoreJournalV17Test.cs`.
   - Diario append-only con identidad de fuente SHA256, fingerprint de parámetros de GA/rangos/scorer, vector exacto de 20 genes y puntuación de doble precisión bajo checksum por fila.
   - Reanuda mediante **repetición determinista de la secuencia del GA** pero usando el score guardado sin recalcular el backtest; el número máximo de generaciones se puede ampliar conservando población, semillas, mutación, dominio y scorer.
   - Si cambia la fuente histórica, la función de fitness, el dominio o la configuración, **rechaza reutilizar** el journal. Rechaza filas duplicadas o corruptas; no repara parcialmente archivos truncados sin auditoría.
   - Test de integración sintético: primera etapa **222** scores; ampliación a 9 generaciones **270** nuevos scores para **492** únicos; tercer reinicio **0 llamadas** al scorer y secuencia idéntica. No se asume persistencia de estado interno aleatorio no documentado: se usa regeneración determinista.
   - Método `RunWithHistoricalJournal` conecta el diario con **V14 cache + V9 score sobre V12 fills M1 estimados**; todavía no ejecutado en datos reales.

3. **CI**: `.github/workflows/nq-v17-100k-generator-qa.yml`, dos jobs verdes. Ejecución: https://github.com/rgentil2/MES-Trading-Research/actions/runs/42243570744

## Siguientes brechas del generador — prioridad técnica

1. **Evaluator alto rendimiento real**: motor de backtest/costos M1 sobre datos reales del mismo histórico visible en `NQ DEC2026`, reproducibilidad de señales/fills, y benchmark **100k candidatos con evaluación económica real**, no solo oracle sintético. No pedir mover datos a GitHub ni auditarlos por contratos ahora.
2. **Biblioteca independiente**: las actuales 132 son **12 familias × 11 condiciones**, no 132 fórmulas técnicas independientes. Ampliar cobertura de indicadores y reglas sin generar pseudodiversidad ni fugas temporales.
3. **Generador operativo**: configuración declarativa, diversidad por familias y estructuras, estrategias con lógica flexible, genes de salida y protección, ranking/pareto, reglas de parada, registros de progreso, checkpoints reanudables más allá del score journal, presupuesto de CPU/memoria y búsqueda configurable mayor que 100k.
4. **Portafolio y estabilidad**: usar los filtros originales V13/V15, contrastes walk-forward y correlación; mantener el holdout externo separado hasta congelar selección.
5. **Al final y una sola vez**: preparar paquete migrable/compilable a NinjaTrader 8 usando `NQ DEC2026`, ejecutar comparación definitiva de operaciones y decidir aceptar/rechazar basado en resultados reales. No pedir F5 ni pantallas intermedias.

**Estado:** V17 fuente de generador y puntuación persistente aprobada por CI sintético; no hay prueba de edge histórico ni autorización para operar.
