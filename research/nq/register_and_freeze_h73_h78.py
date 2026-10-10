#!/usr/bin/env python3
"""Append-only sixth-to-seventh family registration, original controls, NO market reads."""
import json
from pathlib import Path
from tools.research_governance import freeze_family,preflight_family

FAMILY='NQ-DEDUCTIVE-ENSEMBLE-H73-H78-V1'
ledger_path=Path('research/SEARCH_LEDGER.json')
ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
if len(ledger['future_families'])!=6 or any(x['id']==FAMILY for x in ledger['future_families']):
 raise RuntimeError('Family seven must be registered after exactly six existing families, before outcomes')
prereg='research/nq/NQ_H73_H78_PREREG_2026_10_10.md'
labels=[
 'H73 previous RTH range HIGH permits H09 gap continuation, LOW permits H56 premarket reversal, at 09:45, one MNQ position or none',
 'H74 previous RTH range LOW permits H09, HIGH permits H56, at 09:45, one MNQ position or none',
 'H75 08:30-09:30 premarket range CONTRACTED permits H09, EXPANDED permits H56, at 09:45, one MNQ position or none',
 'H76 08:30-09:30 premarket range EXPANDED permits H09, CONTRACTED permits H56, at 09:45, one MNQ position or none',
 'H77 premarket body ALIGNED with same-contract opening gap permits H09, OPPOSED permits H56, at 09:45, one MNQ position or none',
 'H78 premarket body OPPOSED with same-contract opening gap permits H09, ALIGNED permits H56, at 09:45, one MNQ position or none'
]
entries=[]
for k,desc in enumerate(labels,73):
 entries.append(dict(id=f'NQ-H{k}',preregistration_path=prereg,research_instrument='NQ',
  execution_instrument='MNQ',analysis_kind='STRATEGY',definition=desc,
  alternative='Net MNQ stop/1.5R-target/30m bracket mean positive; incremental daily PnL vs fixed H69 analyzed secondarily under equal capital and price conditions',
  endpoint='One MNQ 1m NQ price proxy, first completed 09:45 signal, 09:46 bar OPEN entry, 0.15 prior14 RTH stop, 1.5R TP and 30min maximum, 3.88 USD RT, week-block signflip and bootstrap CI90, BH six-test family',
  costs=dict(point_value_usd=2,commission_round_trip_usd=1.88,slippage_round_trip_usd=2.0),
  transfer_validation_plan='NQ 1m is price proxy for MNQ, validate real MNQ contract quote/pricing alignment, fills, 1m stop slippage and firm-specific transaction costs before any funded account trading; not validated by this study'))
fam=dict(id=FAMILY,index=7,
 question='Can prospectively frozen previous-session volatility, premarket range or directional gap-premarket state causally route H09 vs H56 to improve a single-MNQ bracket strategy relative to frozen H69 baseline?',
 origin_units=[x['id'] for x in entries],data_role='REUSED_DEVELOPMENT',
 independent_inference_justification='H09/H56/H69 outcomes and years have been repeatedly searched on 2020-24. This is adaptive exploratory only, not independent inference. 2025/2026 sealed.',
 members=entries,
 definition_files=[prereg,'research/nq/nq_h73_h78_joint_state_routers.py',
  'research/nq/test_nq_h73_h78_joint_state_routers.py',
  'research/nq/nq_h05_h07_level_volume_screen.py',
  'research/nq/nq_h53_h58.py',
  'research/nq/nq_h67_h72_combined_strategies.py'],
 result_artifacts=['results/development/nq_h73_h78_family.json'])
ledger['future_families'].append(fam)
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
lock=freeze_family(Path.cwd(),FAMILY)
preflight_family(Path.cwd(),FAMILY)
print(json.dumps({'status':'FROZEN','family':FAMILY,'alpha':lock['alpha'],'members':len(entries),
 'family_sha256':lock['family_sha256'],'source_sha256':lock['definition_sha256']}))