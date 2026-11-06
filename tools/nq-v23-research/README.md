# V23 — Generador NQ completo, autónomo y reproducible (sin ejecución de órdenes)

**Objetivo fijo V23:** un único ejecutor configurable que genera y evalúa estrategias, guarda y reanuda candidatos, aplica los filtros V22, produce rankings e informes auditables por operación, mes, año, riesgo, descartes y portafolio, y consolida los módulos V11–V23 en una compilación reproducible. **V24** es exclusivamente escalamiento de backtests de largo horizonte; **V25** es la única integración/validación final con NinjaTrader 8. Consulta [contrato de versiones](../../research/nq/NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md).

## Arquitectura

El proyecto `NQResearchV23.csproj` incluye **explícitamente 42 archivos C#** de la investigación NQ V11–V23. No usa paquetes NuGet externos ni requiere que NinjaTrader esté abierto o instalado. Se compila en .NET 8 y no puede emitir órdenes al broker. El punto de entrada `NQNativeV23Console.cs` ejecuta una única campaña `NQNativeCompleteGeneratorV23.Run`, que llama al motor ya comprobado `NQNativeResearchRunnerV22.Run`. No crea otra búsqueda/GA, no cambia las 120 fórmulas ni los 1.320 tipos y no reordena el embudo.

El archivo `campaign.lock` contiene el SHA del archivo de origen registrado y un **SHA adicional del contenido real de cada barra M1**, versión, configuración completa y reglas del evaluador. Si cambian la fuente o cualquier parámetro, una continuación sobre la misma carpeta se bloquea. La bitácora de resultados `economics_ledger.tsv` reutiliza los scores V21 y mantiene un checksum por fila. Los informes se exportan con orden determinista, sin métricas volátiles en su contenido; `artifacts.sha256` permite detectar cualquier manipulación.

## Comandos de la herramienta (disponibles para cuando se valide el conjunto de investigación completo)

El usuario decidió NO hacer compilaciones/exportaciones/backtests intermedios en NinjaTrader. Los comandos se documentan para la **ejecución futura** del paquete offline; no se solicita acción ahora.

```powershell
dotnet build tools/nq-v23-research/NQResearchV23.csproj -c Release
dotnet run --project tools/nq-v23-research/NQResearchV23.csproj -- --write-example research-config.json
# Solo cuando el conjunto histórico de desarrollo se haya puesto a disposición de la herramienta:
dotnet run --project tools/nq-v23-research/NQResearchV23.csproj -- --run research-config.json
dotnet run --project tools/nq-v23-research/NQResearchV23.csproj -- --verify NQ_V23_RESEARCH_REPORTS
```

El ejecutor offline acepta el formato de importación V16 ya documentado: **NinjaTrader 8 LAST M1** con hora UTC del final de cada barra en `yyyyMMdd HHmmss;open;high;low;close;volume`, conversión a Eastern/New York y reloj de barra completada. Se reserva la validación nativa del **NQ DEC2026** al final de V25; el contrato de futuros fue confirmado disponible por el usuario y no se impone una auditoría separada de rollovers.

El JSON generado por `--write-example` trae la configuración base, las 20 posiciones genéticas y todos los bloques de parámetros `Research.Genetic`, `Robustness`, `Portfolio`, `AccountRisk`, `WalkForward` y `Audit`. Incluye controles de protección: mínimo 1,5× costos, Monte Carlo P95 DD ≤ $2.000, tres años de estabilidad, DD cuenta ≤ $2.000, pérdida diaria/concurrente ≤ $1.000, correlación ≤ 0,45, concentración ≤ 0,40, 3–5 estrategias y corte fijo 2026-11-01 para la muestra final.

## Salidas de una única ejecución

