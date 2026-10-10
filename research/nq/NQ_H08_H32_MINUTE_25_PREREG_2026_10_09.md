# NQ-H08–H32 — 25 hipótesis de velas de un minuto, registro previo

**Pre-registrado 2026-10-09, antes de ejecutar sus resultados.** Estudio exploratorio sobre los datos de desarrollo **2020–2024** ya utilizados anteriormente en NQ. La familia completa contiene **25 pruebas primarias**: no se permitirá presentar solo las vencedoras. Estado al registrar: **NO EJECUTADO**.

## Universo, costes y control temporal

- Fuente: ZIP exportado por NinjaTrader, únicamente **25 archivos `NQ` bajo `/development_2020_2024/`**, leídos mediante la función de carga ya auditada en `research/nq/nq_h05_h07_level_volume_screen.py`. Esta función no abre el contenido de 2025 ni 2026. Se prohíbe usar los precios reservados para diagnóstico de ganancias o ajustes.
- Sesiones de **390 velas consecutivas 09:31–16:00 ET**; una sola serie de un contrato trimestral por sesión, rollover mecánico **jueves ocho días calendario antes del tercer viernes** del mes trimestral; sin interpolación. Esperamos 1.221 sesiones según la auditoría anterior. Si no coinciden, abortar. Históricos últimos 20 días con sesiones completas; ATR contextual = mediana del rango RTH de las 14 sesiones completas anteriores, no del día corriente. Comparaciones de cierre diario o gap de un día a otro se desactivan en rollover y cuando han pasado >5 días calendario entre sesiones. En casos de 2/3 días, todos deben ser el mismo contrato.
- Todas las señales usan información disponible al finalizar una vela **09:45, 10:00, 10:15, 10:30 o 10:45 ET** (índices 14,29,44,59,74). Una señal por hipótesis como máximo y por día. Entrada next bar OPEN; salida primaria OPEN +30min (índice señal+31); secundaria OPEN +15min (índice señal+16). **No se usa información posterior al instante de la señal.**
- Tarifa NinjaTrader Free **US$5,74 round trip por 1 NQ**, más 2 ticks adversos de 0,25 puntos por lado × US$20/punto = **US$20**, coste fijo total **US$25,74/operación**. Slippage de estrés opcional +1 tick por lado = US$10 adicionales. Precios minuto y salida por horizonte: **no stop/TP ni simulación tick, no backtest ejecutable**. Datos de comisión de cuenta Free no equivalen a MFFU.
- Estados estadísticos válidos: `PROMISING_EXPLORATORY`, `NOT_SUPPORTED_EXPLORATORY`, `INSUFFICIENT_EVIDENCE`.

## Las 25 hipótesis (reglas fijas)

En todas, el sentido es simétrico long/short. `ATR` es mediana del rango RTH previo de 14 sesiones; `past20` referencia anterior a la fecha evaluada; `dir` es signo del desplazamiento. No cambiar criterios después de observar resultados. Los horarios que siguen corresponden al **cierre de la vela de un minuto en ET**.

