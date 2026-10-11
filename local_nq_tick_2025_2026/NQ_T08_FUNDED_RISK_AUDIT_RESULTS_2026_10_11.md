# NQ T08 — Resultados verificables de auditoría de riesgo (11-oct-2026)

**Ejecución:** [GitHub Actions #38175102957](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38175102957), **SUCCESS**: pruebas sintéticas, siete trabajos mensuales y consolidación final. El prerregistro `NQ_T08_FUNDED_RISK_AUDIT_PREREG_2026_10_11.md` antecede el nuevo simulador y sus outcomes. Código `nq_t08_risk_audit.py`, agregador `nq_t08_risk_aggregate.py`, pruebas `test_nq_t08_risk_audit.py`.

**Alcance:** exclusivamente desarrollo octubre 2025–abril 2026, 140 días fuente y 135 elegibles; cada uno de los siete archivos Tick Last se descargó desde almacenamiento **privado** con SHA256 verificado. Ningún outcome de mayo–junio 2026, julio–septiembre 2026, 2025 original ni 2026 original fue consultado. Este es un análisis retrospectivo **post-selección**, no confirmación OOS. T02 y T05 se ejecutaron como carteras independientes, NUNCA sumando beneficios.

## Comparación completa sobre los mismos 135 días y 7 meses

| Cartera | Trades | Neto base USD | Neto estrés USD | PF base | PF estrés | DD Last-envolvente base USD | DD Last-envolvente estrés USD | Mín. trades/mes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T02 padre | 190 | +8.420 | +6.860 | 1,30893 | 1,24356 | **3.205** | **3.385** | 17 |
| T05 377 | 115 | +6.220 | +5.102,50 | 1,39923 | **1,31826** | **1.750** | **1.825** | **8** |
| T05 233+377 | 59 | +5.395 | +4.657,50 | 1,77016 | 1,64219 | **1.380** | **1.422,50** | **2** |

**Costes idénticos a T04:** base: USD5 RT + 1 tick adverso por lado; estrés: USD7,50 RT + 2 ticks adversos por lado. No son comisiones verificadas de broker, ni la prueba estrés es literalmente 1,5× de toda clase de gasto. El simulador mantiene 1 NQ, máx. 2 trades diarios, sin solapamiento, stop 16–48 ticks, target 2R, salida a 300 s o 11:30 ET, bloqueo de nuevas entradas si P&L cerrado <=−USD600.

**Control de regresión:** se reprodujeron EXACTAMENTE los 190/115/59 trades y los seis P&L acumulados baseline/estrés ya registrados en T04/T05. El evaluador también coteja diariamente trades, neto, conteo y categorías de ambigüedades contra el motor original, y se niega a continuar ante divergencia.

## Hallazgo causal sobre evaluación de fondeo

- **T02 padre: falla el filtro de riesgo de referencia** por drawdown Last-envolvente en ambos costes (>USD2.000) y PF estrés por debajo de 1,25. Conservar como padre y diagnóstico, NO escoger por el mayor P&L bruto.
- **T05 233+377: falla criterio preliminar de frecuencia.** 2 operaciones en noviembre y 4 en febrero; menor DD observado y PF alto no resuelven actividad insuficiente para el objetivo recurrente. Se conserva como componente condicional, no como ganador obligatorio.
- **T05 377: único candidato que supera la pantalla preliminar bajo costes SUPUESTOS.** 115 operaciones, mínimo 8 en cada mes, PF estrés 1,31826 y DD Last envolvente estrés USD1.825, por debajo de referencia USD2.000. **Solo USD175 de margen; esta pantalla NO acredita elegibilidad de fondeo.**

Detalle mensual T05-377 escenario estrés (trades en paréntesis, según resultados históricos T05): oct-25 +USD137,50 (15), nov-25 +USD760 (8), dic-25 +USD1.450 (22), ene-26 +USD1.572,50 (19), feb-26 **−USD827,50** (13), mar-26 +USD1.372,50 (21), abr-26 +USD637,50 (17). Mes negativo NO se excluye ni se explica retrospectivamente para volverlo ganador.

## Advertencias esenciales

1. **El DD nuevo es envolvente conservadora de marcas Last, no DD de firma ni estimación de fills reales.** Se retoman high-water marks entre meses para calcular caídas acumuladas; en grupos de igual timestamp se toma orden posible adverso high→low aun sin conocer orden real. Puede exceder caídas cronológicas reales en algunos timestamps y subestimar riesgos de mercado no representados por Last/Bid/Ask real, saltos o ejecución en broker. No llamar `realized broker trailing DD`.
2. La cifra **USD2.000** es una referencia histórica no verificada de un escenario anterior de cuenta fondeada 50K. Se requieren **nombre, plan y reglas vigentes** de la firma, liquidación en drawdown abierto o al cierre, comisiones completas, límites de posiciones, consistencia e inactividad. En particular, **USD175 es escaso margen** frente a errores/fricciones.
3. Falta reconciliación real minuto a minuto de archivo independiente NQ 1m con Tick Last y validación de ejecución BBO, no solo pruebas sintéticas. El ZIP 1m sí está guardado en GitHub privado y aún no se usó para conciliación efectiva; NO trasladarlo a runners públicos.
4. **Sin ETF nominal/ROI de bolsillo**: siete meses exploratorios no prueban una rentabilidad anual sostenible > max(15%, VOO TR, QQQM TR). Sostener las políticas de hipótesis combinadas, ablations, régimen, multiplicidad Holm/BH y preregistro para **familias nuevas**. No confundir aprobación de pantalla de riesgo con hipótesis/estrategia confirmada.
5. La cifra de $50K es capital nominal de evaluación, NO capital personal aportado ni payouts cobrados.

## Decisión y siguientes puertas de control

**Estado:** `T05_377_CONDITIONAL_RISK_SCREEN_PASS_NOT_VALIDATED`, `T02_REFERENCE_RISK_FAIL`, `T05_233_AND_377_FREQUENCY_FAIL`. Ninguno es `VALIDATED_FOR_FUNDED_TRADING`.

**Prioridad inmediata (sin tocar holdouts):**
- Cerrar **calidad y ejecutabilidad**: comparar Minute Last original contra Tick Last del mismo contrato/ET, inspeccionar Bid/Ask reales de desarrollo en instantes posteriores a la señal, estimar adversidad ejecutable sin usar datos posteriores para seleccionar los parámetros de la estrategia.
- Verificar reglas escritas y coste real del plan de fondeo (50K) y riesgo con 1 NQ vs sizing MNQ (no suponer que MNQ tiene el mismo spread ni liquidez que NQ).
- Después, aplicar estabilidad por semana/mes/trimestre y robustez de parametrización *sin* seleccionar retrospectivamente variantes: freeze y revisión independiente.
- Solo si pasa, congelar estrategia completa (señal, entrada, SL, TP, sizing, prioridad, costes, rechazos por ambigüedad, riesgos, versión/hash). Abrir **mayo–junio 2026** una sola vez para validación interna. **Julio–septiembre 2026** permanece sellado para pseudo-forward histórico final.
