# Puerta D2 para cohorte de 13 H/T — screening de compatibilidad (no cartera agregada)

**2026-10-13. Autorización del usuario:** agregar económicamente las 5 nuevas y llevar el grupo de las 13 a las fases D sucesivas **como ejercicio evaluativo**. Esto no significa que las 13 aprobaron D1 formal ni que exista un backtest compartido. Esta puerta de factibilidad se definió ANTES de conocer el PnL de T210/T212/T215/T217/T224; no se cambiará por los beneficios.

## Conjunto y separación obligatoria por muestra

| Familia | IDs | Fuente DEV | Núcleo causal | Admisión actual a D2 cartera de una cuenta |
|---|---|---|---|---|
| H Gap/premarket | H09, H56, H69, H74, H77 | NQ 1m 2020–24 | DOS padres H09 y H56; H69/H74/H77 son selectores, no posiciones independientes | NO: solapamiento de padres, NQ/MNQ proxy; no usar los 5 como portafolio de cinco trades |
| T Last antigua | T05-377, T147, T186 | Last NQ oct2025–abr2026 | Falsa ruptura 5s+377; barrida 4181; reversión lejos VWAP 4181 | T05+T147 solo pasó G0 de paridad, falta replay entrada/salida T147. T05+T186 shadow insuficiente |
| T Last nueva | T210, T212, T215, T217, T224 | Mismos Last 135 sesiones READY | Trayectoria precio, cantidad por nivel, permanencia macro | Solo shadow económico individual permitido post-D0 5/20; D1 formal bloqueado por amplitud |

## Chequeos que deben ocurrir en esta puerta, sin escoger winners post hoc

1. **13/13 fichas económicas completas o N/D motivado**, con N, beneficio neto, PF, DD, fees, contrato, IC/q y período. Para ocho antiguos se conservan valores archivados de los respectivos estudios; para cinco T se espera resultado del experimento congelado [puente exploratorio](NQ_13_H_T_EXPLORATORY_ECONOMIC_BRIDGE_PREREG_2026_10_13.md).
2. **NO mezclar ventanas**: H 2020–24 no comparte calendario con T oct2025–abr2026; no existe *equity curve* ni correlación emparejada H+T sin una misma historia. Los holdouts H2025/26 y T mayo–sept2026 NO se abren.
3. **H no son cinco estrategias diferentes**: revisar aporte incremental H69 sobre sus padres y resultado H74/H77 versus H69; nunca sumar H09 + H56 + sus tres routers.
4. **T no son ocho órdenes independientes**: para el portafolio se requiere un solo simulador cronológico que reproduzca N y PnL EXACTOS de cada padre, timestamps de entrada y salida y reglas de riesgos por instrumento/contrato con máximo una posición por cuenta; sin excepción de causalidad por grupo timestamp.
5. **Puerta estadística:** 15 hipótesis descartadas en T209–T228 conservan p=1 en BH20; la D1 monetaria de 5 es *post D0* y no corrige cientos de decisiones previas. q/Holm de familias H no se junta con qBH20 de T. D0 amplitud fallada no se borra ni se reemplaza por 13 contextos incompatibles.
6. **Puerta económica y fondeo:** PF >=1,25, beneficio >0 bajo estrés 1,5× y +$10RT, IC90 lower>0 para la expectativa en datos DEV, actividad mensual y estabilidad, DD closed y **Last floating/trailing de 50K** ≤ riesgo permitido (cuenta 50K como referencia, no un trader activo). T05 extra10 PF1,237<gate, DD por permutación timestamp $2.462,50 supera la referencia. H09 1NQ DD cerrado >$8k, no transferir a 1 MNQ por proporción sin otro motor.
7. **Política D2:** si al cierre de 13 hay **al menos dos** mecanismos económicamente defendibles en el mismo calendario y sin riesgos ambiguos, implementar **UNA** cartera *shadow* congelada con prioridad por timestamp (empate prioridad ex ante), máximo dos entradas/día, stop diario por PnL cerrado -$600, con T05 y T147 fieles al simulador original y los nuevos padres solo si comparables. No optimizar después. D2 formal continuará BLOCKED hasta verificaciones de fills/entradas/outputs coherentes.
8. Si no hay dos mecanismos o el motor no puede reconstruir la exposición, **D2 formal=NO AUTORIZADA** y registrar el bloqueo, sin falsear un backtest. Se puede trasladar 1 especificación congelada a NinjaTrader SIM como prueba de portabilidad, NO simulación ya comprobada de cuenta fondeada.

**Estado inicial:** preregistrada puerta de D2 documental; sin salida monetaria del nuevo bloque al escribir esta versión. Fuentes [riesgo viejo de 8](NQ_ALL_H_T_TOP5_MONETARY_RANKING_2026_10_13.md), [G0 T05/T147](NQ_T05_T147_G0_PREFLIGHT_RESULTS_2026_10_13.md), [D0 T209–228](NQ_T209_T228_20_STRUCTURAL_D0_RESULTS_2026_10_13.md), [puerta NinjaTrader SIM](NQ_NINJATRADER_SIM_PARITY_GATE_BEFORE_50K_2026_10_13.md).
