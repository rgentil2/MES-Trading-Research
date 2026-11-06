# NQ S0.83 — V22: Auditoría integral de robustez, walk-forward y portafolios 3–5

**Fecha:** 2026-11-06  
**Estado:** C# offline con pruebas controladas y workflows de GitHub; **no** resultados de mercado NQ ni NinjaTrader nativo.

## Alcance acordado: V22 = cierre de robustez y portafolio, NO escalado masivo

Se restablece explícitamente la numeración que el usuario recordó. **V22** cierra la validación integral del embudo: >=150 operaciones, >=5 por **cada uno de los 36 meses** 2020–2022, PF neto >=1,25, neto positivo, costos 1,5×, DD cerrado y MAE/MFE bajo $2.000, bootstrap Monte Carlo, estabilidad 2020/21/22, selección diversificada 3–5, correlación mensual <=0,45 y concentración <=0,40, riesgo simultáneo y DD adverso de cuenta < $2.000, pérdida intradiaria y riesgo concurrente < $1.000, cuatro folds train-only V20 y congelación EXCANv19 de los genes exactos. **V23** queda reservado al perfilado de backtests económicos de 36 meses y escala 10k/100k.

El usuario decidió continuar con **NQ DEC2026** como instrumento final en NinjaTrader; la data M1 2020–2022 está disponible directamente en su plataforma según indicó. **No** solicitar análisis de contratos/rollover, compilación/interacción NinjaTrader intermedia, ni nuevas exportaciones; terminar todo primero y migrar **una única vez al final**.

## Cambios funcionales

1. **`NQNativePortfolioAuditV22.cs`** introduce `NQPortfolioAuditConfigV22` y resultado auditado por estrategia y por portafolio. Ejecuta el G0 exacto de V6/V7 vía V13, registra fallas múltiples, P&L, PF, número de operaciones, costo 1,5×, drawdown bootstrap P95. Revisa por separado resultados de **2020, 2021 y 2022** (neto positivo, PF anual >=1,0, >=5 operaciones en cada uno de sus 12 meses y DD cerrado anual <= $2.000); requiere por defecto **3 de 3 años** para evitar confundir el antiguo objetivo de 4/5 años con la fuente real actual 2020–22. El requisito G0 36 meses sigue intacto.
2. La auditoría aplica `NQNativeIntegratedPortfolioRiskV15`: selección V13 exactamente **3–5** candidatos, operaciones y fills reconciliados, correlación mensual <=0,45, contribución individual <=40%, DD cerrado <=2.000, MAE solapado proxy <=1.000, **riesgo conjunto minuto a minuto** (floating close/stress) y daily peak-to-trough **estrictamente inferior** a 1.000 y stress DD **estrictamente inferior** a 2.000. No se afirma certificación MFFU: solo estrés conservador M1, sin orden intraminuto real.
3. Exige `NQWalkForwardResultV15` con **4 folds train12/val6**, fechas exactas 2020–22, ≥3 validaciones positivas/gate pasando y misma identidad calculada `EXCANv19` del genoma elegido por cada fold. **El walk-forward de V20 mide la estabilidad del GENERADOR por ventana, no validación independiente del portafolio seleccionado sobre todo 2020–22.** Su verdadera prueba externa está reservada a 2023–24 y luego 2025–oct2026.
4. `NQNativeResearchRunnerV22.cs` integra la auditoría adicional **antes** de generar los `NQFrozenCandidateV16`, tomando **solo los candidatos efectivamente elegidos** por el selector V13/V15; ninguna estrategia no seleccionada, no canónica, duplicada o con fallas de G0/MC/anual/cronología puede entrar en el congelado. Reutiliza **`NQNativeBulkEconomicV21`**, ranking persistente y costos completos; luego V20 walk-forward y V16 frozen EXCANv19 OOS. El runner no genera portafolios ficticios para superar sus gates.

## Evidencia CI — prueba de controles

