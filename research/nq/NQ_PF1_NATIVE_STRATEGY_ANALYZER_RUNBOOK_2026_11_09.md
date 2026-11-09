# NQ PF1 — Arquitectura obligatoria: TODO desde NinjaTrader 8 Strategy Analyzer

**Decisión reafirmada por el usuario, 2026-11-09:** «la idea es correr todo desde NinjaTrader desde el Analyzer, mira bien cómo lo hicimos anteriormente y documéntalo también».

## 1. Regla principal (NO opcional)

El **único entorno operativo de investigación y validación de PF1** es **NinjaTrader 8 → New → Strategy Analyzer**, con los datos M1 históricos de NQ que YA están instalados en NT8. El usuario no debe tener que ejecutar Python, PowerShell, una CLI .NET, un archivo `.cmd` de backtest, exportar manualmente barras históricas ni subir TSV al chat para que se calculen los filtros.

**Los informes automáticos TSV que el propio NinjaScript guarda en `NQ_NativeResearchResults` sí son parte del proceso nativo**; no implican que el usuario deba sacar los datos de NinjaTrader para correr otra herramienta. Los desarrollos y CI externos pueden usarse para pruebas de ingeniería, **pero no son el flujo de ejecución del usuario**.

Este documento complementa y **NO modifica** [contrato PF1 v1.0.0](NQ_PORTFOLIO_FUNNEL_PF1_CONTRACT_2026_11_09.md), su [JSON de 121 filtros](NQ_PORTFOLIO_FUNNEL_PF1_RULES_2026_11_09.json) ni los objetivos fijos [V19–V25](NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md).

## 2. Cómo lo hicimos antes y qué ya funciona

