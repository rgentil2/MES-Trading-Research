# NQ H05–H07 — Nuevas hipótesis sobre niveles y volumen (2020–2024)

**Fecha:** 2026-10-09. **Alcance:** exploratorio, únicamente 2020–2024; ningún resultado de 2025/2026 abierto. Las reglas de las tres hipótesis se registraron y su versión se congeló en GitHub antes de calcular los efectos. Las siete pruebas del código pasaron localmente.

## Resultados principales — un contrato NQ, 30 minutos después de entrar

| Hipótesis | Mecanismo | N | Efecto neto medio (USD) | Neto total (USD) | PF | Años positivos | IC 90% de media USD | p una cola | q BH (H05–H07) |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| NQ-H05 | Barrida y rechazo de máximo/mínimo RTH previo | 545 | +7,98 | +4.351,70 | 1,019 | 3/5 | [-64,96, 82,32] | 0,429457 | 0,695630 |
| NQ-H06 | Ruptura de máximo/mínimo previo, dos cierres y volumen relativo 1,25x | 745 | -56,72 | -42.256,30 | 0,871 | 1/5 | [-121,93, 7,04] | 0,927607 | 0,927607 |
| NQ-H07 | Primera ruptura fallida de máximo/mínimo nocturno | 229 | +5,79 | +1.325,54 | 1,015 | 2/5 | [-96,72, 109,53] | 0,463754 | 0,695630 |

**Decisión:** las tres fallan el nuevo Gate 1 (q<=0,10 y CI90 por encima de cero). **No hay estrategia ejecutable**, stop loss ni take profit; son efectos causales de 30 minutos con fills supuestos. NQ H06 es netamente negativa. H05 y H07 son casi neutrales y se vuelven negativas al añadir solo **un tick adverso adicional por lado** (H05 -US$1.098,30; H07 -US$964,46). En H06 ese mismo estrés produce -US$49.706,30.

**Modelo de ejecución:** un contrato NQ, US$20/punto, US$5,74 ida/vuelta NinjaTrader Free, deslizamiento de dos ticks adversos en entrada y dos en salida = US$20. Fricción total US$25,74 por operación. Los precios son OHLC 1 minuto, no cotizaciones bid/ask; las órdenes son simulaciones de horizonte fijo.

### Auditoría de rollover adicional

Al observar el cambio de contrato se encontró que **ocho de las 545 señales H05** aparecieron precisamente en la primera sesión elegible del contrato nuevo. H05 utiliza el máximo/mínimo del contrato anterior **sin ajuste del diferencial entre vencimientos**, lo que genera riesgo de señal artefactual.

- 8 señales sobre sesiones de rollover: suma neta **+US$3.159,08**.
- 537 señales restantes: suma neta **+US$1.192,62**, expectativa **+US$2,22**.
- Esas ocho señales concentraron el **72,6% del beneficio neto** de H05.
- En H06: 1 evento de rollover, -US$85,74; en H07: 5 eventos, -US$2.513,70.

**Estos cálculos son una auditoría de contaminación, no un nuevo gate favorable ni una estrategia seleccionada retrospectivamente**. Las reglas originales y su resultado están archivados intactos. Si se crea una versión sin referencias entre contratos no ajustados, debe inscribirse como nuevo experimento y consumir presupuesto de búsqueda.

### Recuento de datos y controles

- 25 particiones NQ 2020–2024, 1.221 sesiones RTH completas, 20 sesiones de calentamiento, 1.201 sesiones evaluables por día;
- 69 sesiones RTH incompletas excluidas;
- 7 fechas elegibles sin al menos 800 barras nocturnas para H07;
- H05/H06/H07: 1.519 señales históricas sumadas **entre hipótesis correlacionadas**; no son 1.519 operaciones independientes de una cartera;
- análisis de incertidumbre por bootstrap de semanas de calendario, 10.000 replicaciones, y corrección BH sobre las tres hipótesis;
- control Holm formal por la familia congelada `NQ-LEVEL-VOLUME-H05-H07-V1` y comparaciones exploratorias acumuladas H01–H07; ningún candidato validado;
- solo se abrieron miembros ZIP `development_2020_2024/`, nunca se cargaron las cotizaciones reservadas de 2025/2026.

### Qué sigue

No recomendaría ajustar horas, niveles, buffers o filtros de H05/H06/H07 para rescatar estas pruebas. El siguiente conjunto **distinto** de señales puede basarse en microestructura de ticks y Bid/Ask históricos, comenzando por un mes de 2024 para auditar disponibilidad, sin abrir los holdouts. El problema de rollover y la calidad de datos deben estar resueltos antes de evaluar eventuales configuraciones ejecutables.

**Fuentes:** preregistración `research/nq/NQ_PRICE_LEVEL_VOLUME_FAMILY_H05_H07_PREREG_2026_10_09.md`, programa `research/nq/nq_h05_h07_level_volume_screen.py` y métricas de `results/nq_h05_h07/NQ_H05_H07_DEV_REPORT_2020_2024.json`.