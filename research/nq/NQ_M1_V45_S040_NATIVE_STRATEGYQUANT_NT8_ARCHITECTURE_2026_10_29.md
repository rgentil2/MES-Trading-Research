# S0.40 — NinjaTrader 8 como generador y evaluador nativo (tipo StrategyQuant)

**Decisión de arquitectura confirmada por el usuario: TODO dentro de NinjaTrader 8.** Python ya no es necesario para generar, calcular, simular ni evaluar esta nueva línea de trabajo. La cohorte histórica de 10.000 AST Python se conserva como archivo **separado**, sin asumir que esta campaña Nativa reproduce sus 10.000 códigos. Se abandona la propuesta anterior de emitir señales desde Python o de generar una estrategia distinta con Python.

## Sí, pero con una distinción importante

NinjaTrader 8 tiene *Strategy Analyzer*, optimización **Default (exhaustiva)** y **Genetic**, optimización multiobjetivo, walk-forward y extensiones de Optimizer/Optimization Fitness. Por defecto **optimiza los parámetros de una estrategia NinjaScript**, no inventa AST arbitrarios como StrategyQuant. Para conseguir estructuras variables hemos programado una **gramática de estrategia** codificada en los parámetros optimizables: tipo de señal A, período A, tipo B, período B, AND/OR, inversión, stop y objetivo. Al variar estos «genes», cada iteración evalúa una estructura de condiciones diferente, con todos los indicadores, señales, entradas y PnL calculados **dentro de NinjaTrader**.

Referencia oficial:
- https://docs.ninjatrader.com/ninjascript
- https://static.ninjatrader.com/support/helpGuides/nt8/optimize_a_strategy.htm
- https://docs.ninjatrader.com/ninjascript/optimizer
- https://docs.ninjatrader.com/ninjascript/oncalculateperformancevalue
- https://static.ninjatrader.com/support/helpGuides/nt8/walk_forward_optimize_a_strate.htm

## Archivos NinjaScript V1

- [NQNativeGeneticLabV1.cs](ninjatrader/NQNativeGeneticLabV1.cs): **Strategy** con diez tipos de señales codificados, dos ramas independientes (AND u OR), inversión, stops/targets en ticks, un solo NQ, máximo 2 entradas propuestas por día, ventana 09:35–11:27 ET, cierre antes de 11:29, y compuerta de pérdida diaria *cerrada* de investigación. NinjaTrader calcula nativamente RSI/CCI/SMA/EMA/WMA y sus combinaciones.
- [NQNativeResearchFitnessV1.cs](ninjatrader/NQNativeResearchFitnessV1.cs): objetivo opcional de **Optimization Fitness** que descarta por trade count <150, PF <1,25, neto ≤0 y DD **de trades cerrados** mayor a USD2.000, y clasifica los que quedan. No implementa DD flotante ni controles oficiales MFFU. Para utilizar esta fitness hay que probar su compilación y resultados en la versión instalada de NT8.

**Primera gramática, ampliable pero NO 132/132:**

| ID de gen de señal | Condición LONG vs SHORT |
|---|---|
| 0 | SMA(n) creciendo / cayendo |
| 1 | EMA(n) creciendo / cayendo |
| 2 | WMA(n) creciendo / cayendo |
| 3 | RSI(n) creciendo / cayendo |
| 4 | CCI(n) creciendo / cayendo |
| 5 | Close encima / debajo de SMA(n) |
| 6 | Close encima / debajo de EMA(n) |
| 7 | RSI(n) >55 / <45 |
| 8 | CCI(n) >100 / <-100 |
| 9 | Cruce SMA(n) vs EMA(2n) arriba / abajo |

Dos tipos diferentes A/B, sus períodos y AND/OR **sí generan distintas estructuras**, no solo optimizan el período de una misma regla. La gramática V1 aún no tiene árboles de 1–8 condiciones como la cohorte de Python, 132 indicadores, órdenes STOP/LIMIT, trailing, break-even, búsquedas recursivas por generaciones ni portafolio compartido. No se debe llamar versión final de StrategyQuant.

## Cómo instalar y hacer la primera prueba EN WINDOWS

