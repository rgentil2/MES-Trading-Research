# MES Market State V1 — auditoría descriptiva 2020–2024

Motor separado de R063. Sin estrategias, retornos futuros ni aprobación para operar.

Filas de minuto utilizadas: 1,738,188. Archivos abiertos: 20 contratos de 2020–2024.
Fechas laborables: 1294. Episodios observados: 484.

| Estado | Fechas | Episodios | Mediana duración observada |
|---|---:|---:|---:|
| R0 | 913 | 358 | 1.0 |
| R1 | 63 | 22 | 3.0 |
| R2 | 65 | 20 | 3.0 |
| R3 | 124 | 43 | 2.0 |
| R4 | 129 | 41 | 3.0 |

R1: High/Directional; R2: High/Chop; R3: Low/Directional; R4: Low/Chop.
High/Low y Directional/Chop retienen el estado previo dentro de P33–P67.
Los episodios no se consideran réplicas independientes y sus duraciones finales son retrospectivas.

## Motivos de R0

| Motivo | Fechas |
|---|---:|
| UNKNOWN_CONTRACT_WARMUP | 228 |
| UNKNOWN_PREVIOUS_RTH | 169 |
| TRANSITION_CUSUM_ALERT | 163 |
| UNKNOWN_BAND_OR_DEGENERATE_REFERENCE | 153 |
| UNKNOWN_REFERENCE_WARMUP | 150 |
| UNKNOWN_OVERNIGHT_COVERAGE | 32 |
| UNKNOWN_NO_OVERNIGHT | 18 |

## Cobertura anual

| Año | Fechas laborables | R1–R4 | R0 |
|---|---:|---:|---:|
| 2020 | 262 | 0 | 262 |
| 2021 | 261 | 121 | 140 |
| 2022 | 260 | 86 | 174 |
| 2023 | 260 | 92 | 168 |
| 2024 | 251 | 82 | 169 |

## Transiciones empíricas dentro del mismo contrato

| Desde / hacia | R0 | R1 | R2 | R3 | R4 |
|---|---:|---:|---:|---:|---:|
| R0 | 90.3% | 1.9% | 1.0% | 3.8% | 3.0% |
| R1 | 19.4% | 66.1% | 14.5% | 0.0% | 0.0% |
| R2 | 18.0% | 8.2% | 73.8% | 0.0% | 0.0% |
| R3 | 19.3% | 0.0% | 0.0% | 68.1% | 12.6% |
| R4 | 20.6% | 0.0% | 1.6% | 7.9% | 69.8% |

Alertas CUSUM: 49. Los umbrales no se ajustaron después de ver la cobertura.
CUSUM no prueba rupturas estructurales; no tiene tasa de falsas alarmas calibrada ni P(Change).

## Verificación y límites

- Pruebas de invariancia por prefijo y modificación de datos futuros; aislamiento de contrato y exclusión de 2025/2026.
- Archivo causal separado de episodios y duraciones finales. Matriz descriptiva; no pronóstico validado.
- Calendario de días laborables, no calendario CME certificado. R0 incluye festivos, cobertura incompleta e inicialización.
- Rollover heredado de extremos de exportación NinjaTrader. No se ha certificado una selección de contrato en vivo.
- Gap preapertura es un proxy; POC/VAH/VAL exactos, HMM, BOCPD, Bai–Perron y ciclos quedan pendientes.
- Los seis folds sólo describen cobertura. No se ejecutó walk-forward de rentabilidad, CPCV, PBO ni DSR.
- MES 2025 ya fue investigado. MES 2026 no se abrió y sigue reservado para una estrategia completa congelada.

Siguiente paso: un fenómeno acotado y registrado antes de calcular sus resultados, con control comparable y evaluación temporal.
