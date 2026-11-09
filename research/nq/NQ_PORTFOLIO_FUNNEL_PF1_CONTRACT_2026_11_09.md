# NQ PF1 — CONTRATO CONGELADO DEL NUEVO EMBUDO DE PORTAFOLIOS

**Fecha:** 2026-11-09 | **ID estable:** NQ_PF1 | **Versión:** 1.0.0 | **Estado real:** SPEC_ONLY (documentado, **NO implementado ni aprobado para operar**).

**Objeto de evaluación definitivo:** portafolio de 3 a 5 estrategias que opere exclusivamente NQ con **máximo 1 contrato simultáneo**. El generador explora los 100.000 genomas ya existentes, pero los PF, drawdowns, Stability, Symmetry, Monte Carlo y OOS aprobatorios son los del **historial de operaciones efectivamente ejecutadas por el gestor central**, jamás la suma de tres estrategias operando al mismo tiempo.

**Este contrato NO cambia objetivos ni códigos V19–V25.** Leer además [CONTRATO DE VERSIONES V19–V25](NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md). V22 y el PR V25 #84 conservan alcance histórico; ninguno pasa automáticamente a implementar PF1. No mezclar PF1 con investigaciones antiguas MES/ES/H/T.

**Fuente vinculante machine-readable:** [NQ_PORTFOLIO_FUNNEL_PF1_RULES_2026_11_09.json](NQ_PORTFOLIO_FUNNEL_PF1_RULES_2026_11_09.json). [Bitácora append-only](NQ_PORTFOLIO_FUNNEL_PF1_CHANGELOG.md). Los tres archivos se modifican juntos, solo mediante cambios expresos y una nueva versión.

**Tiempo:** IS 2020-01-01 a 2022-12-31 (36 meses); **congelar** ganadores, genes, parámetros y prioridades ANTES del OOS; OOS 1 2023-01-01 a 2024-12-31 (24 meses); OOS 2 2025-01-01 a 2026-10-31 (22 meses). Son **46 meses OOS**, sin reiniciar drawdown al cambiar de año. No usar noviembre incompleto. Ninguna reoptimización con datos OOS. Aunque otros programas del repo sí han investigado 2023+, registrar y no ocultar esa exposición previa; este holdout está definido en relación con PF1.

**Decisión operativa:** después de pruebas históricas no existe etapa obligatoria de paper forward en tiempo real, según instrucción del usuario. Aun así se requiere verificar de forma independiente seguridad de órdenes, conexión, broker y reglas actuales de fondeo antes de habilitar dinero real. Pasar gates no garantiza pérdidas limitadas ante gaps o slippage.

**Línea base congelada:** también permanecen los valores que antes se llamaban propuestos: 30 trades individuales, USD200 por entrada, pausa USD500, emergencia USD750, protección DD USD1600 y 5.000 MC confirmatorios. No afirmar que estén optimizados ni cambiarlos silenciosamente.

## Embudo 1 — Banco de estrategias e integridad

**Periodo:** IS 2020–2022.

| Filtro | Exigencia |
|---|---:|
| Banco inicial | 100.000 estrategias |
| Genes por estrategia | 20 genes |
| Formulas tecnicas | 120 formulas |
| Condiciones direccionales | 1.320 condiciones |
| Temporalidad | 1 minuto |
| Meses IS | 36 meses |
| Genomas invalidos | 0 casos |
| Duplicados canonicos | 0 casos |
| Referencias a futuro | 0 casos |
| IDs y parametros trazables | 100 % |

## Embudo 2 — Preseleccion individual ligera

**Periodo:** IS 2020–2022.

| Filtro | Exigencia |
|---|---:|
| Operaciones historicas minimas | ≥30 trades |
| Contratos por senal | 1 NQ |
| Entradas sin stop | 0 casos |
| Riesgo planificado por operacion | ≤200 USD |
| Slippage entrada | 2 ticks |
| Slippage salida | 2 ticks |
| Comision ida/vuelta | 4,68 USD |
| Costo base ida/vuelta | 24,68 USD |
| Multiplicador base | 1 x |
| Genomas redundantes | 0 casos |
| Errores contables | 0 casos |

## Embudo 3 — Construccion de portafolios

**Periodo:** IS 2020–2022.

| Filtro | Exigencia |
|---|---:|
| Estrategias por portafolio | 3–5 estrategias |
| Tamanos explorados | 3, 4, 5 estrategias |
| Correlacion mensual positiva entre miembros | ≤0,45 rho |
| Concentracion beneficio bruto ganador por miembro | ≤40 % |
| Identidades duplicadas | 0 casos |
| Combinaciones repetidas | 0 casos |
| Contratos simultaneos previstos | ≤1 NQ |
| Slippage ida/vuelta supuesto | 4 ticks |
| Costo base por trade | 24,68 USD |

## Embudo 4 — Ejecutor central de NQ

**Periodo:** IS 2020–2022.

