# NQ T169–T188 — Prerregistro monetario de 20 candidatas en cuatro bloques

**Registrado antes de ver cualquier resultado económico del nuevo lote: 13-oct-2026.** Nueva decisión del usuario: investigar *aportación monetaria incremental a T05*, no p/q/IC90 como filtro exploratorio. Esto **no** elimina la necesidad de validación independiente posterior ni habilita fondeo. Datos: exclusivamente 7 meses Last DEV ya almacenados oct2025–abr2026; 140 sesiones fuente, 135 READY esperadas. No abrir mayo–septiembre 2026, series H, ni adquirir datos. Los resultados anteriores de T133–T168 no se recalibran.

## Congelado común ANTES de comparar P&L

- Para cada ID se examina **solo el primer cierre completo** de barra **377 PRINTS** cuyo cierre caiga dentro de la ventana ET congelada. Si no satisface el mecanismo, NO se busca otro cierre más favorable ese día. Contexto de 377/233/4181 construido únicamente con barras completas y grupos de timestamp íntegros. Nunca se usa el último print arbitrario de un grupo empatado ni una barra 5s para señales NUEVAS.
- Una posición NQ, stop fijo **24 ticks**, TP **48 ticks**, timeout **300s**, entrada de mercado *sintética* en Last conforme al simulador B05H/T04 preexistente (latencia1ms, slippage2 ticks/lado en estrés, comisión7,50 USD RT en escenario estrés), hasta 2 operaciones/día, stop de nuevas entradas si P&L cerrado≤−$600. Prioridad por timestamp y, a igual timestamp exacto, gana T05. Sin operaciones simultáneas.
- Se evalúan **20 candidatos individualmente y en 20 routers alternativos T05+Txxx**. No se suman 20 P&L como una cartera. Se exigen paridad exacta de T05 con 115 trades, +US$5.102,50 neto estrés, DD Last US$1.797,50 y +US$3.952,50 con extra US$10RT fijo; si falla la paridad el experimento FALLA.
- Reportar por ID N de señales, N trades aisladas/en router, P&L neto estrés, PF, drawdown Last modelado, operaciones por mes, Q4 vs ene–abr, retención de T05, desplazamientos e **incrementalidad del router contra T05** bajo estrés y +10RT. El cargo adicional es contable sobre misma ruta, no ejecución real. Ningún modelo Last acredita precio negociable, fills ni trailing real.
- Pantalla **monetaria exploratoria**: delta router después de +US$10RT >0, PF router ≥1,25 en ambos escenarios, DD de envolvente Last ≤US$2.000 (referencia ilustrativa, NO firma), ≥104 de las 115 T05 originales conservadas y ≥5 trades de router cada mes. Si alguna falla, etiquetar FALLA sin ajustar regla, SL, TP, período o umbral para rescatar. La evaluación de p/q/IC90 se **aplaza**, no se registra PASS estadístico ni se promociona la D1/D2 formal.

## Bloque A: PREOPEN_0910_0925 (09:10–09:25 ET)

Premarket tardío: buscar entradas que no se solapen con la ventana central de T05.

| ID | Mecanismo fijo | Pregunta económica causal | Estado |
|---|---|---|---|
| T169 | A_PRE_TREND | ¿Persiste el desplazamiento VWAP de tres barras 377 consecutivas? | PRERREGISTRADA, P&L N/D |
| T170 | A_PRE_EXHAUST | ¿Una extensión de 377 de al menos 8 ticks revierte hacia valor? | PRERREGISTRADA, P&L N/D |
| T171 | A_PRE_COMPRESSION | ¿Compresión previa (≤16 ticks) seguida de expansión (≥32 ticks) permite continuación? | PRERREGISTRADA, P&L N/D |
| T172 | A_PRE_BREAK | ¿Un rompimiento aceptado de extremo 377 anterior continúa? | PRERREGISTRADA, P&L N/D |
| T173 | A_PRE_SWEEP | ¿Una barrida sin aceptación del extremo anterior revierte? | PRERREGISTRADA, P&L N/D |

