# Programa NQ H59–H150 — investigación deductiva, no búsqueda de ganadores retrospectiva

Estado: plan de investigación. **No se han registrado todavía H67–H150 ni comprometido sus reglas**, que deberán surgir de diagnósticos causales de cada ronda y quedar congeladas antes de leer sus resultados.

## Punto de partida: 58 hipótesis numeradas, no 58 ensayos independientes

Se observaron 2020–2024 repetidas veces. El conjunto de pruebas no produce evidencia out-of-sample. Las ventanas 2025 y 2026 siguen selladas. H09, H29, H36, H54, H55 y H56 permanecen en la biblioteca, además de H02 y otras señales exploratorias. Cada candidato incluye origen, regla de señal, regla de salida, estado de la prueba, costes, frecuencia, correlaciones y solapamientos. No se borra un candidato por fallar un gate; se restringe su **autoridad**.

## Secuencia de investigación

1. **Observación:** citar la observación previa, incluso si es adversa, con su N, intervalos y años.
2. **Explicación causal:** mecanismo de mercado que explicaría el signo antes de elegir parámetros.
3. **Predicción falsable:** especificar condición observable, lado, horario de señal, unidad y horizonte. Declarar todos los segmentos complementarios, no solo el que parece rentable.
4. **Registro previo y tests sintéticos:** un único JSON/Markdown/fuente congelados. Registrar toda la familia con control global; cada variante consume presupuesto, sin reciclar alfa.
5. **Diagnóstico 2020–2024:** 30m neto, estrés adicional de slippage, IC 90% por semana y BH de toda la familia. Gate 1 intacto: N >150, media neta >0, IC90 inferior >0, q BH ≤0.10, ≥3 de 5 años positivos.
6. **Prueba exploratoria de ejecución:** salida única con SL/TP previamente especificados, MFE/MAE si existe resolución apropiada. Nunca escoger post hoc la combinación mejor y anunciarla confirmada.
7. **Cartera:** colapsar señales duplicadas antes de calcular frecuencia, exposición y drawdown. Medir año a año, simultaneidad, concentración, correlación semanal y compatibilidad con MFFU 50K ($2,000 trailing EOD/intradía de equity), separando mini/micro.
8. **Gate económico prospectivo:** comparar CAGR neto sobre capital nominal de referencia con el mayor entre **15 % anual, VOO y QQQM en USD, retorno total y fechas idénticas**. Verificar costes reales, estrés 1.5×, riesgo de equity flotante, exposición y retornos ajustados por riesgo. Medir **por separado** retorno efectivo de bolsillo del fondeo (desembolsos y payouts). Si faltan benchmarks o prueba de riesgo, declarar `ECONOMIC_DATA_PENDING`, nunca aprobar por defecto.
9. **Decisión:** conservar en biblioteca como `EXPLORATORY_LIBRARY`, `MONITOR_ONLY` o `CANDIDATE_FOR_NEW_DATA`, incluso si su validación individual falla. Ninguna etiqueta implica aprobación.
10. **Confirmación:** 2025 seguirá sellado hasta que se apruebe de forma explícita una estrategia **completamente congelada**. 2026 permanece reservado para pseudo-forward posterior, con SL/TP, costes y router ya fijados.

## Nuevo objetivo de rentabilidad económica (aprobado 2026-10-10)

Además de medir si las hipótesis tienen un efecto estadístico, **cada estrategia o cartera** debe aspirar a superar **estrictamente** el mayor de: (i) **15 % de CAGR neto anual**, (ii) CAGR por retorno total de **VOO**, y (iii) CAGR por retorno total de **QQQM**, calculados sobre la misma ventana temporal, en USD y con dividendos reinvertidos. El **12 % es una referencia diagnóstica**, no un pase del gate. La prueba económica no se aplica como filtro retroactivo que elimine H01-H66 ni reescribe sus conclusiones.

