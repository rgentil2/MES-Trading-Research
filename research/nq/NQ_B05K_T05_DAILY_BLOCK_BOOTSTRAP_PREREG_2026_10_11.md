# NQ-B05K — preregistro de evaluación T05 con 135 retornos diarios y bootstrap de bloques

**Fecha:** 2026-10-11 Colombia / implementación runner puede ocurrir 2026-10-12 UTC. **ESTADO: PROPUESTA DE ANÁLISIS ESTADÍSTICO B, NO HIPÓTESIS ALFA NUEVA**. Prerregistro de procedimiento y de todo umbral **ANTES** de reconstituir cualquier retorno por día desde los archivos existentes.

## Única pregunta
¿El P&L neto simulado de **T05-377 congelada**, expresado **por sesión elegible** e incluyendo los días sin trade, muestra precisión estadística exploratoria suficiente para merecer más investigación, bajo la dependencia temporal por semanas y coste de estrés ya decidido? **No evaluamos un disparador nuevo.** Como diagnóstico de sensibilidad fija, repetir estadísticos sobre la **misma trayectoria fija** añadiendo US$10 RT, pero no reoptimizar señales/stops/horarios ni cambiar admisión diaria.

## Fuente y restricción
- Exclusivamente **siete archivos NQ Last DEV YA almacenados** en releases privados, octubre 2025–abril 2026, mismo SHA256 y rutas de scripts que produjeron H02/T05. Lectura/transporte técnico del mismo release ya disponible **NO** es nueva adquisición a proveedor; no descargar/adquirir histórico distinto, no Replay/L2, no leer T 2026 mayo–septiembre ni programa H sellado.
- Constructor congelado: `frozen_t05` en `nq_b05h01_trade_expansion_month.py` y `risk_trace` solo T05 (`BASE`) en `nq_b05h02_reversion_month.py`, sin cambiar T05 ni generar señales de estrategia con código nuevo. El baseline histórico T05 usa sus 5s como definición YA congelada (instrucción de no usar 5s aplica a señales NUEVAS).
- Reconciliación **obligatoria**: 140 días fuente / **135 elegibles** / 5 excluidos por regla T05 congelada. N trades **115**, P&L estrés **+$5.102,50**, P&L estrés+$10 fijo **+$3.952,50**, y todos los meses en orden: 
  - 2025-10: 15 trades / +$137,50
  - 2025-11: 8 / +$760
  - 2025-12: 22 / +$1.450
  - 2026-01: 19 / +$1.572,50
  - 2026-02: 13 / −$827,50
  - 2026-03: 21 / +$1.372,50
  - 2026-04: 17 / +$637,50.
- Almacenar resultados diarios solo **dentro del runner temporal** en directorio oculto NO subido como artifact ni enviado al log; reportar públicamente únicamente estadísticas agregadas n/IC/p/LOMO por meses/semana y hash de control NO datos por fecha. Borrar los archivos Last licensiados y vectores diarios SIEMPRE con cleanup; no subir ganancias/días/timestamps ni logs por trade.

## Estadística CONGELADA (no escoger parámetros por outcome)

1. `N_sessions =135` y `N_trades=115` reportados por separado; `N_active_days` se mide, `N_eff = unknown`. Ventana total 7 meses, ~28 semanas contiguas (se reportan semanas efectivas sin inventar N independiente).
2. Vector de P&L diario de longitud 135 en orden de calendario ET y **cero para sesiones elegibles sin ejecución**. No incluir los cinco días fuente excluidos como cero: elegibilidad congelada y documentada. Testear parity a mes; NO resultados por fecha publicados.
3. Escenario principal `STRESS` costo comisión $7,50RT +2 ticks por lado, misma ruta y stops congelados. Sensibilidad `STRESS+$10` RT de contabilidad de trayectoria fija, no recalcula stops/fills/gates; **nunca declarar simulación bajo diferente política de admisión**.
4. Bootstrap de bloques móviles **NO CIRCULAR** de sesiones consecutivas **B=10.000**, semilla `20261011`; muestras de inicio uniformes entre 0 y n-L inclusive; concatenar bloques hasta n sesiones, truncar sobrante. Reportar **IC bilateral 90% de la MEDIA USD/SESIÓN** (percentiles 5 y 95 de 10k medias); **p unilateral exploratorio** bajo H0 media<=0, distribución bootstrap centrada en media observada: `p = (1 + count(bootstrap_mean - observed_mean >= observed_mean)) / (B+1)`. P no confirmatorio por selección adaptativa y n pequeño.
5. **L=5 sesiones** como elección PRINCIPAL; sensibilidad obligatoria L=3 y L=10 (mismo B y semilla derivada `20261011 + L` por escenario) **sin elegir el más favorable**. Reportar error estándar de distribución de medias y amplitud de IC. MDE aproximado (α unilateral 0,10; potencia 80% bajo normalidad) `(1.28155+0.84162)*bootstrap_SE`, claramente solo orientación, NO prueba de poder real.
6. Reportar P&L total, media USD/sesión, mediana diaria, N positivo/negativo/cero, meses positivos y **LOMO 7/7** rango P&L sin cada mes, comparado con gate económico y PF/DD congelado; no usar LOMO para elegir horas/meses a operar.
7. **Gate de informe:** `IC90_lower_gt_0` puede marcar `YES/NO` solo como DESCRIPTIVO; `BH_q = N/D`, `Holm=N/D`, `3/5 años=N/D`. Decisión superior **`IN_SAMPLE_DEPENDENCE_DIAGNOSTIC_ONLY`**, incluso con IC favorable. Si cualquier paridad mensual 115/+5102,50 fallase o hubiera fallo duro de ejecución, **FAIL CLOSED y NO PUBLICAR diagnóstico como válido**. Test de signo o bootstrap NO hacen T05 viable para fondeo.
8. Antes de ejecutar, publicar/ejecutar pruebas sintéticas que demuestren que cero-trade permanece 0, dependencia de bloque frente iid, intervalos deterministas por seed, prohibición de meses H/T y ausencia de outputs diarios en los artifacts.
9. El proyecto conserva q BH/Holm de familias y Gate 1 H original, T05 estrés+$10 PF1,23717 y adversidad de DD por timestamps. **No comprar fondeo** a partir de resultados in-sample.

## Seguimiento
Al completar registrar resultados en `research/nq/NQ_B05K_T05_DAILY_BLOCK_BOOTSTRAP_RESULTS_2026_10_11.md`, `NQ_PROJECT_MASTER.md`, `NQ_STATISTICAL_HYPOTHESIS_SCORECARD.md`, `NQ_RESEARCH_LOG.md`. Si workflow no completa o no cumple integridad, registrar honestamente fracaso sin deducir p/IC90 de meses.
