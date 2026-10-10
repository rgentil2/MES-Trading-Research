# Cotización Databento NQ Last ticks — 2020 a 2025 (consulta real)

**Fecha:** 2026-10-10 UTC. **Ejecución:** https://github.com/rgentil2/MES-Trading-Research/actions/runs/38072803705

El workflow de GitHub Actions consultó la API Databento con el secreto `DATABENTO_API_KEY` del repositorio. **Solo se usaron métodos `metadata.get_cost`, `metadata.get_billable_size` y `metadata.get_record_count`.** No se descargaron series ni se abrieron precios/ticks de 2025.

**Consulta exacta:** `dataset=GLBX.MDP3`, `symbols=["NQ.v.0"]`, `stype_in=continuous`, `schema=trades`, `start=2020-01-01`, `end=2026-01-01` (exclusivo). Horario UTC completo. `NQ.v.0` selecciona un solo contrato principal de NQ según volumen del día anterior; no representa todos los vencimientos ni contratos simultáneos.

| Año | Costo USD | Last trade records |
|---|---:|---:|
| 2020 | 112.14 | 89,593,808 |
| 2021 | 102.63 | 81,991,340 |
| 2022 | 138.23 | 110,435,140 |
| 2023 | 120.26 | 96,078,858 |
| 2024 | 119.25 | 95,271,666 |
| 2025 | 117.51 | 93,877,848 |
| **Total seis años** | **710.02** | **567,248,660** |

- **Tamaño facturable sin comprimir:** 25.36 GiB.
- **Total solo desarrollo 2020–2024:** USD 592.51 (aproximado por suma de valores anuales redondeados a centavos).
- **Consulta directa 2020–2025:** USD 710.02, consistente con la suma anual.
- **No confundir tamaño facturable sin comprimir con tamaño del fichero comprimido descargado.**
- **Cotización, no transacción:** el precio final puede depender de los bytes realmente servidos y del plan; Databento señala que el uso de metadatos es gratuito, mientras que el streaming del mismo dato repetido se vuelve a facturar.
- **Datos reservados:** solo metadatos de precios de 2025, sin abrir registros de mercado, operar sobre ellos ni alterar el holdout.
- **Límite funcional:** `trades` = solo Last (time and sales), no MBO, MBP, Bid/Ask. Los rollovers por mayor volumen pueden diferir del calendario usado antes en NinjaTrader; verificar alineación de contratos antes de uso estadístico.

Script ejecutado: `tools/databento_quote_nq_trades_2020_2025.py`; workflow: `.github/workflows/databento-nq-trades-2020-2025-quote.yml`. Artefacto bruto GitHub: https://github.com/rgentil2/MES-Trading-Research/actions/runs/38072803705

**Recomendación:** no comprar los seis años antes de cotizar también una extracción restringida a la ventana operativa (p. ej. 09:30–11:30 ET) o una muestra pequeña, y antes de confirmar compatibilidad con contratos trimestrales del experimento.
