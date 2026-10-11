# NQ Minute Last independiente vs Tick Last — estado del puente, 2026-10-11

**Estado: CÓDIGO Y PRUEBAS LISTOS; COMPARACIÓN CON LA FUENTE INDEPENDIENTE BLOQUEADA POR AUSENCIA DEL ARCHIVO EN LA NUBE.**

El código original [NQMNQBulkMinuteExporter.cs](../ninjatrader/NQMNQBulkMinuteExporter.cs) exporta velas NinjaTrader `Minute Last` en formato UTC `yyyyMMdd HHmmss;Open;High;Low;Close;Volume`. La línea histórica NQ/MNQ H01–H78 (2020–2024) cargó un ZIP del usuario mediante `load_development(zip_path)` en `research/nq/nq_h05_h07_level_volume_screen.py`. GitHub MES conserva código e informes; no se confirmó disponibilidad del ZIP `NQMNQ_Research_2020_2026.zip` en la rama principal, otras ramas, Releases, archivos de proyecto/Biblioteca ni artefactos consultados de los Actions históricos. **Que se haya usado en Python no significa que el ZIP se haya subido al repositorio MES.**

## Trabajo realizado

- `qc_tick_to_minutes.py`: QC de cuatro días reales de NQ Tick Last (15-oct y 16-dic de 2025; 9-mar y 16-jun de 2026). En cada día: **240 de 240 minutos** y consistencia exacta entre barras de 1m/5m **creadas desde los MISMOS ticks**. [Run 38148506627](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38148506627). Esto NO compara contra las velas independientes.
- `compare_independent_nq_minutes.py`: nuevo comparador de `Open, High, Low, Close, Volume` y cobertura entre ticks Last y archivo de minutos distinto, con **exactitud por contrato**, horario America/New_York, convención de marca de minuto explícita (`end` o `start`) y salida exclusivamente agregada. Se descartan y se informan diferencias; no se toleran ni se ajustan silenciosamente.
- `test_compare_independent_nq_minutes.py` y workflow [nq-independent-minute-reconcile-tests.yml](../.github/workflows/nq-independent-minute-reconcile-tests.yml): **11/11 tests nuevos aprobados**, además de 10/10 tests de agregación tick y 13/13 del simulador sintético (total **34/34**), [run 38150302279](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38150302279). Sin descargas de datos privados en ese run.

## Restricciones y archivo requerido

La nueva rama de estudio permite **octubre-diciembre 2025, enero-abril 2026** como desarrollo y **mayo-junio 2026** como validación interna; **julio-septiembre 2026 sigue sellado**. Las investigaciones antiguas 2020–2024 conservan sus holdouts propios.

El comparador **NO abre ZIP anual ni archivos originales multi-día**, porque su contenido podría mezclar meses sellados. Exige un archivo de un solo día y exactamente un contrato, bajo esta estructura **privada** (no hacer commits de precios al repositorio MES público):

```
data/Tick_Last/NQ_12-25_2025_20251015_Tick_Last_ET0800_1200.txt
data/Minute_Last/NQ_12-25_2025_20251015_Minute_Last_ET0800_1200.txt
```

La serie Minute Last debe provenir de la exportación **independiente** de NinjaTrader, no de reconstruir a partir del mismo archivo Tick Last que se quiere auditar. Debe cubrir los 240 minutos ET 08:00–12:00 del día elegido. NinjaTrader BarsRequest suele etiquetar cada barra con su instante final; confirmar la convención en el origen, NO elegirla basándose en cuál opción ajusta mejor los precios.

Una vez se haya separado un día **sin cargar ni analizar otras fechas** y colocado en un espacio privado autorizado, ejecutar:

```bash
PYTHONPATH=local_nq_tick_2025_2026 python local_nq_tick_2025_2026/compare_independent_nq_minutes.py \
  --root data --day 2025-10-15 --minute-label end
```

El resultado publica solo: cobertura, diferencias por columna, desvíos máximos y estado `INDEPENDENT_MINUTE_MATCH` o `SOURCE_MISMATCH_OR_INCOMPLETE`; nunca precios ni barras individuales. Este comando solo se ejecuta con datos que el usuario haya puesto a disposición **fuera del repo público**.

**Próximo gate:** recuperar o conectar el ZIP fuente, aislar un día permitido sin exponer o abrir meses sellados, guardar las velas de 1m en almacenamiento privado y ejecutar por primera vez la comparación real. Si hay desajuste, comprobar etiquetado de barras, zona horaria/DST, volumen de proveedor y contrato sin alterar los resultados originales.

No se ha probado rentabilidad de las familias T01/T02/T03, ni un SLA de ejecución real, ni un forward test.
