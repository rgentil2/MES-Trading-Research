# NQ T06 — Comparación 233+377 Fibonacci vs 250+400: resultados DEV completos (2026-10-11)

**Estado:** 7/7 trabajos de GitHub Actions SUCCESS. **EXPLORATORY_POST_SELECTION_NOT_OOS**. La familia T06 y sus controles se congelaron antes de esta ejecución en [NQ_T06_233_377_VS_250_400_CONTROL_PREREG_2026_10_11.md](./NQ_T06_233_377_VS_250_400_CONTROL_PREREG_2026_10_11.md). [Run T06 38168307588](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38168307588).

**Fuente:** NQ Tick Last privado Dev, verificaciones SHA256 antes de extraer, 140 sesiones fuente / 135 elegibles, exclusivamente octubre 2025–abril 2026. **No** se accedió a mayo–junio para resultados monetarios ni a julio–septiembre 2026 sellado. Cada registro Last equivale a un evento de barra, no un contrato ni movimiento mínimo de precio. Barras ancladas 08:00 ET, cierres estrictamente anteriores al momento de señal. Comparación de cinco **portafolios alternativos**, no acumulables.

**Padre y simulador sin cambios respecto de T05/T04:** T02 rechazo de rango de apertura con desaceleración de impresiones, señales 09:40–11:10, entrada posterior a señal, 1 NQ, máx. dos trades al día; stops 16–48 ticks, objetivo 2x stop, max 300 segundos. Escenario base: comisiones **supuestas** USD 5 round-trip + 1 tick adverso cada lado; estrés USD 7,50 RT + 2 ticks por lado. Tarifas de firma y fills reales **NO verificados**.

## Resultados en los mismos 135 días de desarrollo

| Variante | Operaciones simuladas | Neto modelo base USD | Neto estrés USD | Neto base / oportunidad original T02 USD | Media neta / trade base USD | Meses con P&L base positivo | Peor mes base USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| **T02_PARENT** | 190 | **+8.420** | +6.860 | +28,26 | +44,32 | 6/7 | −840 |
| **T05_233_AND_377** | 59 | +5.395 | +4.657,50 | +18,10 | **+91,44** | **7/7** | +285 |
| **T06_250** | 130 | +6.775 | +5.460 | +22,73 | +52,12 | 5/7 | −360 |
| **T06_400** | 115 | +4.650 | +3.747,50 | +15,60 | +40,43 | 5/7 | −605 |
| **T06_250_AND_400** | 52 | **+1.275** | +610 | **+4,28** | +24,52 | 5/7 | **−905** |

**Denominador fijo:** las 298 oportunidades originales T02 del período de desarrollo, antes de aplicar filtros 233/377 o 250/400. El valor neto por oportunidad muestra que una mayor media por trade puede venir acompañada de muchas operaciones omitidas. Tampoco prueba capacidad de generar un objetivo mensual fijo; hay variación mensual y baja frecuencia para filtros fuertes.

### P&L base por mes para las dos combinaciones

| Mes | T05 233+377 trades / neto USD | Control T06 250+400 trades / neto USD |
|---|---:|---:|
| Octubre 2025 | 7 / +790 | 8 / +860 |
| Noviembre 2025 | **2 / +900** | 5 / +140 |
| Diciembre 2025 | 14 / +285 | **11 / −85** |
| Enero 2026 | 9 / +630 | 8 / +220 |
| Febrero 2026 | **4 / +510** | **4 / +430** |
| Marzo 2026 | 13 / +1.030 | 9 / +615 |
| Abril 2026 | 10 / +1.250 | **7 / −905** |
| **Total** | **59 / +5.395** | **52 / +1.275** |

**Verificación de reproducibilidad:** la variante T02_PARENT reproduce los 190 trades/+USD 8.420 de T04/T05, y T05_233_AND_377 reproduce exactamente 59 trades/+USD 5.395 de T05. No hubo cambio no declarado de señales, política de riesgo ni costes entre estas carteras.

### Qué sí demuestra este experimento y qué no

- Dentro de esta muestra **ya usada para seleccionar T05**, el ajuste 233+377 obtuvo +USD **4.120** netos simulados de diferencia sobre 250+400, sin abrir holdouts y con políticas comparables. Esta diferencia es **descriptiva de desarrollo**, no una ganancia estadísticamente confirmada ni un efecto causal especial de Fibonacci.
- Cambiar 233→250 y 377→400 cambia **dónde cierran las barras** y la pertenencia a señales, no únicamente su duración media. El efecto podría surgir por el posicionamiento de barras ancladas a 08:00, el comportamiento de los pocos días relevantes o el sobreajuste de la selección T05.
- Las comparaciones se realizaron **posteriormente** a observar T05, en los mismos datos. No afirmar un p-value independiente ni escoger 233/377 como ganador listo para fondeo. Ver [Park e Irwin (2010)](https://onlinelibrary.wiley.com/doi/10.1002/fut.20435) sobre múltiples pruebas de reglas técnicas y sesgo de búsqueda.
- Ninguna variante fue aprobada para cuenta de fondeo. No se ha auditado DD máximo flotante continuo/trailing de la firma, ni sus costes y restricciones reales. T05 tiene **solo 2 trades en noviembre y 4 en febrero**, por debajo de cinco/mes orientativo, y `T02_PARENT` aún presenta riesgo alto.

### Decisión y siguiente fase

1. **Conservar:** T02 como padre; T05 233+377 como filtro exploratorio que mejoró DD/frecuencia selectiva; T06 250+400 como control necesario; T06_250 y T06_400 como ablaciones, sin descartar sus componentes.
2. Integrar la observación distinta de los horizontes del usuario (**233 corto, 4.181 medio, 10.946 amplio**) tras el [QC de 36 días](./NQ_233_4181_10946_MULTISCALE_36_DAY_QC_RESULTS_2026_10_11.md): medianas de 8,39 s / 161,52 s / 429,66 s por barra, respectivamente. Estos horizontes NO se han monetizado aún.
3. **Prerregistrar una nueva familia conjunta**, sin escanear libremente Fibonacci: T02+233+4.181+10.946 versus T02+233+4.200+11.000 bajo el mismo anclaje, señal, stops/costes y riesgo. Comparar opciones contra T02/T05 por oportunidad original y por mes.
4. Antes de abrir validación interna mayo–junio, auditar equity flotante completo, trailing DD por firma y comisiones efectivas. Jul–Sep 2026 sellado.

**Conclusión:** 233+377 funcionó mejor que 250+400 en estos siete meses de desarrollo, **pero no existe evidencia OOS** de que las proporciones Fibonacci sean superiores ni de una renta mensual sostenible.
