# Tablero económico unificado de 13 hipótesis H/T — D1 SHADOW, sin D1 formal

**Fecha:** 2026-10-13. **Nuevo resultado VERIFICADO:** [GitHub Action 38426588453 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38426588453), 8 pruebas sintéticas PASS antes de IO, 7 meses Last DEV ya disponibles checksum OK, **140 fuente/135 READY**, [artifact SAFE 11828767306](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38426588453/artifacts/11828767306) ZIP SHA256 `0a479911f4eebe0bdc9ab026cc1316c63daa6ad8b4bbabf3d0424d04375267a1`; fueron eliminados los vectores diarios privados del runner. **No apertura de holdouts ni datos nuevos ni broker fills demostrados.**

**Control de integridad:** código económico posterior a D0 registrado **antes** de leer beneficios de las 5; las 20 máscaras CASE originales se reconciliaron íntegramente contra el reporte D0 previo. Primer intento [38426116624](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38426116624) y segundo [38426344458](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38426344458) fallaron por tipo de fecha `date` vs cadena ISO; **se corrigió exclusivamente la interfaz, sin modificar reglas, umbrales ni costos**. Resultados siguientes son del run SUCCESS. Prerregistro [excepción exploratoria 13 H/T](NQ_13_H_T_EXPLORATORY_ECONOMIC_BRIDGE_PREREG_2026_10_13.md).

## Scorecard de 13 — mismas columnas, distinto modelo y ventana

**NO es una cartera sumada ni un ranking estadístico único**: cinco H provienen de **NQ minuto 2020–24** y ocho T de **NQ Last octubre2025–abril2026**. Los costos, tamaños, brackets, DD Last contra DD cerrado y denominadores q difieren. `N/D` significa NO medido, no cero. T05 bajo estrés y T186 bajo estrés; T147 y las cinco nuevas bajo modelo base; H09/H56/H69/H74/H77 bajo brackets 1m respectivos.

| ID | Familia y contrato modelo | N operaciones modelo | Neto USD | PF | DD USD | Principal impedimento |
|---|---|---:|---:|---:|---:|---|
| **H09** | H, 1 NQ minuto central | 173 | ≈+18.874 | 1,369 | 8.122 cerrado | No supera riesgo nominal de DD 50K en 1NQ; no OOS |
| **H56** | H, 1 NQ minuto bracket | 100 | +8.697,98 | 1,269 | 3.599,09 cerrado | Muestra insuficiente, DD alto, q familiar no significativo |
| **H69** | H, 1 MNQ proxy | 262 | +2.704,44 | 1,335 | 890,64 cerrado | BH q0,115 >0,10, muchos intervalos de inactividad, rentabilidad nominal baja |
| **H74** | H, 1 MNQ proxy | 132 | +1.657,84 | 1,438 | 444,10 cerrado | N132, q0,1149, −1.046,60 USD vs H69 en mismo universo |
| **H77** | H, 1 MNQ proxy | 140 | +2.385,30 | 1,632 | 584,54 cerrado | N140, concentración 75,2% en 2022; no mejora H69 en beneficio total |
| **T05-377** | T, 1 NQ Last estrés | 115 | +5.102,50 | 1,318 | 1.797,50 **Last** | +$10RT reduce PF a 1,237, DD Last sensibilidad hasta 2.462,50 |
| **T147** | T, 17NQ/3MNQ Last base | 20 | +642,25 | 1,499 | 567 cerrado | 20 operaciones, Q4-2025 negativo, faltan tiempos compartidos de exposición |
| **T186** | T, 1 NQ Last estrés | 70 | −970,00 | N/D individual | N/D individual | Standalone pierde; router T05+T186 falla PF y DD |
| **T210** | T, 17NQ Last base | 17 | −418,00 | 0,639 | 741,00 cerrado | Expectativa negativa |
| **T212** | T, 48NQ/1MNQ Last base | 49 | −1.877,50 | 0,470 | 2.036,00 cerrado | Expectativa negativa y DD >2k |
| **T215** | T, 12NQ/2MNQ Last base | **14** | **+835,75** | **2,629** | **258,00 cerrado** | 16 CASE -> solo 14 trades monetizados; N <15, IC90/q NO calculables con gate fijado |
| **T217** | T, 26NQ/20MNQ Last base | 46 | −1.743,00 | 0,612 | 1.791,50 cerrado | Expectativa negativa, 1,5× costo aumenta DD >2k |
| **T224** | T, 93NQ/13MNQ Last base | 106 | **+1.256,00** | **1,173** | 1.051,75 cerrado | PF<1,25, IC90 L5 cruza cero y qBH20=1 |

