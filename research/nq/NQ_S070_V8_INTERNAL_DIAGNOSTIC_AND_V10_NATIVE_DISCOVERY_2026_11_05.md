# NQ S0.70: diagnóstico interno V8 y descubrimiento nativo V10 (2026-11-05)

## Fuentes y alcance

- Entrada: `Texto pegado(9).txt` del usuario, 79 KB, logs NT8 V5+G0V7+V8 para el universo 2020–2022.
- Se analizaron 20 IDs distintos, deduplicando la repetición manual de `NQEX5_010D3F69BD586F67ABA39B85`. La generación previa había dado `executed=20 generatedUnique=20 attempted=23 failure=0`.
- Valores agregados de eventos de estrategia, **no 20 universos independientes** ni resultados de un portafolio: una misma barra puede ser evaluada por múltiples candidatos.
- No hay datos de ticks para establecer cronología intrabar. M1 bar-close no equivale al trailing DD certificado de MFFU.

## Diagnóstico de frecuencia (20 candidatos únicos)

| Año | Señales direccionales brutas | Bloqueadas por ATR | % ATR / señal | Bloqueadas por límite diario | Entradas previstas = trades completados |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2020 | 341,706 | 124,505 | 36.4% | 157,158 | 6,565 |
| 2021 | 341,061 | 134,562 | 39.5% | 152,511 | 6,529 |
| 2022 | 341,668 | 223,245 | 65.3% | 108,298 | 3,305 |

- La frecuencia agregada pasa de 6,529 (2021) a 3,305 (2022), caída del 49.4%.
- La proporción de señales brutas bloqueadas por ATR salta de 39.5% a 65.3%.
- La señal direccional bruta no desaparece (341,061 a 341,668). El mecanismo principal observable es el rechazo del cálculo/presupuesto asociado a las salidas ATR, no una escasez general de señales.
- **No todos los candidatos colapsan:** cinco candidatos tienen `blockedATR=0` y mantienen ~514–516 operaciones por año. No extrapolar el fenómeno a todos los modos de salida.
- Otros riesgos de atribución: cada fila de V8 marca la *primera* razón de bloqueo del embudo; no interpretar el número de `blockedATR` como causalidad experimental ni suma exclusiva de todas las condiciones económicas.

### Frecuencia mensual 2022 (20 candidatos)

| Mes | Operaciones agregadas | Candidatos con menos de 5 operaciones |
| --- | ---: | ---: |
| Ene | 231 | 15 |
| Feb | 222 | 15 |
| Mar | 230 | 15 |
| Abr | 210 | 15 |
| May | 246 | 15 |
| Jun | 269 | 15 |
| Jul | 324 | 2 |
| Ago | 288 | 10 |
| Sep | 266 | 14 |
| Oct | 221 | 15 |
| Nov | 430 | 2 |
| Dic | 368 | 2 |

La diversidad de salidas/periodos es necesaria. No eliminar o elevar límites sin estimar DD y resultados netos.

## Diagnóstico de riesgo V8 (marcado al cierre de M1)

| Año | Peor drawdown diario entre candidatos | Peor drawdown desde pico anual | Candidatos con DD diario > USD 1,000 |
| --- | ---: | ---: | ---: |
| 2020 | USD 1,395.00 | USD 19,156.52 | 6/20 |
| 2021 | USD 3,045.00 | USD 18,644.08 | 6/20 |
| 2022 | USD 1,016.52 | USD 19,214.88 | 1/20 |

Estos son indicadores retrospectivos a *cierre de minuto*, no trazas realistas de fills intrabar ni simulación certificada del trailing de cuenta MFFU.

## Resultado económico original V7

20/20 rechazos, PF < 1.25 en 20/20; 19/20 exceden USD 2,000 de drawdown cerrado y proxy estrés. 15/20 no satisfacen 5 operaciones por mes. 16/20 netos negativos. No utilizar como cartera o estrategias operables.

## Cambio S0.70: generador nativo sin depender de parámetros GUI fijos

Archivo: `research/nq/ninjatrader/NQNativeResearchOptimizerV10.cs`

