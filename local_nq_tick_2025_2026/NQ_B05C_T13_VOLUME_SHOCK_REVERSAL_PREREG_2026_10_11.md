# NQ-B05C / T13 — PRERREGISTRO: shock de volumen Last + reversión del desplazamiento local

**2026-10-11. Congelado ANTES de observar cualquier resultado T13.** Familia T13 distinta de T02/T05 (reversión por opening-range), T09 (trampa rápida de ruptura OR), T11 (VWAP aceptación) y T12 (continuación de ruptura tras compresión). Su mecanismo candidato es **shock local de volumen realmente negociado (`qty`) con desplazamiento que se deshace**, sin inferir volumen agresor, absorción pasiva ni delta de Bid/Ask. Es una hipótesis adaptativa, no estadísticamente independiente de la búsqueda anterior.

## Fuente y ventanas

- Únicamente NQ Tick **Last** DEV privado y SHA256 verificado por mes: sesiones desde 2025-10-15 hasta 2026-04-30. Universo esperado: **7 meses, 140 días fuente y 135 elegibles**. No abrir outcomes mayo–junio 2026, ni pseudo-forward julio–septiembre, ni holdouts H de 2025/2026.
- `price` viene en ticks de precio NQ de $0,25 puntos = $5/tick para 1 NQ; `qty` son contratos de transacción observados en cada print. No hay información sobre si la transacción agredió Bid o Ask, por lo que **nunca llamarla order-flow delta ni absorción verificada**.
- Barras 5s OHLC + **suma de qty**, cerradas causalmente y ancladas a las 08:00 ET. Ventana decisoria **10:00:00–11:10:00 ET**, último 5s cierre estrictamente anterior a 11:10, para no interferir con la apertura inicial de T05 y preservar capacidad. Usar `i∈[1440,2280)`.
- Requiere 31 barras completas `i-30 .. i`; cualquier barra faltante cancela señal. Índices anteriores a `i` no pueden actualizarse con prints futuros.
- **Contexto previo 24 barras `[i-30, i-6)`**: `Qprev=sum(qty)`, debe ser >= 24; no condiciona dirección ni OR.
- **Shock 4 barras `[i-6,i-2)` = i-6,i-5,i-4,i-3**: displacement `D=close(i-3)-close(i-7)` de al menos **12 price ticks** en valor absoluto; dirección de shock `sign(D)`. Volumen del shock `Qshock=sum(qty)`, exigiendo **promedio por barra 2x contexto anterior**: `24*Qshock >= 8*Qprev`. Este shock puede ser alto volumen negociado, no identifica lado/agresor.
- **Confirmación al cerrar i:** choque pierde al menos la mitad de su desplazamiento en **tres barras `i-2, i-1, i`**: `shock_sign*(close(i-3)-close(i)) >= max(6, ceil(abs(D)/2))` price ticks; último cuerpo 5s confirma dirección opuesta (`shock_sign*(close(i)-open(i))<0`). Señal de entrada contraria al shock `side=-shock_sign`. Si simultaneidad/conflictos, no se emite señal.
- **Protección de capacidad de la cuenta:** se emite SOLO LA PRIMERA señal causal de T13 del día (máximo 1 señal/día y, por ende, a lo sumo 1 operación T13/día), seleccionada por cronología, jamás por P&L conocido. El límite global histórico continúa en **2 fills diarios**, con bloqueo diario de nuevas entradas si neto de operaciones ya cerradas <=-$600. Una T13 temprana puede desplazar aun así una T05 posterior; publicar siempre cuántas T05 se conservan.
- No se usa filtro de calendario/meses/régimen futuro, OR ni VWAP como disparador. El OR de 09:30–09:35 solo determina el **mismo stop T04** (25% rango, 16–48 price ticks) y QC de días, sin alterar la señal local.

## Hipótesis y controles congelados

**T13_FULL:** exactamente shock qty >=2x y reversión >=50% + >=6 price ticks, cuerpo contra shock.

**A13_NO_VOLUME:** elimina exclusivamente el umbral 2x de `Qshock`; exige `Qprev>=24`, desplazamiento y confirmación idénticos.

