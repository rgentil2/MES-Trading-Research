# Ranking retrospectivo monetario integral H01–H78 y T01–T208 — 13-oct-2026

**Propósito:** contestar cuáles son cinco hipótesis con mayor *capacidad monetaria histórica* documentada. Esta selección es **POST HOC**, realizada DESPUÉS de observar todos los resultados históricos. **NO es validación OOS, selección de 5 posiciones independientes, confirmación estadística, ni permiso de fondeo.** No se ejecutó nuevo backtest ni se abrió holdout. Fecha de análisis 2026-10-13.

## Universo y comparabilidad

- Se consultaron las familias originales H01–H03, H04, H05–H07, H08–H32, H33–H52, H53–H58, H59–H66, H67–H72, H73–H78; historia H de NQ minutos **2020–2024**, holdouts H 2025–26 cerrados.
- Se contrastaron T01–T13, T14–T19, T20–T25, T26–T28, T29–T58, T59–T96, T97–T132, T133–T168 y monetarias T169–T188 y T189–T208, sobre datos ya investigados T Last DEV **2025-10 a 2026-04**, 140 sesiones fuente/135 READY. Holdouts T mayo–sept2026 cerrados.
- **La mayoría de las hipótesis NO tienen estrategia negociable medida.** H01–H66 incluyen numerosos screens de movimiento a +30 minutos sin bracket real; T20–T132 mayoritariamente son pronósticos de rango/markout sin simulación económica. No convertir amplitud, acumulados de retorno direccional ni N eventos en PnL operable. Entre las 36 T133–T168 ninguna supera todos los gates económicos aun sin q/IC90. En T169–T188 ninguna aprueba, la única aportación neta positiva al router es T186 +US$280 extra10, pero falla PF y DD; T189–T208: 0 positivos incremental, 2 N/D.
- **Criterio cualitativo de priorización** (no puntuación artificial): beneficio neto de ejecución con stop/TP y costos documentados > retorno direccional sin salidas; actividad suficiente/robustez temporal > solo un mes rentable; beneficio neto unido a drawdown y PF > PnL nominal sin control; prioridad a modelos de fuente o arquitectura diferente, pero evidenciar dependencias y superposición. El ranking **NO** suma NQ con MNQ, no anualiza ventanas incompatibles, no equipara DD Last con DD equity cerrada y no afirma costo comparable.

## Cinco perfiles económicos con más interés histórico — NO cinco alphas

| Puesto exploratorio | ID | Universo, contrato y escenario | N trades | Neto histórico USD | PF | DD USD | Años/meses + | Principal limitación |
|---|---|---|---:|---:|---:|---:|---|---|
| 1 | **T05-377** | 2025oct–2026abr, **1 NQ**, Last estrés T04 | **115** | **+5.102,50** | **1,31826** | **1.797,50** Last | **6/7 meses** | Extra **US$10 RT** reduce a +3.952,50 y PF1,23717<1,25; DD Last bajo reordenamiento intratimestamp hasta 2.462,50; cero OOS y fills broker no probados |
| 2 | **H09** | 2020–24, **1 NQ**, stop15%/TP1,5R/30m **configuración central**, no la ganadora ex post | **173** | **≈+18.874** (+109,09/trade redondeado) | **1,369** | **8.122** cerrado | **4/5 años** | DD NQ impropio para referencia fondeo US$2K, largos intervalos sin trades. Mismo escenario de **1 MNQ sintético**: +9,60/trade ≈US$1.661, PF1,318, DD860 |
| 3 | **H69** | 2020–24, **1 MNQ proxy**, H09 O H56, SL15%/TP1,5R/30m, costo RT USD3,88 | **262** | **+2.704,44** | **1,335** | **890,64** cerrado | **4/5 años** | Mejora de +630,18 frente a H09 bajo su costo común, pero q BH 0,115>0,10; 2022 concentra una parte importante; CAGR nominal 50k **1,06%** |
| 4 | **H77** | 2020–24, **1 MNQ proxy**, H09 si gap/PM alineados, H56 si opuestos | **140** | **+2.385,30** | **1,632** | **584,54** cerrado | **4/5 años** | Año 2022 concentra **75,2%** del resultado, N140 no supera >150, resta **−319,14** versus H69 bajo misma cuenta, q nominal familia0,0468 NO salva selección adaptativa |
| 5 | **H74** | 2020–24, **1 MNQ proxy**, H09 en volatilidad previa baja y H56 en alta | **132** | **+1.657,84** | **1,438** | **444,10** cerrado | **5/5 años** | Baja frecuencia, N132, q=0,1149>0,10; diferencia **−1.046,60** frente a H69; CAGR nominal 50k **0,65%** |

