# NQ S0.23 — Embudo operativo de trazabilidad y sus puertas de liberación

**Fecha:** 2026-10-28. **Cohorte:** exclusivamente NQ M1, 10.000 AST de S0.22 (semilla 20261028), un contrato, descubrimiento IST 2020–2022 en una fase futura.

## Mapa actualizado

| Nivel | Total que entra teóricamente | Comprobado estructuralmente | Aprobados *formales* | Rechazados *formales* | Estado |
|---|---:|---:|---:|---:|---|
| Generación RANDOM/MUTATE/CROSSOVER | 10.000 | 10.000 | n/a | n/a | HECHO, sin mercado |
| Auditoría de identidad, AST y linaje previa a G0 | 10.000 | **10.000** | n/a | 0 defectos estructurales | HECHO, solo preflight |
| Liberación de 13 gates antes de cualquier economía | 10.000 | — | **0/13 controles aprobados** | — | BLOQUEO GLOBAL |
| G0 (integridad, contrato, ejecución) | 10.000 | — | **0** | **0** | SIN INICIAR |
| D0 (muestra, frecuencia y evaluabilidad) | 10.000 | — | **0** | **0** | SIN INICIAR |
| D1 (PnL/PF/DD/frecuencia/costes) | 10.000 | — | **0** | **0** | SIN INICIAR |
| D2 (robustez, Monte Carlo y sensibilidad) | 10.000 | — | **0** | **0** | SIN INICIAR |
| ISV1 2023 (sin reoptimizar) | 10.000 | — | **0** | **0** | RESERVADO |
| ISV2 2024 (sin reoptimizar) | 10.000 | — | **0** | **0** | RESERVADO |
| Portfolio Builder (una cuenta NQ 50K) | 10.000 | — | **0** | **0** | SIN INICIAR |
| Prioridad y asignador MFFU | 10.000 | — | **0** | **0** | SIN INICIAR |

**Los 10.000 de la columna «entra» son el tamaño de la cohorte original, no la afirmación de que todos llegarán a cada etapa.** Una vez iniciada la evaluación real, cada etapa debe registrar su propio denominador de entrada, aprobados, rechazados, abstenciones y motivo reproducible, sin esconder descartes.

## Identidad y trazabilidad de cada candidato

[Ledger CSV generado en GitHub Actions](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40780256228/artifacts/12855854273) contiene 10.000 filas con: `id`, SHA256 AST, método RANDOM/MUTATE/CROSSOVER, IDs padres (que aparecen antes del hijo), tipo de orden MARKET/LIMIT/STOP, stop y objetivo, recuento de condiciones LONG/SHORT, número de familias de indicadores, veredicto pre-G0 y estado de espera en cada etapa. Cada fila permanece aunque sea rechazada o técnicamente no evaluable. No incluye PnL, operaciones ni precios.

La fuente de candidatos no se inventa ni se regenera con parámetros diferentes: `nq_m1_v28_funnel_ledger.py` reconstruye la cohorte S0.22 y comprueba la huella canónica fija `b9d2915fc55f86546ef63d74a588df5244d094eeecb4a7c900a4000d47660be9` antes de emitir un registro. El ledger CSV resultante tiene SHA256 `789b108c64e9673960a700cb8773c5cdd683f6efc3b6c494130a7b474849d256`, ZIP de artifacts SHA256 `e25a5af935f7b8f4f05d9509be7b08088f7f42e2201cf557f17cb717efb567f0`. Evidencia CI [40780256228 SUCCESS, 271 tests](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40780256228), retención del ZIP hasta 2026-11-27. Registro duradero [JSON QA](NQ_M1_V28_FUNNEL_LEDGER_QA_2026_10_28.json).

### Qué se comprueba (sin precios)

- 10.000 IDs inequívocos ligados criptográficamente a su AST, con 0 colisiones, orden de padres anterior al hijo.
- Universo NQ M1 1 contrato, reloj de New York, velas completadas y años elegibles IST exactamente 2020–2022.
- Parámetros de los 132 nombres ligados a sus entradas de catálogo; señales AND/OR, comparadores tipados y lags sin dependencia de futuro; salida 11:29 ET, un stop inicial requerido y órdenes de entrada estructuralmente válidas.
- Se detectan y retienen fallos sin eliminarlos de denominadores. Todos los 10.000 resultaron coherentes bajo la definición **estructural**; no significa que sus familias numéricas tengan oráculos externos aprobados.
- Se comprueba que ninguna fila contiene fitness ni puede interpretarse como resultado G0/D0/D1/D2. 13/13 gates aún sin verificación y ningún timestamp/archivo de mercado utilizado.

## Contrato futuro para seguimiento real (NO implementado ni activado aún)

Al aprobar las 13 puertas y la autorización vinculada a SHA del evaluador, el flujo posterior deberá conservar una secuencia auditable por `candidate_id`:

```text
GENERATED → STRUCTURAL_CHECKED → G0 → D0 → D1 → D2
                                        → ISV1_2023 → ISV2_2024
                                        → PORTFOLIO → MFFU_50K
```

Cada transición económica exigirá SHA256 del resultado, CI y fuente de datos permitida, evaluación del costo/riesgo, veredicto `PASS`/`FAIL`/`UNAVAILABLE`, evidencia causal y razón de rechazo. Ningún `FAIL` se eliminará ni convertirá en padre aprobado. G0/D0/D1/D2 todavía requieren adaptar sus motores NQ y verificar de modo independiente; **no existe promoción automática en S0.23**.

## Qué sigue y qué NO puede declararse terminado

Para que el embudo deje el estado `PRE_G0_WAITING`: cerrar certificación matemática/semántica de las 132 rutas, ejecución de órdenes en IST con tratamiento adecuado de ausencia de ticks 2020–22, exacto plan de MFFU 50K, adaptadores G0/D0/D1/D2, métricas compartidas de cartera y firma de las 13 evidencias. Preservar la regla de rollover usuario de jueves -8 días antes del tercer viernes trimestral, sin ajuste retrospectivo.

**Prohibido:** llamar estrategias rentables o finalistas a estos 10.000 AST, usar los años 2023/24 para seleccionar parámetros, abrir 2025/26, o convertir una prueba sintética de preflight en aprobación formal de ejecución económica.