> Los importes de 13 hipótesis **NO deben sumarse**: H09/H56 son padres reutilizados dentro de H69/H74/H77; algunas T comparten sesiones y competirían por el mismo capital. El estudio no ha modelado una única curva de 13 estrategias.

## Nueva D1 SHADOW completa — todas las cinco seleccionadas, sin escoger winners

| ID | N CASE | N trades | Neto BASE USD | Estrés 1,5× | +$10RT | PF base | DD cerrado BASE | IC90 L5 de media neta **diaria** USD | q BH **k=20** | Estado |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| T210 | 18 | 17 | −418,00 | −622,00 | −588,00 | 0,6393 | 741,00 | [−8,22, +3,83] | 1,0 | FAIL NET |
| T212 | 50 | 49 | −1.877,50 | −2.455,25 | −2.367,50 | 0,4700 | 2.036,00 | [−24,33, −3,25] | 1,0 | FAIL NET/DD |
| T215 | 16 | **14** | **+835,75** | **+688,25** | **+695,75** | **2,6291** | **258,00** | **N/D, N<15** | N/D | LOW POWER |
| T217 | 46 | 46 | −1.743,00 | −2.090,00 | −2.203,00 | 0,6120 | 1.791,50 | [−24,84, +3,22] | 1,0 | FAIL NET |
| T224 | 106 | 106 | **+1.256,00** | **+117,25** | **+196,00** | **1,1728** | 1.051,75 | [−11,76, +25,54] | 1,0 | FAIL PF/IC/q |

**Cálculo:** bootstrap moving-block no circular B=10.000 por día; L5 primario y L3/L10 auditados en [artefacto JSON SAFE](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38426588453/artifacts/11828767306). La corrección usa 20 pruebas originales, con p=1 para los quince sin estudio económico, pero **NO corrige todas las decisiones históricas adaptativas**. Los resultados siguen siendo DEV reutilizada y posterior selección D0.

**Detalles críticos T215:** 16 oportunidades CASE, **dos rechazadas** al precio de entrada por superar riesgo; 14 modeladas; 9 TP/5 SL; 12 semanas activas; IC/q=N/D por política de N>=15 para inferencia. Mejor PF retrospectivo no autoriza cambiar tamaño, stops ni aprobarlo. En Q4 2025 +$242,25; enero–abril 2026 +$593,50, pero esto no es OOS.

**Detalles críticos T224:** 106 operaciones, solo 47 TP/59 SL; positivo en Q4 $911 y ene–abr $345 pero neto con +$10RT apenas +$196, IC90 diario [-11,76,+25,54], qBH20=1; riesgo cerrado base $1.051,75 NO es techo del drawdown *floating*, su curva tampoco es OOS.

## Dictamen de fase y paso siguiente

- **D1 económica sombra:** 5/5 completadas, **0/5** superan todos los filtros monetarios/estadísticos; **D1 FORMAL = 0** porque cohorte original T209–T228 solo reunió 5/20 TESTABLE (la excepción NO reduce puerta).
- **Ocho anteriores:** se reutilizan resultados y se conservan fallos históricos: ninguna es una estrategia confirmada ni fill verificado; H son variantes de dos señales padres, no cinco alphas.
- **Próxima D:** [Puerta D2 de compatibilidad para los 13](NQ_13_H_T_D2_READINESS_SCOPE_2026_10_13.md) puede cerrarse como *screen de factibilidad*, **pero D2 de cuenta compartida NO queda autorizada** al faltar ≥2 mecanismos respaldados con ejecución/resultado robustece; no fabricar PF/DD conjunto. 
- **NinjaTrader SIM** es siguiente trabajo técnico viable con UNA especificación congelada para verificar portabilidad, no simulación de cartera 50K. **No abrir holdouts ni conseguir más datos sin nueva decisión explícita**.

**Referencias de las ocho anteriores:** [ranking histórico H/T](NQ_ALL_H_T_TOP5_MONETARY_RANKING_2026_10_13.md), [H09 bracket 2020–24](NQ_H01_H02_H05_H09_EXECUTION_EXPLORATION_RESULTS_2020_2024.md), [H56](NQ_H53_H58_RESULTS_2020_2024.md), [H69](NQ_H67_H72_RESULTS_2020_2024.md), [H74/H77](NQ_H73_H78_RESULTS_2020_2024.md), [T147 G0](NQ_T05_T147_G0_PREFLIGHT_RESULTS_2026_10_13.md), [T186 router](NQ_T169_T188_MONETARY_V3_20_RESULTS_2026_10_13.md).
