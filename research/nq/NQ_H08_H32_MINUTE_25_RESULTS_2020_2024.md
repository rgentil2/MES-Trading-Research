# Ronda NQ de 25 hipótesis de minuto: H08–H32 (desarrollo 2020–2024)

**Ejecución:** 2026-10-09; **universo:** NinjaTrader NQ minuto, 2020–2024 únicamente. **2025 y 2026 no se abrieron.**

## Resultado general

- 25 hipótesis pre-registradas como una sola familia, con definiciones y código congelados en GitHub **antes** de ver los resultados. 6 pruebas unitarias pasadas y el preflight GitHub previo aprobado.
- 1.221 sesiones RTH completas bajo rollover explícito; 25 particiones del instrumento NQ en desarrollo; 69 sesiones RTH parciales excluidas.
- **3.939 eventos** (señales-hypótesis, que pueden coexistir el mismo día); **11 de 25** hipótesis con **N>150**; **1 de esas 11** tiene media monetaria positiva.
- **0 de 25 superan el Gate 1** (N>150, expectativa neta>0, límite inferior IC90>0, BH q<=0,10 sobre 25 pruebas, ≥3/5 años, sin filtros retroactivos).
- No se creó ninguna estrategia ejecutable. Entradas a next 1-minute OPEN y salidas a +30min OPEN **sin SL/TP**. Coste en un NQ: NinjaTrader Free $5,74 ida/vuelta + 2 ticks de deslizamiento adverso por lado ($20), total $25,74/evento; más un estrés descriptivo opcional de $10. No añadir estas comisiones otra vez a los resultados netos.
- Los datos de 2020–2024 **ya se utilizaron para hipótesis anteriores H01–H07**: incluso un Gate1 superado habría sido exploratorio, no evidencia fuera de muestra.

## Resumen de las 25 hipótesis

| H | N | Media neta USD | IC 90 % USD | Años positivos | BH q, 25 pruebas | Dictamen |
|---|---:|---:|---|---:|---:|---|
| NQ-H08 | 555 | -42.02 | [-126.87, +45.36] | 2/5 | 0.852 | No supera Gate 1 |
| NQ-H09 | 173 | +117.38 | [-57.59, +286.64] | 3/5 | 0.706 | No supera Gate 1 |
| NQ-H10 | 10 | +510.76 | [+48.74, +945.76] | 4/5 | 0.684 | N insuficiente |
| NQ-H11 | 147 | +100.01 | [-72.34, +272.40] | 2/5 | 0.706 | N insuficiente |
| NQ-H12 | 157 | -33.70 | [-201.53, +137.35] | 3/5 | 0.852 | No supera Gate 1 |
| NQ-H13 | 197 | -41.53 | [-215.14, +123.22] | 3/5 | 0.852 | No supera Gate 1 |
| NQ-H14 | 86 | +64.43 | [-128.42, +256.10] | 3/5 | 0.852 | N insuficiente |
| NQ-H15 | 106 | +185.49 | [-55.16, +424.96] | 3/5 | 0.706 | N insuficiente |
| NQ-H16 | 343 | -27.97 | [-139.45, +82.11] | 1/5 | 0.852 | No supera Gate 1 |
| NQ-H17 | 160 | -62.80 | [-240.31, +118.25] | 2/5 | 0.852 | No supera Gate 1 |
| NQ-H18 | 170 | -46.00 | [-189.66, +96.71] | 2/5 | 0.852 | No supera Gate 1 |
| NQ-H19 | 59 | -94.30 | [-295.15, +111.50] | 1/5 | 0.852 | N insuficiente |
| NQ-H20 | 343 | -57.72 | [-147.75, +32.38] | 2/5 | 0.852 | No supera Gate 1 |
| NQ-H21 | 26 | +174.26 | [-222.67, +521.31] | 4/5 | 0.830 | N insuficiente |
| NQ-H22 | 127 | -19.72 | [-166.10, +132.41] | 3/5 | 0.852 | N insuficiente |
| NQ-H23 | 36 | +170.65 | [-95.46, +446.27] | 4/5 | 0.706 | N insuficiente |
| NQ-H24 | 17 | +90.44 | [-449.87, +633.38] | 2/5 | 0.852 | N insuficiente |
| NQ-H25 | 9 | +8.15 | [-373.24, +580.51] | 1/5 | 0.852 | N insuficiente |
| NQ-H26 | 71 | +61.09 | [-209.76, +333.49] | 3/5 | 0.852 | N insuficiente |
| NQ-H27 | 6 | -384.07 | [-1232.41, +416.88] | 1/5 | 0.852 | N insuficiente |
| NQ-H28 | 120 | -40.78 | [-190.74, +110.78] | 3/5 | 0.852 | N insuficiente |
| NQ-H29 | 45 | +227.15 | [+19.48, +440.04] | 4/5 | 0.684 | N insuficiente |
| NQ-H30 | 199 | -62.78 | [-168.27, +41.64] | 2/5 | 0.852 | No supera Gate 1 |
| NQ-H31 | 185 | -67.25 | [-182.37, +47.19] | 2/5 | 0.852 | No supera Gate 1 |
| NQ-H32 | 592 | -8.92 | [-67.61, +49.12] | 2/5 | 0.852 | No supera Gate 1 |

