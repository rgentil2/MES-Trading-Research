# B05K — Resultado final nivel B: T05-377, 135 sesiones DEV, bootstrap de bloques móviles

**Fecha de protocolo 2026-10-11 Colombia; ejecución GitHub 2026-10-12 UTC. Estado `B05K_DAILY_BLOCK_DIAGNOSTIC_COMPLETE_IN_SAMPLE_ONLY`, NO validación de alpha, NO promoción a fondeo.**

## Trazabilidad comprobada

- [Prerregistro antes de reabrir outcomes DEV](NQ_B05K_T05_DAILY_BLOCK_BOOTSTRAP_PREREG_2026_10_11.md), commit `629b55dd00811a5e3ad067ad0d9349f6816d3ab3`.
- [Motor congelado T05 diario + bootstrap 10.000](nq_b05k_t05_daily_block_bootstrap.py), commits `a9398791e07835bf86e3c9174c48f218dff11128` y guard QC `be61ec059bcb64473c03eb4ee8b471104a52b6b0`; [pruebas sintéticas](test_nq_b05k_t05_daily_block_bootstrap.py), commits `724b420e27ab99381eeb77da99f218020df240a5` y corrección de fixture PRE-DATA `b915a07c198b012434a803664ae80bac16a015bc`; [workflow](../../.github/workflows/nq-b05k-t05-daily-block-bootstrap-dev.yml), commit `1104bbac9fe169e168ffbfbe85a8f325d7ad59e1`.
- [Primer run **38201131748 FAILURE PRE-DATA**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38201131748): falló solo test sintético porque intentó asignar 15 operaciones en 13 días de prueba dejando 1 sola operación por día después del primero; se corrigió **solo el fixture** para permitir hasta 2/día, no motor, T05, fechas o stats tras P&L.
- [**RUN 38201169890 COMPLETED SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38201169890): 6/6 pruebas sintéticas PASS; 7 archivos privados DEV Last EXISTENTES octubre2025–abril2026 verificados con checksums SHA256 y procesados dentro de **UN SOLO RUNNER**. Artifact público seguro `b05k-t05-135-session-block-bootstrap-aggregates-only`, **ID 11726056329**, incluye `summary.json` y `report.md`; ambos se descargaron/leieron después del run.
- Ninguna nueva fuente/proveedor ni histórico distinto del ya adquirido, no Market Replay/L2, sin abrir holdouts T mayo–septiembre ni programa H sellado. Las ganancias/P&L **por fecha de sesión solo existieron en `_private/derived`** temporal; `_private` se borró al concluir, incluso en fallo, no se exportaron fechas de trades, fuentes/ticks ni retornos diarios. Se publican únicamente agregados.
- No se retocaron T05 señales/risk; el programa de hipótesis nuevas sigue **sin señales de 5 segundos**. T05 tiene señales 5s solo como legado congelado, sin tratarlo como nueva estrategia.

## Auditoría exacta del baseline T05 (PASS)

| Métrica | Confirmación |
|---|---:|
| Días fuente | 140 |
| **Sesiones DEV elegibles** | **135**, incluidos días con cero trades |
| Días con ≥1 trade | **77** |
| Sesiones P&L positivo | 38 |
| Sesiones P&L negativo | 39 |
| Sesiones P&L 0 (incluye días sin trade) | 58 |
| N trades | **115** |
| Semanas de calendario observadas | 29 (NO 29 eventos estadísticamente independientes) |
| Neto estrés original T05 | **+US$5.102,50** |
| Neto estrés +US$10 RT fijo sobre la MISMA trayectoria | **+US$3.952,50** |
| Positivos por mes | 6/7 |
| Leave-one-month-out (total de seis meses) | **+$3.530 a +$5.930** |
| PF estrés+$10 RT del benchmark congelado (sin recálculo broker) | **1,23717, por debajo de 1,25** |

N efectivo independiente no estimado, jamás sustituirlo por 115 trades o 135 sesiones; la unidad de incertidumbre es el retorno neto **por día/sesión** y el bootstrap conserva grupos de sesiones contiguas.

## Estadística REAL por sesiones (predefinido ANTES de outcomes del bloque)