**Fuente exacta de resultados:**
- [T05 benchmark/motores y comparación explícita](NQ_D2_SHADOW_T147_VS_T05_BASELINE_COMPARISON_2026_10_12.md), [T05 bootstrap](NQ_B05K_T05_DAILY_BLOCK_BOOTSTRAP_RESULTS_2026_10_11.md), y [B05G sensibilidad Last](../../local_nq_tick_2025_2026/NQ_B05G_LAST_TIMESTAMP_SENSITIVITY_RESULTS_2026_10_11.md).
- [H09 ejecución central y sensibilidad de 18 parámetros](NQ_H01_H02_H05_H09_EXECUTION_EXPLORATION_RESULTS_2020_2024.md). H09 ex post stop20%/TP2R/+30m +US$36.049,98 para 1 NQ, PF1,625, DD8.928,22: **NO** usar esa opción elegida ex post para elevar el ranking confirmatorio.
- [H69 grupo completo y delta vs H09](NQ_H67_H72_RESULTS_2020_2024.md); [H74/H77 comparación emparejada y años](NQ_H73_H78_RESULTS_2020_2024.md).
- [T133–T168 36 económicos](NQ_T133_T168_ECONOMIC_GATES_WITHOUT_Q_OR_IC90_2026_10_12.md), [D2 shadow T147 vs T05](NQ_D2_SHADOW_T147_VS_T05_BASELINE_COMPARISON_2026_10_12.md), [T169–T188](NQ_T169_T188_MONETARY_V3_20_RESULTS_2026_10_13.md), [T189–T208](NQ_T189_T208_20_MONETARY_RESULTS_2026_10_13.md).

## Por qué otros casos de gran PnL aparente no superan a esos cinco

- **H02 2020–24 +US$24.628,52, H36 aprox. +US$19.800 (114 ×173,56), H44 aprox. +US$15.669 (22×712,21)**: resultados **a 30 minutos SIN stop/TP confirmados** de sus screens originales. H02 ejecutable con bracket central baja PF a 1,027 y su DD cerrado NQ sube a US$14.125; H44 solo 22 eventos y selección retrospectiva. No confundir evento predictivo con dinero realizable.
- **H56** 100 operaciones, 1 NQ, bracket15%/1,5R/30min **+US$8.697,98**, PF1,269, DD cerrado **US$3.599,09**, 4/5 años positivos. Es un **progenitor monetario interesante** de H69/H74/H77, pero peor frecuencia y DD en 1 NQ no permite adoptar la estrategia en 50k. La relación con los routers H es clara y no aporta una sexta familia independiente.
- **T134** +US$846,50/PF2,153 y **T147** +US$642,25/PF1,499, pero N14 y N20 respectivamente; T147 tiene estrés fricción1,5× +US$433 y sobretasa extra10 +US$442,25; 2025Q4 −US$567, ene–abr2026 +US$1.209,25 y 2,86 trades/mes; **NO** router T05+T147 comprobado con misma cuenta. **T145** +US$788/51/PF1,238, peor que gate1,25 y concentra beneficios en un mes 45,4%; T133 PF1,178 y tramos incompatibles. Todos 0 supervivientes de D1 aun quitando q e IC90.
- **T186** no tiene beneficio standalone (−US$970 bajo estrés, N70), pero **sí** efecto incremental sobre el router **+US$780 estrés / +US$280 con sobretasa $10RT**, ejecuta 50 nuevas, retiene 115 T05; **falla** PF router extra10=1,20198<1,25 y DD Last estrés=2.130>2.000. Es una **señal de posible complementariedad**, NO una de las cinco mejores estrategias autónomas.
- **T29/T45/T49, T75/T84, T100/T112/T130**, etc.: efectos causales observacionales sobre amplitud o VWAP de 15min, **no cuentan con fills, stop/TP, PF monetario ni DD**; no rankear USD inventados.

## Conclusión aplicable al proyecto

1. **Ranking por potencial histórico, no por probabilidad futura:** T05 es el mejor candidato del desarrollo tick 2025–26 por frecuencia/beneficio neto simulado. H09 es el padre más atractivo del desarrollo minuto 2020–24 por monetización con bracket uniforme, aunque el NQ pleno tiene DD incompatible con la referencia US$2K. H69 es el mejor de los routers H por beneficio y frecuencia, H77 ofrece el mayor PF del grupo y H74 el DD más pequeño con años 5/5 positivos.
2. **No son cinco alphas independientes**: H09 es componente de H69/H74/H77, y H56 es el otro componente. Conceptualmente el catálogo TOP5 representa principalmente **dos familias de mecanismo**: T05 OR fallida filtrada 377 vs gap/premarket H09/H56. No recomendar sumarlos ni crear cinco posiciones. Ni H77 ni H74 mejoran el PnL de H69 en el contraste emparejado existente.
3. **No existe todavía cinco estrategias listas para fondeo.** Ninguna certificó fills de mercado, trailing DD flotante, compatibilidad con $50k ni CAGR mayor al `max(15%,VOO,QQQM)` en ventanas alineadas. H69 nominal CAGR 1,06%, H77 0,94%, H74 0,65% calculados sobre 50k, todos bajo 15%.
4. Una comparación *incremental real* T05+H requiere primero conciliación de periodos y datos: H 2020–24 y T05 2025–26 DEV nunca se han evaluado juntos sobre misma muestra autorizada ni bajo motor, horarios y fees comunes. **No abrir holdout**, no añadir historia, no inferir que H protege T05. Las T147/T186 pueden conservarse como **observación secundaria** de microestructura pero no promocionarse seleccionando su resultado favorable.

**Nuevos outcomes realizados en este informe: NINGUNO.** El análisis sintetiza documentación inmutable de varios experimentos anteriores; el top5 es una priorización exploratoria retrospectiva.
