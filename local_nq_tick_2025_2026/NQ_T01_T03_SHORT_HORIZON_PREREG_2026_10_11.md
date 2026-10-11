# NQ ticks: primera familia de oportunidades intradía de corto plazo — prerregistro, 2026-10-11

**Estado:** `LOCKED_FOR_DEVELOPMENT_DIAGNOSTIC`, aún sin resultados de esta familia. Pertenece exclusivamente al **nuevo programa ticks NQ Oct2025-Jun2026**. No sustituye H01-H78 ni renumera sus pruebas. El techo de 150 hipótesis no es una cuota de señales.

## Qué significa scalping aquí

**Hipótesis de movimientos cortos de segundos a minutos**, no HFT ni microsecond/latency arbitrage. El timestamp se usa para evitar información futura, no para encontrar ventaja por diferencia de milisegundos. Ventana de señal **09:40–11:10 ET** (apertura de 09:30–09:35 cerrada y 5 minutos de calentamiento); diagnósticos de desplazamiento a **+1, +3, +5, +10 y +20 minutos**, último horizonte completo no más tarde de 11:30 ET. Para la operación definitiva se fijarán límites SL/TP y duraciones acotadas después del gate de señales, sin seleccionar ganadores retrospectivamente.

**Objetivo económico futuro:** oportunidades mensuales suficientes **después** de filtros y costes; expectativa neta positiva, control de DD intradía de cuenta fondeada USD 50K; Gate económico principal > max(15% anual, CAGR VOO TR, CAGR QQQM TR) en ventanas comparables; no confundir capital nominal de 50K con dinero propio ni suponer rentabilidades mensuales garantizadas. Una señal con mejor dirección no implica rentabilidad.

## Fuente y partición inalterable

Datos: `NQ-Ticks-Dev-2026` privado, `Last` NQ al tick; solo se descargan días explícitos y SHA256 del archivo mensual se valida antes de su uso. Barritas agregadas en memoria de **5 segundos**, cada una calculada únicamente con ticks históricos de **esa barra ya finalizada** (open, high, low, close, número de prints y volumen total). Ningún Bid/Ask simultáneo usado para señales. No se utiliza el ZIP original de minuto multi-year para buscar mejores condiciones.

- **Desarrollo:** 2025-10-15 a 2026-04-30. Pilotear días autorizados en Oct2025, Nov2025, Feb2026 y Abr2026, sin optimización.
- **Validación interna:** mayo–junio 2026 **no accesible** para esta ejecución ni para seleccionar parámetros; se abrirá luego de preregistro de estrategia completa, con etiqueta de validación interna (algunos datos se han visto para QC).
- **Pseudo-forward sellado:** julio–septiembre 2026, prohibido abrir hasta congelar señales, costes, stop/TP, sizing y orden de resolución. Octubre 2026 archivado, no para elegir reglas.
- Cambios de horario ET/DST resueltos vía `America/New_York`; no rellenar minutos faltantes ni encadenar contratos de distintos vencimientos como si fueran un único libro.

## Regla de señal congelada antes de observar resultados

La apertura de referencia es el **máximo/minimo de 09:30–09:35 ET** usando exclusivamente Last. Apertura menor que 4 ticks o hueco en cualquier bar 5s de esa apertura: día fuera del diagnóstico. Para decidir cada 5s se requiere una ventana completa, sin huecos, de los últimos 5 minutos de barras 5s. Se compara el número de prints de los últimos 30 segundos contra los 30 segundos anteriores, con base >=20 prints; **no es delta comprador-vendedor ni volumen agresor**, y los umbrales se mantienen fijos.

- **T01 conjunta de continuación:** cierre 5s cruza de abajo hacia arriba el máximo de la apertura **+4 ticks** (o simétricamente el mínimo −4 ticks); desplazamiento neto desde hace 60 segundos >=8 ticks en dirección de ruptura y actividad últimas 30s >= **1,35×** los 30s anteriores.
- **T02 conjunta de reversión:** precio toca una excursión fuera de la apertura >=4 ticks en algún bar de los 90s anteriores, luego cierre 5s retorna al menos 2 ticks dentro del límite y el precio previo estaba en ese límite; actividad reciente <= **0,85×** la ventana previa de 30s. Dirección contraria a la excursión.
- **T03 router conjunto:** usa el rango observado en los últimos 5 min antes/al cierre de la señal y el rango de apertura; si rango reciente >=0,5× rango apertura toma solo T01, si es menor solo T02; de lo contrario no-trade. No permite doble exposición por coincidencias.
- **Controles de ablación C01/C02:** misma condición de ruptura/fracaso que T01/T02 **sin** el filtro de actividad. Comparar frecuencia y eficacia direccional de las señales resultantes, reportar todas las variantes sin eliminar fallos.

Para cada familia solo se registra una oportunidad por cada 5 minutos; no constituye una restricción operativa definitiva y **NO** calcula riesgo de posiciones abiertas. No se ajustarán estas definiciones usando el resultado del piloto. Cuando haya señal se compara **primer precio Last del siguiente bloque 5s** con cierre del bloque a +1/+3/+5/+10/+20 min, siempre *posterior* al instante de señal; reportar desplazamiento direccional en ticks, fracción positiva, mediana y N. **Es un estudio de movimiento de precio bruto, sin comisiones, spread, slippage, órdenes ni P&L**. Si hay un hueco en la entrada o en el horizonte, ese objetivo queda faltante, sin interpolación.

**Regla primaria del diagnóstico:** cobertura y frecuencia mensual de **T03** y dirección mediana a +5min, comparada descriptivamente con T01/T02 y sus controles. Resultados de +1,+3,+10,+20min son secundarios; **no** elegir el horizonte ganador para declarar prueba confirmatoria. Todos los endpoints quedan sujetos a multiplicidad cuando se formalice prueba estadística, incluida selección de umbrales.

## Gate de esta ronda y falsación

1. Debe existir información antes de la señal y oportunidades no concentradas en 1–2 días. Mostrar tasa por **día**, mediana y rango por **mes** y distribución 09:40–11:10.
2. Un resultado bruto +5min favorable aislado o dos sesiones ganadoras NO alcanza para operar. Comprobar aporte incremental frente a C01/C02 y T01/T02, disminución de frecuencia, correlación/solapamiento y problemas de régimen.
3. Si T03 produce frecuencia ínfima, peor mediana/estabilidad que controles o resultado dependiente de unos pocos días, reportar como `INSUFFICIENT_EVIDENCE` o `NOT_SUPPORTED_EXPLORATORY`; conservar componentes para nueva familia **prerregistrada**, sin modificar esta retrospectivamente.
4. Solo después de verificar cobertura mensual y señal: pasar a backtest de órdenes con ejecución Last **después** de señal, SL/TP, timeout <=20min inicial, costes NQ/prop account verificados y sensibilidad 1,5×; evaluar frecuencia, PF neto, máximo DD flotante, pagos y retorno benchmark >max(15%,VOO,QQQM).
5. No inferir ventaja por 31% de operaciones fuera del Bid/Ask previo: la auditoría mostró ambigüedad de secuenciación. La resolución contra fuente 1m independiente sigue como **QA paralelo**, no impide medir viabilidad de señales Last con precaución.

## Control de selección

**Cinco fórmulas registradas:** tres conjuntos (T01, T02, T03), dos ablations (C01, C02); **cinco horizontes por fórmula**, 25 vistas a reportar íntegramente. El umbral de 150 *no obliga* a ejecutar 150 combinaciones. La presente ronda es EXPLORATORIA, no un nuevo test OOS, y no se adjudica alfa estadística retrospectiva a observaciones de piloto.