1. Abrir **NinjaTrader 8 Desktop**, Control Center → New → NinjaScript Editor.
2. Crear o pegar **NQNativeGeneticLabV1.cs** como estrategia, con su nombre de clase y namespace sin cambios. Guardar y **Compile**. No se ha compilado desde GitHub; los errores que muestre el Editor se deben corregir antes de cualquier backtest.
3. Instalar **NQNativeResearchFitnessV1.cs** como tipo *Optimization Fitness* de NinjaScript, opcional en esta primera prueba. Recompilar. No confundir un gate de rendimiento como aval de fondeo.
4. Confirmar que el origen es **NQ Minute 1, Last**, Trading Hours **RTH**, reloj real en la aplicación **Eastern Time / New York**, y que el tramo seleccionado en **Strategy Analyzer solo incluye 2020-01-01 a 2022-12-30**. Verificar manualmente que el rollover de NQ siga la regla congelada (jueves 8 días antes del tercer viernes, medianoche NY): no dar por hecho que el contrato continuo automático lo replica. Nunca abrir 2023–26 en fase de descubrimiento.
5. Control Center → **New → Strategy Analyzer** → **Optimization** → escoger **NQNativeGeneticLabV1**. Seleccionar el **optimizer Genetic** para exploración aleatoria/evolutiva, o **Default** para barridos exhaustivos pequeños. Alternar `AType` de 0 a 9, `BType` de 0 a 9, períodos de 5 a 50 como primera prueba, `CombineMode` 0..1, `ReverseSignals` 0..1, `StopTicks` 8..55 y `TargetTicks` 0..120; mantener `MaxDailyEntrySubmissions` = 2. Así se varían **estructura y parámetros**.
6. Configurar comisiones de NQ, slippage y **Fill limit orders on touch=false** en Strategy Analyzer según el modelo elegido (en esta V1 solo hay entradas MARKET y salidas stop/target). Activar el objetivo de fitness personalizado si compila. Ejecutar primero un experimento pequeño, revisar Trades, calendario, señales, resultados, horarios y drawdowns, y **congelar genotipo+parámetros** de cada variante.
7. Solo tras comprobar resultados y equivalencia de horarios, ampliar iteraciones y robustez. **El Genetic estándar no garantiza 10.000 genotipos distintos ni árboles arbitrarios.** Si exigimos un presupuesto estricto de 10.000 estrategias únicas más generaciones, mutación/crossover sobre árboles de 1–8 condiciones, necesitaremos un **Custom Optimizer NinjaScript C#** usando `OnOptimize()`, `OptimizationParameters` y `RunIteration()`, junto al evaluador estructural C# dentro de la estrategia.

## Qué falta para llegar a un StrategyQuant completo

- Portar al motor **C# nativo** las 132 familias relevantes (cada una con su fuente, rangos, número de salidas, semántica y warmup), usando indicadores nativos NT8 cuando haya equivalencia documentada; implementar las fórmulas personalizadas dentro de NinjaScript. **No afirmar 132 hasta test de cada ruta.**
- Gramática AST C# genérica de 1–8 hojas por LONG/SHORT con AND/OR, operadores niveles/cross/lag, catálogos amplios de stop/TP y entradas pending STOP/LIMIT. La optimización genética estándar variará genotipos expuestos en parámetros; un Custom Optimizer será necesario para evolución estructural compleja y deduplicación/sello de 10K.
- Fitness con pruebas de estabilidad por año, ≥5 operaciones/mes, PF y DD compartidos, controles robustos de Monte Carlo, sensibilidad a slippage/comisiones y walk-forward; sin contaminación ISV 2023/24 ni 2025/26.
- Portfolio Builder que respete **una cuenta y un NQ compartidos**, prioridades, órdenes solapadas, pérdida máxima y drawdown flotante/trailing oficiales MFFU 50K. No sumar backtests de componentes independientes como un portafolio ejecutable.
- Comparar el backtest NinjaScript con el historial mismo NQ M1 y resolver posibles diferencias en fills Standard M1, intrabar stops y datos. Para uso en fondeo se precisa validación por el usuario en NT8 Windows.

## Límites de la primera versión — importantes

Esta V1 ofrece **código fuente experimental, no un optimizador ya compilado ni una estrategia de fondeo**. El código no se ha ejecutado en NinjaTrader 8 desde este entorno. El reloj `Time[0]` depende de la zona horaria que tenga NT8; no realiza conversión implícita a Nueva York. La orden de cierre se emite **a las 11:28 al cerrar la vela**, normalmente próxima apertura 11:29, un escenario conservador *diferente* de la política final de flat al cerrar 11:29. El warmup es solo intrasesión y se descartan períodos que no alcancen a completarse antes de 11:27; por ello algunos genotipos tendrán cero operaciones. Stop $300 y pausa diaria $600 son referencias de investigación, no reglas compradas MFFU verificadas. El DD de fitness es **cerrado**, no el DD flotante de cuenta. No hay pruebas 2023–26 ni selecciones reales.

**Estado de autorizaciones anteriores:** 13 controles de calidad de la línea Python histórica siguen 0/13. Este prototipo nativo inicia una nueva vía experimental; no se los declara aprobados ni se elimina la exigencia de validación real de la cartera completa en NinjaTrader 8.
