# S0.34 — Primer replay exploratorio de operaciones AST sobre NQ M1 IST (12 estrategias × 3 sesiones)

**Fecha 2026-10-29.** El usuario pidió continuar el evaluador desde 900 decisiones de señales hasta entradas, stops, objetivos, salidas y PnL. Este replay constituye una **investigación económica provisional** de las primeras 12 estrategias AST preseleccionadas por índice fijo (no por rendimiento), en tres fechas también fijadas por posición: primera, central y última sesión de las 735 completas de IST 2020–2022. No es un examen de robustez estadística ni una aprobación formal G0/D0/D1/D2.

## Metodología

- El código [`nq_m1_v39_ast_ist_exploratory_order_replay.py`](nq_m1_v39_ast_ist_exploratory_order_replay.py) lee NQ Minute_Last M1 2020–2022 exclusivamente tras verificar SHA256 original `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8`, 15 miembros del ZIP permitidos, 735 sesiones de 390 barras, 39 parciales descartadas y política de rollover inmutable. Contexto de hasta dos sesiones previas del mismo contrato, sin cruzar rollover.
- Cohorte de origen AST SHA `b9d2915fc55f86546ef63d74a588df5244d094eeecb4a7c900a4000d47660be9`, mismos 12 índices preregistrados en S0.33: 0,909,1818,2727,3636,4545,5454,6363,7272,8181,9090,9999. No se reinterpretan para favorecer estrategias.
- En cada día se buscan señales LONG/SHORT causales de 09:35 a 11:27 ET; entrada MARKET inmediata en próxima apertura, o STOP/LIMIT pendiente hasta vencimiento 1–30 barras. No se abren posiciones después de 11:28. Flat forzoso a las 11:29 ET.
- Reutiliza exactamente funciones matemáticas de stop, objetivo, break-even, trailing, órdenes y SL-first del **motor técnico sintético** S0.26; `simulate_synthetic_day` continúa estrictamente artificial y no admite datos históricos. Los tests contrastan el replay nuevo contra S0.26 sobre la misma fuente generada.
- Provisiones de investigación: US$20/punto NQ, grid .25 (US$5/tick), comisión US$4,68 RT y 2 ticks adversos por lado, stop monetario modelo US$300, máximo 2 operaciones al día y pausa de pérdida **cerrada** US$600. Son provisiones, NO las reglas MFFU definitivas, ni una garantía de fill de exchange. En vela ambigua SL y TP, se cobra SL primero; los TP limit requieren trade-through o marketable at open.
- **Admisión posterior a fill no válida para operar:** cuando una orden habría tenido fill y únicamente después se descubre falta de stop válido, un riesgo por encima del cap o un objetivo no resuelto, se incrementa `POST_FILL_*_UNMODELLED`. No se debe interpretar esos casos como «orden cancelada en tiempo real» ni como PnL cero seguro.
- Recolecta recuentos agregados, trades modelo, net USD, PF si hay pérdidas brutas y DD de trades cerrados por cada AST solo en **3 sesiones**. No se publica una cartera ni se rankean como finalistas por ganancias de tres días. Ni riesgo flotante/stop de pérdida EOD ni coherencia de broker están certificados.

## Evidencia de preflight

[CI #40896243585 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40896243585), **379/379 pruebas** (6 adicionales); comparador diferencial S0.26, causalidad, horario, años reservados, rechazo de ZIP sin SHA, cancelaciones posfill no modeladas y ausencia de PF en caso sin trades.

La ejecución real de este replay deberá efectuarse en el repositorio privado, con una nueva versión de workflow firmada. **Una muestra de 3 sesiones nunca basta para aceptar una estrategia.** Los 13 gates formales siguen 0/13 PASSED_VERIFIED, la campaña 10.000 AST todavía no tiene backtest económico, 2023–2026 permanecen sin leer y el portafolio ganador requerirá backtest independiente en NinjaTrader 8.

## Resultado posterior: replay IST real ejecutado

[Run #40896676531 SUCCESS](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/40896676531) (fuente real NQ M1 2020–22): 12 AST predefinidas × 3 sesiones, 14 operaciones modelo completas y **143 eventos POST_FILL no modelados**. Los eventos detectados demostraron un error de secuenciación de la orden: no se podía cancelar sin riesgo después del fill. **No usar este PnL parcial como fitness ni como selector.** [Artifact 12906672973](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/40896676531/artifacts/12906672973). Corregido en [S0.35](NQ_M1_V40_S035_CAUSAL_PRE_ORDER_GUARDS_2026_10_29.md), se repitieron AST y fechas sin cambio de parámetros y desaparecieron esas invalidaciones posfill en la misma muestra.
