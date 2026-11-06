# NQ — CONTRATO DE ALCANCE DE VERSIONES (INMUTABLE A PARTIR DE V23)

**Fijado:** 2026-11-06. **Origen:** solicitud expresa del usuario: «No quiero que me andes cambiando las descripciones de las versiones; con cada versión tenemos un objetivo».

## Una versión = un objetivo único

| Versión | Objetivo fijo / no renegociable | Definición de terminado |
|:--|:--|:--|
| **V19** | Alcanzar **120 fórmulas técnicas implementadas** y 1.320 condiciones combinatorias | Código de las 120 fórmulas, compatibilidad V11/V18 y CI de referencias matemáticas |
| **V20** | Conectar los 1.320 tipos al embudo de robustez, walk-forward, portafolio y OOS | GA V19→G0 V13→riesgo V15→WF V20→campaña congelada V16, CI sintético |
| **V21** | **Evaluador económico M1, optimización de caché y registro reanudable de resultados** | Simulador V12/V9, memo numérica, SHA journal, ranking y recibos de operaciones |
| **V22** | **Robustez, walk-forward y portafolios de 3–5 estrategias** | ≥150 trades, ≥5/mes ×36, PF neto≥1,25, net>0, costes 1,5×, DD≤$2k, pausa diaria<$1k, Monte Carlo, estabilidad por año, correlación/riesgo flotante conjunto, tests positivos/negativos |
| **V23** | **GENERADOR COMPLETO Y RESULTADOS FINALES:** un ejecutor configurable, persistencia, aplicación de filtros, rankings, causas de rechazo, operaciones, P&L, drawdown, estabilidad, resultados por año, portafolios y parámetros definitivos; **consolidar los PR en una versión reproducible** | Un único `--run` offline; expediente completo por ejecución, SHA de datos/config/archivos, reinicio idéntico, auditoría de rechazos y una sola rama/PR acumulada de integración hacia `main` |
| **V24** | **Escalamiento de backtests económicos completos:** rendimiento, memoria y aproximación progresiva a ≥100.000 backtests M1 de 36 meses | Métricas honestas de throughput/CPU/RAM y tests económicos de períodos extensos. No cambiar ni redefinir el producto V23 |
| **V25** | **Una sola integración y validación integral final en NinjaTrader 8 con NQ DEC2026** | Contrastar señales, fills, comisiones, P&L y DD del generador frente a Strategy Analyzer/NT8; no anticipar rentabilidad |

**Estas descripciones no se renumeran.** Un bug de V22 se puede corregir en el historial o en V23 y probar como regresión, pero **no** se presenta como nuevo objetivo de V23. La optimización masiva **es V24**, no V23. El puente nativo **es V25**, no V23.

## Reglas de precisión financiera

- **120 fórmulas matemáticas** no demuestra **120 indicadores estadísticamente independientes** ni paridad exacta con todos los indicadores comerciales de NinjaTrader.
- Las pruebas de GitHub trabajan con barras OHLCV **sintéticas**, salvo cuando se documente expresamente la procedencia verificable del mercado. No confundir 109.464 genomas puntuados con **fitness sintético** con backtests económicos auténticos de todo NQ.
- Una estrategia o portafolio que supera controles en datos fabricados demuestra **lógica de aceptación**, no existencia de ventaja económica real.
- Nada del generador autoriza trading en vivo ni certifica reglas de MFFU. El riesgo M1 con high/low adverso es un **proxy** y debe cotejarse al final con NT8.
- Desarrollo y búsqueda sobre **2020–2022 solamente**; validación externa **2023–24** y final **2025–oct2026** congeladas antes de abrir. No buscar ni ajustar parámetros sobre los holdouts.
- **Instrumento final declarado por el usuario:** `NQ DEC2026`; los datos M1 2020–22 están visibles en su NinjaTrader. No forzar auditorías/descargas de contratos, F5 ni backtests intermedios. **Terminar primero; una sola migración y prueba final V25.**

## Criterios de aceptación específicos de V23

1. Compilación determinista de un **proyecto ejecutable .NET8** sin dependencias nativas NinjaTrader y sin llamadas de ejecución de órdenes.
2. Archivo de configuración con fuente, genes basales, población/semilla, número de generaciones, límites de indicadores/caché, filtros de riesgo/Monte Carlo, portafolio 3–5 y corte congelado.
3. Ejecutor único que llame **V21→V22**, no que replique genéticamente otra biblioteca ni que reentrene con 2023+.
4. Reportes separados y completos: `candidates_full.tsv` (TODOS los genomas GA), `rejected_candidates.tsv` (motivos o límite de auditoría), `robustness_audits.tsv`, `annual_development.tsv`, `monthly_development.tsv`, `audited_trades.tsv`, `portfolio_decision.tsv`, `walkforward.tsv`, `definitive_parameters.tsv` (solo genes realmente congelados), `run_summary.txt`.
5. Journal duradero `economics_ledger.tsv` con score, net, PF, DD, total trades y checksum; salida shortlist `ranking_top.tsv` y `finalist_trades.tsv`, prueba de **0 rebacktests** sobre genes ya calculados.
6. Bloqueo `campaign.lock` con SHA de configuración y **también** del contenido efectivo de las barras; manifest `artifacts.sha256` que detecta archivos editados.
7. **Repetición bit a bit** de los archivos de resultados, sin incluir métricas volátiles como número de backtests recién calculados en el contenido del reporte.
8. Consolidar el árbol fuente V11–V23 en un único archivo `.csproj` explícito, un workflow de integración y un PR acumulado hacia `main`. Documentar de manera transparente si el PR **no ha sido fusionado**.
9. Generar informes **aunque el portafolio se rechace**. No mostrar parámetros «definitivos» ficticios cuando no existe una estrategia aprobada.

**V23 NO incluye** demostrar 100k evaluaciones de 36 meses (V24) ni implementar NinjaTrader NT8 nativo (V25).