| Filtro | Exigencia |
|---|---:|
| Contratos simultaneos | ≤1 NQ |
| Posiciones simultaneas | ≤1 posicion |
| Riesgo planificado por entrada | ≤200 USD |
| Slippage entrada | 2 ticks |
| Slippage salida | 2 ticks |
| Comision RT | 4,68 USD |
| Costo base RT | 24,68 USD |
| Pausa preventiva por perdida diaria | 500 USD |
| Cierre preventivo por perdida diaria | 750 USD |
| Bloqueo preventivo de DD equity | 1.600 USD |
| DD objetivo maximo | ≤2.000 USD |
| Perdida diaria objetivo maxima | ≤1.000 USD |
| Entradas sin stop | 0 casos |
| Entradas por encima del riesgo | 0 casos |
| Posiciones fuera de horario | 0 casos |

## Embudo 5 — Economia y riesgo del portafolio ejecutado

**Periodo:** IS 2020–2022.

| Filtro | Exigencia |
|---|---:|
| Beneficio neto | >0 USD |
| Profit Factor neto | ≥1,25 |
| Operaciones totales | ≥150 trades |
| Operaciones por mes completo | ≥5 trades |
| Meses evaluados | 36 meses |
| Meses con frecuencia inferior | 0 meses |
| Stability | >30 % |
| Symmetry | >30 % |
| DD cerrado | ≤2.000 USD |
| DD adverso M1 | ≤2.000 USD |
| Perdida diaria maxima | ≤1.000 USD |
| Exposicion adversa simultanea | ≤1.000 USD |
| Costo base RT | 24,68 USD |
| Multiplicador de costos estresados | 1,5 x |
| Costo estresado RT | 37,02 USD |
| Beneficio con costos 1.5x | >0 USD |
| Años IS con beneficio positivo | 3 de 3 |
| PF minimo por año | ≥1 |
| Concentracion beneficio bruto ganador | ≤40 % |
| Contratos simultaneos | ≤1 NQ |

## Embudo 6 — Robustez: Monte Carlo del portafolio

**Periodo:** IS 2020–2022.

| Filtro | Exigencia |
|---|---:|
| Simulaciones exploratorias | 500 caminos |
| Simulaciones confirmatorias | 5.000 caminos |
| Bloque bootstrap | 8 trades |
| Percentil drawdown | 95 P |
| DD Monte Carlo P95 | ≤2.000 USD |
| Multiplicador de costos | 1,5 x |
| Costo adicional por trade sobre neto base | 12,34 USD |
| Beneficio total estresado | >0 USD |
| Portafolios aprobados que incumplen P95 | 0 casos |

## Embudo 7 — Validacion nativa NinjaTrader y congelacion

**Periodo:** IS 2020–2022.

| Filtro | Exigencia |
|---|---:|
| Temporalidad | 1 minuto |
| Contratos simultaneos | ≤1 NQ |
| Beneficio neto nativo | >0 USD |
| PF nativo | ≥1,25 |
| Operaciones nativas | ≥150 trades |
| Stability nativa | >30 % |
| Symmetry nativa | >30 % |
| DD nativo | ≤2.000 USD |
| Perdida diaria nativa | ≤1.000 USD |
| MC P95 DD de ejecuciones nativas | ≤2.000 USD |
| Costos bajo estres | 1,5 x |
| Operaciones duplicadas | 0 casos |
| Senales sin reconciliar | 0 casos |
| Entradas sin stop | 0 casos |
| Violaciones de contratos | 0 casos |
| Diferencias monetarias injustificadas | 0 casos |
| Cambios de parametros tras congelar | 0 casos |

## Embudo 8 — OOS historico cronologico del sistema congelado

**Periodo:** OOS 2023–octubre 2026.

| Filtro | Exigencia |
|---|---:|
| OOS 1 | 2023-01-01 a 2024-12-31 |
| OOS 2 | 2025-01-01 a 2026-10-31 |
| Meses OOS completos | 46 meses |
| Beneficio neto por bloque OOS | >0 USD |
| PF minimo por bloque OOS | ≥1,25 |
| PF OOS acumulado | ≥1,25 |
| Operaciones por mes completo OOS | ≥5 trades |
| Stability OOS acumulada | >30 % |
| Symmetry OOS acumulada | >30 % |
| DD OOS continuo sin reinicio anual | ≤2.000 USD |
| Perdida diaria maxima OOS | ≤1.000 USD |
| Estres de costos OOS | 1,5 x |
| Beneficio OOS estresado | >0 USD |
| Monte Carlo OOS P95 DD | ≤2.000 USD |
| Contratos simultaneos OOS | ≤1 NQ |
| Reoptimizaciones usando OOS | 0 casos |
| Cambios despues de observar OOS | 0 casos |

## Embudo 9 — Decision de habilitacion operativa NQ

**Periodo:** Despues de aprobar 1–8.

