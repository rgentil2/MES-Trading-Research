# NQ S0.27 — Adaptador lectura M1 IST real y control de integridad, sin backtest

**Fecha:** 2026-10-28. **Fuente elegida por el usuario:** OHLCV NQ de un minuto 2020–2022, un contrato, sin ticks obligatorios; ISV1 2023 e ISV2 2024 reservados, 2025–26 sellados. El rollover propio jueves −8 días antes del tercer viernes trimestral NO se modifica.

## Implementación nueva

[`nq_m1_v32_real_ist_source_readonly_qa.py`](nq_m1_v32_real_ist_source_readonly_qa.py) introduce un adaptador **de inspección solamente** y no un ejecutor de señales, órdenes ni estrategias:

- Comprueba que los 13 controles económicos permanecen sin certificar y la ejecución está formalmente bloqueada **antes** de leer bytes del mercado.
- Verifica SHA256 inmutable del archivo privado original `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8` antes de abrir miembros internos.
- Reutiliza el parser de `nq_m1_chrono_discovery.load_years` exclusivamente con whitelist `(2020,2021,2022)`; 15 ficheros NQ minute Last esperados. No abre datos de 2023–2026 aunque existan en el ZIP.
- Confirma 390 velas de minuto RTH completo por sesión, OHLC coherente, finitud, volumen no negativo y rejilla de 0,25 puntos. Verifica fechas estrictamente únicas/ordenadas, identidad del contrato elegido y 12 límites trimestrales sin back-adjust.
- Emite hash SHA256 agregado de la fuente M1 seleccionada, con las fechas y contratos incluidos en la huella, para detectar modificaciones de datos. No publica precios ni registros de sesiones individuales.
- Selecciona las fechas origen/mitad/final y cada rollover para contrastar ventanas previas del **mismo contrato**, sin importar contextos del futuro o de la expiración anterior.
- En esa selección llama los **132 nombres de fórmulas** (a índices de barra 118 y 389) mediante `nq_m1_v26_all_132_router.value` para detectar errores numéricos, faltas de contexto y alteraciones del pasado por modificar las velas posteriores a 11:29. Nunca evalúa árboles de estrategia LONG/SHORT, operaciones, PnL ni rentabilidad. Una fórmula que devuelve `None` queda documentada como «no disponible», no reemplazada por cero. Excepciones de implementación bloquean el resultado y se informan solamente por categoría.

**Importante:** la cobertura del 132/132 como ruta numérica y la invariancia causal son controles técnicos, NO equivalencia independiente de todas las fórmulas con TA-Lib, NinjaTrader o StrategyQuant. Para que el backtest económico pueda ejecutarse faltan el cierre explícito de la matriz 13/13, certificación semántica/órdenes/cuenta MFFU y aprobación humana vinculada al SHA.

## Evidencia de tests

[CI S0.27 sintético](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40790198066) PASS, **326 tests** del proyecto, entre ellos lectura de identidad de contrato, rollover, 132 rutas de indicadores, test de barra futura, rechazo de alteración de datos, fechas reservadas, SHA no autorizado y 13 puertas sin abrir.

Para pruebas con el ZIP real, el módulo está diseñado para ejecutarse **dentro de `rgentil2/NQ-Tick-Data`** con el ZIP descargado exclusivamente desde la release privada previamente congelada. Su salida debe ser JSON de recuentos y SHA, nunca arrays OHLC, señales individuales, operaciones o PnL. La prueba de fuente real se acredita por separado: no interpretar pruebas de datos artificiales como auditoría efectiva del ZIP histórico.

## Límite respecto a S0.26

S0.26 continúa artificial-only, sin posibilidad de introducir un array real y «backtestear» escondidamente. S0.27 agrega lectura validada y comprobaciones numéricas, pero **NO pasa ese array al simulador S0.26**. El motor económico real deberá ser un adaptador separado, auditable y aprobado por la matriz 13 controles con sus evidencias.

**Estado:** 10.000 candidatos estructurales congelados S0.22; 0/13 gates formalmente PASSED_VERIFIED; G0, D0, D1 y D2 sin evaluación económica; portafolio no construido.

## Evidencia posterior: auditoría ejecutada con ZIP M1 auténtico

El adaptador ya fue ejecutado en [GitHub privado #40790524579 SUCCESS](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/40790524579), usando el código público SHA `e722734f066e9533db5276b600fea607fdfb8b38` y ZIP privado SHA `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8`.

| Comprobación | Resultado |
|---|---:|
| Sesiones NQ M1 RTH 2020–2022 | 735 |
| Sesiones parciales excluidas | 39 |
| Rollover trimestrales | 12 |
| Contextos fuente reales muestreados | 15 |
| Nombres de indicadores programados muestreados | 132 |
| Cálculos numéricos sobre mercado real en muestra | 3.960 |
| Pruebas de invariancia ante barras futuras | 1.980 |
| Excepciones numéricas en esa muestra | 0 |

[Artefacto de recuentos en repositorio privado](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/40790524579/artifacts/12860344740), SHA256 `dc71bd2214d33bd10d112cf06e2aaba58184c78ef72aef43313b59377c7c2bf4`, caduca el 27-nov-2026. [Resumen permanente con evidencia](NQ_M1_V32_S027_VERIFIED_REAL_SOURCE_QA_2026_10_28.json).

**Límite:** este resultado demuestra integridad y verificaciones causales numéricas internas en una muestra, **no la paridad matemática independiente de 132 fórmulas**. Ningún AST de estrategia, orden, operación, PnL o ranking fue evaluado y los 13 gates económicos siguen sin aprobar.
