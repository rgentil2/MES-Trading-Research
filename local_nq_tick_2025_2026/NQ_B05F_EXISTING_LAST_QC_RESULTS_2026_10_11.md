# NQ-B05F — RESULTADO: QC causal y completitud de barras sobre el HISTÓRICO YA ARCHIVADO

**Fecha:** 2026-10-11 (America/Bogota). **Estado:** `COMPLETADO_INTEGRIDAD_INTERNA_PASS_NO_TRADING_ALPHA_EVALUATED`.

**Evidencia exacta:** [GitHub Actions 38187592666](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38187592666) **COMPLETED SUCCESS**, 9/9 jobs (1 pruebas, 7 meses, 1 agregador). Artifact seguro **`b05f-seven-month-existing-last-safe-qc`** (ID **11720501873**) contiene `summary.json` y `report.md`, ambos descargados y leídos. Las pruebas sintéticas **19/19 PASS**: nueve QC nuevas + diez controles de T05 233/377. El primer run [38187556057](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38187556057) terminó **FAILURE TÉCNICO antes de acceder a datos** porque una prueba asumió que la clave `same_timestamp` existía incluso cuando el contador era cero. Corrigida exclusivamente esa expectativa (`.get(...,0)`), commit `18a55969ef06e3731dd3dc74df9d33f01fe5b11b`; código y QC de mercado no cambiaron para obtener mejor resultado.

**Prerregistro anterior a los outcomes QC**: [NQ_B05F_EXISTING_LAST_QC_PREREG_2026_10_11.md](NQ_B05F_EXISTING_LAST_QC_PREREG_2026_10_11.md), commit `ec824185f55c603cf6a5b8a404bcb010e14c028f`; motor streaming [nq_b05f_existing_last_qc.py](nq_b05f_existing_last_qc.py), commit `652cf2dbbaf2f7dc9677a156e85d411a613d138d`; [pruebas](test_nq_b05f_existing_last_qc.py), commits `550f8d199dc940db948ff3f5c6a8ddda13541b4b` y corrección `18a55969ef06e3731dd3dc74df9d33f01fe5b11b`; [workflow](../.github/workflows/nq-b05f-existing-last-qc.yml), commits `b117b1831038f751f11d4d3d53e38a0381edd2fb` y `3c82ec196e889087833ef0aa3ae0bcf172c3a3e3`.

## 1. Integridad por mes DEV NQ Last (08:00–12:00 ET)

| Mes | Días fuente | Días elegibles | OR incompleta | OR demasiado estrecha | Prints Last | Bins de 5s vacíos 09:40–11:10 |
|---|---:|---:|---:|---:|---:|---:|
| 2025-10 | 13 | 13 | 0 | 0 | 2.909.560 | 0 |
| 2025-11 | 20 | 19 | 1 | 0 | 5.349.362 | 141 |
| 2025-12 | 22 | 21 | 1 | 0 | 4.009.970 | 509 |
| 2026-01 | 21 | 21 | 0 | 0 | 4.907.288 | 2 |
| 2026-02 | 20 | 20 | 0 | 0 | 4.973.288 | 1 |
| 2026-03 | 22 | 21 | 1 | 0 | 4.234.268 | 570 |
| 2026-04 | 22 | 20 | 2 | 0 | 4.467.005 | 1.110 |
| **Total** | **140** | **135** | **5** | **0** | **30.850.741** | **2.333** |

Se reproducen **exactamente 140 días fuente y 135 elegibles** de T05/T13. Los cinco días fuera resultan de apertura 09:30–09:35 ET con al menos una barra de 5 segundos sin transacciones observadas; **no se introdujo selección nueva ni se retiraron los dos trades T05 sin BBO previo fresco de T10**. Las cantidades negociadas observadas suman **33.343.793 contratos**, distintas de 30.850.741 transacciones/prints.

- Sumatoria de prints, volumen, OHLCV interno **5s→1m** y grilla/orden de fuente **PASS** sobre los ficheros leídos; esto **NO** verifica contra un segundo proveedor independiente ni demuestra ausencia absoluta de prints faltantes.
- **10.975** intervalos de 5 segundos sin Last a lo largo de 08:00–12:00 ET (140 sesiones ×2880), de los cuales **2.333** en 09:40–11:10 ET; **131 de 140 sesiones** sin ningún bin de 5s vacío durante esa ventana. Que un bin esté vacío puede ser ausencia legítima de transacciones o registro incompleto; **no interpretar todos como corrupción** ni inventar prints.
- **62 intervalos entre transacciones >=60 s**; máximo salto de **271,4 segundos**. Esto obliga a evaluar completitud de ventanas que lo requieran, no a borrar filas.
- **15.979.304 marcas temporales Last repetidas** respecto al registro anterior (**51,8 % de prints** aproximadamente), **5.390.040** de ellas con cambio de precio. Esas marcas iguales son válidas para QC monotónico pero NO prueban orden de ejecución exchange. **Cuidado con order-sensitive OHLC-close / SL/TP Last y barras por prints cuando un grupo con timestamp idéntico cruza frontera de cuenta.** No se reordenaron registros originales ni se trataron como errores.

