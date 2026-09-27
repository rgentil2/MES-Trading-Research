# R007 — Morning Efficient Momentum

## Restricción operativa
- Señales entre 09:46 ET y 11:30 ET inclusive.
- Salidas pueden ocurrir después de 11:30.
- Desarrollo: 2020–2024.
- 2025 y 2026 reservados.

## Pregunta
Cuando el MES presenta un movimiento de 15 minutos excepcionalmente grande y además direccionalmente eficiente, ¿tiende a continuar en la misma dirección durante los siguientes 15 minutos?

R007 es diferente de R004: R004 estudió shocks de 5 minutos normalizados por volatilidad y planteó reversión. R007 estudia un desplazamiento sostenido de 15 minutos y plantea continuación.

## Variables

### Retorno trailing 15m
```text
r15 = log(Close_t / Close_(t-15m))
```

### Magnitud excepcional
Para cada minuto del día:
- se toman únicamente las 60 sesiones anteriores;
- se calcula el percentil 90 de |r15|;
- el evento requiere |r15| >= ese percentil.

### Efficiency Ratio 15m
```text
ER15 = |log(Close_t / Close_(t-15m))|
       / sum(|r_1m| de los últimos 15 minutos)
```

Se exige:
```text
ER15 >= 0.70
```

Un valor cercano a 1 implica que gran parte del recorrido fue en una dirección, no zigzag.

## Evento
- Ventana: 09:46–11:30 ET.
- Deben existir 15 minutos continuos de historia.
- Debe existir un horizonte futuro exacto de 15 minutos.
- Solo se toma el primer evento elegible de cada sesión.

La dirección es el signo de r15.

## Outcome
```text
Directional return 15m =
sign(r15) × forward_return_15m × 10,000
```

Positivo = continuación.

## Hipótesis H012
Después del primer evento de momentum eficiente de la sesión, el retorno direccional medio de los siguientes 15 minutos es positivo.

## Gate
H012 pasa a validación solo si:
- >= 500 eventos;
- >= 500 sesiones;
- p-value clustered < 0.05;
- IC 95% completamente > 0;
- media direccional >= 1.0 bps;
- al menos 4/5 años con media positiva.

## Descriptivos
- continuation rate;
- magnitud de r15;
- ER15;
- separación LONG/SHORT;
- estabilidad anual.

No se usarán para redefinir H012 después de observar el resultado.

## Estado
Pre-registrado. Pendiente de ejecución.
