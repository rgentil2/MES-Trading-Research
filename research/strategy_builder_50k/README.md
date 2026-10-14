# NQ Strategy Builder 50K — exploración independiente V1

**Fecha de diseño: 14 de octubre de 2026.** Este laboratorio es **INDEPENDIENTE** de la migración congelada T05/T186/T215 a NinjaTrader 8. No importa sus parámetros, no modifica sus documentos de estrategia, no ejecuta órdenes y no abre sus ventanas reservadas. Crear un Builder nuevo no representa una confirmación de edge.

## Qué se implementó

- Fuente: reutiliza **el cargador auditado** `research/nq/nq_h05_h07_level_volume_screen.py` del repositorio. Exclusivamente los **25 archivos NQ 1-minute de `development_2020_2024`** del ZIP exportado originalmente desde NinjaTrader. 2025 sigue sellado y 2026 queda excluido por petición del usuario; el cargador lista nombres de holdout si es necesario, **nunca abre sus barras**.
- Auditoría de la fuente existente: **1.221 sesiones RTH completas 2020–2024** para el contrato trimestral seleccionado, 390 barras etiquetadas 09:31–16:00 hora de Nueva York (DST). Rollover original: jueves 8 días calendario antes del tercer viernes del trimestre, siempre un contrato por sesión. No unir contratos superpuestos ni rellenar minutos ausentes.
- 17 indicadores/factores calculados de OHLCV: **SMA, EMA, RSI, ATR, ADX, MACD, bandas Bollinger, estocástico, CCI, ROC, Donchian, Keltner, VWAP de sesión, OBV, MFI, Williams %R y volumen Z-score.** Features causales al cierre de cada vela, sin usar información posterior ni rellenar valores faltantes.
- Primera cohorte congelada: **16 mecanismos de entrada × 3 configuraciones de contexto y salida = 48 candidatas**. No se ajustan después de mirar beneficios; el código guarda `registry_frozen_before_prices.json` **antes de abrir el ZIP**. Registro de versión y SHA256 para las 48. Se pueden ampliar los operadores/indicadores en futuras cohortes registradas, no optimizar estas 48 adaptativamente.
- Backtest 1m conservador: señal al cierre de la vela → entrada al **OPEN de la siguiente**; solo señales entre 09:35 y 11:29 ET para entrar hasta las 11:30; 1 trade por día y por candidata, sin simultaneidad intradiaria; bracket SL/TP con colisión intrabar resuelta en contra (stop primero), gap through stop adverso, timeout y salida por hora, comisiones y slippage.
- **Sizing proxy en MNQ**: 1–5 contratos micro con riesgo nominal por operación hasta US$250, basado en el NQ 1m. **No** son fills históricos MNQ reales; antes de cualquier fondeo necesitamos fuente MNQ/tick y reconciliación. Comisión por micro **US$1,90 RT** y slippage 2 ticks adversos por lado, como **supuestos de investigación sujetos a actualización** (no costes garantizados MFFU).
- Referencia de cuenta nominal US$50k: objetivo US$3.000, cushion US$2.000, reporte de drawdown cerrado y MAE flotante adverso estimado, no simulación homologada de reglas de evaluación, noticias, trailing oficial, payout o consistency. El límite interno preventivo de DD flotante de pantalla es **US$1.600**, no un valor oficial. Esta primera cohorte **no** comparte capital entre candidatas: el siguiente módulo debe evaluar portfolios y el balance/correlación con la cuenta completa.
- Estadística: test semanal sign-flip unidireccional, bootstrap semanal IC90 de expectativa neta, BH `q` sobre las 48 pruebas de entrenamiento, PF, operaciones/mes, DD, rentabilidad anual, sensibilidad a un tick extra por lado. Es **exploratorio**: ya investigamos intensamente 2020–2024, por lo que 2023–2024 tampoco constituyen validación independiente genuina.

## Partición temporal comprometida

| Uso | Años | Permiso actual |
|---|---|---|
| Descubrimiento | 2020–2022 | Sí; ya reutilizados en investigaciones previas |
| Comprobación interna | 2023–2024 | Sí; tampoco es validación verdaderamente independiente |
| Validación final de una sola cohorte congelada | **2025** | **No abrir en V1**. Su apertura requerirá decisión y registro previo de especificaciones/candidatas |
| Año excluido del Builder | **2026** | **Nunca usar en esta investigación**, independientemente del avance de T05 en NinjaTrader |

