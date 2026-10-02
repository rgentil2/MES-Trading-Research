# MES Trading Research

Laboratorio cuantitativo para investigar y validar estrategias intradía sobre MES.

## Restricción operativa actual
- Entradas desde la apertura RTH.
- **Última entrada permitida: 11:30 ET.**
- Una posición abierta antes o a las 11:30 puede cerrarse después.
- La restricción es operativa, no resultado de optimización retrospectiva.

## División temporal
- MES: 2020–2025 ya investigado; 2026 reservado para una estrategia completa congelada.
- ES: 2020–2024 desarrollo; 2025 validación de candidato congelado; 2026 pseudo-forward final.

## Flujo
Hipótesis → estadística → candidate → estrategia → backtest con costos → robustez/OOS → Monte Carlo → forward → fondeo.

## Estado
El registro histórico conserva R000–R072. R063 es un componente de volatilidad congelado; no genera una estrategia direccional. R064 fue cancelado antes de ejecutarse.

La investigación nueva se centra en ES. Su bloque ES-B01 permanece pre-registrado y sin ejecutar, sujeto al gate de datos y a especificaciones operativas completas.

Consulta la [política de controles MES/ES](research/RESEARCH_CONTROLS_POLICY.md), el [registro acumulado](results/research_controls/SEARCH_REGISTRY.md) y la [auditoría de robustez](results/research_controls/ROBUSTNESS_AUDIT.md).
Las variantes de una misma pregunta se congelan y evalúan juntas. Los resultados de desarrollo reutilizado siguen siendo exploratorios.