- **Ventana primaria 2020–2024 comparable con QQQM:** desde el **13-10-2020 o posterior** hasta una misma última fecha disponible en 2024. QQQM no existía antes; para estudiar 2020 completo se puede usar **QQQ como proxy etiquetado**, nunca como QQQM real.
- **Capital de referencia USD 50.000:** su CAGR equivalente sirve solo para normalizar una curva de estrategia; una cuenta fondeada **no** equivale a haber invertido personalmente USD 50.000. Presentar también el retorno monetario real sobre evaluaciones/fees/resets y payouts, usando flujos fechados/XIRR cuando corresponda.
- **Costes y supervivencia:** desglosar NinjaTrader Free frente a costes reales de la firma elegida, hacer estrés 1.5×, comprobar drawdown de cierres **y flotante**, restricciones MFFU, riesgo correlacionado y retornos ajustados por riesgo frente a ETF. Ningún CAGR alto aprueba por sí solo.
- **Señales conservadas:** H09, H29, H36, H44, H45, H54, H55, H56 y demás quedan en el banco exploratorio incluso si fracasan individualmente. El gate económico califica **carteras completas congeladas**, no borra hipótesis.
- **Estados:** `ECONOMIC_DATA_PENDING` si faltan ETF/curva/costes; `BELOW_ECONOMIC_HURDLE` si no vence al mayor; `ECONOMIC_HURDLE_MET_RISK_PENDING` si sí vence pero falta riesgo; `PROMISING_PORTFOLIO_EXPLORATORY` únicamente si desarrollo económico y controles de riesgo son satisfactorios (no validación OOS).
- **Evidencia intacta:** Gate 1 y gates confirmatorios Holm originales no cambian, ni 2025/2026 se abren por una comparación de CAGR.

**Documento rector del nuevo Gate:** `research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.md`; especificación legible por software: `research/nq/NQ_PORTFOLIO_ECONOMIC_GATE_2026_10_10.json`.

## Presupuesto máximo de 92 hipótesis adicionales (objetivo H150)

| Fase | IDs previstos | Conteo | Pregunta deductiva, a ajustar según pruebas anteriores |
|---|---|---:|---|
| 1 | H59–H66 | 8 | ¿Las coincidencias y la exclusividad de H09/H29/H54/H55/H56 alteran la expectativa, duplican riesgo o agregan información? |
| 2 | H67–H78 | 12 | ¿Qué contexto **conocido antes de 09:45** explica la concentración anual de H09, sin ajustar sus umbrales después del resultado? |
| 3 | H79–H90 | 12 | ¿La dirección o magnitud de H55/H56 cambia por estado de volatilidad *ex ante*? Predefinir estados exhaustivos. |
| 4 | H91–H102 | 12 | ¿Existen relaciones contemporáneas o de liderazgo ES/NQ **causales**? Solo si se verifican fuentes ES y timestamps sincronizados. |
| 5 | H103–H114 | 12 | ¿Qué diferencia ruptura aceptada de barrida rechazada del premercado? Evitar duplicados H05/H07/H53/H54. |
| 6 | H115–H126 | 12 | ¿El valor agregado de VWAP de distintos anclajes supera un control neutro y sobrevive a costes? |
| 7 | H127–H138 | 12 | ¿Hay microestructura informativa respaldada por Tick Last/Bid/Ask? **Condicional a verificar datos**: no simular delta a partir de OHLCV de minuto. |
| 8 | H139–H150 | 12 | ¿Los ensambles/contradicciones de familias antes registradas aportan selección de día o cobertura de cartera fuera del mero apilamiento de exposición? |
| **Total** | **H59–H150** | **92** | No se obliga a ejecutar una fase si no hay datos o mecanismo defendible; 150 es techo, no una cuota de p-hacking. |

## Hipótesis heredadas, no descartadas

H09 (gap continuation), H29 (reversión de impulso corto, muy baja N), H36 (reversión apertura), H55 (acercamiento VWAP nocturno), H56 (reversión premercado), H54 (ruptura premercado, casi neutra); H02 (ruptura fallida) y H05 (barrida high/low con contaminación de rollover) se conservan para auditoría/cartera. H44/H45 (N muy pequeñas) y H57 se conservan como pistas, no como estrategias validadas. La biblioteca registra estado y nunca borra métricas adversas.

## Riesgos de inferencia y derechos de datos

- H59–H66 son **derivaciones explícitas de resultados ya observados**; sus intervalos y p-values dentro de 2020–2024 son descriptivos, no descubrimientos independientes.
- Las pruebas con pocas señales conservan q y N como fallos; no se les fabrican más datos por correlación de índices (MES/ES y MNQ/NQ no son réplicas independientes).
- No depositar en un GitHub **público** ni los ZIP brutos de NinjaTrader ni el registro individual de operaciones, si su redistribución no está verificada.
- Los presupuestos de alfa para futuras familias los determinará `research_governance.py` al momento del preregistro, respetando el historial; no ampliar/quitar miembros después de observar resultados.