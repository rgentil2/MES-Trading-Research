# R006 — Morning Volatility Compression → Expansion

## Restricción operativa congelada

- Las señales/entradas potenciales deben ocurrir <= 11:30 ET.
- Una posición abierta antes o a las 11:30 puede cerrarse después.
- El horizonte no puede cruzar sesión ni contrato.
- Desarrollo: 2020–2024.
- Validación: 2025 reservada.
- Pseudo-forward: 2026 reservado.

## Pregunta

Cuando la volatilidad realizada de los últimos 30 minutos está anormalmente comprimida para esa misma hora del día, ¿la volatilidad realizada de los siguientes 30 minutos supera su nivel normal esperado?

R006 estudia primero si existe el fenómeno de expansión. No intenta todavía predecir dirección.

## Variables

### Volatilidad realizada actual

Con retornos logarítmicos de 1 minuto:

```text
RV30_actual = sqrt(sum(r_1m^2 de los últimos 30 minutos)) × 10,000
```

Solo se calcula si los 30 minutos son continuos.

### Referencia temporal

Para cada minuto exacto del día se usan únicamente las **60 sesiones anteriores**.

Ejemplo: para evaluar 10:17 ET de hoy, la referencia usa 10:17 ET de las 60 sesiones anteriores.

Esto controla el patrón intradía de volatilidad y evita usar información futura.

### Estado de compresión

```text
Compresión = RV30_actual <= percentil 10
             de RV30_actual en las 60 sesiones previas
             para ese mismo minuto del día
```

Se requiere historial completo de 60 observaciones previas.

## Evento

Ventana de señales:

- desde 10:01 ET, cuando ya existe un historial RTH continuo de 30 minutos;
- hasta 11:30 ET inclusive.

Se toma **solo el primer evento de compresión de cada sesión** para reducir dependencia y solapamiento.

## Outcome principal

Se calcula la volatilidad realizada exacta de los 30 minutos posteriores:

```text
RV30_futura = sqrt(sum(r_1m^2 de t+1 a t+30)) × 10,000
```

Para ese mismo minuto del día también se calcula:

```text
Baseline_RV30_futura = media de RV30_futura
                       de las 60 sesiones anteriores
```

La métrica principal es:

```text
Uplift_RV_% = (RV30_futura / Baseline_RV30_futura - 1) × 100
```

## Hipótesis pre-registrada

### H011

Después del primer evento de compresión de volatilidad de la sesión entre 10:01 y 11:30 ET, la volatilidad realizada de los siguientes 30 minutos es superior a su baseline histórico para esa misma hora.

Formalmente:

```text
E[Uplift_RV_% | compresión] > 0
```

## Gate de desarrollo

H011 avanza a validación 2025 solo si cumple todo:

- >= 500 eventos;
- >= 500 sesiones;
- p-value clustered < 0.05;
- IC 95% completamente > 0;
- uplift medio de RV >= 10%;
- al menos 4 de 5 años con uplift medio positivo.

## Métricas secundarias descriptivas

Sin modificar la hipótesis principal también se reportan:

- retorno absoluto futuro a 30m;
- baseline histórico del retorno absoluto a 30m;
- uplift del retorno absoluto;
- rango high-low futuro de 30m;
- hora del evento;
- RV30 actual;
- umbral de compresión usado;
- estabilidad anual.

Estas métricas no se utilizarán para redefinir H011 después de observar el resultado.

## Estado

Pre-registrado. Pendiente de ejecución.
