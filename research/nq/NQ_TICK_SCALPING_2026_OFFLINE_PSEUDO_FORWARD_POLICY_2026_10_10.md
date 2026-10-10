# NQ tick scalping 2026 — separación temporal y pseudo-forward HISTÓRICO offline

**Aprobación expresa del usuario:** 2026-10-10. **Carácter:** protocolo **NUEVO y separado** del programa de estrategias H01–H78 desarrollado en 2020–2024. La autorización permite diseñar y estudiar una nueva línea de scalping usando ticks de **enero–junio 2026**, pero **NO** permite consultar resultados ni precios de julio–septiembre antes del bloqueo de estrategia. El holdout 2025 y el 2026 del proyecto original continúan sellados. 2026 octubre–diciembre queda fuera de este estudio.

## Objetivo de la división

Efectuar validación pseudo-forward **offline en datos históricos ya transcurridos**, sin trading en vivo, sin esperar 3 meses calendario y sin entrar al mercado. Por fecha actual 2026-10-10, los meses julio, agosto y septiembre de 2026 están completos. Este experimento se parece a un *historical out-of-sample / pseudo-forward*; **no** equivale a resultados realmente observados en paper-trading prospectivo ni elimina sesgos de selección humana.

| Período fijo, ET (hora de Nueva York) | Papel | Permiso / procedimiento |
|---|---|---|
| **2026-01-01 a 2026-04-30** | **Desarrollo** | Autoriza abrir ticks disponibles para QC, deducción, diseño de estrategias conjuntas, stops, TP, posición NQ y costes, registrar todas las familias y pruebas |
| **2026-05-01 a 2026-06-30** | **Validación interna** | Permite usarla durante investigación con audit trail; por selección adaptativa pasa a ser desarrollo observado y NO pseudo-forward independiente. No usar para declarar OOS final |
| **2026-07-01 a 2026-09-30** | **Holdout histórico pseudo-forward** | **PROHIBIDO abrir precios, registros tick, velas, features derivados, trade P&L o informes** antes del código/estrategia final congelados y de pasar preflight de toda la familia; ejecutar una única prueba final, guardando resultado íntegro positivo/negativo |
| **2026-10-01 en adelante** | **Fuera del estudio** | No analizar; no usar días parciales ni añadir períodos posteriores a posteriori |
| **2025, y 2026 del programa H01–H78** | **Holdouts independientes previos** | No abiertos. Su autorización no se hereda de la investigación nueva de ticks |

**Nota sobre fechas/huso horario:** clasificar sesiones por **fecha de sesión ET** con horario de verano, no por fecha del archivo en UTC ni timestamps de calendario que crucen medianoche. Registrar qué días corresponden al rollover trimestral; no cambiar exclusiones al ver sus P&L.

## ¿Dos o un mes en lugar de tres?

La opción principal está predeterminada: **julio–septiembre, 3 meses completos**. Si antes de examinar los retornos del bloque existe un impedimento objetivo de **cobertura/veracidad de datos**, se admite **una sola** modificación documental de calendario, limitada a **agosto–septiembre (2 meses) o solo septiembre (1 mes)**, o desplazamiento a una ventana consecutiva con cobertura, con razón técnica, recuento de sesiones *sin retornos*, hashes y fecha de cambio. No es válido elegir meses usando su desempeño, eliminar meses con pérdidas ni probar varias ventanas y publicar solo la mejor. Menos meses reducen la independencia y potencia de la evidencia.

## Firewalls de datos y reproducibilidad

