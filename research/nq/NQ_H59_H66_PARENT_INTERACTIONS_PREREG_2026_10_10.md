# NQ H59–H66: complementariedad y conflictos entre hipótesis heredadas

**Registro antes de ejecutar estas ocho pruebas condicionadas.** Se sabía previamente que H55/H56 coincidían 67 días, H09/H56 11 y H09/H55 tres. Los rendimientos agregados de los padres en 2020–2024 y parte de sus coincidencias también se observaron antes de este registro; **esta familia no constituye evidencia independiente**. El objetivo es documentar de forma completa las particiones, no seleccionar ganadoras.

## Fuente, temporalidad y controles

**Entrada exclusivamente** de los CSV de desarrollo locales congelados de H08–H32 y H53–H58, derivados de NQ Minute Last 2020–2024. No se accede a miembros 2025–2026 del ZIP, ni a sus resultados ni a información externa. Los CSV preservan las señales y operaciones del origen; no se recalculan señales mediante decisiones a posteriori. Los padres son NQ-H09, H29, H54, H55 y H56. `side` normalizado a +1/-1. Se exige una sola señal por hipótesis y sesión y se revisan índices horarios:

- H09, H55, H56: a la conclusión de 09:45 ET, antes de entrada 09:46.
- H29: conclusión de 10:00 ET, antes de entrada 10:01.
- H54: cierre de la barra a partir de 09:47 hasta 10:45, siempre **después** de H55.
- Al filtrar por **ausencia** de una señal de otro padre, esa ausencia debe ser ya observable en el instante de la señal de trading; nunca filtrar un trade a 09:45 por la ausencia de un evento que podría ocurrir a las 10:30.

## Familia íntegra: ocho hipótesis direccionales congeladas

- **H59: H55 ∩ H56 (consenso)**. Ambos padres a 09:45, misma dirección; ejecutar una sola señal con dirección H55; predicción +30m neta positiva.
- **H60: H55 y NO H56 (exclusiva VWAP)**. A las 09:45 ambos padres ya determinados. Un trade H55; predicción +30m neta positiva.
- **H61: H56 y NO H55 (exclusiva reversión PM)**. Un trade H56 a 09:45; predicción +30m neta positiva.
- **H62: H09 y NI H55 NI H56**. Todos determinados a 09:45; seguir H09; predicción +30m neta positiva.
- **H63: H09 ∩ H56**. Ambos determinables a 09:45; solo mismo lado, un trade H09; predicción +30m neta positiva.
- **H64: H29 y NI H55 NI H56**. El estado de H55/H56 era conocido a 09:45, H29 a 10:00; seguir H29; predicción +30m neta positiva.
- **H65: H54 ∩ H55, mismas direcciones**. H55 señal a 09:45; H54 después. Ejecutar solo H54; predicción +30m neta positiva.
- **H66: H54 ∩ H55, direcciones opuestas**. H55 a 09:45, H54 después. Ejecutar solo H54; predicción +30m neta positiva: hipótesis rival para determinar si el flujo de la ruptura invalida el sesgo VWAP.

Estas ocho particiones no agotan el universo de señales ni son mutuamente excluyentes entre todas las hipótesis. Se reportan sus intersecciones como evidencia explícita de dependencia. Las condiciones de exclusividad nunca dependen de resultados, P&L, año, día de semana, cierres futuros ni MFE/MAE.

## Prueba primaria y restricciones

- Un NQ: entrada precio `OPEN` de la barra posterior a la señal y salida exactamente +30m en `OPEN`, dirección congelada; el resultado por señal se **hereda del generador de origen** sin modificación: `pnl30`, que incluye comisión NinjaTrader Free US$5.74 RT y slippage adverso US$20 RT = **US$25.74**.
- También se muestra conversión **de diagnóstico**, no validación MNQ, a 1 MNQ: `(pnl30 +25.74)/10 -3.88`; importe MNQ se basa en multiplicador $2/pt, tarifa hipotética NinjaTrader Free $1.88 RT y slippage adverso $2 RT. No es estructura de MFFU.
- Gate 1 vigente: N >150, media neta NQ >0, IC 90% de media por remuestreo semanal estricto >0, p una cola sign-flip de semanas y BH q<=0.10 sobre las **ocho**, >=3/5 años positivos. 10,000 iteraciones, semilla 20261010, nula p=1 para no estimable. Reportar IC 95%, PF, 5 años, gaps >7 días y estrés de un tick adicional por lado. Además control Holm de toda familia #5, alfa formal 0.05/(5×6)=0.001666667.
- Sin TP/SL nuevos en esta familia. Los padres H55 y H56 ya tienen un único escenario de ejecución predefinido, no mezclar su evaluación con la salida 30m. H09 tiene 18 brackets explorados; no elegirlos aquí.
- No abrir 2025 ni 2026. No declarar estrategia apta para fondeo por un resultado en 2020–2024 reciclado.

## Diagnóstico de cartera complementario (no es una novena prueba estadística)

Combinar **H09, H55, H56 y H29** con máximo un contrato **MNQ** por sesión: si hay varios eventos a 09:45, elegir H09 > H56 > H55 como prioridad mecánica (todas las coincidencias se computan y solo una operación); si no hay ninguno, admitir H29 a 10:00. Una sola salida +30min y coste MNQ $3.88. Reportar años, drawdown cerrado y frecuencia, no interpretarlo como estrategia operable sin stop/riesgo flotante. Las reglas están **fijadas antes de este cálculo de cartera**, pero se eligieron padres después de observar 2020–2024: no es prueba OOS.

## Integridad

El estudio debe detenerse si 2025/2026 aparece en los CSV, si no coinciden los horarios/IDs de origen, si hay duplicados incompatibles o si su familia no aparece congelada en el ledger. Los resultados individuales del mercado no se subirán al repositorio público. Fuente runner `research/nq/nq_h59_h66_parent_interactions.py`; tests `research/nq/test_nq_h59_h66_parent_interactions.py`.