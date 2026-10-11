# NQ-B02 — Conciliación REAL independiente NQ Minute Last ↔ Tick Last

**Fecha:** 2026-10-11. **Resultado:** `INDEPENDENT_MINUTE_MATCH_240_OF_240_ONE_DEV_DAY`. **Gate del piloto de integridad de fuente: PASS.** No es validación de ejecución, rentabilidad, ni prueba OOS. Documento relativo al [prerregistro B02](NQ_B02_CROSS_SOURCE_PILOT_2026_10_11.md).

## Identidad y ventanas congeladas antes de ver resultados

- **Contrato:** NQ 12-25 de NinjaTrader, sin mezclar NQ con MNQ ni rolling/backadjustment.
- **Fecha:** miércoles **2025-10-15** (America/New_York, EDT UTC-4).
- **Ticks Last:** intervalos 08:00–12:00 ET, agrupados por inicio de cada minuto.
- **Minuto original:** barras etiquetadas por **fin** del minuto, 08:01–12:00 ET. No se probó arbitrariamente etiquetado alternativo para maximizar concordancia.
- **Comparación exacta:** 240 tuplas cronológicas `[indice_minuto, apertura_en_ticks_NQ, máximo_en_ticks, mínimo_en_ticks, cierre_en_ticks, volumen]`. Multiplicador de conversión 4 ticks de precio por punto NQ; serialización canónica JSON compacto y digest SHA-256 de todo el día.
- Se validaron rango, orden de timestamps, precios en grid, 240 minutos sin huecos y volumen total.

## Evidencia REAL de DOS archivos distintos, procesados separadamente

| Fuente | Ubicación y ejecución | Velas | Volumen sumado | SHA256 sobre 240 tuplas OHLCV |
|---|---|---:|---:|---|
| Minute Last original | [Workflow privado NQ-Tick-Data 38179138403](https://github.com/rgentil2/NQ-Tick-Data/actions/runs/38179138403) — **SUCCESS** | **240** | **262.422** | `f6c426c60d5691ddd8341db2c1bcf9f944b283d8533497f0d4efdd11e82afb5a` |
| Tick Last DEV | [Workflow público código/privado origen 38179259265](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38179259265) — **SUCCESS** | **240** | **262.422** | `f6c426c60d5691ddd8341db2c1bcf9f944b283d8533497f0d4efdd11e82afb5a` |

**Conclusión:** los hashes de serialización canónica son **idénticos**, y la alineación temporal y el volumen también. Para este contrato y fecha, se acreditó igualdad exacta de **apertura, máximo, mínimo, cierre y volumen en los 240 minutos**, siempre que ambos scripts de canonización sigan las definiciones documentadas. A diferencia de las 34 pruebas sintéticas anteriores, el piloto usó **ambos archivos reales por separado**.

### Procedimiento reproducible y repositorios

1. **Minuto ORIGINAL aislado en repo PRIVADO** `rgentil2/NQ-Tick-Data`, release histórico `nqmnq-minute-2020-2026-v1`. La acción verificó tamaño 65.405.000 bytes y SHA256 de ZIP `a85a37eb66abda2621cab8110af30d8afb115f652dafc02cc76c7577b2280bc8`; identificó SOLO NQ 12-25 y leyó únicamente su miembro dentro del ZIP, filtrando **solo 15/10/2025**. Script `tools/nq_minute_single_day_digest.py`, commit de código privado `efbe5ee959c954152f97fea0a80a04cfb2354e73`; workflow privado commit `138745fd06028dda18b3e6ffe5f60e1275ca82af`.
2. **TICK DEV separado** en repo privado `rgentil2/NQ-Ticks-Dev-2026` (no Sealed), descarga verificando SHA256 de `NQ_2025-10_Last.7z.001`; extracción limitada a `20251015`. Script público de agregación `nq_b02_tick_single_day_digest.py`, commit `40284861df8af7ff3eb0c6f724676dae67bd8ee3` y tests `test_nq_b02_tick_single_day_digest.py`, commit `9f0f683a2de2b3450fc28e517137f063d1fda5bc`. Se añadió el piloto a workflow existente de integridad, commit `0431962d0f2f5a3a9bb8e0eca6811564f474b4e7`. En el run 38179259265 finalizaron **SUCCESS todos los trabajos**; para B02 el job relevante es `source-last (2025-10-15)`.
3. **Privacidad:** no se copió ZIP histórico completo ni archivo independiente minuto al repositorio público ni a sus runners. No se publicaron barras individuales, precios ni eventos Last. Las salidas contienen únicamente SHA256, recuentos y metadatos del día. No se abrieron datos del repo `NQ-Ticks-Sealed`.
4. **Separación de programas:** aunque 2025 es holdout del programa histórico H, este acceso se limitó a QC de la fuente del programa **T** en una fecha DEV previamente acordada; no se examinó ningún retorno, señal o rendimiento del programa H. Mayo–junio de T continúan cerrados para outcomes y julio–septiembre sigue sellado.

## LIMITACIONES CRÍTICAS

- **Es un día**, no 135 días ni todos los rollovers. No se puede proclamar calidad universal, ni independencia entre *proveedores*: ambos archivos proceden de las exportaciones de NinjaTrader, aunque son fuentes de archivo separadas y se compararon independientemente.
- La coincidencia OHLCV no prueba orden exacto de trades con igual timestamp, Bid/Ask, liquidez, fills de limit/market/stop, ruta intrabar ni slippage. Por ello **NO cambia** el P&L estimado de T05-377 (115 trades, USD +6.220 base / +5.102,50 estrés) ni el DD teórico T08.
- No prueba que cifras comparables se mantengan tras rollover; ampliar a fechas con rollovers es una auditoría QC posterior, no un ajuste optimizado.
- El hash impide examinar diferencias campo a campo si aparece un mismatch futuro; entonces habrá que ejecutar un diagnóstico privado agregado y documentar diferencias, no importar bars licenciados al repositorio público.

## Decisión y backlog

- **NQ-B02 piloto original 2025-10-15:** **COMPLETADO (PASS de integridad de OHLCV para un único día)**.
- **NQ-B01/T10:** COMPLETADO como auditoría; cobertura BBO estrictamente previa sólo **113/115 (98,26%)**, no 100%, y NO es confirmación de fills.
- **NQ-B03:** siguiente paso técnico recomendado: auditar cómo las discrepancias Last/BBO y la secuencia de quotes afectan al modelo de ejecución/riesgo de T05 sin reconstruir precios garantizados ni elegir meses favorables.
- **NQ-B05:** futura segunda familia causal verdaderamente distinta; comparar *aportación neta incremental* al portafolio NQ T05 bajo el mismo presupuesto de riesgo.
- **NQ-B12 (opcional, a preregistrar):** ampliar conciliación independiente de minuto↔ticks a fechas de cambio de contrato y estaciones diferentes mediante política de selección basada SOLO en manifiestos y sesiones, no retornos.
- **Holdouts:** ningún cambio ni autorización de apertura.

**Estado final:** `B02_PILOT_MATCH_ONE_DAY_ONLY`, no `FILL_VERIFIED` ni `STRATEGY_VALIDATED`.
