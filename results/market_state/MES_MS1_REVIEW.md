# Revisión de la primera ejecución — MES-MS1

El mapa causal está construido y su primera ejecución pasó. Su aceptación como
filtro de trading queda **PENDIENTE**. No se ha probado una estrategia ni la
existencia estadística de cuatro regímenes; R1–R4 son categorías operativas.

## Resultado y qué significa

Se utilizaron 1.738.188 barras y los veinte contratos MES de 2020–2024.
El calendario de cobertura genera 1.294 fechas laborables: 381 clasificadas
R1–R4 (29,4%) y 913 R0 (70,6%). De las últimas, 163 son ventanas de alerta CUSUM;
las otras 750 corresponden a inicialización, cobertura o incertidumbre de bandas.
Se registraron 49 alertas, 126 episodios R1–R4 y 358 episodios R0.

Todo 2020 quedó R0: no se abrió un historial anterior para rellenar la ventana
de 252 fechas. En 2021–2024 se clasificaron 381/1.032 fechas (36,9%). Por tanto,
la baja cobertura no se explica únicamente por el calentamiento inicial.
La mediana observada de los episodios clasificados es 2–3 fechas. El tamaño y
la dependencia de estas muestras requieren atención antes de investigar efectos.

| Motivo principal R0 | Fechas | Interpretación |
|---|---:|---|
| Inicialización de contrato | 228 | Faltan 14 RTH completas del contrato actual |
| RTH anterior incompleta | 169 | Incluye sesiones cortas o barras ausentes; no se distinguen todavía |
| Ventana de alerta CUSUM | 163 | Monitor heurístico, sin falsas alarmas calibradas |
| Banda incierta/referencia degenerada | 153 | No había memoria válida al caer en P33–P67 |
| Inicialización de referencia | 150 | Ventana/calibración causal insuficiente |
| Cobertura overnight | 32 | No cumple extremos y mínimo de barras |
| Sin overnight | 18 | No se dispone del intervalo |

Estos conteos son exclusivos según la precedencia del protocolo; una fila de
alerta puede tener además alguna componente incierta. Hay 542 fechas con ambas
componentes conocidas antes de la precedencia R0. Ningún conteo expresa trades.

## Límite de calendario encontrado

Los archivos elegidos terminan el 16/12/2024 a las 00:00 ET, no el 31/12/2024.
La última fecha genera una preapertura incompleta; faltan las últimas semanas
del año en este subconjunto. El sexto fold tiene 121 fechas observadas, no el
semestre completo. Parte del calendario 2024 está en el contrato MAR25 bajo el
rollover de la fuente. **No se abrió ese contrato.**

No sería correcto comunicar esta ejecución como cinco años completos con
clasificación útil en todos ellos. La restricción de veinte contratos preservó
el límite de fuentes declarado, pero limita cobertura de fin de 2024.
Un eventual protocolo separado para completar sólo fechas 2024 desde otro
contrato debe resolver primero la lectura y separación física de registros,
sin calcular características ni resultados 2025. Esto no cambia retrospectivamente
el alcance de la primera ejecución.

## Decisión y siguiente trabajo

Conservar esta V1 y sus resultados exactos; no cambiar P33/P67, CUSUM ni cobertura
para aumentar artificialmente las fechas clasificadas. Antes de usar R0 como
filtro o añadir hipótesis, hacer una auditoría de disponibilidad:

1. Separar calendario CME y sesiones legítimamente cortas de barras faltantes,
   especialmente en los 169 casos de RTH anterior incompleta.
2. Medir qué historial del mismo contrato está disponible antes de cada rollover
   en los archivos de origen, y si la selección continua descartó información
   que ya era observable; fijar una política causal de roll y calentamiento.
3. Resolver explícitamente el alcance de las últimas semanas de 2024.

Luego, si una V2 es necesaria por razones de datos, especificarla antes de
ejecutarla, conservando V1. Evaluar primero disponibilidad y comportamiento de
alertas, sin P&L, y registrar cualquier selección posterior vinculada a outcomes.
Sólo después corresponde el primer fenómeno preregistrado con control comparable.

Los seis folds de esta entrega son un esquema y conteos de cobertura. No se
ejecutaron walk-forward de estrategia, CPCV, PBO, DSR, HMM, BOCPD o Bai–Perron.
R063 y resultados históricos no cambian. MES 2025 ya fue investigado; MES 2026
permanece reservado para una estrategia completa congelada.

## Evidencia de ejecución

- Código y protocolo congelados antes de datos: commit
  `12e41e6e634ff10c0132913add5f0c67e84c9c94`.
- Auditoría descriptiva: https://github.com/rgentil2/MES-Trading-Research/actions/runs/37131313227
  — éxito; 11 pruebas de causalidad/datos; invariancia en siete prefijos reales.
- Controles acumulados: https://github.com/rgentil2/MES-Trading-Research/actions/runs/37131313216
  — éxito; 84 pruebas y gobierno de investigación aprobado.
- Artifact original ID `11276459862`, ZIP SHA256
  `2686e0e6ef78b8de03466a3b54a486bfd96237e781a3436ab93de28d9ba5a069`.

Los seis archivos MES_MS1 del artifact se guardan sin alterar sus bytes.
Esta revisión es una anotación posterior de cobertura y autoridad, no una
revisión de las reglas congeladas.
