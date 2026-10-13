# Resultado FINAL cohorte T209–T228 G0/D0 — 20 registradas, solo 5 testables, D1 NO autorizada

**2026-10-13. Action [38418969389 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38418969389).** Ocho pruebas sintéticas PASS antes de acceder a datos, luego siete meses DEV existentes con SHA256 OK; final 140 sesiones fuente y 135 READY, mismas fuentes previamente licenciadas; [artefacto agregado seguro 11825342604](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38418969389/artifacts/11825342604), ZIP SHA256 `4d8cc9ee2f69c728305c8c0207f438708baae1724cc73e42456d1860d10671d6`. Limpieza de archivos licenciados en runner completada. **No datos nuevos, no OOS, no lectura de ganancias futuras, no costos ni fills medidos.** Las condiciones y umbrales de las veinte se congelaron **antes de este run**: [prerregistro JSON](NQ_T209_T228_20_STRUCTURAL_D0_PREREG_2026_10_13.json).

## Resultado agregado verificado

- 20 hipótesis T209–T228 completas en cuatro bloques.
- **5 testables y 5 distintas** (CASÉ≥15, CONTROL≥15, colisiones Jaccard CASE <0,85 según agregador): **T210, T212, T215, T217, T224**.
- **15 insuficientes:** fallan conteo CASE/CONTROL o cobertura necesaria. No atribuir una probabilidad ni PnL a esas reglas.
- G0/D0 oficial: `D0_COHORT_INSUFFICIENT_DISTINCT_TESTABLE_NO_D1`. **No supera las 20 testables distintas exigidas para nueva D1**, por lo que NO se evaluó dinero, PF, drawdown, IC90 ni q. Formal D1/D2 permanecen vacías.
- CASÉ por bloque (solo conteos de clasificaciones, **no operaciones**): A=85, B=77, C=3, D=123. Las activaciones de diferentes hipótesis pueden coincidir dentro de una sesión; no se suman como trades independientes.

## Las 20 preguntas y N CASE en las 135 sesiones READY

| Hipótesis | Mecanismo explorado | Días CASE | Resultado D0 |
|---|---|---:|---|
| T209 | Movimiento eficiente, continuación | 0 | NO TESTABLE |
| T210 | Rotación con poco avance, reversión | 18 | TESTABLE / distinta |
| T211 | Aceleración tardía, continuación | 12 | NO TESTABLE |
| T212 | Alternancia intrabarra, reversión | 50 | TESTABLE / distinta |
| T213 | Salto rechazado, reversión | 5 | NO TESTABLE |
| T214 | Volumen aceptado en extremos, continuación | 2 | NO TESTABLE |
| T215 | Migración POC vs cuerpo, seguimiento del POC | 16 | TESTABLE / distinta |
| T216 | Concentración en tres niveles, regreso al POC | 0 | NO TESTABLE |
| T217 | Volumen extremo y cierre contrario, rechazo | 46 | TESTABLE / distinta |
| T218 | Escape por nivel de bajo volumen | 13 | NO TESTABLE |
| T219 | Prima de prints grandes frente pequeños | 1 | NO TESTABLE |
| T220 | Aumento de tamaño medio negociado | 0 | NO TESTABLE |
| T221 | Divergencia prints grandes y cuerpo | 1 | NO TESTABLE |
| T222 | Cantidad concentrada temprano y reversión | 1 | NO TESTABLE |
| T223 | Agrupación fuerte con compresión | 0 | NO TESTABLE |
| T224 | Tiempo dominante a un lado del VWAP macro | 106 | TESTABLE / distinta |
| T225 | Cruces repetidos del VWAP macro | 5 | NO TESTABLE |
| T226 | Cruce de POC de la barra 10946 | 4 | NO TESTABLE |
| T227 | Pausas entre grupos y rotación | 8 | NO TESTABLE |
| T228 | Cambio de eficiencia frente a barra anterior | 0 | NO TESTABLE |

**Definición:** CASE = condición activada en la primera barra atómica 377 de la ventana preregistrada y plan preliminar de stop/riesgo aceptable, **no significa entrada ejecutada**. Cada CONTROL y OTHER y ausencia de barra figura en el artefacto seguro; aquí se reproducen los CASE sumando exactamente los siete agregados mensuales impresos por el Action. La clasificación TESTABLE está tomada del resultado completo 5/20 y el umbral >=15, sin sustituir CONTROLS hipotéticos.

## Deducciones sin optimizar a posteriori

1. El mecanismo de **tiempo del lado de VWAP macro T224** se activa 106 de 135 sesiones; actividad alta **no es rentabilidad** y puede ser poco discriminante.
2. Las preguntas de **reversión por alternancia T212** (50) y **rechazo de extremo con cantidad T217** (46) presentan activaciones suficientemente frecuentes como para comparar en estudios futuros, pero el embudo de esta cohorte NO permite pasar individualmente a D1 solo porque tienen más casos.
3. El bloque C de tamaño por print dio únicamente 3 activaciones sumadas entre cinco hipótesis: no hay evidencia de cobertura suficiente con estas reglas, **no modificar umbrales para forzar potencia**.
4. El bloque histórico T-C se considera **CERRADO en D0 insuficiente**, sin reparar tres o quince señales, sin descargar datos y sin abrir meses reservados.

## Cambio de fase

**Siguiente fase es ingeniería y paridad NinjaTrader SIM**, tomando una especificación ya congelada y comparando secuencia de barras/decisiones/órdenes con Python. No requiere elevar T210/T212/T215/T217/T224 a candidatas fondeables. [Gate técnico de portabilidad](NQ_NINJATRADER_SIM_PARITY_GATE_BEFORE_50K_2026_10_13.md). El router T05+T147 continúa como posible estudio shadow **único** con exposición temporal pendiente, pero no se vuelve al túnel de optimización.

**Código ejecutado:** [motor D0](../../local_nq_tick_2025_2026/nq_t209_t228_structural_d0.py), [pruebas](../../local_nq_tick_2025_2026/test_nq_t209_t228_structural_d0.py), [workflow](../../.github/workflows/nq-t209-t228-20-structural-G0-D0-dev.yml). D0 es observación causal de activaciones, **NO** confirmación de edge económico, ROI ni autorización de cuenta de fondeo US$50K.