## Casos relevantes, sin reclasificación

- **H09 (gap + drive de apertura, continuación):** 173 eventos, $117,38 promedio neto por NQ, PF descriptivo 1,255 y 3/5 años positivos. Sin embargo, IC90 **[-$57,59; +$286,64]**, q BH **0,706**, por encima del 0,10 permitido. El año 2022 aporta cerca de todo el beneficio observado; 2020 y 2023 fueron negativos. **No valida la hipótesis**.
- **H29 (tres cierres 1m positivos/negativos con desaceleración, contrarian):** 45 eventos, media +$227,15, IC90 **[+$19,48; +$440,04]**, 4/5 años positivos y PF 1,998. **No cumple N>150** y q BH **0,684**. La cifra de ganancias es susceptible de gran error de muestreo. **No valida la hipótesis**.
- **H10:** solo 10 eventos, media +$510,76 e IC90 positivo, pero carece claramente de tamaño de muestra y q. **No valida la hipótesis**.
- Todas las otras 22 hipótesis fallan por expectativa, incertidumbre, multiplicidad o falta de muestra. No seleccionar nuevos umbrales para recuperar estas mismas hipótesis bajo la nueva etiqueta.

## Gobierno estadístico y limitaciones

- Se usó una única familia de 25 p-valores unilaterales mediante randomización sign-flip de **semanas calendario**, junto con bootstrap de bloques por semana (10.000 simulaciones cada uno). Benjamini–Hochberg se calculó sobre los 25 contrastes completos, incluidos los insuficientes. El control formal Holm utiliza el registro familiar index=2 y alfa asignado **0,0083333**, sin reutilizar presupuestos anteriores. Esa prueba también debe leerse como exploratoria sobre esta muestra repetidamente investigada.
- Tener múltiples señales de la misma fecha en distintas hipótesis **no las convierte en 3.939 observaciones independientes**. El agrupamiento por semana protege parcialmente frente a dependencia temporal y la simultaneidad se controla en cada hipótesis, no crea estrategias independientes.
- No se modelaron ticks, bid/ask, noticias, stop loss, take profit, costes por cola de órdenes, límites diarios de una cuenta fondeada ni el enrutador que evita conflictos ES+NQ. Un resultado positivo a 30 minutos no es P&L realizable confirmado.
- **No se usaron precios, retornos, regímenes, resultados ni parámetros de 2025 o 2026**. Un verdadero forward exige operar después de congelar en tiempo real; 2026 histórico es pseudo-forward cronológico y sigue sellado.

## Archivos incluidos

- `NQ_H08_H32_MINUTE_25_PREREG_2026_10_09.md`: especificaciones **anteriores** a resultados.
- `nq_h08_h32_minute_2020_2024.py`: código congelado por SHA del registro familiar GitHub.
- `test_nq_h08_h32_minute_2020_2024.py`: seis verificaciones locales y GitHub CI.
- `nq_h05_h07_level_volume_screen.py`: lector auditado de ZIP de desarrollo, utilizado como dependencia congelada.
- `NQ_H08_H32_EVENTS_2020_2024.csv`: eventos cronológicos detallados por hipótesis.
- `NQ_H08_H32_SUMMARY_25.csv`: cuadro compacto y reproducible.
- `NQ_H08_H32_REPORT_2020_2024.json`: estadísticas, escenarios de estrés e información anual.
- `nq_h08_h32_minute_family.json`: 25 miembros para corrección Holm reproducible.
- `execution_log.txt`: salida resumida de ejecución.

### Reproducir

Desde la raíz del repositorio, pasar primero el preflight:

```shell
python tools/research_governance.py --preflight-family NQ-MINUTE-25-H08-H32-V1
```

Después usar el ZIP original del usuario, **sin abrir 2025/26**:

```shell
python research/nq/nq_h08_h32_minute_2020_2024.py --zip /ruta/NQMNQ_Research_2020_2026.zip --out results/local_nq_h08_h32 --prereg-frozen
```

La bandera `--prereg-frozen` **no ejecuta el preflight por sí misma**: el operador debe comprobar la orden anterior, tal como se hizo en GitHub Actions antes de ejecutar el estudio.

### Decisión siguiente

La ronda no aporta una hipótesis estadísticamente aprobada. No repetir los 25 tests con mejores umbrales sobre los mismos cinco años. El siguiente proyecto puede ser **auditoría de disponibilidad Tick Last/Bid/Ask durante un mes de 2024**, o definir un experimento de minutos basado en una fuente/idea realmente distinta y preregistrada en nueva familia. No abrir 2025/2026.