| Código | Señal/pronóstico direccional a +30min | Momento |
|---|---|---|
| H08 | Gap apertura-cierre previo >=0,25 ATR y precio a 09:45 retiene >=60% gap: **reversión** del gap | 09:45 |
| H09 | Gap >=0,25 ATR y movimiento 09:31–09:45 >=0,15 ATR a favor del gap: **continuación** | 09:45 |
| H10 | Gap >=0,25 ATR; cierre 09:45 <=0,10 ATR del cierre anterior; a 10:00 se aleja >=0,10 ATR en dirección gap: **continuación** | 10:00 |
| H11 | Overnight válido (>=800 barras), rango overnight >=0,4 ATR, apertura en quintil superior/inferior de rango overnight y drive de 15min >=0,12 ATR en misma dirección: **continuación** | 09:45 |
| H12 | Mismas condiciones de overnight H11, pero apertura extrema seguida de drive contrario >=0,12 ATR: **continuación del drive contrario** | 09:45 |
| H13 | Cierre RTH previo en quintil superior/inferior de su rango y drive primera 15min >=0,12 ATR en igual dirección: **continuación** | 09:45 |
| H14 | Rango RTH previo <=0,75 mediana rangos anteriores 20; drive 15min >=0,2 ATR: **continuación** | 09:45 |
| H15 | Rango previo >=1,25 mediana 20; drive 15min >=0,12 ATR coincide con dirección cuerpo RTH previo: **reversión** | 09:45 |
| H16 | Cierre previo cambió respecto al anterior, primera 15min >=0,12 ATR se opone a ese cambio: **continuación reversiva** del drive | 09:45 |
| H17 | Dos cambios cierre-cierre consecutivos y cuerpo previo en la misma dirección, primera 15min >=0,1 ATR mismo sentido: **reversión** de racha | 09:45 |
| H18 | Cruce causal al mismo lado de VWAP desde alguno de 5 cierres previos, pendiente de VWAP últimos 5 minutos concordante: **continuación** | 10:15 |
| H19 | Distancia a VWAP 10:15 >=1,5×media absoluta movimientos 1min previos 20 y >=0,1 ATR; eficiencia últimos15 cierres >=0,6: **continuación** de desviación | 10:15 |
| H20 | Igual distancia VWAP H19 pero eficiencia <=0,3: **reversión** hacia VWAP | 10:15 |
| H21 | Cierre 10:30 lejos de VWAP >=0,1 ATR y pendiente VWAP 10:15–10:30 en dirección contraria a desviación: **reversión** hacia VWAP | 10:30 |
| H22 | Al menos 3 cruces de lado del VWAP durante las 30 velas previas a 10:30, cambio precio 10:15–10:30 >=0,15 ATR: **continuación** del cambio | 10:30 |
| H23 | Volumen de las 6 velas hasta 10:00 >=1,5× mediana past20 misma ventana y cambio desde cierre 09:54 >=0,2 ATR: **continuación** | 10:00 |
| H24 | Mismo volumen alto H23, pero cambio 09:54–10:00 entre 0,03 y 0,10 ATR: **reversión** | 10:00 |
| H25 | Volumen de las 6 velas hasta 10:15 <=0,75× mediana past20 misma ventana y cambio desde 10:09 >=0,15 ATR: **reversión** | 10:15 |
| H26 | Volumen de las 6 velas hasta 10:15 >=1,5× mediana past20, cierre en quintil superior/inferior del rango de esas velas, y cambio >=0,1 ATR en su dirección: **continuación** | 10:15 |
| H27 | Volumen de las 15 velas hasta 10:30 >=1,5× mediana past20 y cambio 10:15–10:30 >=0,15 ATR opuesto a desviación vs VWAP: **continuación** del cambio | 10:30 |
| H28 | Tres cierres 1m consecutivos hasta 10:00 en la misma dirección y avance acumulado >=0,1 ATR: **continuación** | 10:00 |
| H29 | Tres cierres 1m consecutivos hasta 10:00 en misma dirección pero amplitud sucesiva decreciente: **reversión** | 10:00 |
| H30 | Rango 09:46–10:00 <=cuartil 25% de ese rango en past20; cierre a 10:15 rompe máximo/mínimo del tramo anterior al menos un tick: **continuación** | 10:15 |
| H31 | Rango 10:16–10:30 >=1,5× mediana mismo tramo past20 y avance 10:15–10:30 >=0,15 ATR: **continuación** | 10:30 |
| H32 | Cierre 10:45 supera máximo o mínimo de rango 10:16–10:30 en >=un tick: **continuación** | 10:45 |

Las fórmulas exactas de tolerancias, exclusiones y asimetrías están congeladas en `research/nq/nq_h08_h32_minute_2020_2024.py`, incluida la forma de calcular volumen, rangos y signos. La mera existencia de 25 señales no implica 25 fuentes independientes de alfa: pueden ocurrir el mismo día y estar correlacionadas.

## Estadística sin selección posterior

Cada una de las **25** entra en el mismo denominador de corrección BH de valor p, incluso si no dispara eventos (p=1). Contraste principal unidireccional a media **neta >0**; aleatorización *sign flip* de bloques semanales (10.000 replicaciones), bootstrap de semanas con 10.000 replicaciones y semilla 20261009. Se informan **IC 90% bilateral e IC 95%**, corregido BH para las 25 y corrección Holm de familia congelada en el registro global. El bootstrap no garantiza validez si hay correlación de largo plazo o hipótesis ya exploradas en esos mismos años. Se muestra PF, win rate, expectativa, recuento, cinco años por separado, señal +15min, slippage de estrés y huecos temporales.

**Gate 1 exploratorio prospectivo sin alterar criterios:** N>150, expectativa neta positiva, límite inferior IC90>0, q BH<=0,10, efecto positivo en >=3/5 años, sin rescates post hoc. Coste estrés se reporta por separado, pero no se utiliza para cambiar el Gate 1 pactado. Conclusiones favorables en datos ya reutilizados son **solo indicios** para una validación independiente posterior, no confirmación.

No abrir 2025 ni 2026 al concluir esta ronda. No reoptimizar las perdedoras a posteriori. No adoptar stops/TP de las señales ganadoras antes de preregistrar nueva fase.