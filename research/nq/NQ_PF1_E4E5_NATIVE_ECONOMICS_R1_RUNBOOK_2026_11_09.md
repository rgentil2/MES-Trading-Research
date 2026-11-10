# NQ PF1 E4+E5 R1 — ejecución central y filtros económicos en Strategy Analyzer

**Contrato INMUTABLE:** [NQ PF1 v1.0.0](NQ_PORTFOLIO_FUNNEL_PF1_CONTRACT_2026_11_09.md), [121 reglas JSON](NQ_PORTFOLIO_FUNNEL_PF1_RULES_2026_11_09.json). **Fecha:** 2026-11-09. **Estado:** implementación NinjaScript preparada / **pendiente de compilación F5 y backtest real del usuario**. NO autorizada para operar, ni superar E6/7/8/9.

## Evidencia que motivó la entrega

El usuario confirmó el funcionamiento del E4 R1 desde **NinjaTrader 8 → Strategy Analyzer**, con resultado:

```text
PF1_E4_END status=REPLAY_DIAGNOSTIC_ONLY portfolios=3 uniqueMembers=12 validBars=160770 excludedDays=9 OOS=LOCKED readyToTrade=false
```

Se ejecutaron **12/12 flujos de intenciones de estrategia** sobre 3 portafolios preliminares. Es un replay M1, NO una validación de fills nativos, y esos 9 días excluidos requerían detalle de causa.

## Siguiente entrega compacta de instalación

**ZIP:** `NQ_PF1_E4E5_ANALYZER_CMD_R1_20261109.zip`. **SHA-256 del ZIP:** `4a807cdfad75912ed9863ee84421f6586758b47213727e1e11e18bf4e7997e9e`. **SHA-256 del C# incluido:** `841c130c97d599d5cdf998210d9a2ebd4a5e50283492c792a53585a0610cd3dd`. El ZIP se entrega en la conversación y no se añade al repositorio en este PR; no afirmar lo contrario.

**Cuatro archivos:** `NQ_PF1_CentralExecutor.cs` (misma clase/archivo instalado E4, ahora extendido), `INSTALAR_NQ_PF1_E4E5.cmd`, `INSTALAR_NQ_PF1_E4E5.js`, `LEEME_NQ_PF1_E4E5.txt`. El CMD **solo instala** el C#, crea copia de seguridad de la versión anterior, no corre backtests ni modifica R2 `NQ_PF1_Analyzer`. La única ejecución sigue siendo dentro de NinjaTrader.

**Instalación:** descomprimir → doble clic `INSTALAR_NQ_PF1_E4E5.cmd` → NinjaScript Editor **F5** → New → Strategy Analyzer → Backtest → `NQ_PF1_CentralExecutor`.

**Parámetros iguales a E4:** NQ DEC26, Last, M1, **01/01/2020–31/12/2022**, trading hours **CME US Index Futures ETH**, zona horaria New York/ET, `ArmResearch=true`, `ConfirmDevelopmentM1ET=true`, `ProposalsPerSize=1` primero, rutas en blanco para autobúsqueda. **No** hacer Optimization ni abrir OOS para esta entrega.

## Qué añade E5, sin cambiar criterios del contrato

Se calcula todo a partir de las **operaciones ejecutadas por el simulador central de máximo un contrato NQ**, con entradas al minuto siguiente y costos totales base US$24,68 por trade. Las operaciones de cada integrante independiente se usan solo para estimar la **correlación mensual** de la etapa de diversificación; **nunca se suman sus beneficios como P&L del portafolio**.

| Filtro / magnitud | Exigencia PF1 |
|---|---:|
| Beneficio neto de portafolio | >US$0 |
| Profit Factor neto | ≥1,25 |
| Operaciones portafolio | ≥150 |
| Operaciones en cada uno de 36 meses IS | ≥5 |
| **Stability** de equity neta diaria con pendiente OLS positiva | **>30%** |
| **Symmetry** de P&L neto Long/Short del ejecutor | **>30%** |
| Drawdown cerrado (picos de P&L realizado) | ≤US$2.000 |
| Drawdown adverso M1 | ≤US$2.000 |
| Peor pérdida diaria M1 | ≤US$1.000 |
| Máxima excursión adversa simultánea M1 | ≤US$1.000 |
| Beneficio neto con costos 1,5× | >US$0 |
| Años positivos con PF anual ≥1,00 | 3/3 |
| Correlación mensual positiva máxima entre integrantes | ≤0,45 |
| Concentración en ganancias brutas ejecutadas por miembro | ≤40% |

