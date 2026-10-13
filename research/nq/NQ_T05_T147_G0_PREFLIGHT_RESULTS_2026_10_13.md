# RESULTADO FINAL G0 T05 + T147 — paridad positiva, replay de exposición PENDIENTE

**Fecha:** 2026-10-13. **Resultado real:** [GitHub Actions 38415595454 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38415595454), 6 pruebas sintéticas PASS, descarga temporal exclusivamente de los siete archivos Last DEV preexistentes con SHA256 OK, borrado posterior de `_private`, [artifact SAFE 11824631763](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38415595454/artifacts/11824631763), ZIP SHA256 `f58a19d767b8f27d1a3a7978c0d976fbefb93bff91056de508aea94e16b00c78`. **El siguiente resultado está extraído de la salida de agregado del job oficial; no inventar fills.**

## Metodología

Se congeló primero [G0 PREFLIGHT](NQ_T05_T147_SHARED_ROUTER_G0_PREFLIGHT_PREREG_2026_10_13.md), luego código de reproducción causal/whitelist y pruebas sintéticas, y después se ejecutaron exactamente siete meses 2025-10–2026-04. Se preservaron en memoria y borraron los vectores temporales e información de ticks privados; **ningún OOS H 2025/26 ni T mayo–sept2026 abierto**. Esta prueba NO calcula beneficio de un router combinado.

| Métrica G0 | Resultado verificado |
|---|---:|
| Días fuente / READY | **140 / 135** |
| T05-377 operaciones estresadas reproducidas | **115** |
| T05-377 neto estrés reproducido | **+$5.102,50** |
| T05 días abortados por exposición irresoluble | **0** |
| T147 sesiones etiquetadas CASE | **21** |
| T147 operaciones modeladas D1 reproducidas | **20** |
| T147 P&L base D1 reproducido | **+$642,25** |
| T147 CASE con rechazo de riesgo al precio proxy de entrada | **1** |
| Operaciones T147 cuyo grupo de entrada toca el stop ambiguamente | **0** |
| Instrumentos modelados T147 | **17 NQ / 3 MNQ** |
| Días con señales de T05 y T147 | **12** |
| Estado exacto G0 | **G0_PARENT_PARITY_OK_EXPOSURE_REPLAY_REQUIRED** |

**Interpretación:** las dos simulaciones originales se reprodujeron con los mismos N y beneficios, **sin modificar sus reglas, tarifas ni tamaños**. Los 12 días de coincidencia de señales abren la pregunta sobre interferencia/exposición, pero no indican que existan 12 operaciones simultáneas ni que ambas ganen. Un CASE T147 quedó sin operación porque el modelo rechazó el riesgo al simular la entrada, dato que no se debe rescatar post hoc.

**Bloqueo restante:** el motor original T147 de D1 publica stop/target y PnL de cada caso, pero **no da un contrato de entrada y salida timestamp para el router conjunto en el mismo formato que T05**. La cifra 0 de entradas ambiguas del modelo no reemplaza reconstrucción de exposición temporal; hay que hacer esa conciliación de timestamps/stop-first, costo MNQ/NQ y posición única antes de estudiar beneficio incremental. No usar la ganancia +$642,25 como ganancia sumable a T05.

## Decisión y disciplina de rotación

- **Cerrar G0 técnico PASS de paridad**, no anunciar cartera validada. D1 formal 0, D2 formal 0, OOS cerrado.
- **No afinar T05/T147 ni repetir G0 para buscar otro PnL.** Dejar en cola un ÚNICO router shadow preregistrado, que garantice la reconstrucción de entrada/salida en tiempo causal y una única cuenta. Si no es realizable, **NOT_ESTIMABLE**.
- **Pasar ya al BLOQUE H-B** con resultados previos para evaluar independencia H09/H56/H69/H74/H77 y no fijarse indefinidamente en una combinación T. Después pasar al siguiente bloque de mecanismos distintos.
- La comparación de DD referencial US$2000 para cuenta futura US$50K es solo pantalla; ninguna medición de trailing real ni broker fill se hizo.

**Código:** [script de G0](../../local_nq_tick_2025_2026/nq_t05_t147_g0_preflight.py), [tests](../../local_nq_tick_2025_2026/test_nq_t05_t147_g0_preflight.py), [workflow](../../.github/workflows/nq-t05-t147-g0-parent-parity-preflight.yml); [rotación de hipótesis](NQ_RESEARCH_ROTATION_BATCH_POLICY_2026_10_13.md).
