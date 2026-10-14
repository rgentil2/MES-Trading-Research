# NQ Strategy Builder V2 — Gramática lógica, 96 candidatos NUEVOS (sin mezclar NinjaTrader)

**Fecha de preregistro:** 2026-10-14. **Rama aislada:** `exploratory/strategy-builder-50k-v1-20261014`.

## Qué se construyó y se probó

- **V1 sigue congelado en 48 candidatos**. V2 contiene **96 especificaciones inéditas dentro del Builder**: 16 mecanismos de entrada × 6 contextos de reglas causales `AND/OR` (2–3 indicadores adicionales). Total **144 candidatos V1+V2**. La biblioteca de investigaciones NQ anteriores supera ese número: los 144 NO son 144 oportunidades independientes ni la totalidad de tests previos.
- V2 utiliza las 17 familias de indicadores y la fuente NQ 1 minuto de V1; agrega 15 condiciones lógicas con dirección para EMA, MACD, VWAP, ATR, volumen, RSI, ADX, Bollinger squeeze, OBV, MFI y precio relativo al cuerpo de la vela. Cada expresión está en un árbol JSON restringido a `AND/OR/LEAF`, con **máximo 4 hojas y 3 niveles**, sin `eval`, código dinámico ni inspección de indicadores futuros.
- Contextos: `trend_volume`, `quiet_reversal`, `volume_direction`, `momentum_confirm`, `squeeze_release`, `vwap_moneyflow`. Cada contexto tiene SL basado en ATR entre 8 y 60 puntos, TP 1,5R o 2R y salida por tiempo 20–30 min. No se ajustan stops a posteriori.
- Mismo protocolo causal de primera entrada: señal al cierre de barra RTH 1m, entrada en **OPEN siguiente** entre aprox. 09:35 y 11:30 ET, 2 ticks adversos de entrada, modelo conservador de ejecución de stop (incluye riesgo de doble toque intrabar) y 1–5 MNQ proxy con riesgo previsto ≤US$250. **Los precios vienen de NQ, no de ejecuciones comprobadas de MNQ.** Cada candidata a lo sumo 1 operación/día.
- **Un evaluador compartido** `v2_router.py` ya permite armar una cartera con prioridades elegidas y congeladas por el investigador, sin posiciones simultáneas, 2 entradas máximas por sesión y referencia de pérdida de US$2.000 y objetivo US$3.000. No selecciona estrategias automáticamente mirando resultados y **no** reproduce las reglas oficiales de fondeo ni el trailing intradía real: sus drawdowns flotantes vienen de barras de un minuto y son una **aproximación**.
- **Multiplicidad**: al ejecutar con datos, V2 vuelve a calcular la cohorte V1 sobre la misma muestra para obtener un BH conjunto sobre **144 contrastes V1+V2**. El `q` propio de V2 (96) se conserva para diagnóstico, pero un candidato no sobrevive al gate si falla `q` de 144. **Las investigaciones NQ anteriores no están incluidas en este denominador**; los resultados siguen estrictamente EXPLORATORIOS.
- **Pruebas:** 20 tests sintéticos con datos artificiales, incluyendo preregistro inmutable, gramática limitada, indicadores causales, blackout 2025 y 2026, stop-first, siguiente vela, y cartera compartida. Ninguno utiliza históricos ni cuenta de trading.

## Partición temporal y aislamiento

| Bloque | Uso | Estado |
|---|---|---|
| 2020–2022 | Búsqueda/entrenamiento de reglas ya congeladas | Reutilizado, exploratorio |
| 2023–2024 | Comprobación temporal interna | Reutilizado, **no OOS realmente nuevo** |
| 2025 | Validación reservada; no abrir automáticamente | **SEALED** |
| 2026 | Completamente excluido del Builder y sus tests | **PROHIBIDO** |

El CSV y el código T05/T186/T215 del proyecto NinjaTrader NO son dependencias del Builder y no deben modificarse por los resultados de la V2.

## Cómo verificar V2 SIN datos de mercado

Clonar o abrir la rama exploratoria en tu PC, usar Python 3.11+ y dependencias `numpy`, `pandas`; ejecutar desde la raíz del repositorio:

```shell
python research/strategy_builder_50k/run_v2.py --freeze-only
python -m unittest discover -s research/strategy_builder_50k/tests -v
```

Debe indicar **96, SHA256 `fbd9695bdc592b9753441add612654daba8f290e6aaaeb1518bc1a2b1f7b15d0`**, sin abrir ningún histórico.

## Cómo ejecutar 2020–2024 (SOLO cuando esté disponible el ZIP ORIGINAL PRIVADO)

```shell
python research/strategy_builder_50k/run_v2.py --zip "C:\\RUTA_PRIVADA\\NQMNQ_Research_2020_2026.zip" --out "C:\\RUTA_PRIVADA\\NQBuilderV2_Resultados_2020_2024" --approve-reused-dev --bootstrap 1000
```

El script compara su registro inmutable con el archivo GitHub ANTES de leer precios, bloquea carpetas de salida ya existentes, importa `research.nq.nq_h05_h07_level_volume_screen.load_development` para abrir solo 25 miembros NQ **`development_2020_2024`**, comprueba **1.221 sesiones RTH** completas y ejecuta las dos cohortes (48+96) con denominador BH de 144. El proceso puede tardar. Nunca usar `--zip` apuntando a histórico distinto sin QC.

Archivos de salida privada:
- `registry_locked_before_data.json` (copia del registro antes de leer el ZIP)
- `report_V2_2020_2024.json` (96 métricas, gate, causa de fallo y `q` de 96/144)
- `summary_V2_96.csv` (tabla para clasificación/diagnóstico)

**Nota de seguridad de datos:** el ZIP original 2020–2026 puede contener archivos sellados 2025 y 2026; la función lectora tiene allowlist por **miembro ZIP exacto** y jamás abre esos contenidos. Un nombre de fichero ZIP visible no significa leer resultados fuera de muestra. No subir outputs ni históricos licenciados a GitHub público.

## Gate pendiente

No hay nuevo backtest sobre datos reales confirmado en este chat porque el ZIP privado auditado previamente **no está montado aquí**; **no se inventa un top 10 rentable**. El siguiente gate verdadero es ejecutar V1+V2 con el archivo original autorizado, comparar rutas de costes NQ/MNQ y congelar prioridades de cartera **antes** de evaluar el router sobre la comprobación interna. En todo caso 2025 sigue reservado hasta autorización separada.