# ALL13 — Resultados reales: ocho T, 255 combinaciones de una sola cuenta; H cinco opciones separadas

**13-oct-2026 · EJECUTADO Y VERIFICADO.** [GitHub Action 38436947056 COMPLETED SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38436947056), tests sintéticos, controles antes de abrir DEV, 7 fuentes licenciadas con SHA256 correcto, **140 sesiones fuente, 135 READY**, 20/20 máscaras D0 congeladas y 21 CASE T147 intactos. **Los 8 padres reproducidos EXACTAMENTE** y las 255 carteras de subconjuntos T estimables, con máximo una posición y dos entradas/día; el código no abrió datos sellados. [Artefacto SAFE completo con las 255 filas](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38436947056/artifacts/11833059042), ZIP SHA256 `43c802eb7dbe26218a1cc3f951b9941e83b55edcd7be95c73de0f52ca7a39d2a`. **Ningún fill broker, mercado OOS o DD flotante verificado.**

**Incidencia documentada:** corrida inicial [38434851980 FAILED](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38434851980) ya había comprobado paridades pero cayó al ordenar carteras por campo `ID` ausente. Se corrigió **solo el desempate de presentación con el conjunto de IDs** y se añadió test; [nueva Action](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38436947056) SUCCESS. No se cambió una entrada, costo, filtro, señal, stop ni horizonte.

## Universo y paridad

Las 13 originales: H09/H56/H69/H74/H77 + T05-377/T147/T186/T210/T212/T215/T217/T224. [Evaluación estructural 8191](NQ_ALL13_STRUCTURAL_SEARCH_RESULTS_2026_10_13.md): 7905 H+T mixtas sin calendario común, 31 H (5 alternativas +26 duplicaciones de padres) y 255 T con fuente común. **Las H no se suman con T**; la [rama H por contrato homogéneo MNQ](NQ_ALL13_H5_ALTERNATIVES_PARETO_RESULTS_2026_10_13.md) concluyó que H77 lidera ratio histórico 4,0806 con N140, pero sin confirmación.

| Padre T | N reproducido | Beneficio neto original USD | DD diario cerrado USD | Convención de costos |
|---|---:|---:|---:|---|
| T05-377 | 115 | +5.102,50 | 1.310,00 | NQ estrés legacy |
| T147 | 20 | +642,25 | 567,00 | NQ/MNQ base |
| T186 | 70 | −970,00 | 1.970,00 | NQ estrés |
| T210 | 17 | −418,00 | 741,00 | NQ base |
| T212 | 49 | −1.877,50 | 2.036,00 | NQ/MNQ base |
| T215 | 14 | +835,75 | 258,00 | NQ/MNQ base |
| T217 | 46 | −1.743,00 | 1.791,50 | NQ/MNQ base |
| T224 | 106 | +1.256,00 | 1.051,75 | NQ/MNQ base |

Estos son DD **diarios cerrados** en la misma convención de la búsqueda, no DD Last intratrade ni seguimiento real de una cuenta. El agregado NO suma padres, recalcula decisiones y evita concurrencia.

## Hallazgo central: siete subconjuntos T cumplen la criba económica exploratoria

Regla **registrada antes del resultado**: N≥35, ≥4 meses positivos de los 7, beneficio positivo con +$10RT y con 1,5× costos (manteniendo T05/T186 en su estrés original), PF≥1,25 bajo ambos, DD **diario cerrado** +$10RT≤$1.500 y expectativa R calculable. **No es aprobación D1 formal ni prueba estadística OOS**.

| Subconjunto T | N | Neto +$10RT USD | DD cerrado +$10RT USD | Neto/DD | PF +$10RT | Expectativa R/trade | Meses positivos base |
|---|---:|---:|---:|---:|---:|---:|---:|
| **T05 + T215** | **123** | **+5.468,25** | **1.295,50** | **4,2210** | **1,3427** | **0,2426** | **6/7** |
| **T05 + T186 + T215** | **172** | **+5.895,75** | **1.399,50** | **4,2128** | **1,2934** | **0,2179** | **7/7** |
| T05 + T147 + T215 | 134 | +4.484,25 | 1.222,50 | 3,6681 | 1,2649 | 0,1912 | 6/7 |
| T05 + T147 + T215 + T217 | 159 | +5.085,25 | 1.475,50 | 3,4465 | 1,2832 | 0,1477 | 7/7 |
| T05 + T210 + T215 | 135 | +4.847,75 | 1.456,50 | 3,3284 | 1,2961 | 0,1758 | 6/7 |
| T05 + T147 + T210 + T215 + T217 | 170 | +4.732,25 | 1.475,50 | 3,2072 | 1,2614 | 0,1085 | 6/7 |
| T147 + T210 + T215 | 47 | +886,75 | 1.009,00 | 0,8788 | 1,3113 | 0,0642 | 5/7 |

