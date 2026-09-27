# R005 — Morning Opening Range Breakout

## Restricción operativa congelada
- Nuevas entradas permitidas desde la apertura RTH hasta **11:30 ET** inclusive.
- Una posición abierta antes o a las 11:30 puede cerrarse después.
- El análisis sigue siendo intradía dentro de la sesión RTH.

Esta restricción responde a disponibilidad operativa real y se definió antes de ejecutar R005.

## Pregunta
Después del primer cierre fuera del opening range de 15 minutos, cuando ese breakout ocurre como máximo a las 11:30 ET, ¿el MES continúa en la dirección del breakout durante los siguientes 30 minutos?

## Datos
- Desarrollo: 2020-01-01 a 2024-12-31.
- Validación: 2025, reservada.
- Pseudo-forward: 2026, reservado.

## Opening range
Con timestamps de fin de barra de NinjaTrader:
- 09:31–09:45 ET inclusive.
- Deben existir exactamente 15 barras consecutivas.

## Evento
Desde 09:46 ET se toma el **primer cierre de la sesión** fuera del rango:
- UPPER: Close > OR High.
- LOWER: Close < OR Low.

El evento es elegible solo si ese primer breakout ocurre <= 11:30 ET. No se reemplaza por un breakout posterior.

## Outcome
Retorno direccional exacto a 30 minutos:
- UPPER = + retorno futuro 30m.
- LOWER = - retorno futuro 30m.

El horizonte puede terminar después de 11:30 porque la restricción aplica a entradas, no a salidas.

## Hipótesis
### H009
El primer breakout UPPER ocurrido hasta las 11:30 ET tiene retorno direccional medio positivo a 30 minutos.

### H010
El primer breakout LOWER ocurrido hasta las 11:30 ET tiene retorno direccional medio positivo a 30 minutos.

Se evalúan ambos lados simétricamente.

## Gate
Cada hipótesis avanza a 2025 solo si:
- >= 500 eventos;
- >= 500 sesiones;
- q-value BH < 0.05;
- IC 95% clustered completamente > 0;
- media >= 1.0 bps;
- al menos 4/5 años con media positiva.

## Estado
Pre-registrado. Pendiente de ejecución.
