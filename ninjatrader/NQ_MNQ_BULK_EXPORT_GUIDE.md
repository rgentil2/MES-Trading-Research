# NinjaTrader 8 — exportación NQ/MNQ Minute Last 2020–2026

**Estado:** código actualizado en GitHub; pendiente de compilar y ejecutar en NinjaTrader Desktop 8 conectado a un proveedor histórico. **No se han obtenido los datos de mercado reales desde esta conversación.**

## Qué descarga el exportador

- **Instrumentos:** NQ y MNQ; cada uno con contratos individuales trimestrales marzo/junio/septiembre/diciembre.
- **Cobertura histórica solicitada:** 2020–2026, sin solicitar barras futuras. A fecha 2026-10-08, 2026 solo se descarga hasta la fecha disponible y deberá completarse posteriormente.
- **Solicitudes:** 28 contratos por instrumento de 2020–2026 (**56 en total**). Cuando empiece diciembre de 2026, se añade automáticamente MAR27 de NQ y MNQ (**58 en total**) para completar los últimos días de diciembre de 2026 después del rollover. No se guardan barras de 2027.
- **Datos:** `Minute Last` OHLCV, barras de **un minuto**, ETH, `MergePolicy.DoNotMerge`. **No exporta ticks**.
- **Rangos:** el contrato de marzo puede iniciarse el 1 de diciembre del año anterior; los otros comienzan el primer día del trimestre anterior. Diciembre se solicita hasta el 31, sin asumir que el contrato DEC sigue cotizando todo el mes. Los contratos vecinos se solapan y deberán resolverse mediante un rollover explícito.
- **Proveedor:** puede carecer de minutos antiguos. Un resultado `EXPORTED` **no demuestra cobertura completa**. Contratos con menos de 20.000 barras quedan como `.partial` y `INCOMPLETE`; la cifra solo detecta exportaciones claramente insuficientes. La historia debe superar QC.

## Aislamiento físico de la muestra (NO abrir resultados reservados)

Las barras se guardan según **su año calendario UTC**, no el año de expiración del contrato. Por ejemplo, el contrato NQ MAR25 puede generar un archivo de diciembre 2024 en desarrollo **y otro archivo de enero–marzo 2025 en validación**.

La carpeta de salida es:

```text
%USERPROFILE%\Documents\NinjaTrader 8\NQMNQ_Research_2020_2026\
  development_2020_2024\          <- hipótesis, entrenamiento, investigación
    NQ_03-25_2024_Minute_Last.txt  <- SOLO barras 2024 del contrato MAR25
    NQ_03-24_2024_Minute_Last.txt
    ... NQ/MNQ y sus contratos
  validation_holdout_2025\         <- NO examinar precios, efectos ni P&L
    NQ_03-25_2025_Minute_Last.txt
    ...
  pseudo_forward_holdout_2026\    <- NO examinar precios, efectos ni P&L
    NQ_12-26_2026_Minute_Last.txt
    ...
  completed_jobs\                  <- marcadores para reanudar las descargas antiguas
  download_manifest.csv
```

El exportador puede escribir datos de 2025/2026 para almacenarlos. **El investigador no debe leer esas barras para evaluar direcciones, parámetros, ganancias, regímenes o selección de estrategias** antes de las puertas de validación. El validador incluido solo abre `development_2020_2024`, y permite inventariar **nombres y tamaños** de los holdouts sin abrir su contenido.

## Instalación en NinjaTrader Desktop 8

1. Tener una conexión histórica habilitada para NQ y MNQ.
2. Control Center → **New → NinjaScript Editor**, clic derecho en AddOns → New AddOn.
3. Sustituir la plantilla por el contenido de `ninjatrader/NQMNQBulkMinuteExporter.cs`. Compilar (F5). Puede requerir ajustes menores de API según la versión instalada; **todavía no está compilado en un escritorio real**.
4. Control Center → **New → NQ/MNQ 2020-26 Research Export**.
5. Monitorizar **NinjaScript Output 1** y `download_manifest.csv`. No volver a iniciar mientras esté en curso. Esperar a que todas las solicitudes terminen.
6. Volver a ejecutar más adelante para completar 2026. Contratos anteriores exitosos se omiten mediante marcadores; los contratos activos de 2026 se actualizan.

## Control de calidad **solo de desarrollo**

Desde la carpeta del repositorio:

```bash
python research/nq/validate_ninja_bulk_exports.py --folder "C:\Users\TU_USUARIO\Documents\NinjaTrader 8\NQMNQ_Research_2020_2026" --holdout-metadata
```

El informe compara los archivos 2020–2024 esperados, comprueba formato OHLCV, timestamps, duplicados, volumen y grilla de ticks, y produce `nq_mnq_structural_qc.json`. Por el rollover de diciembre hay **50 particiones de contrato-año de desarrollo** previstas entre ambos instrumentos, si el proveedor ofrece historia completa. Que pasen las pruebas estructurales no demuestra calidad de sesiones, Bid/Ask, estrategia ni ejecución.

La bandera `--holdout-metadata` solo enumera rutas y bytes de 2025/2026: **no lee su contenido**. Los períodos se validan cronológicamente solo cuando las estrategias y el controlador de cartera estén congelados según el protocolo.

## ¿Para qué conservamos 2025 y 2026?

- **2020–2024:** hipótesis NQ-H01...H04, desarrollo de estrategias y controles de robustez.
- **2025:** validación fuera de muestra por candidata **después de congelar hipótesis/reglas**.
- **2026:** pseudo-forward cronológico de la **cartera final completamente congelada**, sin retocar parámetros según los resultados.
- Después: simulación NinjaTrader en tiempo real y eventual compra de MFFU, únicamente si las pruebas son satisfactorias.

## Datos de ticks

Este AddOn todavía **no descarga Tick Last, Tick Bid ni Tick Ask**. Se desarrollará un bloque de exportación de ticks por períodos cortos después de comprobar rendimiento y disponibilidad del proveedor. No mezclar en un único archivo los datos Minute y Tick.

## Documentación oficial

- [NinjaTrader BarsRequest](https://ninjatrader.com/support/helpguides/nt8/barsrequest.htm)
- [MergePolicy / DoNotMerge](https://docs.ninjatrader.com/ninjascript/barsrequest_mergepolicy)
- [Disponibilidad según proveedor](https://ninjatrader.com/support/helpguides/nt8/data_by_provider.htm)
