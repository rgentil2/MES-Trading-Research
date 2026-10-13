# Selección prospectiva de eficiencia monetaria/riesgo — nueve hipótesis, SIN retuning

**2026-10-13. Preferencia explícita del usuario:** mantener las estrategias con **mayor beneficio monetario por unidad de drawdown** para aspirar a maximizar eficiencia de capital y de cada trade. Se aplicará a siguientes trabajos como **criterio de priorización condicionado a robustez**, no se reoptimizarán señales ni se prometerán ganancias. Se eligió DESPUÉS de observar métricas DEV y por lo tanto el ranking **es descriptivo/post hoc, NO evidencia OOS**.

## Dos ejes de decisión que no deben confundirse

1. **Eficiencia histórica del capital:** `E = beneficio neto / máximo drawdown`, solo válida internamente cuando el DD es **del mismo motor, unidad y escenario de costos**. DD flotante Last, DD cerrado y trailing de firma NO son intercambiables. DD negativo o N/D => sin ratio económico favorable.
2. **Eficiencia por operación:** `expectativa neta/trade = beneficio neto / N` con comisión/deslizamiento incluido; **no** comparar dólares por trade sin normalizar NQ (tick US$5) frente MNQ (tick US$0,50). Más adelante exigir **expectativa neta medida en R por operación = neto / riesgo ex ante del contrato** y MAE/MFE, disponible solo cuando el motor haya guardado riesgo real coherente. Un retorno promedio alto con 1NQ y DD inasumible no equivale a eficiencia de 50K.
3. **Primero filtros y luego ranking**: beneficio positivo bajo fricción ×1,5 Y +US$10RT; PF≥1,25 bajo esos tests; N y frecuencia sostenibles; estadística IC90 lower>0 y q/Holm conforme familia completa; consistencia por períodos; ningún fill ambiguo; DD *floating* adverso compatible con umbral de cuenta real, con reserva de seguridad (no agotar los US$2k nominales). Una hipótesis que falle cualquier gate puede permanecer como evidencia/contraste, pero NUNCA promoverse por ratio alto únicamente.
4. **Entre supervivientes:** priorizar mejores `E` **con escenarios estresados y riesgo homogéneo**; usar expectativa en R/trade y frecuencia mensual como criterios secundarios, y control de solapamiento/correlación para una sola cuenta. Preferir frontera de Pareto (más neto con igual o menor DD) a un único score sobre parámetros elegidos post hoc. No mezclar H y T en una curva ni contar H routers derivados como alphas independientes.
5. **Prohibición de reingeniería adaptativa:** no modificar stops/ventanas, número de contratos, filtros ni cohortes para rescatar E. No abrir holdouts, ni descargar nuevos datos; toda prueba conjunta debe usar preregistro, motor de ejecución y cálculo de DD comparable.

## Ranking documental histórico de las nueve — periodos, contratos y DD heterogéneos

| ID | Escenario del padre | N | Neto USD | DD USD | Neto/DD | Neto por trade USD | Tipo DD |
|---|---|---:|---:|---:|---:|---:|---|
| H77 | H / 1MNQ proxy / 2020–24 | 140 | 2,385.30 | 584.54 | 4.081 | 17.04 | DD cerrado |
| H74 | H / 1MNQ proxy / 2020–24 | 132 | 1,657.84 | 444.10 | 3.733 | 12.56 | DD cerrado |
| H69 | H / 1MNQ proxy / 2020–24 | 262 | 2,704.44 | 890.64 | 3.037 | 10.32 | DD cerrado |
| T05-377 | T / 1NQ / 2025oct–2026abr | 115 | 5,102.50 | 1,797.50 | 2.839 | 44.37 | DD LAST adverso |
| H56 | H / 1NQ / 2020–24 | 100 | 8,697.98 | 3,599.09 | 2.417 | 86.98 | DD cerrado |
| H09 | H / 1NQ / 2020–24 | 173 | 18,874.00 | 8,122.00 | 2.324 | 109.10 | DD cerrado |
| T224 | T / 93NQ/13MNQ / 2025oct–2026abr | 106 | 1,256.00 | 1,051.75 | 1.194 | 11.85 | DD cerrado |
| T147 | T / 17NQ/3MNQ / 2025oct–2026abr | 20 | 642.25 | 567.00 | 1.133 | 32.11 | DD cerrado |
| T186 | T / NQ / 2025oct–2026abr | 70 | -970.00 | N/D | N/D | -13.86 | DD individual no disponible |