| Filtro | Exigencia |
|---|---:|
| Embudos anteriores aprobados | 8 de 8 |
| Contratos simultaneos | ≤1 NQ |
| Stability final | >30 % |
| Symmetry final | >30 % |
| PF final | ≥1,25 |
| DD objetivo | ≤2.000 USD |
| Perdida diaria objetivo | ≤1.000 USD |
| Monte Carlo P95 DD | ≤2.000 USD |
| Estrategias seleccionadas | 3–5 estrategias |
| Entradas sin stop | 0 casos |
| Ordenes rechazadas sin gestionar | 0 casos |
| Errores criticos sin resolver | 0 casos |
| Reoptimizaciones con OOS | 0 casos |

## Fórmulas y precedencia obligatoria

**Stability >30% (estricto):** calcular equity neta diaria al cierre del portafolio, incluyendo días válidos sin trades; ajustar regresión lineal OLS vs índice secuencial de día. Si pendiente positiva y R² definido: Stability = 100 × R²; si pendiente no positiva: 0%; si varianza o muestra insuficiente: FAIL. Es una fórmula reproducible **propia del proyecto**; no afirmar identidad con la Stability propietaria de StrategyQuant.

**Symmetry >30% (estricto):** L = suma P&L neto de trades Long ejecutados, S = suma P&L neto de trades Short ejecutados. Si L>0 y S>0: Symmetry = 100 × min(L,S)/max(L,S); de lo contrario 0%. Solo fills del ejecutor; no señales descartadas. Exigir en IS, nativo y OOS acumulado.

**Correlación preliminar ≤0,45:** Pearson entre series mensuales netas independientes sobre idénticos 36 meses IS, máximo par positivo; denominador cero o indefinido no significa PASS. Correlación no sustituye el DD y exposición conjunto del ejecutor central.

**Concentración ≤40%:** participación de cada miembro sobre el **beneficio bruto de trades ganadores efectivamente ejecutados** atribuibles a ese miembro, dividida por el beneficio bruto positivo total del portafolio. Si no hay beneficios, FAIL. El denominador se fija así para evitar reinterpretar el filtro cuando un miembro tenga neto negativo.

**Fricción sin duplicación:** cada tick de 1 NQ = USD5; 2 ticks entrada + 2 ticks salida = USD20; comisión RT USD4,68; **costo base USD24,68**, estrés 1,5× = **USD37,02**. Sobre netos que YA contienen costo base, Monte Carlo agrega **solo USD12,34** por operación. Las órdenes límite, stop y mercado deben modelarse sin inventar fills ni descontar la misma fricción dos veces. El riesgo por operación incluye el costo base USD24,68 además de la pérdida del stop. Si excede USD200, omitir la entrada, no modificar su stop original o ATR.

**Monte Carlo PF1:** moving block bootstrap sobre las operaciones **del ejecutor central**, ordenadas cronológicamente por cierre, longitud 8 trades, 500 caminos iniciales, 5000 confirmatorios, con semilla/versiones declaradas en el manifiesto; límite **P95 del drawdown máximo ≤USD2000**. No es una garantía de protección intrabar ni capta todas las dinámicas de órdenes.

**OOS frente a walk-forward:** PF1 hace **OOS cronológico congelado** sobre 2023–24 y 2025–Oct2026, **no** rolling reoptimization anual (0 reajustes). La etiqueta walk-forward en software heredado no prueba automáticamente esta validación. Si un OOS falla, no retocar parámetros con su resultado y seguir llamándolo independiente.

**Controles operativos:** USD500 de pérdida diaria pausa entradas; USD750 solicita cierre de emergencia; USD1600 DD marcado bloquea; objetivos de cuenta USD1000/día y USD2000 de DD. Medir equity flotante y cronología; los stops y bloqueos no garantizan fills ni DD real frente a gaps, latencia y fallos.

## Estados y reglas de bloqueo

SPEC_ONLY → IMPLEMENTED_UNTESTED → IS_RESEARCH_PASS → NATIVE_PARITY_PASS → FROZEN_BEFORE_OOS → OOS1_PASS → OOS2_PASS → READY_FOR_OPERATIONAL_REVIEW. Todo gate ausente, indefinido o sin evidencia = **FAIL / PENDING**, nunca PASS. Ninguna de las siete ternas heredadas queda promovida a aprobado. El estado actual es **SPEC_ONLY**.

**Control de cambios innegociable:** no ajustar criterios o fórmulas, renombrar objetivos históricos ni modificar ventanas por iniciativa del implementador. Requiere propuesta explícita, diff antes/después, análisis de impacto sobre OOS, decisión del usuario, nuevo PR, nueva versión (PF1 1.1.0 o PF2 según alcance), registros append-only y regresiones; preservar versión original. Una implementación PF1 debe registrar el ID/versión/hash de esta especificación y reportar PASS/FAIL por etapa. Si JSON, código y documentación no coinciden, no autorizar OOS ni trading.
