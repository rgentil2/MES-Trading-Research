# R009 — Validation OOS 2025

## Estado al congelar este plan

H014 superó el gate de desarrollo 2020–2024 con las reglas pre-registradas:

- N = 325
- media direccional 30m = +5.201 bps
- p = 0.009638
- IC 95% = [1.263, 9.139] bps
- 4/5 años positivos

Ningún dato de 2025 se ha utilizado para seleccionar o modificar la señal.

## Regla congelada

No se modifica R009:

- Gap = Open 09:31 ET / cierre RTH previo del mismo contrato.
- Strong Gap = |Gap| >= percentil 70 de los 60 gaps elegibles anteriores.
- señal al cierre de 09:31 ET;
- retorno direccional exacto a 30 minutos;
- una señal por sesión.

El percentil continúa calculándose de forma online con las 60 sesiones elegibles anteriores. Esto es parte de la regla original, no una reoptimización.

## Warm-up

Para poder calcular el umbral desde el primer día de 2025, el pipeline puede leer sesiones previas de 2024 exclusivamente como warm-up.

Los resultados de validación incluyen únicamente eventos con timestamp en 2025.

## Gate OOS 2025

H014 se considera replicada en 2025 solo si cumple todo:

- >= 50 eventos;
- >= 50 sesiones;
- media direccional >= +1.0 bps;
- p-value clustered < 0.05;
- IC 95% completamente > 0;
- continuation rate > 50%.

Si falla, R009 se rechaza sin abrir 2026.

Si pasa, se congela un plan separado antes de abrir 2026 como pseudo-forward.

## Estado

Pre-registrado antes de ejecutar validación 2025.
