# Costos MyFundedFutures 50K: T05+T215 frente a T05+T186+T215

**ACTUALIZACIÓN POSTERIOR VERIFICADA 2026-10-13:** las cifras de *retiro* y reparto de este documento presumían de manera irreal que los 7 meses históricos completos eran sim-funded. Ese supuesto quedó reemplazado por la [simulación cronológica de evaluación → nueva etapa funded, con DD Last adverso](NQ_TOP2_MFFU_50K_EOD_FLOATING_REPLAY_RESULTS_2026_10_13.md) (GitHub Action 38443947480 SUCCESS). Retiro máximo condicional **A $1.099,35 y B $2.519,77** con buffer$2.100, **no** $4.407/$5.357 de la ilustración anterior. Los netos brutos fee-adjusted A$6.996,67/B$8.052,35 siguen conciliados, pero las ganancias EVAL no se retiran ni trasladan a la cuenta funded. Documento histórico conservado para trazabilidad.


**Corte 2026-10-13.** Estimación aritmética, **no backtest nuevo** ni confirmación de supervivencia en fondeo. Base: [T255 completo](NQ_ALL13_T255_EXHAUSTIVE_SHARED_ACCOUNT_RESULTS_2026_10_13.md), [summary.json del Action 38436947056](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38436947056/artifacts/11833059042), [lista oficial contratos y comisión MFFU 24-ago-2026](https://help.myfundedfutures.com/en/articles/9735811-futures-instrument-list), [Rapid EOD 50k parámetros oficiales 24-ago-2026](https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look), [plan y precio 50K promocional observado](https://myfundedfutures.com/plans/rapid-eod).

## Supuestos específicos y origen de costo ya cobrado

- Cartera A `T05-377+T215` N123: 109 T05 NQ + 14 T215 (**12 NQ, 2 MNQ**). PnL NETO del backtest BASE mixto +US$6.698,25, PnL +$10RT +US$5.468,25, DD CLOSED diario en stress extra10 $1.295,50, PF1,3427.
- Cartera B `T05-377+T186+T215` N172: 109 T05 NQ + 49 T186 NQ + 14 T215 (**12 NQ, 2 MNQ**). PnL NETO backtest BASE mixto +US$7.615,75, +$10RT +US$5.895,75, DD CLOSED diario en stress extra10 $1.399,50, PF1,2934.
- Ambos números ya restaron comisiones sintéticas y slippage. En código T05 y T186 utilizaron **US$7,50 por RT 1NQ** y slippage **2 ticks por lado** en stress legacy; T215 tuvo **US$4 RT NQ y US$1,50 RT MNQ**, con **2 ticks por lado** de slippage. NO descontar de nuevo las comisiones MFFU sobre esos PnL netos: únicamente **reemplazar** la comisión original, dejando sin modificar slippage simulado, size, señales ni exposición.
- Tarifa oficial MFFU **NQ US$4,68 RT por contrato** y **MNQ US$1,90 RT** (precios publicados en ayuda, posibles cambios posteriores), 1 contrato por operación (1NQ o 1MNQ según riesgo de modelo). Dos cartera no comparten operaciones cuando compiten por capacidad; estos son conteos del router real para ambas.
- `Rap id EOD 50K`: evaluación objetivo +US$3.000, DD MLL US$2.000 EOD, 30% consistencia, mínimo 4 días, sin activación. Sim funded 90/10, **buffer 2.100**, mínimo retiro US$500 y DD EOD trailing; **inactividad siete días**, escalado 3 minis/30 micros y prohibido Tier1 news funded. Página de planes muestra promo **US$135** pago único vs lista **US$225** para Rapid EOD 50K al corte de consulta. Cupón/promoción NO garantizados.
- No se han ejecutado eval con reglas de firma, retiradas, post-payout MLL, checks de noticias o inactividad; por eso PnL condicionado NO es dinero confirmado.

## Sustitución de costos por contrato y nuevo neto simulado

| Métrica USD | T05+T215 (A) | T05+T186+T215 (B) |
|---|---:|---:|
| Trades | 123 | 172 |
| NQ / MNQ | 121 / 2 | 170 / 2 |
| Neto original backtest con comisiones hipotéticas | 6.698,25 | 7.615,75 |
| Comisión **ya descontada** en backtest ($7,50/$4/$1,50 RT por modelo) | 868,50 | 1.236,00 |
| Comisión real **MFFU** ($4,68 NQ, $1,90 MNQ) | 570,08 | 799,40 |
| **Neto ajustado MFFU sin modificar el slippage simulado** | **6.996,67** | **8.052,35** |
| Neto MFFU **añadiendo** recargo conservador de $10 por RT | **5.766,67** | **6.332,35** |
| Beneficio bruto a repartir 90/10 si todos los trades fuesen sim-funded | 6.996,67 | 8.052,35 |
| 90% beneficio teórico atribuible trader, sin buffer | 6.297,00 | 7.247,12 |
| Menos costo único evaluacion $135 | **6.162,00** | **7.112,12** |
| Primera retirada teórica máxima manteniendo **buffer $2.100** = (Neto -2.100)×0,90 | 4.407,00 | 5.357,12 |
| **Cobro hipotético tras evaluación $135 y buffer sin retirar** | **4.272,00** | **5.222,12** |

**Arbitrajes:** B añade 49 NQ trades → **+US$1.055,68 de neto operativo ajustado MFFU**, o **+$950,11** del 90% al trader. Media ajustada por operación: A $56,88 vs B $46,82. La ventaja neta ajustada 15,09% viene de más operaciones, **no** de mayor eficiencia por operación. DD extra10 cerrado A $1.295,50/B $1.399,50 (no recalculado para comisión MFFU; DD MFFU exacto es N/D), B tiene DD +8,03% y PF estrés menor.

**Interpretación rigurosa del reparto:** los 90% y el buffer SOLO se aplican tras superar la **evaluación**. El +$3.000 de objetivo EVALUACIÓN NO es retirable; el saldo sim-funded reinicia separado. La fila de ganancias supone, **hipotéticamente**, que **las 123/172 operaciones transcurren íntegramente en cuenta sim-funded** y sin breach/reglas incumplidas. No se debe restar 3k a este bloque como si generara automáticamente payout; eso requiere una simulación cronológica EVAL→FUNDED todavía no hecha. El buffer queda en la cuenta, NO es comisión irrecuperable. Si comisión de compra pagada con otras ofertas o plataforma extra, actualizar aritmética sin retunar señales.

**RIESGO no comprobado:** DD del reporte T255 es **equity cerrada al cierre de cada sesión**, no excursión Last intraoperación ni equity/open-PnL que puede causar breach aun en cuentas EOD. T05 solo tuvo DD intrabarra adverso por permutación de timestamps hasta $2.462,50; no inferir que el MLL $2.000 permite estas posiciones 1NQ. Además el filtro de **7 días de inactividad** en Rapid EOD puede importar. Los mejores siete subconjuntos T de 255 incluyen T215 de solo **14 operaciones**, insuficiente para D1; selección post-hoc de 255 combinaciones sesga el aparente resultado. Se requiere replay cronológico de reglas MFFU, DD flotante y paper NinjaTrader antes de evaluar o fondear.
