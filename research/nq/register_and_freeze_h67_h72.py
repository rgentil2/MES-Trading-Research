#!/usr/bin/env python3
"""Register H67-H72 in append-only ledger and perform authoritative family snapshot.

No raw market data, parent outcomes or 2025/2026 files are opened here.
"""
import json
from pathlib import Path
from tools.research_governance import freeze_family,preflight_family

FAMILY='NQ-DEDUCTIVE-ENSEMBLE-H67-H72-V1'
ledger_path=Path('research/SEARCH_LEDGER.json')
ledger=json.loads(ledger_path.read_text())
if len(ledger['future_families'])!=5 or any(x['id']==FAMILY for x in ledger['future_families']):
 raise RuntimeError('Family 6 preregistration must be first added only after five frozen families')
prereg='research/nq/NQ_H67_H72_PREREG_2026_10_10.md'
labels=[
 'H09 OR H55/H56 matching side consensus; single 09:45 trade, H09 priority',
 'H09 OR H55 at 09:45, H09 priority, H56 context only',
 'H09 OR H56 at 09:45, H09 priority, H55 context only',
 'H09 OR H55/H56 matching consensus at 09:45 ELSE H29 at 10:00',
 'H09 OR H55/H56 matching consensus at 09:45 ELSE first H54 accepted level breakout 09:47-10:45',
 'Previously closed RTH range > prior20 median: H09 at 09:45 ELSE H54 later; otherwise H55/H56 matching consensus at 09:45 ELSE H29 at 10:00; no regime no trade'
]
entries=[]
for k,desc in enumerate(labels,67):
 entries.append(dict(id=f'NQ-H{k}',preregistration_path=prereg,research_instrument='NQ',
  execution_instrument='MNQ',analysis_kind='STRATEGY',definition=desc,
  alternative='Ex ante joint router has positive expected realized MNQ 30m fixed 0.15 prior14 range stop and 1.5R target net of 3.88 USD commission and slippage',
  endpoint='One proxy MNQ bracket trade max per day. Next 1m open after frozen causal parent, 30m time limit, weekly block bootstrap 90% CI and BH six-test family',
  costs=dict(point_value_usd=2,commission_round_trip_usd=1.88,slippage_round_trip_usd=2.0),
  transfer_validation_plan='NQ minute bar is price proxy for MNQ; validate MNQ contract-timestamp-price parity, own fills, slippage and MFFU fee schedule with independent 2020-24 MNQ source before any implementation; cannot claim validated fill now'))
fam=dict(id=FAMILY,index=6,
 question='Does mechanically choosing and routing gap, premarket/VWAP consensus and fallback signals improve one-MNQ bracket profitability, frequency and risk over each parent and H67 baseline?',
 origin_units=[x['id'] for x in entries],data_role='REUSED_DEVELOPMENT',
 independent_inference_justification='All parents, some collisions and outcomes already examined on 2020-24 data; strategy post-selection only. 2025/26 never opened.',
 members=entries,
 definition_files=[prereg,'research/nq/nq_h67_h72_combined_strategies.py','research/nq/test_nq_h67_h72_combined_strategies.py','research/nq/nq_h05_h07_level_volume_screen.py','research/nq/nq_h08_h32_minute_2020_2024.py','research/nq/nq_h53_h58.py'],
 result_artifacts=['results/development/nq_h67_h72_family.json'])
ledger['future_families'].append(fam)
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
snapshot=freeze_family(Path.cwd(),FAMILY)
preflight_family(Path.cwd(),FAMILY)
print(json.dumps({'status':'FROZEN','family':FAMILY,'members':len(entries),'alpha':snapshot['alpha'],
                  'family_sha256':snapshot['family_sha256'],'files':snapshot['definition_sha256']}))