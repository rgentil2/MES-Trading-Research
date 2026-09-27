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
R000–R004 están cerrados en `research/archive/`.

Experimento activo: **R005 — Morning Opening Range Breakout**.
