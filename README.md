# MES Trading Research

Laboratorio cuantitativo para investigar, validar y documentar estrategias intradía sobre Micro E-mini S&P 500 (MES).

## Objetivo

Desarrollar estrategias basadas en evidencia matemática y estadística, validarlas fuera de muestra y avanzar a fondeo únicamente cuando superen criterios predefinidos de robustez.

## Principios de trabajo

1. Primero hipótesis; después estrategia.
2. Toda prueba debe ser reproducible.
3. Comisiones y slippage siempre incluidos.
4. Separar desarrollo, validación y out-of-sample.
5. Registrar también los experimentos rechazados.
6. No modificar reglas después de observar OOS.
7. El P&L no basta: se evalúan expectancy, drawdown, estabilidad y robustez.

## Flujo

```
Hipótesis
  ↓
Investigación estadística
  ↓
Candidate
  ↓
Backtest
  ↓
Robustez / OOS
  ↓
Forward Test
  ↓
Fondeo
```

## Estado inicial

Baseline histórico: Opening Range Breakout (ORB).

- 79 trades
- 31 ganadores / 48 perdedores
- Win rate: 39.24%
- P&L bruto: -$450.00
- P&L neto: -$796.02
- Profit Factor aproximado: 0.84
- Drawdown aproximado: -$1.36k

Se conserva como experimento base y no se considera una estrategia validada.

## Próxima línea de investigación

**R001 — VWAP + desviaciones estándar + hora del día + régimen de volatilidad.**

Ver `research/R001_VWAP_RESEARCH_PLAN.md`.
