# NQ ticks — Primera familia conjunta T01/T02/T03 — desarrollo 2025-10 a 2026-04

**Estado 2026-10-11:** `EXPLORATORY_DIRECTIONAL_DIAGNOSTIC`. 7/7 jobs terminados SUCCESS en [GitHub Actions 38161815637](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38161815637). Hipótesis, thresholds y 5 horizontes prerregistrados **antes** de abrir los resultados: [NQ_T01_T03_SHORT_HORIZON_PREREG_2026_10_11.md](./NQ_T01_T03_SHORT_HORIZON_PREREG_2026_10_11.md). El primer piloto: [38161578622](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38161578622), 4/4 sesiones éxito.

**Alcance:** Tick Last NQ 08:00–12:00 ET, señales 09:40–11:10 ET, agregación 5s, posterior +1,+3,+5,+10,+20min. 140 fechas de archivos Last, 135 sesiones aptas para análisis y 5 días sin contexto de apertura completo (Nov 1, Dic 1, Mar 1, Abr 2). Datos autorizados Oct2025-Apr2026 **únicamente**. Mayo–junio 2026 **no consultados para resultados de esta familia**, julio–septiembre 2026 continúa sellado, octubre 2026 fuera. Se verificó SHA256 de cada archivo mensual descargado desde el repositorio privado Dev antes del análisis.

## Hallazgo principal 5 minutos — DESPLAZAMIENTO BRUTO, NO P&L

| Familia | Oportunidades (135 sesiones aptas) | Días con >=1 oportunidad | Promedio movimiento firmado +5min (ticks de 0,25 NQ) | Meses con promedio +5min positivo |
|---|---:|---:|---:|---:|
| T01 continuación apertura + velocidad operaciones | 198 | 99 | **−7,672** | 2/7 |
| T02 rechazo del rango + desaceleración operaciones | 298 | 108 | **+10,634** | 4/7 |
| T03 router de rango vol observado | 239 | 102 | **−6,795** | 4/7 |
| C01 ruptura sin filtro de actividad | 401 | 117 | **−4,402** | 2/7 |
| C02 reversión sin filtro de actividad | 508 | 116 | **−5,825** | 2/7 |

Frec. T02: **298 / ~6,5 meses de datos, ~46 eventos al mes** descriptivos, NO 46 trades ejecutados; superposiciones, cooldown 5min y costes/riesgo adicionales reducirán operaciones. El objetivo mensual de rentabilidad NO está verificado. 1 NQ = USD 5 por tick, por lo que +10,634 ticks equivale aritméticamente a +USD 53,17 **de desplazamiento bruto medio teórico**, NO ganancia alcanzable. Sin fills, comisiones, stop, drawdown o coste de fondeo no puede considerarse P&L ni ROI.

## Completo por mes: T02 versus ablación sin filtro y T01/T03

| Mes | Sesiones de origen/aptas | T01 n / +5m medio | T02 n / +5m medio | T03 n / +5m medio | C02 sin filtro n / +5m medio |
|---|---:|---:|---:|---:|---:|
| Oct-25 | 13/13 | 24 / −4,125 | 41 / +16,098 | 28 / +5,214 | 67 / −8,313 |
| Nov-25 | 20/19 | 21 / +52,429 | 20 / −59,400 | 19 / +42,789 | 49 / −46,714 |
| Dic-25 | 22/21 | 27 / −43,556 | 50 / +41,000 | 42 / −18,571 | 75 / +4,973 |
| Ene-26 | 21/21 | 30 / −15,233 | 47 / −1,362 | 34 / −43,029 | 70 / +7,714 |
| Feb-26 | 20/20 | 24 / +22,667 | 37 / −22,405 | 30 / +15,900 | 61 / −6,852 |
| Mar-26 | 22/21 | 31 / −8,161 | 53 / +37,641 | 37 / +5,541 | 89 / −1,674 |
| Abr-26 | 22/20 | 41 / −28,756 | 50 / +10,900 | 49 / −20,857 | 97 / −4,732 |

## Media firmada de desplazamiento a múltiples horizontes (ticks, ponderación por oportunidad)

| Familia | +1m | +3m | +5m | +10m | +20m |
|---|---:|---:|---:|---:|---:|
| T01 | −1,899 | −1,914 | −7,672 | −17,717 | −21,480 |
| T02 | +7,617 | +8,453 | +10,634 | +2,288 | −0,520 |
| T03 | +3,306 | −1,477 | −6,795 | −8,222 | −19,080 |
| C01 | −2,668 | −2,396 | −4,402 | −2,260 | −2,813 |
| C02 | −0,002 | +1,703 | −5,825 | −6,638 | −3,075 |

**Advertencias:** son promedios de cambios de precio desde el primer tick del bloque 5s *posterior* a la señal hasta el último tick del bloque de horizonte, no un modelo de orden ejecutada; ningún stop, TP, drawdown intratrade, slippage o comisiones. La media se estima por agregación mensual de medias diarias redondeadas; precisión reportada 0,001 tick es mecánica y no implica exactitud económica. Fechas correlacionadas, resultados no corregidos por multiplicidad y T02 mejor aparente seleccionada después de observar desarrollo: NO hay p-value confirmatorio o alpha demostrado.

## Deducción y siguiente experimento, aún sin ejecutar

**Observación T02:** mayor desplazamiento bruto +5min vs C02, y menor número de señales. Mecanismo plausible: una ruptura fallida que pierde participación impide algunos rebotes engañosos y apunta a reversión; queda por demostrar que compensa costes y los meses desfavorables, que hay suficientes operaciones no solapadas y que la contribución marginal es real.

**T01/T03:** mantener en la biblioteca, sin declararlos rentables. T03 router original no muestra valor incremental: no ajustar retrospectivamente solo para que elija T02 en meses buenos. Formular familia posterior con estado causal nuevo y criterios falsables, no reinterpretar T03 como éxito.

**Gate siguiente (T04: ejecución de T02 congelada):**
1. Construir o adaptar el motor de operaciones para que una única posición NQ/MNQ esté abierta a la vez, con colisiones y señales simultáneas resueltas causalmente; entradas post-señal; SL, TP, timeout y límite diario. La *duración prevista* puede ser 1–20min; no HFT por latencia.
2. Preregistrar de manera prospectiva **costes reales de la cuenta fondeada** y supuestos adversos 1x/1,5x; probar ablation T02 vs C02 sobre mismos días y exposición/riesgo, sin reoptimizar stop/TP mirando beneficios.
3. Medir por semana, mes, trimestre/semestre, DD flotante y cerrado, PF, expectancy neta, frecuencia mensual, peores rachas y pérdida diaria. Buscar estabilidad, no ROI de un mes extraordinario.
4. Mantener mayo–junio sin resultados de P&L mientras se congela familia ejecutable. Pseudo-forward Jul–Sep estrictamente sellado. Años 2020–2024 H01–H78 estudio distinto.

### Decisión

T02: `CANDIDATE_FOR_EXECUTION_FEASIBILITY_EXPLORATORY`; no lista para operar.
T01: `NOT_SUPPORTED_EXPLORATORY` para esta regla; componentes conservados.
T03: `NOT_SUPPORTED_EXPLORATORY` para este router fijo; componentes conservados.
Se mantienen las 5 variantes originales y los 5 horizontes sin borrar fallos ni reinterpretar vistas.
