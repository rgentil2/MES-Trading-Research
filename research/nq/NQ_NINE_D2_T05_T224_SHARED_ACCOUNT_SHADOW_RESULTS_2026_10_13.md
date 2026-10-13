# Resultado D2 sombra de nueve: T05+T224 en cuenta única — eficiencia beneficio/DD

**Fecha 2026-10-13.** [GitHub Action 38429799987 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38429799987), 7/7 pruebas sintéticas PASS antes de mercado, 7 meses Last DEV 2025-10..2026-04 con checksum, **140 sesiones fuente / 135 READY**, [artifact SAFE 11829834428](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38429799987/artifacts/11829834428) ZIP SHA256 `3bc4956c434b9325d4879122814dc5503f53dfc0a13a62402fbb6aa5561da7b9`. Corrida bajo [prerregistro original de nueve](NQ_NINE_D2_T05_T224_SHARED_ACCOUNT_SHADOW_PREREG_2026_10_13.md), sin optimizar umbrales ni abrir OOS. Se borraron de Actions todos los vectores diarios individuales y Last privados.

## Paridad previa a resultado

- T05 original estrés: **115 operaciones / +US$5.102,50**, paridad exacta.
- T224 original BASE: **106 operaciones / +US$1.256,00**, paridad exacta y **20/20 máscaras CASE D0** reconciliadas.
- B en UNA cuenta conserva **112 trades T05 y 82 T224 = 194 trades**; rechazos por capacidad/posición máximo dos nuevas al día: **49**. La cifra 194 no es 115+106 porque hay conflictos y exposición exclusiva.
- Sin secuencias intratimestamp inventadas, sin nuevos datos, sin fills broker reales. Proxies Last bajo **costos mixtos**: T05 modelo estrés antiguo, T224 modelo base nuevo; costos no homogéneos a todos los contratos.

## Comparación de dinero y eficiencia — SOLO universo Last T 7 meses

| Escenario único T | N | Neto USD | DD **cerrado** USD | Neto/DD cerrado | Neto/trade USD | PF | Observación |
|---|---:|---:|---:|---:|---:|---:|---|
| A: T05 standalone con costos estrés originales | 115 | +5.102,50 | 1.310,00 | **3,895** | 44,37 | 1,3183 | Benchmark reconstruido; DD Last de estudio original separado =1.797,50 |
| B: T05 estrés + T224 BASE, un solo router cronológico | 194 | +6.849,25 | 1.641,00 | **4,174** | 35,305 | 1,3255 | Neto extra +1.746,75, DD cerrado aumenta 331,00; beneficios/costos padres mixtos |
| B: T05 estrés + T224 **1,5×** costos de T224 | 194 | +5.967,75 | 1.718,25 | **3,473** | 30,762 | 1,2780 | **Menor eficiencia** que benchmark A de 3,895; no hay estrés homogéneo en todos los padres |
| B: +US$10 RT ambos, posiciones originales fijas | 194 | +4.909,25 | 1.811,00 | **2,711** | 25,305 | **1,2223** | **FALLA PF >=1,25**; también el T05 individual con +$10 RT falla PF=1,23717 |

**Importante:** la comparación ratio A=3,895 vs B=4,174 usa mismo DD **cerrado** de este motor. No igualar A DD cerrado1.310 con el DD adverso Last1.797,50 de T05 en otras pruebas. La **cartera B no tiene drawdown flotante/Last adverso ni simulación trailing de cuenta 50K**: no se conoce su peor riesgo ejecutable. El objetivo de ser más eficiente *por operación* está representado en la columna **neto/trade**, que **cae un 20,43%** de A a B (aunque el neto total crece 34,23%). No comparar directamente promedio US$/trade en NQ vs MNQ por diferentes tick-values.

**Contribución aparente B−A:** +$1.746,75 al costo mixto y +$956,75 comparando recargo +$10RT sobre ambas variantes, SIN significancia incremental propia. Seleccionar a posteriori T224 porque aumentó B en DEV es **adaptación**, no prueba OOS independiente.

**Distribución mensual del router B costos mixtos:** 2025oct +882,50; nov +159,00; dic +2.931,50; 2026ene +1.805,50; feb −489,50; mar +1.280,75; abr +279,50. Con recargo +$10RT, noviembre −61, febrero −789,50, abril −20,50. La serie NO valida estabilidad generalizable y las curvas son solo simuladas.

## Destino de los nueve y conclusión D2

- H09/H56: padres de familia H 2020–24 minuto, DD cerrados altos en 1NQ; datos no comparables a T tick últimos siete meses. H69/H74/H77 son **ruteadores alternativos** de esos mismos padres; no cinco estrategias de cuenta.
- T147: G0 paridad comprobada pero router con timestamps de entrada/salida no conciliado, N20 insuficiente, no sumable. T186: standalone -$970 y T05+T186 ya falló PF/DD; no repetir optimización.
- T05: benchmark con +$10RT PF1,23717<1,25, y escenarios DD adversos >2.000. T224 standalone PF1,1728<1,25 y qBH20=1. **El router T05+T224 tiene neto/DD cerrado mejor base pero NO supera el gate de robustez de +$10RT (PF1,2223)**.
- **Criterio nuevo solicitado por el usuario:** no elegir la opción de mayor ganancia sino valorar *eficiencia neto/DD* y *expectativa monetaria por trade* sometidas primero a robustez, q/IC, independencia y riesgo flotante. Sin gates completos, solo **comparadores de riesgo exploratorios**.
- **Estado D2 formal: `BLOCKED_NO_TWO_D1_PASSED_NO_EXECUTABLE_FILLS`**. No reporte de 9 PnL total, sin OOS T mayo–sept2026 ni H 2025/26 abiertos, sin fondeo.

Próximo paso metodológico: conservar los resultados sin retocar T05/T224, medir la **factibilidad de paridad de implementación** NinjaTrader SIM/Last para un modelo congelado cuando se autorice una prueba de plataforma; eventualmente contar con trailing/flotante *real* antes de hablar de cuenta 50K. No backtest D2 formal de nueve compatible con calendario actual.
