# S0.30 — Referencia externa TA-Lib sobre NQ IST M1 real (solo QA numérica)

**29-oct-2026.** Este nuevo auditor permite validar selectivamente **11 rutas matemáticas** contra TA-Lib usando solamente el ZIP NQ M1 original de 2020–2022, dentro de un runner privado, SIN evaluar ninguna señal AST, operación, beneficio, drawdown o candidato. No abre 2023–2026.

## Entrada y controles

- [Auditor S0.30](nq_m1_v35_real_ist_talib_oracles_qa.py) exige el SHA256 de ZIP privado original `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8` **antes** de abrir miembros. La whitelist solo acepta las 15 series `Minute_Last` de 2020, 2021 y 2022.
- Reutiliza `_validate_source` S0.27 (735 sesiones RTH completas, 39 parciales excluidas, grid de tick .25, fechas ordenadas y rollovers establecidos), preservando 13 puertas económicas 0/13.
- Selecciona origen, punto medio, última sesión y los 12 cambios de vencimiento: **15 sesiones independientes del resultado**. En cada una compara los índices de vela end-labeled **118=11:29 ET** y **389=16:00 ET**.
- **11 nombres × 15 sesiones × 2 índices = 330 comparaciones numéricas reales esperadas**: SMA, EMA, WMA, DEMA, TEMA, TRIMA, APO, TRIX, ATR, NATR y ADXR. Parámetros preregistrados en el código, no optimizados. Para ADXR el oráculo TA-Lib se transforma al mismo `ADXRx-10` que el router del AST; no confundir distancia a umbral con valor bruto.
- Tolerancias numéricas predeclaradas: .001 unidades para los casos estándar salvo .025 APO y .20 ADXR (paridades históricas en madurez), y **cualquier fallo hace fallar CI**. Las tolerancias requieren auditoría más rigurosa antes de liberar fórmulas.
- El artefacto solo contiene recuentos por familia, versión de TA-Lib, hash del archivo, excepciones/categorías y banderas de exclusión de señales/PNL/holdouts. No incluye ni exporta precios OHLC, números individuales del indicador, estrategias, órdenes, PnL ni ranking.

## Evidencia técnica previa

El primer [CI de adaptación 40866292641](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40866292641) FALLÓ porque comparaba ADXR ya normalizado por su `threshold=10` con ADXR bruto del oráculo. Esa discrepancia era **del comparador**, no un fallo adicional de la fórmula. Se corrigió la transformación del oráculo, y [CI #40866459994 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40866459994) registró **355 tests PASS**, 4 pruebas nuevas del adaptador en datos totalmente fabricados.

El resultado en **datos IST reales** será documentado como ejecución privada independiente, no inferido de este CI. Cualquier fallo se conserva y se investiga; no se aumenta silenciosamente la tolerancia ni se elimina un indicador para forzar PASS.

## Límites y siguiente paso

Este muestreo no certifica las 132 fórmulas, todos los parámetros, todas las sesiones, la ejecución M1 ni NinjaTrader. **0/13 controles** siguen sin aprobar. Antes de buscar y filtrar los 10.000 AST, se requieren criterios formales de cálculo de variantes propias, validación completa de fills/cuenta y adaptadores económicos D0–D2 con firmas. El backtest posterior del **portafolio congelado en NinjaTrader 8** continúa como etapa N8 obligatoria adicional.

## Resultado real posterior (verificado)

El [run privado #40866756442](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/40866756442) terminó SUCCESS contra fuente M1 original 2020–2022, **330/330 comparaciones** sobre 11 nombres y 15 sesiones, cero diferencias fuera de tolerancia. [Artefacto privado](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/40866756442/artifacts/12894730165) SHA `e279882bab3ccb2c9bdf385bef3c23c08483918d764583edeaebb2b8f6c19484`, vence 28-nov-2026. [Evidencia JSON](NQ_M1_V35_S030_REAL_IST_TALIB_330_QA_EVIDENCE_2026_10_29.json). No se han efectuado backtests económicos o en NT8 ni aprobado 132/132 fórmulas o los 13 gates.
