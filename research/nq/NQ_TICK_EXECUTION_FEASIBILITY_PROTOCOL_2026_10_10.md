# NQ Tick Last/Bid/Ask — programa de granularidad y ejecución anticipada

**Fecha:** 2026-10-10. **Estado:** PROTOCOLO DE FACTIBILIDAD DE DATOS Y DISEÑO; NO es el prerregistro ni el resultado de H79. **Alcance:** 2020–2024 como desarrollo exploratorio, sin abrir 2025/2026. Reorienta el trabajo futuro hacia **NQ primero**, preservando MNQ como alternativa de riesgo, las familias previamente congeladas y la meta económica >max(15 %, VOO, QQQM).

## Motivación deductiva y límite actual

- H09 (continuación de gap de apertura) y H56 (reversión de impulso premarket) mostraron resultados exploratorios positivos; la cartera H69 las coordinó. No están confirmadas ni son suficientes para fondeo. El reescalado de H69 a 1 NQ no supera 15 % anual equivalente y supera ampliamente el colchón de pérdida supuesto de USD 2.000.
- Los últimos NQ se estudiaron con datos **Minute Last OHLCV**. Una vela de 1 minuto no identifica el orden cronológico exacto de máximos/mínimos ni la posición real en la cola de órdenes; no puede confirmar un stop ejecutado ni cuándo se produjo un giro intraminuto.
- **Hipótesis de investigación**: tick puede (i) reducir el retraso de una entrada causal, (ii) distinguir confirmación vs ruptura falsa, (iii) colocar un stop estructural más cercano, (iv) simular la trayectoria intratrade con mayor fidelidad. **No se asume** que stops más estrechos sean mejores: pueden elevar stopouts y hacer que comisión, spread y slippage dominen.
- Fuente actual: no hay archivos **NQ Tick Last/Bid/Ask disponibles** en el árbol GitHub auditado. Hay un antecedente **ES MAR24 Tick Last** en LFS y experimentos ES/MES de microestructura; NO son cotizaciones NQ ni verifican su ejecución. La carga NQ de 2020–24 usada para H01–H78 es de minuto.

## Datos solicitados y fuente

**Primer piloto de factibilidad, elegido por calendario y no por rentabilidad:**
- Instrumento/contrato: **NQ 03-24**, sin unir contratos ni back-adjustment; sesiones ET **2024-02-05 a 2024-02-16**.
- Tick trade **Last**: timestamp original UTC subsegundo (idealmente milisegundos o mejor), precio, cantidad/volumen. Ventana mínima por día **08:30–11:30 ET**, con margen si un evento requiere precalentamiento. La estructura intradía previa se calcula de los minutos históricos ya existentes.
- Mejor si se incluyen **Bid y Ask históricos** auténticos con su propio timestamp, precio y eventos. Necesario para estimar spread, dirección agresora y ejecuciones plausibles; no inventar las cotizaciones si faltan.
- Para validar transferencia NQ vs MNQ, una muestra adicional **MNQ 03-24 Tick Last** sincronizada es deseable, pero el proyecto inicia sobre NQ.
- Al descargar desde NinjaTrader, comprobar qué historia ofrece realmente el proveedor; exportar en Control Center > Tools > Historical Data > Load > Export con Interval **Tick**, tipos **Last**, **Bid**, **Ask** cuando estén disponibles. Exportación NinjaTrader en **UTC**. Ver instrucciones oficiales y limitaciones del proveedor.
- **Importante:** conservar los tick files y el ledger individual de operaciones **locales/privados**; repositorio GitHub actualmente **público**. No subir ticks licenciados ni revelar datos individuales a menos que el titular autorice su redistribución. Subir solo código, sumarios agregados y QC.

### Separar calidad de datos de validez de estrategias

