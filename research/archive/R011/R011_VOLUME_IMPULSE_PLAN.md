# R011 — High Volume Directional Impulse

## Restricción operativa
- Señales desde 09:36 ET hasta 11:30 ET inclusive.
- Salidas pueden ocurrir después de 11:30.
- Desarrollo: 2020–2024.
- 2025 y 2026 reservados.

## Pregunta
Cuando el MES presenta un movimiento direccional de 5 minutos acompañado por volumen anormalmente alto para esa misma hora, ¿tiende a continuar durante los siguientes 15 minutos?

## Variables

### Retorno trailing 5m
```text
r5 = log(Close_t / Close_(t-5m))
```

### Volumen trailing 5m
```text
V5 = suma del volumen de las últimas 5 velas
```

### Volumen anormal
Para cada minuto del día se usa únicamente la historia de las 60 sesiones anteriores:

```text
HighVolume = V5 >= percentil 80 de V5
             en las 60 sesiones previas
             para ese mismo minuto
```

### Efficiency Ratio 5m
```text
ER5 = |r5| / suma(|r_1m| de los últimos 5 minutos)
```

Se exige ER5 >= 0.70.

Esto busca un desplazamiento relativamente limpio acompañado de participación elevada.

## Evento
- 09:36–11:30 ET.
- historia continua de 5 minutos;
- horizonte futuro exacto de 15 minutos;
- HighVolume;
- ER5 >= 0.70;
- r5 != 0.

Solo se toma el primer evento elegible de cada sesión.

Dirección = signo de r5.

## Outcome
```text
Directional15 =
sign(r5) × forward_return_15m × 10,000
```

Positivo = continuación.

## Hipótesis H016
Después de un High Volume Directional Impulse, el retorno direccional medio de los siguientes 15 minutos es positivo.

## Gate
H016 avanza a 2025 solo si:
- >= 500 eventos;
- >= 500 sesiones;
- p-value clustered < 0.05;
- IC 95% completamente > 0;
- media direccional >= 1.0 bps;
- al menos 4/5 años con media positiva.

## Descriptivos
- continuation rate;
- UP/DOWN;
- volumen relativo al umbral;
- ER5 medio;
- hora del evento;
- estabilidad anual.

No se redefinirán subgrupos después de observar el resultado.

## Estado
Pre-registrado. Pendiente de ejecución.
