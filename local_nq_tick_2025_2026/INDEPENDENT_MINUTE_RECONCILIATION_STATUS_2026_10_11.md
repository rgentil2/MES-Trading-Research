# NQ Minute Last independiente vs Tick Last — actualización 2026-10-11

**Estado: archivo Minute Last ORIGINAL LOCALIZADO EN RELEASE PRIVADA; comparador y 34 pruebas sintéticas aprobados; conciliación efectiva minuto-a-minuto AÚN NO EJECUTADA.** Sustituye el estado anterior que decía que el ZIP faltaba de GitHub.

## Evidencia de almacenamiento
- Release privado: https://github.com/rgentil2/NQ-Tick-Data/releases/tag/nqmnq-minute-2020-2026-v1
- Archivo real en GitHub: `NQMNQ_Research_2020_2026.1.zip`, **65.405.000 bytes**, único asset según API GitHub.
- README privado: documenta SHA256 `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8`, validación contra el original y la normalización del nombre.
- Archivo original **no es solo Dev**: incluye 2025 validation y 2026 pseudo-forward históricos. No montar/descomprimir el ZIP completo dentro de Actions del repositorio público MES, ni dar al workflow público acceso al repositorio maestro.

## Trabajo existente y validación
- `qc_tick_to_minutes.py`: cuatro días de Tick Last reales con 240/240 minutos y consistencia interna 1m–5m. Run https://github.com/rgentil2/MES-Trading-Research/actions/runs/38148506627.
- `compare_independent_nq_minutes.py`: comparador separado OHLCV por contrato exacto, timestamp UTC/ET y convención de etiqueta (start/end), con resultados agregados.
- `test_compare_independent_nq_minutes.py`, `test_qc_tick_to_minutes.py`, `test_sim_nq_last_execution_skeleton.py`: **34/34 pruebas sintéticas** en https://github.com/rgentil2/MES-Trading-Research/actions/runs/38150302279. Esto NO constituye conciliación real ni estrategia rentable.
- Inspección local autorizada de fuente independiente **NQ 12-25, 2025-10-15**: 240 registros etiquetados consecutivamente **08:01–12:00 ET** (convención aparente de fin de barra), sin huecos ni repeticiones en esta franja; volumen total de estas 240 barras **262.422**. Es evidencia solo del archivo Minute, no de igualdad con Tick Last. El registro de 08:00 ET del ZIP corresponde a una barra adicional fuera de la ventana según etiquetado a fin y NO debe incluirse para comparar los ticks de 08:00–12:00.

## Próximo paso: un piloto real de conciliación, sin minutos privados desperdiciados
1. Crear en entorno privado autorizado un **extracto de un único día NQ 12-25, 2025-10-15**, tomando exclusivamente las 240 marcas UTC correspondientes a **08:01–12:00 ET** de la fuente Minute Last; mantenerlo privado. No pasar todo el ZIP maestro a Actions públicos.
2. Leer desde `NQ-Ticks-Dev-2026` exclusivamente el Tick Last del mismo contrato y fecha, con el token de solo lectura ya empleado en las validaciones anteriores; verificar SHA256 del release de ticks.
3. Ejecutar `compare_independent_nq_minutes.py --root <DIRECTORIO_PRIVADO> --day 2025-10-15 --minute-label end` y conservar métricas agregadas: igualdad de O/H/L/C/V, minutos faltantes, desvíos máximos. Reportar explícitamente un mismatch, no optimizar silenciosamente el timestamp.
4. Si pasa (o se entienden y documentan discrepancias), ampliar a días *del mismo contrato* distribuidos por Oct 2025–Jun 2026, rechazando diferencias por rollovers (en particular junio 2026).
5. Continuar de forma separada la investigación **Tick Last/Bid/Ask**: Oct 2025–Abr 2026 desarrollo; May–Jun validación interna; Jul–Sep 2026 **sellado**. No usar los meses validados para optimizar después de ver sus retornos.

## Foco de investigación
El ZIP 1m sirve como fuente independiente para **control de calidad y contexto de barras cerradas**, no para sustituir los ticks ni reabrir H01–H78. Las siguientes hipótesis *conjuntas* propuestas son NQ-T01 continuación condicionada, NQ-T02 ruptura fallida/reversión y NQ-T03 router de régimen. El motor conservador con entrada posterior a la señal, comisiones explícitas, slippage adverso, SL/TP y cierre por tiempo está sometido solo a pruebas sintéticas: no hay P&L validado ni fills reales.

**Costes GitHub Actions:** priorizar pruebas locales o runner público de código/diagnósticos agregados; solo usar un entorno privado autorizado para aislar el minuto y evitar cualquier acceso de la investigación pública al maestro sellado.