**Fórmula Stability:** `100*R²` de regresión OLS de la equity neta al cierre de cada día elegible (incluidos días con 0 operaciones), solo si pendiente es positiva; si pendiente no positiva, 0; si varianza/muestra insuficientes, `UNDEFINED → FAIL`. Es métrica propia, **no** equivalencia demostrada con la propietaria de StrategyQuant.

**Fórmula Symmetry:** si beneficio neto de operaciones Long `L>0` y Short `S>0`, `100*min(L,S)/max(L,S)`; si no, 0. Se exige **estrictamente mayor** que 30 en ambas.

**Costos:** 2 ticks desfavorables en entrada +2 en salida + US$4,68 RT = US$24,68. Estrés 1,5× equivale a US$37,02: para operaciones netas de costo base agregar **solo US$12,34**, evitando doble contabilización.

**Corrección E4 no normativa:** el DD de operaciones cerradas ya no emplea el máximo de equity flotante; se separó de la curva mark-to-market adversa M1. Este ajuste evita usar un campo de riesgo con significado incorrecto, sin alterar el límite de US$2.000.

**Control de datos:** los días descartados por barras incompletas quedan detallados por **fecha y motivo**, en lugar de informar solo un número. La correlación mensual de E3 se calcula a partir de simulaciones individuales alineadas por los 36 meses IS, sin atribuirlas a la cuenta compartida.

## Reportes de NinjaTrader automáticos

Se generan en `NQ_NativeResearchResults`:
- `NQ_PF1_E4E5_*_TRADES.tsv`: recibos por portafolio y orden, P&L neto, equity.
- `NQ_PF1_E4E5_*_E5_AUDIT.tsv`: métricas, `IS_FILTERS_REJECT` o `IS_FILTERS_PASS_PROVISIONAL_MC_PENDING`, causas precisas.
- `NQ_PF1_E4E5_*_MONTHLY.tsv`: todas las 36 ventanas mensuales por portafolio.
- `NQ_PF1_E4E5_*_ANNUAL.tsv`: 2020, 2021, 2022 y PF anual.
- `NQ_PF1_E4E5_*_EXCLUDED_DAYS.tsv`: fechas excluidas y causas observadas.
- `NQ_PF1_E4E5_*_SUMMARY.txt`: SHA, datos, umbrales, archivos, bloqueo OOS y limitaciones.

### Mensajes esperados

```text
PF1_E4_BEGIN build=PF1_E4E5_NATIVE_CENTRAL_ONE_NQ_20261110_R1 ... OOS=LOCKED liveOrders=0
PF1_E4E5_SIGNALS member=... complete=...
PF1_E5_RESULT portfolio=... trades=... PF=... stability=... symmetry=... net=... verdict=IS_FILTERS_REJECT reasons=...
PF1_E4E5_END status=IS_AUDITED_MC_PENDING portfolios=3 ... OOS=LOCKED readyToTrade=false report=...
```

No predecir aprobación ni rentabilidad: son **valores aún no medidos en NinjaTrader** para este código. `PASS_PROVISIONAL` es solo resultado IS E5; **Monte Carlo E6, paridad nativa de barras/órdenes E7 y OOS E8 siguen pendientes**. La pestaña Trades de Strategy Analyzer puede mostrar **0 órdenes nativas**, porque el motor hace replay M1 dentro del script, no emite `EnterLong/EnterShort`. Los límites de riesgo M1 no garantizan protección real intrabar.

## QA realizada / NO realizada

- QA estática del código: contrato, OOS bloqueado, costos 1.0× y 1.5×, sin órdenes de broker, salidas por portafolio, contabilidad mensual/anual, estructura e instalador.
- Pruebas aritméticas con muestras controladas para Stability, Symmetry, riesgo 35 vs 36 ticks y costo estresado; sintaxis del instalador JS verificada.
- **No** se compiló contra NinjaTrader 8 real ni se ejecutó Strategy Analyzer con este R1 desde el entorno de desarrollo. **No** se declaró aprobación de portafolios, Monte Carlo ni OOS.

## Política de identidad

**NQ PF1 E4+E5 R1 NO es V26 ni redefine V22–V25.** El contrato congelado [v1.0.0](NQ_PORTFOLIO_FUNNEL_PF1_CONTRACT_2026_11_09.md), las 121 reglas y los periodos IS/OOS permanecen inalterados. Un cambio futuro de umbral exige aprobación explícita del usuario y una nueva versión documentada del contrato; corregir un bug del ejecutor se registra con ID propio y pruebas, sin mezclar objetivos antiguos.