**Frontera de Pareto económica exploratoria** según neto +$10RT / DD cerrado / expectativa R: `T05+T215`, `T05+T186+T215`, `T05+T147+T215`, `T147+T210+T215` (este último no es una opción atractiva monetariamente pese a ser no dominado en tres ejes; ratio<1). La variante de mayor beneficio total bajo +$10RT entre las siete admisibles es **T05+T186+T215**, pero su DD sube $104 frente a T05+T215 y baja PF/expectativa; **T05+T215 tiene el mayor neto/DD con eficiencia R superior**.

**Descomposición de operaciones del mejor ratio T05+T215:** de las 123 ejecuciones, **109 fueron T05 y 14 T215**, mientras T05 sola hacía 115. El router descarta/se sustituye capacidad y no simplemente agrega +835,75 a T05. Resultado base B +$6.698,25 vs T05 base +$5.102,50; después +$10RT B +$5.468,25 vs T05 +$3.952,50. DD cerrado diario +$10RT B $1.295,50 vs T05 sola $1.390; ratio base T05 sola +$10RT=2,8435 y B=4,2210. **Ojo:** la superioridad es *in-sample*, no validada.

**Comparadores expresamente revisados:** T05+T224 (194 operaciones, net +$4.909,25 con +$10RT, DD cerrado +$10RT $1.811, PF 1,2223) **NO** cumple PF/DD; T05+T215+T224 (201 ops, net +$5.988, DD $1.762,75, PF1,2767) tampoco cumple DD≤$1.500; muchas combinaciones con más miembros ganan más USD bruto pero empeoran la protección frente a DD/costos.

## Advertencias de mayor importancia antes de cualquier decisión sobre la cuenta 50K

1. **TODOS los siete candidatos con screen favorable incluyen T215.** Esa señal tiene apenas **14 operaciones reales modeladas**, tras 16 CASE de D0 y dos rechazos de riesgo, y NO pasó el mínimo N≥15 de su D1 individual; IC90 y q ajustada individual N/D. Su aparente aporte marginal puede ser ruido o selección adaptativa. **Esto limita severamente la confianza de toda la frontera.**
2. **Se eligió la mejor de 255 configuraciones** sobre los mismos 135 días DEV, después de centenas de decisiones previas de investigación. Este máximo observado **está sesgado hacia arriba**. Reportamos números descriptivos del histórico, no estimaciones imparciales del próximo año. Exigir confirmación prospectiva/holdout genuinamente independiente SOLO cuando sea autorizado y sin usarlo para retocar.
3. **Los costos son heterogéneos** (T05/T186 estrés; T147 y cinco T base). Escenarios +$10RT y 1,5× son sensibilidad fixed-path; no validan fills NQ/MNQ ni comisiones y spreads de un plan fondeado.
4. **El DD de clasificación es equity diaria CERRADA** (por ejemplo $1.295,50). No representa DD intratrade, Last high watermark ni DD intraday/equity trailing My Funded Futures; el Last original T05 ya mostró posibles escenarios mayores $2.000. **No recomendar cuenta/contratos por este DD.**
5. **No existe la mejor cartera GLOBAL de las 13** calculable con el archivo actual: H minuto 2020–24 y T Last 2025–26 no tienen ventanas emparejadas. En H, H77 es solo alternativa de mayor ratio histórico (N140), no un retorno adicionable a T05+T215.
6. **No optimizar otra vez los siete.** Mantener a T05+T215 como **candidato exploratorio de eficiencia** y a T05+T186+T215 como **candidato exploratorio de mayor beneficio**, sin declarar uno aprobado. Portabilidad a NinjaTrader SIM y trayectorias marcadas a mercado deberán verificarse con reglas congeladas, no con una nueva búsqueda adaptativa.

**Estado del proyecto al cierre:** `ALL13_TOPOLOGY_PASS`; `H5_COMPARISON_PASS_REVIEW_ONLY`; `T255_SHADOW_SUCCESS_7_SCREEN_FAVORABLE_4_PARETO`; `H_T_GLOBAL_JOINT_EQUITY_NOT_ESTIMABLE`; `D1_FORMAL_NOT_APPROVED`; `D2_FORMAL_NOT_APPROVED`; `OOS_SEALED`; `FUNDED_ACCOUNT_NOT_OPENED`.
