# NQ-B02 — conciliación independiente de fuentes (2026-10-11)

**Estado inicial:** preregistro y plan técnico, aún sin comparación real.

**Fecha y contrato fijados antes de evaluar:** 15 de octubre de 2025, NQ 12-25. Ventana ET 08:00–12:00. Fuente Minute Last original: 240 barras etiquetadas por fin 08:01–12:00 ET. Fuente Tick Last: agregar prints de esos 240 minutos, usando únicamente el contrato exacto.

**Prueba primaria:** igualdad minuto a minuto de apertura, máximo, mínimo, cierre y volumen. Ambas fuentes tienen que ser independientes, no una transformación de otra. No cambiar las marcas temporales después de mirar el resultado.

**Seguridad:** el ZIP de Minute 2020–2026 contiene periodos reservados y se mantiene privado. Su procesamiento, si está autorizado, debe limitarse al miembro del contrato NQ 12-25 y al día de QC seleccionado. No copiar ni extraer el ZIP maestro en el repositorio público; allí solo se admiten métricas agregadas sin precios ni registros individuales. Julio–septiembre 2026 y los resultados de validación siguen cerrados.

**Estados:** MATCH si coinciden 240 minutos y OHLCV completo; MISMATCH si se comprueba diferencia; BLOQUEADO si falta acceso o un formato de fuente no puede validarse. Nunca inferir MATCH sin comparar dos fuentes originales. Anotar IDs de ejecución, commits, campos discrepantes y siguiente acción.

**Próximo paso:** verificar acceso a entorno privado, generar comparación real del día, conservar evidencia en la bitácora y actualizar NQ-B02 del master. Después abordar NQ-B03 (calidad de fills T05) y nuevas hipótesis NQ independientes que mejoren la cartera.