## Bloque B: OPENING_0930_0940 (09:30–09:40 ET)

Primeros diez minutos RTH, antes de la primera ventana 09:40 de T05.

| ID | Mecanismo fijo | Pregunta económica causal | Estado |
|---|---|---|---|
| T174 | B_OPEN_MACRO_MOMENTUM | ¿Diferencia ≥12 ticks contra VWAP 4181 completado anticipa continuidad? | PRERREGISTRADA, P&L N/D |
| T175 | B_OPEN_MACRO_FADE | ¿Diferencia ≥48 ticks contra VWAP 4181 anticipa reversión? | PRERREGISTRADA, P&L N/D |
| T176 | B_OPEN_EXPANSION | ¿Expansión 377 ≥1,5× previa con impulso ≥8 ticks continúa? | PRERREGISTRADA, P&L N/D |
| T177 | B_OPEN_VALUE_CROSS | ¿Dos cambios 377 recientes con impulso actual ≥2 ticks continúan? | PRERREGISTRADA, P&L N/D |
| T178 | B_OPEN_REJECTION | ¿Barrida 377 ≥8 ticks sin aceptación conduce a reversión? | PRERREGISTRADA, P&L N/D |

## Bloque C: MIDMORNING_1020_1040 (10:20–10:40 ET)

Media mañana; modelos solo pueden entrar si el router T05 tiene capacidad libre.

| ID | Mecanismo fijo | Pregunta económica causal | Estado |
|---|---|---|---|
| T179 | C_MID_MICRO_ALIGN | ¿VWAP 233 y 377 consecutivos alineados continúan? | PRERREGISTRADA, P&L N/D |
| T180 | C_MID_MICRO_DIVERGE | ¿Divergencia 233 versus 377 dispara reversión del impulso macro? | PRERREGISTRADA, P&L N/D |
| T181 | C_MID_MACRO_BREAK | ¿VWAP 377 fuera del rango 4181 previo sostiene tendencia? | PRERREGISTRADA, P&L N/D |
| T182 | C_MID_MACRO_SWEEP | ¿Barrida del rango macro 4181 sin aceptación revierte? | PRERREGISTRADA, P&L N/D |
| T183 | C_MID_VOLUME_EXPANSION | ¿Volumen de barra 377 ≥1,75× precedente con desplazamiento sigue? | PRERREGISTRADA, P&L N/D |

## Bloque D: LATE_1110_1135 (11:10–11:35 ET)

Cola posterior a las 11:10 ET: hipótesis de diversificación temporal.

| ID | Mecanismo fijo | Pregunta económica causal | Estado |
|---|---|---|---|
| T184 | D_LATE_DRIFT | ¿Dos barras 377 y micro 233 alineados sostienen la deriva? | PRERREGISTRADA, P&L N/D |
| T185 | D_LATE_MICRO_EXHAUST | ¿Micro 233 contradice fuerte impulso 377 y gira? | PRERREGISTRADA, P&L N/D |
| T186 | D_LATE_MACRO_FADE | ¿Extensión ≥48 ticks respecto a VWAP 4181 revierte? | PRERREGISTRADA, P&L N/D |
| T187 | D_LATE_TIGHT_BREAK | ¿Rango 377 ≤12 ticks con desplazamiento ≥2 ticks desencadena continuación? | PRERREGISTRADA, P&L N/D |
| T188 | D_LATE_LARGE_REVERT | ¿Rango 377 ≥40 ticks con desplazamiento ≥8 ticks revierte? | PRERREGISTRADA, P&L N/D |

## Integridad y diseño

**Diferenciar diversificación temporal de independencia de mecanismos**: algunos gatillos podrían repetirse en ventanas distintas; reportar su solapamiento y las operaciones desplazadas, sin proclamar 20 fuentes de alpha distintas. No usar mejores días/meses de DEV para escoger retrospectivamente combinaciones; si se desea una cartera con más de una alternativa, **otro prerregistro** deberá congelar un selector causal antes de calcular la mezcla. El análisis es exploratorio sobre DEV reexaminado, no ROI futuro esperado.
