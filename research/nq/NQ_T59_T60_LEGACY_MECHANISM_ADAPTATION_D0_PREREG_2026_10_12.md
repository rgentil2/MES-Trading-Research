# NQ T59–T60 — dos hipótesis NUEVAS inspiradas en H77/H69, D0 SOLO VIABILIDAD

**Prerregistro 12-oct-2026, ANTES de calcular cualquier clasificación T59–T60.** [Auditoría de portabilidad G0 de originales](NQ_LEGACY_H77_H69_H74_T26_PORTABILITY_GATE_2026_10_12.md), [política de bloques ≥20](NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md).

**ACLARACIÓN:** No son H77/H69/H09/H56 originales: no contamos con anterior RTH close 16:00 ET ni ATR de 14 días RTH completos. Las nuevas T59/T60 usarán únicamente PREMKT y apertura HOY 08:00–12:00 ET con Last ya almacenado y agrupación atómica de timestamps; no heredan N, PF, q, IC o años positivos de H. Ningún outcome futuro se examina en D0.

## Datos, reloj, unidades e invariantes

- Mismos siete meses NQ Last DEV **ya almacenados** 2025-10…2026-04 con SHA256, 140 días fuente/135 `frozen_t05 READY`. Este criterio QC ya existente no introduce señales 5s nuevas. `MONTHS` whitelist antes de leer rutas, período sellado jamás abierto. No comprar/descargar historia adicional. Un día READY sin atributos va a `NOT_EVALUABLE`, NO se excluye ex post.
- **Una observación por día** (dos preguntas sobre mismo día) en primera decisión causal al terminar 09:45:00 ET. No fijar ejecutabilidad en ese segundo: timestamp `<09:45:00` constituye únicamente datos plenamente conocidos antes del reloj; **no se simula entrada ni precio fill**.
- Cuatro precios proxy NO equivalentes a cierres exactos de minuto NQ: `PmOpen` = VWAP qty de primera marca atómica timestamp en [08:30,09:30) ET; `PmClose` = VWAP qty de última marca atómica de ese mismo intervalo; `RthOpen` = VWAP qty de primera marca atómica en [09:30,09:45) ET; `RthClose` = VWAP qty de última marca atómica timestamp en [09:30,09:45) ET. Barras de 5 segundos PROHIBIDAS. Empates timestamp indivisibles; primera/última referencia es por **timestamp**, NO print seleccionado del grupo. `PmVWAP` = qty VWAP completo premercado 08:30–09:30; `PmRange` = max-low NQ price ticks de ese intervalo.
- Estado base evaluable si ambos segmentos tienen >=2 **grupos timestamp distintos**, `PmRange>=12 ticks`, `PmBody=PmClose−PmOpen` no nulo, `RthBody=RthClose−RthOpen` no nulo; `abs(PmBody)>=PmRange/5` (20%) y `abs(RthBody)>=PmRange/10` (10%); si no, `OTHER` (si hay cobertura y valores) o `NOT_EVALUABLE` (si no existen segmentos/grupos/rango, cuerpo cero impide dirección). Estas condiciones usan SOLO mercado conocido hasta 09:45, no retorno posterior.
- `sign(x)` es +1 si >0, −1 si <0; no romper timestamp. Los cambios de grupo con datos iguales son invariantes al orden intratimestamp.

## Preguntas y grupos congelados

| Nuevo ID | Pregunta falsable NUEVA | CASE | CONTROL observado | Endpoint FUTURO POSIBLE (NO SE CALCULA EN D0) |
|---|---|---|---|---|
| **T59 PM_BODY_OPPOSITION** | ¿La reversión RTH inicial frente al cuerpo del premercado, a amplitud comparable, se comporta distinto de continuación alineada? | Condiciones base, `sign(RthBody)!=sign(PmBody)` | Las mismas condiciones base y `sign(RthBody)==sign(PmBody)` | Markout signed de +300s desde reloj ancla 09:45 ET, lado de RTHBody, primero timestamp completo después del horizonte; requiere OTRO prerregistro D1 |
| **T60 PM_VWAP_OPEN_DISLOCATION** | ¿La dislocación de apertura RTH respecto al VALOR negociado del premkt actúa como estado que diferencia cuerpos RTH iniciales? | Condiciones base, `abs(RthOpen−PmVWAP)>=PmRange/10`, y `sign(RthOpen−PmVWAP)==sign(PmBody)` (apertura desplazada a favor del premarket) | Las mismas condiciones base y `abs(RthOpen−PmVWAP)>=PmRange/10`, pero `sign(RthOpen−PmVWAP)!=sign(PmBody)` | Diferencia en rango futuro 15min CASE−CONTROL; también requerirá prerregistro D1 aparte |

- `T59` inspirado en oposición premarket de **H56**, pero normaliza por **rango premarket del mismo día** en lugar del ATR RTH del historial. `T60` inspirado en estado premarket/gap de **H77**, pero compara `RthOpen vs PmVWAP`, no OPEN vs CLOSE PREVIO RTH: **no es gap diario original**. El router `H69=H09 OR H56` nunca se etiqueta validado por T59/T60; podría investigarse un **router nuevo** con dos padres solo si existe viabilidad y luego beneficio económico neto con **una cuenta**, registrado antes de outcomes y validado con fills independientes.
- La variable objetivo de T59/T60 **NO es seleccionable o reversible según resultados**. La familia de este lote es dos miembros, sin integrarlos retroactivamente en BH30 T29–T58 ni en el histórico H.

## Criterio de fin de D0

- Publicar **N_CASE/N_CONTROL/N_OTHER/N_NOT_EVALUABLE** por miembro, elegibles por mes, coincidencia caso-caso/solapamiento y auditoría de source 140/135. `TESTABLE` si ambos grupos>=15 días; `LOW_POWER` si alguno 1..14; `UNIDENTIFIABLE` si alguno 0. No estimar trades, P&L, IC90, p, q, DD, PF, delta-router (N/D).
- Conforme a nueva [cadencia por BLOQUES ≥20](NQ_DISCOVERY_STAGED_GATES_POLICY_2026_10_12.md): **DOS hipótesis nuevas no autorizan ejecutar un nuevo D1**; quedan como backlog de próxima cohorte de 20+ distintas con preregistro futuro. No mover parámetros 20%, 10% o 12 ticks si el conteo es desfavorable.
- Confirmar cobertura y no inferir agresor Bid/Ask de Last. No publicar ticks, fechas individuales, precios de sesión, last timestamp ni markouts; workspace privado borrado `always()`. Toda corrección técnica debe mantener el prerregistro y documentar el fallo.
