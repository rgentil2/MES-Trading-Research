#!/usr/bin/env python3
"""Register a prospective family in the cumulative research ledger BEFORE outcomes.
Uses the repository's official freeze_family; refuses double registration.
"""
import json
from pathlib import Path
from tools.research_governance import freeze_family, preflight_family

ledger_path=Path('research/SEARCH_LEDGER.json')
ledger=json.loads(ledger_path.read_text())
family_id='NQ-PREMARKET-WEEKLY-H53-H58-V1'
if len(ledger['future_families'])!=3 or any(f['id']==family_id for f in ledger['future_families']):
    raise RuntimeError('Unexpected prior family history: abort without modifications')
definitions=[
 'First premarket 08:30–09:30 high/low wick break from 09:46–10:45 ET that closes inside; first break consumes day; fade',
 'Two close confirmation beyond premarket range with volume >=1.20 prior20 same-minute median; continuation',
 'Overnight VWAP >=800 bars, first15 reversion toward 0.15 ATR gap from VWAP, body >=0.07 ATR and residual >=0.05 ATR',
 'Premarket body >=0.20 past14 median RTH range, initial15 body >=0.10 past14 median RTH range opposite; follow reversal',
 'Previous completed ISO week >=3 RTH sessions same contract; first wick sweep and close reentry; fade',
 'Premarket range <=0.65 past20 median and initial15 >=1.10 past20 median with >=0.10 past14 ATR body; follow impulse'
]
prereg='research/nq/NQ_H53_H58_PREREG_2026_10_10.md'
ids=[f'NQ-H{n}' for n in range(53,59)]
members=[dict(id=i,preregistration_path=prereg,research_instrument='NQ',analysis_kind='DIRECTIONAL',execution_instrument=None,definition=d,alternative='Directional mean net NQ +30min after Free commission and slippage >0',endpoint='Next-minute entry OPEN to +30min OPEN; block-week bootstrap 90%, BH on six') for i,d in zip(ids,definitions)]
family=dict(id=family_id,index=4,question='Do premarket references, overnight VWAP, weekly levels or overnight-to-RTH transitions predict positive net NQ 30 minute returns?',origin_units=ids,data_role='REUSED_DEVELOPMENT',independent_inference_justification='Previously mined development 2020–2024, no independent support. Strictly no 2025 or 2026 market reads.',members=members,definition_files=[prereg,'research/nq/nq_h53_h58.py','research/nq/test_nq_h53_h58.py','research/nq/nq_h05_h07_level_volume_screen.py'],result_artifacts=['results/development/nq_h53_h58_family.json'])
ledger['future_families'].append(family)
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({'register':family_id,'family_index':4,'members':ids}))
snapshot=freeze_family(Path.cwd(),family_id)
preflight_family(Path.cwd(),family_id)
print(json.dumps({'freeze_preflight':'PASS','alpha':snapshot['alpha'],'family_sha256':snapshot['family_sha256']}))