Método: 10.000 muestras bootstrap de **bloques móviles NO CIRCULARES** de tamaño 5 sesiones como criterio PRINCIPAL, con sensibilidades PREDECLARADAS de 3 y 10, secuencias de 135 valores incluyendo días con 0; IC90 bilateral percentil de media USD/sesión, p unilateral exploratorio bajo nula centrada **después de selección previa de T05**. La evidencia no es p confirmatorio ni implica BH/Holm.

| Escenario | Bloque L | Media neta USD/sesión | IC90 de media USD/sesión | p exploratorio centrado | SE bootstrap USD/sesión | MDE aproximado* |
|---|---:|---:|---|---:|---:|---:|
| **Estrés T05** | 3 | +37,80 | **[−0,62, +74,17]** | 0,0441 | 22,72 | 48,23 |
| **Estrés T05** | **5 principal** | **+37,80** | **[+3,83, +71,02]** | **0,0293** | 20,42 | 43,35 |
| **Estrés T05** | 10 | +37,80 | [+7,09, +67,93] | 0,0205 | 18,44 | 39,15 |
| **Estrés +US$10 RT** | 3 | +29,28 | **[−9,08, +65,69]** | 0,0951 | 22,65 | 48,10 |
| **Estrés +US$10 RT** | **5 principal** | **+29,28** | **[−4,63, +62,22]** | **0,0692** | 20,36 | 43,24 |
| **Estrés +US$10 RT** | 10 | +29,28 | **[−1,33, +59,48]** | 0,0553 | 18,43 | 39,13 |

* MDE es una aproximación normal orientativa a alfa unilateral 0,10 y potencia 80% **por sesión**, no un verdadero cálculo de potencia bajo dependencia/selección. La media del escenario adicional (29,28) está por debajo de su MDE aproximado (43,24). IC90 positivo en 5 y 10 para estrés original, **pero cruza cero** con bloques 3. En **todos los tamaños 3/5/10**, el IC90 estrés+$10 incluye cero.

## Interpretación estadística y decisión del proyecto

1. **T05 gana en simulación** durante estos siete meses y LOMO 7/7 mantiene neto positivo, pero solo **77 de 135 sesiones operaron**; las sesiones de P&L 38 positivas y 39 negativas son muy similares en cantidad (el rendimiento depende de magnitud payoff).
2. Bajo estrés T05 original el IC por bloques principales favorece un efecto positivo, **pero no es estable a todos los tamaños de bloque preregistrados**, y lo más importante, los valores p **NO están calibrados para la selección adaptativa** con múltiples hipótesis previas. **Nunca llamar Gate1 PASS ni estadísticamente confirmado**.
3. El estrés adicional **+$10 RT** conserva mismos 115 trades, pero IC90 por bloques de 3, 5 y 10 sesiones **incluye cero**, y PF1,23717 <1,25. Falta precisión para una ventaja neta robusta frente a pequeños deterioros de ejecución. Este suplemento es fixed-path: no recalcula si el coste hubiese cambiado la admisión por daily risk.
4. Las pruebas de ejecución/microestructura siguen abiertas: B05G riesgo Last DD hasta $2462,50 bajo permutación de prints con igual timestamp; sin garantía de fills reales, NQ 50K condiciones de trailing DD no contrastadas, ni ROI anual comparable a VOO/QQQM en cuenta real.
5. El q Benjamini–Hochberg de familia **NO está calculado** para T05; Holm confirmatorio y años 3/5 del programa H no aplican a este periodo de T; **no sustituirlos por los p exploratorios del bootstrap**. Además las 135 sesiones provienen de datos ya usados para seleccionar T05; este diagnóstico no hace que la muestra vuelva a ser independiente.
6. **Dictamen: `T05_RESEARCH_CANDIDATE_ONLY_IN_SAMPLE_PRECISION_NOT_ROBUST_TO_EXTRA_COST`**. No comprar fondeo ni abrir OOS. Siguiente paso B05L: diagnóstico de robustez de ejecución y presupuesto adaptativo de búsqueda, ex ante, sin reoptimizar T05 ni generar decenas de filtros nuevos sobre los 135 días.

**Fuente verificable:** [Actions 38201169890](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38201169890), artifact `b05k-t05-135-session-block-bootstrap-aggregates-only` ID **11726056329**.
