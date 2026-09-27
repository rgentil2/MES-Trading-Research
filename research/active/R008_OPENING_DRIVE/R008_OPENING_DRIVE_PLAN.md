# R008 — Strong Opening Drive Continuation

## Restricción operativa
- La señal ocurre a las 10:00 ET.
- Entrada potencial <= 11:30 ET.
- Salidas pueden ocurrir después de 11:30.
- Desarrollo: 2020–2024.
- 2025 y 2026 reservados.

## Pregunta
Cuando los primeros 30 minutos de la sesión producen un desplazamiento excepcionalmente grande desde la apertura, ¿el MES tiende a continuar en esa misma dirección durante los siguientes 30 minutos?

## Opening Drive
Con timestamps de fin de barra de NinjaTrader:
- ventana: 09:31–10:00 ET inclusive;
- deben existir exactamente 30 barras continuas.

```text
OpeningDrive = log(Close_10:00 / Open_09:31)
```

## Magnitud excepcional
Se utiliza únicamente información de las 60 sesiones anteriores.

```text
Strong Drive =
|OpeningDrive| >= percentil 70 de |OpeningDrive|
de las 60 sesiones previas
```

No se usan datos futuros ni 2025/2026 para definir el umbral.

## Outcome
Retorno direccional exacto desde 10:00 hasta 10:30:

```text
Directional30 =
sign(OpeningDrive) × forward_return_30m × 10,000
```

Positivo = continuación.

## Hipótesis H013
Un Strong Opening Drive tiene retorno direccional medio positivo durante los 30 minutos posteriores.

## Gate
H013 avanza a validación solo si:
- >= 300 eventos;
- >= 300 sesiones;
- p-value clustered < 0.05;
- IC 95% completamente > 0;
- media direccional >= 1.0 bps;
- al menos 4/5 años con media positiva.

## Descriptivos
- continuation rate;
- separación UP/DOWN;
- magnitud del opening drive;
- rango de los primeros 30 minutos;
- estabilidad anual.

No se redefinirá H013 después de observar el resultado.

## Estado
Pre-registrado. Pendiente de ejecución.