**[GitHub Actions V22 workflow](https://github.com/rgentil2/MES-Trading-Research/actions/workflows/nq-v22-risk-portfolio-qa.yml)**. Las dos suites en CI comprueban:

- **Aceptación de portafolios sintéticos de 3, 4 y 5 estrategias.** Datos OHLCV M1 controlados 2020–2022; **360 operaciones por estrategia (10 por cada uno de los 36 meses)**. Las 3 primeras entran simultáneamente; las estrategias 4 y 5 usan horarios escalonados para no exceder la exposición flotante conjunta. Todos los candidatos seleccionados conservan identidades `EXCANv19` diferentes; se verifica que sus PF, costos 1,5×, Monte Carlo 500 reordenamientos por bloques, anualidad y correlaciones pasan.
- **Caso positivo de tres**: máximo corr mensual ~0,087; mayor contribución ~33,5%; DD adverso M1 conjunto $1.200, pérdida intradiaria proxy $600; cuatro folds pasan.
- **14 verificaciones de rechazo dirigidas**, incluidas: 149 operaciones, un mes de 4 trades, PF <1,25 con neto positivo, neto negativo con frecuencia intacta, costos extra que anulan beneficio, bootstrap DD excedido, inconsistencia 3 años, genoma repetido con distintos IDs, dos estrategias clonadas en sus P&L mensuales, shock flotante que excede 2.000 aunque neto cerrado siga positivo, pérdida diaria demasiado alta para presupuesto, identidad falseada de ganador WF, menos de 3 candidatos, P&L de fill alterado.
- **Camino integral `NQNativeResearchRunnerV22` real sobre OHLCV sintético 36 meses**: GA V19/V21 con 22 simulaciones económicas completas, 10 auditorías V13, 5 aprobadas individualmente, pero selección **rechazada** por riesgo/diversidad, bloqueando walk-forward final y congelación. El módulo V20 walk-forward fue probado aparte con 4 folds / 88 genomas, sin filtración de futuro; el score journal V21 reaprovecha 22 genomas sin recalcular sus backtests.
- **Limitación explícita de prueba:** los resultados de los cuatro folds del **caso de aceptación del portafolio** se construyen deliberadamente en una fixture de QA para comprobar las puertas y las identidades, **no** proceden de un generador que haya descubierto un portafolio ganador. No se ha demostrado que una misma corrida de GA encuentre 3–5 estrategias que aprueben **TODOS** los filtros con un walk-forward auténtico, ni sobre datos reales ni sintéticos.
- Todos los datos/operaciones son **fabricados**, no se ha obtenido resultado real NQ DEC2026 ni P&L/PF/DD financiero creíble.

## Código y QA añadidos

- `research/nq/ninjatrader/NQNativePortfolioAuditV22.cs`
- `research/nq/ninjatrader/NQNativeResearchRunnerV22.cs`
- `research/nq/ninjatrader/tests/NQNativePortfolioAuditV22Test.cs`
- `research/nq/ninjatrader/tests/NQNativeFullFunnelV22Test.cs`
- `.github/workflows/nq-v22-risk-portfolio-qa.yml`

El archivo `NQ_PROJECT_MASTER.md` y la bitácora `NQ_RESEARCH_LOG.md` reflejan S0.83. Los módulos V6/V7/V13/V15/V19–V21 anteriores siguen conservados. No se han modificado reglas históricas para forzar aprobaciones.

## Qué falta realmente antes de la migración final

1. **V23**: medir la velocidad y memoria de backtests económicos M1 de longitud equivalente a 36 meses y escalar decenas de miles de genomas, registrando rechazos y resultados con la persistencia de V21, sin contaminar 2023+.
2. Una vez terminado V23, consolidar las PR apiladas y empaquetar los parámetros de la búsqueda, candidatos congelados, informes y reglas para **una sola integración y validación final** en NinjaTrader 8 / NQ DEC2026.
3. Aún no existen datos NQ reales en CI, ventaja estadística demostrada ni aprobación de fondeo. La verificación final deberá comparar operaciones y DD entre motor de investigación y Strategy Analyzer, con costos/órdenes equivalentes.