**Etapa 0: disponibilidad y QC; no calcular ROI.**
- Definir proveedor, símbolo exacto por vencimiento, timezone UTC/ET con horario de verano, cobertura de sesiones y horarios, resolución, columnas y permisos de redistribución.
- Monotonicidad de timestamps por serie/contrato, duplicados genuinos vs eventos repetidos legítimos, ausencia de saltos de tiempo anormales, precios válidos y múltiplos de tick de **0.25 puntos**; volúmenes Last positivos.
- Bid <= Ask, spread en ticks, quotes cruzadas/faltantes, edad de último Bid/Ask al momento del trade, proporción de Last sin cotización reciente; evitar quote-forward-fill sin límites o across-session/contract.
- Reconstruir velas 1m desde Tick Last y confrontar OHLC/volumen con el minuto existente, tolerando explícitamente convenciones de fin de barra, fuente y posible agregado de proveedor. Si no concuerdan, diagnosticar antes de investigar alpha.
- **Gate de adquisición:** si faltan timestamps o Last de calidad, detener el estudio de entradas tempranas. Si Bid/Ask no están disponibles, limitar piloto a **trayectoria/ejecución Last-only**, SIN inferir delta agresor o spreads observados. Si los diez días son suficientes para QC, pasar a una cobertura mayor 2020–24 planeada; dos semanas NO demuestran una ventaja monetaria.

**Etapa 1A: fidelidad de ejecución, sin anticipación.**
- Mantener EXACTAMENTE el signal close 09:45 ET y demás reglas de H09/H56/H69; reemplazar únicamente su ejecución intraminuto por ticks causales, usando stops/TP congelados. Comparar contra ejecución Minute Last (mismo día, contrato, señales, coste), orden verdadero de toques SL/TP y máximo adverse/favorable excursion desde la entrada.
- Resultado: sesgo de ejecución de minuto, distribución de stopouts, slippage y spread, drawdown intratrade en USD de **1 NQ**. Esto es un **diagnóstico de backtest existente**, no una variante seleccionada ni señal confirmada.

**Etapa 1B: señal y entrada anticipadas = hipótesis NUEVA, preregistro obligatorio.**
- Antes de las 09:45 **no se conoce el cuerpo completo de los primeros 15 minutos**. No usar su cierre futuro para decidir a las 09:35. Necesario definir un `partial_opening_drive` formado exclusivamente de ticks pasados, una confirmación observable por Last y, donde exista, Bid/Ask; entrada posterior al evento y máximo una posición.
- Comparar alternativas exactas de `trigger` (temprano/conservador), pero declarar todas las variantes y sus ventanas en una **familia futura** antes de inspeccionar resultados, incluyendo controles que *no* entren anticipadamente.
- Stops anclados a microestructura observada hasta ese instante; no usar el low/high posterior ni reoptimizar la distancia para maximizar P&L. Testear si menor riesgo inicial compensa más stops barridos, coste/spread, cambios de frecuencia y cola de pérdidas.
- Un filtro flow/delta solo se investiga cuando Last trade + BBO contemporáneos están documentados, quote-age limitado y fiabilidad de agresor reportada; **Tick Last por sí solo no permite delta comprador-vendedor fiel**. No confundir L1 con L2/DOM.

**Etapa 2: riesgos y cartera combinada de NQ.**
- Contra mismos trades/minutos: H69 base con 1 NQ y política de riesgo idéntica; versión tick con trigger/stop, versión tick sin nuevo filtro, y ablations quitando confirmación o ruta. Mostrar N trades, tradeoff de frecuencia, pérdida por stop, PF, esperanza y 90 % IC por semanas, BH y presupuesto Holm de toda la familia preregistrada.
- Congelar costes de NQ del broker/cuenta, por lado, spread y slippage; estrés 1.5×, orden/latencia, caso peor de stop-gaps, límite de operación al 11:30 ET, error de timestamps y supuestos de limit/market fill.
- **Riesgo de un contrato:** NQ = USD 20/punto = **USD 5/tick**. Un stop de 4 puntos equivale a USD 80 brutos, un stop de 8 puntos USD 160 brutos, más spread/slippage/comisiones; estos son **ejemplos, NO stops aprobados**. Elegir el stop según estructura y probabilidad de ejecución, no según el ROI objetivo.
- Medir intratrade *mark-to-market* y drawdown flotante; si la pérdida asociada a 1 NQ no cabe en la regla real de fondeo, descartar 1 NQ para ese producto y mantener MNQ/fondeo distinto.
- Meta económica posterior: CAGR neto de cartera > `max(15 %, VOO total return, QQQM total return)` con ventanas idénticas y riesgo ajustado, separando rentabilidad nominal 50k de retorno real sobre desembolsos/payouts.
- **2020–24 fue ampliamente investigado:** las variantes desarrolladas aquí son EXPLORATORIAS, aunque introduzcan nueva granularidad. Los años 2025 y 2026 siguen sellados y requieren autorización distinta luego de congelar la estrategia completa.

