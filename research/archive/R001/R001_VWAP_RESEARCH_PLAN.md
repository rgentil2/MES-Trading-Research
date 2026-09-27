# R001 — VWAP Statistical Research Plan

## Pregunta central
¿La distancia estadística del precio respecto al VWAP contiene información sobre los retornos futuros del MES?

## Hipótesis inicial

### H001
Cuando el precio entra a <= -2 desviaciones estándar del VWAP, el retorno futuro a 15 minutos tiene media positiva.

### H002
Cuando el precio entra a >= +2 desviaciones estándar del VWAP, el retorno futuro a 15 minutos tiene media negativa.

Estas hipótesis se evalúan antes de introducir stop loss, take profit, sizing o reglas adicionales de ejecución.

## Periodos congelados

Para reducir el riesgo de sobreajuste:

- **Desarrollo R001:** 2020-01-01 a 2024-12-31.
- **Validación:** año 2025. No se abre mientras no se cierre la decisión de desarrollo.
- **Pseudo-forward:** 2026. Se mantiene fuera del desarrollo y de la primera validación.

Los parámetros de R001 deben congelarse antes de consultar 2025.

## Convención temporal

Los TXT exportados por NinjaTrader utilizan timestamps UTC de **fin de barra**.

Para una barra de 1 minuto:
- 09:31 ET representa operaciones de 09:30:00 a 09:30:59;
- 16:00 ET representa operaciones de 15:59:00 a 15:59:59.

Por eso el RTH usado en R001 es:

- timestamp de barra > 09:30 ET;
- timestamp de barra <= 16:00 ET.

## Definición de VWAP y sigma

Precio base por barra:

```text
Typical Price = (High + Low + Close) / 3
```

VWAP acumulado dentro de cada sesión RTH:

```text
VWAP_t = sum(TypicalPrice_i * Volume_i) / sum(Volume_i)
```

Desviación estándar acumulada y ponderada por volumen:

```text
Variance_t = sum(TypicalPrice_i^2 * Volume_i) / sum(Volume_i) - VWAP_t^2
Sigma_t = sqrt(max(Variance_t, 0))
```

Z-score:

```text
z_t = (Close_t - VWAP_t) / Sigma_t
```

No se usa información futura para calcular VWAP, sigma o z-score.

## Definición de evento

El análisis primario no cuenta cada minuto que permanece fuera de la banda como una observación nueva.

Se define un evento cuando el precio **cruza por primera vez** desde dentro hacia fuera de la banda:

- LOWER: z_t <= -k y z_(t-1) > -k.
- UPPER: z_t >= +k y z_(t-1) < +k.

Pueden existir varios cruces durante una misma sesión.

## Horizontes

Forward returns:

- 5 min;
- 10 min;
- 15 min;
- 30 min.

El retorno se calcula desde el close de la barra del evento hasta el close de la barra futura dentro de la misma sesión y del mismo contrato.

No se permiten retornos que crucen sesión ni rollover.

## Estadísticos mínimos

Para cada banda y horizonte:

- N;
- número de sesiones;
- media;
- mediana;
- desviación estándar;
- probabilidad de retorno favorable;
- intervalo de confianza 95%;
- t-statistic;
- p-value;
- effect size;
- MFE;
- MAE.

Para H001 y H002 se usa un **retorno direccional**:

- LOWER: +1 × forward return;
- UPPER: -1 × forward return.

Un retorno direccional positivo representa reversión en la dirección de la hipótesis.

La inferencia usa errores estándar agrupados por sesión para reducir el efecto de observaciones dependientes dentro del mismo día.

## Segmentación

Para el caso principal de 2 sigma / 15 minutos:

- por año;
- 09:30–10:00 ET;
- 10:00–12:00 ET;
- 12:00–14:00 ET;
- 14:00–16:00 ET.

Regímenes adicionales de volatilidad o pendiente VWAP solo se incorporarán después de revisar el resultado primario, y deberán documentarse como análisis adicionales.

## Robustez

Las bandas quedan congeladas antes de observar validación:

- 1.5 sigma;
- 1.75 sigma;
- 2.0 sigma;
- 2.25 sigma;
- 2.5 sigma.

Un resultado que funciona únicamente en un parámetro exacto se considera sospechoso.

## Gate R001

Continuar a validación únicamente si el desarrollo muestra:

- muestra suficiente;
- efecto económicamente no trivial;
- señal coherente en parámetros cercanos;
- intervalo de confianza compatible con un efecto real;
- ausencia de dependencia extrema de un único año u horario.

Si el desarrollo no supera este gate, H001/H002 se rechazan sin abrir 2025 para intentar rescatarlas.

## Resultado

Pendiente de ejecución automatizada del periodo de desarrollo.
