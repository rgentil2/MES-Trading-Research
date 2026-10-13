# D2 SHADOW T133–T168 — ejercicio de cartera; preregistro ANTES de resultados D2

12-oct-2026. Autorizado por el usuario como EJERCICIO aun cuando D1 oficial tiene 0/36 PASS. Esta D2 experimental NO cambia los gates D1/D2 oficiales, no autoriza fondeo y no abre holdouts. Las carteras basadas en resultados positivos de D1 son POST-HOC, sobre los mismos datos DEV, y quedan etiquetadas con sesgo de selección.

## Cinco enrutadores FIJOS por adelantado
- R0_ALL36_ID: elegibles T133…T168, desempate por ID ascendente, sin selección por resultado D1.
- R1_POSITIVE5_ID: elegibles T133, T135, T137, T145, T147, en ese orden (cinco netos positivos con al menos 15 trades proxy D1; POSHOC).
- R2_POSITIVE5_REVERSAL_FIRST: T145, T147, T133, T135, T137, en ese orden (POSTHOC).
- R3_REVERSAL2_ID: T145, T147, en ese orden (POSTHOC).
- R4_T147_ONLY: solo T147, control unitario no diversificado (POSTHOC).

## Ejecución idéntica al D1; no sumar trades solapados
Los 36 mecanismos deciden en el MISMO cierre E377, por tanto máximo UNA posición y UNA entrada hipotética al día de sesión, un contrato NQ o MNQ. Elegir SIEMPRE primer ID cuyo trigger causal sea CASE en lista de prioridad, SIN mirar retornos. Si ese candidato es rechazado por riesgo, modelo o timeout, no tomar otro candidato retrospectivamente. Calcular resultados con EXACTAMENTE el motor D1 del primer grupo Last posterior E, peor precio del grupo +2 ticks adversos en entrada, stop FIRST en timestamp con barrera ambigua, +2 ticks adversos salida, comisiones supuestas NQ US$4 RT/MNQ US$1,50 RT, estrés costos x1,5 y +US$10 RT. Stop/TP de cada candidato congelados; filtro distancia stop 8–400 ticks y riesgo nominal <=US$250 por trade. Proteger contra abrir >1 posición/día, sin asignaciones de contratos múltiples. Cuenta base US$50.000, diario nominal US$500 sería redundante con 1 trade riesgo US$250; pérdidas reales podrían exceder riesgo nominal por gaps y deslizamiento. NO afirmar fills reales.

## Datos, integridad, outcome y comparaciones
Usar únicamente siete meses Last DEV existentes Oct2025–Abr2026, 140 sesiones fuente/135 READY, sin más datos, sin 5 segundos y sin abrir MAY–SEP 2026 sellados. Ejecutar en UN SOLO runner privado; suprimir Last y filas por día al finalizar, publicar SOLO agregados seguros. Validar (a) máscaras D0 originales CASE/CONTROL/OTHER/MISSING para los 36 contra congelado de Action 38325498797, (b) reconstrucción de N proxy trades y PnL US$ por cada estrategia contra summary SAFE original D1 de Action 38326216082 con tolerancia 0,01 USD, antes de emitir comparación D2.

Por router reportar N días señal, conflictos >=2 CASE, N trades proxy de cuenta, rechazos/censuras, contribución por ID y por instrumento, win rate, neto USD base/x1,5/+US$10RT, esperanza/trade, PF, peak-to-trough DD, peor día y pérdida excedente nominal, retorno simple sobre US$50.000 NO anualizado (135 sesiones seleccionadas, no calendario completo), frecuencia por semana, meses positivos/concentración, Q4-2025 versus ene–abr2026 (PERIODOS DEV REUSADOS, no OOS). Bootstrap por día moving-block 10.000 réplicas L5, IC90 DESCRIPTIVO, ninguna q/p confirmatoria.

Check diagnóstico de criterios económicos SIN EFECTO DE APROBACIÓN: >=15 operaciones proxy; neto y esperanza >0; PF>=1,25; ambos estrés positivos; Q4 y ene–abr positivos; DD <=US$1.500; concentración mensual máxima <40% del total de meses positivos; >=1 operación/semana es deseable, no hard gate. Comparar con aspiración 12–15% anual solo cualitativamente; no anualizar los 135 días de muestra condicionada.

Este es análisis POST-HOC de sensibilidad y cartera, no confirmación de alpha. No modificar prioridades tras ver el resultado y no presentar la mejor cartera como seleccionada anticipadamente por validez estadística. D2 OFICIAL mantiene cero elegibles/promovidas, sin autorización para fondeo. Documento creado ANTES de observar cualquier resultado D2.
