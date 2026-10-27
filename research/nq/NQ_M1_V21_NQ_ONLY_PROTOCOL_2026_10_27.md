# NQ M1 V2.1 — señales con parámetros efectivos, contexto RTH y un solo NQ

**Fecha:** 27 de octubre de 2026. **Estado:** implementación S0 técnica, sin aprobación económica, sin portafolio real y sin reabrir ISV/holdouts.

## Decisión nueva que sustituye el alcance prospectivo anterior

El usuario decidió enfocar las campañas nuevas exclusivamente en **NQ**, un contrato, de acuerdo con el presupuesto de riesgo por operación ya prerregistrado. No lanzar escenarios MNQ, no hacer redimensionamiento retrospectivo para rescatar stops, no usar datos de MES/ES/EURUSD como fuente de selección de estrategias NQ. **No borrar** el diagnóstico histórico MNQ de V2.0: su conservación garantiza trazabilidad, pero no pertenece a V2.1.

## Alcance no restringido y dos vías

- Conservar la biblioteca de **132 bloques** (120 indicadores/cálculos y 12 patrones) y la generación **60 % aleatoria / 40 % recombinación y mutación estructural** como configuración inicial; el máximo de condiciones es ampliable por campaña, el tamaño de lote no es un límite científico.
- [Generador NQ V2.1](nq_m1_v21_semantic_generator.py) conserva la vía **BROAD_132**, incluidas candidatas no ejecutables, y genera por separado **ENGINEERING_38**, únicamente para desarrollo del motor actual de 38 fórmulas.
- **Nueva regla semántica:** los umbrales del registro (RSI niveles superior/inferior, Z-score, CCI, MFI, CMO, volumen relativo) se trasladan a predicados **ABOVE_LEVEL, BELOW_LEVEL, CROSS_ABOVE_LEVEL, CROSS_BELOW_LEVEL**, que los usan realmente. Si la condición es RISING/FALLING/lag, la estructura no lleva campos de umbral inactivos. Indicadores calculados guardan solo los parámetros realmente consumidos. SMA/EMA/WMA/RMA respetan fuente de precio; no permitir multiplicidad falsa en hashes por valores decorativos.
- Generación compatible con AND/OR, MARKET/LIMIT/STOP, SL obligatorio, TP opcional y salidas dinámicas ya disponibles como proxy OHLC, con stop-first/expiración de pendientes. Sintaxis V2.1 tiene versión de AST distinta de la V2.0; sus manifiestos y SHA quedan separados.
- **NQ exclusivamente:** cada AST V2.1 lleva `position_sizing={"instrument":"NQ","contracts":1}`. Se preserva riesgo de referencia USD300 por operación, máximo dos entradas/día, una posición simultánea, pausa con PnL cerrado <= -600; *investigación* no implica autorización real MFFU.

## Prerregistro S0.7 reproducible

- Muestra estructural, seed 20261027: **300 AST BROAD_132**, SHA `c20f12fe8d9a4242395c8abb61adb6eeee692601b7867edfa4120cbd0dd1f8bc`; **100 AST ENGINEERING_38**, SHA `fcf49b77937bc3eb687f741e7fa9c2e6e42d59407a59ffb09d9bc51ca9a8d098`.
- **82/100** AST ENGINEERING_38 son semántica y técnicamente interpretables como código M1; los otros **18/100** requieren ancla VWAP o niveles de sesión anterior/pivote no disponibles. Esto NO es validación económica ni D1/D2. Las 300 estructuras amplias no se eliminan ni se limitan a los 38 bloques; se conservan todas.
- [Actions público S0.7 inicial 40584704872 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40584704872), [artefacto 12770887932](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40584704872/artifacts/12770887932), contiene los dos manifiestos JSON sin precios ni PnL.
- [Actions público actualizado 40586072527 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40586072527): **83 pruebas PASS** sumadas de 11 baterías, incluidas comparaciones TA-Lib de 15 indicadores, reglas causales de V2.1, gobierno de parámetros, calentamiento RTH y router shadow corregido.
- V2.0 previa (300+100 AST, 92 con campos inertes) y S1 V1 (120 AST IST 2020–22) **quedan congeladas**. La mejora de sintaxis implica cambio de método: no agregar historiales de pruebas entre versiones como si fueran idénticas.

