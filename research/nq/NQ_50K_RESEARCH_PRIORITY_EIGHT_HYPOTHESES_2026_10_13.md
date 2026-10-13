# Decisión de investigación NQ/MNQ: priorizar estrategias, referencia futura USD 50K — 2026-10-13

**Decisión del usuario:** prefiere en el futuro una evaluación de **USD 50.000** por menor coste y objetivo de aprobarla, pero **pospone elegir, comprar o activar una cuenta** hasta terminar la investigación de hipótesis y una estrategia/cartera ejecutable. No se autoriza operativa real. La preferencia de 50K NO modifica retrospectivamente los gates de las hipótesis ni implica validar un programa específico de MFFU; sus términos se comprobarán de nuevo al llegar a la fase comercial.

**Alcance de este documento:** diagnóstico de investigación y backlog con resultados existentes. **No hay backtest nuevo, parámetros optimizados, OOS abierto, señales nuevas, compras ni confirmaciones de fondeo.** No confundir objetivos de cuenta nominal con dinero realmente disponible para pérdidas.

## Ocho hipótesis revisadas y sus dependencias

| ID | Mecanismo original | Datos DEV ya usados | Métrica monetaria existente | Consideración crítica |
|---|---|---|---|---|
| T05-377 | T02 falsa ruptura 09:30–09:35 + desaceleración prints + contexto de 377 barras completas contrario al giro | NQ Last oct2025–abr2026, 135 READY | 1NQ, 115 trades, +USD 5.102,50 estrés, PF1,31826, Last DD1.797,50; +USD10 RT: neto3.952,50, PF1,23717; intratimestamp DD hasta2.462,50 | Padre legacy usa 5s y 377-print; NO cambiar señalamientos ni atribuir fills verificados |
| H09 | Continuación de gap y primer cuarto de hora RTH | NQ minuto 2020–24 | 1NQ bracket central 173, neto ~18.874, DD cerrado ~8.122; proxy 1MNQ ~1.661 y DD~860 | 1NQ supera ampliamente pérdida nominal 50K; adaptar tamaño NO es validar resultados |
| H56 | Giro 09:31–09:45 contra desplazamiento 08:30–09:30 | NQ minuto 2020–24 | 1NQ N100, +8.697,98, DD cerrado3.599,09 | Poca frecuencia y muestra; progenitor de routers |
| H69 | Primera señal H09 OR H56 (prioridad H09); 1 operación/día | NQ minuto 2020–24 | Proxy 1MNQ N262, +2.704,44, DD cerrado890,64, PF1,335 | Router H comparador, q BH 0,115; no cumple 15% anualizado |
| H77 | GAP y cuerpo premercado alineados -> H09; opuestos -> H56 | NQ minuto 2020–24 | Proxy 1MNQ N140, +2.385,30, DD cerrado584,54 | H69 lo supera en neto bajo mismo universo; 75,2% neto procede de 2022 |
| H74 | Volatilidad previa baja -> H09; alta -> H56 | NQ minuto 2020–24 | Proxy 1MNQ N132, +1.657,84, DD cerrado444,10 | H69 lo supera en neto bajo mismo universo; N insuficiente |
| T147 | Barrida de extremo de 4181 prints completos y rechazo en E377 | NQ Last oct2025–abr2026 | N20, +642,25 base, +433 estrés 1,5x, DD cerrado567 | No existe T05+T147 con ejecución compartida, 2,86 trades/mes |
| T186 | Desviación >=48 ticks respecto VWAP 4181 revierte | NQ Last oct2025–abr2026 | Standalone -970 estrés/N70; router T05+T186 +780 incremental estrés, +280 extra10; DD Last router2.130, PF extra10=1,20198 | Falla economics; positivo marginal no significa señal independiente ni robusta |

**No son ocho estrategias diversificadas.** H69/H74/H77 reciclan H09/H56; no duplicarlas en la misma cuenta. Las H usan 2020–24 minuto; las T 2025–26 tick DEV. H 2025/26 está sellado, T mayo–sept2026 sellado; **no reutilizar las fechas T como OOS H ni juntar resultados de ventanas incompatibles**.

## Orden propuesto de investigación, sin cambiar puertas estadísticas

1. **Auditar riesgo monetario real del modelo T05**, sin reoptimizar: pérdida por operación y por sesión, equity *floating* de máxima excursión adversa, trayectoria Last intratimestamp adversa, costo +USD10 RT y tolerancia a fills peores. El presupuesto USD2.000 funciona como **filtro referencial de 50K**, no como validación contractual MFFU ni justificación de reducir un umbral para hacer pasar al ganador.
2. **Evaluar complementariedad T05 y T147 solo si existe comparabilidad**: primero reproducciones exactas de sus salidas originales (115 y 20 trades), armonización explícita de coste, sesiones, stop/TP y manejo de mismo timestamp, arbitraje por orden cronológico sin información futura, una cuenta, posición excluyente, máximo de entradas y riesgo común. Prerregistro ANTES de medir el router. El estudio sería *shadow DEV* post-selección, no D2 formal ni OOS; sin datos nuevos. Si es físicamente imposible armonizar, dejar N/D y no sumar P&L.
3. **Mantener T05+T186 como contraejemplo** a la mejora aparente: el delta positivo +280 extra10 no cumple PF1,25 ni DD nominal2.000; no manipular horarios/filtros retrospectivamente.
4. **Consolidar familias H, sin backtest sobre holdouts**: H69 como router comparador en 1MNQ sintético; medir mecanismos H09 y H56 por separado, solapamiento, aporte marginal por régimen y fragilidad de concentración en 2022; H74/H77 como alternativas históricas no independientes, sin promocionar PF alto a validación. 1NQ H09/H56 excede el presupuesto DD indicativo.
5. **Puerta a cualquier cuenta futura**: cartera con aportación neta robusta tras costos, PF>=1,25 bajo estrés, supervivencia de drawdown flotante y trailing a reglas exactas, estabilidad mensual y revisión de fills/bid/ask, reglas de noticias y actividad/inactividad. Confirmación independiente y tres fuentes de alpha realmente distintas siguen metas, no logros.

**Política de actividad:** no usar operaciones *de relleno* únicamente para cumplir inactividad como parte de una estrategia investigada. Una posible orden de rápida entrada/salida en MNQ tendría spread, comisiones, slippage y riesgo real; una decisión de cumplimiento futura se hará con las reglas oficiales vigentes y sin asumir que un trade artificial es una solución sin coste.

**Próximo entregable sugerido:** auditoría de factibilidad/riesgo para T05, T147 y T186 usando SOLO artefactos ya existentes, seguida de una **propuesta congelable de motor compartido T05+T147** si la comparabilidad de entradas/salidas lo permite. No se ha corrido este siguiente análisis con este documento.

**Fuentes internas:** [ranking integral H/T](NQ_ALL_H_T_TOP5_MONETARY_RANKING_2026_10_13.md), [contraste T05/T147](NQ_D2_SHADOW_T147_VS_T05_BASELINE_COMPARISON_2026_10_12.md), [T169–188 monetario](NQ_T169_T188_MONETARY_V3_20_RESULTS_2026_10_13.md), [H69](NQ_H67_H72_RESULTS_2020_2024.md), [H74/H77](NQ_H73_H78_RESULTS_2020_2024.md).
