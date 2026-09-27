# R009 — Strong RTH Overnight Gap Continuation

## Restricción operativa
- La señal se evalúa al cierre de la primera vela RTH (09:31 ET).
- Entrada potencial: 09:31 ET, dentro del límite de 11:30 ET.
- Salidas pueden ocurrir después de 11:30 ET.
- Desarrollo: 2020–2024.
- 2025 y 2026 permanecen reservados.

## Definición del gap

Para cada sesión RTH:

```text
Gap = log(Open_09:31 / Close_RTH_sesión_anterior)
```

Solo se consideran sesiones en las que:
- la sesión anterior existe;
- el contrato es el mismo en ambas sesiones;
- la sesión actual tiene una primera vela válida a 09:31 ET;
- la sesión anterior tiene una última vela válida a 16:00 ET.

Esto evita mezclar gaps mecánicos de rollover.

## Magnitud excepcional

La magnitud del gap se compara únicamente contra las 60 sesiones elegibles anteriores:

```text
Strong Gap =
|Gap| >= percentil 70 de |Gap|
de las 60 sesiones previas
```

No se usa información futura.

## Evento

Un Strong Gap produce una sola señal por sesión.

Dirección:
- GAP_UP si Gap > 0.
- GAP_DOWN si Gap < 0.

## Outcome principal

Desde el cierre de la vela 09:31 ET se mide el retorno exacto 30 minutos después:

```text
Directional30 =
sign(Gap) × forward_return_30m × 10,000
```

Positivo = continuación en la dirección del gap.

## Hipótesis H014

Después de un Strong Gap, el MES presenta retorno direccional medio positivo durante los siguientes 30 minutos.

## Gate de desarrollo

H014 avanza a 2025 solo si:
- >= 300 eventos;
- >= 300 sesiones;
- p-value clustered < 0.05;
- IC 95% completamente > 0;
- media direccional >= 1.0 bps;
- al menos 4/5 años con media positiva.

## Descriptivos

- continuation rate;
- gap medio absoluto;
- breakdown GAP_UP / GAP_DOWN;
- gap fill parcial/completo durante 30m;
- estabilidad anual.

No se redefine H014 después de observar resultados.

## Estado

Pre-registrado. Pendiente de ejecución.
