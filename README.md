# MES Trading Research

> **INVESTIGACIÓN ACTIVA NQ/MNQ — PUNTO DE ENTRADA OBLIGATORIO**
>
> - **[NQ_PROJECT_MASTER.md — objetivo, reglas, estados, decisiones, backlog y prompt para otro chat](NQ_PROJECT_MASTER.md)**
> - **[NQ_RESEARCH_LOG.md — bitácora cronológica completa, resultados y errores T01–T10](NQ_RESEARCH_LOG.md)**
>
> El proyecto conserva MES/ES y el programa histórico NQ, pero **el enfoque activo actual es construir un portafolio de estrategias complementarias NQ**. MES/ES queda en pausa por decisión del usuario. **No hay estrategia aprobada para operar**. Para continuar, leer los dos documentos anteriores y comprobar el último GitHub Actions antes de cambiar estados. La descripción histórica debajo corresponde al proyecto MES original y no sustituye el estado NQ.

---

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

## MES Market State V1 — mapa descriptivo separado

La auditoría [MES-MS1](research/market_state/MES_MS1_PROTOCOL.md) usa exclusivamente
el subconjunto de contratos MES 2020–2024 y conserva R063. Produce atributos
causales a las 09:30 ET, R0–R4, episodios y transiciones. La primera ejecución
pasó las pruebas de causalidad y gobierno de investigación, pero su uso como
filtro de trading sigue pendiente: sólo clasificó 381/1.294 fechas laborables.

Consultar primero la [revisión de cobertura y siguiente trabajo](results/market_state/MES_MS1_REVIEW.md),
el [informe original](results/market_state/MES_MS1_REPORT.md) y el
[artifact completo conservado](results/market_state/MES_MS1_FIRST_RUN.zip).
El subconjunto termina con una preapertura incompleta el 16/12/2024; no cubre
el año completo. No se probaron estrategias, no se modificaron umbrales después
de la ejecución y no se abrió MES 2026. MES 2025 ya es desarrollo reutilizado.
