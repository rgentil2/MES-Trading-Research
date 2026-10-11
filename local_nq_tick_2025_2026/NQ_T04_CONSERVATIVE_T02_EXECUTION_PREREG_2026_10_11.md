# T04 — Prerregistro prospectivo de ejecución exploratoria para NQ T02, 2026-10-11

**Registrado después** de observar los resultados direccionales T01–T03 del desarrollo (140 fechas, T02 +10,634 ticks brutos promedio a +5m en 298 oportunidades). Por esa selección basada en resultados vistos, este T04 es **EXPLORATORIO**, NO una confirmación estadística independiente. No reabrir antiguos holdouts H01–H78. No usar mayo–junio 2026 para elegir parámetros, julio–septiembre 2026 sigue sellado.

## Pregunta

¿La regla T02 (ruptura fallida del rango 09:30–09:35 ET + desaceleración del número de operaciones Last en ventanas previas de 30s) sobrevive, como estrategia de duración **segundos/minutos**, al riesgo acotado de 1 NQ, stop, TP, una única posición, comisión de prueba y fricciones conservadoras? **NO** investigar ventaja microsegundo/latencia.

## Política de trading F-I-J-A, ANTES de ejecutar outcomes

- Fuente Tick Last NQ exclusiva Oct 15 2025–Abr 30 2026, datos Dev privados con checksum. Señales 09:40–11:10 ET según script `nq_tick_short_horizon.py` **sin modificar**. Ejecutar misma política sobre **T02** y ablación **C02 sin filtro de desaceleración**; no sumar posiciones entre ambos: son carteras simuladas comparadas por separado.
- Entrada: **primer tick de una marca temporal posterior al cierre de la barra de 5s de la señal**; dentro del primer timestamp elegible usar el peor precio del grupo, sin asumir orden interno. Slippage adverso inicial: **1 tick por lado** (entrada y salida) en base, 2 ticks por lado en estrés. Retraso técnico de resguardo 1 ms únicamente para evitar ejecución simultánea con la señal, NO objeto de optimización ni promesa de fills.
- Riesgo: 1 contrato NQ; 0 posiciones superpuestas; máximo **2 operaciones al día**, deshabilitar nuevas entradas si P&L realizado intradía <= **−USD 600**. NQ = $5/tick. Stop fijo por operación **max(16, min(48, ceil(0,25 × rango apertura en ticks)))**; target **2× stop**. Tope inicial estimado del stop de 48 ticks equivale a $240 por NQ **antes** de slippage, comisiones y saltos de precio; no demuestra cumplimiento automático de trailing DD.
- Salida: en primer tick que toque SL/TP, peor caso stop-first ante eventos con mismo timestamp; si no, cerrar en primer tick al cumplir **300 segundos** desde entrada, o a las 11:30 ET, lo anterior primero. Saltos adversos se liquidan al precio Last peor observado, no a un stop teórico favorable. Eventos de entrada ambiguos = clasificar **UNRESOLVED**, no inventar beneficio.
- Costes analíticos, **NO TARIFA COMPROBADA DEL BROKER/FONDO**: baseline **USD 5 RT comisiones +1 tick adverso por lado**; estrés **USD 7,50 RT +2 ticks adversos por lado**. Son escenarios de simulación previamente definidos, no datos del contrato del usuario. Si comisiones efectivas son distintas, actualizar como nueva política preregistrada sin borrar este resultado.
- Máximo 1 oportunidad cada 5m heredada del detector T02/C02; 2 entradas/día con no superposición, sin operar si falta contexto de apertura ni rellenar gaps. Cuenta nominal referencial $50.000 solo para riesgo/drawdown analítico; nunca se presentará como inversión personal ni ROI personal.

## Métricas y adversarial checks

Informar los siete meses íntegros (incluidos pérdidas y cero trades), n días, n oportunidades, n trades y descartes por capacidad y solapamiento, win rate, media neta USD, suma P&L neto, PF neto, porcentaje meses positivos, máximo DD cerrado, peor trade, peor resultado diario, rachas y sensibilidad al estrés. Auditar el peor MAE intratrade observado en Last (marca indicativa conservadora, no P&L a precio Bid/Ask) para no confundir DD cerrado con trailing flotante de fondeo.

**Comparación primaria:** T02 vs C02 en net expectancy USD por trade bajo *mismo* conjunto de fechas, cuenta/riesgo/costes, con pérdida de frecuencia reportada. Este análisis no mide prueba inferencial confirmatoria dada la selección previa T02 en desarrollo.

**Criterios de falsación:** expectativa neta <=0, PF neto <=1, estrés inviable, meses muy inestables, concentración extrema, DD de fondeo incompatible, señales ejecutables insuficientes, o costo de retorno no remunerado por riesgo. Ni un resultado positivo parcial ni superar nominalmente 15 % anual acreditaría operativa real sin validación independiente y reglas concretas del programa de fondeo.

## Siguiente gate

Tras ejecución y auditoría revisar causalidad/equity y decidir:
- T04 inviable: conservar la observación de desaceleración como componente explicativo, preparar nueva familia con causas falsables sin reescribir los resultados.
- T04 exploratoriamente prometedor: congelar un candidato final, contrastar periodos de validación interna May–Jun **una única vez**; julio–septiembre pseudo-forward offline separado una vez completamente congelada la estrategia. Benchmark VOO/QQQM requiere fuente de total return y duración comparable; NO calcular CAGR irreal para siete meses.

**No cambiar parámetros retrospectivamente ni llamar a T04 confirmación fuera de muestra.**