- Preserva V5, V8 y V9; es un **optimizador nuevo** para Strategy Analyzer.
- Usa rangos internos explícitos para los 20 genes V5, aunque los 20 rangos visuales de Strategy Analyzer estén `Min=Max`.
- Valida que haya exactamente 20 genes elegidos, escribe y verifica el valor de cada `Parameter` **y** el de la estrategia antes de `RunIteration()`. Restaura valores en `finally`.
- Emplea `NQUniqueSearchV5`: semilla determinista, deduplicación canónica y rechazo de estructuras redundantes *antes* del backtest. **Es búsqueda aleatoria estructural, NO genética guiada por fitness ni el catálogo de 132 indicadores de StrategyQuant.**
- El criterio para ordenar resultados está separado: `NQNativeDiscoveryFitnessV9`. Es puntuación continua de descubrimiento, no G0.
- El filtro estricto G0 V7 permanece intacto y **solo** se usa después para comprobar candidatos supervivientes.
- `ExploreExits=true` varía stop/target fijos, modo ATR, periodo, múltiplos y máximo de entradas de 1–2. `false` conserva exactamente los 7 genes de salida/riesgo del baseline.
- Todos los backtests se ejecutan sobre las barras M1 cargadas en NinjaTrader, sin PowerShell, CSV externo, Python ni nuevas descargas.

### Guía de instalación en Windows NinjaTrader 8

1. Usar la instalación en la que ya compilan `NQNativeGeneticLabV5`, `NQNativeUniqueSearchV5`, `NQNativeExitCanonicalV5`, `NQNativeDiscoveryFitnessV9` y sus dependencias.
2. Copiar `NQNativeResearchOptimizerV10.cs` a `Documentos/NinjaTrader 8/bin/Custom/Optimizers/` (o crear en NinjaScript Editor > Optimizers), abrir NinjaScript Editor y compilar con **F5**. Si hay errores, no iniciar backtest; registrar salida exacta de compilación.
3. Strategy Analyzer > Optimization. Estrategia **NQNativeGeneticLabV5** para descubrir; instrumento NQ DEC26 merged Last, 1 Minute, misma zona horaria e historial de la validación previa, fechas 2020-01-01 a 2022-12-31, plantilla de comisiones y deslizamiento anteriores.
4. En los parámetros de optimización, seleccionar **los 20** genes de V5. Los valores `Min/Max` pueden ser iguales, porque V10 define internamente la exploración. Si no hay 20 seleccionados, se cancela y avisa, sin ejecutar.
5. Optimizer: **NQNativeResearchOptimizerV10**; Optimize on: **NQNativeDiscoveryFitnessV9**; Keep best results: 20 o 50.
6. Primera ejecución técnica: `UniqueCandidates=20`, `Seed=20261105`, `MaxAttempts=2000`, `ExploreExits=true`. Esperado *solo como contrato técnico*: 20 `NQ_V10 PRE_RUN` diferentes, `FINAL executed=20 failures=0`. Los resultados económicos no se predicen.
7. Si la prueba real pasa, se puede ampliar de forma controlada a 200–1,000 candidatos; luego auditar finalistas en V8 y G0V7, separar temporalmente los datos de desarrollo y mantener 2023–2026 fuera del entrenamiento.
8. **Nunca activar la estrategia de investigación en una cuenta live/prop.** V5 está programado para operar solo en `State.Historical`.

### Limitaciones y siguiente fase

El código nuevo está en rama de revisión, **no** se ha compilado todavía contra los ensamblados propietarios de NinjaTrader en Windows ni ejecutado un backtest real desde este entorno. La batería CI C# con shim incluye 1,000 genomas únicos, repetición determinista por semilla, 500 genomas con los siete genes de salidas congelados, verificación de variación real de modos de salida y restauración de parámetros, más fallo seguro ante parámetros faltantes o restricciones estrictas Min=Max. **El shim no sustituye la validación de la plataforma.** Un setter real de NT8 que obligue a respetar el Min/Max de la interfaz podría rechazar el rango interno; V10 se detiene entonces sin ejecutar silenciosamente estrategias incorrectas.

El catálogo actual V5 solo comprende 10 tipos de condición. Para aproximar de verdad la cobertura de StrategyQuant se requiere una siguiente versión de Strategy que incorpore los indicadores/transformaciones del catálogo (~132), árboles booleanos con varias jerarquías, optimización genética dependiente del score, walk-forward, Monte Carlo y construcción de cartera con control de correlación. No declarar el V10 como equivalente completo hasta completar esas fases.
