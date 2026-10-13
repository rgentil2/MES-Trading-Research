# ENMIENDA V2 ANTES DE RESULTADOS — T169–T188 ventanas compatibles con motor legado
Fecha 2026-10-13. Documento original V1 permanece intacto para rastreo.
GitHub Actions [38350008027](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38350008027) pasó los tests sintéticos, pero los primeros meses abortaron durante la simulación por 'Signal must occur 09:30-11:30 ET'. No existe artifact de siete meses, PF, ROI ni P&L de la cohorte V1. Se modifica la ventana de evaluación por IMPOSIBILIDAD TÉCNICA de usar el simulador ya congelado en las ventanas anteriores; no por observar retornos.

- **Bloque A T169–T173:** V1 09:10–09:25, no ejecutable en modelo de órdenes. V2 09:40–10:00 ET. Las etiquetas de código A_PRE_ se mantienen como identificador histórico, pero el bloque V2 **NO es premercado**. Esta es una **nueva definición prospectiva**, no una prueba del mecanismo premercado original.
- **Bloque D T184–T188:** V1 11:10–11:35; V2 11:10–11:30 ET para impedir señales no negociables. B y C sin cambios.
- El selector continúa siendo el **primer cierre atómico completo de barra 377 dentro de la ventana**; si no dispara, no se busca otra oportunidad. No se altera ninguna regla direccional de los mecanismos, horizonte 300s, SL24 ticks, TP48 ticks, costes, gestión global, ni T05. Se conservan 20 IDs para la cohorte V2, pero se distingue estrictamente de V1.
- Se sigue requiriendo paridad T05 115 operaciones/$5102,50 estrés/$3952,50 extra10/DD Last1797,50; cero OOS, cero compras de datos, cero 5s para nuevas señales.
- Si nuevos errores de secuencia Last o de ventana impiden ejecución, **FALLAR CERRADO Y REGISTRAR**; no fabricar economía ni ocultar un fallo técnico. Un V2 PASS económico sería únicamente DEV exploratorio.

La fuente de verdad prospectiva al reejecutar es [PREREG V2 JSON](NQ_T169_T188_MONETARY_BLOCKS_PREREG_V2_2026_10_13.json); V1 [original](NQ_T169_T188_MONETARY_BLOCKS_PREREG_2026_10_13.md) jamás se sobrescribe.
