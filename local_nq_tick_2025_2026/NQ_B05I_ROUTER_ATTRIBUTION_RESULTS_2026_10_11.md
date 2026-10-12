# B05I — Diagnóstico FINAL de coste de oportunidad y contribución H02 en cartera NQ

**Fecha:** 2026-10-11 Colombia. Estado `B05I_COMPLETE_AUDIT_NO_NEW_ALPHA`. El estudio se realizó EXCLUSIVAMENTE sobre el **artifact agregado seguro que ya existía** del backtest B05H02, sin acceso a ticks ni barras nuevas, y mantiene **H02 rechazada y T05 exploratoria**.

## Evidencia, fuente y reproducibilidad

- [Prerregistro del diagnóstico](NQ_B05I_ROUTER_ATTRIBUTION_SAFE_ONLY_PREREG_2026_10_11.md), commit `30d5c6dcc1cfaf5ef77c29f7e58cae4c86fd1c6a`, define identidad de contabilidad ANTES del motor B05I, sin experimentar con señales nuevas.
- Fuente: solo `summary.json` del artifact seguro `b05h02-seven-month-safe-reversion-report` ID **11722303789**, resultado H02 ya congelado en [GitHub Actions 38193895252 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38193895252); el workflow actual **NO tiene TOKEN privado de datos licenciados ni los abre**. No se compran/descargan periodos/archivos Last nuevos, ni se ingresa a holdouts H/T, ni se generan señales con velas de 5s.
- [Motor de atribución](nq_b05i_router_accounting.py), commit `278b2e29215977c069aca228b3ccda5af2e4c853`; [3 tests sintéticos](test_nq_b05i_router_accounting.py), commit `b6ca33ff597382139d22119683b70c85a2054082`; [workflow](../.github/workflows/nq-b05i-safe-router-attribution.yml), commit `8ec3ab2e8f03f03e50b6df6bc39441cba96e40a6`.
- [**GitHub Actions 38194498000 COMPLETED SUCCESS**](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38194498000), **3 tests PASS** y conciliación total exacta 140/135, siete meses de source aggregate, T05 115, H02 75, router 166, 60 H02 ejecutadas; artifact `b05i-safe-router-attribution-existing-aggregate-only` ID **11722524127**, `report.md/summary.json` descargados y leídos. Ningún nuevo modelo alpha ni P&L generado.

## Ecuaciones de control de UNA CUENTA

Por mes m:
`T05_retenido_m = Router_m − H02_atribuido_m`;
`T05_desplazado_m = T05_original_m − T05_retenido_m`;
`ΔRouter_m = H02_atribuido_m − T05_desplazado_m`.

**Conciliación EXACTA** sobre costos de estrés:
- T05 original: **115 trades, +USD5102,50**.
- T05 retenida en router: **106 trades, +USD4725**.
- Nueve T05 desplazadas: **neto histórico combinado +USD377,50**.
- H02 añadidas realmente en router: **60 trades, −USD2530**.
- Cartera total: **166 trades, +USD2195**.
- Delta cartera−T05 = **−USD2907,50**; al añadir +USD10 RT fijo sobre ruta congelada, delta **−USD3417,50**. Cuadra con los resultados H02 previamente publicados. Este coste extra no recalcula la ruta ejecutada.

## Todos los meses: los siete son negativos para la incorporación H02

| Mes | H02 ejecutada en router: neto USD | # T05 desplazadas / su neto USD | Variación router frente a T05 USD | H02 standalone neto USD |
|---|---:|---:|---:|---:|
| 2025-10 | −255,00 | 3 / −237,50 | **−17,50** | −387,50 |
| 2025-11 | −442,50 | 0 / 0 | **−442,50** | −442,50 |
| 2025-12 | −605,00 | 1 / −257,50 | **−347,50** | **+530,00** |
| 2026-01 | −797,50 | 3 / +667,50 | **−1465,00** | −945,00 |
| 2026-02 | −245,00 | 0 / 0 | **−245,00** | −22,50 |
| 2026-03 | +85,00 | 1 / +462,50 | **−377,50** | **+307,50** |
| 2026-04 | −270,00 | 1 / −257,50 | **−12,50** | −467,50 |
| **Total** | **−2530,00** | **9 / +377,50** | **−2907,50** | **−1427,50** |

**Resultado robusto en el historial de desarrollo, NO OOS:** H02 fue standalone negativa 5/7 meses, aportó P&L atribuible negativo dentro de router 6/7 y el *incremento contra T05 resultó negativo en 7/7 meses*. El hecho de que algunas T05 desplazadas fueran perdedoras indica que el cambio de asignación a veces evitó resultados negativos a posteriori; **no existe una regla disponible en vivo para identificarlas antes de su resultado** y no debe montarse un filtro basado en esos meses.

**Diciembre particularmente engañoso:** H02 sola +$530, pero su subconjunto ejecutado por cronología/capacidad bajo T05 compartida **−$605**; el resultado global cae $347,50 frente a T05 sola. No sumar resultados standalone ni promover señales que rindieron positivamente *a posteriori*.

## Dictamen para el proyecto

1. **H02 DESCARTADA** sin cambiar los parámetros por resultados. La descomposición 7/7 negativa hace injustificable incorporarla a la cuenta de fondeo simulada con esas reglas.
2. **T05 sigue solo candidata exploratoria**, PF estrés+$10/RT fijo 1,23717 (<1,25), DD adverso bajo permutación de timestamp hasta $2462,50 y sin demostrar fills broker ni reglas de fondeo.
3. **No generar inmediatamente decenas de variantes H03–H100 a partir de los mismos 135 días**. Priorizar formular **una nueva razón económica independiente** sin repetición de reversión VWAP (H02) o expansión de rango (H01), preservar cinco segundos excluidos de señales nuevas, no datos nuevos, no abrir holdouts, y declarar dependencia de búsquedas previas. Si no hay mecanismo respaldado antes de mirar retornos, **pausar** el search NQ en lugar de declarar un portfolio validado.
4. Una idea futura para estudiar por separado, SOLO si se pre-registra con parámetros y causalidad antes de resultados: volatilidad y velocidad de **barras por prints** para distinguir *regímenes* usando variables Last observables, con una lógica de operación distinta y evaluación atribuible bajo el mismo router, no un filtro construido para borrar trades perdedores retrospectivamente.
5. El objetivo anual >max(15%, VOO, QQQM) **no está demostrado** ni traducible a ROI real de fondeo con estos siete meses.