1. **Crear proyecto separado**, p. ej. `research/nq_scalping_2026/`, con **ledger, ejecución y directorios de datos aislados**. A partir de H79 o identificadores nuevos, vincular los experimentos al nuevo rol de datos; la política anterior se preserva, sin reaprovechar 2026 para los viejos OOS de H01–H78.
2. Los pipelines de **development** deben utilizar **allowlist explícita enero–junio** y fallar si accidentalmente encuentran julio–septiembre. Pueden consultar únicamente **metadatos de cobertura** del holdout (archivos presentes, fechas, cantidad de bytes/sesiones), **sin cargar ticks, OHLC, features, resultados, retornos ni estadísticas dependientes de precio**. No generar informes de retornos agregados del bloque reservado.
3. Descargar datos 2026 disponibles desde NinjaTrader solo tras piloto pequeño; no afirmar cobertura ni resolución hasta comprobarla. Tick **Last** permite reconstruir trayectoria y precio/volumen; no inferir Bid/Ask o delta agresor de Last. Si falta profundidad, limitar afirmaciones de ejecución, spread y stop; registrar comisiones NQ reales y sensibilidad de costes 1.5×.
4. Precongelar antes de abrir holdout: fuente y QC, tabla contratos/rollover, fechas y sesiones aceptadas, lógica de estrategias **conjuntas** (señal + contexto/régimen + decisión ejecutable), timestamps causales, filtros, inversión de lados, router, riesgo por operación, sizing NQ/MNQ, órdenes, SL/TP, toma de ganancias, time-out, política de gaps, costes, supuestos de Bid/Ask y latencia, resultado primario, múltiple comparación y benchmark, reglas de fondeo. Registrar **SHA256 de código/configuración**, commit y fecha; pasar tests sintéticos y auditar que no haya leído holdout.
5. Congelada la estrategia definitiva, una **única ejecución offline** reproducible sobre **todos los días elegibles del holdout**; prohibido optimizar después de verlos y volver a llamar al resultado pseudo-forward “limpio”. Si falla, conservar informe y registrar modificaciones como nuevas investigaciones que requieren datos futuros realmente no vistos.
6. Informe final: N trades, frecuencia/mes, distribución de beneficio y pérdida, esperanza/PF, DD cerrado e **intradía/flotante**, ratio beneficio/riesgo, estrés 1.5× costos, simulación de límite/trailing de la cuenta fondeada, estabilidad mensual, atribución de cada componente, y criterio de rentabilidad >max(15% CAGR anual, VOO y QQQM con retorno total en período comparable) **solo si duración y benchmark hacen válida la comparación**. Un test de 1–3 meses no basta para asegurar 15% *sostenible anual*; reportar resultado bruto del período y un equivalente anualizado marcado como ilustrativo, nunca prueba de rendimiento anual futuro.
7. **NQ primero** ($20 por punto y $5 por tick), pero si un contrato NQ incumple presupuesto predefinido de riesgo/tamaño para fondeo no forzar 1 NQ para aumentar el retorno; MNQ como contingencia. Distinguir la base nominal de USD50k del dinero realmente pagado en evaluaciones y recibido vía payouts.
8. No subir ZIP/ticks/observaciones licenciadas al **GitHub público**. Solo código, registros y estadísticas agregadas sin redistribución de precios; preservar soporte local y hashes de datos en almacenamiento privado.

## Estado, próximos pasos y restricciones

**Por ahora:** `NEW_STUDY_AUTHORIZED_DEVELOPMENT_JAN_JUN` / `JUL_SEP_PSEUDOFORWARD_SEALED` / `DATA_AVAILABILITY_UNVERIFIED`.

**Primer paso:** piloto de 1–2 días de NQ Tick Last de enero–junio 2026 y validación de resolución, contrato y timestamps. **Segundo:** cobertura de enero–junio; el pseudo-forward no se ejecuta todavía. **Tercero:** registrar estrategia final/objetivos y abrir una sola vez julio–septiembre para simulación histórica offline.

**No implica:** permiso para emplear 2025 en la investigación anterior, apertura anticipada del holdout 2026 H01–H78, ni trading en vivo, compra de datos o compra de fondeo.

Este documento tiene prioridad para el **nuevo estudio tick-scalping 2026** sobre frases anteriores que catalogaban *todo* 2026 como no disponible. Las reglas de congelamiento de estudios antiguos y sus resultados no se reescriben.
