# ES 1min Strategy Builder 50K — resultados de transferencia V1/V2 congeladas

**Ejecutado 2026-10-14 en GitHub Actions** [run 38654961549](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38654961549). **Solo estudio exploratorio**, sin nuevas hipótesis tras revisar ganancias, sin MES real ni NinjaTrader T05/T186/T215. Todas las reglas son las 144 configuraciones congeladas previamente para NQ, transportadas a ES sin adaptar sus parámetros. Los beneficios se simulan sobre **MES (5 USD/punto, tarifa $1.90 RT, 2 ticks de slippage adverso por lado, 1–5 contratos, referencia USD250/trade)**. No inferir validez de fondeo.

## Fuente / cobertura / protección temporal

- Origen: archivos ES 1min Last trimestrales ya registrados en **Git LFS** del repositorio, fuente 2020–2024 exclusiva.
- **20 contratos** DEV SHA256, byte length y row-count validados según `data_es_staging/manifests/ES_MINUTE_LAST_MANIFEST.csv`.
- **1.748.293 barras cargadas** tras retirar **70.829 filas solapadas**; 491.057 barras dentro de RTH; **1.220 sesiones completas** de 390 barras, 201 sesiones no completas descartadas.
- 2025 **sellado** (ningún fichero de contenido cargado); 2026 completamente excluido. Retest original ES y nuevo Builder son `REUSED DEV`, nunca OOS.
- Ventana de descubrimiento 2020–22; ventana temporal interna 2023–24, **ambas ya reutilizadas**. Los resultados son de modelación conservadora OHLC 1m con stop primero en barras ambiguas y no certifican secuencia tick.

## Resultado completo del embudo

| Métrica | Cohorte V1 | Cohorte V2 | Total |
|---|---:|---:|---:|
| Hipótesis registradas | 48 | 96 | **144** |
| Que generaron operaciones | 48 | 92 | **140** |
| Con beneficio acumulado positivo 2020–2024 | 0 | 0 | **0** |
| Con beneficio en entrenamiento 2020–2022 | 0 | 3 | 3 |
| Con beneficio en comprobación interna 2023–2024 | 0 | 3 | 3 |
| Con beneficio en ambos subperíodos | 0 | 0 | 0 |
| Superan todos los gates | 0 | 0 | **0** |

- Todos los contrastes tienen **BH `q_144=1.0`**. No hay una candidata seleccionable con evidencia robusta bajo estos parámetros y costes.
- El resultado menos negativo entre candidatas con más de 90 operaciones es V2 **SB2-03-5**, 111 trades, neto -$120.10, PF 0.984; beneficio +$182.65 en entrenamiento y -$302.75 en comprobación interna. **No se recomienda ni reoptimiza**: se presenta solo como diagnóstico de cercanía al punto de equilibrio.
- Los 144 resultados completos se guardaron en el artifact oficial (`ES_BUILDER_REPORT.json`, `ES_BUILDER_ALL144.csv`, `ES_TRANSPORT_PRECOMMIT.json`), además de la tabla CSV versionada en esta rama exploratoria.

**Decisión:** esta cohorte transportada de NQ a ES se CIERRA como NO SOPORTADA, sin mirar 2025/2026 ni rescatar configuraciones alterando parámetros. Una posible nueva cohorte ES, con mecanismos propios y límites económicos preregistrados, sería un **nuevo experimento exploratorio** sujeto a corrección por la búsqueda acumulada; no constituye un retoque de las mismas 144 estrategias. Como ES funcionó y sus resultados son válidos para el diagnóstico, no hace falta usar el fallback NQ Tick de otra ventana temporal (NQ Tick disponible principalmente Oct2025–2026, incompatible con 'excluir 2026' y mantener 2025 reservado).

No se tocó la transferencia NinjaTrader activa ni se fusionó la rama experimental con `main`.