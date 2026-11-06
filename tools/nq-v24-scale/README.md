# V24 — Escalamiento de backtests económicos completos NQ (objetivo fijo)

**No renumerar:** V23 = generador completo, informes finales y consolidación de PR (fusionado en `main` por #82). **V24 = benchmarking, memoria y escalamiento de backtests económicos M1 de 36 meses**. V25 = una sola integración/validación final NinjaTrader 8 con `NQ DEC2026`. Ver [contrato fijo](../../research/nq/NQ_FIXED_VERSION_SCOPE_V19_V25_2026_11_06.md).

V24 reutiliza las **mismas 42 fuentes C# del ejecutor V23** y añade solamente tres módulos de escalamiento: `NQNativePreparedEconomicV24`, `NQNativeEconomicScaleV24` y `NQNativeSynthetic36V24`. Se compilan en un `.csproj` explícito, sin NinjaTrader ni órdenes.

## Cómo funciona

Un candidato tiene exactamente los **20 genes EXCANv19** de 120 fórmulas/1.320 condiciones. Primero prepara las tablas numéricas (familia × periodo) para sus hojas efectivas, respetando los primeros 396 tipos heredados V11/V18. Después el **mismo bucle conservador V12 de M1** produce entradas, stops, targets, SL-prioritario ante ambigüedad intrabar, fees, slippage, net USD, PF, DD, MAE/MFE, y score V9. Se escribe una fila SHA por genoma económico en el diario V21, con fingerprint adicional de V24. La GA V12 se repite con la misma semilla y puede reanudar con **0 nuevos backtests** para genomas ya puntuados.

El perfil informa backtests completos nuevos/segundo, millones de **barras RTH procesadas** por segundo, tablas nuevas/reutilizadas/expulsadas, bytes del payload de cachés, heap final y máximo aproximado de memoria del proceso. **No** equivale a monitoreo exacto de toda la memoria ni sirve como predicción lineal de una búsqueda 100k.

## Comandos (para uso futuro cuando corresponda)

```powershell
dotnet build tools/nq-v24-scale/NQResearchV24.csproj -c Release

# PERFIL SINTÉTICO REPRODUCIBLE, 36 meses completos (no es NQ de mercado):
dotnet run --project tools/nq-v24-scale/NQResearchV24.csproj -- --bench-synthetic36 ./v24_demo_1k 200 6 512 256

# Escala más grande, solo si se dispone del tiempo/RAM necesarios:
dotnet run --project tools/nq-v24-scale/NQResearchV24.csproj -- --bench-synthetic36 ./v24_demo_10k 600 19 512 256

# Entrada de investigación de desarrollo 2020–22, cuando esté autorizada
# la fuente real y terminada la construcción del sistema:
dotnet run --project tools/nq-v24-scale/NQResearchV24.csproj -- --run-development ./research-config.json
```

Los últimos dos números del modo sintético indican **MiB de caché numérica y de señales heredadas**, respectivamente. No son límites de memoria total. El directorio contiene `v24_economics_ledger.tsv` (SHA por fila, todos los genomas puntuados), `v24_top_ranking.tsv` y `v24_scale_profile.tsv` (tiempos y memoria del último run). Se recomienda separar rutas de distintos escenarios para no mezclar fingerprints. En el modo `--run-development` el programa usa una subcarpeta propia bajo el directorio de resultados V23, sin alterar sus 16 artefactos firmados.

La configuración base V23 con su semilla, tamaños de población, costes y parámetros sigue siendo la fuente declarativa. V24 **no** modifica reglas G0, portafolio, walk-forward ni holdouts; **nunca** acepta dataset 2023–24/2025–26 como material de optimización.

## Evidencias

[Reporte S0.85](../../research/nq/NQ_S085_V24_LONG_HORIZON_ECONOMIC_SCALE_2026_11_06.md).

- [CI de longitud real: 36 meses sintéticos y paridad V12](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42292796604): 783 sesiones, 164.430 barras M1, 66 simulaciones económicas completas, cinco genomas/5.275 operaciones **idénticas** entre V21 y V24; 0 nuevas en replay.
- [CI de 1.120 y 10.500](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42293251090): etapa 1.120 verificada, 56,065 s, 19,9766 backtests/s, 520 MiB pico proceso, 0 nuevas en segundo run. **No atribuir éxito a etapa 10.500 si aún no hay conclusión SUCCESS.**
- [Prueba de capacidad 100.700](https://github.com/rgentil2/MES-Trading-Research/actions/runs/42293746661): se ejecuta íntegramente con el simulador económico de M1 sobre fuente sintética de 36 meses, no con oráculo. **No afirmar éxito antes de verificar el run y 100.701 filas de ledger + 0 nuevas al repetir.**

**No son datos reales de NQ DEC2026**. El usuario ya ve su M1 2020–22 en NinjaTrader y ha pedido **UNA sola integración/validación final V25**. No solicitamos exportaciones nuevas, F5 ni auditorías de contratos/rollovers como trabajo intermedio. Hasta V25 no habrá paridad nativa de fills; hasta investigar datos reales no existe evidencia de portafolio rentable ni cumplimiento MFFU.