| Archivo | Contenido |
|:--|:--|
| `economics_ledger.tsv` | Todos los genomas únicos puntuados, con score, net USD, PF, DD cerrado, operaciones, salidas y SHA por fila |
| `candidates_full.tsv` | **Todos** los genomas generados, ranking, score, identidad EXCANv19, métricas, 20 genes, estado y motivo de descarte |
| `rejected_candidates.tsv` | Por qué un genoma no se congeló, incluso si quedó fuera del límite de auditoría G0 |
| `robustness_audits.tsv` | G0, costo estresado 1,5×, Monte Carlo, pérdida de actividad mensual y razón específica de rechazo |
| `annual_development.tsv` | Operaciones, neto, PF y DD por año **2020, 2021 y 2022**, para cada candidato revisado por robustez |
| `monthly_development.tsv` | Los 36 meses de cada candidato revisado y comprobación ≥5 operaciones |
| `audited_trades.tsv` | **Todas las operaciones de candidatos auditados**: timestamps Eastern, posición, precio, fees, neto y MAE/MFE |
| `ranking_top.tsv`, `finalist_trades.tsv` | Ranking compacto V21 y recibos revisados nuevamente de los N mejores |
| `portfolio_decision.tsv` | Resultado global, integrantes, beneficio conjunto, correlación/concentración y DD flotante/día/concurrencia |
| `walkforward.tsv` | Folds train-only 2020–22 y métricas del ganador; **solo** se ejecuta si el portafolio previo pasó |
| `definitive_parameters.tsv` | **Únicamente si se congelaron candidatos aprobados**: 20 genes por estrategia, fórmula de señal y salida; si no hay portafolio, queda solo la cabecera, sin inventar parámetros |
| `settings_snapshot.tsv` | Parámetros fuente, selección, riesgos, genes basales y versión |
| `campaign.lock`, `run_summary.txt`, `artifacts.sha256` | Huellas de datos/configuración, resumen no-promocional, hashes de todos los artefactos |

## Evidencia de pruebas

GitHub Actions compila el ejecutor autónomo y ejecuta `NQNativeCompleteGeneratorV23Test.cs` y el test histórico de regresión V22, todos **con barras M1 sintéticas**:

- **22 candidatos** realmente puntuados por V12/V9 en el fixture 2020–22, **10 auditados**, **5** pasaron individualmente, pero **el portafolio quedó rechazado**, correctamente, sin generar parámetros definitivos falsos.
- El expediente contiene **22 filas de ranking**, **22 descartes**, **360 perfiles mensuales** y **30 perfiles anuales** de los diez auditados, además de sus recibos M1 por operación y 16 archivos con checksum.
- Segunda corrida idéntica: **0 nuevos backtests económicos** y **SHA256 idéntico del paquete**.
- Cambiar parámetros, el contenido de una barra aun usando el mismo SHA declarado de fuente, o adulterar un informe, hace fallar las verificaciones.
- Una **fixture separada** verifica la serialización de **3 y 5 estrategias congeladas artificiales** (60 y 100 genes respectivamente) sin presentarlas como ganadoras reales. Regresión V22 independiente sigue aprobada.
- **No se ha corrido el NQ DEC2026 real ni abierto las muestras externas 2023–24/2025–26** en esas pruebas. No se ha demostrado encontrar un portafolio rentable con un GA auténtico de principio a fin; no confundir prueba de gates con aprobación fondeada.

**Límite de reporte:** el ranking económico cubre todos los genomas GA. Las series de operaciones y resultados por mes/año cubren **todos los candidatos efectivamente auditados por G0** (configurable hasta 10.000); no se recalcula una historia completa de operaciones para los genomas deliberadamente fuera del shortlist. Esta diferencia se marca explícitamente en los TSV.

**Consolidación:** la versión V23 usa una lista explícita de 42 módulos y un PR acumulado a `main`; su árbol Git/commit y el lock de fuente/configuración permiten reconstruir el mismo software. Un PR abierto no implica por sí mismo que se haya fusionado a `main`. V24 parte de este alcance, sin rebautizar V23.