## Warmup: preparado, no conectado aún a simulación

[NQ V2.1 warmup](nq_m1_v21_warmup_context.py) + [pruebas](test_nq_m1_v21_warmup_context.py) implementan cálculo causal de indicadores con hasta dos sesiones RTH completas **anteriores, estrictamente ordenadas y pertenecientes al mismo contrato exacto NQH21/NQM21/etc.** Se niegan ISV, fechas futuras, OHLC parciales y cruces de contrato sin ajuste. VWAP y OBV vuelven a comenzar cada sesión; ATR y medias pueden aprovechar ventanas retrospectivas sin información futura. El cálculo de ATR multisesión incluye la brecha RTH entre sesiones como convención que debe documentarse y comparar independientemente.

**No marcar como implementado en el ejecutor económico:** el histórico Minute_Last ya validado se ofrece a la capa existente como sesiones y barras, pero no tiene aún una interfaz probada que asocie a cada barra el contract_id correcto. Antes de integrar warmup con PnL se necesita proveer metadatos de contrato verificables; si no, **fallar explícitamente**, sin unir series de contratos distintos con grandes gaps artificiales.

## Portafolio bajo NQ compartido

Se corrigió el [router shadow](nq_m1_v2_pipeline.py): el timestamp de señales simultáneas se reserva solo tras aceptar ex ante una orden admisible para **NQ**. Si la prioridad 1 falla el límite de riesgo conocido antes de la orden, una candidata de prioridad 2 puede entrar, sin consultar su PnL ni desempeño futuro. [Prueba de regresión](test_nq_m1_v2_s0.py). Aún NO es Portfolio Master de ejecución, no tiene drawdown flotante ni asignación completa o retest de órdenes al consolidar portafolios.

## Piloto privado y límites

- [Runner privado NQ V2.1 40585881792](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/40585881792): código fuente SHA `9f295b5205cb67da9fa414b2d33e7eda9fb00fc6`, lista de 82 AST semánticamente válidas registrada y primeras **10 AST** por orden de generación × **10 primeras sesiones RTH IST 2020–22**. Solo diagnóstico de cantidad de señales, rechazos por orden/riesgo/SL/TP y fills *modelo*. **No usar ni publicar PnL**; no ranking, sin G0–D2 formal. El workflow utiliza el ZIP privado previamente validado por SHA y lector V1 de datos con whitelist de años.
- El piloto corre sin warmup anterior integrado: si detecta señales que requieren > barras disponibles, quedarán en diagnóstico como no evaluables; su ausencia no es evidencia de alpha negativo.
- Los años **ISV1 2023 / ISV2 2024** siguen sin abrirse para V2.1. **Holdouts 2025/2026 y T** sellados. La investigación histórica reutilizada tampoco debe denominarse OOS virgen.

## Próximo trabajo

1. Comprobar resultado y artifact del piloto tipado NQ, registrar entradas/no-evaluables, sin elegir ganadores por esa muestra.
2. Acoplar historia de sesiones previas al motor solo tras metadatos de contrato comprobados; pruebas de rollover, gap y paridad, y reglas de 09:30–11:29 ET.
3. Completar otros 94 bloques a implementación y paridad, conservando la vía amplia de 132 y la diversidad estructural sin imponer PF/DD al generador.
4. Crear adaptadores *formales* de G0/D0/D1/D2 para AST, con tests y compatibilidad con criterios congelados; no inventar estados PASS ni relajar umbrales.
5. Evaluar tamaño fijo **1 NQ** y router de una sola cuenta en IST 2020–22 cuando esté auditable, añadiendo DD flotante/variación de comisiones/Monte Carlo; generar portafolios en IST y congelar antes de ISV1/ISV2.
