# Corrección autorizada — NQ Tick Scalping Q4-2025 a H1-2026

**Fecha:** 2026-10-11. **Mandato del usuario:** incluir **desde octubre de 2025** datos `Last`, `Bid`, `Ask` para el nuevo estudio de scalping NQ. Esta regla amplía *exclusivamente esta línea* y prevalece en ella sobre la división inicial que empezaba enero de 2026. Los estudios anteriores H01–H78 y el holdout 2025 del programa histórico de minutos permanecen con sus políticas propias, sin autorización de reaprovechar este material.

| Período ET | Uso | Acceso |
|---|---|---|
| **Oct–dic 2025 + ene–abr 2026** | **Desarrollo**; microestructura, hipótesis conjuntas, stops, TP, ejecución | Sí, únicamente en la rama nueva y auditada |
| **May–jun 2026** | **Validación interna**; selección final, repetidamente inspeccionada = desarrollo observado | Sí |
| **Jul–sep 2026** | **Pseudo-forward histórico offline** | **SELLADO** hasta congelamiento final de código, señales, stops, comisiones, sizing y protocolo; apertura completa única |
| **Oct 2026** | Archivo fuera de este estudio | No para desarrollo ni selección; separado |

**Inicio real disponible:** exportación NinjaTrader del 14-oct-2025 arrojó ceros tras filtro de sesión; se registró exportación positiva a partir de 15-oct-2025. Ningún estudio debe inventar sesiones previas. Descargar de GitHub no valida integridad del contenido: comprobar SHA256 y QC de fechas, contratos, last/bid/ask, timestamps, horarios DST/ET y volúmenes.

## Almacenamiento privado

- `rgentil2/NQ-Ticks-Dev-2026` ahora será **el único repositorio de datos que las herramientas de desarrollo podrán leer**, con paquetes `2025-10`, `2025-11`, `2025-12` y `2026-01` a `2026-06` después de ejecutar la copia controlada. Su nombre `Dev-2026` se conserva por compatibilidad aunque su rango incluya Q4-2025.
- Los paquetes Q4-2025 se originaron en `rgentil2/NQ-Ticks-Sealed`, junto con los de julio–septiembre y octubre de 2026. **Nunca dar a los trabajos de desarrollo un token con acceso al repositorio `NQ-Ticks-Sealed`**. Copiar únicamente Q4-2025 desde los archivos `.7z.001` ya almacenados en el PC al repo Dev.
- Script idempotente de copia desde PC: `local_nq_tick_2025_2026/copiar_q4_2025_a_dev.ps1`. Solo meses allowlist Q4-2025, checksums locales, no descarga, no recodifica ZIP, no usa GitHub Actions. Paso sin `-Upload` solo verifica, y con `-Upload -LicenseConfirmed` efectúa la copia tras comprobar licencia de redistribución/almacenamiento externo.

## Controles en GitHub público — evitar consumir minutos facturables

- `local_nq_tick_2025_2026/qc_tick_day.py`: lector local o sobre archivo extraído, **streaming**, una única fecha, tres tipos, resumen sin precios ni eventos individuales. Fallar cerrado fuera de `2025-10-01..2026-06-30`, incluidos julio–septiembre. Medida preliminar de dispersión y BBO, no evidencia de órdenes realmente ejecutadas. La conservación de diferencia de timestamps subsegundo no equivale a precisión absoluta del proveedor.
- `.github/workflows/nq-tick-qc-q4-2025-to-jun-2026-manual.yml`: solo `workflow_dispatch` en el **repositorio público principal**, `runs-on: ubuntu-latest`, sin triggers push/cron/PR, sin runners de mayor capacidad. Por defecto solo ejecuta pruebas sintéticas, no usa token ni descarga mercado. Al activar `use_private_market_data=true` consulta **un mes permitido del repo Dev**, extrae **un único día**, compara SHA256 y ejecuta QC. El resultado es agregado y se mantiene separado del código; NO publicar archivos de ticks ni artefactos con series.
- El secreto `NQ_DEV_TICKS_READ_TOKEN` debe ser PAT fine-grained configurado por el usuario con **solo `NQ-Ticks-Dev-2026`, permiso `Contents: Read-only`**. No dar acceso a `NQ-Ticks-Sealed`.
- Los Actions estándar en repositorios públicos son gratuitos bajo la política vigente de GitHub, pero siguen usando CPU y límites de concurrencia. Ejecutar pilotos QC por fecha antes de programar evaluaciones extensivas.

## Criterios para pasar a investigación

Solo tras QC aprobado en octubre 2025, cambios DST y los rollovers de diciembre, marzo y junio, construir estrategias causales juntas con Bid/Ask/Last; conservar cada fallo y comprobar diferencia entre trades y actualizaciones cotizadas. Los resultados exploratorios de 2025 Q4 no se reutilizarán como OOS del estudio antiguo ni se verá el bloque julio–septiembre 2026 antes del congelamiento.