## 2. Contextos causalmente terminados, sin mirar futuras barras

Cada decisión es un cierre de cinco segundos 09:40–11:10 ET (1080 oportunidades de comprobación *140 días = **151.200**, incluidas 5 sesiones que fueron no elegibles por apertura). La disponibilidad exige **dos barras de N prints totalmente cerradas**, usando únicamente Last con timestamp estrictamente anterior a cada cierre; `qty` no se confunde con número de filas.

| Tamaño de contexto (prints) | Decisiones con 2 barras completas / 151.200 | Cobertura | Días listos 09:30 | Días listos 10:00 | Días listos 11:10 |
|---|---:|---:|---:|---:|---:|
| **233** | 151.200 | **100,00 %** | 138/140 | 140/140 | 140/140 |
| **377** | 151.073 | **99,92 %** | 138/140 | 140/140 | 140/140 |
| **4181** | 146.452 | **96,86 %** | 133/140 | 135/140 | 137/140 |
| **10946** | 144.220 | **95,38 %** | 81/140 | 134/140 | 134/140 |

**Interpretación:** técnicamente son posibles las cuatro longitudes sobre el Last disponible para investigación de **mecanismos observables**, particularmente 233/377 en ventana tardía. El 10946 no siempre está listo a las 09:30 y la disponibilidad no significa ventaja ni robustez estadística. Hay que recalcular readiness en los **135 días elegibles** al ejecutar una hipótesis, sin utilizar los cinco descartados para fabricar resultados.

## 3. Restricción de fuentes y monetización

- Se usaron únicamente los **siete releases DEV Last preexistentes** de `rgentil2/NQ-Ticks-Dev-2026`, con verificación SHA256 y limpieza de copias temporales al terminar cada runner. **NO se adquirió historial, fuente, nueva fecha, L2 ni Replay**. No se usaron periodos 2026 mayo–septiembre T, ni históricos H 2025/2026 sellados, ni datos nuevos.
- **No se modificó T05:** referencia anterior **115 trades, +$5.102,50 estrés, PF1,31826, DD Last $1.797,50; estrés +$10/RT fijo PF1,23717 (<1,25)**. No se ejecutó nueva simulación monetaria aquí.
- La secuencia Last original es el **orden de exportación**, no orden de matching necesariamente certificado para timestamps idénticos. La transparencia sobre esta ambigüedad es necesaria antes de defender fills más finos. Bid/Ask previa fresca en 113/115 T05 sigue siendo QC, no fill real.
- **No se puede identificar true agressor side, delta genuino comprador-vendedor, L2 o cola**. No intentaremos forzar estas variables sobre TXT actuales.

## 4. Decisión

**`B05F_QC_PASS_INTERNAL_SOURCE_AND_CAUSAL_BAR_READINESS`**: conservar intacta toda fuente original; ningún motivo demostrado para borrar masivamente filas/ticks; usar `VALID_LAST_ONLY` y `CONTEXT_READY_AT_DECISION` como condiciones causales definidas por cada estrategia. Los cinco días ya excluidos por apertura se mantienen fuera del baseline elegible y se reportan.

**Siguiente NQ-B05G recomendado: prueba de sensibilidad a desempate de timestamps Last** para T05, usando **solo los mismos archivos DEV** y preservando cada grupo de prints simultáneos en timestamp, precio y cantidad. Congelar variantes de orden alternativo como **stress adversarial, NO limpiezas ni secuencia exchange verdadera**, y cuantificar si cambiar orden relativo **dentro de una misma marca de tiempo** altera cierres 233/377, señales y ejecución Last; sin escoger el orden más rentable. Si se prueba robustez o se identifica magnitud de incertidumbre, avanzar a formular hipótesis NQ realmente diferenciadas sobre precio/actividad/volatilidad y contexto 4181/10946, con presupuesto de búsqueda y router de capital único. No reoptimizar costos/stops, no abrir holdouts, no contratar fondeo.

**Estado:** B05F COMPLETADO, no Alpha, no fuente adicional, periodos OOS cerrados.
