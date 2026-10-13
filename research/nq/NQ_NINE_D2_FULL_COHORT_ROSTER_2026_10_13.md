# Nueve hipótesis — cohorte activa D2 exploratoria, registro de evidencia y exclusiones

**Nueva decisión 2026-10-13 del usuario:** incluir T224 con las ocho antiguas, excluir de la cohorte *activa* T210/T212/T215/T217 (no borrar resultados). Las N de H son 2020–24 NQ1min; T son 2025-10 a 2026-04 NQ Last. **Nunca calcular PnL o DD de nueve sumando filas.**

| ID | Mecanismo / dependencia | Unidad y período probado | N trades proxy | Neto USD del padre | PF padre | DD padre USD | Estado evaluativo en D2 |
|---|---|---|---:|---:|---:|---:|---|
| H09 | Continuación de gap | 1NQ 2020–24 minuto | 173 | ≈+18.874 | 1,369 | 8.122 cerrado | Padre H, DD demasiado alto 50K, periodo no común |
| H56 | Reversión premercado | 1NQ 2020–24 minuto | 100 | +8.697,98 | 1,269 | 3.599,09 cerrado | Padre H, N insuficiente, periodo no común |
| H69 | Router OR H09/H56 | 1MNQ proxy 2020–24 | 262 | +2.704,44 | 1,335 | 890,64 cerrado | Router comparador de la MISMA familia H, qBH0,115 |
| H74 | Router volatilidad H09/H56 | 1MNQ proxy 2020–24 | 132 | +1.657,84 | 1,438 | 444,10 cerrado | Alternativa H, no señal independiente, N132 |
| H77 | Router alineación gap/premercado H09/H56 | 1MNQ proxy 2020–24 | 140 | +2.385,30 | 1,632 | 584,54 cerrado | Alternativa H, depende de 2022 y N140 |
| T05-377 | Falsa ruptura legacy 5s+filtro377 | 1NQ Last DEV, **estrés** | 115 | +5.102,50 | 1,31826 | 1.797,50 Last | Benchmark congelado, falla PF1,25 con +$10RT; sensibilidad DD Last >2k |
| T147 | Barrida/rechazo 4181 E377 | 17 NQ/3 MNQ Last DEV, BASE | 20 | +642,25 | 1,4992 | 567 cerrado | Paridad G0 sí; temporalidad exposición común pendiente |
| T186 | Fade dislocación macro VWAP | NQ Last DEV, estrés | 70 | −970 | N/D | N/D | Padre standalone negativo; router ya falló PF/DD |
| **T224** | Permanencia lado VWAP 4181 y continuación | 93NQ/13MNQ Last DEV, BASE | 106 | +1.256 | 1,1728 | 1.051,75 cerrado | **Incorporada por solicitud**: PF<1,25, IC90[-11,76,+25,54] USD/día, qBH20=1; D1 no PASS |

**Fases y acciones**: H 2020–24 no compara con T2025–26; router T05+T186 anterior delta +$280 extra10 pero PF extra10=1,20198 y DD Last 2.130 FAIL; T05+T147 solo G0 parent parity, no una sola curva; únicamente T05+T224 comparten calendario y disponen de motores con stop/TP, por lo que el nuevo D2 SHADOW se restringe a la prueba de [prerregistro](NQ_NINE_D2_T05_T224_SHARED_ACCOUNT_SHADOW_PREREG_2026_10_13.md) con costos MIXTOS fieles a padres y 1 cuenta, no validación de ejecución.

**Nuevas candidatas T210,T212,T215,T217:** fuera del grupo ACTIVO de nueve por decisión del usuario; pruebas guardadas completas en [tablero de 13](NQ_13_H_T_D1_SHADOW_ECONOMIC_SCORECARD_2026_10_13.md). T215 no se borra ni se convierte en señal aprobada. D1 formal de cohorte T209–T228 sigue BLOQUEADO 5/20, D2 formal bloqueada. Esta tabla no utiliza q/Holm homogeneizado y DD Last y closed no son comparables directamente.

**Cuenta $50K:** objetivo potencial y no decisión de compra; sin trailing flotante simulado, sin NinjaTrader SIM probado, sin OOS abierto.