**Advertencia crítica:** esta tabla es un *inventario ordenado por ratio histórico*, NO ranking válido entre H2020–24 y T2025–26; las primeras tres usan **1MNQ en cinco años**, T05 usa **1NQ siete meses**; H09/H56 1NQ y riesgo elevado; T147/T224 DD cerrado, T05 DD Last. H77/H74/H69 compiten por los **mismos padres** H09/H56 y son **tres elecciones de router**, no tres exposiciones simultáneas. El % de retorno acumulado sobre cuenta nominal 50K de H69 es bajo.

## Experimento nuevo COMPLETADO T05+T224 — DD CERRADO homogéneo dentro de un motor

Resultado [GitHub Action 38429799987 SUCCESS](https://github.com/rgentil2/MES-Trading-Research/actions/runs/38429799987) y [reporte D2 exacto](NQ_NINE_D2_T05_T224_SHARED_ACCOUNT_SHADOW_RESULTS_2026_10_13.md):

| Sistema | N | Neto USD | DD cerrado USD | Neto/DD cerrado | Expectativa USD/trade | PF |
|---|---:|---:|---:|---:|---:|---:|
| T05 sola, estrés original | 115 | +5.102,50 | 1.310,00 | **3,895** | +44,37 | 1,3183 |
| T05+T224, costos padres mixtos | 194 | +6.849,25 | 1.641,00 | **4,174** | +35,305 | 1,3255 |
| Router con costo T224 1,5× | 194 | +5.967,75 | 1.718,25 | **3,473** | +30,762 | 1,2780 |
| Router ambos +US$10RT | 194 | +4.909,25 | 1.811,00 | **2,711** | +25,305 | **1,2223 FAIL** |

**Interpretación de selección:** la mejora de +7,2% de E BASE *no supera* la caída de robustez cuando se estresan costos; la expectativa/trade cae 20,43%. Además son escenarios con costos propios de padres no homogéneos NQ/MNQ, **sin DD flotante conjunto**, por lo cual **NO ascender el router como mejor estrategia**. T05 individual con +$10RT también PF1,23717<1,25, DD Last original 1.797,50 y peor orden intra-timestamp hasta 2.462,50.

## Cartera reducida / bandeja de trabajo después de esta criba

| Destino operativo | Identificadores | Motivo | Acción |
|---|---|---|---|
| **BENCHMARK T de ejecución** | **T05-377** | PnL realzado en DEV y >100 operaciones, mejor USD/op que router pero fails costo extra | Mantener reglas congeladas y examinar portabilidad/fill, NO operar ni tuneo |
| **CANDIDATO T de complementariedad** | **T05+T224** como alternativa al anterior, NO adicional | Ratio DD cerrado 4,174 BASE pero falla +10RT, PF1,2223, DD float N/D | Conservar solo en archivo de cartera sombra; no elegir como ganador ni optimizar |
| **ALTERNATIVA H de eficiencia** | **H77, H74** (mutuamente excluyentes) | Mayor neto/DD histórico de H proxy 1MNQ (4,08 y 3,73) | Mantener para comparación solo dentro de H, revisar 2022 concentrado y muestras 140/132; sin D1/OOS confirmado |
| **COMPARADOR H de frecuencia y beneficio** | **H69** | 262 ops, mayor PnL H en 1MNQ que H77/H74 | Retener como control de selectores; q0,115, no promover |
| **PADRES/DIAGNÓSTICOS, NO sumables** | H09, H56 | Construyen rutas H; 1NQ DD elevado/ventanas no comparables | No operar independientes a tamaño 1NQ para $50K |
| **ARCHIVO — baja eficiencia, N insuficiente o pérdidas** | T147, T186, T224 *standalone* | T147 N20 E1,133, T186 neto negativo, T224 E1,194/PF1,173 | Archivar como mecanismos estudiados, no dedicar nuevos filtros ni optimización |

**No confundir “quedarnos” con borrar historiales o declarar una estrategia capaz de fondeo:** cero D1/D2 formal PASS. Se conservan registros y evidencia negativa. El trabajo siguiente será comprobar calidad causal de fills/riesgo bajo condiciones homogéneas de NinjaTrader SIM sobre una especificación congelada, y SOLO entonces escoger capital/fondeo. **Siempre mantener las nueve fichas documentales** aunque la bandeja de implementación esté reducida.
