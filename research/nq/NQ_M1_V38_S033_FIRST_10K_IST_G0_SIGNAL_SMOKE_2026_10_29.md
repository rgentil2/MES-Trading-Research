# NQ S0.33 — Comienzo del evaluador económico 10K: primer G0 diagnóstico de señales con IST M1 real

**29-oct-2026.** Se comienza la integración real del evaluador de las **10.000 estructuras AST** registradas con 132 rutas de indicadores. Esta **primera versión es un smoke test de señales**, NO ejecuta operaciones, PnL, DD, cartera, ni ranking. Por diseño mantiene `0/13 PASSED_VERIFIED`, G0 formal sin aprobación, y años 2023–2026 sin abrir.

## Contrato reproducible

- Fuente futura: ZIP NQ `Minute_Last` auténtico 2020–2022 SHA256 `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8`. Validación antes de lectura; 735 sesiones completas, 39 parciales excluidas, 12 rollovers y uso solo del **mismo contrato NQ** en máximo dos RTH anteriores.
- Cohorte: regenerar los 10.000 AST con semilla **20261028**, identidad SHA `b9d2915fc55f86546ef63d74a588df5244d094eeecb4a7c900a4000d47660be9`, sin nuevos parámetros ni mutaciones. Primera prueba: índices **0, 909, 1818, 2727, 3636, 4545, 5454, 6363, 7272, 8181, 9090, 9999**, independientemente del rendimiento.
- Muestra de 15 sesiones: primera, mediana, última y las doce primeras sesiones posteriores a rollovers trimestrales. En cada combinación AST-sesión, evaluar cinco cierres M1 **índices 4, 25, 50, 85, 116**, todos previos al flat obligatorio 11:29.
- Volumen previsto de comprobaciones reales: **12 × 15 × 5 = 900** decisiones AST LONG/SHORT/NO_SIGNAL/BOTH_CONFLICT/UNAVAILABLE. Un indicador sin suficientes barras devuelve dato no disponible, no falso. Se suprime la excepción numérica como falso dato: una excepción auténtica detiene el runner con el nombre del tipo y dispara corrección.
- Enviar a la salida solamente recuentos por candidato de señales, no precios, sesiones individualizadas ni operaciones. **No** inferir que 12 estrategias comprobadas equivalen a 10.000 evaluadas ni que señales disponibles implican estrategia rentable.

## QA técnica antes de usar ZIP real

[CI #40892536845 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/40892536845): **373 tests aprobados**, 5 adicionales sobre muestras sintéticas con condiciones SMA, SHA congelado 10K, datos prohibidos posteriores a 2022 y rechazo de ZIP sin identidad. El módulo nuevo es [`nq_m1_v38_10k_real_ist_signal_smoke.py`](nq_m1_v38_10k_real_ist_signal_smoke.py).

## Próxima etapa

Cuando el smoke sobre IST real funcione, construir un ejecutor ECONÓMICO por operaciones que implemente los **AST 132 → señales → órdenes pendientes completas → SL/TP/trailing → horario 11:29 → PnL/comisión/costes → DD + control de cuenta compartida**, con tests de paridad y reglas exactas MFFU, sin contaminar ISV 2023/2024. Solo entonces escalar a candidatos completos en fases y filtros G0/D0/D1/D2. Mantener validación final **N8 NinjaTrader 8** del portafolio seleccionado antes de fondeo.
