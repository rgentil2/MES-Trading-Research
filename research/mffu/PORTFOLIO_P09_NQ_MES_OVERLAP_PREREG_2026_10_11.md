# P09 — Piloto preregistrado de compatibilidad NQ T05-377 con cartera MES (11-oct-2026)

**Objetivo real:** construir una cartera de estrategias diferenciadas, no aprobar el mejor backtest individual. P09 es diagnóstico de **solapamientos y cobertura sincronizada**, NO nueva hipótesis monetaria H79, NO prueba OOS y NO un portafolio combinado listo para fondeo.

## Evidencia anterior a este piloto

- PDC (106 operaciones), POC (108), R072 (149): tres CSV canónicos NinjaTrader 2020–2025 con 2 ticks de deslizamiento y $1,88 RT de coste histórico. El replay anterior de las **363** operaciones, 2020–2025, total +$1.897,80 tras ajustar comisión a $1,90; 91 pausas >7 días; cartera de 1 MES/operación **falló** la evaluación 50K y su objetivo de $3.000.
- NQ T08 en Last-only DEV 2025-10 a 2026-04: T05-377, **115 trades**, +$6.220 base / +$5.102,50 estrés, DD Last envolvente estrés $1.825; no es fill ejecutable ni fondeo validado.
- T05-233+377 es **subfiltro** del padre T02 y se compara como alternativa, no como segundo motor de alpha independiente respecto a T05-377.
- Coincidencia temporal DISPONIBLE para un estudio descriptivo: **2025-10-15 a 2025-12-31** (MES en muestra histórica 2025 ya analizada, NQ Tick DEV público solo en agregados). Revisión previa de los CSV identificó 7 señales PDC, 4 POC y 7 R072 en ese periodo: son **18 candidatos de MES**, no 18 rentables ni 18 entradas aprobadas en una cuenta conjunta.

## Pregunta y endpoint congelados ANTES de mirar resultados P09

**Primaria:** porcentaje de las operaciones T05-377 NQ reproducidas exactamente que se solapan en tiempo con cualquier trade histórico MES PDC/POC/R072 disponible en las mismas sesiones. **Secundarias:** cuántos días tienen trades en ambos mercados, número de pares NQ-MES solapados, máximo de posiciones abiertas a la vez sin router, coincidencia por estrategia, fechas y sesiones excluidas por QC, y fracción de la actividad MES que coincide con actividad NQ por fecha. **No se selecciona** una estrategia según qué pareja tuvo menos choques en esta submuestra pequeña.

## Método

1. El CSV de NinjaTrader es 2020–25 y tiene etiquetas `dd/mm/yyyy hh:mm:ss a. m./p. m.`. Su exportación se **asume ET para este diagnóstico**, coherente con los reportes previos, pero las marcas no están acompañadas de offset; auditarlo frente a NinjaTrader antes de interpretar una coincidencia intraminuto como cierta.
2. Descargar con hash SHA256 únicamente tres meses NQ Last DEV privados **oct, nov, dic 2025**. Rechazar todo mes externo *antes de abrir el fichero*. No tocar mayo–junio ni julio–septiembre 2026 ni 2025/26 del estudio H01–H78. Los csv MES no abren precios 2026.
3. Reconstruir exactamente las señales T02 + filtro 377 y operaciones simuladas T04 **sin optimización**, con `simulate_single_trade`; cotejar diariamente con `simulate_portfolio`: cantidad, neto en ambos escenarios, ambigüedades, pérdidas. Si falla, **FAIL CLOSED**.
4. Una pareja está temporalmente solapada cuando `max(entry_a,entry_b) < min(exit_a,exit_b)`, ambos timestamps ET y ambos contratos admitidos. Un día con señales pero posiciones no coincidentes **no** es solapamiento de posiciones.
5. Para cada día, deduplicar parejas por ID de estrategia/tiempo; cuantificar máximo de posiciones concurrentes. No sumar P&L MES de seis años con NQ de tres meses; no extrapolar estadísticamente este subperiodo.
6. Emitir **solo estadísticas agregadas** al repositorio público; no publicar eventos Last, precios, entradas individuales, posiciones privadas ni trade logs derivados de datos licenciados. Revisar origen / privacidad del CSV MES ya existente como parte de gobernanza.
7. No intentar certificar DD conjunto aquí: MES y NQ necesitan equity intradía sincronizada (mismo reloj) y rellenos verificables. La correlación diaria entre activos distintos no se reemplaza con añadir DD máximos independientes.

## Gate de cartera posterior

- Separar estrategia NQ de mean-reversion (T05-377) de PDC/POC MES y R072 provisional: NO llamarlas independientes hasta medir co-movimiento, solapamiento, periodos y costes en muestra unificada.
- Preparar router con prioridades *anteriores* a outcomes, conteo de contratos agregados ES/MES/NQ/MNQ, riesgo global, veto de exposición contraria del mismo índice, eventos de noticias, inactividad y evaluación MFFU Rapid EOD 50k. No escoger a posteriori una política porque elimina una pérdida histórica.
- La expansión a nuevas estrategias H79–H150 necesita hipótesis conjuntas causales y controles, pre-registro propio, estadística con correcciones, costes y holdouts respectivos; este P09 NO consume hipótesis.
- El Rapid EOD de MFFU declara máximo 3 minis/30 micros en general, pero la política de escalado puede restringir más en sim-funded. Consultar el plan y etapa vigente en la aprobación final. El EOD trailing se actualiza al cierre, pero pérdidas de equity abierta pueden vulnerar el suelo intradía.
- **Estado autorizado:** `STRUCTURAL_OVERLAP_DIAGNOSTIC_ONLY`. **No** generar recomendaciones de tamaño definitivo ni comprar fondeo con este piloto.
