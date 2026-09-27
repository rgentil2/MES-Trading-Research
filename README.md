# MES Trading Research

Laboratorio cuantitativo para investigar y validar estrategias intradía sobre MES.

## Restricción operativa actual
- Entradas desde la apertura RTH.
- **Última entrada permitida: 11:30 ET.**
- Una posición abierta antes o a las 11:30 puede cerrarse después.
- La restricción es operativa, no resultado de optimización retrospectiva.

## División temporal
- 2020–2024: desarrollo.
- 2025: validación OOS reservada.
- 2026: pseudo-forward reservado.

## Flujo
Hipótesis → estadística → candidate → estrategia → backtest con costos → robustez/OOS → Monte Carlo → forward → fondeo.

## Estado
R000–R005 están cerrados y archivados en `research/archive/`.

R005 fue la primera prueba bajo la restricción de entrada <= 11:30 ET. Ninguna de sus dos hipótesis superó el gate, por lo que 2025 y 2026 continúan sin abrirse.

La próxima hipótesis debe pertenecer a una nueva línea de investigación y quedar pre-registrada antes de ejecutarse.