**Nota:** la solicitud de usar datos 2020–2025 no obliga a gastar 2025 durante la generación. Lo conservamos para evaluar una sola vez las propuestas que sobrevivan. Si el usuario decide expresamente cambiar esa política, se registrará por anticipado y la evaluación ya no será un OOS virgen para el Builder ni para experimentos previos que lo reservaron.

## Primera cohorte (16 mecanismos)

1. Cruce EMA y filtro VWAP
2. Cruce SMA
3. RSI vuelve desde sobreventa/sobrecompra
4. Precio retorna al interior de bandas Bollinger
5. Cruce MACD y señal
6. Estocástico vuelve de extremos
7. CCI vuelve de ±100
8. Ruptura del canal Donchian de las 20 velas previas
9. Ruptura de Keltner
10. ROC cruza ±0,2%
11. Williams %R vuelve de extremos
12. ADX supera 22 con dirección EMA
13. MFI vuelve de sobrecompra/sobreventa
14. OBV cruza su media con confirmación EMA
15. Desviación extrema de VWAP a más de 1,2 ATR
16. Ruptura Donchian con anomalía de volumen

Para cada familia se ensayan exactamente: F1 filtro `volume_z>0,3`, SL 1 ATR, TP 1,5R, timeout 20m; F2 `ADX>20`, SL 1,5 ATR, TP 1,5R, timeout 30m; F3 régimen ATR% por debajo de su mediana pasada, SL 2 ATR, TP 2R, timeout 30m. Stop mínimo 8 puntos, máximo 60 puntos. Son combinaciones fijadas a priori **para el ejercicio exploratorio**, no recomendaciones optimizadas.

## Cómo ejecutarlo cuando esté disponible el ZIP privado en una computadora con el repo

**Nadie debe subir los históricos privados o outputs derivados con licencias a un repo público.** El archivo ZIP fuente ya fue usado en este proyecto, pero **no está disponible en el contenedor del asistente de esta conversación**, por lo que solo se han ejecutado pruebas técnicas sintéticas, no backtests reales ni resultados nuevos.

1. Descargar este proyecto como carpeta `research/strategy_builder_50k/` dentro del repositorio **solo en su rama exploratoria**.
2. Instalar Python 3.11+ y `numpy`, `pandas` según `requirements.txt`. Si ya están disponibles en tu ambiente, no reinstalarlos.
3. Localizar el **ZIP original privado** `NQMNQ_Research_2020_2026.zip` (o el equivalente ya auditado), sin extraer/abrir 2025/2026.
4. Desde el directorio raíz del repositorio, ejecutar:

```shell
python research/strategy_builder_50k/run_builder.py --zip "RUTA_PRIVADA_AL_ZIP" --out "RUTA_PRIVADA_NUEVA_A_RESULTADOS" --approve-reused-dev
```

Esto crea `registry_frozen_before_prices.json`, `report_DEV_2020_2024.json`, `candidate_summary_DEV.csv` y un CSV privado por candidata que haya operado. Rechaza sobreescribir resultados existentes o guardarlos dentro de GitHub. Ejecuta:

```shell
python -m unittest discover -s research/strategy_builder_50k/tests -v
```

Todas las tablas son de **INVESTIGACIÓN EXPLORATORIA REUTILIZADA, NO OPERABLE**. No conectar con SIM/fondeo ni modificar la migración NinjaScript por ningún resultado del Builder.

## Puertas antes de avanzar

- Gate de ingeniería: loader original, barras y contratos exactos, sin look-ahead, calendario y costes documentados, tests de entradas/salidas y gap/doble toque.
- Gate de exploración: entre cohortes, no rescatar variantes de una familia sin registrarlas como pruebas adicionales; supervisar denominador global de búsqueda acumulada. Nuestro BH de 48 **no corrige las numerosas familias NQ previas** y no debe presentarse como evidencia independiente.
- Gate económico provisional: ≥5 trades/mes sobre 2020–2024, N entrenamiento ≥90, PF≥1,25 entrenamiento y comprobación interna, DD flotante proxy <1.600, costes extra adversos y positividad de ambos años internos. Se presenta cada gate/rechazo, no solo el ranking de ganadoras.
- Gate de cuenta real: engine tick/fills, comisiones vigentes, balance único con cartera y correlación, noticias/consistencia/prohibiciones del plan MFFU elegido, protección contra drawdown intradía, OOS realmente independiente y validación prospectiva.

**Siguiente desarrollo:** tras auditar ejecución real del primer lote, optimizar cálculo de features multiactivo/por sesiones, crear árboles lógicos limitados y mutación genética con presupuestos de búsqueda **predefinidos**, filtros de duplicados/alta correlación y dashboard interactivo. No crear una fábrica de millones de combinaciones sin registrar multiplicidad.
