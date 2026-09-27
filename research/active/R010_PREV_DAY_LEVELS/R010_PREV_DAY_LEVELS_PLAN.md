# R010 — Previous RTH High/Low Breakout

## Restricción operativa
- Señales desde 09:31 ET hasta 11:30 ET inclusive.
- Salidas pueden ocurrir después de 11:30.
- Desarrollo: 2020–2024.
- 2025 y 2026 reservados.

## Pregunta
Cuando el MES cierra por primera vez por encima del máximo RTH del día anterior o por debajo del mínimo RTH del día anterior durante la mañana, ¿tiende a continuar en la dirección del rompimiento durante los siguientes 30 minutos?

## Niveles previos
Para cada sesión elegible:

```text
PDH = High máximo RTH de la sesión anterior
PDL = Low mínimo RTH de la sesión anterior
```

Solo se usa la sesión anterior si pertenece al mismo contrato. Así se evitan niveles contaminados por rollover.

## Evento
Entre 09:31 y 11:30 ET:

- BREAK_HIGH: Close > PDH.
- BREAK_LOW: Close < PDL.

Se toma únicamente el **primer cierre** de la sesión que esté fuera de cualquiera de los dos niveles.

Si el mercado abre y la primera vela RTH ya cierra fuera del nivel, esa vela puede ser el evento.

## Outcome
Retorno direccional exacto 30 minutos después:

```text
BREAK_HIGH = + forward_return_30m
BREAK_LOW  = - forward_return_30m
```

Positivo = continuación.

## Hipótesis H015
Después del primer rompimiento de PDH/PDL antes o a las 11:30 ET, el retorno direccional medio de los siguientes 30 minutos es positivo.

## Gate de desarrollo
H015 avanza a 2025 solo si:
- >= 500 eventos;
- >= 500 sesiones;
- p-value clustered < 0.05;
- IC 95% completamente > 0;
- media direccional >= 1.0 bps;
- al menos 4/5 años con media positiva.

## Descriptivos
- continuation rate;
- BREAK_HIGH vs BREAK_LOW;
- distancia del cierre al nivel roto;
- hora del rompimiento;
- estabilidad anual.

No se promoverán subgrupos descriptivos a hipótesis nuevas después de observar el resultado.

## Estado
Pre-registrado. Pendiente de ejecución.
