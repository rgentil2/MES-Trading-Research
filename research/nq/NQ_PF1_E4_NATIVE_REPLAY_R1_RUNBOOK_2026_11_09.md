# NQ PF1 E4 R1 — Ejecutor central de un contrato NQ desde Strategy Analyzer

**Fecha:** 2026-11-09. **Contrato:** [NQ PF1 v1.0.0](NQ_PORTFOLIO_FUNNEL_PF1_CONTRACT_2026_11_09.md). **Estado:** código preparado, instalación y compilación NinjaTrader real pendientes. No autoriza trading.

## Antecedente validado

El usuario ejecutó correctamente NQ_PF1_Analyzer R2 desde Strategy Analyzer: 100.000 genomas, 12.373 candidatos de stop fijo elegibles, 65.376 ATR pendientes, y 300 propuestas (100 por tamaño 3/4/5). No repetir la generación del banco ni alterar los filtros.

## Entrega E4 R1

- NinjaScript nuevo **NQ_PF1_CentralExecutor.cs**, independiente del R2 funcional; instalador CMD + JS Windows y LEEME, **4 archivos**.
- ZIP entregado por chat **NQ_PF1_E4_EJECUTOR_CENTRAL_ANALYZER_CMD_R1.zip**, SHA256 **e9f4486032f7e728a7b272b7b4ebd66735663847792725a9028ff0a339513525**.
- Fuente C# SHA256 **9559ca3466b48c4f28f013e89e9e321e4fca22699ca1eecb1a8738de0283826b**.
- **Alcance de este PR: documentar la entrega**, no añadir el código C# al repositorio; el ZIP tiene la fuente. Ninguna ejecución NT8 real o compilación F5 ha sido verificada en este entorno.

## Implementación interna

1. Lee y verifica SHA256 íntegro del ledger original 100k: **be94604c3a735d6396fe71194c81dc56e8826f3dcf9aa1714282a3cc558c6980**, y metadata usableBars **d35d429f71e37da175c02eb5c199d42a30a5f813af7fc0f1a26c5f5327a310fb**.
2. Lee automáticamente los reportes de 300 propuestas PRELIMINARES del R2; compara ID, 20 genes, canonical, SHA parcial y tipo de stop de cada miembro con el registro original.
3. Usa barras reales disponibles en Strategy Analyzer, NQ DEC26, Last, M1, ETH, 2020–2022; filtra sesiones RTH sin 120 minutos completos. **La igualdad byte por byte con las barras fuente no está comprobada y debe conciliarse en E7.**
4. Calcula señales por candidato con las clases originales previamente instaladas en el generador: NQBarV11, NQNativeConditionCatalogV19 y NQNativeATRExitMathV5. Requiere que ya existan y compilen en NT8.
5. Resuelve señales simultáneas por **prioridad de ID ascendente** y solo permite **una posición NQ** por combinación. La señal se observa en una vela completada; se simula entrada a apertura de la siguiente. Calcula stop fijo/ATR, TP, salida por hora, gaps adversos y stop primero ante SL/TP simultáneos.
6. Riesgo de stop por trade: stopTicks × USD5 + costo total USD24,68 ≤ USD200. Comisiones US$4,68 RT, deslizamiento **2 ticks en entrada y 2 en salida**, aplicado una sola vez; se mantienen las pausas USD500, USD750 y bloqueo por DD adverso USD1600. La limitación OHLC M1 impide garantizar stops, riesgo intrabarra y ejecución en vivo.
7. Genera automáticamente archivos TRADES.tsv, AUDIT.tsv y SUMMARY.txt de las operaciones realmente simuladas por el ejecutor **central**, sin sumar resultados independientes. Estado fijo: **REPLAY_DIAGNOSTIC_ONLY_NOT_PORTFOLIO_PASS**.

## Cómo ejecutar en Windows / NT8

1. Descomprimir el ZIP y ejecutar **INSTALAR_NQ_PF1_E4.cmd** con doble clic (solo instala el C#, conserva y no reemplaza R2).
2. NinjaTrader 8 → NinjaScript Editor → **F5**. Si falla la compilación por dependencia o sintaxis, reportar errores sin ejecutar.
3. New → Strategy Analyzer → Backtest → estrategia **NQ_PF1_CentralExecutor**; NQ DEC26, Last, Minute 1, CME US Index Futures ETH, 01-01-2020 hasta 31-12-2022; zona horaria ET.
4. Activar ArmResearch y ConfirmDevelopmentM1ET; dejar rutas en blanco; ProposalsPerSize = **1** para evaluar **3 portafolios de integración** (uno de 3, uno de 4 y uno de 5 integrantes).
5. Ejecutar y revisar logs PF1_E4_BEGIN, PF1_E4_SIGNALS y PF1_E4_END o PF1_E4_REJECTED con razón. Para ampliar la misma implementación a 300 combinaciones, ProposalsPerSize=100.

## Estado contractual

- **Solo E4 inicial en diagnóstico**, no marcar las fases 3, 4 definitiva, 5, 6, 7, 8 o 9 como PASS.
- No se evalúan en esta entrega como filtros eliminatorios Stability >30%, Symmetry >30%, PF >=1,25, correlación, Monte Carlo, OOS, ni paridad nativa.
- Cero archivos externos de barras descargados, cero procesos Python o PowerShell de análisis, **cero órdenes NinjaTrader reales** y cero acceso OOS 2023–2026.
- CI no equivale a validación en NinjaTrader. Antes de pasar a fases 5–6 faltan prueba F5 y confrontación de los fills simulados contra un motor independiente con las mismas barras.
- Contrato PF1 v1.0.0 y versiones históricas V19–V25 **sin cambios**.

## Evidencia QA disponible

Se comprobó por SHA256 el ledger original de 100k, fórmulas de costo y validaciones de no OOS/no órdenes de código; ZIP 4/4 sin errores. No se dispone de NinjaTrader 8 en este entorno para probar compilación o la ejecución de E4 en datos reales.