## Sobre NinjaTrader: Tick Replay vs fills

**Tick Replay no valida fills.** Documentación de NinjaTrader: Tick Replay reconstruye cálculos tick-a-tick, pero no equivale a backtest con ejecución real; para mejorar la simulación de órdenes se utiliza una serie tick separada o configuración de alta resolución cuando es compatible. En estrategias multiinstrumento, revisar limitaciones de High Fill Resolution y Tick Replay, y usar orden dirigida a serie tick en NinjaScript. Las cotizaciones Bid/Ask históricas pueden no estar presentes o ser solo sustitutos de proveedor.

Fuentes oficiales:
- Exportación de ticks, UTC y tipos Last/Bid/Ask: https://ninjatrader.com/es/support/helpguides/nt8/exporting.htm
- Descarga y cobertura según proveedor: https://ninjatrader.com/es/support/helpguides/nt8/download.htm
- Tick Replay: https://ninjatrader.com/support/helpguides/nt8/tick_replay.htm
- Realismo de histórico/High Fill: https://ninjatrader.com/support/helpGuides/nt8/understanding_historical_fill_.htm
- Formato subsegundo de tick y Tick Replay importado: https://ninjatrader.com/support/helpguides/nt8/importing.htm
- Código antecedente: `research/mes_v2_tick_2024.py`; caso específico ES: `research/MES_V2_LAYER2_TICK_2024_PREREG.md`.

## Próxima decisión — por resolver

1. **Comprobar acceso real a NQ 03-24 Tick Last (y Bid/Ask)** en la conexión actual NinjaTrader. Si no está disponible, cotizar proveedor alternativo *antes* de comprar cinco años de ticks.
2. Recibir una muestra de 1–2 sesiones de 2024 para QC básico, luego cubrir 2024-02-05–16 para evaluar si la fuente y el formato permiten trabajo causal; si el período no está disponible, documentar sustitución elegida por disponibilidad ex ante.
3. Solo después redactar y congelar la nueva familia de **estrategias conjuntas H79+** y ejecutar outcome. Un QC o diagnóstico de ejecución no es una H79 nueva ni consume un presupuesto de hipótesis por sí mismo.

## Actualización de alcance — estudio separado 2026 con pseudo-forward histórico offline

**2026-10-10: autorización posterior del usuario**, que supera únicamente para la **nueva línea scalping/tick 2026** la regla antigua de no utilizar 2026. Se **permiten** enero–abril 2026 (desarrollo) y mayo–junio 2026 (validación interna); **julio–septiembre 2026 permanece sellado como pseudo-forward histórico** y solo se abre una vez después de bloquear estrategias, costes, sizing, códigos y auditoría. Octubre–diciembre queda fuera del experimento. La investigación H01–H78 conserva sus propios holdouts 2025 y 2026 sellados.

El estudio pseudo-forward es **offline histórico, no vivo ni paper-trading prospectivo**. Puede reducirse a agosto–septiembre o septiembre **solo por falta de cobertura objetiva documentada antes de examinar retornos**, no por rendimientos favorables. Tick NinjaTrader de 2026 necesita QC de disponibilidad antes de su uso.

**Norma vigente y detallada:** `research/nq/NQ_TICK_SCALPING_2026_OFFLINE_PSEUDO_FORWARD_POLICY_2026_10_10.md`. El protocolo piloto de febrero 2024 anterior queda como antecedente; para la nueva línea de trabajo, primero verificar una muestra de enero–junio 2026. Este cambio no modifica familias congeladas ni confirma rentabilidad.