1. El NinjaScript **`NQ_NativeResearchAnalyzer`** se seleccionó en **Strategy Analyzer**, se ejecutó sobre `NQ DEC26`, **Last / M1 / 2020–2022** y simuló **100.000 genomas NQ** en el motor de investigación interno. Salida observada: `NQ_NATIVE_END unique=100000` con 21 lotes de búsqueda y 100.000 únicos. No equivale a 100.000 órdenes que aparezcan en la pestaña Trades: era un motor **interno de investigación**, no una estrategia de órdenes nativas.
2. El script produjo automáticamente `NQ_100K_..._ALL_CANDIDATES.tsv`, `..._SUMMARY.tsv` y registros del motor. **No fue necesario ejecutar Python para generarlos**.
3. El origen de M1 admitido ya tiene identificadores en el ledger: `usableBarsSHA256=d35d429f71e37da175c02eb5c199d42a30a5f813af7fc0f1a26c5f5327a310fb`; el archivo `ALL_CANDIDATES` observado y verificado tiene `SHA256=be94604c3a735d6396fe71194c81dc56e8826f3dcf9aa1714282a3cc558c6980`.
4. La reauditoría anterior de 7 ternas obtuvo 0 aprobadas después de Monte Carlo. Eso era sobre un **embudo anterior**, no prueba de PF1 con un ejecutor común de 1 NQ.
5. El anterior `NQ_V25_FrozenAnalyzer` es un **puente de validación final de genes congelados**, no un generador de 100.000 ni un portafolio central. Ver [decisión nativa preexistente de Strategy Analyzer (PR V25 #84)](https://github.com/rgentil2/MES-Trading-Research/blob/feat/nq-v25-one-shot-ninjatrader-native-validation/research/nq/NQ_NATIVE_STRATEGY_ANALYZER_ARCHITECTURE_DECISION.md) del PR V25 #84. No mezclar objetivos.
6. Se hizo un intento con `NQ_PF1_E1_E3.py` y `EJECUTAR_PF1.cmd`, con resultados de preselección. **Ese paquete queda SUPERADO para ejecutar PF1** porque viola la decisión de usar solamente Strategy Analyzer. Los filtros/conteos pueden servir de referencia para QA, pero **no** se exige usar ese programa.

## 3. Mapa único del nuevo embudo

| Fase | Acción dentro de Strategy Analyzer | Estado de implementación |
|---|---|---|
| 1 | Banco de 100.000 y verificación de identidad | Motor nativo previo ya generó el banco; adaptador PF1 preparado |
| 2 | Filtro ligero ≥30 trades, stop y riesgo de 1 NQ ≤USD200 | Adaptador PF1 preparado |
| 3 | Propuestas 3–5 miembros, luego correlación ≤0,45 y concentración ≤40% | **Solo propuestas:** gates de diversificación aún pendientes |
| 4 | Ejecutar señales cronológicas compartiendo **máximo 1 NQ**, stops originales/ATR, conflictos, costos, bloqueos | **Pendiente: siguiente módulo** |
| 5 | PF neto≥1,25, ≥150 trades, ≥5/mes, Stability>30%, Symmetry>30%, DD≤USD2000 y pérdidas diarias≤USD1000 **del portafolio** | Pendiente |
| 6 | Monte Carlo sobre **los trades ejecutados del portafolio**, bloques de 8, 500/5000, P95 DD≤USD2000 y costos 1,5× | Pendiente |
| 7 | Prueba de órdenes/fills nativos en Analyzer, conciliación, congelación | Pendiente |
| 8 | OOS congelado 2023–24 y 2025–oct2026, **sin reentrenar** | Sellado |
| 9 | Decisión operativa de NQ con protecciones de cuenta verificadas | Pendiente |

**No hay forward test en demo obligatorio.** Solo **NQ**, nunca MNQ. El uso de M1 con cierre de vela no garantiza DD máximo ante gaps ni fills inesperados. Ninguna etapa no implementada puede aparecer como PASS.

## 4. Entrega nativa actual: `NQ_PF1_Analyzer`

**Formato de instalación:** ZIP compacto con `NQ_PF1_Analyzer.cs` y `LEEME_NQ_PF1_NATIVE.txt`, sin ejecutables externos. Copiar el `.cs` a `Documentos/NinjaTrader 8/bin/Custom/Strategies`, NinjaScript Editor → **F5**, y luego ejecutar **Strategy Analyzer → Backtest**. **No** usar el ZIP como `Tools → Import NinjaScript Add-On` porque no es el paquete exportado propio de NinjaTrader.

**Parámetros de Analyzer:** `NQ DEC26`, `Last`, `Minute 1`, `CME US Index Futures ETH`, **2020-01-01 a 2022-12-31**, zona horaria New York/ET; propiedades `ArmResearch=true` y `ConfirmDevelopmentM1ET=true`. `LedgerFile` en blanco busca el TSV original automáticamente; solo configurar la ruta dentro de Analyzer si el archivo anterior no está en las carpetas reconocidas. `ResultsFolder` en blanco conserva la carpeta habitual.

**Funcionamiento:** usa exclusivamente el runtime de NinjaScript; comprueba el contrato/costos incrustados, el instrumento, la cobertura temporal de las barras nativas, el hash completo del ledger y sus columnas/metadata, 100.000 IDs, 20 genes, identidad canónica, y elegibilidad estática o ATR condicional. Produce 100 propuestas de cada tamaño 3/4/5 con selección determinista. No usa Python, no coloca órdenes ni abre OOS.

**Resultados:** el `NinjaScript Output` deberá mostrar `PF1_NATIVE_BEGIN` y al terminar `PF1_NATIVE_END`, o `PF1_NATIVE_REJECTED`. El NinjaScript guarda automáticamente `*_STAGE1_2.tsv`, `*_STAGE3_PRELIMINARY.tsv` y `*_SUMMARY.txt` en `NQ_NativeResearchResults`. Si la tabla Trades muestra **0 trades**, es esperado en esta fase: se están clasificando genomas en un simulador de investigación, **no enviando órdenes**.

**Reproducción exacta de las 300 propuestas anteriores:** no se promete. Los filtros y universo son los mismos, pero el muestreo de propuestas ahora es nativo con semilla fija e implementación RNG explícita. **No seleccionar la mejor estrategia basándose en comparaciones retrospectives entre las dos listas**; el primer ejecutor central será el referente.

**Estado honesto de esta entrega:** archivo `.cs` preparado y QA estática de integridad; **compilación NinjaTrader real F5 pendiente en la instalación del usuario**, y backtest de mercado desde este script todavía no ejecutado. Tampoco se verificó una SHA nueva del OHLCV desde el script: el valor de barras se lee únicamente de la metadata del ledger. La fase 3 es `PROPOSALS_ONLY`, no `PORTFOLIO_PASS`.

## 5. Arquitectura de la implementación restante

El trabajo siguiente deberá **extender el mismo punto de entrada lógico PF1 en Strategy Analyzer**, no lanzar otro lenguaje/ejecutable externo. El motor central leerá señales barra por barra (o sus tablas de señales generadas dentro de NinjaTrader), resolverá causalmente conflictos con prioridad congelada, ejecutará **una sola posición NQ** bajo stops y controles, preservará los recibos de fills, evaluará economía+Stability+Symmetry+Monte Carlo, y escribirá ranking/causas de rechazo. No sumar P&L individuales como portafolio. El OOS se habilitará solo con identidad de freeze y gates previos verificables; cualquier resultado faltante = FAIL.

**El contrato PF1 no se versiona por cada avance de implementación.** Los hitos de ingeniería se documentarán como entregas del mismo PF1, y cambiar un umbral requerirá solicitud del usuario, nueva versión de contrato y changelog. El antiguo V25 conserva su significado histórico. No crear `V22 nuevo`, ni mover Monte Carlo a una estrategia individual. Código y docs anteriores no deben presentarse como aprobaciones operativas.

## 6. Evidencia de control

- **Contrato PF1:** 9 etapas, 121 filtros, con validador GitHub Actions ya aprobado.
- **Banco histórico:** 100.000 genomas, SHA de fuente/verificación indicado arriba.
- **Preselección de referencia del prototipo previo:** 12.373 elegibles de stop fijo; 65.376 ATR condicionales; 11.714 rechazados por riesgo fijo; 10.537 por <30 trades. No presentarlos como nueva corrida nativa del adaptador.
- **Entregable actual:** NinjaScript sin órdenes, reporte `PROPOSALS_ONLY`, compilación de NinjaTrader aún no confirmada.
- **Riesgo:** no abrir el OOS, no conectar a un broker, no entregar un bot de trading live basándose en esta fase.

> **Regla de aceptación:** la interfaz para el usuario siempre será **NinjaTrader 8 Strategy Analyzer**. Si una nueva entrega exige Python, PowerShell, dotnet run, .cmd de ejecución de backtests, exportación de barras o importaciones manuales para completar PF1, esa entrega **no cumple** la arquitectura, aunque sus cálculos sean correctos.
