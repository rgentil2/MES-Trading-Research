#!/usr/bin/env python3
"""Fixed descriptive MES market map. No hypothesis outcomes are evaluated."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data_pipeline import build_continuous, contract_info
from src.mes_market_state_v1 import VERSION, STATES, causal_inputs, classify, diagnose, configuration

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'research/market_state/MES_MS1_FREEZE.json'
FROZEN_FILES = ['src/mes_market_state_v1.py', 'src/data_pipeline.py',
                'tools/audit_mes_market_state.py', 'tests/test_mes_market_state_v1.py',
                'research/market_state/MES_MS1_PROTOCOL.md', 'requirements.txt',
                '.github/workflows/mes-market-state-v1.yml']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze():
    if LOCK.exists():
        raise ValueError('immutable first-run freeze already exists')
    record = {'version': VERSION, 'authority': 'DESCRIPTIVE_FEATURE_MAP_ONLY',
              'base_commit': '27ac8ef15729832841e382f15cbad5d20b1a4503',
              'config': configuration(), 'outcomes_permitted': False,
              'fingerprints': {p: digest(ROOT/p) for p in FROZEN_FILES}}
    LOCK.write_text(json.dumps(record, indent=2, allow_nan=False)+'\n')
    return record


def preflight():
    lock = json.loads(LOCK.read_text())
    if lock['version'] != VERSION or lock['config'] != configuration() or lock['outcomes_permitted']:
        raise ValueError('freeze metadata mismatch')
    if lock['fingerprints'] != {p: digest(ROOT/p) for p in FROZEN_FILES}:
        raise ValueError('frozen MS1 definition/dependency changed')
    return lock


def development_files(raw_dir):
    # Discover names only; never open out-of-scope contract contents.
    files = sorted((p for p in raw_dir.glob('MES ??-??.Last.txt')
                    if 2020 <= contract_info(p)[0] <= 2024), key=lambda p: contract_info(p)[:2])
    expected = {(y, m) for y in range(2020, 2025) for m in [3, 6, 9, 12]}
    if {contract_info(p)[:2] for p in files} != expected or len(files) != 20:
        raise ValueError('require exactly twenty MES development contracts')
    return files


def folds(features):
    rows = []
    for i, (train_start, train_end, test_start, test_end) in enumerate([
        ('2020-01-01','2021-12-31','2022-01-01','2022-06-30'),
        ('2020-07-01','2022-06-30','2022-07-01','2022-12-31'),
        ('2021-01-01','2022-12-31','2023-01-01','2023-06-30'),
        ('2021-07-01','2023-06-30','2023-07-01','2023-12-31'),
        ('2022-01-01','2023-12-31','2024-01-01','2024-06-30'),
        ('2022-07-01','2024-06-30','2024-07-01','2024-12-31')], 1):
        t = features[features.date.between(test_start, test_end)]
        rows.append(dict(fold=i, train_start=train_start, train_end=train_end,
                         test_start=test_start, test_end=test_end,
                         status='INTERNAL_REUSED_DATA_SCAFFOLD_NO_STRATEGY_TEST',
                         test_weekday_rows=len(t), test_state_counts={s:int((t.regime==s).sum()) for s in STATES},
                         test_episode_ids_observed=int(t.episode_id.nunique())))
    return rows


def markdown(report):
    lines = ['# MES Market State V1 — auditoría descriptiva 2020–2024', '',
             'Motor separado de R063. Sin estrategias, retornos futuros ni aprobación para operar.', '',
             f"Filas de minuto utilizadas: {report['input_rows']:,}. Archivos abiertos: 20 contratos de 2020–2024.",
             f"Fechas laborables: {report['weekday_rows']}. Episodios observados: {report['episodes']}.", '',
             '| Estado | Fechas | Episodios | Mediana duración observada |',
             '|---|---:|---:|---:|']
    for s in STATES:
        a = report['states'][s]
        lines.append(f"| {s} | {a['weekday_rows']} | {a['episodes']} | {a['median_observed_sessions']} |")
    lines += ['', 'R1: High/Directional; R2: High/Chop; R3: Low/Directional; R4: Low/Chop.',
              'High/Low y Directional/Chop retienen el estado previo dentro de P33–P67.',
              'Los episodios no se consideran réplicas independientes y sus duraciones finales son retrospectivas.',
              '', '## Motivos de R0', '', '| Motivo | Fechas |', '|---|---:|']
    for reason, n in report['r0_reasons'].items():
        lines.append(f'| {reason} | {n} |')
    lines += ['', '## Cobertura anual', '', '| Año | Fechas laborables | R1–R4 | R0 |', '|---|---:|---:|---:|']
    for year, a in report['annual'].items():
        lines.append(f"| {year} | {a['weekday_rows']} | {a['classified_rows']} | {a['r0_rows']} |")
    lines += ['', '## Transiciones empíricas dentro del mismo contrato', '',
              '| Desde / hacia | R0 | R1 | R2 | R3 | R4 |', '|---|---:|---:|---:|---:|---:|']
    for s in STATES:
        values = report['transition_proportions'][s]
        lines.append('| '+s+' | '+' | '.join('N/A' if values[t] is None else f'{100*values[t]:.1f}%' for t in STATES)+' |')
    lines += ['', f"Alertas CUSUM: {report['change_alerts']}. Los umbrales no se ajustaron después de ver la cobertura.",
              'CUSUM no prueba rupturas estructurales; no tiene tasa de falsas alarmas calibrada ni P(Change).',
              '', '## Verificación y límites', '',
              '- Pruebas de invariancia por prefijo y modificación de datos futuros; aislamiento de contrato y exclusión de 2025/2026.',
              '- Archivo causal separado de episodios y duraciones finales. Matriz descriptiva; no pronóstico validado.',
              '- Calendario de días laborables, no calendario CME certificado. R0 incluye festivos, cobertura incompleta e inicialización.',
              '- Rollover heredado de extremos de exportación NinjaTrader. No se ha certificado una selección de contrato en vivo.',
              '- Gap preapertura es un proxy; POC/VAH/VAL exactos, HMM, BOCPD, Bai–Perron y ciclos quedan pendientes.',
              '- Los seis folds sólo describen cobertura. No se ejecutó walk-forward de rentabilidad, CPCV, PBO ni DSR.',
              '- MES 2025 ya fue investigado. MES 2026 no se abrió y sigue reservado para una estrategia completa congelada.',
              '', 'Siguiente paso: un fenómeno acotado y registrado antes de calcular sus resultados, con control comparable y evaluación temporal.', '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--freeze', action='store_true')
    p.add_argument('--preflight', action='store_true')
    p.add_argument('--raw-dir', type=Path, default=ROOT/'data/raw')
    args = p.parse_args()
    if args.freeze:
        freeze(); print('PASS: fixed descriptive MS1 protocol frozen before data run'); return
    lock = preflight()
    if args.preflight:
        print('PASS: MS1 frozen files and configuration unchanged'); return
    files = development_files(args.raw_dir)
    raw, manifest, rolls = build_continuous(files, 'UTC', .25)
    before = len(raw)
    # Late DEC24 exports can include timestamps outside the target years.
    raw = raw[raw.timestamp_et.dt.year.between(2020, 2024)].copy()
    if raw.empty:
        raise ValueError('no in-scope rows')
    inputs = causal_inputs(raw)
    features = classify(inputs)
    matrix, probabilities, episodes = diagnose(features)
    for r in features.itertuples():
        if r.source_max_et and pd.Timestamp(r.source_max_et) > pd.Timestamp(r.asof_et):
            raise ValueError('future bar reached as-of features')
        if r.previous_rth_date and r.previous_rth_date >= r.date:
            raise ValueError('current RTH reached preopen features')
    # Recompute every chronological H1/H2 boundary on a raw prefix. This tests
    # aggregation and sequential classification, not just date declarations.
    verified_prefixes = []
    for ds in ['2021-12-31','2022-06-30','2022-12-30','2023-06-30','2023-12-29','2024-06-28','2024-12-31']:
        cutoff = pd.Timestamp(ds, tz='America/New_York') + pd.Timedelta(minutes=570)
        prefix = classify(causal_inputs(raw[raw.timestamp_et <= cutoff]))
        full = features[features.date <= ds].reset_index(drop=True)
        pd.testing.assert_frame_equal(full, prefix.reindex(columns=features.columns), check_dtype=False)
        verified_prefixes.append(ds)
    report = dict(version=VERSION, authority='DESCRIPTIVE_ONLY_NO_STRATEGY_PROMOTION',
                  source_scope='ET calendar 2020-2024 only; MES 2025 already researched',
                  source_files=manifest.to_dict('records'), source_rollovers=rolls.to_dict('records'),
                  input_rows=len(raw), excluded_out_of_scope_rows=before-len(raw),
                  weekday_rows=len(features), episodes=len(episodes),
                  states={}, r0_reasons=features[features.regime=='R0'].r0_reason.value_counts().to_dict(),
                  change_alerts=int(features.change_alert.sum()), annual={},
                  config=configuration(), freeze=lock, strategy_authorized=False,
                  forward_returns_computed=False, pnl_computed=False,
                  contract_2025_opened=False, contract_2026_opened=False,
                  calendar_2025_features_computed=False, calendar_2026_features_computed=False,
                  prefix_invariance_verified=verified_prefixes,
                  transition_counts=matrix.to_dict(orient='index'),
                  transition_proportions=json.loads(probabilities.to_json(orient='index')),
                  internal_folds=folds(features),
                  environment=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    for s in STATES:
        e = episodes[episodes.regime==s]
        report['states'][s] = dict(weekday_rows=int((features.regime==s).sum()), episodes=len(e),
                                   median_observed_sessions=float(e.sessions.median()) if len(e) else None,
                                   max_observed_sessions=int(e.sessions.max()) if len(e) else None)
    for year in range(2020, 2025):
        y = features[features.date.str.startswith(str(year))]
        report['annual'][str(year)] = dict(weekday_rows=len(y), classified_rows=int((y.regime!='R0').sum()),
                                          r0_rows=int((y.regime=='R0').sum()))
    out = ROOT/'results/market_state'
    out.mkdir(parents=True, exist_ok=True)
    features.to_csv(out/'MES_MS1_CAUSAL_FEATURES.csv', index=False)
    episodes.to_csv(out/'MES_MS1_EPISODES.csv', index=False)
    matrix.to_csv(out/'MES_MS1_TRANSITION_COUNTS.csv', index_label='from_state')
    probabilities.to_csv(out/'MES_MS1_TRANSITION_PROPORTIONS.csv', index_label='from_state')
    # Timestamps in the source manifest are provenance, not feature values.
    (out/'MES_MS1_REPORT.json').write_text(json.dumps(report, indent=2, default=str, allow_nan=False)+'\n')
    (out/'MES_MS1_REPORT.md').write_text(markdown(report))
    print(markdown(report))


if __name__ == '__main__':
    main()
