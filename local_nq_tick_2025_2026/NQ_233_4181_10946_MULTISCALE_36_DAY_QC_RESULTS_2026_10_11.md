# NQ multi-escala de barras por operaciones Last: 233 / 4.181 / 10.946 — QC de 36 sesiones (2026-10-11)

**Estado: 9/9 trabajos de GitHub Actions SUCCESS, SOURCE ACTIVITY DIAGNOSTIC ONLY. NO rentabilidad, NO identificación del mejor Fibonacci, NO validación de estrategia.**

[Workflow y logs](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38167981413) · Código [qc_nq_multiscale_tick_bars.py](./qc_nq_multiscale_tick_bars.py) · Tests [test_qc_nq_multiscale_tick_bars.py](./test_qc_nq_multiscale_tick_bars.py)

## Alcance y precisión

- 36 sesiones ya seleccionadas en el manifiesto de estudio (cuatro fechas por mes, Oct 2025–Jun 2026).
- **8.484.232 registros Last** procesados en cuatro horas ET (08:00–12:00) en total. Las duraciones reportadas abajo corresponden solo a cierres de barras entre **09:30 y 11:30 ET**.
- Definición: una barra n-tick contiene **n filas Last registradas**, y NO n cambios del precio, contratos negociados ni n milisegundos. El volumen de contratos se conserva internamente sin publicarse.
- Anclaje: reiniciar a **08:00 ET** por cada día de archivo; una sesión ETH completa de NinjaTrader podría producir barras con otro punto inicial. No elegir anclajes por P&L.
- Solo barras completamente cerradas y de timestamp estrictamente anterior son elegibles en una eventual señal; conservar el tick Last individual como fuente de ejecución/riesgo.
- Mayo–junio: únicamente diagnóstico de actividad, **no P&L** ni selección de estrategias; julio–septiembre 2026: sellados.

## Tiempo real que representa cada barra: mediana entre las medianas de 36 días

| Registros Last por barra | Duración mediana 09:30–11:30 | Rango intercuartílico entre días | Barras cerradas en 2h, mediana/día | Contexto cerrado disponible a 09:30 |
|---|---:|---:|---:|---|
| **233** (propuesta) | **8,393 segundos** | 7,282–9,814 s | 746 | 36/36 días |
| 240 (control próximo) | 8,609 segundos | 7,498–10,088 s | 724 | 36/36 |
| **4.181** (propuesta) | **161,520 segundos = 2 min 41,5 s** | 136,556–183,463 s | 41,5 | 36/36 |
| 4.200 (control próximo) | 159,596 segundos | 138,951–184,765 s | 41,5 | 36/36 |
| **10.946** (propuesta) | **429,655 segundos = 7 min 9,7 s** | 369,679–488,197 s | 16 | 36/36 |
| 11.000 (control próximo) | 425,775 segundos | 374,483–491,308 s | 16 | 36/36 |

Las barras de 233, 4.181 y 10.946 capturan **tres horizontes de actividad distintivos** (segundos, ~2,7 minutos y ~7,2 minutos para este conjunto). Esto NO significa que Fibonacci sea superior: los controles 240, 4.200 y 11.000 producen duraciones casi idénticas.

## Contexto 09:30 ET y peligro de antigüedad

Mediana entre días del tiempo desde el último cierre de la barra de cada escala antes de abrir:

- 233: **3,56 segundos**.
- 4.181: **135,188 segundos**.
- 10.946: **717,136 segundos (~11 min 57 s)**.

El 10.946 disponible a 09:30 puede describir un bloque de transacciones cerrado mucho antes de la apertura, por lo que debe combinarse con estructura reciente/volatilidad, no tratarse como indicador puntual de últimos segundos. El estudio muestra que *existe* una barra cerrada en 36/36 días, NO que el contexto sea óptimo o independiente.

## Implicaciones falsables

1. **Basal:** mantener Tick Last como fuente de datos en bruto para trayectoria, costes, gaps, SL/TP; usar barras de 233 como contexto de corto plazo, 4.181 medio y 10.946 amplio. Contexto diario exige velas completas de **sesión anterior**, que el archivo 08:00–12:00 por sí solo no provee.
2. No presentar T05 233/377 como refutación o aprobación de 4.181/10.946: T05 responde a otra pregunta y utiliza ~segundos como contexto dual, mientras este análisis demuestra una separación real de escalas. No calibrar retrospectivamente para maximizar profit.
3. Prueba de falsación directa de Fibonacci (T06) ya **prerregistrada** en [NQ_T06_233_377_VS_250_400_CONTROL_PREREG_2026_10_11.md](./NQ_T06_233_377_VS_250_400_CONTROL_PREREG_2026_10_11.md). Diferencias de P&L entre n próximos deben evaluarse por *oportunidad del padre*, trades/mes, costes adversos y drawdown, no solo ganancias acumuladas.
4. Próxima familia estrictamente **nueva** para 233/4.181/10.946: definir filtro causal con tres contextos, compararlo con 233/4.200/11.000, con T02 padre y con T05 233/377. Bloquear parámetros antes de observar sus outcomes y contabilizar todas las variantes/corrección por selección. Congelar reglas antes de abrir mayo–junio.

### Fuentes y límites
NinjaTrader distingue **Tick bars** por número de ticks recibidos de **Volume bars** por contratos negociados: [NinjaTrader 8 Bar Types](https://ninjatrader-devel.ninjatrader.com/support/helpguides/nt8/bar_types.htm). White/Sullivan/Timmermann sobre riesgo de probar muchas reglas: https://cepr.org/publications/dp1976. Esto justifica **comparaciones de control predefinidas** y validación fuera de desarrollo, no valida ninguna combinación Fibonacci.

**Estado actual:** 36/36 sesiones analizadas con éxito, ninguna de 2026-07 a 09 abierta, sin utilidades/ROI estimados en este QC.
