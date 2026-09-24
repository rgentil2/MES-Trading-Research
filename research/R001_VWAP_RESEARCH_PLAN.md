# R001 — VWAP Statistical Research Plan

## Pregunta central
¿La distancia estadística del precio respecto al VWAP contiene información sobre los retornos futuros del MES?

## Hipótesis inicial

### H001
Cuando el precio se encuentra a <= -2 desviaciones estándar del VWAP, el retorno medio futuro a 15 minutos es positivo.

### H002
Cuando el precio se encuentra a >= +2 desviaciones estándar del VWAP, el retorno medio futuro a 15 minutos es negativo.

Estas hipótesis deben evaluarse antes de introducir stop loss, take profit o reglas de ejecución.

## Variables

### Explicativas
- distancia precio-VWAP;
- z-score respecto al VWAP;
- hora del día;
- realized volatility;
- dirección/pendiente del VWAP;
- volumen relativo.

### Resultados
Forward returns:
- 5 min;
- 10 min;
- 15 min;
- 30 min.

## Estadísticos mínimos
- N;
- media;
- mediana;
- desviación estándar;
- percentiles;
- probabilidad de retorno positivo;
- intervalo de confianza;
- t-statistic;
- p-value;
- effect size;
- MFE;
- MAE.

## Segmentación
- 09:30–10:00 ET;
- 10:00–12:00 ET;
- 12:00–14:00 ET;
- 14:00–16:00 ET;
- baja / media / alta volatilidad;
- pendiente VWAP positiva / neutra / negativa.

## Robustez
Comparar bandas cercanas:
- 1.5 sigma;
- 1.75 sigma;
- 2.0 sigma;
- 2.25 sigma;
- 2.5 sigma.

Un resultado que funciona solo en un parámetro exacto se considera sospechoso.

## Gate R001
Continuar únicamente si:
- existe muestra suficiente;
- el efecto persiste en parámetros cercanos;
- el intervalo de confianza no sugiere un efecto trivial;
- el resultado no depende de un único periodo u horario;
- sobrevive a validación fuera de muestra.

## Resultado
Pendiente.
