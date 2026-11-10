# NQ PF1 — REGISTRO DE CAMBIOS (APPEND ONLY)

## 2026-11-09 — PF1 v1.0.0: contrato inicial

- Decisión: congelar nueva secuencia de nueve embudos; objeto de evaluación = portafolio central NQ de 3–5 miembros, 1 NQ máximo.
- Universo IS = 2020–2022; OOS 1 = 2023–24; OOS 2 = 2025–oct2026; 46 meses OOS; cero reoptimizaciones fuera de muestra.
- Stability >30%, Symmetry >30% con fórmula operativa fijada en el contrato. Aplicar al portafolio, no individualmente.
- Continuidad de umbrales: PF>=1.25; mínimo 150/5 mensuales en portafolio; DD<=USD2000; pérdida diaria<=USD1000; MC P95 DD<=USD2000; costos 2 ticks por lado + USD4.68 RT, estrés 1.5x, sin doble cargo.
- Baseline de diseño antes propuesto y ahora fijado: 30 trades individuales; riesgo 200; pausa 500, salida 750, bloqueo DD1600; MC confirmatorio 5000.
- Efecto sobre V19–V25: ninguno; **no** dar por implementado PF1, no reinterpretar pruebas anteriores.
- Estado real: SPEC_ONLY; ningún portfolio puede habilitarse a operar por este commit.

## Plantilla obligatoria para futuras propuestas

### AAAA-MM-DD — PF1 vX.Y.Z

- Solicitud y decisión expresa del usuario:
- Valor previo → nuevo, fórmula y motivo:
- Impacto en OOS / contaminación / nueva campaña:
- PR y commits (conservar historia):
- Pruebas de regresión y evidencias:
- Estado aprobado / rechazado / pendiente:

No editar entradas anteriores; agregar una nueva. Si falta aprobación, no cambiar los valores.


## 2026-11-09 — PF1 v1.0.0: enmienda de ejecución NO normativa

- Corrección de implementación sin cambio de umbrales: todo PF1 corre desde NinjaTrader 8 → Strategy Analyzer; no Python, PowerShell ni CLI externa.
- El generador nativo previo produjo 100.000 genomas y TSV desde Analyzer. El prototipo Python de embudos 1–3 queda SUPERADO como herramienta de ejecución, no se borra su evidencia.
- Guia: [Arquitectura nativa PF1](NQ_PF1_NATIVE_STRATEGY_ANALYZER_RUNBOOK_2026_11_09.md).
- Entrega C# NQ_PF1_Analyzer: importación del ledger de NT8, cribado y propuestas; pendiente F5/backtest real, aún no aprobó embudo 3; embudos 4–9 pendientes.
- No se modifican Stability >30%, Symmetry >30%, costos, OOS, limites de 1 NQ, ni objetivos V19–V25. No se habilitan operaciones.

## 2026-11-09 — PF1 v1.0.0 / NinjaScript R2 — corrección de error de transcripción

- **Causa:** versión nativa R1 rechazaba el ledger original por `PF1_LEDGER_SOURCE_BARS_SHA_MISMATCH`: se había escrito `...eb5a199...` cuando el origen íntegro dice `...eb5c199...`.
- **Evidencia:** SHA completo del ledger 100K `be94604c3a735d6396fe71194c81dc56e8826f3dcf9aa1714282a3cc558c6980` verificado; fuente IS `d35d429f71e37da175c02eb5c199d42a30a5f813af7fc0f1a26c5f5327a310fb`.
- **Cambio:** solo constante `SourceUsableBarsSha256` en el NinjaScript + identificador build R2 en código e instalador + instrucciones actualizadas. **No** se debilita validación del ledger ni cambian las 121 reglas del contrato PF1.
- **Estado:** ZIP R2 entregado; aún requiere compilación F5 y backtest NT8 para verificar `PF1_NATIVE_END`.
