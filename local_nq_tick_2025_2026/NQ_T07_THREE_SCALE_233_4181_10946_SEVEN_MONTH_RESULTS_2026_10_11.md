# NQ T07 — Resultado real de estudio DEV con tres contextos 233/4.181/10.946 (2026-10-11)

**Estado:** 7/7 trabajos [GitHub Actions SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38168829410). Prerregistro ANTERIOR a los outcomes: [NQ_T07_THREE_SCALE_233_4181_10946_PREREG_2026_10_11.md](./NQ_T07_THREE_SCALE_233_4181_10946_PREREG_2026_10_11.md). **EXPLORATORY / POST-SELECTION DEVELOPMENT; NOT FOR LIVE/FUNDED TRADING.**

**Período:** solo octubre 2025–abril 2026, 140 días de archivos NQ Tick Last privados (SHA256 mensual comprobado), **135 sesiones elegibles**, 298 oportunidades T02 originales. No se abrieron resultados monetarios de mayo–junio (validación interna reservada) ni julio–septiembre (sellado), ni los holdouts originales de minuto del ZIP NQ/MNQ. 7 variantes de escala cuentan **registros Last**, no contratos ni ticks de precio. Fuente Last-only, no rellenos demostrados de mercado.

## Pregunta predefinida

El usuario utiliza **233** (corto/ejecución), **4.181** (intermedio), **10.946** (amplio) + contexto diario. ¿Una tendencia amplia alineada con la reversión, retroceso medio en contra y giro rápido en el corto mejoran la regla madre T02 de ruptura fallida y desaceleración de operaciones?

Se exigieron cierres completos, estrictamente anteriores a la señal, con barras reiniciadas a 08:00 ET. No se usó contexto diario verdadero: el export Tick Last disponible 08:00–12:00 ET NO garantiza una vela de sesión diaria completa. T05 233+377 se preserva como control histórico. Near-count triple **240/4.200/11.000** conserva reglas equivalentes.

## Resultado comparado de 7 meses de desarrollo — carteras ALTERNATIVAS, NO SUMABLES

| Regla | Trades simulados | P&L neto base USD | P&L neto costes estrés USD | Neto USD por oportunidad T02 original | Meses positivos base | Media/trade base USD |
|---|---:|---:|---:|---:|---:|---:|
| T02 padre, sin filtros | 190 | **+8.420** | +6.860 | +28,26 | 6/7 | +44,32 |
| T05: 233+377 | 59 | **+5.395** | +4.657,50 | +18,10 | **7/7** | +91,44 |
| T07: 233+4.181 | 96 | +2.635 | +1.635 | +8,84 | 5/7 | +27,45 |
| **T07: 233+4.181+10.946** | **29** | **+790** | **+557,50** | **+2,65** | **4/7** | +27,24 |
| Control 240+4.200+11.000 | 24 | **−980** | **−1.200** | **−3,29** | 2/7 | −40,83 |

Costes de fuente T04 **SUPUESTOS** y sin validar proveedor: baseline comisión **USD 5 round-trip +1 tick adverso por lado**, estrés **USD 7,50 RT +2 ticks adversos por lado**. Stop 25% del rango inicial acotado **16–48 ticks**, TP **2R**, timeout **300s**, máximo **2 operaciones por día**, 1 NQ, señales T02 **09:40–11:10**.

### Comparación mensual de la triple Fibonacci T07

| Mes | Trades / P&L base USD | Triple control: trades / P&L base USD |
|---|---:|---:|
| Oct-25 | 3 / −275 | 3 / −285 |
| Nov-25 | **2 / +220** | **1 / +470** |
| Dic-25 | 5 / −85 | 3 / −555 |
| Ene-26 | **4 / −305** | **4 / −290** |
| Feb-26 | **3 / +685** | **2 / −425** |
| Mar-26 | 7 / +395 | 7 / −315 |
| Abr-26 | 5 / +155 | 4 / +420 |
| **Total** | **29 / +790** | **24 / −980** |

La combinación de tres escalas deja solo **~4,1 trades por mes** y **cuatro meses con menos de cinco operaciones**, por debajo de la frecuencia deseada. La mejora descriptiva frente al control similar es pequeña y de escasa muestra; **no** implica ventaja Fibonacci confirmada. La regla de tres escalas, aplicada como filtro estricto, **pierde mucha frecuencia y rentabilidad por oportunidad**.

### Análisis de límites / decisión

- **T07 TRIPLE: no promover.** Aunque el control triple no-Fibonacci fue negativo, el triple Fibonacci no cumple robustez y frecuencia deseadas; el outcome es de desarrollo repetidamente examinado, no un test confirmatorio. No escoger otro Fibonacci para rescatarlo.
- **T07 233+4.181: tampoco promover** con esta condición direccional específica: neto por oportunidad T02 original +8,84 vs +18,10 de T05 233+377, 96 trades en vez de 59, menor expectativa/trade. Conservar idea de contexto medio como descriptor, no validación de filtro.
- **T05 233+377** conserva liderazgo descriptivo por DD simulado y expectativa por trade, con frecuencia heterogénea (2 trades en Nov y 4 en Feb). **T05 377 solo**, del experimento anterior, mantiene 115 trades en siete meses (~16/mes), pero un mes negativo y requiere comparar DD flotante por firma; no descartar.
- **T02 padre** con 190 trades y +US$8.420 sigue siendo benchmark que permite detectar si los filtros realmente añaden robustez o solo bajan frecuencia.
- Filtro 10.946 puede seguir sirviendo como **contexto descriptivo**, pero no debe agregarse como requisito rígido a T02 según estos resultados. 08:00 ET como ancla puede no coincidir con chart NinjaTrader ETH completo. La fecha de nacimiento del tick no representa necesariamente orden secuenciado de bolsa cuando hay múltiples prints idénticos en timestamp.
- Contexto **diario verdadero** requiere barras completas de sesiones previas, no inventar cierres a partir del período 08:00–12:00.
- **Gate prioritario ahora:** dejar de añadir filtros ad hoc; auditar equity **intradía flotante continuo/trailing DD**, comisiones de firma reales, límites de pérdida por sesión/mes, riesgo de 1 NQ vs varios MNQ y robustez bajo costos. Seleccionar entre T05 377, T05 233+377 y T02 según **riesgo y frecuencia**, no solo P&L.
- Hasta superar ese gate, no abrir **mayo–junio 2026** para outcomes ni julio–septiembre 2026 sellado.

## Reproducibilidad

Código y tests: [nq_t07_three_scale.py](./nq_t07_three_scale.py), [nq_t07_month.py](./nq_t07_month.py), [test_nq_t07_three_scale.py](./test_nq_t07_three_scale.py). Pruebas sintéticas y 7 meses completados con los mismos T04 costes y capital alternativo; T02 y T05 se reproducen exactamente frente a informes previos. Fuente Last NQ privada Dev verificada por SHA256 y temporalmente extraída en runners públicos que borran los archivos, sin exponer licencias.

**No declarar ROI anual, beneficios seguros, alfa estadísticamente significativa, ejecución verificada o compatibilidad con fondeo a partir de esta etapa.**
