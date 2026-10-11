# NQ BBO: diagnóstico segmentado de operaciones fuera del spread — 2026-10-11

**Estado:** `DIAGNOSTIC_ONLY`. No se estimó rentabilidad, ejecución, latencia real, agresor o fill. Datos privados solo del repositorio `NQ-Ticks-Dev-2026`, verificados por SHA-256, ejecutados temporalmente en Actions público. **No se consultó 2026-07 a 2026-09 (pseudo-forward sellado)**.

**Workflow y registros:** [ejecución de cuatro fechas, completada satisfactoriamente](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38146478120). El código es [qc_bbo_dislocation.py](./qc_bbo_dislocation.py), con seis pruebas sintéticas en [test_qc_bbo_dislocation.py](./test_qc_bbo_dislocation.py). Solo incluye resúmenes; sin precios individuales ni archivos tick.

## Pregunta

¿Por qué aproximadamente 27–35% de las operaciones Last aparecen por fuera del Bid/Ask reconstruido **estrictamente anterior**? Evaluar explicación por horario, antigüedad de la cotización, ancho de spread y actualizaciones **en el mismo timestamp**, sin inferir secuencias entre archivos de NinjaTrader.

Ventana principal de diagnóstico: **09:30–11:30 ET**, segmentos 09:30–10:00, 10:00–10:30, 10:30–11:30. La implementación calcula también 08:00–09:30 y 11:30–12:00 como contexto; parámetros 50, 100, 250, 500, 1.000 ms son umbrales descriptivos *preestablecidos*, no optimizaciones de trading.

## Resultados principales, solo 09:30–11:30 ET

| Fecha ET | Operaciones Last | Fuera de BBO estrictamente previo | Máximo 50 ms: % fuera | Máximo 250 ms: % fuera | Máximo 1000 ms: % fuera | Operaciones fuera que pasan a dentro del BBO posterior *del mismo timestamp* |
|---|---:|---:|---:|---:|---:|---:|
| 2025-10-15 | 165.739 | 29,11% | 29,72% | 29,13% | 29,11% | 84,53% |
| 2025-11-03 | 162.339 | 27,27% | 26,90% | 27,28% | 27,27% | 84,54% |
| 2026-03-09 | 166.635 | 35,23% | 35,74% | 35,25% | 35,23% | 86,49% |
| 2026-06-16 | 154.265 | 33,23% | 33,44% | 33,23% | 33,23% | 87,67% |
| **Total ponderado** | **648.978** | **31,20%** | **31,55%** | **31,21%** | **31,20%** | **85,90%** |

**Importante:** El 85,90% usa como denominador *solo las operaciones fuera del BBO previo que tenían un cambio de cotización en el mismo timestamp*, no todas las operaciones, ni todos los casos anómalos. Este BBO alternativo es **NO CAUSAL**: las tres series no contienen secuenciación fiable para ordenar Last/Bid/Ask con igual timestamp. No usarlo para señales, TP/SL ni fills.

### Segmentos: porcentaje fuera del BBO previo (sin filtrado de antigüedad)

| Fecha | 09:30–10:00 | 10:00–10:30 | 10:30–11:30 |
|---|---:|---:|---:|
| 2025-10-15 | 35,39% | 24,16% | 24,90% |
| 2025-11-03 | 28,98% | 29,04% | 24,60% |
| 2026-03-09 | 38,77% | 36,61% | 30,91% |
| 2026-06-16 | 35,21% | 31,91% | 32,55% |

## Inferencia, con cautela

- **Edad de cotización sola no lo explica:** entre 50 y 1000 ms las proporciones anómalas son parecidas; cambiar solo el umbral no arregla el problema.
- **El orden del timestamp sí importa:** entre los casos anómalos coincidentes, ~85,9% cambia de clasificación bajo la reconstrucción *hipotética* posterior; esto es consistente con movimientos y actualizaciones sin orden global verificable en capturas independientes.
- **Horario y régimen importan:** la anomalía suele ser mayor en la primera media hora (especialmente octubre y marzo), pero cuatro fechas seleccionadas no permiten inferir estabilidad estadística ni una regla explotable.
- **No implica errores de fuente demostrados ni arbitraje:** un trade fuera del BBO previo puede ser normal si el libro cambia rápido o las capturas quedan desfasadas. Tampoco se dispone de NBBO, profundidad completa ni prioridad de cola.
- El nivel de tick puede servir para estudiar patrones de Last y estado de mercado, pero **no** para afirmar que una orden podía comprarse/venderse a un BBO histórico reconstruido.

## Próximo gate (antes de estrategias de scalping)

1. Extender segmentos a más fechas del conjunto de desarrollo, incluyendo diciembre, enero y el rollover de marzo; reportar mediana por **día** (no tratar millones de ticks correlacionados como millones de muestras independientes).
2. No usar el BBO de igual timestamp para decisiones ni asignar agresor sin secuenciación confiable. Explorar operaciones Last con cierres al precio ejecutado + costes conservadores y filtros de volatilidad/spread **previos**, con estrés de deslizamiento.
3. Para validar ejecución microestructural real exigir fuente ordenada por secuencia/venue o comparar con Market Replay/eventos registrados en orden por plataforma. Esta verificación no puede inferirse del export histórico separado.
4. No abrir el pseudo-forward julio–septiembre 2026 antes de preregistro y congelamiento del modelo, reglas TP/SL, sizing y comisiones.

No hay cálculo de ROI, CAGR, PF ni rentabilidad neta de estrategias en estos resultados.
