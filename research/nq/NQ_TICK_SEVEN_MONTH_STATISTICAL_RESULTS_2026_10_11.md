# NQ T — Resultados de la evaluación estadística adaptada a siete meses

Fecha de actualización documental 2026-10-11 Colombia; GitHub Actions **2026-10-12 UTC**. **No hay nueva hipótesis, nueva data, nuevas órdenes simuladas ni acceso a los holdouts.** Es un diagnóstico posterior de estrategias históricamente elegidas, basado exclusivamente en el artifact `summary.json` que ya existía de B05H02.

**Política prospectiva aplicada:** [NQ_TICK_SEVEN_MONTH_STATISTICAL_POLICY_2026_10_11.md](NQ_TICK_SEVEN_MONTH_STATISTICAL_POLICY_2026_10_11.md), commit `b4e80c6864f0c0b4ef7a153edda5167f32cc2a3d`.

**Implementación ejecutada:** [nq_tick_seven_month_diagnostic.py](nq_tick_seven_month_diagnostic.py), commit `45190a257df161fcdb8541304e500c7ab6878130`; [pruebas sintéticas](test_nq_tick_seven_month_diagnostic.py), commit `2f4ba0384b0458ed11b9295424e2a20988b2f9fd`; [workflow de solo artifact seguro](../../.github/workflows/nq-tick-seven-month-stats-existing-aggregate.yml), commit `1d5f255b6386d8b7ec79bd925e96a563a0dc4e1e`. [**Run 38200366148 COMPLETED SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38200366148), **6 tests PASS**, artifact `nq-seven-month-descriptive-stats-no-new-ticks`.

## Evidencia REAL que admite este tamaño muestral

**Fuente:** 7/7 meses 2025-10 a 2026-04, 140 sesiones fuente/135 elegibles. Total de trades: T05=115, H02=75, router T05+H02=166; **no** significa 115/75/166 eventos independientes, ni que existan datos de P&L diario por sesión en el artifact seguro. Este diagnóstico tiene **N estadístico=7 OBSERVACIONES MENSUALES**. Se ha calculado sobre NETO escenario estrés en USD y **sin completar/seleccionar meses de forma oportunista**.

| Unidad de resultado mensual (USD) | N trades | Meses P&L positivo/7 | Neto siete meses USD | Media mensual USD | IC90 bilateral de la media mensual (USD/mes) | p unilateral exacto del signo mensual* | ¿Gate estadístico aprobado? |
|---|---:|---:|---:|---:|---|---:|---|
| T05-377 (standalone) | 115 | **6/7** | **+5.102,50** | +728,93 | **[+98,03, +1.359,83]** | 0,0625 | **NO EVALUABLE FORMALMENTE** |
| H02-377 (standalone) | 75 | **2/7** | **−1.427,50** | −203,93 | **[−576,31, +168,45]** | 0,9375 | **NO EVALUABLE / DESCARTADA OPERATIVAMENTE** |
| Router T05 + H02 (misma cuenta) | 166 | **6/7** | **+2.195,00** | +313,57 | **[−221,53, +848,67]** | 0,0625 | **NO EVALUABLE FORMALMENTE** |
| **Δ router − T05, EMPAREJADO** | N/A: diferencia mensual | **0/7** | **−2.907,50** | −415,36 | **[−777,42, −53,29]** | 1,0000 (hipótesis mejora positiva) | **NO: ECONÓMICAMENTE DESFAVORABLE** |

*El test de signo unilateral modela 7 signos mensuales como independientes/equiprobables bajo la nula; estos supuestos no se verifican con 7 meses consecutivos y **el p NO es q BH ni evidencia confirmatoria**. Un IC90 positivo mensual de T05 NO permite inferir confianza por trade/semana y está sujeto a búsqueda adaptativa previa. Usamos Student `t(0,95;6)=1,9431802805` y `n=7`; intervalos en USD **por MES**, no USD por trade.

## Leave-one-month-out (LOMO) sin rescatar variantes

- **ΔRouter menos T05** permaneció negativo si se excluye cualquiera de los siete meses. Rango de neto de seis meses **[−US$2.895,00, −US$1.442,50]**. No se seleccionó ni eliminó ningún mes: solo sensibilidad.
- T05 continúa históricamente más prometedora que añadir H02, pero **con estrés+$10 RT PF=1,23717**, incertidumbre de ejecución y riesgo de timestamp. No está lista para fondeo.
- Con 7 meses el test de signos de 5/7 positivos tendría todavía **p=0,2265625** bajo independencia, por lo que un umbral 5/7 solo puede ser señal de consistencia descriptiva, NO significancia.

## Qué cambia en el programa T (y qué no)

1. **Ya NO trasladar mecánicamente el test 3/5 años de H 2020–24** a los siete meses T. Mostrar aquí **meses positivos 0–7, IC90 USD/mes descriptivo, p signo bajo supuestos y LOMO**, sin llamar a esto una prueba formal de alpha.
2. **N trades, N sesiones y N unidades de inferencia quedan separados**. Para un resultado definitivo de desarrollo se requiere P&L por TODAS las 135 sesiones, ceros incluidos, análisis de bloques de **cinco sesiones**, IC90 de media diaria y p unilateral bajo dependencia, sensibilidad 3/10 sesiones; la familia de q BH debe estar preregistrada completa y Holm sigue siendo puerta independiente. **Estos últimos aún NO han sido calculados**, porque el artifact sólo contiene montos mensuales.
3. No disminuir arbitrariamente N>150 a 75 o 100 para aprobar H02/T05; la política histórica continúa congelada. Los 135 días sí se pueden usar para **medir incertidumbre**, no para prometer validación que excede su información.
4. T05 **exploratoria**, H02 **rechazada**, H01 **ejecución ambigua**. No traer más históricos, abrir OOS ni usar 5 segundos para las señales nuevas.

**Resultado:** `NQ_T_7_MONTH_DESCRIPTIVE_DIAGNOSTIC_COMPLETE`, **ningún Gate 1 estadístico formal aprobado**; ninguna estrategia con autorización de fondeo.