**A13_WEAK_RETRACE:** conserva shock qty>=2x, displacement>=12 y el cuerpo opuesto, pero relaja únicamente cierre de reversión a **>=2 price ticks** en lugar de >=max(6,ceil(D/2)). No se promocionan ablations aunque alguna gane; si controles resultan idénticos por lógica, declarar redundancia. Es una única familia nueva **T13**, no tres estrategias.

## Simulador, ruta de riesgo y costes

- Reutilizar código y política T04, sin cambiar condiciones de fills, stop, TP, timeout ni riesgos: 1 NQ, máximo 2 operaciones/día total, una posición a la vez, stops 16–48 ticks price según OR, TP 2R, 300s, cierre <=11:30. Ejecución Last sintética, 1ms posterior a la señal, no estimar fills reales con BBO desordenado.
- Comparadores **T05_377 standalone**, T13_FULL standalone, A13_NO_VOLUME, A13_WEAK_RETRACE y **router compartido T05_PLUS_T13_ROUTER**, señales ordenadas por barra y empate con prioridad fija T05. **T13 solo primera señal/día**; se ejecutan como máximo 1 T13 y 2 trades diarios totales. Una cuenta con equity única. Comparar efecto incremental router vs T05; no sumar P&L de backtests separados.
- Escenario base T04 fee RT $5 y 1 tick adverso/lado, estrés fee $7,50 + 2 ticks adversos/lado; estrés +$10/RT **solo imputación contable sobre mismos trades**, no recalcular SL/TP, daily stop ni asignación de capacidad. La misma contabilidad base/estrés se aplica a todos los modelos.
- Controles invariantes: T05 reproduce **115 trades +$6.220 base, +$5.102,50 estrés**, DD Last cronológico base $1.725 y estrés $1.797,50 (bajo +$10 extra $1.887,50), 140 fuente/135 elegibles. Tests sintéticos fronteras, no lookahead, volumen qty y no conteo de prints, primera señal/día, orden y holdout firewall. **Cualquier paridad incumplida impide resultados científicos.**

## Gates de aceptación exploratory (todos exigidos, ninguna promoción directa a fondeo)

1. Router **incremento neto positivo** frente a T05 bajo **estrés +$10/RT** sobre ruta congelada.
2. **PF router estrés original >=1,25 y PF estrés+$10 >=1,25**.
3. DD Last *adverso* conjunto estrés original **< $2.000 de referencia histórica NO VERIFICADA**. No es regla actual de una firma.
4. **P&L estrés atribuible a T13 dentro del router estrictamente positivo**, no solo eliminación de trades perdedores T05 (caso T11).
5. **Conservación T05 ≥90% de 115 trades = al menos 104 trades T05 ejecutados en el router** (meta de no consumir capacidad; esta cifra se fija AHORA antes de outcomes), sin usar selección ex-post.
6. Conjunto al menos **5 operaciones por mes**; T13 al menos una ejecución en 5/7 meses como objetivo **descriptivo optativo**, no rescate si faltan.

En cualquier resultado, registrar **todos los 7 meses incluyendo pérdidas**, DD, PF, frecuencia, ablations y desplazamiento de T05. Si cualquier gate obligatorio falla, **T13 NO PROMOVER** y B06 permanece bloqueado; evitar volver a ajustar thresholds T13 en la misma muestra como si fueran nuevos OOS. Si pasa en DEV, NO significa robustez ni autoriza compra fondeo: aún requiere walk-forward independiente, QC/fills validables, comparación anual neta >max(15%,VOO-TR,QQQM-TR), presupuesto de multiplicidad y reglas reales.

## Gobierno de búsqueda

La muestra DEV ya se usó para familias T05, T09, T11, T12. T13 representa **otra familia adaptativa**, documentar cada resultado y no inventar alfa ajustado formal. No usar signed order flow, Bid/Ask secuenciado, DOM o actividad buy/sell porque Last no contiene esa información. No publicar operaciones individuales, precios, timestamps, muestras del proveedor ni ticks licenciados; en Actions solo agregados mensuales y reportes.
